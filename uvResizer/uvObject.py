# -*- coding: utf-8 -*-


from maya.api import OpenMaya
import math
import time


class UVPoint():
    def __init__(self, u, v, index):
        # type: (float, float, int) -> None

        self.u = u
        self.v = v
        self.index = index

    def __eq__(self, other):
        # type: (UVPoint) -> bool

        if isinstance(other, UVPoint):
            return self.index == other.index

    def __hash__(self):
        return id(self.index)


class UVShell():
    def __init__(self, shellIndex):
        # type: (int) -> None

        self.shellIndex = shellIndex
        self.points = []
        self.paths = []

        self.polyArea = 0.0
        self.uvArea = 0.0

    def __eq__(self, other):
        # type: (UVShell) -> bool

        if isinstance(other, UVShell):
            return self.shellIndex == other.shellIndex

    def __hash__(self):
        return id(self.shellIndex)

    def getStrings(self):
        paths = [i.path for i in self.points]
        return paths

    def getShellPivot(self):
        u_sum = 0.0
        v_sum = 0.0
        for p in self.points:
            u_sum += p.u
            v_sum += p.v

        u = u_sum / len(self.points)
        v = v_sum / len(self.points)

        return (u, v)

    def has(self, path):
        # type: (str) -> bool
        """ Check if uv shell has a specific uv point
            Args:
                path: full path uv component

            Returns:
                True if shell has a component
        """

        if path in self.paths:
            return True
        else:
            return False


class UVObject():
    def __init__(self, dagPath, space=OpenMaya.MSpace.kWorld):
        # type: (OpenMaya.MDagPath, OpenMaya.MSpace) -> bool
        """ Get uv shell objects
            Args:
                uvs: List of uv components in full path strings

            Returns:
                None
        """

        self.shells = []
        self.dagPath = dagPath

        t = time.time()

        mesh = OpenMaya.MFnMesh(dagPath)
        nbUvShells, uvShellIds = mesh.getUvShellsIds()

        # Init UV shell
        for shellId in range(nbUvShells):
            shell = UVShell(shellId)
            for n, j in enumerate(uvShellIds):
                id = uvShellIds[n]
                if shellId == id:
                    path = dagPath.fullPathName() + ".map[{}]".format(n)
                    u, v = mesh.getUV(n)
                    p = UVPoint(u, v, n)
                    shell.points.append(p)
                    shell.paths.append(path)

            self.shells.append(shell)

        # Init uv and polygon area for each shell
        polyIter = OpenMaya.MItMeshPolygon(dagPath)

        while not polyIter.isDone():
            shellId = uvShellIds[polyIter.getUVIndex(0)]
            shell = self.shells[shellId]
            polyArea = polyIter.getArea(space)
            uvArea = polyIter.getUVArea()
            shell.polyArea += polyArea
            shell.uvArea += uvArea
            polyIter.next(None)

        print(time.time() - t)

    def getShells(self, uvs):
        # type: (list) -> list
        """Get uv shell objects
            Args:
                uvs: List of uv components in full path strings

            Returns:
                List of uv shell objects
        """

        shellSet = set()

        for i in uvs:
            for shell in self.shells:
                if shell.has(i):
                    shellSet.add(shell)
                    break

        return list(shellSet)

    def scaleShells(self, shells, sourceRatio, keepLayout=False):
        # type: (list, float, bool) -> None
        """Scale uv shells
            Args:
                shells: List of uv shell objects
                sourceRatio: source mesh scale ratio
                keepLayout: keep relative positions to each uv shell

            Returns:
                None
        """

        fnMesh = OpenMaya.MFnMesh(self.dagPath)
        uArray, vArray = fnMesh.getUVs()

        pivot_u = 0.0
        pivot_v = 0.0

        if keepLayout:
            for i in shells:
                u, v = i.getShellPivot()
                pivot_u += u
                pivot_v += v
            pivot_u = pivot_u / len(shells)
            pivot_v = pivot_v / len(shells)

        for shell in shells:
            shellRatio = shell.uvArea / shell.polyArea
            mult = math.sqrt(sourceRatio / shellRatio)
            if not keepLayout:
                pivot_u, pivot_v = shell.getShellPivot()

            for uv in shell.points:
                u = ((uv.u - pivot_u) * mult) + pivot_u
                v = ((uv.v - pivot_v) * mult) + pivot_v
                uArray[uv.index] = u
                vArray[uv.index] = v

        fnMesh.setUVs(uArray, vArray)
        fnMesh.updateSurface()


if __name__ == "__main__":
    pass
