# 微信聊天机器人 - 个人账号版

这是一个基于微信网页版接口的，个人账号聊天机器人。

不同于微信公众号和订阅号，个人账号腾讯并没有提供 API 接口，所以只能模拟微信网页版的协议来做。由于使用未公开通信协议，故不能保证向后兼容性。

* wechat-asyncio 是异步实现的。需要 Python 3.5。
* wechat-draft 是很早的第一个可用的版本。只有两个线程。只需要 > Python 3。

## 简单说明

### 依赖

申请一枚图灵机器人 API，新建 auth.py，并写入 

    apikey = 'xxxxxxxxxxx'

* pip3 install aiohttp

### 快速开始

目前使用起来还不友好，且登陆有一定失败率。

    (terminal 1) python3 main.py 

运行后会在当前文件夹内下载二维码，根据终端提示做即可。

1. 若 10s 内二维码下载失败则重来。
2. 若 wx.log 提示 sync 失败则重来。

### 参数调整

在 config.py 中可以对各个时间间隔做调整。

## Changelog

### 2016.2.4

改成了基于 asyncio/aiohttp 的异步框架。现在只有 5 个任务：sync, sendmsg, updategroupinfo, msgloop, monitor。

### 2016.1.23

wechat-robot.py 改用 Python3。原来的 urllib2/urllib 全部改为了 requests。


## 参考

前期参考了 [查看被删的微信好友](https://github.com/0x5e/wechat-deleted-friends)。

也参考了 [Nodejs 版的微信聊天机器人](https://github.com/HalfdogStudio/wechat-user-bot)。
