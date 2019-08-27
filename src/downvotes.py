#! /bin/env python3

import time
import datetime
from db import DB

from steem.steem import Steem
from steem.blockchain import Blockchain

steemd_nodes = [
  'https://anyx.io',
  'https://api.steemit.com',
  'https://steemd.minnowsupportproject.org',
]

db    = DB('curangel.sqlite3')
steem = Steem(nodes=steemd_nodes)
chain = Blockchain(steem)

def getDownvotes():
  pending = db.select('downvotes',['slug','account'],{'status': 'wait'},'slug','9999')
  downvotes = {}
  if len(pending) > 0:
    for post in pending:
      delegations = steem.get_vesting_delegations(post['account'],'curangel',1)
      if len(delegations) > 0 and delegations[0]['delegatee'] == 'curangel':
        if downvotes[slug]:
          downvotes['slug'] += float(delegations[0]['vesting_shares'][:-6])
        else:
          downvotes['slug'] = float(delegations[0]['vesting_shares'][:-6])
  return downvotes

def downvote():
  downvotes = getDownvotes()
