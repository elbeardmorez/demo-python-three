from collections import deque
from threading import Lock


class state:
    class __state:
        def __init__(self):
            self.mode = "master"
            self.target = ""
            self.scope = ""
            self.url_pools = {
                "unprocessed": deque(),
                "processing": {},
                "processed": {},
                "vulnerable": [],
            }
            self.blacklist = ['logout']
            self.mutex = {
                "processed": Lock(),
                "processing": Lock(),
                "unprocessed": Lock(),
            }
            self.credentials = [('admin', 'password')]
            self.service = ('localhost', 10080)
            self.verbosity = 0

    instance = None

    def __init__(self):
        if not state.instance:
            state.instance = state.__state()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name, value):
        return setattr(self.instance, name, value)
