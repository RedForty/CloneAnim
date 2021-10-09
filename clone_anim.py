#------------------------------------------------------------------------------#

from maya import cmds, mel
import maya.OpenMaya as om
import math

LOC_SCALE = 1
TIMELINE = mel.eval('string $tmpString=$gPlayBackSlider')

#------------------------------------------------------------------------------#

def APIMatrix(mlist):  # where mlist is a list of floats
    matrix = om.MMatrix()
    om.MScriptUtil.createMatrixFromList(mlist, matrix)
    return matrix

def APIPoint(plist): # where plist is a list of floats
    return om.MPoint(plist[0], plist[1], plist[2], 1.0)

def APIVector(vlist): # where vlist is a list of floats
    return om.MVector(vlist[0], vlist[1], vlist[2])
    
def get_rotation_from_matrix(matrix_list, rot_order):
    
    mMatrix = APIMatrix(matrix_list)

    #-------------------------------------------
    # Part 2, get the euler values
    
    # Convert to MTransformationMatrix to extract rotations:
    mTransformMtx = om.MTransformationMatrix(mMatrix)
    
    # Get an MEulerRotation object
    eulerRot = mTransformMtx.eulerRotation() # MEulerRotation
    # Update rotate order to match original object, since the orig MMatrix has
    # no knoweldge of it:
    eulerRot.reorderIt(rot_order)

    # Convert from radians to degrees:
    angles = [math.degrees(angle) for angle in (eulerRot.x, eulerRot.y, eulerRot.z)]
    return angles 

def get_timeline_selection():
    if cmds.timeControl(TIMELINE, q=True, rangeVisible=True):
        return cmds.timeControl(TIMELINE, q=True, rangeArray=True)
    else: 
        return []

def get_timeline_range():
    start_frame = cmds.playbackOptions(q=True, minTime=True)
    end_frame = cmds.playbackOptions(q=True, maxTime=True)
    return [start_frame, end_frame]

def run(nodes=None, anim=True, bake=False, sampleBy='keys', translate=True, rotate=True, scale=LOC_SCALE, useAPI=False, timer=False):
    if timer:
        # code that is being timed
        start_timer = cmds.timerX()
    
    if not nodes: 
        nodes = cmds.ls(sl=1)
    if not nodes:
        cmds.warning("Select something first!")
        return

    locators = []
    for obj in nodes:
        loc = cmds.spaceLocator()[0]
        loc = cmds.rename(loc, obj + '_loc') # This will return the unique name
        locators.append(loc)
        cmds.setAttr(loc + '.localScale', *[scale]*3) # Make the list 3 long and unpack it
        
        # Create an attribute that tracks where this loc came from
        cmds.addAttr(loc, longName='link', dataType='string')
        cmds.setAttr(loc + '.link', obj, type='string')

        rot_order = cmds.getAttr(obj + '.rotateOrder')
        cmds.setAttr(loc + '.rotateOrder', rot_order)

        timeline_selection = get_timeline_selection() # Selection takes priority
        if timeline_selection:
            timeline_selection = [x * 1.0 for x in range(int(min(timeline_selection)), int(max(timeline_selection))+1)]

        if anim:
            keyframes = cmds.keyframe(obj, q=True) or []
            keyframes = list(set(keyframes)) # All the keys
            if bake:
                time_range = get_timeline_range()
                start      = min(time_range + keyframes)
                end        = max(time_range + keyframes)
                keyframes = [x * 1.0 for x in range(int(start), int(end)+1)]
                
            if timeline_selection:
                new_keyframes = []
                for key in keyframes:
                    if key in timeline_selection:
                        new_keyframes.append(key)
                keyframes = new_keyframes # Crop to selection

            if not sampleBy == 'keys':
                if isinstance(sampleBy, int):
                    # Resample the keys by the number
                    new_keyframes = [x * 1.0 for x in range(int(min(keyframes)), int(max(keyframes))+1, sampleBy)]
                    if not max(keyframes) in new_keyframes:
                        new_keyframes.append(max(keyframes))
                    keyframes = new_keyframes
        else: # If no anim, take current frame
            current_frame = cmds.currentTime(q=True)
            keyframes = [current_frame]
            cmds.warning("No keyframes detected on object. Defaulting to current frame only.")
        

        for key in keyframes:
            if translate:
                # Do Translate
                matrix       = cmds.getAttr(obj + '.parentMatrix', time=key) # NOT the world!
                rotate_pivot = cmds.getAttr(obj + '.rotatePivot' , time=key)[0] # A tuple in a list
                translate    = cmds.getAttr(obj + '.translate'   , time=key)[0] # A tuple in a list
                rp_translate = cmds.getAttr(obj + '.rotatePivotTranslate', time=key)[0] # A tuple in a list
                
                if useAPI:
                    # Could use API, but it's slower
                    api_matrix        = APIMatrix(matrix)
                    point_pivot       = APIPoint(rotate_pivot)
                    vec_translate     = APIVector(translate)
                    vec_rp_translate  = APIVector(rp_translate)
                    offset = (point_pivot + vec_rp_translate + vec_translate) * api_matrix
                
                else: # Could do the math manually: http://discourse.techart.online/t/maya-get-world-space-rotatepivot-at-a-specified-time/4559/2
                    offset_pivot = [x + y + z for x,y,z in zip(rotate_pivot, rp_translate, translate)]

                    offset = [matrix[0]*offset_pivot[0] + matrix[4]*offset_pivot[1] + matrix[8]*offset_pivot[2]  + matrix[12],
                              matrix[1]*offset_pivot[0] + matrix[5]*offset_pivot[1] + matrix[9]*offset_pivot[2]  + matrix[13],
                              matrix[2]*offset_pivot[0] + matrix[6]*offset_pivot[1] + matrix[10]*offset_pivot[2] + matrix[14]]                
                    
                cmds.setKeyframe(loc, attribute='translateX', value=offset[0], time=key)
                cmds.setKeyframe(loc, attribute='translateY', value=offset[1], time=key)
                cmds.setKeyframe(loc, attribute='translateZ', value=offset[2], time=key)
            
            if rotate:
                # Rotation
                rot_matrix = cmds.getAttr(obj + '.worldMatrix', time=key)
                angles = get_rotation_from_matrix(rot_matrix, rot_order)
                cmds.setKeyframe(loc, attribute='rotateX', value=angles[0], time=key)
                cmds.setKeyframe(loc, attribute='rotateY', value=angles[1], time=key)
                cmds.setKeyframe(loc, attribute='rotateZ', value=angles[2], time=key)
    
    cmds.select(locators)
    # mel.eval('dgdirty -a;') # Old way of refreshing
    cmds.currentTime(cmds.currentTime(q=True)) # Evaluate the current frame
    
    if timer:
        end_timer = cmds.timerX()
        print("Finished in {0} seconds.".format(end_timer - start_timer))

#------------------------------------------------------------------------------#

if __name__ == "__main__":
    run(sampleBy=1, anim=True, timer=True)

