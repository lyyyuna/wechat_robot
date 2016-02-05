# coding=utf-8


import asyncio

class Monitor():
    def __init__(self, wx):
        self.wx = wx

    async def monitor(self):
        while True:
            print
            print ('Monitoring..........')
            print ('SyncKey: ', self.wx.SyncKey['List'][0])
            print ('recvqueue size: ', self.wx.recvqueue.qsize())
            print ('sendqueue size: ', self.wx.sendqueue.qsize())
            print ('updatequeue size: ', self.wx.updatequeue.qsize())
            print

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

            await asyncio.sleep(5)
