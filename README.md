# cloneAnim.py
Copies animation in worldspace from selected objects to generated locators. Super fucking fast.


##
Usage:
Use these python commands to run the tool.


By default cloneAnim will copy the current keys of the selected object(s).

    import cloneAnim.py
    cloneAnim.run()

Clone will be baked on 1s for the duration of keyframes

    cloneAnim.run(sampleBy=1)

Clone will be bakes on 1s for the duration of the timeline plus keyframes

    cloneAnim.run(bake=True)

Clone will only copy translates

    cloneAnim.run(rotate=False) 

Clone will only copy rotates

    cloneAnim.run(translate=False)


