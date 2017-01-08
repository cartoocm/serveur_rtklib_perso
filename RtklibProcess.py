#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on %(date)s

@author: %(username)s
"""


import re
import os
import sys
import numpy as np
import gpstime as gps
import gnsstoolbox.rinex_o as rx
#from gnsstoolbox import *
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import RtklibUtils as utils
from Station import *

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
        self.proche_stations_list = []
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
                        if re.search(child2.tag,'user_mail'):
                            self.mail = child2.text

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

            print ("first obs time",self.tStart.doy)
        if hasattr (head,'TIME_OF_LAST_OBS'):
            self.tEnd = head.TIME_OF_LAST_OBS
#           print ("end obs time",self.tEnd)
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
       
        all_stations_sorted_filtred =list( filter(lambda station : station.last_dist < self.max_distance*1000 , all_stations_sorted))

        print("here-------------------------------------------------------------",len(all_stations_sorted_filtred))

        proche_stations =self.prepare_proche_station(all_stations_sorted_filtred,self.station_number)

#        for station in all_stations_sorted:
#            print(station.nom,station.last_dist)
        
        print("here-------------------------------------------------------------",len(proche_stations))

        self.proche_stations_list = proche_stations
        self.proche_stations_names = [station.nom for station in proche_stations]
        print("les n stations les plus proches et dont les distances inférieure de la distance maximal \n\n")
            
        for station in (proche_stations):
            #self.proche_stations_list.append(
            print("//////////////////////////////////////////////////////////////////////////////////")
            print("nom "+station.nom + " X "+str(station.X)+" Y "+str(station.Y)+" Z "+str(station.Z)+" distance au recepteur "+str(station.last_dist))
            print("//////////////////////////////////////////////////////////////////////////////////")
            #print(station.nom,self.station_number, station.last_dist )
        print ("name list",self.proche_stations_names)
#        for station in all_stations_filtred:
#            print("finalement",station.nom,station.last_dist,self.max_distance)
        
        

        print("approximated coordinate",Xrec,Yrec,Zrec)
        return (Xrec,Yrec,Zrec)

    def prepare_proche_station(self,all_sorted_list,station_number):
        ftp = utils.connexionftp() 
        proche_stations_list =[]
        ficftp_dir = "pub/data/"+str(self.tStart.yyyy)+"/"+str(self.tStart.doy)+"/data_30"
        ftp.cwd(ficftp_dir)
        curennt_ftp_dir = ftp.pwd()
        ftp.cwd("/")
        ftp.cwd(ficftp_dir)
        ftp_list_file = ftp.nlst() # la liste des fichiers dans la réportoire ftp
        for stat in   all_sorted_list :
            ficftp_name = stat.nom.lower()+str(self.tStart.doy)+str("0.")+str(self.tStart.yy)+"d.Z"
#            ficftp = os.path.join(ficftp_dir,ficftp_name)
            
            if ficftp_name in ftp_list_file:
                print(ficftp_name,  " is in this directory")
                proche_stations_list.append(stat)
        
            if (len(proche_stations_list) == station_number ):
                break
        ftp.cwd("/")
        ftp.cwd(curennt_ftp_dir) 
        ftp.quit()
        return proche_stations_list

    def process(self):
        """
        Fonction qui se déclenche pour le commencement du process de calcum
        """
        print('Starting rtklib automatic process we are here')
        print("dirrrr",self.directory)
        print(self.directory,"\n\n",self.RnxFileList[0])
        #self.rinex_info(os.path.join(self.directory,self.RnxFileList[0]))
            
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
        ftp_list_file = ftp.nlst() # la liste des fichiers dans la réportoire ftp
        if not ficftp_name in ftp_list_file:
            print(ficftp_name,  " is not in this directory")
        else:
            
            if ficdsk==None:
                ficdsk=ficftp_name
                
            with open(os.path.join(repdsk, ficdsk), 'wb') as f:
                ftp.retrbinary('RETR ' + ficftp_name, f.write)
                downloadedFilePath = os.path.join(repdsk,ficftp_name)
                print("file :",downloadedFilePath," is successfully downloaded")
        ftp.cwd("/")
        ftp.cwd(curennt_ftp_dir) 

        
        
    def download_radio(self, ftp,ficftp, repdsk='.', ficdsk=None):
        """télécharge le fichier ficftp du serv. ftp dans le rép. repdsk du disque
           - ftp: variable 'ftplib.FTP' sur une session ouverte
           - ficftp: nom du fichier ftp dans le répertoire courant
           - repdsk: répertoire du disque dans lequel il faut placer le fichier
           - ficdsk: si mentionné => c'est le nom qui sera utilisé sur disque
        """
        print(ficftp)
        #ficftp_name est le nom de fichier à télécharger à partir de la station et fictftp_dir son current directory
        ficftp_dir, ficftp_name1 = os.path.split(ficftp)        
        ficftp_name2 ="brdm"+ficftp_name1[4:-1]
        ficftp_names = [ficftp_name1, ficftp_name2]
        #ficftp_names contient la liste de possibilité des nom des fichiers des orbites radiodiffusé
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
                downloadedFilePath = os.path.join(repdsk,ficftp_name)
        ftp.cwd("/")
        ftp.cwd(curennt_ftp_dir)  
      
    def unzip(self, obs_dir):
        os.chdir(obs_dir)
        for file in os.listdir(obs_dir):
            if (os.path.isfile(file) and file.endswith("Z")):
                print(file)
                os.system("gzip -d "+file )
    def gzip_crx(self, obs_dir):
        os.chdir(obs_dir)
        for file in os.listdir(obs_dir):
            if file.endswith("d"):
                print(file)
                #os.system("gzip -d "+file )
                os.system("./CRX2RNX " +file+" -s")
                # effacer observation .d avec décompression .o
                os.remove(file)
                

                
        

    def calcul_rtklib(self, rep_obs, rep_rec):
           os.chdir(rep_obs)
           file_sp3 = utils.get_files_by_ext(rep_obs,"sp3")[0]
           #un seul fichier sp3
           file_brdc = utils.get_files_by_ext(rep_obs,"n")[0]
           #un seul fichier brdc
           files_obs = utils.get_files_by_ext(rep_obs,"o")
           #les fichiers observations des stations
           file_rec = utils.get_files_by_ext(rep_rec,"o")[0]
           file_conf = utils.get_files_by_ext(rep_obs,"conf")[0]
#           print ("test extensio file33333333333333333333333333333333333333")
#           print(file_sp3,"\n\n",file_brdc,"\n\n",files_obs,"\n\n",file_rec,"\n\n",file_conf)
           for i in range(len(files_obs)):
           # a =os.system("./rnx2rtkp" 17301530.16o test.16o brdc1530.16n igr18993.sp3 -k static.conf -o out.pos")
           #print(a)
               os.system("./rnx2rtkp " +os.path.join(rep_rec,file_rec)+" "+files_obs[i]+" "+file_brdc+" "+file_sp3+" -k "+file_conf+" -o out"+str(i)+".pos")
               print("./rnx2rtkp " +os.path.join(rep_rec,file_rec)+" "+files_obs[i]+" "+file_brdc+" "+file_sp3+" -k "+file_conf+" -o out"+str(i)+".pos")
   
    
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

    #print("ftp://rgpdata.ensg.eu/pub/data/"+str(R.tStart.yyyy)+"/"+str(R.tStart.doy)+"/data_30/"+stat1+str(R.tStart.doy)+str("0.")+str(R.tStart.yy)+"d.Z")
    
    print(R.directory)
    obs_dir = os.path.abspath(os.path.join(R.directory,"../..","DEPOT_OBS"))
    print("chemin",obs_dir)

    if not os.path.exists(obs_dir):
        os.makedirs(obs_dir)
   # os.mkdir(obs_dir) does not work FileExistsError
    for stat in R.proche_stations_names:
        ftp=utils.connexionftp()
        ficftp ="pub/data/"+str(R.tStart.yyyy)+"/"+str(R.tStart.doy)+"/data_30/"+stat.lower()+str(R.tStart.doy)+str("0.")+str(R.tStart.yy)+"d.Z"
        R.downloadftp(ftp,ficftp,obs_dir)
        ftp.quit()
       
   
       
    # téléchargement des orbites précise
    
    wk= R.tStart.wk
    wd = R.tStart.wd
    #print("week in gps",wk,int(wd))
    #igr18993.sp3.Z
    ficftp_orb_pr ="pub/products/ephemerides/"+str(wk)+"/igr"+str(wk)+str(int(wd))+".sp3.Z"
    #print(ficftp_orb_pr)
    #orb_pre = 
    ftp=utils.connexionftp()
    R.downloadftp(ftp,ficftp_orb_pr,obs_dir)
    #R.gzip_crx(obs_dir)
    print("téléchargement des orbites précise")
    ftp.quit()
    
    #    téléchargement des éphémérides radio diffusés
    ficftp_radio ="pub/data/"+str(R.tStart.yyyy)+"/"+str(R.tStart.doy)+"/data_30/"+"brdc"+str(R.tStart.doy)+str("0.")+str(R.tStart.yy)+"n.Z"
    # ftp://rgpdata.ign.fr/pub/data/2016/153/data_30/brdc1530.16n.Z   --- n : gps g : glonass
    ftp=utils.connexionftp()
    R.download_radio(ftp,ficftp_radio,obs_dir)
    
    R.unzip(obs_dir)     
     # décompression hanataka 
    R.gzip_crx(obs_dir)    
    #R.calcul_rtklib(obs_dir)
    R.calcul_rtklib(obs_dir,os.path.abspath(R.directory))
    
    #after extracting n pos file for the position our receiver we are going to send mail 
    
    pos_files = utils.get_files_by_ext(obs_dir,"pos")
    utils.send_mail('serveurRtklib@gmail.com', R.mail, "subject", "here is a test",files=pos_files, server="smtp.gmail.com", port=587, username='serveurRtklib@gmail.com', password='rtklibensg', isTls=True) 
    t2 = gps.gpstime()
    #print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"+file_rec, type(file_rec))
    print ('%.3f sec elapsed ' % (t2-t1))


