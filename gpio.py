from gpiozero import LED
from time import sleep

led_open = LED(4)

while True:
    led_open.on()
    sleep(1)
    led_open.off()
    sleep(1)