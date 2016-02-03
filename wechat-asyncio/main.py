# coding=utf-8

import aiohttp
import asyncio

from Wechat import Wechat
from MsgHandler import MsgHandler
from RobotEngine import RobotEngine

with aiohttp.ClientSession() as client:
    wx = Wechat(client)
    robot = RobotEngine()
    msg = MsgHandler(wx, robot)
    tasks = [
            wx.sync(),
            wx.sendmsg(),
            wx.updategroupinfo(),
            msg.msgloop(),
            robot.dance()
            ]
    asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))
