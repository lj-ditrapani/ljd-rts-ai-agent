'''Author:  Lyall Jonathan Di Trapani                                       '''

import ctypes, shelve
import cdata, gamemap, unitmanager, buildmanager, defensemanager, attackmanager
import group

# load callback library using ctypes
cdata.clb.saveAgentClb.argtypes = [ctypes.c_int, ctypes.py_object]


class Agent:

    def __init__(self, sid, cap):
        self.sid = sid                      # skirmishAI ID number
        print '<Agent {0}> saving callback'.format(sid)
        cdata.clb.saveAgentClb(sid, cap)    # store callback in library
        self.frame = 0
        if not cdata.unitDefsLoaded:
            cdata.loadUnitDefs(sid)
            cdata.unitDefsLoaded = True
            gamemap.loadMapData(sid)
            print '<Agent {0}> map data loaded'.format(sid)
        config = cdata.playerConfigs[sid]
        self.collectData = config[1]
        strategy = cdata.strategies[config[0]]
        gMap = gamemap.Map(sid)
        self.unitManager = unitmanager.UnitManager(sid, gMap)
        self.idleEventFlilter = group.IdleEventFilter()
        self.attackManager = attackmanager.AttackManager(
            sid, self.idleEventFlilter)
        self.defenseManager = defensemanager.DefenseManager(
            sid, strategy, self.attackManager, self.unitManager, 
            gMap, self.idleEventFlilter)
        self.buildManager = buildmanager.BuildManager(
            sid, strategy, gMap, self.defenseManager)
        cdata.clb.cheat(sid)
        self.data = []

    def update(self, frame):
        self.frame = frame
        # Quit after 37 minutes
        # Number of minutes * 60 sec/min * 30 frame/sec
        if frame > 37 * 60 * 30:
            self._endGame('timeup')
        if frame % 5 == 0:
            self.idleEventFlilter.frame = frame
            self.defenseManager.update(frame)
            self.attackManager.update(frame)
        if frame % 15 == 0:
            self.buildManager.update(frame)
        # Write to file every 5 seconds
        if self.collectData and frame % (5 * 30) == 0:
            self._captureState()

    def _captureState(self):
        # get every friendly unit defId and position
        units = self.unitManager.units
        unitIds = units.keys()
        points = cdata.clb.getPositions(self.sid, unitIds, len(unitIds))
        unitData = []
        for unitId, p in zip(unitIds, points):
            unit = units[unitId]
            unitData.append((unit.defi.defId, p[0], p[2]))
        unitData.sort(key=lambda u: u[0])
        # get metal and energy values (8)
        econData = cdata.clb.getResourceUpdate(self.sid)
        # Store in data along with current frame
        self.data.append((self.frame, unitData, econData))

    def unitCreated(self, unitId):
        unit, unitType = self.unitManager.makeUnit(unitId)
        if unitType in unitmanager.buildingTypes:
            self.buildManager.buildingCreated(unit, unitType)

    def unitFinished(self, unitId):
        unit, unitType = self.unitManager.makeFriendlyUnit(unitId)
        name = unit.defi.name
        if unitType in ('econBuilding', 'factory'):
            self.buildManager.buildingFinished(unit, unitType)
        elif unitType == 'com':
            self.buildManager.comFinished(unit)
            self.defenseManager.setCom(unit)
        elif unitType == 'cons':
            self.buildManager.consFinished()
        elif unitType == 'defenseBuilding':
            self.buildManager.defenseFinished()
        elif unitType == 'combat':
            self.defenseManager.unitFinished(unit)

    def unitIdle(self, unitId):
        unit = self.unitManager.getUnit(unitId)
        if unit == None:
            return
        unitType = unit.defi.type
        if unitType == 'factory':
            self.buildManager.factoryIdle(unit)
        elif unitType == 'com':
            self.buildManager.comIdle()
        elif unitType == 'cons':
            self.buildManager.consIdle(unit)
        elif unitType == 'combat':
            if unit.group.defense:
                self.defenseManager.groupIdle()
            else:
                self.attackManager.groupIdle(unit.group)

    def unitDamaged(self, unitId, enemyId):
        # Ensure enemy in within our LOS
        LOS = self.unitManager.LOS
        if (not LOS.has_key(enemyId)) or (not LOS[enemyId]):
            return
        # Ensure the defenders are not already busy attacking someone else
        if self.defenseManager.attacking:
            return
        # Ensure the unit that was attacked is not in an attack group
        unit = self.unitManager.getUnit(unitId)
        if not unit is None:
            unitType = unit.defi.type
            if unitType == 'combat':
                if not unit.group.defense:
                    return
        # Send defense group to counter-attack
        self.defenseManager.attack(self.unitManager.getEnemy(enemyId))

    def unitDestroyed(self, unitId):
        self.buildManager.checkBuildingCells(unitId)
        unit = self.unitManager.removeFriendly(unitId)
        if unit is None:
            return
        unitType = unit.defi.type
        if unitType in ('econBuilding', 'factory'):
            self.buildManager.buildingDestroyed(unit, unitType)
        elif unitType == 'cons':
            self.buildManager.consDestroyed()
        elif unitType == 'defenseBuilding':
            self.buildManager.defenseDestroyed()
        elif unitType == 'combat':
            if unit.group.defense:
                self.defenseManager.unitDestroyed(unit)
            else:
                self.attackManager.unitDestroyed(unit, unit.group)
            unit.group = None
        elif unitType == 'com':
            self._endGame('loss')

    def enterLOS(self, enemyId):
        enemy = self.unitManager.enterLOS(enemyId)
        if enemy is None:
            return
        self.attackManager.enterLOS(enemy)

    def leaveLOS(self, enemyId):
        self.unitManager.leaveLOS(enemyId)

    def enemyDestroyed(self, enemyId):
        comDestroyed = self.unitManager.removeEnemy(enemyId)
        if comDestroyed:
            self._endGame('win')

    def enemyFinished(self, enemyId):
        self.unitManager.makeEnemyUnit(enemyId)

    def _endGame(self, result):
        print 'last frame', self.frame
        # construct database file name
        fmt = '{0}../data/{1}/{2}_{3}_{4}_{5:02}.db'
        gc = cdata.gameConfig
        pc = cdata.playerConfigs
        fName = fmt.format(cdata.rootDir, gc['mapSize'], pc[self.sid][0], 
                           pc[0][0], pc[1][0], gc['gameNum'])
        db = shelve.open(fName)
        db['result'] = result
        db['data'] = self.data
        db.close()
        cdata.clb.quit(self.sid)
