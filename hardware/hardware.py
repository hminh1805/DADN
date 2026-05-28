from yolobit import *
button_a.on_pressed = None
button_b.on_pressed = None
button_a.on_pressed_ab = button_b.on_pressed_ab = -1
from mqtt import *
from aiot_lcd1602 import LCD1602
from event_manager import *
from aiot_rgbled import RGBLed
import music
from aiot_hcsr04 import HCSR04
from machine import Pin, SoftI2C
from aiot_dht20 import DHT20

aiot_lcd1602 = LCD1602()

event_manager.reset()

tiny_rgb = RGBLed(pin2.pin, 4)

AIO_SERVER = 'io.adafruit.com'
AIO_PORT = 1883
AIO_USERNAME = 'DADN252'
AIO_KEY = 'key'

a = 0.0
b = 0.0
c = 0.0
x = 0.0
RT = 0.0
RH = 0.0
motion = False
ada_connected = False

def set_fan_speed(percent):
  pin16.write_analog(round(translate(percent, 0, 100, 0, 1023)))

def set_heater_on(is_on):
  if is_on:
    tiny_rgb.show(0, hex_to_rgb('#ff0000'))
  else:
    tiny_rgb.show(0, hex_to_rgb('#000000'))

def connect_adafruit():
  global ada_connected
  try:
    if not mqtt.wifi_connected():
      ada_connected = False
      return False
    if ada_connected:
      return True
    mqtt.connect_broker(server=AIO_SERVER, port=AIO_PORT, username=AIO_USERNAME, password=AIO_KEY)
    mqtt.on_receive_message('heater', on_mqtt_message_receive_callback__heater_)
    mqtt.on_receive_message('maybom', on_mqtt_message_receive_callback__maybom_)
    #mqtt.on_receive_message('servo', on_mqtt_message_receive_callback__servo_)
    mqtt.on_receive_message('dog-feeder', on_mqtt_message_receive_callback__dog_feeder)
    mqtt.on_receive_message('cat-feeder', on_mqtt_message_receive_callback__cat_feeder)
    mqtt.on_receive_message('quat', on_mqtt_message_receive_callback__quat_)
    mqtt.on_receive_message('speaker', on_mqtt_message_receive_callback__speaker_)
    mqtt.on_receive_message('savevar', on_mqtt_message_receive_callback__savevar_)
    ada_connected = True
    return True
  except:
    ada_connected = False
    return False

import sys
import select

def listen_serial_commands():
    # Kiểm tra xem có dữ liệu trong buffer Serial không (không làm block chương trình)
    while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        char = sys.stdin.read(1)
        
        # Bắt đầu nhận diện lệnh
        if char == 'D':
            state = sys.stdin.read(1)
            if state == '1':
                on_mqtt_message_receive_callback__dog_feeder('1')
            elif state == '0':
                on_mqtt_message_receive_callback__dog_feeder('0')
        
        elif char == 'C':
            state = sys.stdin.read(1)
            if state == '1':
                on_mqtt_message_receive_callback__cat_feeder('1')
            elif state == '0':
                on_mqtt_message_receive_callback__cat_feeder('0')

def auto_ctrl():
  global x
  x = (a * RT + b * RH) + c
  if x <= -1:
    set_fan_speed(0)
    set_heater_on(True)
  else:
    set_heater_on(False)
    if x >= 2:
      set_fan_speed(100)
    else:
      if x >= 1:
        set_fan_speed(70)
      else:
        set_fan_speed(0)

def on_mqtt_message_receive_callback__heater_(th_C3_B4ng_tin):
  if th_C3_B4ng_tin == '1':
    tiny_rgb.show(0, hex_to_rgb('#ff0000'))
  else:
    tiny_rgb.show(0, hex_to_rgb('#000000'))

def on_mqtt_message_receive_callback__maybom_(th_C3_B4ng_tin):
  if th_C3_B4ng_tin == '1':
    pin14.write_analog(round(translate(100, 0, 100, 0, 1023)))
  else:
    pin14.write_analog(round(translate(0, 0, 100, 0, 1023)))

def on_mqtt_message_receive_callback__servo_(th_C3_B4ng_tin):
  if th_C3_B4ng_tin == '1':
    pin15.servo_write(100)
  else:
    pin15.servo_write(0)

def on_mqtt_message_receive_callback__dog_feeder(th_C3_B4ng_tin):
  if th_C3_B4ng_tin == '1':
    pin15.servo_write(100) # Cắm Servo của Chó ở chân Pin 15
  else:
    pin15.servo_write(0)

def on_mqtt_message_receive_callback__cat_feeder(th_C3_B4ng_tin):
  if th_C3_B4ng_tin == '1':
    pin13.servo_write(100) # Cắm Servo của Mèo ở chân Pin 13
  else:
    pin13.servo_write(0)

def on_mqtt_message_receive_callback__quat_(th_C3_B4ng_tin):
  if th_C3_B4ng_tin == '2':
    pin16.write_analog(round(translate(100, 0, 100, 0, 1023)))
  elif th_C3_B4ng_tin == '1':
    pin16.write_analog(round(translate(70, 0, 100, 0, 1023)))
  else:
    pin16.write_analog(round(translate(0, 0, 100, 0, 1023)))

def on_mqtt_message_receive_callback__speaker_(th_C3_B4ng_tin):
  if th_C3_B4ng_tin == '1':
    music.play(music.BIRTHDAY, wait=False)
  else:
    music.stop()

def _C4_90_C4_82NG_K_C3_9D_SERVER():
  global aiot_ultrasonic
  connect_adafruit()
  aiot_ultrasonic = HCSR04(trigger_pin=pin3.pin, echo_pin=pin6.pin)

def on_mqtt_message_receive_callback__savevar_(th_C3_B4ng_tin):
  global a, b, c, x
  try:
    values = th_C3_B4ng_tin.split(':')
    if len(values) == 3:
      a = float(values[0])
      b = float(values[1])
      c = float(values[2])
      try:
        x = (a * RT + b * RH) + c
      except:
        pass
  except:
    pass

def publish_sensor_data(sensor_data):
  global ada_connected
  try:
    mqtt.publish('SENSOR', sensor_data)
    ada_connected = True
    return True
  except:
    ada_connected = False
    return False

def run_offline_control_if_needed(is_ada_connected):
  if not is_ada_connected:
    auto_ctrl()

aiot_dht20 = DHT20()

def on_event_timer_callback_U_h_W_p_G():
  global RT, RH, motion, SM, dis
  ada_ok = connect_adafruit()
  aiot_dht20.read_dht20()
  RT = aiot_dht20.dht20_temperature()
  RH = aiot_dht20.dht20_humidity()
  motion = pin0.read_digital()==1
  SM = round(translate((pin1.read_analog()), 0, 4095, 0, 100))
  dis = aiot_ultrasonic.distance_cm()
  aiot_lcd1602.move_to(0, 0)
  aiot_lcd1602.putstr('RT:')
  aiot_lcd1602.move_to(3, 0)
  aiot_lcd1602.putstr(RT)
  aiot_lcd1602.move_to(7, 0)
  aiot_lcd1602.putstr('*C')
  aiot_lcd1602.move_to(10, 0)
  aiot_lcd1602.putstr('RH:')
  aiot_lcd1602.move_to(13, 0)
  aiot_lcd1602.putstr(RH)
  aiot_lcd1602.move_to(15, 0)
  aiot_lcd1602.putstr('%')
  aiot_lcd1602.move_to(0, 1)
  aiot_lcd1602.putstr('DIS:')
  aiot_lcd1602.move_to(4, 1)
  aiot_lcd1602.putstr(dis)
  aiot_lcd1602.move_to(10, 1)
  aiot_lcd1602.putstr('SM:')
  aiot_lcd1602.move_to(13, 1)
  aiot_lcd1602.putstr(SM)
  aiot_lcd1602.move_to(15, 1)
  aiot_lcd1602.putstr('%')
  sensor_data = ''.join([str(x2) for x2 in ['#', RT, ':', RH, ':', SM, ':', motion, ':', dis, '!']])
  if serial == 1:
    print(sensor_data, end =' ')
  else:
    if ada_ok:
      ada_ok = publish_sensor_data(sensor_data)
  run_offline_control_if_needed(ada_ok)

event_manager.add_timer_event(9000, on_event_timer_callback_U_h_W_p_G)

def on_button_a_pressed():
  global serial
  serial = 1

button_a.on_pressed = on_button_a_pressed

def on_button_b_pressed():
  global serial
  serial = 0

button_b.on_pressed = on_button_b_pressed

if True:
  display.scroll('YOLOPET')
  try:
    mqtt.connect_wifi('M', 'hminh1805')
  except:
    pass
  display.scroll('wf')
  _C4_90_C4_82NG_K_C3_9D_SERVER()
  serial = 0
  aiot_lcd1602.clear()
  display.scroll('OK')

while True:
  try:
    mqtt.check_message()
  except:
    ada_connected = False
  
  listen_serial_commands()
  event_manager.run()
  
  time.sleep_ms(10)
