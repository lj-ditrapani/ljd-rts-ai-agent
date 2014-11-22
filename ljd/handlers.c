#include "agent.h"
#include "AISCommands.h"
#include "AISEvents.h"

struct IntBox 
{
    int val;   // try unitId instead?
};

void callMethodWithUnitId(int sid, int unitId, char *meth)
{
    PyObject *ret = PyObject_CallMethod(agents[sid], meth, "(i)", unitId);
    if (ret == NULL)
        PyErr_Print();
}

void callMethod(int sid, const void *data, char *meth)
{
    callMethodWithUnitId(sid, ((struct IntBox *) data)->val, meth);
}

// Null function, does nothing
void n(int sid, const void *data)
{
}

void update(int sid, const void *data)
{
    callMethod(sid, data, "update");
}

void unitCreated(int sid, const void *data)
{
    callMethod(sid, data, "unitCreated");
}

void unitFinished(int sid, const void *data)
{
    callMethod(sid, data, "unitFinished");
}

void unitIdle(int sid, const void *data)
{
    callMethod(sid, data, "unitIdle");
}

void unitDamaged(int sid, const void *data)
{
    struct SUnitDamagedEvent *e = (struct SUnitDamagedEvent *) data;
    int enemyId = e->attacker;
    if (enemyId < 0)
        return;
    int unitId = e->unit;
    PyObject *ret = PyObject_CallMethod(agents[sid], "unitDamaged", "(ii)", 
        unitId, enemyId);
    if (ret == NULL)
        PyErr_Print();
}

void unitDestroyed(int sid, const void *data)
{
    int unitId = ((struct SUnitDestroyedEvent *) data)->unit;
    callMethodWithUnitId(sid, unitId, "unitDestroyed");
}

void enterLOS(int sid, const void *data)
{
    callMethod(sid, data, "enterLOS");
}

void leaveLOS(int sid, const void *data)
{
    callMethod(sid, data, "leaveLOS");
}

void enemyDestroyed(int sid, const void *data)
{
    int enemyId = ((struct SEnemyDestroyedEvent *) data)->enemy;
    callMethodWithUnitId(sid, enemyId, "enemyDestroyed");
}

void enemyFinished(int sid, const void *data)
{
    callMethod(sid, data, "enemyFinished");
}

handleEventFp ljd_handlers[28] = {
    n,                      // 0
    n,                      // 1 init
    n,                      // 2 release
    update,                 // 3
    n,                      // 4
    unitCreated,            // 5 unit_created
    unitFinished,           // 6
    unitIdle,               // 7
    n,                      // 8
    unitDamaged,            // 9 unit_damaged
    unitDestroyed,          //10 unit_destroyed
    n,                      //11
    n,                      //12
    enterLOS,               //13
    leaveLOS,               //14
    n,                      //15
    n,                      //16
    n,                      //17
    enemyDestroyed,         //18 enemy destroyed
    n,                      //19
    n,                      //20
    n,                      //21
    n,                      //22 command finished
    n,                      //23
    n,                      //24
    n,                      //25 enemy created
    enemyFinished,          //26 enemy finished
    n};                     //27
