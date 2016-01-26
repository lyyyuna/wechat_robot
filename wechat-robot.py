# coding=utf-8

import os
import requests
import simplejson as json
import time
import re
import xml.dom.minidom
# from collections import deque
import queue
import html

import threading
# lock = threading.Lock()

DEBUG = False
LOG = True

deviceId = 'e000000000000000' 
g_info = {}
g_info['tip'] = 0
g_queue = queue.Queue()# []

import config
apikey = config.apikey

def getUUID():
    global g_info

    url = 'https://login.weixin.qq.com/jslogin'
    params = {
        'appid': 'wx782c26e4c19acffb',
        'fun': 'new',
        'lang': 'zh_CN',
        '_': int(time.time()),   
    }

    r = requests.post(url, params)
    if DEBUG:
        print (r.text)
    text = r.text
    regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
    pm = re.search(regx, text)

    code = pm.group(1)
    uuid = pm.group(2)

    g_info['uuid'] = uuid
    if code == '200':
        return True 

    return False

def showQRImage():
    global g_info

    uuid = g_info['uuid']
    url = 'https://login.weixin.qq.com/qrcode/' + uuid
    params = {
        't': 'webwx',
        '_': int(time.time()),
    }

    r = requests.post(url, params)
    g_info['tip'] = 1

    with open('qrcode.jpg', 'wb') as fd:
        for chunk in r.iter_content(512):
            fd.write(chunk)

    print ('请扫描二维码。。。')

def waitForLogin():
    global g_info

    tip = g_info['tip']
    uuid = g_info['uuid']
    url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (
        tip, uuid, int(time.time()))  

    r = requests.get(url)
    text = r.text
    regx = r'window.code=(\d+);'
    pm = re.search(regx, text)
    
    code = pm.group(1)
    if code == '201':
        print ('成功扫描,请在手机上点击确认以登录')
        g_info['tip'] = 0
    elif code == '200':
        print ('正在登录。。。')
        regx = r'window.redirect_uri="(\S+?)";'
        pm = re.search(regx, text)
        redirect_uri = pm.group(1) + '&fun=new'
        g_info['redirect_uri']  = redirect_uri
        base_uri = redirect_uri[:redirect_uri.rfind('/')]
        g_info['base_uri'] = base_uri

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
        g_info['push_uri'] = push_uri

    elif code == '408':
        pass

    return code

def login():
    global g_info

    redirect_uri = g_info['redirect_uri']
    r = requests.get(redirect_uri)


    g_info['cookies'] = r.cookies

    doc = xml.dom.minidom.parseString(r.text)
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
        'DeviceID': deviceId,
    }

    g_info['skey'] = skey
    g_info['wxsid'] = wxsid
    g_info['wxuin'] = wxuin
    g_info['pass_ticket'] = pass_ticket
    g_info['BaseRequest'] = BaseRequest

    if DEBUG:
        print (skey, wxsid, wxuin)

    return True



def responseState(func, BaseResponse):
    ErrMsg = BaseResponse['ErrMsg']
    Ret = BaseResponse['Ret']
    if DEBUG:
        print('func: %s, Ret: %d, ErrMsg: %s' % (func, Ret, ErrMsg))

    if Ret != 0:
        return False

    return True

def webwxinit():
    global g_info

    base_uri = g_info['base_uri']
    pass_ticket = g_info['pass_ticket']
    skey = g_info['skey']
    BaseRequest = g_info['BaseRequest']

    url = base_uri + \
        '/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (
            pass_ticket, skey, int(time.time()))
    params = {
        'BaseRequest': BaseRequest
    }

    r = requests.post(url, json.dumps(params))
    text = r.text

    if DEBUG:
        with open('webwxinit.json', 'wb') as fd:
            for chunk in r.iter_content(512):
                fd.write(chunk)

    dic = json.loads(text)
    ContactList = dic['ContactList']
    My = dic['User']
    SyncKey = dic['SyncKey']

    g_info['ContactList'] = ContactList
    g_info['My'] = My 
    g_info['SyncKey'] = SyncKey

    state = responseState('webwxinit', dic['BaseResponse'])
    return state

def webwxgetcontact():
    global g_info

    base_uri = g_info['base_uri']
    pass_ticket = g_info['pass_ticket']
    skey = g_info['skey']

    url = base_uri + \
        '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (
            pass_ticket, skey, int(time.time()))
    headers = {'Content-Type':'application/json; charset=UTF-8'}
    r = requests.get(url,headers=headers,cookies=g_info['cookies'])
    text = r.text

    if DEBUG:
        with open('webwxgetcontact.json', 'wb') as fd:
            for chunk in r.iter_content(512):
                fd.write(chunk)

    
    dic = json.loads(text, 'utf-8')
    MemberList = dic['MemberList']
    SpecialUsers = ["newsapp", "fmessage", "filehelper", "weibo", "qqmail", "tmessage", "qmessage", "qqsync", "floatbottle", "lbsapp", "shakeapp", "medianote", "qqfriend", "readerapp", "blogapp", "facebookapp", "masssendapp",
                    "meishiapp", "feedsapp", "voip", "blogappweixin", "weixin", "brandsessionholder", "weixinreminder", "wxid_novlwrv3lqwv11", "gh_22b87fa7cb3c", "officialaccounts", "notification_messages", "wxitil", "userexperience_alarm"]
    for i in range(len(MemberList) - 1, -1, -1):
        Member = MemberList[i]
        if Member['VerifyFlag'] & 8 != 0:  # 公众号/服务号
            MemberList.remove(Member)
        elif Member['UserName'] in SpecialUsers:  # 特殊账号
            MemberList.remove(Member)   
    
    _MemberList = {}
    for user in MemberList:
        _MemberList[user['UserName']] = user['NickName']

    g_info['MemberList'] = _MemberList


def syncKey():
    global g_info

    SyncKey = g_info['SyncKey']
    SyncKeyItems = ['%s_%s' % (item['Key'], item['Val'])
                    for item in SyncKey['List']]
    SyncKeyStr = '|'.join(SyncKeyItems)
    return SyncKeyStr

def syncCheck():
    global g_info

    push_uri = g_info['push_uri']
    BaseRequest = g_info['BaseRequest']
    url = push_uri + '/synccheck?'
    params = {
        'skey': BaseRequest['Skey'],
        'sid': BaseRequest['Sid'],
        'uin': BaseRequest['Uin'],
        'deviceId': BaseRequest['DeviceID'],
        'synckey': syncKey(),
        'r': int(time.time()),
    }

    r = requests.get(url, params=params, cookies=g_info['cookies'], timeout=300)
    text = r.text
    regx = r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}'
    pm = re.search(regx, text)    

    retcode = pm.group(1)
    selector = pm.group(2)

    if DEBUG or LOG:
        print (text)

    return (retcode, selector)


def webwxsync():
    global g_info

    base_uri = g_info['base_uri']
    BaseRequest = g_info['BaseRequest']
    SyncKey = g_info['SyncKey']
    pass_ticket = g_info['pass_ticket']
    # url = base_uri + '/webwxsync?lang=zh_CN&skey=%s&sid=%s&pass_ticket=%s' % (
    #     BaseRequest['Skey'], BaseRequest['Sid'], quote_plus(pass_ticket))
    url = base_uri + '/webwxsync?'
    params = {
        'BaseRequest': BaseRequest,
        'SyncKey': SyncKey,
        'rr': ~int(time.time()),
    } 
    url_params = {
        # 'lang' : 'zh_CN' ,
        'skey' : BaseRequest['Skey'] ,
        'pass_ticket' : pass_ticket ,
        'sid' : BaseRequest['Sid']
    }
    headers = {
        'ContentType': 'application/json; charset=UTF-8'
    }
    r = requests.post(url, params=url_params, data=json.dumps(params), headers = headers, cookies=g_info['cookies'])

    # if DEBUG:
    #     global i 
    #     i = i + 1
    #     with open('sync' +  str(i) + '.json', 'wb') as fd:
    #         for chunk in r.iter_content(512):
    #             fd.write(chunk)
    r.encoding = 'utf-8'
    dic = json.loads(r.text)
    # print (dic)
    # 更新 synckey
    g_info['SyncKey'] = dic['SyncKey']
    state = responseState('webwxsync', dic['BaseResponse'])

    msg_list = dic['AddMsgList']
    if DEBUG:
        print (msg_list)

    return (state, msg_list)


def getMsg(msg_list):
    global g_info, g_queue

    My = g_info['My']

    for msg in msg_list:
        if msg['MsgType'] != 1:
            continue
        if msg['FromUserName'] == My['UserName']:
            continue
        if msg['ToUserName'] == My['UserName']:
            response = {}
            content = msg['Content']

            # 群消息中 :<br/> 之前是 UserName
            if content.find(':<br/>') != -1:
                fromsomeone = content[:content.find(':<br/>')]
            else:
                fromsomeone = ''

            fromsomeone_NickName = ''
            if msg['FromUserName'].find('@@') != -1:
                # 如果是来自群，那就试着去 g_info[] 对应的群中找群成员列表
                groupName = msg['FromUserName']
                # 群还没有记录
                if groupName not in g_info:
                    g_info['Group_UserName_Req'] = msg['FromUserName']
                # 在群列表中有了，因为可能群成员会变化，所以要再次找一遍
                elif fromsomeone in g_info[groupName]:
                    fromsomeone_NickName = g_info[groupName][fromsomeone]
                    fromsomeone_NickName = '@' + fromsomeone_NickName + ' '
                # 找不到，所以置标志位，会在另一个群中触发寻找行为
                else:
                    g_info['Group_UserName_Req'] = msg['FromUserName']
            else:
                fromsomeone_NickName = ''

            response['fromsomeone'] = fromsomeone_NickName
            response['Content'] = content[content.find('>')+1:]
            response['FromUserName'] = msg['FromUserName']

            # g_info['Group_UserName_Req'] = response['FromUserName']

            # 不停地塞新消息
            # lock.acquire()
            # try:
            #     g_queue.append(response)
            # finally:
            #     lock.release()
            # print (response['Content'])

            # test
            if g_queue.qsize() > 5:
                g_queue.get()
                g_queue.get()
            g_queue.put(response)

    if LOG:
        print ('getmsg queue: %s' % g_queue.qsize())


def webwxsendmsg(content, user):
    global g_info

    base_uri = g_info['base_uri']
    pass_ticket = g_info['pass_ticket']
    BaseRequest = g_info['BaseRequest']
    My = g_info['My']

    wxuin = BaseRequest['Uin']
    wxsid = BaseRequest['Sid']
    skey = BaseRequest['Skey']
    deviceId = BaseRequest['DeviceID']

    url = base_uri + \
    '/webwxsendmsg?pass_ticket=%s' % (pass_ticket)

    msgid = int(time.time()*10000000)
    msg = {
        'ClientMsgId' : msgid ,
        'Content' : content,
        'FromUserName' : My['UserName'] ,
        'LocalID' : msgid ,
        'ToUserName' : user,
        'Type' : 1
    }
    params = {
        'BaseRequest' : BaseRequest,
        'Msg' : msg
    }
    data = json.dumps(params, ensure_ascii=False)
    # print (data)
    data = data.encode('utf-8')
    r = requests.post(url, data=data, cookies=g_info['cookies'])


def sendMsg():
    global g_info, g_queue

    MemberList = g_info['MemberList']
    tuling_url = 'http://www.tuling123.com/openapi/api?key=' + apikey + '&info='

    time.sleep(1)
    if LOG:
        print ('sendmsg queue: %s' % g_queue.qsize())
    while g_queue.empty() is False:
        # lock.acquire()
        # try:
        #     response = g_queue.popleft()
        # finally:
        #     lock.release()
        response = g_queue.get()

        content = response['Content']
        from_user = response['FromUserName']
        AT = response['fromsomeone']
        tuling_url = tuling_url + content
        try:
            data = requests.get(tuling_url)
            data = json.loads(data.text)
            text = data['text']
        except:
            text = '网络异常。。。。。'          
        webwxsendmsg(AT + text, from_user)
        time.sleep(1)

        if LOG:
            print
            print ('机器人收到回复：%s' % content)
            print ('机器人的回复: %s' % text)
            print




def webwxbatchgetcontact(UserName):
    global g_info

    base_uri = g_info['base_uri']
    pass_ticket = g_info['pass_ticket']
    BaseRequest = g_info['BaseRequest']

    url = base_uri + '/webwxbatchgetcontact?'


    List = [{
        'ChatRoomId' : '',
        'UserName' : UserName
    }]
    
    post_params = {
        'BaseRequest': BaseRequest ,
        'Count' : 1 ,
        'List' : List
    } 
    url_params = {
        'lang' : 'zh_CN' ,
        'type' : 'ex' ,
        'pass_ticket' : pass_ticket ,
        'r' : int(time.time())
    }

    headers = {
        'ContentType': 'application/json; charset=UTF-8'
    }
    r = requests.post(url, params=url_params, data=json.dumps(post_params), headers = headers, cookies=g_info['cookies'])

    r.encoding = 'utf-8'
    dic = json.loads(r.text)    


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

            if DEBUG:
                print (member['NickName'])

    # 整群的成员列表消息记录
    g_info[UserName] = GroupMapUsers




def getgroupinfo():
    global g_info

    if 'Group_UserName_Req' not in g_info:
        return
    if g_info['Group_UserName_Req'] == '0':
        return

    Group_UserName = g_info['Group_UserName_Req']
    webwxbatchgetcontact(Group_UserName)

    # 这个变量表示一次 获取群成员列表 请求。请求完毕置空
    g_info['Group_UserName_Req'] = '0'

    time.sleep(0.5)


    
def heartBeatLoop():
    while True:
        retcode, selector = syncCheck()
        if retcode != '0':
            print ('sync 失败。。。')
        if selector == '2':
            state, msg_list = webwxsync()
            getMsg(msg_list)
            getgroupinfo()

        time.sleep(1)



def main():
    global g_info

    if not getUUID():
        print ('获取 uuid 失败')
        return
    print ('获取二维码图片中。。。')
    showQRImage()
    time.sleep(1)

    while waitForLogin() != '200':
        pass

    if not login():
        print ('登陆失败')
        return

    if not webwxinit():
        print ('初始化失败')
        return

    print ('登陆')

    print ('获取好友。。。。')
    webwxgetcontact()

    print ('开始心跳 噗咚噗通')
    t1 = threading.Thread(target=heartBeatLoop)
    t1.start()

    MemberCount = len(g_info['MemberList'])
    print ('这位同志啊，你有 %s 个好友' % MemberCount)

    try:
        while True:
            sendMsg()
            time.sleep(1.5)
    except KeyboardInterrupt:
        print ('bye bye ~')

if __name__ == '__main__':
    main()