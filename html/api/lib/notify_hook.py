import requests
from loguru import logger

from .config import config

_warned = False


def _warn():
    global _warned
    if not _warned:
        logger.warning("ntfy not configured; skipping notification")
        _warned = True


def notify(subtopic, title, public_info="", *, priority="default", private_info=None):
    try:
        endpoint = config.ntfy.endpoint
        master_topic = config.ntfy.master_topic
        url = f"{endpoint}/{master_topic}--{subtopic}"
    except AttributeError:
        _warn()
        return

    try:
        result = requests.post(
            url,
            data=public_info,
            headers={
                "Title": title,
                "Priority": priority,
                "Firebase": "no"
            }
        )
    except requests.exceptions.RequestException:
        logger.exception(f"exception caught while notifying on {subtopic}")
        return

    if not result.status_code == requests.codes.ok:
        error = result.status_code
        logger.error(f"failed notification on {subtopic}: {error}")

