import asyncio
import json
import tornado
from tornado import httpclient, httputil
from tornado.web import Application as httpserver, RequestHandler as handler
import src.api as api
from .exceptions import FatalException
from .utils import trace


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

    async def header(self, url, name):
        try:
            response = await self.client.fetch(
                url, method='HEAD',
                headers=self.request_headers, raise_error=False)
            return response.headers.get_list(name)
        except Exception as e:
            raise FatalException(e)

    async def pull(self, url, follow=False):
        try:
            return await self.client.fetch(
                url, headers=self.request_headers,
                follow_redirects=follow, raise_error=False)
        except Exception as e:
            raise FatalException(e)

    async def push(self, url, body=None, follow=False):
        try:
            return await self.client.fetch(
                url, method='POST', body=body,
                headers=self.request_headers,
                follow_redirects=follow, raise_error=False)
        except Exception as e:
            raise FatalException(e)


class next_url_handler(handler):
    def initialize(self, state):
        self.state = state

    async def get(self):
        next_ = api.spdr_next_url(self.state)
        self.set_status(200)
        if next_:
            trace(2, f"pushing url '{next_}' to slave")
        self.finish({'url': next_})


class add_links_handler(handler):
    def initialize(self, state):
        self.state = state

    async def post(self):
        data = json.loads(self.request.body)
        url = data['url']
        links = data['links']
        trace(2, f"received {len(links)} scraped link" +
              f"{'s' if len(links) != 0 else ''} from slave")
        asyncio.run_coroutine_threadsafe(
            api.spdr_add_links(url, links, self.state),
            loop=self.state.event_loops[f"{self.state.mode}-main"])
        self.set_status(200)
        self.finish()


class webserver:
    state = None
    server = None
    loop = None

    def __init__(self, state):
        trace(2, "starting server for master instance")
        self.state = state
        loop = tornado.ioloop.IOLoop(make_current=True)
        httpclient.AsyncHTTPClient.configure(
            "tornado.curl_httpclient.CurlAsyncHTTPClient")
        self.client = httpclient.AsyncHTTPClient(force_instance=True)

        self.server = httpserver([
            ('/next_url', next_url_handler, {'state': self.state}),
            ('/add_links', add_links_handler, {'state': self.state})
        ])
        self.server.listen(self.state.service[1])
        loop.start()

    def __del__(self):
        self.server.stop()
