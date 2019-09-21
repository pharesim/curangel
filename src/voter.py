#! /bin/env python3

# TODO: this can probably be cleaned up
import sys
import os
sys.path.append(
  os.path.join(
    os.path.split(__file__)[0],
    "../html/api/lib"))

from db_util import QueueDBHelper, NoVoteStrengthError

import time
import datetime
from db import DB

from steem.steem import Steem
from steem.blockchain import Blockchain
from steem.account import Account

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
WEIGHT_FACTOR = 1.15;

steemd_nodes = [
  'https://anyx.io',
  'https://api.steemit.com',
  'https://steemd.minnowsupportproject.org',
]

class Voter:
  def __init__(self, steem, account):
    self.db = DB('curangel.sqlite3')
    steem = Steem(nodes=steemd_nodes)
    self.chain = Blockchain(steem)
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

      uri = link[-2][1:]+'/'+link[-1]
      post = steem.get_content(link[-2][1:],link[-1])

      # check payout time
      cashoutts = time.mktime(datetime.datetime.strptime(post['cashout_time'], "%Y-%m-%dT%H:%M:%S").timetuple())
      chaints = time.mktime(datetime.datetime.strptime(self.chain.info()['time'], "%Y-%m-%dT%H:%M:%S").timetuple())
      if cashoutts - chaints < 60*60*12:
        print("\nskipping '{}' because payout is in less than 12 hours...".format(results[0]['link']))
        self.db.update('upvotes',{'status':'skipped voting due to payout approaching'},{'id':results[0]['id']})
        return self.next_in_queue(steem)

      # check if author used bitbots
      bidbots = ['alfanso','appreciator','bdvoter','bid4joy','boomerang','booster','brandonfrye','buildawhale','edensgarden','inciter','joeparys','leo.voter','luckyvotes','minnowbooster','minnowhelper','minnowvotes','ocdb','onlyprofitbot','postpromoter','profitvote','promobot','qustodian','redlambo','rocky1','sct.voter','smartmarket','smartsteem','sneaky-ninja','sportsvoter','spydo','steemyoda','thebot','therising','tipu','treeplanter','triplea.bot','upmewhale','upmyvote','whalepromobot']
      postaccount = Account(post['author'],steem)
      history = postaccount.get_account_history(-1,2500,filter_by='transfer')
      for h in history:
        if h['to'] in bidbots:
          print("\nskipping '{}' because author bought vote...".format(results[0]['link']))
          self.db.update('upvotes',{'status':'skipped voting due to vote buying'},{'id':results[0]['id']})
          return self.next_in_queue(steem)
        last = h['timestamp']
        txts = time.mktime(datetime.datetime.strptime(h['timestamp'], "%Y-%m-%dT%H:%M:%S").timetuple())
        chaints = time.mktime(datetime.datetime.strptime(self.chain.info()['time'], "%Y-%m-%dT%H:%M:%S").timetuple())
        if chaints - txts > 60*60*24*7:
          break

      return uri, results[0]['id'];
    else:
      return False, False;

  def calculate_vote_weight(self):
    results = self.db.select('upvotes',['id'],{'status':'in queue'},'created ASC','9999')
    weight = MAX_VOTE_WEIGHT

    with QueueDBHelper('curangel.sqlite3') as qdbh:
      for result in results:
        try:
          strength = qdbh.query_upvote_strength(result["id"])
        except NoVoteStrengthError:
          strength = 1
        diff = weight - (weight / (WEIGHT_FACTOR))
        weight = weight - diff * strength

    weight *= strength

    if weight < MIN_VOTE_WEIGHT:
      weight = MIN_VOTE_WEIGHT
    weight = int(weight)
    return float(weight/100)

  def sendVote(self,uri,weight,id):
    last_vote_time = self._get_account()["last_vote_time"]
    try:
      self.steem.commit.vote(uri, weight, self.account)
    except:
      time.sleep(3)
      self.sendVote(uri,weight,id)
    else:
      self.db.update('upvotes',{'status':'voted with '+str(weight)+'%','vote_time':datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')},{'id':id})
      while last_vote_time == self._get_account()["last_vote_time"]:
        # Block until the vote is reflected on the remote node.
        # This prevents double vote attempts.
        time.sleep(1)

  def vote(self, uri, id):
    weight = self.calculate_vote_weight()
    print("\nvoting '{}' with weight of {}...".format(uri,weight))
    self.sendVote(uri,weight,id)
