import json

# initialize database
db = {"names":[],"embeddings":[]}
dbtree = ""
try:
    db = json.loads(open('att_db.txt').read())
except:
    pass

name = "Arun"

# find position of name in db
index = 0;
for i in db['names']:
	if(i == name):
		break
	index+=1

# remove item from db
db['names'].remove(name);
db['embeddings'].remove(db['embeddings'][index])

with open('att_db.txt','w') as att:
    att.write(json.dumps(db))


print(db)