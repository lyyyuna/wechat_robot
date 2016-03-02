# coding=utf-8

import aiohttp
import asyncio

from Wechat import Wechat
from MsgHandler import MsgHandler
from RobotEngine import RobotEngine
from Monitor import Monitor
import auth

import logging
import logging.handlers

WXLOG_FILE = 'wx.log'
MOLOG_FILE = 'monitor.log'

handler = logging.handlers.RotatingFileHandler(WXLOG_FILE, maxBytes = 1024*1024, backupCount = 5) # 实例化handler
fmt = '%(asctime)s <%(filename)s><%(lineno)d>: [%(levelname)s] - %(message)s'
handler2 = logging.handlers.RotatingFileHandler(MOLOG_FILE, maxBytes = 1024*1024, backupCount = 5) # 实例化handler

formatter = logging.Formatter(fmt)   #
handler.setFormatter(formatter)      #
handler2.setFormatter(formatter)
logger = logging.getLogger('wx')    #
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
logger1 = logging.getLogger('monitor')    #
logger1.addHandler(handler2)
logger1.setLevel(logging.DEBUG)



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
