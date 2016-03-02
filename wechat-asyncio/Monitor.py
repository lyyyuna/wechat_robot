# coding=utf-8

import logging
import asyncio
from time import ctime
import config

logger = logging.getLogger('monitor')

class Monitor():
    def __init__(self, wx):
        self.wx = wx

    async def monitor(self):
        while True:
            logger.info('Monitoring.......... ' + ctime())
            logger.info('retcode %s,  selector %s' % (self.wx.retcode, self.wx.selector))
            logger.info('recvqueue size: %s' % self.wx.recvqueue.qsize())
            logger.info('sendqueue size: %s' % self.wx.sendqueue.qsize())
            logger.info('updatequeue size: %s' % self.wx.updatequeue.qsize())
            logger.info('Monitor end.......... ')

            if self.wx.recvqueue.qsize() > 3:
                while self.wx.recvqueue.qsize() > 1:
                    try:
                        self.wx.recvqueue.get_nowait()
                    except:
                        pass

            if self.wx.sendqueue.qsize() > 3:
                while self.wx.sendqueue.qsize() > 1:
                    try:
                        self.wx.sendqueue.get_nowait()
                    except:
                        pass

            if self.wx.updatequeue.qsize() > 3:
                while self.wx.updatequeue.qsize() > 1:
                    try:
                        self.wx.updatequeue.get_nowait()
                    except:
                        pass

            await asyncio.sleep(config.monitor_interval)
