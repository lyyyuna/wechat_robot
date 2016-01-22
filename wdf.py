#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function

import os
try:
    from urllib import urlencode, quote_plus
except ImportError:
    from urllib.parse import urlencode, quote_plus

try:
    import urllib2 as wdf_urllib
    from cookielib import CookieJar
except ImportError:
    import urllib.request as wdf_urllib
    from http.cookiejar import CookieJar

import re
import time
import xml.dom.minidom
import json
import sys
import math
import subprocess
import ssl
import thread

DEBUG = True


interested_user = {u'加一坏成狗':1, u'蠡湖官方扯淡分队':1}
user_interested = {}
contents_to_response = {}
##########


QRImagePath = os.path.join(os.getcwd(), 'qrcode.jpg')

tip = 0
uuid = ''

base_uri = ''
redirect_uri = ''
push_uri = ''

skey = ''
wxsid = ''
wxuin = ''
pass_ticket = ''
deviceId = 'e000000000000000'

BaseRequest = {}

ContactList = []
My = []
SyncKey = []

try:
    xrange
    range = xrange
except:
    # python 3
    pass


def responseState(func, BaseResponse):
    ErrMsg = BaseResponse['ErrMsg']
    Ret = BaseResponse['Ret']
    if DEBUG or Ret != 0:
        print('func: %s, Ret: %d, ErrMsg: %s' % (func, Ret, ErrMsg))

    if Ret != 0:
        return False

    return True


def getRequest(url, data=None):
    try:
        # data = data.encode('utf-8')
    	# data = urlencode(data)
    	# print (data)
    	pass
    except:
        pass
    finally:
        return wdf_urllib.Request(url=url, data=data)


def getUUID():
    global uuid

    url = 'https://login.weixin.qq.com/jslogin'
    params = {
        'appid': 'wx782c26e4c19acffb',
        'fun': 'new',
        'lang': 'zh_CN',
        '_': int(time.time()),
    }

    request = getRequest(url=url, data=urlencode(params))
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')

    # print(data)

    # window.QRLogin.code = 200; window.QRLogin.uuid = "oZwt_bFfRg==";
    regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
    pm = re.search(regx, data)

    code = pm.group(1)
    uuid = pm.group(2)

    if code == '200':
        return True

    return False


def showQRImage():
    global tip

    url = 'https://login.weixin.qq.com/qrcode/' + uuid
    params = {
        't': 'webwx',
        '_': int(time.time()),
    }

    request = getRequest(url=url, data=urlencode(params))
    response = wdf_urllib.urlopen(request)

    tip = 1

    f = open(QRImagePath, 'wb')
    f.write(response.read())
    f.close()

    if sys.platform.find('darwin') >= 0:
        subprocess.call(['open', QRImagePath])
    elif sys.platform.find('linux') >= 0:
        subprocess.call(['xdg-open', QRImagePath])
    else:
        os.startfile(QRImagePath)

    print('请使用微信扫描二维码以登录')


def waitForLogin():
    global tip, base_uri, redirect_uri, push_uri

    url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (
        tip, uuid, int(time.time()))

    request = getRequest(url=url)
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')

    # print(data)

    # window.code=500;
    regx = r'window.code=(\d+);'
    pm = re.search(regx, data)

    code = pm.group(1)

    if code == '201':  # 已扫描
        print('成功扫描,请在手机上点击确认以登录')
        tip = 0
    elif code == '200':  # 已登录
        print('正在登录...')
        regx = r'window.redirect_uri="(\S+?)";'
        pm = re.search(regx, data)
        redirect_uri = pm.group(1) + '&fun=new'
        base_uri = redirect_uri[:redirect_uri.rfind('/')]

        # push_uri与base_uri对应关系(排名分先后)(就是这么奇葩..)
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

        # closeQRImage
        if sys.platform.find('darwin') >= 0:  # for OSX with Preview
            os.system("osascript -e 'quit app \"Preview\"'")
    elif code == '408':  # 超时
        pass
    # elif code == '400' or code == '500':

    return code


def login():
    global skey, wxsid, wxuin, pass_ticket, BaseRequest

    request = getRequest(url=redirect_uri)
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')

    # print(data)

    doc = xml.dom.minidom.parseString(data)
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

    # print('skey: %s, wxsid: %s, wxuin: %s, pass_ticket: %s' % (skey, wxsid,
    # wxuin, pass_ticket))

    if not all((skey, wxsid, wxuin, pass_ticket)):
        return False

    BaseRequest = {
        'Uin': int(wxuin),
        'Sid': wxsid,
        'Skey': skey,
        'DeviceID': deviceId,
    }

    return True


def webwxinit():

    url = base_uri + \
        '/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (
            pass_ticket, skey, int(time.time()))
    params = {
        'BaseRequest': BaseRequest
    }

    request = getRequest(url=url, data=json.dumps(params))
    request.add_header('ContentType', 'application/json; charset=UTF-8')
    response = wdf_urllib.urlopen(request)
    data = response.read()

    if DEBUG:
        f = open(os.path.join(os.getcwd(), 'webwxinit.json'), 'wb')
        f.write(data)
        f.close()

    data = data.decode('utf-8', 'replace')

    # print(data)

    global ContactList, My, SyncKey
    dic = json.loads(data)
    ContactList = dic['ContactList']
    My = dic['User']
    SyncKey = dic['SyncKey']

    global interested_user
    for user in ContactList:
    	if user['NickName'] in interested_user:
    		interested_user[user['NickName']] = user['UserName']
    		user_interested[user['UserName']] = user['NickName']
    		if DEBUG:
    			print (interested_user)


    state = responseState('webwxinit', dic['BaseResponse'])
    return state



import requests
# send msg to weixin
def webwxsendmsg(content, user):

	url = base_uri + \
	'/webwxsendmsg?pass_ticket=%s' % (pass_ticket)

	if DEBUG:
		print (interested_user)

	#content = u"[lyy 养的机器人]： 我是钦定的，蛤铪。..............\n"
	msg = {
		'ClientMsgId' : 14533331712090640,
		'Content' : content.encode('utf-8'),
		'FromUserName' : My['UserName'].encode('utf-8') ,
		'LocalID' : 14533331712090640 ,
		'ToUserName' : user.encode('utf-8') ,
		'Type' : 1
	}
	_BaseRequest = {
        'Uin': int(wxuin),
        'Sid': wxsid.encode('utf-8'),
        'Skey': skey.encode('utf-8'),
        'DeviceID': deviceId.encode('utf-8'),
    }
	params = {
		'BaseRequest' : _BaseRequest,
		'Msg' : msg
	}

	
	data = json.dumps(params, ensure_ascii=False)
	if DEBUG:
		print (data)
		print 
		print (type(data))
		print
	# request = getRequest(url=url, data = data)
	# # print (request)
	# response = wdf_urllib.urlopen(request)
	# data = response.read()
	data = requests.post(url, data)



	if DEBUG:
		#print (json.dumps(params))
		#print (data)
		pass

	

def webwxgetcontact():

    url = base_uri + \
        '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (
            pass_ticket, skey, int(time.time()))

    request = getRequest(url=url)
    request.add_header('ContentType', 'application/json; charset=UTF-8')
    response = wdf_urllib.urlopen(request)
    data = response.read()

    if DEBUG:
        f = open(os.path.join(os.getcwd(), 'webwxgetcontact.json'), 'wb')
        f.write(data)
        f.close()

    # print(data)
    data = data.decode('utf-8', 'replace')

    dic = json.loads(data)
    MemberList = dic['MemberList']

    # 倒序遍历,不然删除的时候出问题..
    SpecialUsers = ["newsapp", "fmessage", "filehelper", "weibo", "qqmail", "tmessage", "qmessage", "qqsync", "floatbottle", "lbsapp", "shakeapp", "medianote", "qqfriend", "readerapp", "blogapp", "facebookapp", "masssendapp",
                    "meishiapp", "feedsapp", "voip", "blogappweixin", "weixin", "brandsessionholder", "weixinreminder", "wxid_novlwrv3lqwv11", "gh_22b87fa7cb3c", "officialaccounts", "notification_messages", "wxitil", "userexperience_alarm"]
    for i in range(len(MemberList) - 1, -1, -1):
        Member = MemberList[i]
        if Member['VerifyFlag'] & 8 != 0:  # 公众号/服务号
            MemberList.remove(Member)
        elif Member['UserName'] in SpecialUsers:  # 特殊账号
            MemberList.remove(Member)
        elif Member['UserName'].find('@@') != -1:  # 群聊
            # MemberList.remove(Member)
            pass
        elif Member['UserName'] == My['UserName']:  # 自己
            MemberList.remove(Member)

    return MemberList





def syncKey():
    SyncKeyItems = ['%s_%s' % (item['Key'], item['Val'])
                    for item in SyncKey['List']]
    SyncKeyStr = '|'.join(SyncKeyItems)
    return SyncKeyStr


def syncCheck():
    url = push_uri + '/synccheck?'
    params = {
        'skey': BaseRequest['Skey'],
        'sid': BaseRequest['Sid'],
        'uin': BaseRequest['Uin'],
        'deviceId': BaseRequest['DeviceID'],
        'synckey': syncKey(),
        'r': int(time.time()),
    }

    request = getRequest(url=url + urlencode(params))
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')

    # print(data)

    # window.synccheck={retcode:"0",selector:"2"}
    regx = r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}'
    pm = re.search(regx, data)

    retcode = pm.group(1)
    selector = pm.group(2)

    return selector


def webwxsync():
    global SyncKey, contents_to_response

    url = base_uri + '/webwxsync?lang=zh_CN&skey=%s&sid=%s&pass_ticket=%s' % (
        BaseRequest['Skey'], BaseRequest['Sid'], quote_plus(pass_ticket))
    params = {
        'BaseRequest': BaseRequest,
        'SyncKey': SyncKey,
        'rr': ~int(time.time()),
    }

    request = getRequest(url=url, data=json.dumps(params))
    request.add_header('ContentType', 'application/json; charset=UTF-8')
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')

    # print(data)

    dic = json.loads(data)
    SyncKey = dic['SyncKey']

    
    for msg in dic['AddMsgList']:
        if DEBUG:
            print (msg['ToUserName'])
        if (msg['ToUserName'] in user_interested): # and (msg['FromUserName'] is not My['UserName']):
            if msg['MsgType'] == 1:
                contents_to_response[msg['Content']] = msg['ToUserName']
        if (msg['FromUserName'] in user_interested):
            if msg['MsgType'] == 1:
                content_tmp = msg['Content']
                content_tmp = content_tmp[71:]
                contents_to_response[content_tmp] = msg['FromUserName']


    state = responseState('webwxsync', dic['BaseResponse'])
    return state


def send_msg():
	global contents_to_response

	tuling_url = 'http://www.tuling123.com/openapi/api?key=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx&info='
	for content, user in contents_to_response.iteritems():
		tuling_url = tuling_url + content
		try:
			data = requests.get(tuling_url)
			data = json.loads(data.text)
			text = data['text']
		except:
			text = u'网络异常。。。。。'
		webwxsendmsg(u'钦定的 lyy robot: ' + text, user)
		time.sleep(0.2)

	contents_to_response = {}

def heartBeatLoop():
    while True:
        try:
            selector = syncCheck()
            time.sleep(0.1)
        except:
            print ('sync error')
            pass
        if selector != '0':
            webwxsync()
            send_msg()
            time.sleep(0.2)
        time.sleep(1)


def main():

    try:
        ssl._create_default_https_context = ssl._create_unverified_context

        opener = wdf_urllib.build_opener(
            wdf_urllib.HTTPCookieProcessor(CookieJar()))
        opener.addheaders = [
            ('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.125 Safari/537.36')]
        wdf_urllib.install_opener(opener)
    except:
        pass

    if not getUUID():
        print('获取uuid失败')
        return

    print('正在获取二维码图片...')
    showQRImage()
    time.sleep(1)

    while waitForLogin() != '200':
        pass

    os.remove(QRImagePath)

    if not login():
        print('登录失败')
        return

    if not webwxinit():
        print('初始化失败')
        return

    MemberList = webwxgetcontact()

    print('开启心跳线程')
    thread.start_new_thread(heartBeatLoop, ())

    MemberCount = len(MemberList)
    print('通讯录共%s位好友' % MemberCount)

    try:
    	while True:
    		time.sleep(1)
    except KeyboardInterrupt:
    	print ('bye bye')





class UnicodeStreamFilter:

    def __init__(self, target):
        self.target = target
        self.encoding = 'utf-8'
        self.errors = 'replace'
        self.encode_to = self.target.encoding

    def write(self, s):
        if type(s) == str:
            s = s.decode('utf-8')
        s = s.encode(self.encode_to, self.errors).decode(self.encode_to)
        self.target.write(s)

if sys.stdout.encoding == 'cp936':
    sys.stdout = UnicodeStreamFilter(sys.stdout)

if __name__ == '__main__':

    
    main()
    
