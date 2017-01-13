#usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  8 22:42:41 2017

@author: farah
"""
import numpy as np
import ftplib
import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders
#from BeautifulSoup import BeautifulSoup
from bs4 import BeautifulSoup

def send_mail(send_to, subject, text, files ,project_directory):
    
    with open(os.path.join(project_directory,"mail.conf.xml")) as f:
        content = f.read()
    y= BeautifulSoup(content, "lxml")

    send_from = y.server.send_from.contents[0] 
    host = y.server.host.contents[0] 
    port = y.server.port.contents[0] 
    user = y.server.user.contents[0] 
    passwd = y.server.passwd.contents[0] 
    isTls = y.server.tls.contents[0]
    
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime = True)
    msg['Subject'] = subject

    msg.attach( MIMEText(text) )

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(f,"rb").read() )
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="{0}"'.format(os.path.basename(f)))
        msg.attach(part)

    smtp = smtplib.SMTP(host, port)
    if isTls: smtp.starttls()
    smtp.login(user,passwd)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()

def get_files_by_ext(directory,ext):
    os.chdir(directory)
    listeFiles=[]
    for file in os.listdir(directory):
        if file.endswith(ext):
            #print(file)
            listeFiles.append(file)
    return listeFiles
    
    
def connexionftp():
        """connexion au serveur ftp et ouverture de la session
           - adresseftp: adresse du serveur ftp
           - nom: nom de l'utilisateur enregistré ('anonymous' par défaut)
           - mdpasse: mot de passe de l'utilisateur ('anonymous@' par défaut)
           - passif: active ou désactive le mode passif (True par défaut)
           retourne la variable 'ftplib.FTP' après connexion et ouverture de session
        """
#        try:
        pathProject = get_project_path()    
        with open(os.path.join(pathProject,"ftp.conf.xml")) as f:
            content = f.read()

        #y = BeautifulSoup(content)
        y= BeautifulSoup(content, "lxml")
         #markup_type=markup_type))

        adresseftp = y.servers.server1.host.contents[0]
        nom = y.servers.server1.user.contents[0]
        mdpasse = y.servers.server1.passwd.contents[0]
        passif = y.servers.server1.passif.contents[0]
        #adresseftp = y.servers.server1.host.contents[0]
#        for tag in y.other.preprocessing_queue:
#            print(tag)  
        
        try :
            print (adresseftp , nom , mdpasse , passif)
            ftp = ftplib.FTP()
            ftp.connect(adresseftp)
            ftp.login(nom, mdpasse)
            ftp.set_pasv(passif)
            print("connexion établie")
        except:
            adresseftp = y.servers.server2.host.contents[0]
            ftp = ftplib.FTP()
            ftp.connect()
            ftp.login(nom, mdpasse)
            ftp.set_pasv(passif)
#          
        return ftp
        
def fermerftp(ftp):
        """ferme la connexion ftp
           - ftp: variable 'ftplib.FTP' sur une connexion ouverte
        """
        try:
            ftp.quit()
        except:
            ftp.close()    
def get_project_path():
    with open("project.conf.xml") as f:
        content = f.read()
    y= BeautifulSoup(content, "lxml")
    pathProject = y.paths.project_path.contents[0]
    return pathProject
    
def get_exeConf_path():
    with open("project.conf.xml") as f:
        content = f.read()
    y= BeautifulSoup(content, "lxml")
    return y.paths.exe_conf_path.contents[0]    
    

def pod_pos(sigma_init):
    #Get all POS files
    observationPath = '/media/farah/Data/PPMD-PERSO/INFO_CODE/DEPOT_OBS' #get_observation_path()
    posFiles = get_files_by_ext(observationPath,"pos")
    list_station = []
    list_coor_rec = []
    Var_cov = []
    for file in posFiles:
        """Read file"""
        posFile = open(file,"r")
        """Get file lines"""
        lines = posFile.readlines()
        posFile.close()
        """Go to the last line"""
        last_line = lines[-1]
        element_list = last_line.strip().split()
        valQ = float(element_list[5])
        if valQ != 2 :
                list_station.append(os.path.basename(file))
                list_coor_rec.append([float(element_list[2]),float(element_list[3]),float(element_list[4])])
                """Get var and _cov values"""
                S_xx = np.double(element_list[7])
                S_yy = np.double(element_list[8])
                S_zz = np.double(element_list[9])
                S_xy = np.double(element_list[10])
                S_xz = np.double(element_list[12])
                S_yz = np.double(element_list[11])
                mat_var_cov = np.array([[S_xx**(2),S_xy,S_xz],[S_xy,S_yy**(2),S_yz],[S_xz,S_yz,S_zz**(2)]])
                Var_cov.append(mat_var_cov)
                
    Kl=np.zeros((len(list_station)*3,len(list_station)*3))
    for i in range(len(list_station)):
        Kl[3*i:3*i+3,3*i:3*i+3]=Var_cov[i]
    print("list_coor_rec",list_coor_rec)
    Ql = (1/sigma_init**(2))*Kl
    P = np.linalg.inv(Ql)
    # defining matrix A
    n = len(list_station)
    I = np.eye(n)
    A=I
    for i in range(n-1):
        A = np.concatenate((A,I), axis = 0)
    
    # constructing B
    B =[list_coor_rec[i][j] for i in range(0,len(list_coor_rec))  for j in range(0,len(list_coor_rec[i]))]
    B = np.asarray(B).reshape(len(B),1)
    N = A.T.dot(P).dot(A)
    K = A.T.dot(P).dot(B)
    X_chap = np.linalg.inv(N).dot(K) 
    Qxx = np.linalg.inv(N)
    V = B - A.dot(X_chap)
    sigma02 = (V.T.dot(P).dot(V))/((n*3) -3)
    QX_chap = sigma02 *np.linalg.inv(N)
    
        
    return Kl , Ql, P , A , B, X_chap,QX_chap,sigma02,V
        
    
    
if __name__ == "__main__":
     Kl , Ql, P , A , B, X_chap,QX_chap,sigma02,V=pod_pos(1000)
     print("P",P,"\n\n",A,"\n\n",B,"\n\n","Kl\n" ,Kl,"\n\nQl\n" , Ql,"last\n",X_chap,"\nQX_chap\n",QX_chap,"\nsigma02\n",sigma02,"\nV\n",V)
     print ("fuuuuuuuuuuuuuuuuuuuuuuuu ")
    
                

    