#!/usr/bin/python3
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
        self.projectPath = utils.get_project_path()
        #self.requestPath = utils.get_receiver_path()
        self.observationPath = utils.get_observation_path()
        self.exeConfPath = utils.get_exeConf_path()
        self.ephemeridPath = utils.get_ephemerides_path()
        
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
            #self.directory = os.path.dirname(filename)
            #print (self.directory)

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
        ret = myrinex.load_rinex_o(filename)  # à remplacer par LoadRinexO(filename)
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
            
        #for station in (proche_stations):
            ##self.proche_stations_list.append(
            #print("//////////////////////////////////////////////////////////////////////////////////")
            #print("nom "+station.nom + " X "+str(station.X)+" Y "+str(station.Y)+" Z "+str(station.Z)+" distance au recepteur "+str(station.last_dist))
            #print("//////////////////////////////////////////////////////////////////////////////////")
            ##print(station.nom,self.station_number, station.last_dist )
        #print ("name list",self.proche_stations_names)
#        for station in all_stations_filtred:
#            print("finalement",station.nom,station.last_dist,self.max_distance)
        
        

        print("approximated coordinate",Xrec,Yrec,Zrec)
        return (Xrec,Yrec,Zrec, head)

    def prepare_proche_station(self,all_sorted_list,station_number):
        """ this function would find the n nearest stations and that have data at the date of observation 
            on the ftp server
            output : the list of name of the n nearest stations     
        """        
        
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

           
    def downloadftp(self, ftp,ficftp, repdsk='.', ficdsk=None):
        """télécharge le fichier ficftp du serv. ftp dans le rép. repdsk du disque
           - ftp: variable 'ftplib.FTP' sur une session ouverte
           - ficftp: nom du fichier ftp dans le répertoire courant
           - repdsk: répertoire du disque dans lequel il faut placer le fichier
           - ficdsk: si mentionné => c'est le nom qui sera utilisé sur disque
        """
        print(ficftp)
        #ficftp_name est le nom de fichier à télécharger à partir de la station et fictftp_dir son current directory
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
        
    def download_or_precise(self, ftp,ficftp, repdsk='.', ficdsk=None):
        """download precise orbite 
        """
        ficftp_dir, ficftp_name1 = os.path.split(ficftp) 
        ficftp_name2 = "igr"+ficftp_name1[3:]
        ficftp_name3 = "igu"+ficftp_name1[3:]
        ficftp_names = [ficftp_name1, ficftp_name2,ficftp_name3]
        curennt_ftp_dir = ftp.pwd()
        ftp.cwd("/")
        ftp.cwd(ficftp_dir)
        ftp_list_file = ftp.nlst()
        # boucle igs en premier psi trouve pas igr sinon igu
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
#                downloadedFilePath = os.path.join(repdsk,ficftp_name)
        ftp.cwd("/")
        ftp.cwd(curennt_ftp_dir) 
        print("precise succées,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,")
      
    def unzip(self, obs_dir):
        #os.chdir(obs_dir)
        print("obs_dir in zip ",obs_dir)
        for file in os.listdir(obs_dir):
            print("d5alllllllllllllllllll",file)
            if (os.path.isfile(os.path.join(obs_dir,file)) and file.endswith("Z")):
                print("zipppppppppppppppppppppppppppp",os.path.join(obs_dir,file))
                os.system("gzip -d "+os.path.join(obs_dir,file))
                
                
    def gzip_crx(self, obs_dir):
        #os.chdir(obs_dir)
        for file in os.listdir(obs_dir):
            if file.endswith("d"):
                print(file)
                #os.system("gzip -d "+file )
                os.system(self.exeConfPath+"/CRX2RNX " +os.path.join(obs_dir,file)+" -s")
                # effacer observation .d avec décompression .o
                os.remove(os.path.join(obs_dir,file)) # in case u need the file without hanataka decompression
                

                
        

    def calcul_rtklib(self, obs_dir, rep_rec):
           #os.chdir(obs_dir)
           file_sp3 = utils.get_files_by_ext(obs_dir,"sp3")[0]
           #un seul fichier sp3
           file_brdc = utils.get_files_by_ext(obs_dir,"n")[0]
           #un seul fichier brdc
           files_obs = utils.get_files_by_ext(obs_dir,"o")
           #les fichiers observations des stations
           file_rec = utils.get_files_by_ext(rep_rec,"o")[0]
           file_conf = utils.get_files_by_ext(self.exeConfPath,"conf")[0]
#           print ("test extensio file33333333333333333333333333333333333333")
#           print(file_sp3,"\n\n",file_brdc,"\n\n",files_obs,"\n\n",file_rec,"\n\n",file_conf)
           for i in range(len(files_obs)):
           # a =os.system("./rnx2rtkp" 17301530.16o test.16o brdc1530.16n igr18993.sp3 -k static.conf -o out.pos")
           #print(a)
               os.system(self.exeConfPath+"/rnx2rtkp " +os.path.join(rep_rec,file_rec)+" "+os.path.join(obs_dir,files_obs[i])+" "+os.path.join(obs_dir,file_brdc)+" "+os.path.join(obs_dir,file_sp3)+" -k "+os.path.join(self.exeConfPath,file_conf)+" -o "+os.path.join(obs_dir,os.path.splitext(os.path.basename(files_obs[i]))[0])+".pos")
               print(self.exeConfPath+"/rnx2rtkp " +os.path.join(rep_rec,file_rec)+" "+files_obs[i]+" "+file_brdc+" "+file_sp3+" -k "+os.path.join(self.exeConfPath,file_conf)+" -o "+os.path.splitext(os.path.basename(files_obs[i]))[0]+".pos")
   
    def whatToWriteInRepport(self,obs_dir,requestDir):
        
        t=gps.gpstime()
        #obs_dir ="/media/farah/Data/PPMD-PERSO/INFO_CODE/DEPOT_OBS" 
        #obs_dir =utils.get_obs_path()   
        print(os.path.join(obs_dir,"rapport.txt"))
        with open(os.path.join(obs_dir,"rapport.txt"), "w") as f:
            print("success 1 ecriture fichier")
            
            
            f.write("------------------------------------------------------------------\n")
            f.write("ENSG \t\t\tCALCUL GNSS EN LIGNE \n \t\t\t\tRTKLIB 2.4.2 \t\t\n")
            f.write("------------------------------------------------------------------\n")
            f.write("\n\n")
            orb =utils.get_files_by_ext(obs_dir,"sp3")[0]
            f.write("ORBITES\t\t\t:"+utils.get_files_by_ext(obs_dir,"sp3")[0]+".Z\n")
            f.write("1/ ELEMENTS EN ENTREE \n")
            f.write("------------------------------------------------------------------")
            (Xrec,Yrec,Zrec, head) = self.rinex_info(os.path.join(requestDir,self.RnxFileList[0]))
            f.write(head.__str__())
#            lines="FICHIER RINEX :"+self.RnxFileList[0]+"\n"+"EN-TETE NOM STATION :"+head.MARKER_NAME+"\n"+\
#            "EN-TETE NUMERO    :"+head.MARKER_NUMBER+"\nEN-TETE RECEPTEUR   : "+head.REC_TYPE+"EN-TETE ANTENNE :"+\
#            head.ANT_TYPE+"\nEN-TETE POSITION  : " +Xrec+"\t"+Yrec+"\t"+Zrec+"\n"+"EN-TETE ANT H/E/N  : "+\
#            head.dH+"\t"+head.dE+"\n"+head.dN+"\n"+"NOMBRES D'EPOQUES"+len(head.epochs)+"\n"+"DATE DEBUT     : "+\
#            str(print(self.tStart))+"\nDATE FIN   : "+str(print(self.tEnd))
#            #antennaFile = utils.get
            # l'idee c'est trouver l'instance de nom de l'antenne et puis rendre la premiére occurence 
            # et puis la deuxième qui est la dernière de NORTH / EAST / UP 
            # f.write(lines)
            P, X_chap,QX_chap,sigma02,V = utils.pod_pos(obs_dir,10)
            
            
            
            
            
            print("success 2 ecriture fichier")
        f.close()
        return f
    
    
        
    
    
    def process(self,requestDir):
        """
        Fonction qui se déclenche pour le commencement du process de calcul
        """
        print('Starting rtklib automatic process we are here')
        print("dirrrr",requestDir)
        #print(requestDir,"\n\n",self.RnxFileList[0])
        #self.rinex_info(os.path.join(self.directory,self.RnxFileList[0]))
     
    #def execute(self,requestDir):
        t1 = gps.gpstime()
    
#        print("Nb parametres: ",len(sys.argv))
#        if (len(sys.argv)<2):
#            print("Usage: ....")
#            exit(0)
        #request_file=sys.argv[1]
        #print("Request file: "+request_file)
        
        requestFile = requestDir+'/request.xml'
        
        
        
        #R = rtklib_process()

        #R.directory = '/media/farah/Data/PPMD-PERSO/INFO_CODE/DEPOT_CALCUL/2016-11-04T12:12:56Z_172.31.42.114'  # pour récuperer le numéro de stations demandé
        #Create directory with the same name of the subdirctory which contains the request file
        obs_dir = os.path.join(self.observationPath,os.path.basename(requestDir))
        #os.makedirs( obs_dir ,0755 )
        self.read(requestFile)
        self.rinex_info(os.path.join(requestDir,self.RnxFileList[0]))
        #R.rinex_info('/media/farah/Data/PPMD-PERSO/INFO_CODE/DEPOT_CALCUL/2016-11-04T12:12:56Z_172.31.42.114/17301530.16o')
        #R.rinex_info(filename)


        #print("ftp://rgpdata.ensg.eu/pub/data/"+str(R.tStart.yyyy)+"/"+str(R.tStart.doy)+"/data_30/"+stat1+str(R.tStart.doy)+str("0.")+str(R.tStart.yy)+"d.Z")

        #print(R.directory) en attente de mise a jour
        #####obs_dir = os.path.abspath(os.path.join(R.directory,"../..","DEPOT_OBS"))
        
        print("chemin",obs_dir)

        if not os.path.exists(obs_dir):
            os.makedirs(obs_dir)
        # os.mkdir(obs_dir) does not work FileExistsError
        for stat in self.proche_stations_names:
            ftp=utils.connexionftp()
            ficftp ="pub/data/"+str(self.tStart.yyyy)+"/"+str(self.tStart.doy)+"/data_30/"+stat.lower()+str(self.tStart.doy)+str("0.")+str(self.tStart.yy)+"d.Z"
            self.downloadftp(ftp,ficftp,obs_dir)
            ftp.quit()
           

           
        # téléchargement des orbites précise
        project_directory = os.getcwd()
        print("dddddddddddddddddddddddddddddddddddddddddddd",project_directory)
        wk= self.tStart.wk
        wd = self.tStart.wd
        #print("week in gps",wk,int(wd))
        #igr18993.sp3.Z
        ficftp_orb_pr = self.ephemeridPath+"/"+str(wk)+"/igs"+str(wk)+str(int(wd))+".sp3.Z"
        
        #print(ficftp_orb_pr)
        #orb_pre = 
        ftp=utils.connexionftp()
        #-----------------------------------------------remplacement par fct-----------    
        #    self.downloadftp(ftp,ficftp_orb_pr,obs_dir)
        self.download_or_precise(ftp,ficftp_orb_pr, obs_dir)

        #self.gzip_crx(obs_dir)
        print("téléchargement des orbites précise")
        ftp.quit()

        #    téléchargement des éphémérides radio diffusés
        ficftp_radio ="pub/data/"+str(self.tStart.yyyy)+"/"+str(self.tStart.doy)+"/data_30/"+"brdc"+str(self.tStart.doy)+str("0.")+str(self.tStart.yy)+"n.Z"
        # ftp://rgpdata.ign.fr/pub/data/2016/153/data_30/brdc1530.16n.Z   --- n : gps g : glonass
        ftp=utils.connexionftp()
        self.download_radio(ftp,ficftp_radio,obs_dir)

        self.unzip(obs_dir)     
         # décompression hanataka 
        self.gzip_crx(obs_dir)    
        #self.calcul_rtklib(obs_dir)
        self.calcul_rtklib(obs_dir,requestDir)

        #after extracting n pos file for the position our receiver we are going to send mail 

        #pos_files = utils.get_files_by_ext(obs_dir,"pos")
        #utils.send_mail('serveurRtklib@gmail.com', self.mail, "subject", "here is a test",files=pos_files, server="smtp.gmail.com", port=587, username='serveurRtklib@gmail.com', password='rtklibensg', isTls=True) 
        
        rapport = self.whatToWriteInRepport(obs_dir,requestDir)
        rapports = utils.get_files_by_ext(obs_dir,"txt")
        #os.chdir(project_directory)
        
        
        #rapports.append(rapport)
        #send_mail(send_to, subject, text, files ,project_directory)
        print("ddddddddddddddddddddddddddddddddddddd",os.getcwd())        
        utils.send_mail(self.mail, "Position final", "Veuillez trouvez ci-joint le rapport de calcul GNSS",rapports,self.projectPath) 
        #print("hereetttttttttttttttttttttttttttttttttttttttttttttttttt\n",self.observationPath)
        print("ddddddddddddddddddddddddddddddddddddd",os.getcwd())  
        t2 = gps.gpstime()
        #print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"+file_rec, type(file_rec))
        print ('%.3f sec elapsed ' % (t2-t1))


    


if __name__ == "__main__" :
    #utils.send_mail(self.mail, "Position final", "Veuillez trouvez ci-joint le rapport de calcul GNSS",rapports,self.projectPath) 
   # utils.send_mail('serveurRtklib@gmail.com', self.mail, "subject", "here is a test",files=pos_files, server="smtp.gmail.com", port=587, username='serveurRtklib@gmail.com', password='rtklibensg', isTls=True) 
    print("hello")
    
