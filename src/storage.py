from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from .utils import trace
from .exceptions import FatalException


class storage:
    class __storage:
        state = None
        client = None

        def __init__(self, state):
            self.state = state
            self.client = MongoClient(self.uri())
            try:
                self.client.admin.command('buildinfo')
                self.setup()
            except ConnectionFailure:
                self.client.close()
                self.client = None
                trace("mongodb connection failure")

        def uri(self):
            return f"mongodb://{self.state.storage[0]}:" + \
                   f"{self.state.storage[1]}/"

        def connected(self):
            return self.client is not None

        def connect_or_die(self):
            if not self.connected():
                raise FatalException(
                    "storage implementation error, no reconnects!")

        def restore_state(self):
            self.connect_or_die()

        def reset_state(self):
            self.connect_or_die()

        def reset(self):
            self.connect_or_die()

        def setup(self):
            connection_address = self.state.storage
            database = "spider"
            collections = ["unprocessed", "processing", "processed"]

    instance = None

    def __init__(self, state):
        if not storage.instance:
            storage.instance = storage.__storage(state)

    def __getattr__(self, name):
        return getattr(self.instance, name)
