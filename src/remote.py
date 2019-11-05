from tornado import httpclient, httputil


class webclient:
    request_headers = None

    def __init__(self):
        httpclient.AsyncHTTPClient.configure(
            "tornado.curl_httpclient.CurlAsyncHTTPClient")
        self.client = httpclient.AsyncHTTPClient(force_instance=True)

        self.request_headers = httputil.HTTPHeaders()
        self.request_headers.add("Keep-Alive", "timeout=5, max=100")
        self.request_headers.add("Connection", "Keep-Alive")
        self.request_headers.add("DNT", "1")
        self.request_headers.add("Upgrade-Insecure-Requests", "1")

    def __del__(self):
        self.client.close()

    async def pull(self, url):
        return await self.client.fetch(
            url, headers=self.request_headers,
            follow_redirects=False, raise_error=False)

    async def push(self, url, body=None):
        return await self.client.fetch(
            url, method='POST', body=body,
            headers=self.request_headers, raise_error=False)
