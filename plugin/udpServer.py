import socket
import json

class UdpServer():
    
    def __init__(self, udp_host, udp_port):
        self.udp_host = udp_host
        self.udp_port = udp_port

    def handle (self, messages_queue):    
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((self.udp_host, self.udp_port))
        print('[handle] :[开启udp监听] {0}'.format(self.udp_port))
        while True:
            data, addr = s.recvfrom(1024 * 1024)
            obj = str(data, encoding="utf-8")  
            print('[handle] :[新消息] {0}'.format(obj))
            messages_queue.put(json.loads(obj))
   
