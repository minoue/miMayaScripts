# -*- coding: utf-8 -*-

""" Snap selected UVs to closest target UVs

Requirement:
    kdtree: Copyright (c) Stefan Kögl <stefan@skoegl.net>
    https://github.com/stefankoegl/kdtree

"""

from PySide2 import QtWidgets, QtCore
from maya.api import OpenMaya
from maya import OpenMayaUI
from maya import cmds
import shiboken2
import time
import re

try:
    import kdtree
except ImportError:
    raise ImportError(
        "KDTree is not installed. Download and install KDTree lib")


def createTree(mesh):
    # type: (OpenMaya.MFnMesh) -> kdtree.KDNode

    uArray, vArray = mesh.getUVs()
    numUVs = mesh.numUVs()
    points = [(uArray[i], vArray[i]) for i in range(numUVs)]
    tree = kdtree.create(points, dimensions=2)

    return tree


def getMesh(path):
    # type: (str) -> OpenMaya.MFnMesh

    sel = OpenMaya.MSelectionList()
    sel.add(path)
    dagPath = sel.getDagPath(0)
    mesh = OpenMaya.MFnMesh(dagPath)
    return mesh


def getMayaWindow():
    ptr = OpenMayaUI.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(long(ptr), QtWidgets.QMainWindow)


class Window(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        self.setWindowTitle("UV snap")
        self.setWindowFlags(QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.LE = QtWidgets.QLineEdit()
        self.LE.setEnabled(False)
        self.setBtn = QtWidgets.QPushButton("Set")
        self.setBtn.clicked.connect(self.setObject)
        self.snapBtn = QtWidgets.QPushButton("Snap")
        self.snapBtn.clicked.connect(self.snapIt)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.LE)
        layout.addWidget(self.setBtn)
        layout.addWidget(self.snapBtn)
        self.setLayout(layout)

    def setObject(self):

        sel = cmds.ls(sl=True, fl=True, long=True)

        if sel:
            self.LE.setText(sel[0])

    def snapIt(self):

        sel = cmds.ls(sl=True, fl=True)

        if not sel:
            cmds.warning("Nothing is selected")
            return

        componentType = sel[0].split(".")[-1][0:3]
        if not componentType == "map":
            cmds.warning("UVs are selected")
            return

        snapTargetMeshPath = self.LE.text()

        sourceMesh = getMesh(snapTargetMeshPath)
        sourceTree = createTree(sourceMesh)

        sel = OpenMaya.MGlobal.getActiveSelectionList()
        dagPath = sel.getDagPath(0)

        mesh = OpenMaya.MFnMesh(dagPath)
        uArray, vArray = mesh.getUVs()

        sel = cmds.ls(sl=True, fl=True, long=True)

        for i in sel:
            index = int(re.findall(r'\d+', i)[-1])
            uv = cmds.polyEditUV(i, q=True)
            nn = sourceTree.search_nn(uv)
            data = nn[0].data
            uArray[index] = data[0]
            vArray[index] = data[1]

        mesh.setUVs(uArray, vArray)


if __name__ == "__main__":
    t = time.time()
    w = Window(getMayaWindow())
    w.show()
    et = time.time() - t
    print(et)
