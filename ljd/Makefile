# Path to Python.h
incPyDir=/usr/include/python2.7
# Path to libpython2.7.so
libpy=/usr/lib/libpython2.7.so
# Where agent is installed (will put libSkirmishAI.so here)
binDir=/home/ljd/springDev/share/games/spring/AI/Skirmish/ljd/0.1
# Spring engine source code path
source=/home/ljd/usb/school/AFIT_MSCS/spring_Dev.0
incDir=${source}/rts/ExternalAI/Interface
incRtsDir=${source}/rts

all: ${binDir}/libSkirmishAI.so proxy.so python/clb.so

${binDir}/libSkirmishAI.so: agent.o handlers.o
	gcc -shared agent.o handlers.o ${libpy} -ldl -o ${binDir}/libSkirmishAI.so

agent.o: agent.c agent.h
	gcc -c -fpic agent.c -I${incDir} -I${incRtsDir} -I${incPyDir}

handlers.o: handlers.c agent.h
	gcc -c -fpic handlers.c -I${incDir} -I${incRtsDir} -I${incPyDir}

python/clb.so: clb.o
	gcc -shared clb.o ${libpy} -o python/clb.so

clb.o: clb.c
	gcc -c -fpic clb.c -I${incDir} -I${incRtsDir} -I${incPyDir}

proxy.so: proxy.o
	gcc -shared proxy.o ${libpy} -o proxy.so

proxy.o: proxy.c
	gcc -c -fpic proxy.c -I${incPyDir}

redo: Makefile
	make clean
	make all

clean:
	rm -f *.so python/clb.so *.o python/*.pyc ${binDir}/libSkirmishAI.so
