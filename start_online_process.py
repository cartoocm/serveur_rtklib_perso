#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
#import numpy as np
import gpstime as gps
#from gnsstoolbox import *
#import math
#import matplotlib.pyplot as plt
import os
import xml.etree.ElementTree as ET
import RtklibProcess
import RtklibUtils as utils


class ManageProcess():
    def __init__(self):
        #self.HomeDir = '/home/farah/DEPOT_CALCUL/'
        self.HomeDir = utils.get_receiver_path()+"/"

        #'/media/farah/Data/PPMD-PERSO/INFO_CODE/DEPOT_CALCUL/'

    def IsThereAnythingToDo(self):

        L = os.listdir(self.HomeDir)
        for d in L:
            if re.search('LOCKED',d):
                continue

            RequestDir = self.HomeDir + d
#            print(RequestDir)
            R = RtklibProcess.rtklib_process()
            R.projectPath = utils.get_project_path()
            R.process(RequestDir)
            os.rename(RequestDir,RequestDir+'_LOCKED')
#            self.read(RequestDir+'/request.xml')

#            tree = ET.parse(RequestDir+'/request.xml')
#            root = tree.getroot()
#            for child in root:
#                if child.tag=='options':
#                    for child2 in child:
#                        if re.search(child2.tag,'strategy'):
#                            self.strategy = child2.text
#                        if re.search(child2.tag,'station_number'):
#                            self.station_number = int(child2.text)
#                        if re.search(child2.tag,'max_distance'):
#                            self.max_distance = int(child2.text)
#
#                if child.tag=='files':
#                    for child2 in child:
#                        self.RnxFileList.append(child2[1].text)

            #print(R)
            #self.process()
            




if __name__ == "__main__":

    t1 = gps.gpstime()
#    print("Packages (local only) :")
#    for i in pip.get_installed_distributions(local_only=True):
#        print("-",i)

    S = ManageProcess()
    S.IsThereAnythingToDo()
    #R = RtklibProcess.rtklib_process()
    #d =self.()
   # print(d)
    

    t2 = gps.gpstime()
    print ('%.3f sec elapsed ' % (t2-t1))



