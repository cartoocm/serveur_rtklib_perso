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

def send_mail( send_from, send_to, subject, text, files=[], server="localhost", port=587, username='', password='', isTls=True):
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

    smtp = smtplib.SMTP(server, port)
    if isTls: smtp.starttls()
    smtp.login(username,password)
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
    
    
def connexionftp(adresseftp="rgpdata.ensg.eu", nom='anonymous', mdpasse='anonymous@', passif=True):
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
        
def fermerftp(ftp):
        """ferme la connexion ftp
           - ftp: variable 'ftplib.FTP' sur une connexion ouverte
        """
        try:
            ftp.quit()
        except:
            ftp.close()    