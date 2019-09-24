import os

from yaml import safe_load
from munch import munchify

with open (os.path.join(os.path.split(__file__)[0],
                        "../../../config/config.yaml"), "r") as f:
    config = munchify(safe_load(f))
