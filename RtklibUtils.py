#usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  8 22:42:41 2017

@author: farah
"""
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
#    
        print (adresseftp , nom , mdpasse , passif)
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
    pathProject = y.paths.project.contents[0]
    return pathProject