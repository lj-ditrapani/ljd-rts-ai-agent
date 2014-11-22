''' Author:  Lyall Jonathan Di Trapani                                      ---
    Constant data used by multiple modules
'''

import sys, ctypes

rootDir = sys.path[0]       # src dir prepended to path before loading module
# Use PyDLL so ctypes does NOT release the GIL when calling into clb.so
clb = ctypes.PyDLL(rootDir + 'clb.so', ctypes.RTLD_GLOBAL)
clb.getUnitDefName.restype = ctypes.c_char_p
clb.saveAgentClb.argtypes = [ctypes.c_int, ctypes.py_object]
clb.getUnitPosition.restype = ctypes.py_object
clb.getPositions.argtypes = [ctypes.c_int, ctypes.py_object, ctypes.c_int]
clb.getPositions.restype = ctypes.py_object

unitDefsLoaded = False
gameConfig = {}             # game number and map size
playerConfigs = []          # 2-item list of tuples (strategy, collectData)
strategies = {}
strategyNames = []
unitClasses = {}
unitFactories = []
unitDefs = {}


class UnitClass:
    # Types are:  com cons combat factory econBuilding defenseBuilding
    typeMap = {'armcom': 'com'}
    unitNames = ['armcom']
    combatUnits = []
    buildingNames = []
    footprints = {}

    def __init__(self, factory, consUnit, units):
        self.factory = factory
        self.consUnit = consUnit
        self.units = units
        UnitClass.unitNames += [consUnit] + units
        UnitClass.typeMap[consUnit] = 'cons'
        for unit in units:
            UnitClass.typeMap[unit] = 'combat'
            UnitClass.combatUnits.append(unit)

    def __str__(self):
        return '{0}: {1}'.format(self.consUnit, self.units)


class UnitDef:

    def __init__(self, name):
        self.name = name
        self.type = UnitClass.typeMap[name]
        if self.type == 'econBuilding':
            self.category = 'econ'
        elif self.type == 'defenseBuilding':
            self.category = 'defense'

    def set(self, defId, mCost, eCost, buildTime, buildSpeed, speed):
        self.mCost, self.eCost, self.buildTime  = mCost, eCost, buildTime
        self.defId, self.speed, self.buildSpeed = defId, speed, buildSpeed

    def __str__(self):
        return ('Name {0:9}  Id {1:3}  mCost {2:4.0f}  eCost {3:5.0f}  '
        'buildTime {4:5.0f}  buildSpeed {5:3.0f}  speed {6:5.1f}').format(
        self.name, self.defId, self.mCost, self.eCost, self.buildTime, 
        self.buildSpeed, self.speed)


def printAllUnitDefs():
    for k in UnitClass.unitNames:
        print unitDefs[k]
    for k in UnitClass.buildingNames:
        print unitDefs[k]


class Strategy:
    NUM_UNIT_TYPES = 16
    def __init__(self, line):
        values = [int(val) for val in line.split()]
        bVals, values = values[:4], values[4:]
        self.buckets = dict(
            buildPower  = bVals[0],
            econ        = bVals[1],
            defense     = bVals[2],
            units       = bVals[3])
        n = Strategy.NUM_UNIT_TYPES
        unitCounts, self.initEcon = values[:n], values[n:]
        self.combatUnitNames = []
        self.combatUnits = {}
        for combatUnitName, i in zip(UnitClass.combatUnits, range(n)):
            self.combatUnits[combatUnitName] = unitCounts[i]
            if unitCounts[i] > 0:
                self.combatUnitNames.append(combatUnitName)
    def __str__(self):
        s = 'buckets: {0}\ncombat units: {1}\ninitEcon{2}'
        return s.format(self.buckets, self.combatUnits, self.initEcon)

        
def getTxt(fName):
    f = open(rootDir + '../config/' + fName, 'rb')
    txt = f.read().strip()
    f.close()
    return txt


def loadConfiguration():
    # Load the types of units available in the game
    for record in getTxt('unitClasses.txt').split('\n===\n'):
        factory, consUnit, units = record.split('\n')
        unitClasses[factory] = UnitClass(factory, consUnit, units.split())
        unitFactories.append(factory)
    # Load the types of buildings available in the game
    lines = getTxt('buildings.txt').split('\n')
    for line in lines:
        bName, bType, fpx_s, fpz_s = line.split(':')
        bName, bType = bName.strip(), bType.strip()
        footprintX, footprintZ = int(fpx_s), int(fpz_s)
        UnitClass.typeMap[bName] = bType
        UnitClass.buildingNames.append(bName)
        UnitClass.footprints[bName] = (footprintX, footprintZ)
    # Load the strategy definitions
    for line in getTxt('strategyDefs.txt').split('\n'):
        if line[0] == '#':
            continue
        strategyName, line = line.split(None, 1)
        strategies[strategyName] = Strategy(line)
        strategyNames.append(strategyName)
    configLines = getTxt('config.txt').split('\n')
    configLines = [line.strip() for line in configLines if line[0] != '#']
    gameConfig['gameNum'] = int(configLines[0])
    gameConfig['mapSize'] = configLines[1]
    # Load player 1 and 2 configurations (strategy name and collect data)
    for line in configLines[2:]:
        # Take the second word of the line---the strategy
        p, strategyName, collectData = line.strip().split()
        if not strategyName in strategyNames + ['ljd']:
            raise Exception('Invalid strategy in config file (2nd arg)')
        if not collectData in ('on', 'off'):
            s = 'Invalid Collect Data Option in config file (3rd) arg'
            raise Exception(s)
        playerConfigs.append((strategyName, collectData))


def loadUnitDefs(sid):
    for name in UnitClass.unitNames:
        unitDefs[name] = UnitDef(name)
    for name in UnitClass.buildingNames:
        unitDefs[name] = UnitDef(name)
    clb.loadUnitDefs.argtypes = [ctypes.c_int, 
        ctypes.py_object, ctypes.py_object]
    names = UnitClass.unitNames + UnitClass.buildingNames
    clb.loadUnitDefs(sid, names , unitDefs)
    for name in UnitClass.buildingNames:
        uDef = unitDefs[name]
        footprint = UnitClass.footprints[name]
        uDef.footprintX, uDef.footprintZ = footprint[0], footprint[1]


loadConfiguration()
