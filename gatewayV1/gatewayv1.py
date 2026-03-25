import sys
from Adafruit_IO import MQTTClient
import serial.tools.list_ports

import os
import random
import time
import json
from dotenv import load_dotenv 
load_dotenv()

AIO_TEST_LOCAL = 'test' # bật tắt cái auto tạo giá trị ảo để test
AIO_SENSOR_ID = 'sensor'
AIO_FEED_ID = ['maybom','led','servo','quat','heater'] # tạo thành list cho dễ



AIO_USERNAME = os.getenv("AIO_USERNAME", "your_name")
AIO_KEY = os.getenv("AIO_KEY", "your_key")
 
print(AIO_USERNAME)
print(AIO_KEY)

def connected(client):
    print("Ket noi thanh cong")
    client.subscribe(AIO_TEST_LOCAL)
    for feed in AIO_FEED_ID:
        client.subscribe(feed)

def subscribe(client, userdata, mid, granted_qos):
    pass

def disconnected(client):
    print("Ngat ket noi")
    sys.exit(1)

# tự động tìm Port
import serial.tools.list_ports

def getPort():
    ports = serial.tools.list_ports.comports()
    print("--- ĐANG QUÉT CỔNG USB ---")

    for port in ports:
        print(f"lỗ cắm: {port.device} - {port.description}")
        
        
        keyword = ["USB", "SERIAL", "CH340", "CP210", "FTDI", "MBED", "ARDUINO", "JLINK"]
        desc = port.description.upper()
        if any(key in desc for key in keyword):
            return port.device
            
    print(" Không tìm thấy cổng nào phù hợp!")
    return "None" 

#================================
# CHIỀU MẠCH -> SERVER
#================================

#xử lý data -> json và gửi lên server
def processData ( data ) :
    data = data.replace('!',"").replace("#","").strip()
    splitData = data.split(':')
    print("Dữ liệu thô từ cổng USB: ", splitData)
    if(len(splitData) == 5):
        try:
            thong_so = {
                'nhiet_do' : float(splitData[0]),
                'do_am' : float(splitData[1]),
                'muc_nuoc' : float(splitData[2]),
                'motion' : splitData[3],
                'distance' : float(splitData[4])
            }
            
            chuoi_json = json.dumps(thong_so)
            print("Đang đẩy JSON lên: ", chuoi_json)
            
            client.publish(AIO_SENSOR_ID,chuoi_json)
            
        except ValueError:
            print("Lỗi giá trị")
            
    else:
        print("Lỗi thiếu hoặc dư tham số. Yêu cầu gửi 6 tham số! (nhiệt độ :độ ẩm kk : độ ẩm đất : motion, distance)")

#đọc từng byte từ mạch -> tạo thành data
mess = ""
def readSerial () :
    bytesToRead = ser.inWaiting()
    if ( bytesToRead > 0) :
        
        global mess
        mess = mess + ser.read( bytesToRead ).decode("UTF -8")
        
        while ("#" in mess ) and ("!" in mess ) :
            start = mess.find("#")
            end = mess.find("!")
            print(mess [ start : end + 1])
            processData( mess [ start : end + 1])
            if ( end == len( mess )) :
                mess = ""
            else :
                mess = mess[ end +1:]


#================================
# CHIỀU SERVER -> MẠCH
#================================
# tin nhắn từ server gửi xuống
def message(client, feed_id, payload):
    global on_auto
    print(f"Nhận lệnh từ Kênh [{feed_id}] - Giá trị: {payload}")
    
    lenh_xuong_mach = "" 

    # 1. NHẬN LỆNH TỪ SERVER
    if feed_id == 'maybom':
        lenh_xuong_mach = f"{payload}#"
        
    elif feed_id == 'servo':
        lenh_xuong_mach = f"{payload}#"
        
    elif feed_id == 'led':
        lenh_xuong_mach = f"{payload}#"
    
    elif feed_id == 'heater':
        lenh_xuong_mach = f"{payload}#"
        
    elif feed_id == 'quat':
        lenh_xuong_mach = f"{payload}#"
        
    #test -> ko can quan tam
    elif feed_id == 'test':
        if payload == '0':
            on_auto = False
            print(">>> ĐÃ TẮT CHẾ ĐỘ AUTO <<<")
        else:
            on_auto = True
            print(">>> ĐÃ BẬT CHẾ ĐỘ AUTO <<<")
        return # Thoát hàm luôn, ko chạy phần gửi USB bên dưới
        
    else:
        print("Lệnh lạ, không biết xử lý: ")
        print('feed_id : ' + feed_id + 'payload : ' + payload ) 
        return


    # 2. GỬI LỆNH QUA CÁP USB XUỐNG MẠCH

    if lenh_xuong_mach != "":
        try:
            ser.write(lenh_xuong_mach.encode('utf-8'))
            print(f"Đã gửi lệnh [{lenh_xuong_mach}] qua cổng USB thành công!")
        except Exception as e:
            print("Cảnh báo: Chưa cắm mạch hoặc lỗi cáp USB!")




client = MQTTClient(AIO_USERNAME,AIO_KEY)
client.on_connect = connected 
client.on_disconnect = disconnected
client.on_subscribe = subscribe
client.on_message = message
client.connect()
client.loop_background()

ser = None
def operPort():
    portName = getPort()
    print("PORT = " + portName)
    if portName != 'None':
        try:
            global ser
            ser = serial.Serial(port=portName, baudrate=115200)
            print(f"Đã kết nối mạch qua cổng: {portName}")
        except Exception as e:
            print("Lỗi mở cổng USB!")
            
    else:
        print("Không cắm cáp USB. Đang chạy chế độ GIẢ LẬP (Mock Data) chờ Web!")
        ser = None


on_auto = False
print(">>> ĐÃ TẮT CHẾ ĐỘ AUTO <<<")

operPort()
while True: 
    #nếu có cắm dây
    #operPort()
    
    if ser is not None: 
        readSerial()
        
        time.sleep(0.1) 
    #nếu ko cắm dây
    else:
        
        if on_auto == True:
            thong_so = {
                'nhiet_do': round(random.uniform(25.0, 35.0), 1),
                'do_am': round(random.uniform(50.0, 80.0), 1),
                'muc_nuoc': round(random.uniform(10.0, 90.0), 1),
                'anh_sang': round(random.uniform(200.0, 800.0), 1)
                
            }
            chuoi_json = json.dumps(thong_so)
            print("TEST ẢO: Đang đẩy JSON lên: ", chuoi_json)
            client.publish(AIO_SENSOR_ID, chuoi_json)
        time.sleep(10)
    
