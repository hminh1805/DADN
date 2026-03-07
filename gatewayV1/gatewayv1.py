import sys
from Adafruit_IO import MQTTClient
import serial.tools.list_ports

import random
import time


on_auto = True

AIO_FEED_ID = ['your_feed_id']
AIO_USERNAME = 'your_username'
AIO_KEY = 'your_key'

def connected(client):
    print("Ket noi thnah cong")
    for feed in AIO_FEED_ID:
        client.subscribe(feed)

def subscribe(client, userdata, mid, granted_qos):
    print("subcribe thanh cong")

def disconnected():
    print("Ngat ket noi")
    sys.exit(1)
    
def message(client, feed_id, payload):
    global on_auto
    print("nhan du lieu "+ payload)
    if payload == '0':
        on_auto = False
        print(">>> ĐÃ TẮT CHẾ ĐỘ AUTO <<<")
    else: 
        on_auto = True
        print(">>> ĐÃ BẬT CHẾ ĐỘ AUTO <<<")
    
def getPort(): # tu dong tim dung port
    ports = serial.tools.list_ports.comports()
    N = len(ports)
    comPort = 'None'
    for i in range(0,N):
        port = ports[i]
        strPort = str(port)
        if 'USB Serial Device' in strPort:
            splitPort  = strPort.split(' ')
            comPort = (splitPort[0])
    return comPort
    

# khi nao cam usb vao moi xai
#ser = serial.Serial ( port = getPort (), baudrate =115200)

client = MQTTClient(AIO_USERNAME,AIO_KEY)
client.on_connect = connected
client.on_disconnect = disconnected
client.on_subscribe = subscribe
client.on_message = message
client.connect()
client.loop_background()


def processData ( data ) :
    data = data . replace ("!", "")
    data = data . replace ("#", "")
    splitData = data . split (":")
    print ( splitData )
    if splitData [1] == " TEMP ":
        client . publish ("bbc - temp ", splitData [2])

# khi nao cam usb moi xai
# mess = ""
# def readSerial () :
#     bytesToRead = ser.inWaiting()
#     if ( bytesToRead > 0) :
#         global mess
#         mess = mess + ser.read( bytesToRead ).decode("UTF -8")
#         while ("#" in mess ) and ("!" in mess ) :
#             start = mess.find("!")
#             end = mess.find("#")
#             processData( mess [ start : end + 1])
#             if ( end == len( mess )) :
#                 mess = ""
#             else :
#                 mess = mess[ end +1:]





while True: 
    val = random.randint(1,30)
    if on_auto == True:
        print("cap nhat gia tri : " , val)
        client.publish('temp',val)
    time.sleep(4)
    
