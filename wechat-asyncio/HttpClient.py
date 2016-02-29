# coding=utf-8

import logging
import asyncio
import aiohttp
import json

logger = logging.getLogger('wx')


class HttpClient:
    def __init__(self, client):
        if not isinstance(client, aiohttp.ClientSession):
            raise TypeError('Please init with a aiohttp.ClientSession instance')
        self.__client = client
        self.__cookies = None

    async def get(self, url, params=None):
        try:
            self.__cookies = self.__client.cookies
            async with await self.__client.get(url, params=params) as r:
                #assert r.status == 200
                return await r.text()

        except Exception:
            logger.exception("Network Exception, url: %s, params: %s" % (url, params))
            return None

    async def get_json(self, url, params=None):
        try:
            self.__cookies = self.__client.cookies
            async with await self.__client.get(url, params=params) as r:
                text = await r.text(encoding='utf-8')
                return json.loads(text)

        except Exception:
            logger.exception("Network Exception, url: %s, params: %s" % (url, params))
            return None

    async def get_json_timeout(self, url, params=None):
        try:
            self.__cookies = self.__client.cookies
            with aiohttp.Timeout(2):
                async with await self.__client.get(url, params=params) as r:
                    text = await r.text(encoding='utf-8')
                    return json.loads(text)

        except Exception:
            logger.exception("Network Exception, url: %s, params: %s" % (url, params))
            return None

    async def post(self, url, data, params=None):
        try:
            async with await self.__client.post(url, params=params, data=data) as r:
                #assert r.status == 200
                return await r.text()

        except Exception:
            logger.exception("Network Exception, url: %s, params: %s" % (url, params))
            return None

    async def post_json(self, url, data, params=None):
        try:

            async with await self.__client.post(url, params=params, data=data) as r:
                #assert r.status == 200
                text = await r.text(encoding='utf-8')
                return json.loads(text)

        except Exception:
            logger.exception("Network Exception, url: %s, params: %s" % (url, params))
            return None

    async def downloadfile(self, url, data, filename):
        try:
            async with await self.__client.post(url, data=data) as r:
                #assert r.status == 200
                with open(filename, 'wb') as fd:
                    while True:
                        chunk = await r.content.read(512)
                        if not chunk:
                            break
                        fd.write(chunk)
                return True
        except aiohttp.errors.DisconnectedError:
            return False
