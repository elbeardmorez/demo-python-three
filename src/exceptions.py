class FatalException(Exception):
    def __init__(self, e=None):
        self.e = e


class NonFatalException(Exception):
    def __init__(self, e=None):
        self.e = e
