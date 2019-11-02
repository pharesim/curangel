#! /bin/env python3

import time
import datetime
import json
import rfc3987
from string import ascii_letters, digits

from db import DB

from steem.steem import Steem
from steem.blockchain import Blockchain

steemd_nodes = [
  'https://anyx.io',
  'https://api.steemit.com',
  'https://steemd.minnowsupportproject.org',
]

credfile = open("credentials.txt")
user = credfile.readline().strip()
key = credfile.readline().strip()

db    = DB('curangel.sqlite3')
steem = Steem(keys=[key],nodes=steemd_nodes)
chain = Blockchain(steem)

mentions = []

def getVotedPosts():
  return db.select('upvotes',['account','user','link','slug','title','status','type'],{'status LIKE':'voted%','vote_time >':"datetime('now','-1 day')"},'account','9999')

def escape(text):
  escaped = ""
  for character in text:
    if character not in ascii_letters + digits:
      codepoint = ord(character)
      escaped += "&#{codepoint};".format(**locals())
    else:
      escaped += character
  return escaped

def getPostContent():
  content = '<center>'+"\n"
  content += '# Welcome to the daily compilation post of the Curangel project'+"\n<br />\n"
  content += 'https://i.imgur.com/NI4bwBx.png<br />'+"\n"
  content += 'Here we highlight the posts picked by our curators, providing you with a resource to discover content worth your time, and maybe even your vote!'+"\n"
  content += '<img src="https://steemitimages.com/p/2FFvzA2zeqoVJ2SVhDmmumdPfnVEcahMce9nMwwksSDdRvQBSJ15CK7qPMiVRw3fSP6uC94yTyYJg4N59kGHCvx92PC9z477WfXCyNByjLWaj3FvtFQchhjkQVgWi" />'+"\n"

  content += getVotesTable(getVotedPosts())

  content += '<img src="https://steemitimages.com/p/2FFvzA2zeqoVJ2SVhDmmumdPfnVEcahMce9nMwwksSDdRvQBSJ15CK7qPMiVRw3fSP6uC94yTyYJg4N59kGHCvx92PC9z477WfXCyNByjLWaj3FvtFQchhjkQVgWi" />'+"\n"

  content += 'Thank you for your interest in the Curangel project! If you want to help us supporting a wide range of valuable community members and at the same time receive a share of the generated curation rewards, consider sending us a delegation. '
  content += 'By doing so, you will also receive the possibility to help us move rewards from overrated posts back to the pool.'+"\n"
  content += 'For more info, check out our '
  content += '<a href="https://steemit.com/curangel/@curangel/announcing-the-curangel-project-curation-serving-everyone">introduction post</a>'+"\n"

  content += '<img src="https://steemitimages.com/p/2FFvzA2zeqoVJ2SVhDmmumdPfnVEcahMce9nMwwksSDdRvQBSJ15CK7qPMiVRw3fSP6uC94yTyYJg4N59kGHCvx92PC9z477WfXCyNByjLWaj3FvtFQchhjkQVgWi" />'+"\n"
  content += 'Come and join our <a href="https://discord.gg/yrzAZqS">Discord</a>!'+"\n"

  content += 'https://i.imgur.com/1TgMmfZ.png'

  content += 'The Curangel project is brought to you by witness <a href="http://pharesim.me">@pharesim</a>'+"\n"
  content += 'Vote for your witnesses <a href="https://steemit.com/~witnesses">here</a>'+"\n"

  content += '</center>'
  return content

def getThumbnailContent(metadata):
  if 'image' not in metadata:
    return 'no preview'
  images = metadata['image']
  if len(images) < 1:
    return 'no preview'
  try:
    img_uri = images[0].strip()
    rfc3987.parse(img_uri, "URI")
    return '<img src="https://steemitimages.com/128x256/{img_uri}" />'.format(**locals())
  except Exception:
    return 'no preview'

def getVotesTable(posts):
  content = ''
  last_account = ''
  n = 0
  for post in posts:
    metadata = steem.get_content(post['user'],post['slug'])['json_metadata']
    if metadata != '':
      metadata = json.loads(metadata)

      # skip vimm.tv streams
      if 'app' in metadata:
        app = metadata['app'].split('/')
        if app == 'vimm.tv':
          continue

    if post['account'] != last_account:
      n = n + 1
      last_account = post['account']
      if n > 1:
        content += '<img src="https://steemitimages.com/p/2FFvzA2zeqoVJ2SVhDmmumdPfnVEcahMce9nMwwksSDdRvQBSJ15CK7qPMiVRw3fSP6uC94yTyYJg4N59kGHCvx92PC9z477WfXCyNByjLWaj3FvtFQchhjkQVgWi" />'
      content += "\n"+'*Curator @'+post['account']+"*\n"
      mentions.append(post['account'])
      content += '| <center>Thumb</center> | <center>User</center> | <center>Post</center> |'+"\n"
      content += '| --- | --- | --- |'+"\n"
    title = ''
    if post['title'] == '' and post['type'] == 2:
      title = 'Comment'
    else:
      title = escape(post['title'])
    vote = post['status'].split('/')[-1]
    image = getThumbnailContent(metadata)
    content += '| <center><a href="'+post['link']+'">'+image+'</a></center> | <center>@'
    content += post['user']+'</center> | <center><a href="'+post['link']+'">'+title+'</a></center> |'+"\n"
    mentions.append(post['user'])
  return content

def compilation():
  date = datetime.datetime.utcnow().strftime("%B %d, %Y")

  title  = 'Curangel curation compilation '+date
  body   = getPostContent()
  author = user
  tags   = ['curangel','curation','palnet','neoxian']
  json_metadata = {'users':mentions,'image':['https://i.imgur.com/NI4bwBx.png']}

  last_post_time = steem.get_account(user)['last_post']
  steem.commit.post(title, body, author, tags=tags, json_metadata=json_metadata)
  while last_post_time == steem.get_account(user)['last_post']:
    time.sleep(1)
  print(date+' posted!')

if __name__ == "__main__":
  compilation()
