from threading import Thread, Event
from datetime import datetime, timedelta

import _cgi_path  # noqa: F401
from lib.notify_hook import notify


class _Watchdog(Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self._timeout_seconds = None
        self._next_notify_time = datetime.max
        self._event = Event()

    @property
    def timeout_seconds(self):
        return self._timeout_seconds

    @timeout_seconds.setter
    def timeout_seconds(self, seconds):
        self._timeout_seconds = seconds
        self._set(datetime.now())

    def _set(self, dt: datetime):
        if self.timeout_seconds is None:
            self._next_notify_time = datetime.max
        else:
            interval = timedelta(seconds=self.timeout_seconds)
            self._next_notify_time = dt + interval
        self._event.set()

    def run(self):
        self._set(datetime.now())
        while True:
            now = datetime.now()
            if now > self._next_notify_time:
                self._next_notify_time = datetime.max
                notify(
                    "bot-watchdog",
                    "Curangel bot is unresponsive",
                    "watchdog timer expired",
                    priority="urgent"
                )
            else:
                sleep_for = self._next_notify_time - now
                try:
                    self._event.wait(sleep_for.total_seconds())
                except OverflowError:
                    self._event.wait(timedelta(days=1).total_seconds())
                self._event.clear()

    def touch(self):
        self._set(datetime.now())


watchdog = _Watchdog()
watchdog.start()
