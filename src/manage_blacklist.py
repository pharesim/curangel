#! /bin/env python3
from hive.hive import Hive
from hive.account import Account

from db import DB
import uuid
import requests

from pprint import pprint
import sys

db = DB('curangel.sqlite3')

def manageSPIholders():
  # spi steem-engine token, list available at https://steem-engine.rocks/tokens/SPI/richlist
  URL = "https://steem-engine.rocks/tokens/SPI/richlist"
  richlist = requests.get(url = URL).json()['richlist']
  spiusers = []
  for holder in richlist:
    if float(holder['balance']) > 0:
      spiusers.append(holder['account'])

  print('Number of SPI holders: '+str(len(spiusers)))

  for user in spiusers:
    exists = db.select('blacklist',['user'],{'user':user},'user',1)
    if len(exists) < 1:
      db.insert('blacklist',{'id':uuid.uuid4().hex,'user':user,'reason':'holder of spi','account':'pharesim'})
      print(user+' inserted for holding spi')

  removeOld = db.select('blacklist',['user'],{'reason': 'holder of spi'},'user',9999)
  print('Checking '+str(len(removeOld))+' entries for changes')
  for user in removeOld:
    if user['user'] not in spiusers:
      db.delete('blacklist',{'user':user['user']})
      print('removed '+user['user']+' because not holding spi any more')

steemcryptosicko = db.select('blacklist',['user'],{'reason': 'part of steemcryptosicko circle'},'user',9999)
xiguang = db.select('blacklist',['user'],{'reason': 'delegates to xiguang'},'user',9999)

manageSPIholders()
