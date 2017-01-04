#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
#import numpy as np
import gpstime as gps
#from gnsstoolbox import *
#import math
#import matplotlib.pyplot as plt
import pip
import os
import xml.etree.ElementTree as ET
import RtklibProcess


class ManageProcess():
    def __init__(self):
        #self.HomeDir = '/home/farah/DEPOT_CALCUL/'
        self.HomeDir = '/media/farah/Data/PPMD-PERSO/INFO_CODE/DEPOT_CALCUL/'

    def IsThereAnythingToDo(self):

        L = os.listdir(self.HomeDir)
        for d in L:
            if re.search('LOCKED',d):
                continue

            RequestDir = self.HomeDir + d
#            print(RequestDir)
            R = RtklibProcess.rtklib_process()
            R.read(RequestDir+'/request.xml')
#            tree = ET.parse(RequestDir+'/request.xml')
#            root = tree.getroot()
#            for child in root:
#                if child.tag=='options':
#                    for child2 in child:
#                        if re.search(child2.tag,'strategy'):
#                            R.strategy = child2.text
#                        if re.search(child2.tag,'station_number'):
#                            R.station_number = int(child2.text)
#                        if re.search(child2.tag,'max_distance'):
#                            R.max_distance = int(child2.text)
#
#                if child.tag=='files':
#                    for child2 in child:
#                        R.RnxFileList.append(child2[1].text)

            print(R)
            R.process()
            

#            os.rename(RequestDir,RequestDir+'_LOCKED')


if __name__ == "__main__":

    t1 = gps.gpstime()
#    print("Packages (local only) :")
#    for i in pip.get_installed_distributions(local_only=True):
#        print("-",i)

    S = ManageProcess()
    S.IsThereAnythingToDo()
    R = RtklibProcess.rtklib_process()
    #d =R.()
   # print(d)
    

    t2 = gps.gpstime()
    print ('%.3f sec elapsed ' % (t2-t1))



