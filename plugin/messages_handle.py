# -*- coding: utf-8 -*-
import redis
import requests
import json
import time
import traceback
from redis.exceptions import ConnectionError 
host = '127.0.0.1'
port = 18083


# 创建订阅
def subscribe(client_id, topic, qos):     
    postdata = {
      "topic": topic,
      "qos": qos,
      "client_id": client_id
    }
    print('[subscribe] :[需重新订阅主题] {0}'.format(postdata))
    postdata = json.dumps(postdata) 
    r = requests.post('http://' + host + ':' + str(port) + '/api/v3/mqtt/subscribe', data=postdata, auth=('admin', 'public'))
    print('[subscribe] :[回复] {0}'.format(r.text))  


# 创建批次订阅
def subscribe_batch(batch_topic):  
    postdata = json.dumps(batch_topic) 
    print('[subscribe_batch] :[需重新订阅主题] {0}'.format(postdata))
    r = requests.post('http://' + host + ':' + str(port) + '/api/v3/mqtt/subscribe_batch', data=postdata, auth=('admin', 'public'))
    print('[subscribe_batch] :[回复] {0}'.format(r.text))
    

def publish_batch(batch_payload):  
    postdata = json.dumps(batch_payload) 
    print('[publish_batch] :[需重新发布消息] {0}'.format(postdata))
    r = requests.post('http://' + host + ':' + str(port) + '/api/v3/mqtt/publish_batch', data=postdata, auth=('admin', 'public'))
    print('[publish_batch] :[回复] {0}'.format(r.text))


def subscriptions(client_id):  
    r = requests.get('http://' + host + ':' + str(port) + '/api/v3/subscriptions/' + client_id, auth=('admin', 'public'))
    j = json.loads(r.text)
    data = j['data']
    topices = []
    for item in data:
        topices.append(item['topic'])
    print('[subscriptions] :[已订阅主题列表] {0}>>{1}'.format(client_id, topices))
    return topices   


def check_persistence(client_id):
    r = requests.get('http://' + host + ':' + str(port) + '/api/v3/sessions/' + client_id, auth=('admin', 'public'))
    j = json.loads(r.text)
    flag = False
    if j['code'] == 0:
        data = j['data']
        if data:
            sess = data[0]
            clean_session = sess['clean_start']
            if not clean_session:
                flag = True
    print('[check_persistence] :[验证session持久化] {0}>>{1}'.format(client_id, flag))
    return flag        


# 断开指定连接
def disconnection(client_id):
    r = requests.delete('http://' + host + ':' + str(port) + '/api/v3/connections/' + client_id, auth=('admin', 'public'))
    print('[disconnection] :[回复] {0}>>{1}'.format(client_id, r.text))


class MessagesHandle():
    
    def __init__(self, redis_host='127.0.0.1', redis_password='', mqtt_host='127.0.0.1', mqtt_web_port=18083): 
        flag = True
        while flag:
            try :
                self.pool = redis.ConnectionPool(host=redis_host, password=redis_password)  # 实现一个连接池
                self.red = redis.Redis(connection_pool=self.pool)
                self.red.set('redis_connection', 'success')
                flag = False 
                global host, port
                host = mqtt_host
                port = mqtt_web_port
            except:
                traceback.print_exc()
                time.sleep(3)        
        
    def consumer_queue (self, messages_queue, topic_resume):
        while True:
            try :
                MQTT_RETAINER_NAME = 'mqtt_retainer'
                SPECIAL_CLIENT_ID = 'emqx_restart_retainer_plugin_by_gm' 
                
                self.red.get('redis_connection')
                
                message = messages_queue.get()  
                action = message['action']
                # print('--->', message)
                if action == 'session_subscribed' and topic_resume:
                    # 新增订阅
                    client_id = message['client_id']
                    
                    # 持久化session且开启主题恢复
                    if check_persistence(client_id):
                        topic = message['topic']
                        opts = message['opts']
                        qos = opts['qos']
                        self.red.sadd(client_id, topic + ';' + str(qos))
                        print('[consumer_queue] :[主题持久化完成] {0}>>{1}>>{2}'.format(client_id, topic, qos))
                elif action == 'client_connected':
                    # 连接成功，调用web Api进行历史订阅
                    client_id = message['client_id']
                    
                    # 指定用户上线，利用它的身份进行持久化消息转发
                    if client_id == SPECIAL_CLIENT_ID:
                        s = self.red.hgetall(MQTT_RETAINER_NAME)
                        batch_payload = []
                        for (k, v) in  s.items():
                            topic = str(k, encoding="utf-8")
                            v = str(v, encoding="utf-8")
                            qos = str(v.split(';;')[1])
                            payload = str(v.split(';;')[0])
                            postdata = {
                              "topic": topic,
                              "qos": int(qos),
                              "client_id": client_id,
                              'payload':payload,
                              'retain':True
                            }
                            batch_payload.append(postdata)
                        # if batch_payload:    
                        publish_batch(batch_payload)     
                        time.sleep(5)
                        disconnection(client_id) 
                    elif client_id != SPECIAL_CLIENT_ID and topic_resume:
                        time.sleep(3)
                        # 持久化session
                        if check_persistence(client_id):    
                            batch_topic = []
                            # 已订阅主题列表
                            topices = subscriptions(client_id)
                            s = self.red.smembers(client_id)   
                            for obj in s:
                                obj = str(obj, encoding="utf-8")  
                                topic = str(obj.split(';')[0])
                                qos = int(obj.split(';')[1])
                                # 未订阅过的主题信息
                                if topic not in topices:
                                    postdata = {
                                      "topic": topic,
                                      "qos": qos,
                                      "client_id": client_id
                                    }
                                    batch_topic.append(postdata)
                            if batch_topic:
                                subscribe_batch(batch_topic)
                    
                elif action == 'session_unsubscribed' and topic_resume:
                    client_id = message['client_id']
                    # 持久化session
                    if check_persistence(client_id):   
                        topic = message['topic']
                        # 移除订阅
                        self.red.srem(client_id, topic + ';0')
                        self.red.srem(client_id, topic + ';1')
                        self.red.srem(client_id, topic + ';2')   
                        print('[consumer_queue] :[主题删除完成] {0}>>{1}'.format(client_id, topic))
                elif action == 'message_publish' and message['from_client_id'] != SPECIAL_CLIENT_ID:
                    if message['retain']:
                        topic = message['topic']
                        qos = message['qos']
                        payload = message['payload']
                      
                        self.red.hset(MQTT_RETAINER_NAME, topic, payload + ';;' + str(qos))
                        print('[consumer_queue] :[消息持久化完成] {0}>>{1}>>{2}>>{3}'.format(client_id, topic, qos, payload))
            except ConnectionError:
                print('wait reconnection ...') 
                time.sleep(3)     
            except:
                traceback.print_exc()    
        
