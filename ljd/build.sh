# Compile agent c code and run test
# Modify paths to match installation
binPath=/home/ljd/springDev/bin/spring
scriptPath=/home/ljd/.spring/AI/Skirmish/ljd
scriptName=scriptHuman.txt
scriptName=script.txt
scriptName=sml.txt
scriptName=med.txt
scriptName=lrg.txt
make all && ${binPath} ${scriptPath}/${scriptName} 2>&1 | tee out.test
