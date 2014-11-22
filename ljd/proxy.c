#include <Python.h>
#include <string.h>

PyObject *getAgentClass(const char* dir)
{
    size_t len = strlen(dir);
    char code[len + 48];
    strncpy(code, "import sys; sys.path = ['", 26); 
    strncat(code, dir, len + 1);
    strncat(code, "python/'] + sys.path\n", 21);
    Py_Initialize();
    PyRun_SimpleString(code);           // Adds python src dir to sys.path[0]
    PyObject *pName = PyString_FromString("agent");
    if (!pName) {
        printf("*** <proxy.c> Error making agent name pname\n");
        PyErr_Print();
    }
    PyObject *pModule = PyImport_Import(pName);
    if (!pModule) {
        printf("*** <proxy.c> Error loading agent (pModule) ***\n");
        PyErr_Print();
    }
    Py_DECREF(pName);
    PyObject *pDict = PyModule_GetDict(pModule);
    Py_DECREF(pModule);
    PyObject *agentClass = PyDict_GetItemString(pDict, "Agent");
    Py_DECREF(pDict);
    return agentClass;
}
