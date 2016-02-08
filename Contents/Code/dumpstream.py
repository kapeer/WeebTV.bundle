#!/usr/bin/python
import os,sys,subprocess,signal
from time import sleep
from datetime import datetime,timedelta

rtmpStr = None
duration = 3600
if len(sys.argv) > 1:
    rtmpStr = sys.argv[1]
    
if len(sys.argv) > 2:
    duration = sys.argv[2]
    
if rtmpStr:
    args = rtmpStr.split(" ")
    p = subprocess.Popen(rtmpStr,shell=True,stdout=subprocess.PIPE,preexec_fn=os.setsid)
    startTime = currentTime = datetime.now()
    
    bRun = True
    while bRun:
        sleep(15)
        currentTime = datetime.now()
        timeElapsed = (currentTime - startTime).total_seconds()
        print "{} seconds elapsed".format(timeElapsed)
        if int(timeElapsed) > int(duration):
            bRun = False

    os.killpg(p.pid,signal.SIGTERM)
else:
    print "ERROR"
print "DONE"
