# HHU_YjsScoreMonitor
## 简介
自动登陆[河海大学研究生教学管理系统](http://yjss.hhu.edu.cn/gmis/home/stulogin)查询成绩，并通过[Server酱](http://sc.ftqq.com/)推送至微信微信;本系统采用多线程机制，可以查询多位用户成绩，并设置守护线程自动重启挂掉的进程。

## 使用教程
### 1.Selenium 安装 
使用Chrome Driver,[安装教程](https://www.cnblogs.com/lfri/p/10542797.html)
### 2.Pytessarct 安装
[安装教程](https://www.cnblogs.com/linyouyi/p/11427443.html)
### 3.Server酱 注册
[Server酱](http://sc.ftqq.com/)

## 技术详解
登陆部分使用Selenium模拟登陆，并调用tessarct识别验证码，登陆成功后获取Cookie;查询部分使用抓包获取的API接口。
