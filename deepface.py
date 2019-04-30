"""

 * Author:    Azmath Moosa
 * Created:   5th May 2018
 * Description: Performs face recognition and marks attendance
 * Dependencies: Deepsight Face, Python 3 packages:- requests, argparse, opencv-python, scipy
 
"""

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
from tinydb import TinyDB, Query
import after_response


face_api = "http://192.168.43.192:5000/inferImage?returnFaceId=true&detector=yolo&returnFaceLandmarks=true"

# init logger
logger = logging.getLogger('Home pro security')
logger.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)

#visitors db
db_visitors = TinyDB('visitors.json')

# attendance register
att_reg = []
try:
    att_reg = json.loads(open('att_log').read())
except:
    pass

# parse arguments
parser = argparse.ArgumentParser(description='Home pro security System')
parser.add_argument('--enroll', action='store_true', help='Enable enrollment of unknown faces')
parser.add_argument('--src', action='store', default=0, nargs='?', help='Set video source; default is usb webcam')
parser.add_argument('--w', action='store', default=320, nargs='?', help='Set video width')
parser.add_argument('--h', action='store', default=240, nargs='?', help='Set video height')
args = parser.parse_args()

# initialize database
db = {"names":[],"embeddings":[]}
dbtree = ""
try:
    db = json.loads(open('face_data.txt').read())
    dbtree = spatial.KDTree(db["embeddings"])
except:
    pass

# start the camera
cap = cv2.VideoCapture(args.src)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(args.w))
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(args.h))
cap.set(cv2.CAP_PROP_FPS, 10)

fps = cap.get(cv2.CAP_PROP_FPS)
print("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps))

ret, frame = cap.read()

# catch exit signal
def signal_handler(signal, frame):
    if args.enroll:
        logger.info("Saving User DB")
        with open('face_data.txt','w') as att:
            att.write(json.dumps(db))
    
    logger.info("Saving user")
    with open('att_log','w') as att:
        att.write(json.dumps(att_reg, indent=4, sort_keys=True))

    exit(0)
signal.signal(signal.SIGINT, signal_handler)


# search for a face in the db
def identify_face(embedding):
    if dbtree != "":
        dist, idx = dbtree.query(embedding)                               
        name = db["names"][idx]
        print(name)
        if dist > 0.5:
            name = "unknown"
    else:
        name = "unknown"
    
    return name


# returns minutes since
def mins_since_last_log():
    return ((datetime.datetime.now() - datetime.datetime.strptime(att_reg[-1]['time'], '%Y-%m-%d %H:%M:%S')).seconds/60)


def mark_present(name):
    if len(att_reg) == 0: 
        logger.info("Detected %s"%name)
        stime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        att = {'name':name,'time':stime}
        att_reg.append(att)
        return

    if att_reg[-1]['name'] != name or mins_since_last_log() > 1:
        logger.info("Detected %s"%name)
        stime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        att = {'name':name,'time':stime}
        att_reg.append(att)        


# start processing
count = 0
user_count = 0;
prev_name = []
while True:
    
    _, framex = cap.read()
    key = cv2.waitKey(1) & 0xFF

    count += 1
    if count % 2 != 0:
        continue

    frame = cv2.resize(framex, (int(args.w),int(args.h)))
    
    r, imgbuf = cv2.imencode(".bmp", frame)    
    image = {'pic':bytearray(imgbuf)}
    
    r = requests.post(face_api, files=image)
    result = r.json()

    if len(result) > 1:
        faces = result[:-1]
        diag = result[-1]['diagnostics']        

        print(user_count)
        for face in faces:
            rect, embedding = [face[i] for i in ['faceRectangle','faceEmbeddings']]
            x,y,w,h, confidence = [rect[i] for i in ['left', 'top', 'width', 'height', 'confidence']]

            if confidence < 0.8:
                user_count = 0
                prev_name = []
                continue

            name = identify_face(embedding)
            if(name not in prev_name):
                prev_name.append(name)

            if name == "unknown":
                user_count += 1

            else:
                if name != "unknown":
                    user_count += 1

            mark_present(name)
            if(name not in prev_name):
                user_count = 0
                prev_name = []

            if user_count > 2:
                print("Found some one => ", prev_name)
                ts = time.time()
                url = str(ts) + '.jpg'
                dt = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                st = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')

                cv2.imwrite('visitors/' + url, frame)
                db_visitors.insert({'name': str(prev_name), 'url': url, 'date': dt, 'time': st})
                print("Inserted")

                visitors = ", ".join(prev_name)

                after_response.send_push(visitors, st)

                prev_name = []
                user_count = 0
                time.sleep(5)

            # cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,255),5,8)        
            # cv2.rectangle(frame, (x,y+h-20), (x+w,y+h), (255,0,255), -1, 8)
            # cv2.putText(frame, "%s"%(name), (x,y+h), cv2.FONT_HERSHEY_DUPLEX, 1,  (255,255,255),2,8)
  
        # cv2.putText(frame, diag['elapsedTime'], (0,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255))                

    # cv2.imshow("Home Pro Security System", frame)        
    if key == ord('q'):
        break

print("Exit")
