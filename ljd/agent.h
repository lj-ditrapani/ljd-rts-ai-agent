/* Author:  Lyall Jonathan Di Trapani                                        */
#ifndef __AGENT_H
#define __AGENT_H

#include <Python.h>                 // Include this first!

extern PyObject *agents[];
typedef void (*handleEventFp)(int, const void *);
extern handleEventFp ljd_handlers[];
#endif
