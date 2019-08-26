#! /bin/env python3

import time
import datetime
import sqlite3
from db import DB

from steem.blockchain import Blockchain

# Maximum VP allowed.
MAX_VP = 10000

# Time to recharge VP from zero.
FULL_VP_RECHARGE_TIME = 432000

# Time to recharge a single point of VP (0.01%).
VP_TICK_SECONDS = FULL_VP_RECHARGE_TIME / MAX_VP

# maximum vote weight allowed
MAX_VOTE_WEIGHT = 10000

# minimum vote weight allowed
MIN_VOTE_WEIGHT = 50;

# FACTOR FOR VOTE WEIGHT BY QUEUE LENGTH
WEIGHT_FACTOR = 1.1;

class Voter:
  def __init__(self, steem, account):
    self.db = DB('curangel.sqlite3')
    self.chain = Blockchain()
    self.steem = steem
    self.account = account

  def _get_account(self):
    return self.steem.get_account(self.account)

  def get_current_vp(self, includeWaste=False):
    account = self._get_account()
    base_vp = account["voting_power"]
    timestamp_fmt = "%Y-%m-%dT%H:%M:%S"
    base_time = datetime.datetime.strptime(account["last_vote_time"], timestamp_fmt)
    since_vote = (datetime.datetime.utcnow() - base_time).total_seconds()
    vp_per_second = 1 / VP_TICK_SECONDS
    current_power = since_vote * vp_per_second + base_vp
    if not includeWaste and current_power > MAX_VP:
      current_power = MAX_VP
    return current_power

  def get_recharge_time(self, allowNegative=False):
    current_power = self.get_current_vp(True)
    remaining_ticks = MAX_VP - current_power
    seconds_to_full = remaining_ticks * VP_TICK_SECONDS
    if not allowNegative and seconds_to_full < 0:
      seconds_to_full = 0
    return datetime.timedelta(seconds=seconds_to_full)

  def next_in_queue(self,steem):
    results = self.db.select('upvotes',['id,link'],{'status':'in queue'},'created ASC','1')
    if len(results) > 0:
      link = results[0]['link'].split('#')
      if len(link) > 1:
        link = link[1].split('/')
      else:
        link = results[0]['link'].split('/')

      post = steem.get_content(link[-2][1:],link[-1])
      cashoutts = time.mktime(datetime.datetime.strptime(post['cashout_time'], "%Y-%m-%dT%H:%M:%S").timetuple())
      chaints = time.mktime(datetime.datetime.strptime(self.chain.info()['time'], "%Y-%m-%dT%H:%M:%S").timetuple())
      if cashoutts - chaints < 60*60*24*5:
        print("\nskipping '{}' because payout is in less than 24 hours...".format(results[0]['link']))
        self.db.update('upvotes',{'status':'skipped voting due to payout approaching'},{'id':results[0]['id']})
        return self.next_in_queue(steem)

      return results[0]['link']
    else:
      return False

  def calculate_vote_weight(self):
    results = self.db.select('upvotes',['link'],{'status':'in queue'},'created ASC','9999')
    weight = MAX_VOTE_WEIGHT
    for _ in range(len(results)-1):
      weight = weight / WEIGHT_FACTOR

    return weight

  def vote(self, uri):
    last_vote_time = self._get_account()["last_vote_time"]
    weight = int(self.calculate_vote_weight())
    print("\nvoting '{}' with weight of {}...".format(uri,weight))
    self.steem.commit.vote(uri, weight, self.account)
    while last_vote_time == self._get_account()["last_vote_time"]:
      # Block until the vote is reflected on the remote node.
      # This prevents double vote attempts.
      time.sleep(1)
    self.db.update('upvotes',{'status':'voted with '+str(weight/100)+'%'},{'link':uri})
