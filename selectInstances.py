from maya import cmds
from maya.api import OpenMaya


def getInstances(path: str):
    sel = OpenMaya.MSelectionList()
    sel.add(path)
    dagPath = sel.getDagPath(0)

    objs = []

    itDag = OpenMaya.MItDag()
    itDag.reset(dagPath, OpenMaya.MItDag.kBreadthFirst)

    fnDag = OpenMaya.MFnDagNode()

    while not itDag.isDone():
        fnDag.setObject(itDag.currentItem())
        if fnDag.isInstanced():
            mObj = fnDag.parent(0)
            p = OpenMaya.MFnDagNode(mObj)

            dataParent = p.fullPathName()
            dagPath2 = itDag.getPath()
            dagPath2.pop(1)
            hierarchyParent = dagPath2.fullPathName()

            if dataParent != hierarchyParent:
                objs.append(hierarchyParent)

        itDag.next()

    return objs


def main(select=True):
    root = cmds.ls(sl=True, fl=True, long=True)

    if not root:
        cmds.error("Nothing is select, select root group.")
    else:
        root = root[0]

    instances = getInstances(root)
    if select:
        cmds.select(instances, r=True)


if __name__ == "__main__":
    main()
