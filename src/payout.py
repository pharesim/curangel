#! /bin/env python3

import yaml
import json
import math
import sys
from uuid import uuid4
from datetime import datetime
from time import sleep
from argparse import ArgumentParser

from beemapi.exceptions import MissingRequiredActiveAuthority, UnhandledRPCError

from db import DB

import _cgi_path # noqa: F401
from lib.config import config, load_credentials

from lib.notify_hook import notify

from beem.hive import Hive
from beem.account import Account
from loguru import logger
from munch import Munch

from payment_builder import PaymentBuilder

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
    self.hive = Hive(keys=self.keys, node=self.nodes)
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
        try:
          return to_call()
        except TypeError as e:
          if "string indices" in e.args[0]:
            raise BadNodeError("bad error message from node")
          raise
      except BadNodeError:
        logger.warning(f"Node problem detected (primary node is {self.nodes[0]}).")
        self.next()
        if starting_primary == self.nodes[0]:
          passes += 1
        if passes > 1:
          logger.error(f"Cycling is not fixing node problem!")
          raise

def get_bot_acc():
  return Account(bot, full=False, lazy=True, blockchain_instance=cycler.hive)

def get_bot_hive_balance():
  balance = get_bot_acc().get_balance('available', 'HIVE')
  return balance.amount

def find_bot_tx(txid, start_block):
  bot = get_bot_acc()
  limit = 50
  for op in bot.get_account_history(-1, limit):
    if op["block"] < start_block:
      return False
    if op["trx_id"].lower() == txid.lower():
      return True
  raise RuntimeError("exhausted history range")

def wait_bot_tx(txid):
  logger.info(f"waiting for tx: {txid}")
  bot = get_bot_acc()
  start_block = bot.blockchain.get_dynamic_global_properties()["head_block_number"]
  while not find_bot_tx(txid, start_block):
    sleep(3)

def unwrap_nai(nai_dict, expect_unit=None):
  value = float(nai_dict['amount'])
  value /= 10 ** int(nai_dict['precision'])
  unit = {
    "@@000000037": "VESTS",
    "@@000000021": "HIVE",
    "@@000000013": "HBD"
  }[nai_dict['nai']]
  if expect_unit is not None and expect_unit != unit:
    raise ValueError(f"unexpected unit {unit} (wanted {expect_unit})")
  return value, unit

def getRewards(dry=False):
  rewards = {}
  last_block = db.select('last_check',['rewards_block'],'1=1','rewards_block',1)[0]['rewards_block']
  hive_per_mvests = cycler.hive.get_hive_per_mvest()

  last_block_seen = False
  num_ops = 0
  new_last_block = None
  updated_upvotes = []
  delegation_ops = []

  logger.info("database is at height {}", last_block)

  for r in get_bot_acc().history_reverse(batch_size=100):
    if r['type'] not in ['curation_reward', 'delegate_vesting_shares']:
      # disturbingly, api.hive.blog seems to silently skip curation rewards
      # unless we do the filtering ourselves... better safe than sorry
      continue
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
        vesting_shares, _ = unwrap_nai(r['vesting_shares'])
        op = (r['timestamp'], r['delegator'], vesting_shares)
        delegation_ops.append(op)
        logger.info("{} delegates {} at {} in block {}",
                    op[1], op[2], op[0], r['block'])
    else:
      vests, _ = unwrap_nai(r['reward'], "VESTS")
      hp = round((vests / 1000000 * hive_per_mvests),3)

      # apparently the 'curation_reward' vop is changing...
      # https://gitlab.syncad.com/hive/hive/-/merge_requests/1170
      author = r['author'] if 'author' in r else r['comment_author']
      permlink = r['permlink'] if 'permlink' in r else r['comment_permlink']

      vote = db.select('upvotes',['id','account'],{'user':author,'slug':permlink,'status LIKE':'voted%'},'vote_time',1)
      if len(vote) > 0:
        if 'delegators' in rewards:
          rewards['delegators'] = rewards['delegators'] + (hp*0.8)
        else:
          rewards['delegators'] = hp*0.8
        if vote[0]['account'] in rewards:
          rewards[vote[0]['account']] = rewards[vote[0]['account']] + (hp*0.2)
        else:
          rewards[vote[0]['account']] = (hp*0.2)
        path = f"@{author}/{permlink}"
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

def get_vesting_delegation(account):
  account_obj = Account(account, lazy=True)
  delegations = account_obj.get_vesting_delegations(bot, 1)
  if len(delegations):
    delegation = delegations.pop()
    if delegation['delegatee'] == bot:
      return delegation
  return None

def getDelegators():
  delegators = {}
  logger.info("fetching delegations...")
  bot_acc = Account(bot, blockchain_instance=cycler.hive)
  own_vests = get_bot_acc().get_balance('available', 'VESTS')
  total_delegations = float(own_vests.amount)
  delegations = db.select('delegators',['account','created'],"1=1",'account',9999)
  for delegator in delegations:
    created = datetime.strptime(delegator['created'], "%Y-%m-%dT%H:%M:%S")
    now = datetime.utcnow()
    duration = now - created
    if duration.days >= 1:
      logger.info(f"fetching delegation from {delegator['account']}...")
      delegation = get_vesting_delegation(delegator['account'])
      if delegation is not None:
        vesting_shares, _ = unwrap_nai(delegation['vesting_shares'], "VESTS")
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
    db.insert('rewards',{'account':account,'sp':amount}, throw=True)
  else:
    db.update('rewards',{'sp':existing[0]['sp']+amount},{'account':account}, throw=True)

def assignRewards(delegators):
  # This lock prevents rewards from being reassigned in an edge case
  # where final reward assignment failed
  #
  acquire_RAL()
  for id, group, sp in db.select('partially_calculated_rewards',
                             ['id', 'group_', 'sp'], '1=1', 'group_', None):
    if group != 'delegators':
      addReward(group,sp)
    else:
      for account, pct in delegators.items():
        part = sp * pct
        addReward(account,part)
    db.delete('partially_calculated_rewards', {'id': id}, throw=True)
  if len(db.select('partially_calculated_rewards',
                   ['group_', 'sp'], '1=1', 'group_', None)) > 0:
    raise RuntimeError("unassigned partially calculated rewards")
  release_RAL()

def safe_transfer(to, value, unit, memo, expect_balance):
  try:
    balance = get_bot_hive_balance()
    if balance != expect_balance:
      raise RuntimeError("Aborting transfer: balance mismatch")
    get_bot_acc().transfer(to, value, unit, memo, skip_account_check=True)
  except MissingRequiredActiveAuthority:
    # What the hell? Some node(s) think(s) our signatures are bad (they're not)
    raise BadNodeError("broadcast on this node might be broken")


def do_payment(context, balance, reward, recipient):
  if amount >= 0.001 and balance >= amount:
    try:
      msg = 'Thank you for being a part of @curangel!'
      cycler.tryUntilSuccess(
        lambda: safe_transfer(reward['account'], amount, 'HIVE', msg, balance)
      )
      print(
        'Sending transfer of ' + str(amount) + ' HIVE to ' + reward['account'])
    except:
      logger.exception(
        f"missed payment of {amount} to {recipient}: transaction error")
      notify(
        "payout-error",
        "Curangel payout skipped",
        "transaction error (check server logs)"
      )
    else:
      tx_verified = None
      while not tx_verified:
        old_balance = balance
        try:
          if tx_verified is not None:
            print('Waiting for transfer...')
            sleep(3)

          new_balance = cycler.tryUntilSuccess(lambda: get_bot_hive_balance())
          tx_verified = new_balance < old_balance
        except:
          logger.exception(f"API failure while verifying balance!")
          notify(
            "payout-error",
            "Curangel payout failure",
            "API failure while verifying balance",
            priority="urgent"
          )
          sleep(3)
      context.last_good_recipient = recipient
  elif balance < amount:
    logger.error(f"missed payment of {amount} to {recipient}: low balance")
    notify(
      "payout-error",
      "Curangel low balance",
      "check server logs for details",
      priority="urgent"
    )
  elif amount < 0.001:
    logger.info(
      f"skipped payment of {amount} to {recipient}: below precision threshold")

def assert_aggregation_empty():
  pending = db.select('payout_aggregation', ['account', 'amount'], "1=1", 'account', 9999)
  if len(pending) > 0:
    raise RuntimeError("pending payout aggregation detected")

def flush_aggregation():
  db.delete_all('payout_aggregation')

def payout(context):
  pb = PaymentBuilder(get_bot_acc())
  memo = "Thank you for being a part of @curangel!"
  lgr = context.last_good_recipient

  rewards = db.select('rewards',['account','sp'],'1=1','account',9999)
  for reward in rewards:
    recipient = reward["account"]
    amount = math.floor(reward['sp']*1000)/1000
    if context.last_good_recipient is not None:
      if recipient <= context.last_good_recipient:
        logger.info(f"skipping payment to {recipient} (LGR: {context.last_good_recipient})")
        continue
    if context.user is not None:
      if recipient != context.user:
        logger.info(f"skipping payment to {recipient} (not forced user {context.user})")
        continue
    if amount < 0.001:
      logger.info(f"skipped payment of {amount} to {recipient}: below precision threshold")
      continue
    print('Adding: '+str(amount)+' for '+recipient)
    pb.add_payment(recipient, amount, memo)
    # do_payment(context, balance, reward, recipient)

  while pb.has_pending():
    assert_aggregation_empty()
    txb, tx, paying = pb.build_tx()
    total = 0
    for account, amount in paying:
      total += amount
      db.insert('payout_aggregation', {'account': account, 'amount': amount})
      acc_bal = db.select('rewards',['sp'], {'account': account},'account',9999)[0]['sp']
      db.update('rewards', {'sp': acc_bal - amount}, {'account': account})
      db.insert('reward_payouts',{'account': account, 'amount': amount})

    # ready to send
    balance = get_bot_hive_balance()
    print(yaml.safe_dump(json.loads(str(tx))))
    print('Current balance: '+str(balance))
    print(f'Total to send: {total} HIVE')
    print("waiting 10 seconds...")
    sleep(10)
    try:
      txb.broadcast()
    except UnhandledRPCError as e:
      if "Duplicate transaction check failed" in " ".join(e.args):
        logger.warning("got duplicate transaction error; check API node responses")
    wait_bot_tx(tx.id)
    flush_aggregation()

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
      notify(
        "payout-error",
        "Curangel payout exception",
        "check server logs for details",
        priority="urgent"
      )
      raise

def claimRewards():
  get_bot_acc().claim_reward_balance()

def acquire_RAL():
  db.insert("reward_assignment_lock", {'id': 0}, throw=True)

def release_RAL():
  db.delete("reward_assignment_lock", {'id': 0}, throw=True)

def savePartialRewards(results):
  acquire_RAL()
  for target, amount in results.items():
    db.insert("partially_calculated_rewards", {"id": str(uuid4()), "group_": target, "sp": amount}, throw=True)
  release_RAL()

if __name__ == "__main__":
  args = _ap.parse_args()
  cycler = NodeCycler(bot, [key], config.nodes)
  try:
    results = cycler.tryUntilSuccess(lambda: getRewards(dry=args.test_scan))
    for target, amount in results.items():
      print(f"{target} will be assigned {amount} HIVE")
    if not args.test_scan:
      savePartialRewards(results)
      delegators = cycler.tryUntilSuccess(getDelegators)
      assignRewards(delegators)
      payout_until_complete(args.last_good_recipient, args.user)
      claimRewards()
    notify(
      "payout-success",
      "Curangel payout successful"
    )
  except Exception:
    logger.exception("uncaught exception during payout")
    notify(
      "payout-error",
      "Curangel payout exception",
      "check server logs for details",
      priority="urgent"
    )
    sys.exit(1)
