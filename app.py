from flask import Flask, request, jsonify, send_from_directory
import base64
from tinydb import TinyDB, Query
import time
import os
import socket
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
import json

#raspi ip
IP = 'http://192.168.43.90:8080/'

# api address
face_api = "http://192.168.43.192:5000/inferImage?returnFaceId=true&detector=yolo&returnFaceLandmarks=true"

parser = argparse.ArgumentParser(description='Home pro security system')
args = parser.parse_args()

# initialize database
db = {"names": [], "embeddings": []}
dbtree = ""
try:
    db = json.loads(open('face_data.txt').read())
    dbtree = spatial.KDTree(db["embeddings"])
except:
    pass

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello world"

@app.route("/api/users")
def list_users():

    users = TinyDB('db/users.json')
    users_list = users.all();
    for user in users_list:
        user['pro_pic'] = IP + 'images/' + user['name'] + '/' + user['pro_pic']

    return jsonify(users_list)

@app.route("/api/access", methods=['POST'])
def user_access_permission():
    # access = request.form.access;
    name = request.form["name"];
    access = request.form['access'];

    users = TinyDB('db/users.json')
    User = Query();
    users.update({'access': json.loads(access)}, User.name == name)

    return jsonify({"success": True, "message": "asdf"})

# save new user
@app.route("/api/user", methods=['GET', 'POST'])
def user():
    if request.method == 'POST':
        imageBlob = request.form['image']
        name = request.form['name'].rstrip().lstrip()
        access = request.form['access']

        # find position of name in db
        flag = False
        for i in db['names']:
            if(i == name):
                flag = True
        if(flag):
            return jsonify({"success": False, "message": "User already exist"})


        imgdata = base64.b64decode(imageBlob)

        # save it
        ts = int(time.time())
        filepath = 'images/' + name
        filename = filepath + '/' + str(ts) + '.jpg'

        if not os.path.isdir(filepath):
            os.mkdir(filepath)

        with open(filename, 'wb') as f:
            f.write(imgdata)

            enroll.counter = 0

            image = cv2.imread(filename)
            key = cv2.waitKey(1) & 0xFF

            frame = cv2.resize(image, (int(320), int(240)))

            r, imgbuf = cv2.imencode(".bmp", frame)
            image = {'pic': bytearray(imgbuf)}

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

                    return_name = identify_face(embedding)
                    if(return_name == "unknown"):
                        is_entered = enroll(embedding, frame[y:y+h, x:x+w], name);
                        #store it in the db
                        users = TinyDB('db/users.json')
                        users.insert({'name': name, 'access': json.loads(access), 'pro_pic': str(ts) + '.jpg'})
                        return jsonify({"success": True, "message": "User added successfully"})
                    else:
                        if return_name != "unknown":
                            return jsonify({"success": False, "message": "User already exist"})


# enroll a new face into db
def enroll(embedding, face, name):
    print("reached entroll")
    global dbtree
    facename = name
    enroll.counter += 1
    if not os.path.exists("dbimg/%s" % (facename)):
        os.makedirs("dbimg/%s" % (facename))

    cv2.imwrite("dbimg/%s/%d.jpg"%(facename,enroll.counter), face)
    db["names"].append(facename)
    db["embeddings"].append(embedding)
    print("Enrolled %s into db!" % facename)

    dbtree = spatial.KDTree(db["embeddings"])

    with open('face_data.txt', 'w') as att:
        att.write(json.dumps(db))

    return "success"


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



if __name__ == "__main__":
    app.run(host='0.0.0.0' , port=5000)
