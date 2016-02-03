# coding=utf-8

import asyncio

class RobotEngine():
    def __init__(self):
        pass

    async def dance(self):
        while True:
            await asyncio.sleep(1)
