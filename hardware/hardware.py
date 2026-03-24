from mqtt import *
from yolobit import *
button_a.on_pressed = None
button_b.on_pressed = None
button_a.on_pressed_ab = button_b.on_pressed_ab = -1
from aiot_rgbled import RGBLed
import music
from machine import RTC
import ntptime
import time
from aiot_lcd1602 import LCD1602
from event_manager import *
from machine import Pin, SoftI2C
from aiot_dht20 import DHT20

tiny_rgb = RGBLed(pin13.pin, 4)

def on_mqtt_message_receive_callback__LED_(th_C3_B4ng_tin):
  global serial, RT, RH, LUX, SM
  if th_C3_B4ng_tin == '1':
    tiny_rgb.show(0, hex_to_rgb('#ff0000'))
  else:
    tiny_rgb.show(0, hex_to_rgb('#000000'))

def on_mqtt_message_receive_callback__MAYBOM_(th_C3_B4ng_tin):
  global serial, RT, RH, LUX, SM
  if th_C3_B4ng_tin == '1':
    pin14.write_analog(round(translate(70, 0, 100, 0, 1023)))
  else:
    pin14.write_analog(round(translate(0, 0, 100, 0, 1023)))

def on_mqtt_message_receive_callback__SERVO_(th_C3_B4ng_tin):
  global serial, RT, RH, LUX, SM
  if th_C3_B4ng_tin == '1':
    pin15.servo_write(90)
  else:
    pin15.servo_write(0)

def on_mqtt_message_receive_callback__QUAT_(th_C3_B4ng_tin):
  global serial, RT, RH, LUX, SM
  if th_C3_B4ng_tin == '1':
    pin16.write_analog(round(translate(70, 0, 100, 0, 1023)))
  else:
    pin16.write_analog(round(translate(0, 0, 100, 0, 1023)))

def on_mqtt_message_receive_callback__CANHBAO_(th_C3_B4ng_tin):
  global serial, RT, RH, LUX, SM
  if th_C3_B4ng_tin == '1':
    music.play(music.POWER_UP, wait=False)
  else:
    music.stop()

# Mô tả hàm này...
def _C4_90_C4_82NG_K_C3_9D_SERVER():
  global th_C3_B4ng_tin, serial, RT, RH, LUX, SM, aiot_dht20, tiny_rgb, aiot_lcd1602
  mqtt.on_receive_message('LED', on_mqtt_message_receive_callback__LED_)
  mqtt.on_receive_message('MAYBOM', on_mqtt_message_receive_callback__MAYBOM_)
  mqtt.on_receive_message('SERVO', on_mqtt_message_receive_callback__SERVO_)
  mqtt.on_receive_message('QUAT', on_mqtt_message_receive_callback__QUAT_)
  mqtt.on_receive_message('CANHBAO', on_mqtt_message_receive_callback__CANHBAO_)

aiot_lcd1602 = LCD1602()

event_manager.reset()

aiot_dht20 = DHT20()

def on_event_timer_callback_U_h_W_p_G():
  global th_C3_B4ng_tin, serial, RT, RH, LUX, SM
  aiot_dht20.read_dht20()
  RT = aiot_dht20.dht20_temperature()
  RH = aiot_dht20.dht20_humidity()
  LUX = round(translate((pin0.read_analog()), 0, 4095, 0, 100))
  SM = round(translate((pin1.read_analog()), 0, 4095, 0, 100))
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
  if serial == 1:
    print((''.join([str(x) for x in ['#', RT, ':', RH, ':', LUX, ':', SM, '!']])), end =' ')
  else:
    mqtt.publish('SENSOR', (''.join([str(x2) for x2 in ['!', RT, ':', RH, ':', LUX, ':', SM, '#']])))

event_manager.add_timer_event(5000, on_event_timer_callback_U_h_W_p_G)

def on_button_a_pressed():
  global th_C3_B4ng_tin, serial, RT, RH, LUX, SM
  serial = 1

button_a.on_pressed = on_button_a_pressed

def on_button_b_pressed():
  global th_C3_B4ng_tin, serial, RT, RH, LUX, SM
  serial = 0

button_b.on_pressed = on_button_b_pressed

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
