#! /bin/env python3
from db import DB
import uuid

db = DB('curangel.sqlite3')

# spi steem-engine token, list available at
spifile = open("spi.txt")
spiusers = []
user = spifile.readline().strip()
while user != '-endoflist-':
  spiusers.append(user)
  user = spifile.readline().strip()

print('Number of SPI holders: '+str(len(spiusers)))

for user in spiusers:
  exists = db.select('blacklist',['user'],{'user':user},'user',1)
  if len(exists) < 1:
    db.insert('blacklist',{'id':uuid.uuid4().hex,'user':user,'reason':'holder of spi','account':'pharesim'})
    print(user+' inserted for holding spi')
  user = spifile.readline().strip()

removeOld = db.select('blacklist',['user'],{'reason': 'holder of spi'},'user',9999)
for user in removeOld:
  if user['user'] not in spiusers:
    db.delete('blacklist',{'user':user['user']})
    print('removed '+user+' because not holding spi any more')
