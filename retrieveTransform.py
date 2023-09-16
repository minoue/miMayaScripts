from maya import cmds
import numpy


def main():
    sel = cmds.ls(os=True, fl=True, long=True)
    obj = sel[0].split(".")[0]

    origin_pos = cmds.pointPosition(sel[0], world=True)
    x_pos = cmds.pointPosition(sel[1], world=True)
    y_pos = cmds.pointPosition(sel[2], world=True)
    piv = cmds.xform(obj, q=True, piv=True, ws=True)[:3]

    OP = numpy.array(origin_pos)
    X = numpy.array(x_pos)
    Y = numpy.array(y_pos)
    PIV = numpy.array(piv)

    OX = X - OP
    OY = Y - OP
    OZ = numpy.cross(OX, OY)

    OX = OX/numpy.linalg.norm(OX)
    OY = OY/numpy.linalg.norm(OY)
    OZ = OZ/numpy.linalg.norm(OZ)

    OX = numpy.append(OX, 0)
    OY = numpy.append(OY, 0)
    OZ = numpy.append(OZ, 0)
    PIV = numpy.append(PIV, 1)

    M_tmp = numpy.matrix([OX, OY, OZ, PIV])
    M_inv = numpy.linalg.inv(M_tmp)

    toOrigin = M_inv.flatten().tolist()[0]
    toPosition = M_tmp.flatten().tolist()[0]

    cmds.xform(obj, m=toOrigin, ws=True)
    cmds.select(obj, r=True)
    cmds.makeIdentity(apply=True, t=True, r=True, s=True, n=False)
    cmds.xform(obj, matrix=toPosition, ws=True)


if __name__ == "__main__":
    main()
