# 微信聊天机器人

这是一个基于微信网页版接口的，个人账号聊天机器人。使用 Python 实现。

不同于微信公众号和订阅号，个人账号腾讯并没有提供 API 接口，所以只能模拟微信网页版的协议来做。

由于使用未公开通信协议，故不能保证向后兼容性。

## 参考

login 和 sync 的逻辑和代码参考并复用了 [查看被删的微信好友](https://github.com/0x5e/wechat-deleted-friends) 。

也参考了 [Nodejs 版的机器人](https://github.com/HalfdogStudio/wechat-user-bot)

自己实现了获取群组名单，发送消息等部分。

## 问题

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
