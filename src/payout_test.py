#! /bin/env python3

import math
from datetime import datetime
from time import sleep

from db import DB

from hive.hive import Hive
from hive.account import Account
from hive.converter import Converter
from hive.blockchain import Blockchain

hived_nodes = [
#  'https://anyx.io',
  'https://api.hive.blog',
]

credfile = open("credentials.txt")
bot = credfile.readline().strip()
postkey = credfile.readline().strip()
key = credfile.readline().strip()

db    = DB('curangel.sqlite3')
client = Hive(keys=[key],nodes=hived_nodes)
chain = Blockchain(client)
converter = Converter(client)
account = Account(bot,client)

client.claim_reward_balance(account=bot)
