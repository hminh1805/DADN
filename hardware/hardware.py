from yolobit import *
button_a.on_pressed = None
button_b.on_pressed = None
button_a.on_pressed_ab = button_b.on_pressed_ab = -1
from mqtt import *
from machine import RTC
import ntptime
import time
from aiot_lcd1602 import LCD1602
from event_manager import *
from aiot_rgbled import RGBLed
from machine import Pin, SoftI2C
from aiot_dht20 import DHT20

aiot_lcd1602 = LCD1602()

event_manager.reset()

def on_mqtt_message_receive_callback__V6_(th_C3_B4ng_tin):
  global RT, RH, LUX, SM
  if th_C3_B4ng_tin == 'Hết nước':
    mqtt.publish('V10', '1')
  else:
    mqtt.publish('V10', '0')

def on_mqtt_message_receive_callback__V10_(th_C3_B4ng_tin):
  global RT, RH, LUX, SM
  if th_C3_B4ng_tin == '1':
    pin14.write_analog(round(translate(70, 0, 100, 0, 1023)))
  else:
    pin14.write_analog(round(translate(0, 0, 100, 0, 1023)))

tiny_rgb = RGBLed(pin0.pin, 4)

def on_mqtt_message_receive_callback__V11_(th_C3_B4ng_tin):
  global RT, RH, LUX, SM
  if th_C3_B4ng_tin == '1':
    tiny_rgb.show(0, hex_to_rgb('#ff0000'))
  else:
    tiny_rgb.show(0, hex_to_rgb('#000000'))

# Mô tả hàm này...
def _C4_90_C4_82NG_K_C3_9D_SERVER():
  global th_C3_B4ng_tin, RT, RH, LUX, SM, aiot_dht20, aiot_lcd1602, tiny_rgb
  mqtt.on_receive_message('V6', on_mqtt_message_receive_callback__V6_)
  mqtt.on_receive_message('V10', on_mqtt_message_receive_callback__V10_)
  mqtt.on_receive_message('V11', on_mqtt_message_receive_callback__V11_)

aiot_dht20 = DHT20()

def on_event_timer_callback_u_a_N_O_h():
  global th_C3_B4ng_tin, RT, RH, LUX, SM
  aiot_dht20.read_dht20()
  RT = aiot_dht20.dht20_temperature()
  RH = aiot_dht20.dht20_humidity()
  LUX = round(translate((pin0.read_analog()), 0, 4095, 0, 100))
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
  aiot_lcd1602.putstr('LUX:')
  aiot_lcd1602.move_to(4, 1)
  aiot_lcd1602.putstr(LUX)
  aiot_lcd1602.move_to(6, 1)
  aiot_lcd1602.putstr('%')
  aiot_lcd1602.move_to(9, 1)
  aiot_lcd1602.putstr('SM')
  aiot_lcd1602.move_to(13, 1)
  aiot_lcd1602.putstr(SM)
  aiot_lcd1602.move_to(15, 1)
  aiot_lcd1602.putstr('%')
  mqtt.publish('V1', RT)
  mqtt.publish('V2', RH)
  mqtt.publish('V3', LUX)
  mqtt.publish('V4', SM)

event_manager.add_timer_event(30000, on_event_timer_callback_u_a_N_O_h)

def on_event_timer_callback_A_U_i_h_L():
  global th_C3_B4ng_tin, RT, RH, LUX, SM
  if (aiot_dht20.dht20_temperature()) >= '27':
    pin14.write_analog(round(translate(70, 0, 100, 0, 1023)))
    mqtt.publish('V11', '1')
  if (aiot_dht20.dht20_temperature()) < '27':
    pin14.write_analog(round(translate(0, 0, 100, 0, 1023)))
    mqtt.publish('V11', '0')

event_manager.add_timer_event(1800000, on_event_timer_callback_A_U_i_h_L)

if True:
  display.scroll('YOLOPET')
  mqtt.connect_wifi('wifi', 'password')
  mqtt.connect_broker(server='mqtt.ohstem.vn', port=1883, username='YOLOPET', password='')
  ntptime.settime()
  (year, month, mday, week_of_year, hour, minute, second, milisecond) = RTC().datetime()
  RTC().init((year, month, mday, week_of_year, hour+7, minute, second, milisecond))
  aiot_lcd1602.clear()
  _C4_90_C4_82NG_K_C3_9D_SERVER()
  display.scroll('OK')

while True:
  mqtt.check_message()
  event_manager.run()
  time.sleep_ms(1000)
  time.sleep_ms(10)
