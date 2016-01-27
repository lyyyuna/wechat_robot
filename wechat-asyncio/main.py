# coding=utf-8

import aiohttp
import asyncio

from Wechat import Wechat

with aiohttp.ClientSession() as client:
    wx = Wechat(client)
    tasks = [wx.sync(), wx.sendmsg()]
    asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))

