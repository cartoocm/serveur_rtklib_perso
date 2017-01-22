#usr/bin/python3
"""
Created on Sun Jan  8 22:42:41 2017

@author: farah
"""
import numpy as np
import re 
import ftplib
import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders
from bs4 import BeautifulSoup
import pyproj

def send_mail(send_to, subject, text, files ,project_directory):
    """
        input : the adress of the receiver 
                the subject of the email to send
                the text joining the e-mail
                the files: list of the attachement files to send
                project_directory : the directory of configuration file
        output : an e_mail sent to the receiver adress
        
    """
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
        print (os.path.abspath(f))
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(f,"r").read() )
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="{0}"'.format(os.path.basename(f)))
        msg.attach(part)

    smtp = smtplib.SMTP(host, port)
    if isTls: smtp.starttls()
    smtp.login(user,passwd)
    smtp.sendmail(send_from, send_to, msg.as_string())
    print("sucess sending mail")
    smtp.quit()

def get_files_by_ext(directory,ext):
    os.chdir(directory)  # elle était commentée avant 
    print("get_ext_file",directory)
    listeFiles=[]
    for file in os.listdir((directory)): #os.path.abspath
        if file.endswith(ext):
            #print(file)
            listeFiles.append(os.path.join(directory,file))
    return listeFiles
    
    
def connexionftp(projectDirectory):
        """connexion au serveur ftp et ouverture de la session
           - adresseftp: adresse du serveur ftp
           - nom: nom de l'utilisateur enregistré ('anonymous' par défaut)
           - mdpasse: mot de passe de l'utilisateur ('anonymous@' par défaut)
           - passif: active ou désactive le mode passif (True par défaut)
           retourne la variable 'ftplib.FTP' après connexion et ouverture de session
        """
        with open(os.path.join(projectDirectory,"ftp.conf.xml")) as f:
        #with open("ftp.conf.xml") as f:
            content = f.read()

        y= BeautifulSoup(content, "lxml")
         #markup_type=markup_type))
        adresseftp = y.servers.server1.host.contents[0]
        nom = y.servers.server1.user.contents[0]
        mdpasse = y.servers.server1.passwd.contents[0]
        passif = y.servers.server1.passif.contents[0]

        
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
    """
    
    """
    print("get_project_path_121_ddddddddddddddddddddddddddddddddddddd",os.getcwd())
    #with open(os.path.join(dire,"project.conf.xml")) as f:
    with open("project.conf.xml") as f:

        content = f.read()
    y= BeautifulSoup(content, "lxml")
    pathProject = y.paths.project_path.contents[0]
    return pathProject
    
def get_exeConf_path(projectDirectory):
    
    """
    
    """
    # i modified the nomenclature of the function that used to take no parameter now i added
    #projectDirectory in order to find the correct path while i changed the pasth in getting extention
    #pathProject = get_project_path() 
    with open(os.path.join(projectDirectory,"project.conf.xml")) as f:
   # with open("project.conf.xml") as f:
        content = f.read()
    y= BeautifulSoup(content, "lxml")
    return y.paths.exe_conf_path.contents[0]    
    
def get_observation_path(projectDirectory):
    """
    return the path of the observation path where all the downloaded data and the final repport
    """
    #pathProject = get_project_path() 
    with open(os.path.join(projectDirectory,"project.conf.xml") )as f:   
    #with open("project.conf.xml") as f:
        content = f.read()
    y= BeautifulSoup(content, "lxml")
    return y.paths.observation_path.contents[0] 

def get_receiver_path():
    
    with open("project.conf.xml") as f:
        content = f.read()
    y= BeautifulSoup(content, "lxml")
    return y.paths.receiver_path.contents[0]   
    
def get_ephemerides_path(projectDirectory):
    """
    return the path of ftp from where to download the ephemerides
    """
    with open(os.path.join(projectDirectory,"project.conf.xml")) as f:
        content = f.read()
    y= BeautifulSoup(content, "lxml")
    return y.paths.ftp_ephemerides_path.contents[0] 

def pod_pos( obs_dir, sigma_init):
    """
        function of ponderation of the multiple observation baselines
        the outputs of least squares : X_chap(X,Y,Z), QX_chap :the cov matrix
        sigma02 : the factor of variance
        list_station of the station that were integrated in the calculation of 
        the finale position where the ambiguity was solved
    """
    posFiles = get_files_by_ext(obs_dir,"pos")
    list_station = []
    list_coor_rec = []
    Var_cov = []
    for file in posFiles:
        """Read file"""
        print("osb_dir******************"+obs_dir+"fileooooooooooooooo"+file)
        posFile = open(file,"r")
        """Get file lines"""
        lines = posFile.readlines()
        posFile.close()
        """Go to the last line"""
        last_line = lines[-1]
        element_list = last_line.strip().split()
        valQ = float(element_list[5])
        # valQ l'élémént dans le fichier.pos qui indique
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
    I = np.eye(3)
    A=I
    for i in range(n-1):
        A = np.concatenate((A,I), axis = 0)
    
    # constructing B
    B =[list_coor_rec[i][j] for i in range(0,len(list_coor_rec))  for j in range(0,len(list_coor_rec[i]))]
    B = np.asarray(B).reshape(len(B),1)
    N = A.T.dot(P).dot(A)
    K = A.T.dot(P).dot(B)
  #  X_chap = np.linalg.inv(N).dot(K) 
    X_chap = np.dot(np.linalg.inv(N),K)
    Qxx = np.linalg.inv(N)
    V = B - A.dot(X_chap)
    sigma02 = (V.T.dot(P).dot(V))/((n*3) -3)
    QX_chap = sigma02 *np.linalg.inv(N)
    #Q_XE = np.dot(sigma02[0][0],(Qxx))
    
        
    return  P, X_chap,QX_chap,sigma02,V,list_station
    
def generateStd(QX_chap):

    S_xx = np.abs((QX_chap[0][0]))**(0.5)
    S_yy = np.abs((QX_chap[1][1]))**(0.5)
    S_zz = np.abs((QX_chap[2][2]))**(0.5)
    S_xy = (QX_chap[0][1])
    S_xz = (QX_chap[0][2])
    S_yz = (QX_chap[1][2])
    return S_xx ,S_yy,S_zz
        
def generateStdENU():
    pass

def convertDDToDMS(angle):
    """ input : DD angle
        output : DMS angle
    """
    d = int(angle)
    m = int((angle - d)* 60)
    s = (angle - d - m/60)*3600
    DMS = str(d)+" "+str(m)+" "+str(s) # str((s,"%.6f"))
    return DMS   #d ,m , s


def gettingCoordinate(X_chap,QX_chap):
    """
        input X Y Z
        output longitude , latitude Hell 
        and alti 
    
    """
    #Kl , Ql, P , A , B, X_chap,QX_chap,sigma02,V =pod_pos(1)
    lambert93 = pyproj.Proj("+proj=lcc +lat_1=49 +lat_2=44 +lat_0=46.5 +lon_0=3 +x_0=700000 +y_0=6600000 +ellps=GRS80 +geoidgrids=RAF09.gtx,null  +towgs84=0,0,0,0,0,0,0 +units=m +no_defs")
    #ecef = pyproj.Proj(proj='geocent', ellps='WGS84', datum='WGS84')
    ecef = pyproj.Proj("+proj=geocent +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs")
    #rg__ =pyproj.Proj(init='epsg:2154')
    #tuplell = rg__(X_chap[0][0],  X_chap[1][0], inverse = True)
    #lla = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')
    rgf93ll = pyproj.Proj("+proj=latlong  +lat_1=49 +lat_2=44 +lat_0=46.5 +lon_0=3 +x_0=700000 +y_0=6600000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs")
    lon ,  lat , he = pyproj.transform(ecef, rgf93ll , X_chap[0][0],  X_chap[1][0],  X_chap[2][0] )    

    E,N,H = pyproj.transform(ecef, lambert93, X_chap[0][0],  X_chap[1][0],  X_chap[2][0])
    #lon, lat, alt = pyproj.transform(ecef, lla, X_chap[0][0],  X_chap[1][0],  X_chap[2][0], radians=False)
    #E,N = rgf93(lon , lat )
    # matrice de rotaion     
    d2r = np.pi/180
    Rot = np.array([[-np.sin(lon*d2r) , np.cos(lat*d2r),0],
                    [-np.sin(lat*d2r)*np.cos(lon*d2r),-np.sin(lat*d2r)*np.sin(lon*d2r),np.cos(lat*d2r)],
                    [np.cos(lat*d2r)*np.cos(lon*d2r),np.cos(lat*d2r)*np.sin(lon*d2r),-np.sin(lat*d2r)]])
                    
    varENU = Rot.dot(QX_chap).dot(Rot.T)
    #return lon, lat, alt,E,N ,varENU  ,tuplell
    return  E,N ,H, varENU , lon ,  lat , he
    

"""
def whatToWriteInRepport():
    
    if re.search('ANT # / TYPE',line[60:]):
                ANT_N=line[0:20].rstrip()
    if re.search('ANTENNA: DELTA H/E/N',line[60:]):
        val = line[0:60].split()
        dH=float(val[0])
        dE=float(val[1])
        dN=float(val[2])
        """

def read_antenna_name(antenna_lines):
    """ the name of antenna in return from the atx file """
    firstLine =antenna_lines[0]
    antennaName =firstLine.split()[0]
    #frequency =firstLine.split()[1]
    return antennaName #,frequency
def find_antenna_info(atx_lines, antName):
    """ it return the information related to the antenna specified by its name "antName"  in list"""
    antenna_start_e = re.compile(".*START OF ANTENNA")
    antenna_end_e = re.compile(".*END OF ANTENNA")
    
    antenna_curr_lines =[]
    reading_antenna = False

    for line in atx_lines: 
        if not reading_antenna :
            m = re.match(antenna_start_e,line)
            if m :
                reading_antenna = True
                #print("antenna_start")
        else:
            m = re.match(antenna_end_e,line)
            if not m:
                antenna_curr_lines.append(line)
            else:
                reading_antenna = False
                antennaName =read_antenna_name(antenna_curr_lines)
                if antennaName == antName :
                    print("find antenna")
                    return antenna_curr_lines
                antenna_curr_lines = []
    return None
    
def find_ENH_atx(antenna_lines):
    listENH = []
    listFreq = []
    for line in antenna_lines:
        m = re.match(".*NORTH / EAST / UP" ,line)
        m2 = re.match(".*START OF FREQUENCY" ,line)
        if m2 :
            listFreq.append(line.split()[0])
        if m :
            enh = line.split()[0:3]
            listENH.append(enh) 
    return listENH ,listFreq
    
if __name__ == "__main__":
     #Kl , Ql, P , A , B, X_chap,QX_chap,sigma02,V=pod_pos(10)
#     print("P",P,"\n\n",A,"\n\n",B,"\nKl\n" ,Kl,"\n\nQl\n" , Ql,"last\n",X_chap,"\nQX_chap\n",QX_chap,"\nsigma02\n",sigma02,"\nV\n",V)
#     print ("fuuuuuuuuuuuuuuuuuuuuuuuu ")
#     lon, lat, alt,E,N ,varENU,tuplell =gettingCoordinate()
#     print ("\nlon, lat, alt,E,N ,varENU\n",lon, lat, alt,E,N ,varENU)
#     print("************rg__***********",tuplell)
     X_chap = np.array([[ 4576765.88053333],[  461664.53346667],[ 4404250.9063    ]] )
     QX_chap = np.array( [[3.61419634e-07,1.00394343e-04 ,1.75690100e-04],[1.00394343e-04,9.03549085e-08, -1.25492928e-04],[  1.75690100e-04,-1.25492928e-04, 4.24166098e-07]] )     
     E,N ,H, varENU , lon ,  lat , he =gettingCoordinate(X_chap,QX_chap)
     print("E,N ,H ,varENU\n",E,N ,H,varENU)
     list_coor_rec =np.array( [[4576765.897, 461664.5461, 4404250.8885],\
     [4576765.6539, 461664.4103, 4404250.8123],\
     [4576765.8759, 461664.5259, 4404250.9035],\
     [4576765.9114, 461664.5643, 4404250.9387],\
     [4576765.9062, 461664.516, 4404250.929],\
     [4576765.7851, 461664.4875, 4404250.8555]])
     print("\n",QX_chap[1][1]**(0.5))

                

    
