/* Author:  Lyall Jonathan Di Trapani                                        */
#include "agent.h"                // Put first (includes Python.h)
#include <dlfcn.h>
#include <string.h>
#include "aidefines.h"
#include "SSkirmishAILibrary.h"   // 4 event functions
#include "SSkirmishAICallback.h"  // handleCommand and unsynched callback funcs

#define MAX_AGENTS 12
PyObject *AgentClass = (PyObject *) 0;
int agentIdsIndex = 0;
int agentIds[MAX_AGENTS];
PyObject *agents[MAX_AGENTS];
void *handle;

EXPORT(int) init(int skirmishAIId, const struct SSkirmishAICallback *callback) 
{
    if (AgentClass == 0) {
        //const char* dir = "/home/ljd/.spring/AI/Skirmish/ljd/";
        const char* dir = "AI/Skirmish/ljd/";
        size_t len = strlen(dir);
        char path[len + 8 + 1];             // String large enough for both
        strncpy(path, dir, len + 1);        // Copy string + null at end
        strncat(path, "proxy.so", 8 + 1);   // Cat proxy.so + null at end
        handle = dlopen(path, RTLD_NOW|RTLD_GLOBAL);
        PyObject *(*getAgentClass)();
        getAgentClass = dlsym(handle, "getAgentClass");
        AgentClass = getAgentClass(dir);
    }
    char buf[8];
    snprintf(buf, 8, "agent%d", skirmishAIId);
    const char *name = (const char *) &buf;
    PyObject *pCap = PyCapsule_New((void *) callback, name, NULL);
    agentIds[agentIdsIndex] = skirmishAIId;
    agentIdsIndex += 1;
    PyObject *agent = 
        PyObject_CallFunction(AgentClass, "(iO)", skirmishAIId, pCap);
    if (agent == NULL)
        PyErr_Print();
    agents[skirmishAIId] = agent;
    return 0;
}

EXPORT(int) release(int sid)
{
    printf("(Agent %d) Release called with agent count %d\n", sid, 
        agentIdsIndex);
    Py_DECREF(agents[sid]);
    agentIdsIndex -= 1;
    if (agentIdsIndex == 0) {
        printf("(Agent %d) Finalize python and unload proxy.so\n", sid);
        Py_DECREF(AgentClass);
        Py_Finalize();
        dlclose(handle);
    }
    return 0;
}

EXPORT(int) handleEvent(int skirmishAIId, int topic, const void *data)
{
    ljd_handlers[topic](skirmishAIId, data);
    return 0;
}
