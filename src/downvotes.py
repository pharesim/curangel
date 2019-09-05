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

credfile = open("credentials.txt")
bot = credfile.readline().strip()
key = credfile.readline().strip()

db    = DB('curangel.sqlite3')
steem = Steem(keys=[key],nodes=steemd_nodes)
chain = Blockchain(steem)

def getCurrentVoteValue():
  account = steem.get_account(bot)
  total_vests = float(account['received_vesting_shares'][:-6]) + float(account['vesting_shares'][:-6])
  base_mana = int(total_vests*1000000)
  downvote_mana = base_mana / 4
  base_vp = int(account['downvote_manabar']['current_mana'])*10000/downvote_mana
  timestamp_fmt = "%Y-%m-%dT%H:%M:%S"
  base_time = datetime.datetime.strptime(account["last_vote_time"], timestamp_fmt)
  since_vote = (datetime.datetime.utcnow() - base_time).total_seconds()
  VP_TICK_SECONDS = FULL_VP_RECHARGE_TIME / 10000
  vp_per_second = 1 / VP_TICK_SECONDS
  current_power = int(since_vote * vp_per_second + base_vp)

  reward_fund = steem.get_reward_fund('post')
  median_price = steem.get_current_median_history_price()
  rshares = base_mana * 0.02
  median = float(median_price['base'][:-4]) / float(median_price['quote'][:-6])
  estimate = rshares / float(reward_fund['recent_claims']) * float(reward_fund['reward_balance'][:-6]) * median * current_power / 100

  return estimate;

def getDownvotes():
  pending = db.select('downvotes',['id','slug','user','account'],{'status': 'wait'},'slug','9999')
  downvotes = {}
  if len(pending) > 0:
    total_shares = 0
    for post in pending:
      delegator = 0
      delegations = steem.get_vesting_delegations(post['account'],bot,1)
      if len(delegations) == 0 or delegations[0]['delegatee'] != bot:
        db.update('downvotes',{'status': 'undelegated'},{'id':post['id']})
        continue
      postdata = steem.get_content(post['user'],post['slug'])
      cashoutts = time.mktime(datetime.datetime.strptime(postdata['cashout_time'], "%Y-%m-%dT%H:%M:%S").timetuple())
      chaints = time.mktime(datetime.datetime.strptime(chain.info()['time'], "%Y-%m-%dT%H:%M:%S").timetuple())
      if cashoutts - chaints < 60*60*12:
        db.update('downvotes',{'status':'skipped due to payout approaching'},{'id':post['id']})
        continue
      delegations = steem.get_vesting_delegations(post['account'],bot,1)
      account_downvotes = db.select('downvotes',['id'],{'status': 'wait','account':post['account']},'id','3')
      if len(delegations) > 0 and delegations[0]['delegatee'] == bot:
        vesting_shares = float(delegations[0]['vesting_shares'][:-6]) / len(account_downvotes)
        total_shares += vesting_shares
        if post['user']+'/'+post['slug'] in downvotes:
          downvotes[post['user']+'/'+post['slug']] += vesting_shares
        else:
          downvotes[post['user']+'/'+post['slug']] = vesting_shares
    for slug, shares in downvotes.items():
      pct = shares*100/total_shares
      vote_weight = pct*1.25
      downvotes[slug] = round(vote_weight,2)
    downvotes = distributeRest(downvotes)
  return downvotes

def distributeRest(downvotes):
  notMax = 0
  rest   = 0
  distribute_rest  = {}
  distribute_total = 0
  for slug, weight in downvotes.items():
    if weight >= 100:
      rest += weight - 100
      downvotes[slug] = 100
    else:
      notMax += 1
  if rest > 0 and notMax > 0:
    for slug, weight in downvotes.items():
      if weight < 100:
        distribute_rest[slug] = weight
        distribute_total += weight
    for slug, weight in distribute_rest.items():
      pct = weight*100/distribute_total
      downvotes[slug] += pct*100/rest
    return distributeRest(downvotes)
  else:
    return downvotes

def adjustByValue(downvotes, vote_value):
  notMax = 0
  rest   = 0
  distribute_rest  = {}
  distribute_total = 0
  for slug, weight in downvotes.items():
    post = slug.split('/')
    post = steem.get_content(post[0],post[1])
    pending = float(post['pending_payout_value'][:-4])
    expected = weight * vote_value / 10000
    if expected > pending:
      new_weight = pending * 10000 / vote_value
      downvotes[slug] = new_weight
      rest += weight - new_weight
    else:
      distribute_rest[slug] = weight
      distribute_total += weight
      notMax += 1
  if rest > 0 and notMax > 0:
    for slug, weight in distribute_rest.items():
      pct = weight*100/distribute_total
      downvotes[slug] += pct*rest/100
    return adjustByValue(downvotes,vote_value)
  else:
    return distributeRest(downvotes)

def downvote():
  downvotes = adjustByValue(getDownvotes(), getCurrentVoteValue())
  for slug, weight in downvotes.items():
    weight = round(weight,2)
    print('Downvoting '+slug+' with '+str(weight)+'%')
    last_vote_time = steem.get_account(bot)["last_vote_time"]
    try:
      steem.commit.vote('@'+slug,float(weight)*-1,bot)
    except:
      pass
    else:
      slug = slug.split('/')
      db.update('downvotes',{'status':'downvoted with '+str(weight)+'%'},{'user':slug[0],'slug':slug[1]})
      while last_vote_time == steem.get_account(bot)["last_vote_time"]:
        time.sleep(1)


downvote()
