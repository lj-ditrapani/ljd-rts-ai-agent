'''Author:  Lyall Jonathan Di Trapani                                       '''

import cdata

buildingTypes = ['econBuilding', 'defenseBuilding', 'factory']

class Unit:

    def __init__(self, unitId, defi):
        self.unitId = unitId
        self.defi = defi
        self.group = None


class UnitManager:

    def __init__(self, sid, gMap):
        self.sid = sid
        self.gMap = gMap
        self.units = {}
        self.enemyGroundUnits = {}
        self.enemyBuildings = {}
        self.enemyAircraft = {}
        self.LOS = {}               # Line of sight: enemyId -> bool
        self.aircraftNames = cdata.unitClasses['armap'].units

    def makeFriendlyUnit(self, unitId):
        unit, unitType = self.makeUnit(unitId)
        self.units[unitId] = unit
        return unit, unitType

    def makeEnemyUnit(self, enemyId):
        enemy, unitType = self.makeUnit(enemyId)
        if not self.LOS.has_key(enemyId):
            self.LOS[enemyId] = False
        if enemy.defi.type == 'com':
            self.enemyCom = enemy
        if self.isAircraft(enemy):
            self.enemyAircraft[enemyId] = enemy
        elif unitType in buildingTypes:
            self.enemyBuildings[enemyId] = enemy
            # Find building position and attach to unit object
            pos = cdata.clb.getUnitPosition(self.sid, enemy.unitId)
            enemy.pos = pos
            # attach to cell in gmap
            cell = self.gMap.getCellContainingPoint(pos)
            cell.enemyBuilding = enemy
        else:
            # if not a plane or building, it is a ground unit; combat/cons/com
            self.enemyGroundUnits[enemyId] = enemy
        return enemy

    def makeUnit(self, unitId):
        unitDefName = cdata.clb.getUnitDefName(self.sid, unitId)
        unit = Unit(unitId, cdata.unitDefs[unitDefName])
        return unit, unit.defi.type

    def getUnit(self, unitId):
        if self.units.has_key(unitId):
            return self.units[unitId]

    def getEnemy(self, enemyId):
        if self.enemyGroundUnits.has_key(enemyId):
            return self.enemyGroundUnits[enemyId]
        elif self.enemyBuildings.has_key(enemyId):
            return self.enemyBuildings[enemyId]
        elif self.enemyAircraft.has_key(enemyId):
            return self.enemyAircraft[enemyId]

    def removeFriendly(self, unitId):
        return  self.units.pop(unitId, None)

    def removeEnemy(self, enemyId):
        if self.enemyGroundUnits.has_key(enemyId):
            enemy = self.enemyGroundUnits.pop(enemyId)
            del self.LOS[enemyId]
            if enemy.defi.type == 'com':
                return True
        elif self.enemyAircraft.has_key(enemyId):
            del self.enemyAircraft[enemyId]
            del self.LOS[enemyId]
        elif self.enemyBuildings.has_key(enemyId):
            enemy = self.enemyBuildings.pop(enemyId)
            cell = self.gMap.getCellContainingPoint(enemy.pos)
            cell.enemyBuilding = None
            del self.LOS[enemyId]
        return False

    def enterLOS(self, enemyId):
        self.LOS[enemyId] = True
        return self.getEnemy(enemyId)

    def leaveLOS(self, enemyId):
        self.LOS[enemyId] = False

    def isAircraft(self, unit):
        return unit.defi.name in self.aircraftNames

