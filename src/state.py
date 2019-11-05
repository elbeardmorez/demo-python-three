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
        self.mutex = {
            "processed": Lock(),
            "processing": Lock(),
            "unprocessed": Lock(),
        }
        self.credentials = [('admin', 'password')]
        self.verbose = 0
