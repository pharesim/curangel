#! /bin/env python3

import time
import datetime
import json

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
  return db.select('upvotes',['account','user','link','slug','status','title','type'],{'status LIKE':'voted%','vote_time >':"datetime('now','-1 day')"},'account','9999')

def compilation():
  content = 'Welcome to the daily compilation post of the Curangel project!'+"\n"
  content += 'Here we highlight the posts picked by our curators, and give you a resource to discover content worth your time, and maybe even your vote!'+"\n\n"

  last_account = ''
  posts = getVotedPosts()
  for post in posts:
    metadata = json.loads(steem.get_content(post['user'],post['slug'])['json_metadata'])
    if post['account'] != last_account:
      last_account = post['account']
      content += "\n\n"+'*Curator @'+post['account']+"*\n"
      content += '| Thumb | User | Post | Vote weight |'+"\n"
      content += '| --- | --- | --- | ---: |'+"\n"
    if post['title'] == '' and post['type'] == 2:
      post['title'] = 'Comment'
      vote = post['status'].split('/')[-1]
    content += '| <a href="'+post['link']+'"><img src="'+metadata['image'][0]+'" height="100px"/></a> | '
    content +post['user']+' | <a href="'+post['link']+'">'+post['title']+'</a> | '+vote+' |'+"\n"

  print(content)
compilation()

'json_metadata': "image":["https://res.cloudinary.com/dmuksl47x/image/upload/v1566997389/DSC_0017_tkoo0t.jpg","
