#! /bin/env python3

import time
import datetime
from db import DB

from steem.steem import Steem
from steem.blockchain import Blockchain

FULL_VP_RECHARGE_TIME = 432000
ADDED_VALUE_TRAIL = 3130

steemd_nodes = [
  'https://anyx.io',
  'https://api.steemit.com',
#  'https://steemd.minnowsupportproject.org',
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

  return estimate + ADDED_VALUE_TRAIL;

def getCurrentMaxWeight():
  account = steem.get_account(bot)
  shares = float(account['vesting_shares'][:-6]) + float(account['received_vesting_shares'][:-6]) - float(account['vesting_withdraw_rate'][:-6])
  dvpool = shares * 1000000 / 4
  timestamp_fmt = "%Y-%m-%dT%H:%M:%S"
  base_time = datetime.datetime.strptime(account["last_vote_time"], timestamp_fmt)
  since_vote = (datetime.datetime.utcnow() - base_time).total_seconds()
  vp_per_second = 1 / (432000 / dvpool)
  current_power = since_vote * vp_per_second + int(account['downvote_manabar']['current_mana'])
  percent = current_power * 100 / dvpool
  if percent > 95:
    return 5
  elif percent > 60:
    return 2.5
  elif percent > 28:
    return 2
  elif percent > 16:
    return 1.5
  else:
    return 1.25

def getDownvotes():
  pending = db.select('downvotes',['id','slug','user','account','maxi'],{'status': 'wait'},'slug','9999')
  downvotes = {}
  if len(pending) > 0:
    total_shares = 0
    for post in pending:
      delegations = steem.get_vesting_delegations(post['account'],bot,1)
      if len(delegations) == 0 or delegations[0]['delegatee'] != bot:
        db.update('downvotes',{'status': 'undelegated'},{'id':post['id']})
        continue
      else:
        postdata = steem.get_content(post['user'],post['slug'])
        cashoutts = time.mktime(datetime.datetime.strptime(postdata['cashout_time'], "%Y-%m-%dT%H:%M:%S").timetuple())
        chaints = time.mktime(datetime.datetime.strptime(chain.info()['time'], "%Y-%m-%dT%H:%M:%S").timetuple())
        if cashoutts - chaints < 60*60*12:
          db.update('downvotes',{'status':'skipped due to payout approaching'},{'id':post['id']})
          continue
        account_downvotes = db.select('downvotes',['id'],{'status': 'wait','account':post['account']},'id','3')

        vesting_shares = float(delegations[0]['vesting_shares'][:-6]) / len(account_downvotes)
        total_shares += vesting_shares
        if post['user']+'/'+post['slug'] in downvotes:
          downvotes[post['user']+'/'+post['slug']]['shares'] += vesting_shares
          if post['maxi'] < downvotes[post['user']+'/'+post['slug']]['limit']:
            downvotes[post['user']+'/'+post['slug']]['limit'] = post['maxi']
        else:
          downvotes[post['user']+'/'+post['slug']] = {'shares': vesting_shares, 'limit': post['maxi']}
    max_weight = getCurrentMaxWeight()
    for slug, shares in downvotes.items():
      s = shares['shares']
      pct = s*100/total_shares
      vote_weight = pct*max_weight
      downvotes[slug]['shares'] = round(vote_weight,2)

  return distributeRest(downvotes)

def distributeRest(downvotes):
  notMax = 0
  rest = 0
  distribute_rest = {}

  for slug, weight in downvotes.items():
    if weight['shares'] > 100:
      rest += weight['shares'] - 100
      downvotes[slug]['shares'] = 100
    elif weight['shares'] < 100:
      distribute_rest[slug] = weight
      notMax += 1

  if rest > 0 and notMax > 0:
    for slug, weight in distribute_rest.items():
      downvotes[slug]['shares'] += rest/notMax
    return distributeRest(downvotes)
  else:
    return downvotes

def adjustByValue(downvotes, vote_value, doadjust):
  notMax = 0
  rest   = 0
  total_expected = 0
  total_required = 0
  distribute_rest  = {}
  distribute_total = 0
  for slug, weight in downvotes.items():
    post = slug.split('/')
    post = steem.get_content(post[0],post[1])
    pending = float(post['pending_payout_value'][:-4])
    required = pending - weight['limit']
    if required > 0:
      total_required += required
    else:
      required = 0
    expected = weight['shares'] * vote_value / 10000
    total_expected = total_expected + expected
    if expected > required:
      new_weight = required * 10000 / vote_value
      if new_weight > 100:
        new_weight = 100
      rest += weight['shares'] - new_weight
      downvotes[slug]['shares'] = new_weight
    elif expected < required:
      distribute_rest[slug] = weight
      distribute_total += weight['shares']
      notMax += 1
  adjust = 0
  if rest > 0 and notMax > 0:
    for slug, weight in distribute_rest.items():
      pct = weight['shares']*100/distribute_total
      downvotes[slug]['shares'] += pct*rest/100
      if downvotes[slug]['shares'] > 100:
        if doadjust == 1:
          adjust = 1
        else:
          downvotes[slug]['shares'] = 100

    if adjust == 1:
      downvotes = distributeRest(downvotes)

    return adjustByValue(downvotes,vote_value,0)
  else:
    return downvotes

def sendVote(slug,weight):
  last_vote_time = steem.get_account(bot)["last_vote_time"]
  if weight == 0:
    slug = slug.split('/')
    db.update('downvotes',{'status':'no vote cast'},{'user':slug[0],'slug':slug[1]})
    return True
  try:
    steem.commit.vote('@'+slug,float(weight)*-1,bot)
  except:
    time.sleep(10)
    sendVote(slug,weight)
  else:
    slug = slug.split('/')
    db.update('downvotes',{'status':'downvoted with '+str(weight)+'%'},{'user':slug[0],'slug':slug[1]})
    while last_vote_time == steem.get_account(bot)["last_vote_time"]:
      time.sleep(3)
    return True

def downvote():
  downvotes = adjustByValue(getDownvotes(), getCurrentVoteValue(), 1)
  for slug, weight in downvotes.items():
    w = round(weight['shares'],2)
    print('Downvoting '+slug+' with '+str(w)+'%')
    sendVote(slug,w)


downvote()
