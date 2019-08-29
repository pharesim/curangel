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

def getVotedPosts():
  posts = db.select('upvotes',['account','user','link','status','title','type'],{'status LIKE':'voted%','vote_time >':"datetime('now','-1 day')"},'account','9999')
  print(posts)

getVotedPosts()
