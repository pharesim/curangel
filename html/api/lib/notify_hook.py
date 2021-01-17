import requests
from loguru import logger

from .config import config

_warned = False


def _warn():
    global _warned
    if not _warned:
        logger.warning("notify_endpoint not configured; skipping notification")
        _warned = True


def notify(channel, data):
    try:
        url = config.notify_endpoint
    except AttributeError:
        _warn()
        return

    body = {
        "channel": channel,
        "data": data
    }
    try:
        result = requests.post(config.notify_endpoint, json=data)
    except requests.exceptions.RequestException:
        logger.exception(f"exception caught while notifying channel {channel}")
        return

    if not result.status_code == requests.codes.ok:
        error = result.status_code
        logger.error(f"failed notification on channel {channel}: {error}")

