#usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  8 22:42:41 2017

@author: farah
"""

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

send_mail('serveurRtklib@gmail.com', 'farah.battikh@ensg.eu', "subject", "here is a test", files=['/media/farah/Data/PPMD-PERSO/e_mail_py/file1.txt','/media/farah/Data/PPMD-PERSO/e_mail_py/file2.txt'], server="smtp.gmail.com", port=587, username='serveurRtklib@gmail.com', password='rtklibensg', isTls=True) 