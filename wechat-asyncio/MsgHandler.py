# coding=utf-8

LOG = True
DEBUG = True

import asyncio
import re

class MsgHandler:
    def __init__(self, wx, robot):
        self.wx = wx
        self.robot = robot

    async def __parsemsg(self):
        msg = await self.wx.recvqueue.get()
        # 自己从别的平台发的消息忽略
        if msg['FromUserName'] == self.wx.My['UserName']:
            return None
        # 排除不是发给自己的消息
        if msg['ToUserName'] != self.wx.My['UserName']:
            return None
        # 在黑名单里面
        if msg['FromUserName'] in self.wx.blacklist:
            return None

        msginfo = {}
        # 文字消息
        if msg['MsgType'] == 1:
            content = msg['Content']
            fromsomeone_NickName = ''
            ## 来自群消息
            if msg['FromUserName'].find('@@') != -1:
                fromsomeone = content[:content.find(':<br/>')]
                groupname = msg['FromUserName']
                if groupname not in self.wx.grouplist:
                    await self.wx.updatequeue.put(groupname)
                elif fromsomeone in self.wx.grouplist[groupname]:
                    fromsomeone_NickName = self.wx.grouplist[groupname][fromsomeone]
                    fromsomeone_NickName = '@' + fromsomeone_NickName + ' '
                else:
                    await self.wx.updatequeue.put(groupname)
                # 去掉消息头部的来源信息
                content = content[content.find('>')+1:]
            # 普通消息
            else:
                fromsomeone_NickName = ''

            # print (content)
            if len(content)>1:
                regx = re.compile(r'@.+?\u2005')
                content = regx.sub(' ', content)

            if DEBUG == True:
                print (content)
            msginfo['Content'] = content
            msginfo['fromsomeone'] = fromsomeone_NickName
            msginfo['FromUserName'] = msg['FromUserName']

            return msginfo
        else:
            return None

    async def msgloop(self):
        while True:
            msginfo = await self.__parsemsg()
            if msginfo != None:
                response = {}
                answser = await self.robot.answser(msginfo)
                response['Content'] = msginfo['fromsomeone'] + answser
                response['user'] = msginfo['FromUserName']
                await self.wx.sendqueue.put(response)
                if LOG == True:
                    # windows 上打印一些字符会有问题
                    try:
                        print (msginfo['fromsomeone'] + ' say: ' + msginfo['Content'])
                        print ('Harry Potter say: ' + response['Content'])
                    except:
                        pass
            await asyncio.sleep(1)
