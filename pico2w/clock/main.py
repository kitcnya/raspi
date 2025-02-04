import machine, utime
led = machine.Pin("LED", machine.Pin.OUT)
while True:
    led.value(1)
    utime.sleep(0.5)
    led.value(0)
    utime.sleep(0.5)
