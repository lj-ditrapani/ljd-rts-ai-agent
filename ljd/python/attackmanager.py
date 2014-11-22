class AttackManager:

    def __init__(self, sid, idleEventFlilter):
        self.sid = sid
        self.groups = []
        self.idleEventFlilter = idleEventFlilter

    def update(self, frame):
        for group in self.groups:
            if group.pendingIdleEvent:
                self.groupIdle(group)

    def groupIdle(self, group):
        if self.idleEventFlilter.newEvent(group):
            group.attack()

    def add(self, group):
        self.groups.append(group)
        group.attack()

    def unitDestroyed(self, unit, group):
        usable = group.remove(unit)
        if not usable:
            self.groups.remove(group)

    def enterLOS(self, enemy):
        for group in self.groups:
            # order == 'attack' means group is attacking an enemy in LOS
            if not group.order == 'attack':
                self.groupIdle(group)
