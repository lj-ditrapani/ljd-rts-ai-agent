'''Author:  Lyall Jonathan Di Trapani                                       '''

import ctypes, random
import cdata

cdata.clb.loadMetalPatchLocations.restype = ctypes.py_object
cdata.clb.getMapDimensions.restype = ctypes.py_object
cdata.clb.giveUnit.argtypes = [ctypes.c_int, ctypes.py_object, ctypes.c_int]

gData = {'metalMap': False}         # Global, const data
gridToHeight = 16                   # mult by grid units to get heightMap units
cellWidth = 8                       # cell width
gridToTrue = cellWidth*gridToHeight # mult by grid units to get true coords
fpToTrue = 16                       # Convert footprint units to true coords


def loadMapData(sid):
    global gData
    maxSize = 150
    rawMetalPatches = cdata.clb.loadMetalPatchLocations(sid, maxSize)
    metalPatches = []
    mexFootPrint = cdata.unitDefs['armmex'].footprintX
    offset = (mexFootPrint + 1)/2.0 * fpToTrue
    if len(rawMetalPatches) > maxSize - 1:
        gData['metalMap'] = True
    else:
        for mp in rawMetalPatches:
            metalPatches.append((mp[0] + offset, mp[1], mp[2] + offset))
    gData['metalPatches'] = metalPatches
    htMapDims = cdata.clb.getMapDimensions(sid) # height map xMax, yMax
    gData['gridDims'] = (htMapDims[0]/gridToHeight, htMapDims[1]/gridToHeight)
    print 'gridDims', gData['gridDims']


class Cell:

    def __init__(self, x, z):
        self.x = x                              # Grid coords
        self.z = z                              # Grid coords
        # True coords
        self.topLeft = Point(x * gridToTrue, z * gridToTrue)
        self.enemyGroundUnits = []
        self.enemyAircraft = []
        self.enemyBuilding = None
        self.free = True
        self.metalPatch = False

    def getPossibleBuildSites(self, fpx, fpz):
        yield self.getCenter()
        xStep, zStep = fpx*fpToTrue/2.0, fpz*fpToTrue/2.0
        tl = self.topLeft                       # Top left corner
        tr = Point(tl.x + gridToTrue, tl.z)     # Top right corner
        bl = Point(tl.x, tl.z + gridToTrue)     # Bottom left corner
        br = Point(tr.x, bl.z)                  # Bottom right corner
        yield Point(tl.x + xStep, tl.z + zStep)
        yield Point(tr.x - xStep, tr.z + zStep)
        yield Point(bl.x + xStep, bl.z - zStep)
        yield Point(br.x - xStep, br.z - zStep)

    def getCenter(self):
        offset = gridToTrue/2
        return Point(self.topLeft.x + offset, self.topLeft.z + offset)

    def __str__(self):
        return '({0},{1})'.format(self.x, self.z)


class Point:

    def __init__(self, x, z):
        self.x = x
        self.z = z


class Map:

    def __init__(self, sid):
        self.sid = sid
        self.gData = gData
        xRange, zRange = gData['gridDims']
        grid = []
        for z in range(zRange):
            row = []
            for x in range(xRange):
                row.append(Cell(x, z))
            grid.append(row)
        self.xRange = xRange
        self.zRange = zRange
        self.grid = grid
        if not gData['metalMap']:
            self._setMetalPatchInfo()
        # Direction 'AB' means from A to B
        self.incTable = dict(NE=(1, 1), NW=(-1, 1), SE=(1, -1), SW=(-1, -1))

    def getCell(self, x, z):
        return self.grid[z][x]

    def _setMetalPatchInfo(self):
        c = 0
        maxX, maxZ = gData['gridDims'][0] - 1, gData['gridDims'][1] - 1
        for mp in gData['metalPatches']:
            cell = self.getCellContainingPoint(mp)
            cell.metalPatch = True
            cell.metalPatchLoc = mp
            fp = cdata.unitDefs['armmex'].footprintX
            margin = fp / 2.0 * fpToTrue
            x, z = cell.x, cell.z
            x1 = x * gridToTrue
            z1 = z * gridToTrue
            x2 = x1 + 1 * gridToTrue
            z2 = z1 + 1 * gridToTrue
            mpx, mpz = mp[0], mp[2]
            tl = tr = bl = br = 0
            '''if on a map where patches are right on edge, may need to replace
            the <= >= with < >, since it will try to index outside the bounds
            of the map'''
            if x > 0 and mpx <= x1 + margin:
                self.getCell(x - 1, z).free = False
                tl += 1
                bl += 1
            if x < maxX and mpx >= x2 - margin:
                self.getCell(x + 1, z).free = False
                tr += 1
                br += 1
            if z > 0 and mpz <= z1 + margin:
                self.getCell(x, z - 1).free = False
                tl += 1
                tr += 1
            if z < maxZ and mpz <= z2 - margin:
                self.getCell(x, z + 1).free = False
                bl += 1
                br += 1
            if tl == 2:
                self.getCell(x - 1, z - 1).free = False
            if tr == 2:
                self.getCell(x + 1, z - 1).free = False
            if bl == 2:
                self.getCell(x - 1, z + 1).free = False
            if br == 2:
                self.getCell(x + 1, z + 1).free = False

    def getCellContainingPoint(self, point):
        x, y, z = point     # True units, convert to grid units
        # Compute grid coords from true x and z of point
        gridx = int(x / gridToTrue)
        gridz = int(z / gridToTrue)
        # If grid x or z is out of bounds, clamp to within grid dimensions
        xWidth, zWidth = gData['gridDims']
        if gridx < 0:
            gridx = 0
        if gridx >= xWidth:
            gridx = xWidth - 1
        if gridz < 0:
            gridz = 0
        if gridz >= zWidth:
            gridz = zWidth - 1
        return self.getCell(gridx, gridz)

    def generateCells(self, origine):
        cell = self.getCellContainingPoint(origine)
        return self.generateCellsGridCoords(cell.x, cell.z)

    def generateCellsGridCoords(self, x, z):
        yield self.getCell(x, z)
        layer = 1
        while(True):
            for cell in self._generateCellsForLayer(layer, x, z):
                yield cell
            layer += 1

    def iterateCells(self):
        for row in self.grid:
            for cell in row:
                yield cell

    def _generateCellsForLayer(self, layer, x, z):
        cells = []
        incTable = dict(N=(0, -1), S=(0, 1), W=(-1, 0), E=(1, 0))
        pointTable = {}
        directions = ['N', 'S', 'W', 'E']
        random.shuffle(directions)
        for dir in directions:
            xInc, zInc = incTable[dir]
            p = Point(x + layer * xInc, z + layer * zInc)
            pointTable[dir] = p
            if self.inBounds(p):
                cells.append(self.getCell(p.x, p.z))
        # Direction 'AB' means from A to B
        directions = ['NE', 'SW', 'NW', 'SE']
        random.shuffle(directions)
        for dir in directions:
            startPoint = pointTable[dir[0]]
            endPoint = pointTable[dir[1]]
            cells += self._getDiag(dir, startPoint, endPoint)
        if len(cells) == 0:
            raise StopIteration
        return cells

    def _getDiag(self, dir, startPoint, endPoint):
        cells = []
        xInc, zInc = self.incTable[dir]
        p = startPoint
        while(True):
            p = Point(p.x + xInc, p.z + zInc)
            if p.x == endPoint.x and p.z == endPoint.z:
                return cells
            if self.inBounds(p):
                cells.append(self.getCell(p.x, p.z))

    def inBounds(self, point):
        x, z = point.x, point.z
        return x >= 0 and z >= 0 and x < self.xRange and z < self.zRange

    def getFacing(self, x, z):
        xMax, zMax = gData['gridDims']
        toEdge = [0] * 4
        toEdge[0] = zMax - z    # South
        toEdge[1] = xMax - x    # East
        toEdge[2] = z           # North
        toEdge[3] = x           # West
        v = max(toEdge)
        for i in range(4):
            if v == toEdge[i]:
                return i
