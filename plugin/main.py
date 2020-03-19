# -*- coding: utf-8 -*-
from flask import Flask, request
import argparse
import time
from messages_handle import MessagesHandle
from mqtt_handle import MqttHandle
from udpServer import UdpServer
import shutil 
import os
import traceback
# 使用多进程，进程队列
# from multiprocessing import Process, Queue
# messages_queue = Queue()

# 使用多线程，线程队列
import queue, threading

messages_queue = queue.Queue()
app = Flask(__name__)

 
@app.route('/webHook', methods=['GET', 'POST'])
def webHook():
    obj = request.get_json(force=True)
    print('[webHook] :{0}'.format(obj))
    messages_queue.put(obj)
    return "200"

   
def messages_handle_thread(redis_host, redis_password, mqtt_host, mqtt_web_port, messages_queue,topic_resume):
    messagesHandle = MessagesHandle(redis_host, redis_password, mqtt_host, mqtt_web_port) 
    messagesHandle.consumer_queue(messages_queue,topic_resume)


def mqtt_handle_thread(mqtt_host, mqtt_port):
    mqttHandle = MqttHandle(mqtt_host, mqtt_port) 
    mqttHandle.connect()

    
def udp_server_thread(udp_host, udp_port, messages_queue):
    updServerHandle = UdpServer(udp_host, udp_port) 
    updServerHandle.handle(messages_queue)


def copy_emqx_files():
    try:
        if not os.path.exists('/home/plugin/logs'):
            os.makedirs('/home/plugin/logs') 
            
        filepath = '/home/plugin/complete.tag'
        if not os.path.exists(filepath):
            shutil.copy('/home/plugin/emqx_web_hook.beam', '/opt/emqx/lib/emqx_web_hook-3.2.7/ebin/emqx_web_hook.beam')
            shutil.copy('/home/plugin/emqx_app.beam', '/opt/emqx/lib/emqx-3.2.7/ebin/emqx_app.beam')
            shutil.copy('/home/plugin/emqx_listeners.beam', '/opt/emqx/lib/emqx-3.2.7/ebin/emqx_listeners.beam')
            shutil.copy('/home/plugin/emqx_mgmt_api_pubsub.beam', '/opt/emqx/lib/emqx_management-3.2.7/ebin/emqx_mgmt_api_pubsub.beam')
            shutil.copy('/home/plugin/emqx_web_hook.conf', '/opt/emqx/etc/plugins/emqx_web_hook.conf')
            shutil.copy('/home/plugin/loaded_plugins', '/opt/emqx/data/loaded_plugins')
            fd = open(filepath, mode="w", encoding="utf-8")
            fd.close()
            print('completed emqx files copy')
    except:
        traceback.print_exc()        

     
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='emqx 持久化恢复服务')
   
    parser.add_argument('-redis_host', '--redis_host', default='127.0.0.1', help='目标redis地址')
    parser.add_argument('-redis_password', '--redis_password', default='', help='目标redis密码')
    
    # 配置开启的Web、UDP服务的监听地址和端口
    parser.add_argument('-mqtt_host', '--mqtt_host', default='127.0.0.1', help='目标mqtt地址')
    parser.add_argument('-mqtt_port', '--mqtt_port', default=11883, help='目标mqtt端口')
    parser.add_argument('-mqtt_web_port', '--mqtt_web_port', default=18083, help='目标mqtt Web服务的端口')
    parser.add_argument('-main_host', '--main_host', default='127.0.0.1', help='')
    parser.add_argument('-web_port', '--web_port', default=8881, help='')
    parser.add_argument('-udp_port', '--udp_port', default=4000, help='')
    args = parser.parse_args()
    
    # copy_emqx_files()
    
    print('[main] :持久化插件各模块开始加载')  
    
    try: 
        env_dist = os.environ
        redis_host = env_dist.get("redis_host", args.redis_host)
        redis_password = env_dist.get("redis_password", args.redis_password)
        # 默认
        topic_resume = env_dist.get("topic_persist", "false")
        print('[main] :topic_persist={0}'.format(topic_resume))  
        if topic_resume == "false":
            topic_resume = False
        else:
            topic_resume = True     
    except:
        traceback.print_exc()    
    
    print('[main] :redis_host={0}'.format(redis_host))  
    print('[main] :redis_password={0}'.format(redis_password))  
    print('[main] :topic_persist={0}'.format(topic_resume))  
    
    # 开启进程
    # p1 = Process(target=handle, args=(args.redis_host, messages_queue))
    # p1.start()
         
    # 开启线程 
    t = threading.Thread(target=messages_handle_thread, args=(redis_host, redis_password, args.mqtt_host, args.mqtt_web_port, messages_queue,topic_resume))
    t.start()
    
    t2 = threading.Thread(target=mqtt_handle_thread, args=(args.mqtt_host, args.mqtt_port))
    t2.start()
    
    t3 = threading.Thread(target=udp_server_thread, args=(args.main_host, args.udp_port, messages_queue))
    t3.start()

    print('[main] :持久化插件各模块加载完成')
    app.run(host=args.main_host, port=args.web_port)
