from maya import OpenMaya
from maya import cmds


def getFnCurve():
    """

    Returns:
        fnCurve (MfnNurbsCurve) :

    """
    mSel = OpenMaya.MSelectionList()
    mDagPath = OpenMaya.MDagPath()

    OpenMaya.MGlobal.getActiveSelectionList(mSel)

    mSel.getDagPath(0, mDagPath)

    fnCurve = OpenMaya.MFnNurbsCurve(mDagPath)
    return fnCurve


def getFirstCVMatrix(fnCurve):
    """

    Args:
        fnCurve (MFnNurbsCurve): nurbs curve fuction mesh

    Returns:
        matrix (list): 16 numbers of list

    """

    firstCV = OpenMaya.MPoint()
    fnCurve.getCV(0, firstCV, OpenMaya.MSpace.kWorld)

    utils = OpenMaya.MScriptUtil()

    doublePointer = utils.asDoublePtr()
    fnCurve.getParamAtPoint(firstCV, doublePointer)

    param = utils.getDouble(doublePointer)

    normal = fnCurve.normal(param, OpenMaya.MSpace.kWorld)
    tangent = fnCurve.tangent(param, OpenMaya.MSpace.kWorld)
    biTangent = normal ^ tangent

    matrix = [
        normal.x, normal.y, normal.z, 0,
        tangent.x, tangent.y, tangent.z, 0,
        biTangent.x, biTangent.y, biTangent.z, 0,
        firstCV.x, firstCV.y, firstCV.z, 1
    ]

    return matrix


def ropeExtrude(profileCurve, pathCurve):
    """

    Args:
        profileCurve:
        pathCurve:

    Returns:

    """
    ext = cmds.extrude(
        profileCurve,
        pathCurve,
        ch=True,
        rn=False,
        po=1,
        et=2,
        ucp=0,
        fpt=1,
        upn=1,
        scs=True,
        rotation=-10000,
        scale=1,
        rsp=1
    )

    return ext

def createProfile():
    """

    Returns (str): path to the new curve

    """
    pp = [
        [-0.6859763264656067, 0.0, -0.005694257095456123],
        [-0.7646133303642273, 0.0, 0.031250569969415665],
        [-0.9004402160644531, 0.0, 0.48873579502105713],
        [-0.5552256107330322, 0.0, 0.8969211578369141],
        [-0.014898685738444328, 0.0, 0.9972710013389587],
        [0.3511762022972107, 0.0, 0.685110867023468],
        [0.3380568027496338, 0.0, 0.5969200134277344],
        [0.40937042236328125, 0.0, 0.6465492248535156],
        [0.8734776973724365, 0.0, 0.5354361534118652],
        [1.054369330406189, 0.0, 0.03237885609269142],
        [0.8711113929748535, 0.0, -0.4857328534126282],
        [0.41773533821105957, 0.0, -0.6466829776763916],
        [0.3479194939136505, 0.0, -0.591225802898407],
        [0.35524284839630127, 0.0, -0.6777997612953186],
        [0.026962488889694214, 0.0, -1.0241718292236328],
        [-0.49914371967315674, 0.0, -0.9293000102043152],
        [-0.8562126159667969, 0.0, -0.5115381479263306],
        [-0.7689114809036255, 0.0, -0.03842794522643089],
    [-0.6859763264656067, 0.0, -0.005694257095456123]]
    print range(len(pp))

    profile = cmds.curve(
        periodic=True,
        p=pp,
        degree=1,
        k=range(len(pp))
    )

    return profile
    
    
if __name__ == "__main__":
    fnCurve = getFnCurve()
    matrix = getFirstCVMatrix(fnCurve)

    p = createProfile()
    cmds.xform(p, m=matrix)

    path = fnCurve.fullPathName()

    ext = ropeExtrude(p, path)

    newSurface = ext[0]
    newSurfaceShape = cmds.listRelatives(newSurface, shapes=True)[0]
    extrudeNode= ext[1]
    tesse = cmds.listConnections(newSurfaceShape, type="nurbsTessellate")[0]

    cmds.setAttr(extrudeNode + ".rotation", 1080)
    cmds.setAttr(tesse + ".polygonType", 1)
    cmds.setAttr(tesse + ".format", 2)
    cmds.setAttr(tesse + ".uNumber", 1)
    cmds.setAttr(tesse + ".vNumber", 32)

    ctrlGrp = cmds.group(w=True, em=True)
    ropeGrpName = "rope_GRP"
    newRopeName = cmds.rename(ctrlGrp, ropeGrpName)

    cmds.parent(p, newRopeName)
    cmds.parent(newSurface, newRopeName)

    cmds.addAttr(
        newRopeName,
        shortName='tw',
        longName='twist', 
        at='short',
        keyable=True)
    cmds.addAttr(
        newRopeName,
        shortName='w',
        longName='width',
        at='float',
        keyable=True)
    cmds.addAttr(
        newRopeName,
        shortName='div',
        longName='division',
        at='long',
        keyable=True,
        defaultValue=64)

    cmds.connectAttr(newRopeName + ".division", tesse + ".vNumber")
    # cmds.connectAttr(newRopeName + ".width", tesse + ".vNumber")

    md = cmds.shadingNode("multiplyDivide", asUtility=True)
    cmds.connectAttr(newRopeName + ".twist", md + ".input1.input1X")
    cmds.setAttr(md + ".input2X", 360)

    cmds.connectAttr(md + ".outputX", extrudeNode + ".rotation")
