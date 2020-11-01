# -*- coding: utf-8 -*-

""" Snap selected UVs to closest target UVs

Requirement:
    kdtree: Copyright (c) Stefan Kögl <stefan@skoegl.net>
    https://github.com/stefankoegl/kdtree

"""

from maya.api import OpenMaya
from maya import cmds
import kdtree
import time
import re


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


def main(snapTargetMeshPath=None):
    # type: (str) -> None

    if snapTargetMeshPath is None:
        cmds.error("Target mesh not speficied")

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
    main("source1")
    et = time.time() - t
    print(et)
