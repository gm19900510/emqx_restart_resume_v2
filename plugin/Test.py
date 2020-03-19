# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
import time
import traceback

client = mqtt.Client(client_id='emqx_test', clean_session=False)


# 用于响应服务器端 CONNACK 的 callback，如果连接正常建立，rc 值为 0
def on_connect(mqttClient, userdata, flags, rc):
    print("Connection returned with result code:" + str(rc))

    
def on_subscribe():
    # time.sleep(0.5)
    client.subscribe("test", 1)  # 主题为"test"
    client.subscribe("test123123123", 1)
    client.subscribe("testtopic", 1)
    client.on_message = on_message_come  # 消息到来处理函数


# 消息处理函数
def on_message_come(mqttClient, userdata, msg): 
    print("产生消息", msg.payload.decode("utf-8"))

    
# 在连接断开时的 callback，打印 result code
def on_disconnect(mqttClient, userdata, rc):
    print("Disconnection returned result:" + str(rc))
    
    flag = True
    while flag:
        try:    
            # 连接 broker
            # connect() 函数是阻塞的，在连接成功或失败后返回。如果想使用异步非阻塞方式，可以使用 connect_async() 函数。
            mqttClient.connect('192.168.3.163', 1883, 60)
            flag = False
        
        except:
            traceback.print_exc()
            time.sleep(1)     
    
    mqttClient.loop_start()
    

def on_socket_close(client, userdata):
    print(client, userdata)

        
if __name__ == '__main__':

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_socket_close = on_socket_close
    flag = True
    while flag:
        try:    
            # 连接 broker
            # connect() 函数是阻塞的，在连接成功或失败后返回。如果想使用异步非阻塞方式，可以使用 connect_async() 函数。
            client.connect('192.168.3.163', 1883, 60)
            flag = False
        
        except:
            traceback.print_exc()
            time.sleep(1)     
    
    client.loop_start()
    on_subscribe()
        
    while not flag: 
        # 断开连接
        time.sleep(5)  # 等待消息处理结束 
