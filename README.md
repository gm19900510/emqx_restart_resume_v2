# emqx_restart_resume
> 用于emqx开源版 服务重启后恢复原订阅主题和持久化数据

## 问题

 1. 开源版emq在服务重启后原订阅的主题会清空，在客户端保持原clientId，保持原session未重新订阅时，接不到服务器转发的消息。
 2. 开源版持久化会模型保存主题下的最后一条消息，在重启后也会被清空。

## 解决方案
利用EMQ X Web Hook插件将时间发送到指定的请求，利用Redis 和 EMQ X自带的Web API进行扩展，可查看博文[了解详情](https://blog.csdn.net/ctwy291314/article/details/103820919)

- 基于emqx 3.2.7版本改造
- message_publish传输更改为采用UDP方式
- client_connected、session_subscribed、session_unsubscribed采用HTTP方式
- EMQX服务启动后内部11883端口用于消息持久化恢复，在持久化消息恢复完成后开启1883端口监听
- 在clear_session=False 的客户端连接成功后，进行已订阅主题查询及未订阅主题恢复
- redis使用源码编译，采用RDB和AOP并行持久化

## 安装说明
- 生成镜像
cd emqx_restart_resume
docker build -t ubuntu18.04:emqx_restart_resume .
  > 说明：
  > ubuntu18.04表示镜像名称，emqx_restart_resume表示标签
- 启动容器
docker run -itd --name test2 -p 1883:1883 -p 8083:8083 -p 8883:8883 -p 8084:8084 -p 18083:18083 -p 8123:8123  -p 6379:6379 --log-opt max-size=100m --log-opt max-file=3 --restart=unless-stopped -e topic_persist="true" ubuntu18.04:emqx_restart_resume
  > 说明：
  > -e topic_persist="true"表示开启订阅主题持久化恢复
  > -e redis_host="192.168.104.251" -e redis_password="redis"表示使用外部redis，默认采用容器内部redis
- 测试
python main.py
- 镜像导出
sudo docker save > /home/hylink/ubuntu18.04-emqx3.2.7.tar ubuntu18.04:emqx_restart_resume
- 镜像加载
docker load < /home/hylink/ubuntu18.04-emqx3.2.7.tar


## 资料
- https://github.com/emqx/emqx-web-hook/
- https://github.com/emqx/emqx-enterprise-docs-cn/blob/master/rest.rst

## Git
https://github.com/gm19900510/emqx_restart_resume_v2







