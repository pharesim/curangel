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
from munch import Munch

_ap = ArgumentParser()
_ap.add_argument("--test-scan", action="store_true",
                 help="test history scanning function only")
_ap.add_argument("--last-good-recipient", type=str, default=None,
                 help="resume failed payout after specified user")
_ap.add_argument("--user", type=str, default=None,
                 help="force instant payout to specified user only")


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
  updated_upvotes = []
  delegation_ops = []

  logger.info("database is at height {}", last_block)

  for r in cycler.account.history_reverse(['curation_reward', 'delegate_vesting_shares'], batch_size=100):
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
        op = (r['timestamp'], r['delegator'], float(r['vesting_shares'][:-6]))
        delegation_ops.append(op)
        logger.info("{} delegates {} at {} in block {}",
                    op[1], op[2], op[0], r['block'])
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
        logger.info(f"{vests} VESTS for {path}")
        updated_upvotes.append(({'reward_sp':str(hp)}, {'id':vote[0]['id']}))

  mod_counts = Munch(created=0, updated=0, removed=0)

  def create_delegation(delegator_, timestamp_):
    if not dry:
      db.insert('delegators', {'account': delegator_, 'created': timestamp_})
    logger.info("create delegation for {} at {}", delegator_, timestamp_)
    mod_counts.created += 1

  def update_delegation(delegator_, timestamp_):
    if not dry:
      # Actually updating the created time would cause delegators to be missed
      # for a day. Since we don't want to happen, we'll leave this happy little
      # accident intact.
      #
      # db.update('delegators', {'created': timestamp_}, {'account': delegator_})
      pass
    logger.info("update delegation for {} at {}", delegator_, timestamp_)
    mod_counts.updated += 1

  def remove_delegation(delegator_):
    if not dry:
      db.delete('delegators', {'account': delegator_})
    logger.info("remove delegation for {}", delegator_)
    mod_counts.removed += 1

  if not last_block_seen:
    # it's unsafe to update the database as there may be unprocessed ops
    raise BadNodeError(f"History scan failed to reach last scanned block after {num_ops} ops.")

  # sort received delegation by timestamp (since we scanned backwards)
  delegation_ops.sort(key=lambda x: x[0])

  # apply updates in chronological order
  dele_updates = {}
  for timestamp, delegator, vests in delegation_ops:
    dele_updates[delegator] = (vests, timestamp)

  # check updated amounts against database state and update accordingly
  for delegator, (vests, timestamp) in dele_updates.items():
    dele_records = db.select('delegators',['account','created'],{'account':delegator},'account',1)
    dele_record = dele_records[0] if len(dele_records) > 0 else None
    if dele_record is None:
      if vests > 0:
        create_delegation(delegator, timestamp)
      else:
        logger.info("skip creating empty delegation for {}", delegator)
    else:
      created = datetime.strptime(dele_record['created'], "%Y-%m-%dT%H:%M:%S")
      new = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
      assert new > created
      if vests > 0:
        update_delegation(delegator, timestamp)
      else:
        remove_delegation(delegator)

  if not dry:
    db.update('last_check',{'rewards_block':new_last_block},{'rewards_block':last_block})

  print("Finished scanning {} ops since block {} (latest block: {})".format(
    num_ops,
    last_block,
    new_last_block
  ))
  print("Found {} new, {} updated, and {} removed delegations.".format(
    mod_counts.created,
    mod_counts.updated,
    mod_counts.removed
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

def payout(context):
  rewards = db.select('rewards',['account','sp'],'1=1','account',9999)
  for reward in rewards:
    recipient = reward["account"]
    if context.last_good_recipient is not None:
      if recipient <= context.last_good_recipient:
        logger.info(f"skipping payment to {recipient} (LGR: {context.last_good_recipient})")
        continue
    if context.user is not None:
      if recipient != context.user:
        logger.info(f"skipping payment to {recipient} (not forced user {context.user})")
        continue
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
        tx_verified = None
        while not tx_verified:
          old_balance = balance
          try:
            if tx_verified is not None:
              print('Waiting for transfer...')
              sleep(3)
            new_balance = cycler.tryUntilSuccess(lambda: float(cycler.hive.get_account(bot)['balance'][:-5]))
            tx_verified = new_balance < old_balance
          except:
            logger.exception(f"API failure while verifying balance!")
            notify("payout-verify-error", dict_of(recipient, amount, old_balance))
            sleep(3)
        db.update('rewards',{'sp':reward['sp']-amount},{'account':reward['account']})
        db.insert('reward_payouts',{'account':reward['account'],'amount':amount})
        context.last_good_recipient = recipient
    elif balance < amount:
      logger.error(f"missed payment of {amount} to {recipient}: low balance")
      notify("payout-low-balance", dict_of(amount, recipient))
    elif amount < 0.001:
      logger.info(f"skipped payment of {amount} to {recipient}: below precision threshold")
  context.done = True

def payout_until_complete(last_good_recipient=None, user=None):
  context = Munch()
  context.done = False
  context.last_good_recipient = last_good_recipient
  context.user = user
  while not context.done:
    try:
      payout(context)
    except Exception:
      logger.exception("payout hiccup")
      logger.error("ctx was: {}", dict(context))

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
      payout_until_complete(args.last_good_recipient, args.user)
      claimRewards()
    notify("payout-success", results)
  except Exception:
    logger.exception("uncaught exception during payout")
    notify("payout-failed", {})
