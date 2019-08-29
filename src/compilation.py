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
  return db.select('upvotes',['account','user','link','slug','title','status','type'],{'status LIKE':'voted%','vote_time >':"datetime('now','-1 day')"},'account','9999')

def getPostContent():
  content = '<center>'+"\n"
  content += '# Welcome to the daily compilation post of the Curangel project (beta test)!'+"\n<br />\n"
  content += 'https://i.imgur.com/NI4bwBx.png<br />'+"\n"
  content += 'Here we highlight the posts picked by our curators, and give you a resource to discover content worth your time, and maybe even your vote!'+"\n"
  content += '<img src="https://steemitimages.com/p/2FFvzA2zeqoVJ2SVhDmmumdPfnVEcahMce9nMwwksSDdRvQBSJ15CK7qPMiVRw3fSP6uC94yTyYJg4N59kGHCvx92PC9z477WfXCyNByjLWaj3FvtFQchhjkQVgWi?format=match&mode=fit&width=640" />'+"\n"

  content += getVotesTable(getVotedPosts())

  content += '<img src="https://steemitimages.com/p/2FFvzA2zeqoVJ2SVhDmmumdPfnVEcahMce9nMwwksSDdRvQBSJ15CK7qPMiVRw3fSP6uC94yTyYJg4N59kGHCvx92PC9z477WfXCyNByjLWaj3FvtFQchhjkQVgWi?format=match&mode=fit&width=640" />'+"\n"

  content += 'Thank you for your interest in the Curangel project! If you want to help us supporting a wide range of valuable community members and at the same time receive a share of the generated curation rewards, consider sending us a delegation. '
  content += 'By doing so, you will also receive the possibility to help us move rewards from overrated posts back to the pool as soon as we are out of beta.'+"\n"
  #content += 'For more info, check out our '
  #content += '<a href="https://steemit.com/curangel/@curangel/officially-introducing-the-curangel-project-help-us-making-steem-a-better-place">introduction post</a>'+"\n"

  #content += '<img src="https://steemitimages.com/p/2FFvzA2zeqoVJ2SVhDmmumdPfnVEcahMce9nMwwksSDdRvQBSJ15CK7qPMiVRw3fSP6uC94yTyYJg4N59kGHCvx92PC9z477WfXCyNByjLWaj3FvtFQchhjkQVgWi?format=match&mode=fit&width=640" />'+"\n"
  #content += 'Come and join our discord at -discordlink-!'+"\n"

  content += '<img src="https://steemitimages.com/p/2FFvzA2zeqoVJ2SVhDmmumdPfnVEcahMce9nMwwksSDdRvQBSJ15CK7qPMiVRw3fSP6uC94yTyYJg4N59kGHCvx92PC9z477WfXCyNByjLWaj3FvtFQchhjkQVgWi?format=match&mode=fit&width=640" />'+"\n"

  content += 'The Curangel project is brought to you by witness @pharesim - vote for your witnesses at https://steemit.com/~witnesses'
  content += '</center>'
  return content

def getVotesTable(posts):
  content = ''
  last_account = ''
  n = 0
  for post in posts:
    metadata = json.loads(steem.get_content(post['user'],post['slug'])['json_metadata'])
    if post['account'] != last_account:
      n = n + 1
      last_account = post['account']
      if n > 1:
        content += '<img src="https://steemitimages.com/p/2FFvzA2zeqoVJ2SVhDmmumdPfnVEcahMce9nMwwksSDdRvQBSJ15CK7qPMiVRw3fSP6uC94yTyYJg4N59kGHCvx92PC9z477WfXCyNByjLWaj3FvtFQchhjkQVgWi?format=match&mode=fit&width=640" />'
      content += "\n"+'*Curator @'+post['account']+"*\n"
      content += '| <center>Thumb</center> | <center>User</center> | <center>Post</center> |'+"\n"
      content += '| --- | --- | --- |'+"\n"
    if post['title'] == '' and post['type'] == 2:
      post['title'] = 'Comment'
    vote = post['status'].split('/')[-1]
    content += '| <center><a href="'+post['link']+'"><img src="https://steemitimages.com/128x256/'+metadata['image'][0]+'" height="100px"/></a></center> | <center>@'
    content += post['user']+'</center> | <center><a href="'+post['link']+'">'+post['title']+'</a></center> |'+"\n"
  return content

def compilation():
  date = datetime.date.today().strftime("%B %d, %Y")
  title = 'Curangel curation compilation '+date

  content = getPostContent()
  print(content)
compilation()
