# coding=utf-8

import asyncio
import re
import config
from HttpClient import *
import RobotPredefinedAnswer
import random

class RobotEngine():
    def __init__(self, client):
        self.rbclient = HttpClient(client)
        self.acc = 0
        self.lasttext = ''
        self.lastuser = ''

    async def answser(self, msginfo):
        content = msginfo['Content']
        # 去掉英文，因为图灵机器人不支持
        content = re.sub(r'[a-zA-Z]', '', content)
        # 做一下字数限制
        content = content[:50]
        tuling_url = 'http://www.tuling123.com/openapi/api?key=' +\
                 config.apikey + '&info=' + content
        print (tuling_url)
        dic = await self.rbclient.get_json(tuling_url)
        if dic != None:
            text = dic['text']
        else:
            text = '网络异常。。。。。。。。。。。。'
        # 做一下字数回复的限制
        if len(text)>100:
            text = text[:100]
            text = text + '......'
        print (11111)
        # 对于不能回答的问题直接回复数数
        if text.find('不明白你是什么意思，麻烦换一种说法') != -1:
            text = str(self.acc)
            self.acc = self.acc + 1
        if text.find('不明白你说的什么意思') != -1:
            text = str(self.acc)
            self.acc = self.acc + 1
        if text == self.lasttext and msginfo['FromUserName'] == self.lastuser:
            text = self.__randomanswer()

        self.lasttext = text
        self.lastuser = msginfo['FromUserName']
        return text

    def __randomanswer(self):
        diaglen = len(RobotPredefinedAnswer.dialoglist)
        index = random.randint(0, diaglen-1)
        return RobotPredefinedAnswer.dialoglist[index]
