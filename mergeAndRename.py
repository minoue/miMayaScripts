from maya import cmds


def main():
    sel = cmds.ls(sl=True, fl=True, long=True)
    target = sel[-1]

    targetShortName = target.split("|")[-1]

    targetParent = cmds.listRelatives(target, parent=True, fullPath=True)

    if targetParent is not None:
        targetParent = targetParent[0]

    uniteResult = cmds.polyUnite()
    newMesh = uniteResult[0]
    cmds.DeleteHistory()

    tempName = targetShortName + "_TMP"
    cmds.rename(newMesh, tempName)

    if targetParent is not None:
        cmds.parent(tempName, targetParent)

    cmds.rename(tempName, targetShortName)


if __name__ == "__main__":
    main()