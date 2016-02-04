# coding=utf-8

import aiohttp
import asyncio

from Wechat import Wechat
from MsgHandler import MsgHandler
from RobotEngine import RobotEngine

with aiohttp.ClientSession() as client, aiohttp.ClientSession() as rclient:
    wx = Wechat(client)
    robot = RobotEngine(rclient)
    msg = MsgHandler(wx, robot)
    tasks = [
            wx.sync(),
            wx.sendmsg(),
            wx.updategroupinfo(),
            msg.msgloop(),
            ]
    asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))
