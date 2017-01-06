#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on %(date)s

@author: %(username)s
"""
import ftplib
import re
import os
import sys
import numpy as np
import gpstime as gps
import gnsstoolbox.rinex_o as rx
#from gnsstoolbox import *
#import math
#import matplotlib.pyplot as plt
#import skimage
#import pip
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
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
        self.proche_stations_names =[]
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
            print (self.directory)

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
        """
        fonction qui s'en sert de fichier rinex pour déduire les stations plus proches et les coord approx du 
        récepteur
        """
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
        
        if hasattr (head,'TIME_OF_FIRST_OBS'):
            self.tStart = head.TIME_OF_FIRST_OBS
            #self.doy = self.tStart.doy
            #self.yy= self.tStart.yy
            print ("first obs time",self.tStart.doy)
        if hasattr (head,'TIME_OF_LAST_OBS'):
            self.tEnd = head.TIME_OF_LAST_OBS
            print ("end obs time",self.tEnd)
#
        #RGP = np.genfromtxt('stations.txt',comments ="#",skip_header=4)  #   , dtype =None #lgenfromtxt does convert string the name of station 

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
            #print(station.nom)
            station.calc_dist(Xrec,Yrec,Zrec)
        # all_stations_sorted est une liste de toutes les objets Stations trié par leur distance % au rec
        all_stations_sorted = sorted(self.all_stations,key=lambda station : station.last_dist )# objet entré Station (nommé station)critére detrie station.last_dist
        
#        for station in all_stations_sorted:
#            print(station.nom,station.last_dist)
        
        proche_stations = filter(lambda station : station.last_dist < self.max_distance*1000 , 
                                 all_stations_sorted[0:self.station_number])
        self.all_stations = proche_stations
        self.proche_stations_names = [station.nom for station in proche_stations]
        print("les n stations les plus proches et dont les distances inférieure de la distance maximal \n\n")
            
        for station in list(proche_stations):
            print(station.nom,self.station_number, station.last_dist )
        print ("name list",self.proche_stations_names)
#        for station in all_stations_filtred:
#            print("finalement",station.nom,station.last_dist,self.max_distance)
        
        

        print("approximated coordinate",Xrec,Yrec,Zrec)
        return (Xrec,Yrec,Zrec)

        

    def process(self):
        """
        Fonction qui se déclenche pour le commencement du process de calcum
        """
        print('Starting rtklib automatic process we are here')
        print("dirrrr",self.directory)
        print(self.directory,"\n\n",self.RnxFileList[0])
        #self.rinex_info(os.path.join(self.directory,self.RnxFileList[0]))
        
    def connexionftp(self,adresseftp="rgpdata.ensg.eu", nom='anonymous', mdpasse='anonymous@', passif=True):
        """connexion au serveur ftp et ouverture de la session
           - adresseftp: adresse du serveur ftp
           - nom: nom de l'utilisateur enregistré ('anonymous' par défaut)
           - mdpasse: mot de passe de l'utilisateur ('anonymous@' par défaut)
           - passif: active ou désactive le mode passif (True par défaut)
           retourne la variable 'ftplib.FTP' après connexion et ouverture de session
        """
#        try:
            
        ftp = ftplib.FTP()
        ftp.connect(adresseftp)
        ftp.login(nom, mdpasse)
        ftp.set_pasv(passif)
        print("connexion établie")
#        except:
##            ftp = ftplib.FTP()
##            ftp.connect("ftp://rgpdata.ign.fr")
##            ftp.login(nom, mdpasse)
##            ftp.set_pasv(passif)
#            self.connexionftp("ftp://rgpdata.ign.fr")
        return ftp
        
    def fermerftp(self,ftp):
        """ferme la connexion ftp
           - ftp: variable 'ftplib.FTP' sur une connexion ouverte
        """
        try:
            ftp.quit()
        except:
            ftp.close()
            
    def downloadftp(self, ftp,ficftp, repdsk='.', ficdsk=None):
        """télécharge le fichier ficftp du serv. ftp dans le rép. repdsk du disque
           - ftp: variable 'ftplib.FTP' sur une session ouverte
           - ficftp: nom du fichier ftp dans le répertoire courant
           - repdsk: répertoire du disque dans lequel il faut placer le fichier
           - ficdsk: si mentionné => c'est le nom qui sera utilisé sur disque
        """
        print(ficftp)
        #ficftp_name est le nom de fichhier à télécharger à partir de la station et fictftp_dir son current directory
        ficftp_dir, ficftp_name = os.path.split(ficftp)        
        curennt_ftp_dir = ftp.pwd()
        ftp.cwd("/")
        ftp.cwd(ficftp_dir)
        ftp_list_file = ftp.nlst()
        if not ficftp_name in ftp_list_file:
            print(ficftp_name,  " is not in this directory")
        else:
            
            if ficdsk==None:
                ficdsk=ficftp_name
                
            with open(os.path.join(repdsk, ficdsk), 'wb') as f:
                ftp.retrbinary('RETR ' + ficftp_name, f.write)
        ftp.cwd("/")
        ftp.cwd(curennt_ftp_dir) 
        print("succès téléchargement radio diffusé")
        
    def download_radio(self, ftp,ficftp, repdsk='.', ficdsk=None):
        """télécharge le fichier ficftp du serv. ftp dans le rép. repdsk du disque
           - ftp: variable 'ftplib.FTP' sur une session ouverte
           - ficftp: nom du fichier ftp dans le répertoire courant
           - repdsk: répertoire du disque dans lequel il faut placer le fichier
           - ficdsk: si mentionné => c'est le nom qui sera utilisé sur disque
        """
        print(ficftp)
        #ficftp_name est le nom de fichhier à télécharger à partir de la station et fictftp_dir son current directory
        ficftp_dir, ficftp_name1 = os.path.split(ficftp)        
        ficftp_name2 ="brdm"+ficftp_name1[4:-1]
        ficftp_names = [ficftp_name1, ficftp_name2]
        curennt_ftp_dir = ftp.pwd()
        ftp.cwd("/")
        ftp.cwd(ficftp_dir)
        ftp_list_file = ftp.nlst()
        
        ficftp_name = None
        for name in ficftp_names:
            if not name in ftp_list_file:
                print(name,  " is not in this directory")
            else :
                ficftp_name = name
                break
            #+str(R.tStart.doy)+str("0.")+str(R.tStart.yy)+"n.Z"
            
        if ficftp_name:            
            if ficdsk==None:
                ficdsk=ficftp_name
                
            with open(os.path.join(repdsk, ficdsk), 'wb') as f:
                ftp.retrbinary('RETR ' + ficftp_name, f.write)
        ftp.cwd("/")
        ftp.cwd(curennt_ftp_dir)   
        #self.fermerftp(ftp)
        
# 
#ftp.cwd(repftp)

        

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
    
    print("Nb parametres: ",len(sys.argv))
    if (len(sys.argv)<2):
        print("Usage: ....")
        exit(0)
    request_file=sys.argv[1]
    print("Request file: "+request_file)
    
    print("Packages (local only) :")
#    for i in pip.get_installed_distributions(local_only=True):
#        print("-",i)
    R = rtklib_process()

    #R.directory = '/media/farah/Data/PPMD-PERSO/INFO_CODE/DEPOT_CALCUL/2016-11-04T12:12:56Z_172.31.42.114'  # pour récuperer le numéro de stations demandé
    R.read(request_file)
    R.rinex_info(os.path.join(R.directory,R.RnxFileList[0]))
    #R.rinex_info('/media/farah/Data/PPMD-PERSO/INFO_CODE/DEPOT_CALCUL/2016-11-04T12:12:56Z_172.31.42.114/17301530.16o')
    #R.rinex_info(filename)
    print("test  qppel des variable")
    print("listeeeeeeeeeeeee",R.proche_stations_names)
    print("doy**************",R.tStart.doy)
    stat1 = R.proche_stations_names[0].lower()
    #ftp.pwd("ftp://rgpdata.ensg.eu/data/"+R.tStart.yyyy+"/"+R.tStart.doy+"/data_30/"+stat1)
    #ftp://rgpdata.ensg.eu/pub/data/2016/017/data_30/abmf0170.16d.Z
    print("ftp://rgpdata.ensg.eu/pub/data/"+str(R.tStart.yyyy)+"/"+str(R.tStart.doy)
    +"/data_30/"+stat1+str(R.tStart.doy)+str("0.")+str(R.tStart.yy)+"d.Z")
    
    #ficftp ="pub/data/"+str(R.tStart.yyyy)+"/"+str(R.tStart.doy)+"/data_30/"+stat+str(R.tStart.doy)+str("0.")+str(R.tStart.yy)+"d.Z"
    #fichier_ =stat1+str(R.tStart.doy)+"0."+str(R.tStart.yy)+"d.Z"
    print(R.directory)
    obs_dir = os.path.abspath(os.path.join(R.directory,"../..","DEPOT_OBS",os.path.basename(R.directory)))
    print("chemin",obs_dir)

    if not os.path.exists(obs_dir):
        os.makedirs(obs_dir)
   # os.mkdir(obs_dir) does not work FileExistsError
    for stat in R.proche_stations_names:
        ftp=R.connexionftp()
        ficftp ="pub/data/"+str(R.tStart.yyyy)+"/"+str(R.tStart.doy)+"/data_30/"+stat.lower()+str(R.tStart.doy)+str("0.")+str(R.tStart.yy)+"d.Z"
        R.downloadftp(ftp,ficftp,obs_dir)
        ftp.quit()
        
    # téléchargement des orbites précise
    
    wk= R.tStart.wk
    wd = R.tStart.wd
    print("week in gps",wk,int(wd))
    #igr18993.sp3.Z
    ficftp_orb_pr ="pub/products/ephemerides/"+str(wk)+"/igr"+str(wk)+str(int(wd))+".sp3.Z"
    #print(ficftp_orb_pr)
    #orb_pre = 
    ftp=R.connexionftp()
    R.downloadftp(ftp,ficftp_orb_pr,obs_dir)
    print("téléchargement des orbites précise")
    ftp.quit()
    
    #    téléchargement des éphémérides radio diffusés
    ficftp_radio ="pub/data/"+str(R.tStart.yyyy)+"/"+str(R.tStart.doy)+"/data_30/"+"brdc"+str(R.tStart.doy)+str("0.")+str(R.tStart.yy)+"n.Z"
    # ftp://rgpdata.ign.fr/pub/data/2016/153/data_30/brdc1530.16n.Z   --- n : gps g : glonass
    ftp=R.connexionftp()
    R.downloadftp(ftp,ficftp_radio,obs_dir)
    t2 = gps.gpstime()
    print ('%.3f sec elapsed ' % (t2-t1))


