#! /bin/env python3

import time
import datetime
from db import DB

from steem.steem import Steem
from steem.blockchain import Blockchain

FULL_VP_RECHARGE_TIME = 432000

steemd_nodes = [
  'https://anyx.io',
  'https://api.steemit.com',
  'https://steemd.minnowsupportproject.org',
]

db    = DB('curangel.sqlite3')
steem = Steem(nodes=steemd_nodes)
chain = Blockchain(steem)

def getCurrentVP():
  account = steem.get_account('curangel')
  base_mana = int(float(account['received_vesting_shares'][:-6])*1000000)
  downvote_mana = base_mana / 4
  base_vp = int(account['downvote_manabar']['current_mana'])*10000/downvote_mana
  timestamp_fmt = "%Y-%m-%dT%H:%M:%S"
  base_time = datetime.datetime.strptime(account["last_vote_time"], timestamp_fmt)
  since_vote = (datetime.datetime.utcnow() - base_time).total_seconds()
  VP_TICK_SECONDS = FULL_VP_RECHARGE_TIME / 10000
  vp_per_second = 1 / VP_TICK_SECONDS
  current_power = int(since_vote * vp_per_second + base_vp)

def getDownvotes():
  pending = db.select('downvotes',['id','slug','user','account'],{'status': 'wait'},'slug','9999')
  downvotes = {}
  if len(pending) > 0:
    total_shares = 0
    for post in pending:
      postdata = steem.get_content(post['user'],post['slug'])
      cashoutts = time.mktime(datetime.datetime.strptime(postdata['cashout_time'], "%Y-%m-%dT%H:%M:%S").timetuple())
      chaints = time.mktime(datetime.datetime.strptime(chain.info()['time'], "%Y-%m-%dT%H:%M:%S").timetuple())
      if cashoutts - chaints < 60*60*24:
        db.update('downvotes',{'status':'skipped due to payout approaching'},{'id':post['id']})
        continue
      delegations = steem.get_vesting_delegations(post['account'],'curangel',1)
      if len(delegations) > 0 and delegations[0]['delegatee'] == 'curangel':
        vesting_shares = float(delegations[0]['vesting_shares'][:-6])
        total_shares += vesting_shares
        if post['slug'] in downvotes:
          downvotes[post['slug']] += vesting_shares
        else:
          downvotes[post['slug']] = vesting_shares
    for slug, shares in downvotes.items():
      pct = shares*100/total_shares
      vote_weight = pct*1.25
      downvotes[slug] = int(vote_weight*100)/100
    downvotes = distributeRest(downvotes)
  return downvotes

def distributeRest(downvotes):
  notMax = 0
  rest   = 0
  for slug, weight in downvotes.items():
    if weight >= 100:
      rest += weight - 100
      downvotes[slug] = 100
    else:
      notMax += 1
  distribute_rest = {}
  if rest > 0 and notMax > 0:
    for slug, weight in downvotes.items():
      if weight < 100:
        distribute_rest[slug] = weight
    for slug, pct in distribute_rest.items():
      downvotes[slug] += pct*100/rest
    return distributeRest(downvotes)
  else:
    return downvotes

def downvote():
  current_power = getCurrentVP()
  downvotes = getDownvotes()
  print(downvotes)


downvote()
