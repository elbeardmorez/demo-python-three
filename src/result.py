class result():
    url = ""
    data = []

    def __init__(self, url, data):
        self.url = url
        self.data = data

    def __str__(self):
        return f"url: '{self.url}'\n" + \
               "data: '" + ", ".join([f"{d[0]}|{d[1]}" for d in self.data]) + \
               "'"
