from collections import deque
from threading import Lock


class state:
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
        self.storage = ('localhost', 27017)
        self.modified = 0
        self.sync_threshold = 10
        self.verbosity = 0
