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
  return db.select('upvotes',['account','user','link','slug','title','type'],{'status LIKE':'voted%','vote_time >':"datetime('now','-1 day')"},'account','9999')

def compilation():
  content = '<center>'+"\n"
  content += '# Welcome to the daily compilation post of the Curangel project (beta test)!'+"\n<br/>\n"
  content += 'https://i.imgur.com/z2fbtrQ.png'+"\n"
  content += 'Here we highlight the posts picked by our curators, and give you a resource to discover content worth your time, and maybe even your vote!'+"\n\n"

  last_account = ''
  posts = getVotedPosts()
  for post in posts:
    metadata = json.loads(steem.get_content(post['user'],post['slug'])['json_metadata'])
    if post['account'] != last_account:
      last_account = post['account']
      content += "\n\n"+'*Curator @'+post['account']+"*\n"
      content += '| Thumb | User | Post |'+"\n"
      content += '| --- | --- | --- |'+"\n"
    if post['title'] == '' and post['type'] == 2:
      post['title'] = 'Comment'
    vote = post['status'].split('/')[-1]
    content += '| <a href="'+post['link']+'"><img src="https://steemitimages.com/128x256/'+metadata['image'][0]+'" height="100px"/></a> | '
    content += post['user']+' | <a href="'+post['link']+'">'+post['title']+'</a> |'+"\n"

  content += 'Thank you for your interest in the Curangel project! If you want to help us supporting a wide range of valuable community members, consider sending us a delegation. '
  content += 'By doing so, you will also receive the possibility to help us move rewards from overrated posts back to the pool as soon as we are out of beta.'
  #content += 'For more info, check out our '
  #content += '<a href="https://steemit.com/curangel/@curangel/officially-introducing-the-curangel-project-help-us-making-steem-a-better-place">introduction post</a>'
  content += '</center>'
  print(content)
compilation()
