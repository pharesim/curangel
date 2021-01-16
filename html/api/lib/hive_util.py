import hive.hive

from .config import config


class Hive(hive.hive.Hive):
    def __init__(self, **kwargs):
        if "nodes" in kwargs:
            nodes = kwargs["nodes"]
        else:
            nodes = config.nodes
        super().__init__(nodes, **kwargs)
