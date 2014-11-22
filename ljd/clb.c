/* Author:  Lyall Jonathan Di Trapani                                        */
#include <Python.h>
#include "SSkirmishAICallback.h"
#include "AISCommands.h"

// Resource ID {0 -> Metal;  1 -> Energy}
#define METAL_ID 0
#define ENERGY_ID 1
#define TIME_OUT 1000000

struct SSkirmishAICallback *clbs[10];

void saveAgentClb(int sid, PyObject *cap)
{
    char buf[8];
    snprintf(buf, 8, "agent%d", sid);
    const char *name = (const char *) &buf;
    void *vp = PyCapsule_GetPointer(cap, name);
    clbs[sid] = (struct SSkirmishAICallback *) vp;
    Py_DECREF(cap);
}

// List of PyStrings, dictionary PyString -> UnitDef
void loadUnitDefs(int sid, PyObject *names, PyObject *defs)
{
    Py_ssize_t len = PySequence_Length(names);
    Py_ssize_t i;
    for (i = 0; i < len; i++) {
        PyObject *pName = PySequence_GetItem(names, i);
        char *name = PyString_AsString(pName);
        PyObject *def = PyObject_GetItem(defs, pName);
        Py_DECREF(pName);
        // Get all the def values from spring engine
        int defId = clbs[sid]->getUnitDefByName(sid, name);
        float mCost = clbs[sid]->UnitDef_getCost(sid, defId, METAL_ID);
        float eCost = clbs[sid]->UnitDef_getCost(sid, defId, ENERGY_ID);
        float bTime = clbs[sid]->UnitDef_getBuildTime(sid, defId);
        float bSpeed = clbs[sid]->UnitDef_getBuildSpeed(sid, defId);
        float speed = clbs[sid]->UnitDef_getSpeed(sid, defId);
        // call set on def (def.set) to set all values
        PyObject *res = PyObject_CallMethod(def, "set", "(ifffff)", defId, 
            mCost, eCost, bTime, bSpeed, speed);
        Py_DECREF(def);
        Py_DECREF(res);  // Callmethod returns new ref, must be decrefed!
    }
}

PyObject *loadMetalPatchLocations(int sid, int maxSize) 
{
    float spots[maxSize*3];  // Enough for 60 (x,y,z) positions
    int ret = clbs[sid]->Map_getResourceMapSpotsPositions(
        sid, METAL_ID, spots, maxSize*3);
    int numSpots = ret/3;
    PyObject* mpLocations = PyList_New(numSpots);
    int i;
    for (i = 0; i < numSpots; i++) {
        float* fp = spots + i*3;
        // Returns new ref to spot; would normally have to DECREF
        PyObject *spot = Py_BuildValue("(fff)", *fp, *(fp+1), *(fp+2));
        // Does not leak, SetItem does not increment ref count, steals a ref
        PyList_SetItem(mpLocations, i, spot);
    }
    return mpLocations;     // Ownership transfered to python
}

PyObject *getMapDimensions(int sid) 
{
    int w = clbs[sid]->Map_getWidth(sid);   // height map x dimension max
    int h = clbs[sid]->Map_getHeight(sid);  // height map z dimension max
    return Py_BuildValue("(ii)", w, h);
}

void cheat(int sid) 
{
    clbs[sid]->Cheats_setEnabled(sid, true);
    clbs[sid]->Cheats_setEventsEnabled(sid, true);
}

void giveUnit(int sid, PyObject *pyPos, int defId) 
{
    float pos[3];
    PyArg_ParseTuple(pyPos, "fff", pos, pos + 1, pos + 2);
    struct SGiveMeNewUnitCheatCommand cc = {defId, pos, 99};
    clbs[sid]->Engine_handleCommand(sid, COMMAND_TO_ID_ENGINE, -1, 
        COMMAND_CHEATS_GIVE_ME_NEW_UNIT, &cc);
}

const char *getUnitDefName(int sid, int unitId) 
{
    int defId = clbs[sid]->Unit_getDef(sid, unitId);
    return clbs[sid]->UnitDef_getName(sid, defId);
}

PyObject *getUnitPosition(int sid, int unitId) 
{
    float p[3];         // Position of unit
    clbs[sid]->Unit_getPos(sid, unitId, p);
    PyObject *pos = Py_BuildValue("(fff)", p[0], p[1], p[2]);
    return pos;     // No decref, passing reference on to buildManager
}

PyObject *getPositions(int sid, PyObject *unitIds, int size) 
{
    PyObject* positions = PyList_New(size);
    int i;
    for (i = 0; i < size; i++) {
        PyObject *py_id = PySequence_GetItem(unitIds, i);
        int unitId = (int) PyInt_AsLong(py_id);
        Py_DECREF(py_id);
        float p[3];         // Position of unit
        clbs[sid]->Unit_getPos(sid, unitId, p);
        // Returns new ref to pos; would normally have to DECREF
        PyObject *pos = Py_BuildValue("(fff)", p[0], p[1], p[2]);
        // Does not leak, SetItem does not increment ref count, steals a ref
        PyList_SetItem(positions, i, pos);
    }
    return positions;     // Ownership transfered to python

}

int canBuildHere(int sid, int defId, float x, float z, int facing)
{
    float pos[3] = {x, 25.0, z};
    return clbs[sid]->Map_isPossibleToBuildAt(sid, defId, pos, facing);
}

/*
consId:         ID of construction unit
defId:          Unit definition ID of structure to be built
 */
void buildStruct(int sid, int consId, int defId, float x, float z, int facing) 
{
    float buildSite[3] = {x, 25.0, z};
    // unitId, groupId, options, timeout, uDefId, pos, facing (-1 default)
    struct SBuildUnitCommand bcmd = {consId, -1, (short) 0, TIME_OUT, defId,
        buildSite, facing};
    // sid, toId, commandId=-1, commandTopic, commandData
    int rv = clbs[sid]->Engine_handleCommand(sid, COMMAND_TO_ID_ENGINE, -1,
        COMMAND_UNIT_BUILD, &bcmd);
}

// Command unit with guardId to guard unit with targetId
void guardUnit(int sid, int guardId, int targetId) 
{
    // unitId, groupId, options, timeout, uDefId, pos, facing
    struct SGuardUnitCommand cmd = {guardId, -1, (short) 0, 
                                    TIME_OUT, targetId};
    // sid, toId, commandId=-1, commandTopic, commandData
    int rv = clbs[sid]->Engine_handleCommand(sid, COMMAND_TO_ID_ENGINE, -1,
         COMMAND_UNIT_GUARD, &cmd);
}

/*
Command factory with factId to build a unit with definition defId
factId, unit id of factory that will build the unit
defId,  unit definition ID of unit to be built by factory
*/
void buildUnit(int sid, int factId, int defId) 
{
    float pos[3] = {300.0, 300.0, 300.0};
    //float currPos[3];
    //clbs[sid]->Unit_getPos(sid, unitId, currPos);
    // unitId, groupId, options, timeout, uDefId, pos, facing
    struct SBuildUnitCommand bcmd = {factId, -1, (short) 0, TIME_OUT, defId,
        pos, -1};
    // sid, toId, commandId=-1, commandTopic, commandData
    int rv = clbs[sid]->Engine_handleCommand(sid, COMMAND_TO_ID_ENGINE, -1,
        COMMAND_UNIT_BUILD, &bcmd);
}

// Command unit with unitId to attack enemy with enemyId
void attack(int sid, int unitId, int enemyId)
{
    struct SAttackUnitCommand cmd = {unitId, -1, 0, TIME_OUT, enemyId};
    clbs[sid]->Engine_handleCommand(sid, COMMAND_TO_ID_ENGINE, -1,
        COMMAND_UNIT_ATTACK, &cmd);
}

// Command unit with unitId to move to position (x, z)
void move(int sid, int unitId, float x, float z)
{
    float pos[3] = {x, 25.0, z};
    struct SMoveUnitCommand cmd = {unitId, -1, 0, TIME_OUT, pos};
    clbs[sid]->Engine_handleCommand(sid, COMMAND_TO_ID_ENGINE, -1,
         COMMAND_UNIT_MOVE, &cmd);
}

// Retrieve current metal and energy status (6 values)
PyObject *getResourceUpdate(int sid)
{
    float currM = clbs[sid]->Economy_getCurrent(sid, METAL_ID);
    float currE = clbs[sid]->Economy_getCurrent(sid, ENERGY_ID);
    float incoM = clbs[sid]->Economy_getIncome(sid, METAL_ID);
    float incoE = clbs[sid]->Economy_getIncome(sid, ENERGY_ID);
    float usagM = clbs[sid]->Economy_getUsage(sid, METAL_ID);
    float usagE = clbs[sid]->Economy_getUsage(sid, ENERGY_ID);
    float storM = clbs[sid]->Economy_getStorage(sid, METAL_ID);
    float storE = clbs[sid]->Economy_getStorage(sid, ENERGY_ID);
    PyObject *rData = Py_BuildValue("(ffffffff)", currM, currE, incoM, incoE,
        usagM, usagE, storM, storE);
    return rData;
}

/* Toggles waiting mode of unit with unitId
 * if waiting -> stop waiting
 * else wait
 * Exactly like pressing the 'W' key while the unit is selected */
void wait(int sid, int unitId)
{
    // unitId, groupId, options, timeout
    struct SWaitUnitCommand cmd = {unitId, -1, (short) 0, TIME_OUT};
    // sid, toId, commandId=-1, commandTopic, commandData
    int rv = clbs[sid]->Engine_handleCommand(sid, COMMAND_TO_ID_ENGINE, -1,
         COMMAND_UNIT_WAIT, &cmd);
}

void quit(int sid)
{
    struct SSendTextMessageCommand cmd = {"/quit", 0};
    clbs[sid]->Engine_handleCommand(sid, COMMAND_TO_ID_ENGINE, -1,
         COMMAND_SEND_TEXT_MESSAGE, &cmd);
}
