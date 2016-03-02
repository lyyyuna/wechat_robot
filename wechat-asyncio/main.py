# coding=utf-8

import aiohttp
import asyncio

from Wechat import Wechat
from MsgHandler import MsgHandler
from RobotEngine import RobotEngine
from Monitor import Monitor
import auth

import logging
import logging.config

logging.config.fileConfig("logger.conf")

with aiohttp.ClientSession() as client, aiohttp.ClientSession() as rclient:
    wx = Wechat(client)
    robot = RobotEngine(rclient, auth.apikey)
    msg = MsgHandler(wx, robot)
    god = Monitor(wx)
    tasks = [
            wx.sync() ,
            wx.sendmsg() ,
            wx.updategroupinfo() ,
            msg.msgloop() ,
            god.monitor()
            ]
    asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))
