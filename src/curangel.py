#! /bin/env python3

from time import sleep, time
from traceback import format_exc

from hive.hive import Hive

from voter import Voter
from watchdog import watchdog

import _cgi_path # noqa: F401
from lib.config import config, load_credentials

# Print status at least once every this many seconds.
MONITOR_INTERVAL_SEC = 300

class Curangel():
  def __init__(self, user, postingKey):
    self.client = Hive(keys=[postingKey],nodes=config.nodes)
    self.user = user
    self.voter = Voter(self.client, config.nodes, user)
    self.last_update_duration = 0

  def wait_for_recharge(self):
    while True:
      sleep(3)
      current_vp = self.voter.get_current_vp()
      if current_vp >= 9990:
        print('VP at '+str(current_vp))
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
      watchdog.touch()
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
  credentials = load_credentials()
  user = credentials.username
  key = credentials.posting

  # allow up to 1.25x the status logging interval before sending notification
  watchdog.timeout_seconds = 1.25 * MONITOR_INTERVAL_SEC
  curangel = Curangel(user,key)

  curangel.run()
