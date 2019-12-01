import os
import json
from maya import OpenMaya
from maya import cmds
from PySide2 import QtWidgets, QtCore


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

def createProfile(data):
    """

    Returns (str): path to the new curve

    """

    profile = cmds.curve(
        periodic=True,
        p=data,
        degree=1,
        k=range(len(data))
    )

    return profile
    

class Window(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.setWindowTitle("rope")
        self.setWindowFlags(QtCore.Qt.Window)
        self.resize(600, 150)

        self.le = QtWidgets.QLineEdit()
        self.loadButton = QtWidgets.QPushButton("Load")
        self.loadButton.clicked.connect(self.load)
        self.cb = QtWidgets.QComboBox()
        self.bn = QtWidgets.QPushButton("Make")
        self.bn.clicked.connect(self.make)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.le)
        layout.addWidget(self.loadButton)
        layout.addWidget(self.cb)
        layout.addWidget(self.bn)

        self.setLayout(layout)

        self.data = None

    def load(self):
        path = self.le.text()
        if os.path.exists(path):
            with open(path, 'rb') as data:
                self.data = json.load(data)
                keys = [k for k in self.data]
                self.cb.addItems(keys)
    
    def make(self):
        sel = cmds.ls(sl=True, fl=True, long=True)
        for i in sel:
            cmds.select(i, r=True)

            typ = self.cb.currentText()
            data = self.data[typ]

            fnCurve = getFnCurve()
            matrix = getFirstCVMatrix(fnCurve)

            p = createProfile(data)
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

            cmds.addAttr(newRopeName, shortName='tw', longName='twist', at='short', keyable=True)
            cmds.addAttr(newRopeName, shortName='tsx', longName='tubeScaleX', at='float', keyable=True, defaultValue=1.0)
            cmds.addAttr(newRopeName, shortName='tsy', longName='tubeScaleY', at='float', keyable=True, defaultValue=1.0)
            cmds.addAttr(newRopeName, shortName='tsz', longName='tubeScaleZ', at='float', keyable=True, defaultValue=1.0)
            cmds.addAttr(newRopeName, shortName='div', longName='division', at='long', keyable=True, defaultValue=64)

            cmds.connectAttr(newRopeName + ".division", tesse + ".vNumber")

            md = cmds.shadingNode("multiplyDivide", asUtility=True)
            cmds.connectAttr(newRopeName + ".twist", md + ".input1.input1X")
            cmds.setAttr(md + ".input2X", 360)

            cmds.connectAttr(md + ".outputX", extrudeNode + ".rotation")
            cmds.connectAttr(newRopeName + ".tubeScaleX", p + ".scaleX")
            cmds.connectAttr(newRopeName + ".tubeScaleY", p + ".scaleY")
            cmds.connectAttr(newRopeName + ".tubeScaleZ", p + ".scaleZ")       

            cmds.select(d=True)


if __name__ == "__main__":
    w = Window()
    w.show()