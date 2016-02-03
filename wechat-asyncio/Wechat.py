# coding=utf-8

# import logging
# import logging.handlers
#
# LOG_FILE = 'WechatLogin.log'
#
# handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes = 1024*1024, backupCount = 5) # 实例化handler
# fmt = '%(asctime)s <%(filename)s>: [%(levelname)s] - %(message)s'
# formatter = logging.Formatter(fmt)   #
# handler.setFormatter(formatter)      #
# logger = logging.getLogger()    #
# logger.addHandler(handler)
# logger.setLevel(logging.DEBUG)

DEBUG = True

from HttpClient import HttpClient
import aiohttp
import asyncio
import time
import re
import xml.dom.minidom
import json
import html

class Wechat():
    def __init__(self, client):
        self.__wxclient = HttpClient(client)
        self.tip = 0
        self.deviceId = 'e000701000000000'

        self.recvqueue = asyncio.Queue()
        self.sendqueue = asyncio.Queue()
        self.blacklist = []
        self.updatequeue = asyncio.Queue() # 更新群组信息的请求
        self.grouplist = {} # 存储群组的联系人信息

    async def __getuuid(self):
        # logging.debug('Entering getuuid.')
        url = 'https://login.weixin.qq.com/jslogin'
        payload = {
            'appid': 'wx782c26e4c19acffb',
            'fun': 'new',
            'lang': 'zh_CN',
            '_': int(time.time()),
        }

        text = await self.__wxclient.post(url=url, data=payload)
        # logging.info(text)

        regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
        pm = re.search(regx, text)

        code = pm.group(1)
        uuid = pm.group(2)

        self.uuid = uuid
        if code == '200':
            return True
        else:
            return False

    async def __downloadQR(self):
        # logging.debug('Entering downloadQR.')
        url = 'https://login.weixin.qq.com/qrcode/' + self.uuid
        payload = {
            't': 'webwx',
            '_': int(time.time()),
        }

        su = await self.__wxclient.downloadfile(url, data=payload, filename='qrimage.jpg')
        print ('请扫描二维码')
        return su

    async def __waitforlogin(self):
        # logging.debug('Waiting for login.......')
        url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (self.tip, self.uuid, int(time.time()))
        text = await self.__wxclient.get(url)

        regx = r'window.code=(\d+);'
        pm = re.search(regx, text)
        code = pm.group(1)

        if code == '201':
            print ('成功扫描,请在手机上点击确认以登录')
            self.tip = 0
        elif code == '200':
            print ('正在登录。。。')
            regx = r'window.redirect_uri="(\S+?)";'
            pm = re.search(regx, text)
            redirect_uri = pm.group(1) + '&fun=new'
            self.redirect_uri  = redirect_uri
            base_uri = redirect_uri[:redirect_uri.rfind('/')]
            self.base_uri = base_uri

            services = [
                ('wx2.qq.com', 'webpush2.weixin.qq.com'),
                ('qq.com', 'webpush.weixin.qq.com'),
                ('web1.wechat.com', 'webpush1.wechat.com'),
                ('web2.wechat.com', 'webpush2.wechat.com'),
                ('wechat.com', 'webpush.wechat.com'),
                ('web1.wechatapp.com', 'webpush1.wechatapp.com'),
            ]

            push_uri = base_uri
            for (searchUrl, pushUrl) in services:
                if base_uri.find(searchUrl) >= 0:
                    push_uri = 'https://%s/cgi-bin/mmwebwx-bin' % pushUrl
                    break
            self.push_uri = push_uri
        elif code == '408':
            pass

        return code


    async def __checklogin(self):
        # logging.debug('Entering checklogin.')
        text = await self.__wxclient.get(self.redirect_uri)

        doc = xml.dom.minidom.parseString(text)
        root = doc.documentElement

        for node in root.childNodes:
            if node.nodeName == 'skey':
                skey = node.childNodes[0].data
            elif node.nodeName == 'wxsid':
                wxsid = node.childNodes[0].data
            elif node.nodeName == 'wxuin':
                wxuin = node.childNodes[0].data
            elif node.nodeName == 'pass_ticket':
                pass_ticket = node.childNodes[0].data

        if not all((skey, wxsid, wxuin, pass_ticket)):
            return False

        BaseRequest = {
            'Uin': int(wxuin),
            'Sid': wxsid,
            'Skey': skey,
            'DeviceID': self.deviceId,
        }
        # logging.debug('%s, %s, %s, %s', skey, wxsid, wxuin, pass_ticket)
        self.skey = skey
        self.wxsid = wxsid
        self.wxuin = wxuin
        self.pass_ticket = pass_ticket
        self.BaseRequest = BaseRequest

        return True


    async def __responseState(self, func, BaseResponse):
        ErrMsg = BaseResponse['ErrMsg']
        Ret = BaseResponse['Ret']
        # logging.info('func: %s, Ret: %d, ErrMsg: %s' % (func, Ret, ErrMsg))
        if Ret != 0:
            return False
        return True


    async def __webwxinit(self):
        # logging.debug('Entering webwxinit.')
        url = self.base_uri + \
            '/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (
                self.pass_ticket, self.skey, int(time.time()))
        payload = {
            'BaseRequest' : self.BaseRequest
        }

        dic = await self.__wxclient.post_json(url=url, data=json.dumps(payload))

        self.My = dic['User']
        self.SyncKey = dic['SyncKey']
        # logging.debug('The new SyncKey is: %s' % self.SyncKey)

        return await self.__responseState('webwxinit', dic['BaseResponse'])

    async def __webwxgetcontact(self):
        url = self.base_uri + \
        '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (
            self.pass_ticket, self.skey, int(time.time()))

        dic = await self.__wxclient.get_json(url)

        SpecialUsers = ["newsapp", "fmessage", "filehelper", "weibo", "qqmail", "tmessage", "qmessage", "qqsync", "floatbottle", "lbsapp", "shakeapp", "medianote", "qqfriend", "readerapp", "blogapp", "facebookapp", "masssendapp",
                    "meishiapp", "feedsapp", "voip", "blogappweixin", "weixin", "brandsessionholder", "weixinreminder", "wxid_novlwrv3lqwv11", "gh_22b87fa7cb3c", "officialaccounts", "notification_messages", "wxitil", "userexperience_alarm"]
        self.blacklist += SpecialUsers

        MemberList = {}
        for member in dic['MemberList']:
            if member['VerifyFlag'] & 8 != 0: # 公众号
                continue
            elif member['UserName'] in SpecialUsers:
                continue
            MemberList[member['UserName']] = {
                'NickName' : member['NickName'] ,
                'DisplayName' : member['DisplayName']
            }

        self.memberlist = MemberList
        # logging.info('You have %s friends.' % len(MemberList))



    async def __login(self):
        success = await self.__getuuid()
        if not success:
            print ('获取 uuid 失败')
        success = await self.__downloadQR()
        if not success:
            print ('获取二维码失败')

        while await self.__waitforlogin() != '200':
            pass

        success = await self.__checklogin()
        if not success:
            print ('登陆失败')
        print ('登陆成功')
        success = await self.__webwxinit()
        if not success:
            print ('初始化失败')
        print ('初始化成功')

        await self.__webwxgetcontact()

    def __syncKey(self):
        SyncKey = self.SyncKey
        SyncKeyItems = ['%s_%s' % (item['Key'], item['Val'])
                        for item in SyncKey['List']]
        SyncKeyStr = '|'.join(SyncKeyItems)
        return SyncKeyStr

    async def __synccheck(self):
        url = self.push_uri + '/synccheck?'
        BaseRequest = self.BaseRequest
        params = {
            'skey': BaseRequest['Skey'] ,
            'sid': BaseRequest['Sid'] ,
            'uin': BaseRequest['Uin'] ,
            'deviceId': BaseRequest['DeviceID'] ,
            'synckey': self.__syncKey() ,
            'r': int(time.time()*1000)
        }
        text = await self.__wxclient.get(url, params = params)
        regx = r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}'
        pm = re.search(regx, text)

        retcode = pm.group(1)
        selector = pm.group(2)
        # logging.info('retcode: %s, selector: %s' % (retcode, selector))
        return (retcode, selector)

    async def __webwxsync(self):
        url = self.base_uri + '/webwxsync?'
        payload = {
            'BaseRequest' : self.BaseRequest ,
            'SyncKey' : self.SyncKey ,
            'rr' : ~int(time.time())
        }
        params = {
            'skey' : self.BaseRequest['Skey'] ,
            'pass_ticket' : self.pass_ticket ,
            'sid' : self.BaseRequest['Sid']
        }

        dic = await self.__wxclient.post_json(url, params=params, data=json.dumps(payload))
        # 更新 synckey
        self.SyncKey = dic['SyncKey']

        await self.__responseState('webwxsync', dic['BaseResponse'])

        msglist = dic['AddMsgList']
        for msg in msglist:
            await self.recvqueue.put(msg)


    async def __webwxsendmsg(self, content, user):
        url = self.base_uri + \
            '/webwxsendmsg?pass_ticket=%s' % (self.pass_ticket)

        msgid = int(time.time()*10000000)
        msg = {
            'ClientMsgId' : msgid ,
            'Content' : content,
            'FromUserName' : self.My['UserName'] ,
            'LocalID' : msgid ,
            'ToUserName' : user,
            'Type' : 1
        }
        payload = {
            'BaseRequest' : self.BaseRequest ,
            'Msg' : msg
        }
        data = json.dumps(payload, ensure_ascii=False)
        data = data.encode('utf-8')

        if DEBUG == True
            print (data)
        text = await self.__wxclient.post(url, data=data)
        # print (text)


    async def __webwxbatchgetcontact(self, groupname):
        url = self.base_uri + '/webwxbatchgetcontact?'
        List = [{
            'ChatRoomId' : '',
            'UserName' : groupname
        }]
        payload = {
            'BaseRequest': self.BaseRequest ,
            'Count' : 1 ,
            'List' : List
        }
        params = {
            'lang' : 'zh_CN' ,
            'type' : 'ex' ,
            'pass_ticket' : self.pass_ticket ,
            'r' : int(time.time())
        }

        dic = await self.__wxclient.post_json(url, params=params, data=json.dumps(payload))
        GroupMapUsers = {}
        ContactList = dic['ContactList']
        for contact in ContactList:
            memberlist = contact['MemberList']
            for member in memberlist:
                # 默认 @群名片，没有群名片就 @昵称
                nickname = member['NickName']
                displayname = member['DisplayName']
                AT = ''
                if displayname == '':
                    # 有些人的昵称会有表情 <span> 会表示成 &lt;span&gt;
                    # 需要 html.unescape() 转义一下
                    AT = html.unescape(nickname)
                else:
                    AT = html.unescape(displayname)
                GroupMapUsers[member['UserName']] = AT

        self.grouplist[groupname] = GroupMapUsers

    async def sync(self):
        await self.__login()
        print ('开始心跳噗通噗咚 咚咚咚！！！！')
        # logging.info('Begin to sync with wx server.....')
        while True:
            retcode, selector = await self.__synccheck()
            if retcode != '0':
                print ('sync 失败')
            if selector == '2':
                await self.__webwxsync()

            await asyncio.sleep(1)


    async def sendmsg(self):
        while True:
            print (self.recvqueue.qsize())
            await asyncio.sleep(1)

            response = await self.sendqueue.get()
            print ('shoudao huifu')
            await self.__webwxsendmsg(response['Content'], response['user'])

    async def updategroupinfo(self):
        while True:
            groupname = await self.updatequeue.get()
            print ('更新群信息ddd')
            await self.__webwxbatchgetcontact(groupname)
            await asyncio.sleep(1)
            print ('更新群信息')
