from maya.api import OpenMaya
from maya import cmds
import time

class UVShell():
    def __init__(self, shellIndex, dagPath):
        self.uvIndices = []
        self.shellIndex = shellIndex
        self.dagPath = dagPath
        self.fullPathList = []
    
    def setPath(self):
        for i in self.uvIndices:
            path = self.dagPath + ".map[%s]" % i
            self.fullPathList.append(path)
                 
def selectTextureBorderEdges(obj):
    sel = OpenMaya.MSelectionList()
    sel.add(obj)
    dagPath = sel.getDagPath(0)
    fnMesh = OpenMaya.MFnMesh(dagPath)
    nbUvShells, uvShellIds = fnMesh.getUvShellsIds()
    uvShells = [UVShell(i, dagPath.fullPathName()) for i in range(nbUvShells)]

    for n, i in enumerate(uvShellIds):
        uvShells[i].uvIndices.append(n)
        
    for i in uvShells:
        i.setPath()

    edges = []

    for s in uvShells:
        cmds.select(s.fullPathList[0], r=True)
        cmds.ConvertSelectionToUVShellBorder()
        cmds.ConvertSelectionToVertices()
        cmds.ConvertSelectionToContainedEdges()
        shellBorderEdges = cmds.ls(sl=True, fl=True, long=True)
        edges.extend(shellBorderEdges)
        cmds.select(d=True)

    return list(set(edges))


def main():
    sel = cmds.ls(sl=True, fl=True, long=True)
    for i in sel:
        edges = selectTextureBorderEdges(i)
        cmds.select(edges, r=True)
        cmds.DetachEdgeComponent(edges)
        cmds.select(i, r=True)
        cmds.SeparatePolygon()

    cmds.select(sel, r=True)

if __name__ == "__main__":
    t = time.time()
    main()
    print time.time() - t
