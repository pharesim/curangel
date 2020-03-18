#! /bin/env python3

from threading import Thread
from time import sleep, time
from traceback import format_exc

from hive.hive import Hive

from voter import Voter

# Print status at least once every this many seconds.
MONITOR_INTERVAL_SEC = 300

hived_nodes = [
#  'https://anyx.io',
  'https://api.hive.blog',
]

class Curangel(Thread):
  def __init__(self, user, postingKey):
    self.client = Hive(keys=[postingKey],nodes=hived_nodes)
    self.user = user
    self.voter = Voter(self.client, user)
    self.last_update_duration = 0
    super().__init__(None)
    self.daemon = True

  def wait_for_recharge(self):
    while True:
      current_vp = self.voter.get_current_vp()
      if current_vp >= 9990:
        return
      else:
        t = "voting power at {:0.2f}%; "
        t += "estimated 100% in {}.\n"
        t += "waking up in {:0.3f}s."
        recharge_time = self.voter.get_recharge_time()
        sleep_s = recharge_time.total_seconds()
        if sleep_s > 0:
          print(t.format(current_vp / 100,
                str(recharge_time),
                sleep_s))
          sleep(min([sleep_s, MONITOR_INTERVAL_SEC]))
        else:
          return

  def run(self):
    while True:
      try:
        self.wait_for_recharge()
        uri, id = self.voter.next_in_queue(self.client)
        if uri is False:
          print("\nqueue is empty. Sleeping for a minute.")
          sleep(60)
        else:
          self.voter.vote(uri, id)
      except Exception:
        # log exception, sleep 10 seconds and retry
        print(format_exc())
        sleep(10)
        print("\nretrying after exception...")
        pass

if __name__ == '__main__':
  credfile = open("credentials.txt")
  user = credfile.readline().strip()
  key = credfile.readline().strip()

  curangel = Curangel(user,key)

  curangel.start()
  curangel.join()
