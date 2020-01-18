import steem.steem

DEFAULT_NODES = ['https://anyx.io',
                 'https://api.steemit.com',
#                 'https://steemd.minnowsupportproject.org']


class Steem(steem.steem.Steem):
    def __init__(self, **kwargs):
        if "nodes" in kwargs:
            nodes = kwargs["nodes"]
        else:
            nodes = DEFAULT_NODES
        super().__init__(nodes, **kwargs)
