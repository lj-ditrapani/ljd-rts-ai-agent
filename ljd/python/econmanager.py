import ctypes, cdata

cdata.clb.getResourceUpdate.restype = ctypes.py_object


class EconManager:

    def __init__(self, sid, strategy, gMap):
        self.sid = sid
        self.setStrategy(strategy)
        self.gMap = gMap
        mCount, sCount = strategy.initEcon
        self.econBuildingMax = dict(mex=mCount, solar=sCount)
        self.econBuildingCount = dict(mex=0, solar=0)
        self.factory = None
        self.buckets = Buckets(strategy.buckets)
        self.nextDefense = 'armllt'
        self.comBuilding = False
        self.factoryWaiting = False
        self.waitFrame = 0

    def getConsUnitDef(self):
        return cdata.unitDefs[self.unitClass.consUnit]
        
    def setStrategy(self, strategy):
        self.strategy = strategy
        self.unitClass = getUnitClass(strategy)
        # if unitClass changes, must set initEcon to factory type
        # if factory type does not exist
        # Or maybe just automatic...if factory type DNE, create it first?

    def update(self, frame):
        if self.factory is None:
            return
        waiting = self.factoryWaiting
        timeUp = frame - self.waitFrame >= 3 * 30
        drained = self._isEconDrained()
        if (not waiting and self.comBuilding and drained):
            self.factoryWaiting = True
            self.waitFrame = frame
            cdata.clb.wait(self.sid, self.factory.unitId)
        elif (waiting and (not self.comBuilding or (timeUp and not drained))):
            self.factoryWaiting = False
            cdata.clb.wait(self.sid, self.factory.unitId)

    def _inInitEcon(self):
        'Returns True if in initial economy mode, else False'
        ebc = self.econBuildingCount
        ebm = self.econBuildingMax
        if (ebc['mex'] < ebm['mex'] or ebc['solar'] < ebm['solar'] or 
                self.factory is None):
            return True
        else:
            return False

    def _nextInitEconBuilding(self):
        ebc = self.econBuildingCount
        ebm = self.econBuildingMax
        if ebc['mex'] >= ebm['mex'] and ebc['solar'] >= ebm['solar']:
            return self.unitClass.factory
        elif ebc['mex'] < ebm['mex'] and ebc['solar'] < ebm['solar']:
            if ebc['mex'] <= ebc['solar']:
                return 'armmex'
            else:
                return 'armsolar'
        elif ebc['mex'] < ebm['mex']:
            return 'armmex'
        elif ebc['solar'] < ebm['solar']:
            return 'armsolar'

    def buildingFinished(self, unit, unitType):
        if unitType == 'factory':
            self.factory = unit
            self.factoryWaiting = False
            # do not call self.factoryIdle, let buildManager do that
        elif unit.defi.name == 'armmex':
            self.econBuildingCount['mex'] += 1
        elif unit.defi.name == 'armsolar':
            self.econBuildingCount['solar'] += 1

    def factoryIdle(self, unit, consLimit):
        # if buildPower.storage >= bp cons.unitDef.cost (cost of ck|cv|ca)
        consCost = self.getConsUnitDef().mCost
        if not consLimit and self.buckets.getStore('buildPower') >= consCost:
            # build cons unit
            self.buckets.update('buildPower', consCost)
            return 'consUnit'
        else:
            return 'combatUnit'

    def _isEconDrained(self):
        # and metal storage < 0.15 or energy storage < 0.15 
        res = self._getResourceUpdate()
        lowM = res['currM'] / res['storM'] < 0.15
        lowE = res['currE'] / res['storM'] < 0.15
        return lowM or lowE
        
    def comIdle(self, com, defenseLimit):
        # a) if curr econ < initial econ:  
        if self._inInitEcon():
            # fix initial econ (mex, solar, factory)
            return 'build', cdata.unitDefs[self._nextInitEconBuilding()]
        # b) Start new construction
        # Pick build unit for each 2 categories (econ, def)
        econDef = self._nextEconBuilding()
        if defenseLimit:
            defenseDef = None
        else:
            defenseDef = cdata.unitDefs[self.nextDefense]
        buildings = []
        for building in [econDef, defenseDef]:
            if not building is None:
                buildings.append(building)
        # sort 2 buildings by store amount in decending order
        buildings.sort(key=lambda defi: defi.mCost)
        for building in buildings:
            if self.buckets.getStore(building.category) >= building.mCost:
                if building.category == 'defense':
                    self._swapNextDefenseBuilding()
                self.buckets.update(building.category, building.mCost)
                return 'build', building
        # c) Help factory unconditionally
        # Factory exists or inInitEcon would have caught it
        return 'guard', self.factory

    def _nextEconBuilding(self):
        res = self._getResourceUpdate()
        mneed = res['storM'] / res['currM']
        eneed = res['storE'] / res['currE']
        # 1 / 0.40 = 2.5
        if mneed > eneed and mneed > 2.5:
            return cdata.unitDefs['armmex']
        elif eneed > 2.5:
            return cdata.unitDefs['armsolar']
        else:
            return None

    def _getResourceUpdate(self):
        res = cdata.clb.getResourceUpdate(self.sid)
        d = {}
        keys = ('currM', 'currE', 'incoM', 'incoE',
                'usagM', 'usagE', 'storM', 'storE')
        for key, val in zip(keys, res):
            d[key] = val
        return d

    def _swapNextDefenseBuilding(self):
        'Toggle next to build (llt or rl)'
        d = {'armllt': 'armrl', 'armrl': 'armllt'}
        self.nextDefense = d[self.nextDefense]

    def consIdle(self, cons):
        pass

    def buildingDestroyed(self, unit, unitType):
        # if factory, remove from econManager
        if self.factory and self.factory.unitId == unit.unitId:
            self.factory = None
            return False
        elif unit.defi.name == 'armmex':
            self.econBuildingCount['mex'] -= 1
        elif unit.defi.name == 'armsolar':
            self.econBuildingCount['solar'] -= 1

    def updateUnitsBucket(self, metalValue):
        self.buckets.update('units', metalValue)


class Buckets:

    def __init__(self, targets):
        self.targets = targets
        self.totals = dict(buildPower=0.0, econ=0.0, defense=0.0, units=0.0)

    def getStore(self, category):
        target, total = self.targets[category], self.totals[category]
        return (target / 100.0 * self._sumTotals() - total)

    def update(self, category, metalValue):
        self.totals[category] += metalValue

    def _sumTotals(self):
        return sum(self.totals.values())


def getUnitClass(strategy):
    'What class of units are used in this strategy?'
    uName = strategy.combatUnitNames[0]
    for unitClass in cdata.unitClasses.values():
        if uName in unitClass.units:
            return unitClass
