# -*- coding: utf-8 -*-

"""
Requirements: * https://github.com/mottosso/apiundo
              * uvObject.py
"""

from PySide2 import QtWidgets, QtCore
from maya.api import OpenMaya
from maya import OpenMayaUI
from maya import cmds

import shiboken2
import apiundo
import math
import uvClass

try:
    # For python3
    from importlib import reload
except ImportError:
    pass


reload(uvClass)


__author__ = 'Michitaka Inoue'
__license__ = '{license}'
__version__ = '1.0.0}'


def getMayaWindow():
    ptr = OpenMayaUI.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(long(ptr), QtWidgets.QMainWindow)


class Mesh(object):
    def __init__(self, dagPath, uArray, vArray):
        self.dagPath = dagPath
        self.uArray = uArray
        self.vArray = vArray


class Window(QtWidgets.QDialog):

    def closeExistingWindow(self):
        """ Close window if exists """

        for qt in QtWidgets.QApplication.topLevelWidgets():
            try:
                if qt.__class__.__name__ == self.__class__.__name__:
                    qt.close()
            except Exception:
                pass

    def __init__(self, parent=getMayaWindow()):

        self.closeExistingWindow()

        super(Window, self).__init__(parent)

        self.setWindowTitle("UV Resizer")
        self.setWindowFlags(QtCore.Qt.Window)
        self.resize(300, 100)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.setBtn = QtWidgets.QPushButton("Set reference mesh")
        self.le = QtWidgets.QLineEdit()
        self.le.setEnabled(False)

        checkBoxLayout = QtWidgets.QHBoxLayout()
        self.keepCheckBox = QtWidgets.QCheckBox("Keep layout")
        self.spaceCheckBox = QtWidgets.QCheckBox('World space')
        checkBoxLayout.addWidget(self.keepCheckBox)
        checkBoxLayout.addWidget(self.spaceCheckBox)

        self.spaceCheckBox.setChecked(True)
        self.btn = QtWidgets.QPushButton("Scale it")
        self.btn.clicked.connect(self.scaleUVs)
        self.setBtn.clicked.connect(self.setObj)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.setBtn)
        layout.addWidget(self.le)
        layout.addLayout(checkBoxLayout)
        layout.addWidget(self.btn)

        self.setLayout(layout)

        self.history = []

    def setObj(self):
        sel = cmds.ls(sl=True, fl=True, long=True)
        if sel:
            self.le.setText(sel[0])

    def scaleUVs(self):

        source = self.le.text()

        sel = cmds.ls(sl=True, fl=True, long=True)

        if not sel:
            cmds.warning("Nothing is selected")
            return

        if "." in sel[0]:
            mode = "components"
        else:
            mode = "object"

        if self.spaceCheckBox.isChecked():
            sourceRatio = getRatio(source, 'world')
        else:
            sourceRatio = getRatio(source, 'local')

        self.doIt(sourceRatio, mode)

        apiundo.commit(undo=self.undoIt, redo=self.doIt)

    def doIt(self, sourceRatio, mode):
        # type: (float) -> None

        mSel = OpenMaya.MGlobal.getActiveSelectionList()
        cmdsSel = cmds.ls(sl=True, fl=True, long=True)

        if mode == "object":
            uCenter, vCenter = getScalePivot(cmdsSel)

            self.history = []

            # Calculate ratio for all selected
            ratio_for_all = 0.0
            for i in cmdsSel:
                if self.spaceCheckBox.isChecked():
                    ratio_for_all += getRatio(i, 'world')
                else:
                    ratio_for_all += getRatio(i, 'local')

            ratio_for_all = ratio_for_all / len(cmdsSel)
            mult_for_all = math.sqrt(sourceRatio / ratio_for_all)

            for i in range(mSel.length()):
                dagPath = mSel.getDagPath(i)
                mesh = OpenMaya.MFnMesh(dagPath)
                uArray, vArray = mesh.getUVs()
                copyUarray = OpenMaya.MFloatArray(uArray)
                copyVarray = OpenMaya.MFloatArray(vArray)

                # Restore data for undo
                oldMesh = Mesh(dagPath, copyUarray, copyVarray)
                self.history.append(oldMesh)

                if self.keepCheckBox.isChecked():
                    mult = mult_for_all
                else:
                    # Re-calcurate pivot for each object

                    uCenter, vCenter = getScalePivot([dagPath.fullPathName()])
                    if self.spaceCheckBox.isChecked():
                        singleRatio = getRatio(dagPath.fullPathName(), 'world')
                    else:
                        singleRatio = getRatio(dagPath.fullPathName(), 'local')

                    mult = math.sqrt(sourceRatio / singleRatio)

                for j in range(mesh.numUVs()):
                    u_new = ((uArray[j] - uCenter) * mult) + uCenter
                    v_new = ((vArray[j] - vCenter) * mult) + vCenter
                    uArray[j] = u_new
                    vArray[j] = v_new

                mesh.setUVs(uArray, vArray)
                mesh.updateSurface()

        elif mode == "components":
            print("components selection mode")
            dagPath = mSel.getDagPath(0)
            dagPath.pop(1)

            # Restore data for undo
            mesh = OpenMaya.MFnMesh(dagPath)
            uArray, vArray = mesh.getUVs()
            copyUarray = OpenMaya.MFloatArray(uArray)
            copyVarray = OpenMaya.MFloatArray(vArray)
            oldMesh = Mesh(dagPath, copyUarray, copyVarray)
            self.history.append(oldMesh)

            if self.spaceCheckBox.isChecked():
                uvObj = uvClass.UVObject(dagPath)
            else:
                uvObj = uvClass.UVObject(dagPath, OpenMaya.MSpace.kObject)

            selectedShells = uvObj.getShells(cmdsSel)

            if self.keepCheckBox.isChecked():
                uvObj.scaleShells(selectedShells, sourceRatio, True)
            else:
                uvObj.scaleShells(selectedShells, sourceRatio)
        else:
            pass

    def undoIt(self, *args):
        for i in self.history:
            fnMesh = OpenMaya.MFnMesh(i.dagPath)
            fnMesh.setUVs(i.uArray, i.vArray)
            fnMesh.updateSurface()


def getScalePivot(objs):
    # type: (list) -> tuple

    xMin = []
    xMax = []
    yMin = []
    yMax = []

    for i in objs:
        bbox = cmds.polyEvaluate(i, boundingBox2d=True)
        xMin.append(bbox[0][0])
        xMax.append(bbox[0][1])
        yMin.append(bbox[1][0])
        yMax.append(bbox[1][1])

    xMin = min(xMin)
    xMax = max(xMax)
    yMin = min(yMin)
    yMax = max(yMax)

    x = (xMax + xMin) / 2
    y = (yMax + yMin) / 2

    return (x, y)


def getRatio(path, space):
    # type: (str, str) -> float

    polyArea = 0.0

    if space == 'world':
        polyArea = cmds.polyEvaluate(path, worldArea=True)
    elif space == 'local':
        polyArea = cmds.polyEvaluate(path, area=True)
    else:
        cmds.error("wrong space")

    uvArea = 0.0

    sel = OpenMaya.MSelectionList()
    sel.add(path)

    dagPath = sel.getDagPath(0)

    polyIter = OpenMaya.MItMeshPolygon(dagPath)

    while not polyIter.isDone():
        uvArea += polyIter.getUVArea()
        polyIter.next(None)

    ratio = uvArea / polyArea

    return ratio


def main():
    w = Window()
    w.show()
    w.raise_()
    w.activateWindow()


if __name__ == "__main__":
    main()