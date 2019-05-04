import cv2
import requests
import numpy as np
import json
import argparse
import signal
import logging
import datetime, time
from scipy import spatial
import os

face_api = "http://192.168.1.3:5000/inferImage?returnFaceId=true&detector=yolo&returnFaceLandmarks=true"

parser = argparse.ArgumentParser(description='Home pro security system')
args = parser.parse_args()

# initialize database
db = {"names":[],"embeddings":[]}
dbtree = ""
try:
    db = json.loads(open('att_db.txt').read())
    print(db);
    dbtree = spatial.KDTree(db["embeddings"])
except:
    pass

# search for a face in the db
def identify_face(embedding):
    if dbtree != "":
        dist, idx = dbtree.query(embedding)                               
        name = db["names"][idx]
        if dist > (0.4):
            name = "unknown"
    else:
        name = "unknown"
    
    return name

# enroll a new face into db
def enroll(embedding, face):
    global dbtree
    facename = "Arun"    
    enroll.counter += 1
    if not os.path.exists("dbimg/%s"%(facename)):
        os.makedirs("dbimg/%s"%(facename))
     
    db["names"].append(facename)
    db["embeddings"].append(embedding)
    print("Enrolled %s into db!"%facename)

    dbtree = spatial.KDTree(db["embeddings"])

    with open('att_db.txt','w') as att:
        att.write(json.dumps(db))

    exit(0)

enroll.counter = 0

image = cv2.imread('1.jpg')
key = cv2.waitKey(1) & 0xFF

frame = cv2.resize(image, (int(320),int(240)))

r, imgbuf = cv2.imencode(".bmp", frame)    
image = {'pic':bytearray(imgbuf)}

r = requests.post(face_api, files=image)
result = r.json()

count = 0
if len(result) > 1:
    faces = result[:-1]
    diag = result[-1]['diagnostics'] 

    for face in faces:
        rect, embedding = [face[i] for i in ['faceRectangle','faceEmbeddings']]
        x,y,w,h, confidence = [rect[i] for i in ['left', 'top', 'width', 'height', 'confidence']]
        
        if confidence < 0.8:
            continue

        name = identify_face(embedding)
        if(name == "unknown"):
        	enroll(embedding, frame[y:y+h,x:x+w]) 

       	else:
       		if name != "unknown":
       			print("user already entered: " + name);




