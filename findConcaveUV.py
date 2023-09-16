from maya.api import OpenMaya
from maya import cmds


def getTriangleArea(Ax, Ay, Bx, By, Cx, Cy):
    return (Ax * (By - Cy) + Bx * (Cy - Ay) + Cx * (Ay - By)) / 2


def main():
    sel = OpenMaya.MGlobal.getActiveSelectionList()
    dagPath = sel.getDagPath(0)

    itPoly = OpenMaya.MItMeshPolygon(dagPath)

    badUVs = []

    while not itPoly.isDone():
        _, ids = itPoly.getTriangles()
        numVerts = itPoly.polygonVertexCount()
        for i in range(numVerts):
            p1 = i
            p2 = i + 1
            if p2 > numVerts-1:
                p2 -= numVerts
            p3 = i + 2
            if p3 > numVerts-1:
                p3 -= numVerts
            uv = [p1, p2, p3]
            b = [itPoly.getUV(i) for i in uv]

            area = getTriangleArea(
                b[0][0],
                b[0][1],
                b[1][0],
                b[1][1],
                b[2][0],
                b[2][1])

            if area <= 0.00000000001:
                badUVs.append(itPoly.index())

        itPoly.next()

    badFaces = [dagPath.fullPathName() + ".f[{}]".format(i) for i in badUVs]

    cmds.select(badFaces, r=True)


if __name__ == "__main__":
    main()
