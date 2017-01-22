#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
#import numpy as np
import gpstime as gps
import os
import RtklibProcess
import RtklibUtils as utils


class ManageProcess():
    def __init__(self):

        self.HomeDir = utils.get_receiver_path()+"/"

    def IsThereAnythingToDo(self):

        L = os.listdir(self.HomeDir)
        R = RtklibProcess.rtklib_process()
        R.projectPath = utils.get_project_path()
        R.observationPath =  utils.get_observation_path(R.projectPath)
        R.exeConfPath =     utils.get_exeConf_path(R.projectPath)
        R.ephemeridPath = utils.get_ephemerides_path(R.projectPath)
        for d in L:
            if re.search('LOCKED',d):
                continue

            RequestDir = self.HomeDir + d
            R.process(RequestDir)
            os.rename(RequestDir,RequestDir+'_LOCKED')

            




if __name__ == "__main__":

    t1 = gps.gpstime()
    
    print ("starting here procces path",os.getcwd())
    S = ManageProcess()
    S.IsThereAnythingToDo()
    
    t2 = gps.gpstime()
    print ('%.3f sec elapsed ' % (t2-t1))



