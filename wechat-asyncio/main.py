import aiohttp
import asyncio

from Wechat import Wechat




async def test(wx):

    await wx.login()

async def tes(wx):
    while True:
        await wx.log()


with aiohttp.ClientSession() as client:
    wx = Wechat(client)
    tasks = [test(wx), tes(wx)]
    asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))

