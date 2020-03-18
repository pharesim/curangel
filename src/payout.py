#! /bin/env python3

import math
from datetime import datetime
from time import sleep

from db import DB

from steem.steem import Steem
from steem.account import Account
from steem.converter import Converter
from steem.blockchain import Blockchain

steemd_nodes = [
  'https://anyx.io',
  'https://api.steemit.com',
#  'https://steemd.minnowsupportproject.org',
]

credfile = open("credentials.txt")
bot = credfile.readline().strip()
postkey = credfile.readline().strip()
key = credfile.readline().strip()

db    = DB('curangel.sqlite3')
steem = Steem(keys=[key],nodes=steemd_nodes)
chain = Blockchain(steem)
converter = Converter(steem)
account = Account(bot,steem)

def getRewards():
  rewards = {}
  last_block = db.select('last_check',['rewards_block'],'1=1','rewards_block',1)[0]['rewards_block']
  steem_per_mvests = converter.steem_per_mvests()
  received = account.get_account_history(-1,2500,filter_by=['curation_reward','delegate_vesting_shares'])
  i = 0
  for r in received:
    if i < 1:
      i = i+1
      db.update('last_check',{'rewards_block':r['block']},{'rewards_block':last_block})
    if r['block'] <= int(last_block):
      break

    if 'delegatee' in r:
      if r['delegatee'] == bot:
        if float(r['vesting_shares'][:-6]) > 0:
          delegator = db.select('delegators',['account','created'],{'account':r['delegator']},'account',1)
          if len(delegator) == 0:
            db.insert('delegators',{'account':r['delegator'],'created':r['timestamp']})
          else:
            created = datetime.strptime(delegator[0]['created'], "%Y-%m-%dT%H:%M:%S")
            new     = datetime.strptime(r['timestamp'], "%Y-%m-%dT%H:%M:%S")
            if new < created:
              db.update('delegators',{'created':r['timestamp']},{'account':r['delegator']})
        else:
          db.delete('delegators',{'account':r['delegator']})
    else:
      vests = float(r['reward'][:-6])
      hp = round((vests / 1000000 * steem_per_mvests),3)
      vote = db.select('upvotes',['id','account'],{'user':r['comment_author'],'slug':r['comment_permlink'],'status LIKE':'voted%'},'vote_time',1)
      if len(vote) > 0:
        if 'delegators' in rewards:
          rewards['delegators'] = rewards['delegators'] + (hp*0.8)
        else:
          rewards['delegators'] = hp*0.8
        if vote[0]['account'] in rewards:
          rewards[vote[0]['account']] = rewards[vote[0]['account']] + (hp*0.2)
        else:
          rewards[vote[0]['account']] = (hp*0.2)
        db.update('upvotes',{'reward_sp':str(hp)},{'id':vote[0]['id']})

  return rewards

def getDelegators():
  delegators = {}
  total_delegations = float(steem.get_account(bot)['vesting_shares'][:-6])
  delegations = db.select('delegators',['account','created'],"1=1",'account',9999)
  for delegator in delegations:
    created = datetime.strptime(delegator['created'], "%Y-%m-%dT%H:%M:%S")
    now = datetime.utcnow()
    duration = now - created
    if duration.days >= 1:
      delegation = steem.get_vesting_delegations(delegator['account'],bot,1)
      if len(delegation) > 0 and delegation[0]['delegatee'] == bot:
        vesting_shares = float(delegation[0]['vesting_shares'][:-6])
        total_delegations = total_delegations + vesting_shares
        delegators[delegator['account']] = vesting_shares
  for account, delegation in delegators.items():
    delegators[account] = delegation / total_delegations

  return delegators

def addReward(account,amount):
  existing = db.select('rewards',['sp'],{'account':account},'account',1)
  if len(existing) == 0:
    db.insert('rewards',{'account':account,'sp':amount})
  else:
    db.update('rewards',{'sp':existing[0]['sp']+amount},{'account':account})

def assignRewards(rewards,delegators):
  for account, amount in rewards.items():
    if account != 'delegators':
      addReward(account,amount)
    else:
      for account, pct in delegators.items():
        part = amount * pct
        addReward(account,part)

def payout():
  rewards = db.select('rewards',['account','sp'],'1=1','account',9999)
  for reward in rewards:
    balance = float(steem.get_account(bot)['balance'][:-6])
    print('Current balance: '+str(balance))
    amount = math.floor(reward['sp']*1000)/1000
    print('Next: '+str(amount)+' for '+reward['account'])
    if amount >= 0.001 and balance >= amount:
      try:
        steem.transfer(reward['account'], amount, 'STEEM', 'Thank you for being a part of @curangel!', bot)
        print('Sending transfer of '+str(amount)+' STEEM to '+reward['account'])
      except:
        pass
      else:
        while float(steem.get_account(bot)['balance'][:-6]) == balance:
          print('Waiting for transfer...')
          sleep(3)
        db.update('rewards',{'sp':reward['sp']-amount},{'account':reward['account']})
        db.insert('reward_payouts',{'account':reward['account'],'amount':amount})

assignRewards(getRewards(),getDelegators())
payout()
steem.claim_reward_balance(account=bot)
