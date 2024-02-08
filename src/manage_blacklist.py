#! /bin/env python3
from db import DB
import uuid
import requests

db = DB('curangel.sqlite3')

def get_holders(url):
  richlist = requests.get(url=url).json()["richlist"]
  return {u["account"] for u in richlist if float(u["balance"]) > 0}

def pardon_spi():
  # get all blacklisted users with reason "holder of spi"
  rows = db.select('blacklist', ['user', 'reason'], {'reason': 'holder of spi'}, 9999)
  for row in rows:
    user = row['user']
    db.delete('blacklist', {'user': user})
    print(f"pardoned user {user} for holding SPI")

def manageSPIholders():
  # spi steem-engine token, list available at https://steem-engine.rocks/tokens/SPI/richlist
  sespiusers = get_holders("https://steem-engine.rocks/tokens/SPI/richlist")
  print(f"Number of SE:SPI holders: {len(sespiusers)}")

  # spi hive-engine token, list available at https://hive-engine.rocks/tokens/SPI/richlist
  hespiusers = get_holders("https://hive-engine.rocks/tokens/SPI/richlist")
  print(f"Number of HE:SPI holders: {len(hespiusers)}")

  # take the intersection of the two sets for now
  spiusers = sespiusers & hespiusers
  print(f"Number of users holding SPI on both chains: {len(hespiusers)}")

  blacklisted_by_reason = {}
  for user in spiusers:
    exists = db.select('blacklist',['user', 'reason'],{'user':user},'user',1)
    if len(exists) < 1:
      db.insert('blacklist',{'id':uuid.uuid4().hex,'user':user,'reason':'holder of spi','account':'curangel'})
      print(user+' inserted for holding spi')
    for row in exists:
      try:
        blacklisted_by_reason[row["reason"]].add(row["user"])
      except KeyError:
        blacklisted_by_reason[row["reason"]] = {row["user"]}

  for reason, users in blacklisted_by_reason.items():
    print(f"{len(users)} already blacklisted with reason \"{reason}\"")

  removeOld = db.select('blacklist',['user'],{'reason': 'holder of spi'},'user',9999)
  print('Checking '+str(len(removeOld))+' entries for changes')
  for user in removeOld:
    if user['user'] not in spiusers:
      db.delete('blacklist',{'user':user['user']})
      print('removed '+user['user']+' because not holding spi any more')

if __name__ == "__main__":
  # manageSPIholders()
  pardon_spi()

