""" duplicate along curve """

import random

from maya import OpenMaya
from maya import OpenMayaUI
from maya import cmds
from PySide2 import QtWidgets, QtCore
import shiboken2


def getMayaWindow():
    ptr = OpenMayaUI.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(long(ptr), QtWidgets.QMainWindow)


class GUI(QtWidgets.QWidget):
    """ doc string """

    def __init__(self, parent=getMayaWindow()):
        super(GUI, self).__init__(parent)

        self.windowName = "Dupcalite along curve"

        if cmds.window(self.windowName, q=True, ex=True):
            cmds.deleteUI(self.windowName)

        self.setObjectName(self.windowName)

        self.setWindowTitle(self.windowName)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.surfaceLE = QtWidgets.QLineEdit("|test")
        self.surfaceSetButton = QtWidgets.QPushButton("set surface")
        self.surfaceSetButton.clicked.connect(self.setSurface)
        self.rivetLE = QtWidgets.QLineEdit("|rivet_GEP")
        self.rivetSetButton = QtWidgets.QPushButton("set rivet")
        self.rivetSetButton.clicked.connect(self.setRivet)
        self.intervalLE = QtWidgets.QLineEdit("0.2")
        self.randomLE = QtWidgets.QLineEdit("0.005")
        self.doButton = QtWidgets.QPushButton("Do it")
        self.doButton.clicked.connect(self.doIt)

        columnLayout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom)
        columnLayout.addWidget(QtWidgets.QLabel("Surface"))
        columnLayout.addWidget(self.surfaceSetButton)
        columnLayout.addWidget(self.surfaceLE)
        columnLayout.addWidget(QtWidgets.QLabel("Rivet"))
        columnLayout.addWidget(self.rivetSetButton)
        columnLayout.addWidget(self.rivetLE)
        columnLayout.addWidget(QtWidgets.QLabel("Interval"))
        columnLayout.addWidget(self.intervalLE)
        columnLayout.addWidget(QtWidgets.QLabel("Randomness"))
        columnLayout.addWidget(self.randomLE)
        columnLayout.addWidget(self.doButton)

        self.setLayout(columnLayout)

    def doIt(self):
        """ just do it """

        surface = self.surfaceLE.text()
        rivet = self.rivetLE.text()
        interval = float(self.intervalLE.text())
        randomness = float(self.randomLE.text())

        duplicateAloneCurves(surface, rivet, interval, randomness)

    def setSurface(self):
        """ set snap target object """

        sel = cmds.ls(sl=True, fl=True, long=True)[0]
        self.surfaceLE.setText(sel)

    def setRivet(self):
        """ set rivet object to duplicate """

        sel = cmds.ls(sl=True, fl=True, long=True)[0]
        self.rivetLE.setText(sel)


def duplicateAloneCurves(surface, rivet, interval, randomness):
    """ duplicate alone curve """

    cmds.undoInfo(openChunk=True)

    sel = OpenMaya.MSelectionList()
    OpenMaya.MGlobal.getActiveSelectionList(sel)
    numSelected = sel.length()

    dagPath = OpenMaya.MDagPath()

    # Setup snap target surface
    surfaceDagPath = OpenMaya.MDagPath()
    surfaceSelection = OpenMaya.MSelectionList()
    surfaceSelection.add(surface)
    surfaceSelection.getDagPath(0, surfaceDagPath)
    surfaceFnMesh = OpenMaya.MFnMesh(surfaceDagPath)

    # iterate selected curves
    for s in range(numSelected):
        sel.getDagPath(s, dagPath)

        fnCurve = OpenMaya.MFnNurbsCurve(dagPath)
        point = OpenMaya.MPoint()
        start = 0.0

        N = OpenMaya.MVector()
        length = fnCurve.length()
        numRivets = int(length / interval)

        rivets = []

        # Closest Point
        P = OpenMaya.MPoint()

        for i in range(numRivets):
            param = fnCurve.findParamFromLength(start)
            fnCurve.getPointAtParam(param, point)

            # randomize point
            randX = 1.0 + (random.uniform(-0.1, 0.1) * randomness)
            randY = 1.0 + (random.uniform(-0.1, 0.1) * randomness)
            randZ = 1.0 + (random.uniform(-0.1, 0.1) * randomness)
            point.x = point.x * randX
            point.y = point.y * randY
            point.z = point.z * randZ

            # Tangent vector
            T = fnCurve.tangent(param)

            # Normal vector
            surfaceFnMesh.getClosestPointAndNormal(point, P, N, OpenMaya.MSpace.kWorld)

            # Bi-tangent vector
            B = N ^ T

            # Normalize vectors
            T.normalize()
            N.normalize()
            B.normalize()

            # 4x4 transformation matrix
            M = [T.x, T.y, T.z, 0,
                 N.x, N.y, N.z, 0,
                 B.x, B.y, B.z, 0,
                 P.x, P.y, P.z, 1]

            # Duplicate rivets and apply transformations
            obj = cmds.duplicate(rivet)[0]
            cmds.xform(obj, matrix=M)

            start += interval

            rivets.append(obj)

        cmds.group(rivets)

    cmds.undoInfo(closeChunk=True)


if __name__ == "__main__":
    w = GUI()
    w.show()

