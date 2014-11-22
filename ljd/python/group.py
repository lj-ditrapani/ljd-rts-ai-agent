import ctypes, math
import cdata
cdata.clb.move.argtypes = [ctypes.c_int, ctypes.c_int, 
                           ctypes.c_float, ctypes.c_float] 

class Group:
    groupId = 0

    def __init__(self, sid, gMap, unitManager):
        self.sid = sid
        self.gMap = gMap
        self.unitManager = unitManager
        self.units = []
        self.defense = True         # Am I the current defense group
        self.order = 'move'
        self.lastIdleEventFrame = 0
        self.pendingIdleEvent = False
        self.groupId = Group.groupId
        self.mode = 'ground'
        Group.groupId += 1

    def remove(self, unit):
        self.units.remove(unit)
        if len(self.units) == 0:
            return False
        else:
            return True

    def add(self, unit):
        if len(self.units) == 0:
            if unit.defi.name in self.unitManager.aircraftNames:
                self.mode = 'air'
            else:
                self.mode = 'ground'
        self.units.append(unit)
        unit.group = self

    def setAttacking(self):
        self.defense = False
        self.units.sort(key=lambda unit: unit.defi.speed)

    def attack(self):
        # Update gMap unit pos and time stamp
        # clear old enemy values in gMap
        for cell in self.gMap.iterateCells():
            cell.enemyGroundUnits = []
        # Get position of each enemy ground unit; enemyGroundUnits is a dict
        enemyMap = self.unitManager.enemyGroundUnits
        size = len(enemyMap)
        unitIds = enemyMap.keys()
        enemyPositions = cdata.clb.getPositions(self.sid, unitIds, size)
        for i in range(size):
            enemy = enemyMap[unitIds[i]]
            # attach pos to enemy unit
            pos = enemyPositions[i]
            enemy.pos = pos
            # get cell containing pos
            cell = self.gMap.getCellContainingPoint(pos)
            # attach enemy unit to cell.enemy*.append(unit)
            cell.enemyGroundUnits.append(enemy)
        xavg, zavg = self._getCenterOfMass()
        enemy = None
        for cell in self.gMap.generateCells((xavg, 25.0, zavg)):
            enemyBuilding = cell.enemyBuilding
            enemies = cell.enemyGroundUnits
            if not enemyBuilding is None:
                # attack building
                enemy = enemyBuilding
                break
            elif len(enemies) > 0:
                # attack unit
                enemy = self._getClosestEnemy(xavg, zavg, enemies)
                break
        if self.mode == 'air':
            enemy = self.unitManager.enemyCom
        if enemy is None:
            return
        elif self.unitManager.LOS[enemy.unitId]:
            self.order = 'attack'
            self.attackEnemy(enemy)
        else:
            # Since enemy is outside of LOS, find a point to move to
            self.order = 'move'
            pos = enemy.pos
            self.movePos = pos
            if self.mode == 'air':
                for unit in self.units:
                    cdata.clb.move(self.sid, unit.unitId, pos[0], pos[2])
            else:
                target, guards = self.units[0], self.units[1:]
                cdata.clb.move(self.sid, target.unitId, pos[0], pos[2])
                self._guard(target, guards)

    def attackEnemy(self, enemy):
        for unit in self.units:
            cdata.clb.attack(self.sid, unit.unitId, enemy.unitId)

    def guard(self, target):
        self._guard(target, self.units)

    def _guard(self, target, guards):
        for guard in guards:
            cdata.clb.guardUnit(self.sid, guard.unitId, target.unitId)

    def _updateUnitPositions(self):
        unitIds = [unit.unitId for unit in self.units]
        size = len(self.units)
        friendlyPositions = cdata.clb.getPositions(self.sid, unitIds, size)
        for unit, pos in zip(self.units, friendlyPositions):
            unit.pos = pos
        return friendlyPositions

    def _getCenterOfMass(self):
        size = len(self.units)
        xsum = zsum = 0
        for pos in self._updateUnitPositions():
            xsum += pos[0]
            zsum += pos[2]
        xavg = xsum/size
        zavg = zsum/size
        return xavg, zavg

    def _getClosestEnemy(self, x, z, enemies):
        minDist = 25600
        closest = None
        for enemy in enemies:
            dist = calcDist((x, 0.0, z), enemy.pos)
            if dist < minDist:
                minDist = dist
                closest = enemy
        return enemy


def calcDist(p1, p2):
    'Calculate distance from p1 to p2 in true euclidean coordinates'
    return math.sqrt((p2[0] - p1[0])**2 + (p2[2] - p1[2])**2)


class IdleEventFilter:
    'Ensures only one idleEvent per group per interval'
    
    def __init__(self):
        self.frame = 0

    def newEvent(self, group):
        if self.frame > group.lastIdleEventFrame:
            group.lastIdleEventFrame = self.frame
            group.pendingIdleEvent = False
            return True
        else:
            group.pendingIdleEvent = True
            return False
