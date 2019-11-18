from maya.api import OpenMaya
from maya import cmds
import time


def checkIt(plug):
    dataHandle = plug.asMDataHandle()
    arrayDataHandle = OpenMaya.MArrayDataHandle(dataHandle)
    while not arrayDataHandle.isDone():
        outputHandle = arrayDataHandle.outputValue()
        x, y, z = outputHandle.asFloat3()
        if x != 0.0:
            plug.destructHandle(dataHandle)
            return True
        if y != 0.0:
            plug.destructHandle(dataHandle)
            return True
        if z != 0.0:
            plug.destructHandle(dataHandle)
            return True
        arrayDataHandle.next()

    return False


def fixIt(plug, path):
    # fix most vertices
    cmds.polyMoveVertex(path, lt=(0, 0, 0), nodeState=1, ch=False)
    
    # Sometimes the above comand doesn't fix very small number such as 0.000.....1
    # So manually reset those numbers to 0
    dataHandle = plug.asMDataHandle()
    arrayDataHandle = OpenMaya.MArrayDataHandle(dataHandle)
    while not arrayDataHandle.isDone():
        outputHandle = arrayDataHandle.outputValue()
        outputHandle.set3Float(0.0, 0.0, 0.0)
        arrayDataHandle.next()
    plug.setMDataHandle(dataHandle)
    plug.destructHandle(dataHandle)


def main(fix=False):
    result = []
    
    mSel = OpenMaya.MSelectionList()
    sel = cmds.ls(sl=True, fl=True, long=True)[0]
    mesh = cmds.listRelatives(sel, ad=True, fullPath=True, type="mesh") or []
    
    for i in mesh:
        mSel.add(i)
    
    for num, obj in enumerate(mesh):
        dagPath = mSel.getDagPath(num)
        dagNode = OpenMaya.MFnDagNode(dagPath)
        plug = dagNode.findPlug("pnts", False)
        hasTransform = checkIt(plug)
        
        if hasTransform:
            result.append(dagPath.fullPathName())
            if fix:
                fixIt(plug, dagPath.fullPathName())


if __name__ == "__main__":
    main(fix=False)
