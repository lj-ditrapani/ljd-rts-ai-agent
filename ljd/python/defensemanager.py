import cdata, group

class DefenseManager:

    unitNamesByCost = []

    def __init__(self, sid, strategy, attackManager, 
                 unitManager, gMap, idleEventFlilter):
        self.sid = sid
        self.strategy = strategy            # Update on strategy change
        self.attackManager = attackManager
        self.unitManager = unitManager
        self.gMap = gMap
        self.idleEventFlilter = idleEventFlilter
        self.attacking = False
        unitNamesByCost = DefenseManager.unitNamesByCost
        # Only first player needs to compute unitNamesByCost
        if len(unitNamesByCost) == 0:
            for name in cdata.UnitClass.combatUnits:
                uDef = cdata.unitDefs[name]
                unitNamesByCost.append((name, uDef.mCost))
            def key(pair):
                return pair[1]
            unitNamesByCost.sort(key=key)
        buildList = []
        for (name, cost) in unitNamesByCost:
            count = self.strategy.combatUnits.get(name, 0)
            buildList += [name] * count
        # Must update buildList, buildListCopy, and group on strategy change
        self.buildList = buildList
        self.buildListCopy = buildList[:]
        self.group = group.Group(self.sid, self.gMap, self.unitManager)

    def setCom(self, com):
        self.com = com

    def nextUnitToBuild(self):
        if len(self.buildList) == 0:
            self.buildList = self.buildListCopy[:]
        name = self.buildList.pop(0)
        return cdata.unitDefs[name]

    def update(self, frame):
        if self.group.pendingIdleEvent:
            self.groupIdle()

    def attack(self, enemy):
        isAircraft = self.unitManager.isAircraft(enemy)
        if self.group.mode == 'air' and not isAircraft:
            return
        self.attacking = True
        self.group.attackEnemy(enemy)

    def groupIdle(self):
        if self.idleEventFlilter.newEvent(self.group):
            self.attacking = False
            self.group.guard(self.com)

    def unitFinished(self, unit):
        self.group.add(unit)
        if len(self.buildList) == 0:
            self.group.setAttacking()
            self.attackManager.add(self.group)
            self.group = group.Group(self.sid, self.gMap, self.unitManager)
        else:
            pass
            #self.groupIdle()

    def unitDestroyed(self, unit):
        hasUnits = self.group.remove(unit)
        if not hasUnits:
            self.group = group.Group(self.sid, self.gMap, self.unitManager)
