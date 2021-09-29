#------------------------------------------------------------------------------#

from maya import cmds
import maya.OpenMaya as om
import math

LOC_SCALE = 1

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
   
    # Convert to MTransformationMatrix to extract rotations:
    mTransformMtx = om.MTransformationMatrix(mMatrix)
    
    # Get an MEulerRotation object
    eulerRot = mTransformMtx.eulerRotation() # MEulerRotation
    # Update rotate order
    eulerRot.reorderIt(rot_order)

    # Convert from radians to degrees:
    angles = [math.degrees(angle) for angle in (eulerRot.x, eulerRot.y, eulerRot.z)]
    return angles 


def run(translate=True, rotate=True, bake=False, scale=LOC_SCALE, useAPI=False):
    sel = cmds.ls(sl=1)
    if not sel:
        print "Select something first"
        return
    
    locators = []
    for obj in sel:
        loc = cmds.spaceLocator()[0]
        loc = cmds.rename(loc, obj + '_loc') # This will return the unique name
        locators.append(loc)
        cmds.setAttr(loc + '.localScale', *[scale]*3) # Make the list 3 long and unpack it
        
        # Create an attribute that tracks where this loc came from
        cmds.addAttr(loc, longName='link', dataType='string')
        cmds.setAttr(loc + '.link', obj, type='string')
        
        rot_order = cmds.getAttr(obj + '.rotateOrder')
        cmds.setAttr(loc + '.rotateOrder', rot_order)
        
        keyframes = cmds.keyframe(obj, q=True) or []
        keyframes = list(set(keyframes))
                
        if not keyframes:
            current_frame = cmds.currentTime(q=True)
            keyframes.append(current_frame)
            cmds.warning("No keyframes detected on object. Defaulting to current frame only.")
        elif bake:
            keyframes = [x * 1.0 for x in xrange(int(min(keyframes)), int(max(keyframes))+1)]
                    
        for key in keyframes:
            if translate:
                # Do Translate
                matrix = cmds.getAttr(obj + '.parentMatrix', time=key) # NOT the world!
                rotate_pivot = cmds.getAttr(obj + '.rotatePivot', time=key)[0] # A tuple in a list
                rotate_pivot_translate = cmds.getAttr(obj + '.rotatePivotTranslate', time=key)[0] # A tuple in a list
                translate = cmds.getAttr(obj + '.translate', time=key)[0] # A tuple in a list
                
                if useAPI:
                    # Could use API, but it's slower
                    api_matrix = APIMatrix(matrix)
                    point_pivot  = APIPoint(rotate_pivot)
                    vec_pivot_translate  = APIVector(rotate_pivot_translate)
                    vec_translate  = APIVector(translate)
                    offset = (point_pivot + vec_pivot_translate + vec_translate) * api_matrix
                
                else: # Could do the math manually: 
                    offset_pivot = [x + y + z for x,y,z in zip(rotate_pivot, rotate_pivot_translate, translate)]

                    offset = [matrix[0]*offset_pivot[0] + matrix[4]*offset_pivot[1] + matrix[8]*offset_pivot[2] + matrix[12],
                              matrix[1]*offset_pivot[0] + matrix[5]*offset_pivot[1] + matrix[9]*offset_pivot[2] + matrix[13],
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
                

#------------------------------------------------------------------------------#

if __name__ == "__main__":
    # code that is being timed
    start = cmds.timerX()
    run(bake=False)
    elapsed = cmds.timerX()
    print("Finished in {0} seconds.".format(elapsed - start))
