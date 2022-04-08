from maya import cmds
from maya import OpenMaya


def getInstances(path):
    # type: (str) -> list
    """
    http://shihchinw.github.io/2011/10/how-to-determine-direct-instances-in-maya.html
    Get instance objects from selected selected node and its children

    """

    sel = OpenMaya.MSelectionList()

    dagPath = OpenMaya.MDagPath()
    fnDag = OpenMaya.MFnDagNode()
    sel.add(path)
    sel.getDagPath(0, dagPath)

    objs = []

    itDag = OpenMaya.MItDag()
    itDag.reset(dagPath, OpenMaya.MItDag.kBreadthFirst)

    while not itDag.isDone():

        fnDag.setObject(itDag.currentItem())

        if fnDag.isInstanced():
            mObj = fnDag.parent(0)
            p = OpenMaya.MFnDagNode(mObj)

            dataParent = p.fullPathName()

            itDag.getPath(dagPath)
            dagPath.pop(1)
            hierarchyParent = dagPath.fullPathName()

            if dataParent != hierarchyParent:
                objs.append(hierarchyParent)

        itDag.next()

    return objs


def main():
    root = cmds.ls(sl=True, fl=True, long=True)

    if not root:
        cmds.error("Nothing is select, select root group.")
    else:
        root = root[0]

    instances = getInstances(root)
    cmds.select(instances, r=True)


if __name__ == "__main__":
    main()
