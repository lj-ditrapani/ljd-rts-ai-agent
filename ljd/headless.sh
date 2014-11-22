binPath=/home/ljd/springDev/bin/spring-headless
scriptPath=/home/ljd/.spring/AI/Skirmish/ljd
scriptName=scriptHuman.txt
scriptName=script.txt
scriptName=sml.txt
scriptName=lrg.txt
scriptName=med.txt
make all && ${binPath} ${scriptPath}/${scriptName} 2>&1 | tee out.test
