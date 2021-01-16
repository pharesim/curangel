#! /bin/env python3

import math
from datetime import datetime
from time import sleep
from argparse import ArgumentParser

from db import DB
from config import config

from hive.hive import Hive
from hive.account import Account
from hive.converter import Converter
from hive.blockchain import Blockchain

_ap = ArgumentParser()
_ap.add_argument("--test-scan", action="store_true",
                 help="test history scanning function only")

credfile = open("credentials.txt")
bot = credfile.readline().strip()
postkey = credfile.readline().strip()
key = credfile.readline().strip()

db    = DB('curangel.sqlite3')
client = Hive(keys=[key],nodes=config.nodes)
chain = Blockchain(client)
converter = Converter(client)
account = Account(bot,client)

def getRewards(dry=False):
  rewards = {}
  last_block = db.select('last_check',['rewards_block'],'1=1','rewards_block',1)[0]['rewards_block']
  hive_per_mvests = converter.hive_per_mvests()

  new_last_block = None
  new_delegations = []
  updated_delegations = []
  removed_delegations = []
  updated_upvotes = []

  for r in account.history_reverse(['curation_reward', 'delegate_vesting_shares']):
    if new_last_block is None:
      new_last_block = r['block']
      print(f"Latest block is {new_last_block}")
    if r['block'] <= int(last_block):
      # done fetching
      break
    if 'delegatee' in r:
      if r['delegatee'] == bot:
        if float(r['vesting_shares'][:-6]) > 0:
          delegator = db.select('delegators',['account','created'],{'account':r['delegator']},'account',1)
          if len(delegator) == 0:
            print(f"Processing new delegation from {r['delegator']}.")
            new_delegations.append( {'account': r['delegator'], 'created': r['timestamp']})
          else:
            created = datetime.strptime(delegator[0]['created'], "%Y-%m-%dT%H:%M:%S")
            new     = datetime.strptime(r['timestamp'], "%Y-%m-%dT%H:%M:%S")
            if new < created:
              print(f"Processing updated delegation from {r['delegator']}.")
              updated_delegations.append(({'created':r['timestamp']}, {'account':r['delegator']}))
        else:
          print(f"Processing removed delegation from {r['delegator']}.")
          removed_delegations.append({'account':r['delegator']})
    else:
      vests = float(r['reward'][:-6])
      hp = round((vests / 1000000 * hive_per_mvests),3)
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
        path = f"@{r['comment_author']}/{r['comment_permlink']}"
        print(f"{vests} VESTS for {path}")
        updated_upvotes.append(({'reward_sp':str(hp)}, {'id':vote[0]['id']}))

  if not dry:
    for record in new_delegations:
      db.insert('delegators', record)
    for values, selector in updated_delegations:
      db.update('delegators', values, selector)
    for selector in removed_delegations:
      db.delete('delegators', selector)
    for values, selector in updated_upvotes:
      db.update('upvotes', values, selector)
    db.update('last_check',{'rewards_block':new_last_block},{'rewards_block':last_block})

  print("Finished scanning since block {} (latest block: {})".format(
    last_block,
    new_last_block
  ))
  print("Found {} new, {} updated, and {} removed delegations.".format(
    len(new_delegations),
    len(updated_delegations),
    len(removed_delegations)
  ))
  print(f"Processed {len(updated_upvotes)} curation rewards.")

  return rewards

def getDelegators():
  delegators = {}
  total_delegations = float(client.get_account(bot)['vesting_shares'][:-6])
  delegations = db.select('delegators',['account','created'],"1=1",'account',9999)
  for delegator in delegations:
    created = datetime.strptime(delegator['created'], "%Y-%m-%dT%H:%M:%S")
    now = datetime.utcnow()
    duration = now - created
    if duration.days >= 1:
      delegation = client.get_vesting_delegations(delegator['account'],bot,1)
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
    balance = float(client.get_account(bot)['balance'][:-5])
    print('Current balance: '+str(balance))
    amount = math.floor(reward['sp']*1000)/1000
    print('Next: '+str(amount)+' for '+reward['account'])
    if amount >= 0.001 and balance >= amount:
      try:
        client.transfer(reward['account'], amount, 'HIVE', 'Thank you for being a part of @curangel!', bot)
        print('Sending transfer of '+str(amount)+' HIVE to '+reward['account'])
      except:
        pass
      else:
        while float(client.get_account(bot)['balance'][:-5]) == balance:
          print('Waiting for transfer...')
          sleep(3)
        db.update('rewards',{'sp':reward['sp']-amount},{'account':reward['account']})
        db.insert('reward_payouts',{'account':reward['account'],'amount':amount})


if __name__ == "__main__":
  args = _ap.parse_args()
  if args.test_scan:
    getRewards(dry=True)
  else:
    assignRewards(getRewards(),getDelegators())
    payout()
    client.claim_reward_balance(account=bot)
