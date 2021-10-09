# CloneAnim
Copies animation in worldspace from selected objects to generated locators. Super fucking fast.


##
Usage:
Use these python commands to run the tool.


By default CloneAnim will copy the current keys of the selected object(s).

    import clone_to_locators.py
    clone_to_locators.run()

Clone will be baked on 1s for the duration of keyframes

    clone_to_locators.run(sampleBy=1)

Clone will be bakes on 1s for the duration of the timeline plus keyframes

    clone_to_locators.run(bake=True)

Clone will only copy translates

    clone_to_locators.run(rotate=False) 

Clone will only copy rotates

    clone_to_locators.run(translate=False)


