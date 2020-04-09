import hive.hive

DEFAULT_NODES = [
  'https://api.pharesim.me',
  'https://anyx.io',
  'https://api.hive.blog',
  'https://api.openhive.network',
]


class Hive(hive.hive.Hive):
    def __init__(self, **kwargs):
        if "nodes" in kwargs:
            nodes = kwargs["nodes"]
        else:
            nodes = DEFAULT_NODES
        super().__init__(nodes, **kwargs)
