# 微信聊天机器人

这是一个基于微信网页版接口的，个人账号聊天机器人。使用 Python 实现。不同于微信公众号和订阅号，个人账号腾讯并没有提供 API 接口，所以只能模拟微信网页版的协议来做。

由于使用未公开通信协议，故不能保证向后兼容性。

## 简单说明

* wechat-asyncio 是异步实现的。需要 Python 3.5。
* wechat-draft 是很早的第一个可用的版本。只有两个线程。只需要 > Python 3。

## Changelog

### 2016.2.4

一次大的改动，改了又改，岂止于改。

改成了基于 asyncio/aiohttp 的异步框架。现在只有四个任务：sync, sendmsg, updategroupinfo, msgloop。任务同步使用 Queue。
也顺便分离了一些逻辑，共三大块：同步与发送，消息处理，机器人对话机制。

错误处理还没有完善，但费解的是登陆失败率好高。同步和发送失败率还好。
联系人更新还是以前逻辑，需要改成实时更新的。

### 2016.1.24

sync 改为定时。之前是 sync -> sendmsg -> sync ....

定时之后，sync 时间固定，与 sendmsg 分开。收到的消息用 lock+deque 同步。
群消息回复改为 '@nickname xxxxx'，在回复时找不到用户就会触发一次 webwxbatchgetcontact，在另一个线程中。
目前缺点是，第一次回复找不到用户就没有 @ 了，从第二次开始。

### 2016.1.23

wechat-robot.py 改用 Python3。原来的 urllib2/urllib 全部改为了 requests。

webwxgetcontact/websync 那块需要 login() 阶段获取的 cookie。

用 requests 有个小坑，在 websync 阶段获取的 r.text 会被认为 r.encoding = 'ISO-8859-1'。需要手动改为 r.encoding = 'utf-8'。

### 2016.1.22

sync 部分会出错，连接错误。不清楚这部分如果捕获异常后再次发送会不会有问题，因为 synckey 每次 sync 都会改变，再次 sync 不知腾讯是否接受。

别人发送的 content 我是直接截取 [71:]，实测有问题。

以上需要更多测试。

另外可以尝试 sync 和 sendmsg 并行。


## 参考

前期参考了 [查看被删的微信好友](https://github.com/0x5e/wechat-deleted-friends)。

也参考了 [Nodejs 版的微信聊天机器人](https://github.com/HalfdogStudio/wechat-user-bot)。