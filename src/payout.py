#! /bin/env python3

import math
from datetime import datetime
from time import sleep
from argparse import ArgumentParser

from db import DB

import _cgi_path # noqa: F401
from lib.config import config, load_credentials

from lib.notify_hook import notify

from hive.hive import Hive
from hive.account import Account
from hive.converter import Converter
from hive.blockchain import Blockchain
from loguru import logger
from sorcery import dict_of

_ap = ArgumentParser()
_ap.add_argument("--test-scan", action="store_true",
                 help="test history scanning function only")


credentials = load_credentials()
bot = credentials.username
postkey = credentials.posting
key = credentials.active

db    = DB('curangel.sqlite3')

class BadNodeError(RuntimeError):
  pass

class NodeCycler:
  def __init__(self, username, keys, nodes):
    self.username = username
    self.nodes = nodes
    self.keys = keys
    self._make_objects()

  def _make_objects(self):
    self.hive = Hive(keys=self.keys, nodes=self.nodes)
    self.chain = Blockchain(self.hive)
    self.converter = Converter(self.hive)
    self.account = Account(self.username, self.hive)
    logger.debug(f"Hive objects reconstructed with \"{self.nodes[0]}\" as primary node.")

  def next(self):
    self.nodes.append(self.nodes.pop(0))
    self._make_objects()
    logger.info(f"Node \"{self.nodes[-1]}\" moved to end of list.")

  def tryUntilSuccess(self, to_call):
    starting_primary = self.nodes[0]
    passes = 0
    while True:
      try:
        return to_call()
      except BadNodeError:
        logger.warning(f"Node problem detected (primary node is {self.nodes[0]}).")
        self.next()
        if starting_primary == self.nodes[0]:
          passes += 1
        if passes > 1:
          logger.error(f"Cycling is not fixing node problem!")
          raise

def getRewards(dry=False):
  rewards = {}
  last_block = db.select('last_check',['rewards_block'],'1=1','rewards_block',1)[0]['rewards_block']
  hive_per_mvests = cycler.converter.hive_per_mvests()

  last_block_seen = False
  num_ops = 0
  new_last_block = None
  new_delegations = []
  updated_delegations = []
  removed_delegations = []
  updated_upvotes = []

  for r in cycler.account.history_reverse(['curation_reward', 'delegate_vesting_shares']):
    if new_last_block is None:
      new_last_block = r['block']
      print(f"Latest block is {new_last_block}")
    if r['block'] <= int(last_block):
      # done fetching; it is now safe to update the database
      print(f"Found op in known processed block (#{r['block']})")
      last_block_seen = True
      break
    num_ops += 1
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

  if not last_block_seen:
    # it's unsafe to update the database as there may be unprocessed ops
    raise BadNodeError(f"History scan failed to reach last scanned block after {num_ops} ops.")
  elif not dry:
    for record in new_delegations:
      db.insert('delegators', record)
    for values, selector in updated_delegations:
      db.update('delegators', values, selector)
    for selector in removed_delegations:
      db.delete('delegators', selector)
    for values, selector in updated_upvotes:
      db.update('upvotes', values, selector)
    db.update('last_check',{'rewards_block':new_last_block},{'rewards_block':last_block})


  print("Finished scanning {} ops since block {} (latest block: {})".format(
    num_ops,
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
  logger.info("fetching delegations...")
  total_delegations = float(cycler.hive.get_account(bot)['vesting_shares'][:-6])
  delegations = db.select('delegators',['account','created'],"1=1",'account',9999)
  for delegator in delegations:
    created = datetime.strptime(delegator['created'], "%Y-%m-%dT%H:%M:%S")
    now = datetime.utcnow()
    duration = now - created
    if duration.days >= 1:
      logger.info(f"fetching delegation from {delegator['account']}...")
      delegation = cycler.hive.get_vesting_delegations(delegator['account'],bot,1)
      if len(delegation) > 0 and delegation[0]['delegatee'] == bot:
        vesting_shares = float(delegation[0]['vesting_shares'][:-6])
        total_delegations = total_delegations + vesting_shares
        delegators[delegator['account']] = vesting_shares
    else:
      logger.info(f"skipping delegation from {delegator['account']} (too young)")
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
    recipient = reward["account"]
    balance = float(cycler.hive.get_account(bot)['balance'][:-5])
    print('Current balance: '+str(balance))
    amount = math.floor(reward['sp']*1000)/1000
    print('Next: '+str(amount)+' for '+reward['account'])
    if amount >= 0.001 and balance >= amount:
      try:
        cycler.hive.transfer(reward['account'], amount, 'HIVE', 'Thank you for being a part of @curangel!', bot)
        print('Sending transfer of '+str(amount)+' HIVE to '+reward['account'])
      except:
        logger.warning(f"missed payment of {amount} to {recipient}: transaction error")
        notify("payout-tx-error", dict_of(amount, recipient))
      else:
        while float(cycler.hive.get_account(bot)['balance'][:-5]) == balance:
          print('Waiting for transfer...')
          sleep(3)
        db.update('rewards',{'sp':reward['sp']-amount},{'account':reward['account']})
        db.insert('reward_payouts',{'account':reward['account'],'amount':amount})
    elif balance < amount:
      logger.error(f"missed payment of {amount} to {recipient}: low balance")
      notify("payout-low-balance", dict_of(amount, recipient))
    elif amount < 0.001:
      logger.info(f"skipped payment of {amount} to {recipient}: below precision threshold")


def claimRewards():
  cycler.hive.claim_reward_balance(account=bot)

if __name__ == "__main__":
  args = _ap.parse_args()
  cycler = NodeCycler(bot, [key], config.nodes)
  try:
    results = cycler.tryUntilSuccess(lambda: getRewards(dry=args.test_scan))
    for target, amount in results.items():
      print(f"{target} will be assigned {amount} HIVE")
    if not args.test_scan:
      delegators = cycler.tryUntilSuccess(getDelegators)
      assignRewards(results,delegators)
      payout()
      claimRewards()
    notify("payout-success", results)
  except Exception:
    logger.exception("uncaught exception during payout")
    notify("payout-failed", {})
