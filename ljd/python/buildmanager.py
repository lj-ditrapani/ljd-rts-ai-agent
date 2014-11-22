import ctypes, cdata, econmanager
cdata.clb.canBuildHere.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_float,
                                   ctypes.c_float, ctypes.c_int]
cdata.clb.buildStruct.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                  ctypes.c_float, ctypes.c_float, ctypes.c_int]


MAX_CONS = 7
MAX_DEFENSE = 18
MIN_DEFENSE = 11


class BuildManager:

    def __init__(self, sid, strategy, gMap, defenseManager):
        self.sid = sid
        self.defenseManager = defenseManager
        self.gMap = gMap
        self.econManager = econmanager.EconManager(sid, strategy, gMap)
        self.constructionCell = None
        self.buildingCells = {}
        self.consCount = 0
        self.consLimit = False
        self.defenseCount = 0
        self.defenseLimit = False

    def update(self, frame):
        self.econManager.update(frame)

    def buildingCreated(self, unit, unitType):
        self.buildingCells[unit.unitId] = self.constructionCell

    def checkBuildingCells(self, unitId):
        cell = self.buildingCells.pop(unitId, None)
        if not cell is None:
            cell.free = True

    def buildingFinished(self, unit, unitType):
        self.econManager.buildingFinished(unit, unitType)
        if unitType == 'factory':
            self.factoryIdle(unit)

    def comFinished(self, com):
        self.com = com
        self.comIdle()

    def consFinished(self):
        self.consCount += 1
        if self.consCount >= MAX_CONS:
            self.consLimit = True

    def defenseFinished(self):
        self.defenseCount += 1
        if self.defenseCount >= MAX_DEFENSE:
            self.defenseLimit = True

    def factoryIdle(self, factory):
        unitToBuild = self.econManager.factoryIdle(factory, self.consLimit)
        if unitToBuild == 'combatUnit':
            targetDef = self.defenseManager.nextUnitToBuild()
            self.econManager.updateUnitsBucket(targetDef.mCost)
        elif unitToBuild == 'consUnit':
            targetDef = self.econManager.getConsUnitDef()
        cdata.clb.buildUnit(self.sid, factory.unitId, targetDef.defId)
        if not self.econManager.comBuilding:
            self.comIdle()

    def comIdle(self):
        order, param = self.econManager.comIdle(self.com, self.defenseLimit)
        if order == 'build':
            self.econManager.comBuilding = True
            self._build(self.com, param)
        elif order == 'guard':
            self.econManager.comBuilding = False
            cdata.clb.guardUnit(self.sid, self.com.unitId, param.unitId)

    def consIdle(self, cons):
        cdata.clb.guardUnit(self.sid, cons.unitId, self.com.unitId)

    def buildingDestroyed(self, unit, unitType):
        self.econManager.buildingDestroyed(unit, unitType)

    def consDestroyed(self):
        self.consCount -= 1
        if self.consCount < MAX_CONS:
            self.consLimit = False

    def defenseDestroyed(self):
        self.defenseCount -= 1
        if self.defenseCount <= MIN_DEFENSE:
            self.defenseLimit = False

    def _build(self, cons, structDef):
        '''
        cons:   construction unit
        structDef: unit definition of building to construct
        '''
        pos = cdata.clb.getUnitPosition(self.sid, cons.unitId)
        for cell in self.gMap.generateCells(pos):
            if not cell.free:
                continue
            # if normal map & trying to build mex, it must be on a metal patch
            if ((not self.gMap.gData['metalMap']) and 
                    structDef.name == 'armmex'):
                if cell.metalPatch:
                    mp = cell.metalPatchLoc
                    self._buildHere(cons, structDef, mp[0], mp[2], cell)
                    break               # Go to end
                else:
                    continue
            # If not building a mex and metal patch on cell, skip cell
            if cell.metalPatch:
                continue
            buildable, pos = self._canBuildHere(cell, structDef)
            if buildable:
                self._buildHere(cons, structDef, pos.x, pos.z, cell)
                break                   # Go to end

    def _buildHere(self, cons, structDef, x, z, cell):
        facing = self.gMap.getFacing(cell.x, cell.z)
        cdata.clb.buildStruct(self.sid, cons.unitId, 
            structDef.defId, x, z, facing)
        self.constructionCell = cell
        cell.free = False

    def _canBuildHere(self, cell, structDef):
        facing = self.gMap.getFacing(cell.x, cell.z)
        fpx, fpz = structDef.footprintX, structDef.footprintZ
        for pos in cell.getPossibleBuildSites(fpx, fpz):
            if cdata.clb.canBuildHere(self.sid, structDef.defId, 
                                      pos.x, pos.z, facing):
                return True, pos
        return False, False
