
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


face_api = "http://192.168.43.192:5000/inferImage?returnFaceId=true&detector=yolo&returnFaceLandmarks=true"

# init logger
logger = logging.getLogger('Attendance')
logger.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)


# attendance register
att_reg = []
try:
    att_reg = json.loads(open('att_log').read())
except:
    pass

db = {"names":[],"embeddings":[]}
dbtree = ""
try:
    db = json.loads(open('att_db.txt').read())
    dbtree = spatial.KDTree(db["embeddings"])
except:
    pass

# start the camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(320))
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(240))
cap.set(cv2.CAP_PROP_FPS, 20)

ret, frame = cap.read()



# search for a face in the db
def identify_face(embedding):
    if dbtree != "":
        dist, idx = dbtree.query(embedding)                               
        name = db["names"][idx]
        if dist > (0.4 if args.enroll else 0.5):
            name = "unknown"
    else:
        name = "unknown"
    
    return name

# start processing
count = 0
while True:
    
    _, framex = cap.read()
    key = cv2.waitKey(1) & 0xFF

    count += 1
    if count % 2 != 0:
        continue

    frame = cv2.resize(framex, (int(320),int(240)))

    r, imgbuf = cv2.imencode(".bmp", frame)    
    image = {'pic':bytearray(imgbuf)}

    r = requests.post(face_api, files=image)
    result = r.json()
    print(result)

    if len(result) > 1:
        faces = result[:-1]
        diag = result[-1]['diagnostics']  

        for face in faces:
            rect, embedding = [face[i] for i in ['faceRectangle','faceEmbeddings']]
            x,y,w,h, confidence = [rect[i] for i in ['left', 'top', 'width', 'height', 'confidence']]

            if confidence < 0.8:
                continue

            name = identify_face(embedding)
            if  name == "unknown":
                # enroll(embedding, frame[y:y+h,x:x+w])
                print("for storing");
            else:
                if name != "unknown":
                    mark_present(name)

            cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,255),5,8)        
            cv2.rectangle(frame, (x,y+h-20), (x+w,y+h), (255,0,255), -1, 8)
            cv2.putText(frame, "%s"%(name), (x,y+h), cv2.FONT_HERSHEY_DUPLEX, 1,  (255,255,255),2,8)
                        
        cv2.putText(frame, diag['elapsedTime'], (0,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255))     


    cv2.imshow("Attendance", frame)        
    if key == ord('q'):
        break

print("Exit")



