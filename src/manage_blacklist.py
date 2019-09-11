#! /bin/env python3
from db import DB

from steem.steem import Steem
from steem.blockchain import Blockchain

FULL_VP_RECHARGE_TIME = 432000

steemd_nodes = [
  'https://anyx.io',
  'https://api.steemit.com',
  'https://steemd.minnowsupportproject.org',
]

spifile = open("spi.txt")
spiusers = []
user = spifile.readline().strip()
while user != '':
  spiusers.append(user)

for user in spiusers:
  exists = db.select('blacklist',['user'],{'user':user},'user',1)
  if len(exists) > 0:
    db.insert('blacklist',{'user':user,'reason':'holder of spi'})
    print(user+' inserted for holding spi')
  else:
    print(user+' already on list')
  user = spifile.readline().strip()

removeOld = db.select('blacklist',['user'],{'reason': 'holder of spi'},'user',9999)
for user in removeOld:
  if user['user'] not in spiusers:
    db.delete('blacklist',{'user':user['user']})
    print('removed '+user+' because not holding spi any more')
