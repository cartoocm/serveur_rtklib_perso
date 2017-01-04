# -*- coding: utf-8 -*-
"""
Created on %(date)s

@author: %(username)s
"""
import re
import os
import numpy as np
import gpstime as gps
import gnsstoolbox.rinex_o as rx
from gnsstoolbox import *
#import math
#import matplotlib.pyplot as plt
#import skimage
import pip
import xml.etree.ElementTree as ET
#from StringIO import StringIO
#from operator import itemgetter, attrgetter, methodcaller

class rtklib_process():
    def __init__(self):
        self.strategy = 'static'
        self.station_number = 10
        self.max_distance = 100
        self.mail = ""
        self.directory = "" 
        self.RnxFileList = []
        self.all_stations =[]
        self.tStart = gps.gpstime()
        self.tEnd = gps.gpstime()
        
    def read(self,filename):
            tree = ET.parse(filename)
            root = tree.getroot()
            for child in root:
                if child.tag=='options':
                    for child2 in child:
                        if re.search(child2.tag,'strategy'):
                            self.strategy = child2.text
                        if re.search(child2.tag,'station_number'):
                            self.station_number = int(child2.text)
                        if re.search(child2.tag,'max_distance'):
                            self.max_distance = int(child2.text)

                if child.tag=='files':
                    for child2 in child:
                        self.RnxFileList.append(child2[1].text)
            self.directory = os.path.dirname(filename)
            

    def __str__(self):
        s = "%-20s: %s\n" % ("Strategy",self.strategy)
        s+= "%-20s: %s\n" % ("Station number",self.station_number)
        s+= "%-20s: %s\n" % ("Max distance",self.max_distance)
        s+= "%-20s: %s\n" % ("Mail",self.mail)

        s+= "Files :\n"
        for f in self.RnxFileList:
             s+= "- %s\n" % (f)

        return s
    def rinex_info(self, filename):
        myrinex = rx.rinex_o()
        #filename = str(self.RnxFileList) 
        #filename = '/home/farah/projet__/17301530.16o'
        ret = myrinex.load_rinex_o(filename)
        print("return",ret)
        head= myrinex.headers[0]
        if hasattr (head,'X'):
            Xrec = head.X
        if hasattr (head,'Y'):
            Yrec = head.Y   
        if hasattr (head,'Z'):
            Zrec = head.Z
        RGP = np.genfromtxt('stations.txt')  #   , dtype =None #lgenfromtxt does convert string the name of station 
        # to nan so i compenstate to number 0 -- 449 
#        Xsta = RGP[:,1]
#        Ysta = RGP[:,2]
#        Zsta = RGP[:,3]
#        n = RGP.shape[0]
#        dist =[np.sqrt(((Xsta[i] - X)**(2 ))+ ((Ysta[i] - Y)**(2)) +(Zsta[i]-Z )**(2)) for i in range(n) ] 
#        dist =(np.asarray(dist)).reshape(n,1)
#        numsta = np.arange(0,n).reshape(n,1)
#        #name =( np.asarray(RGP[:,0])).reshape(n,1)
#        list_dist_n = np.hstack((numsta,dist))
#        #sorted(student_tuples, key=lambda student: student[2])   # sort by age        
#        res = sorted(list_dist_n,key=lambda distance : distance[1] )
        #print (res)
        #return res
        
        #lecture stations
        stations_fichier = open("stations.txt", "r")
        stations_texte = stations_fichier.readlines() #liste lignes du fichier
        stations_fichier.close()
        # on va créer attribut all_stations qui contient les ligne du fichier splité selon le format
        # on appel au constructeur pour créer les objet station et on ajoute a chaque fois l'objet 
        # à la la liste
        self.all_stations=[]
        for line in stations_texte:
            data_station=line.split()
            self.all_stations.append( Station(data_station[0],float(data_station[1]),float(data_station[2]),float(data_station[3])) )
        
        for station in self.all_stations:
            print(station.nom)
            print(station.calc_dist(Xrec,Yrec,Zrec))
        # all_stations_sorted est une liste de toutes les objets Stations trié par leur distance % au rec
        all_stations_sorted = sorted(self.all_stations,key=lambda station : station.last_dist )# objet entré Station (nommé station)critére detrie station.last_dist
        
        for station in all_stations_sorted:
            print(station.nom,station.last_dist)
        
        proche_stations = filter(lambda station : station.last_dist < self.max_distance*1000 , 
                                 all_stations_sorted[0:self.station_number])
        self.all_stations = proche_stations
        proche_stations_names = [station.nom for station in proche_stations]
        print("les n stations les plus proches et dont les distances inférieure de la distance maximal \n\n")
        for station in self.all_stations:
            print(station.nom,self.station_number, station.last_dist )
        print ("name list",proche_stations_names)
#        for station in all_stations_filtred:
#            print("finalement",station.nom,station.last_dist,self.max_distance)
        
        
        
        
        print("approximated coordinate",Xrec,Yrec,Zrec)
        return (Xrec,Yrec,Zrec)

        

    def process(self):
        print('Starting rtklib automatic process')
        print(self.directory,"\n\n",self.RnxFileList[0])
        self.rinex_info(os.path.join(self.directory,self.RnxFileList[0]))
        
        

class Station():
    def __init__(self,nom , X = 0,Y = 0, Z = 0):
        self.nom = nom
        self.X = X
        self.Y = Y
        self.Z = Z
        self.last_dist=-1
    def calc_dist(self,Xrec,Yrec,Zrec):
        self.last_dist = np.sqrt(((self.X - Xrec)**(2 ))+ ((self.Y - Yrec)**(2)) +(self.Z- Zrec )**(2))
        return self.last_dist
        
    

    
    
    
if __name__ == "__main__":

    t1 = gps.gpstime()
    print("Packages (local only) :")
#    for i in pip.get_installed_distributions(local_only=True):
#        print("-",i)
    R = rtklib_process()
    
#    filename = '/home/farah/DEPOT_CALCUL/request.xml'  # pour récuperer le numéro de stations demandé
#    R.read(filename)
    R.rinex_info()
   # R.proche_station(n=10)
    t2 = gps.gpstime()
    print ('%.3f sec elapsed ' % (t2-t1))



