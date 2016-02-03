# coding=utf-8

class MsgHandler:
    def __init__(self, wx, robot):
        self.__wx = wx

    async def msgloop(self):
        while True:
            await asyncio.sleep(1)
