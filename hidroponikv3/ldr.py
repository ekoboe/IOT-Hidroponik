import RPi.GPIO as GPIO
import time
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT)

def rc_time():
    count=0
    GPIO.setup(3, GPIO.OUT)
    GPIO.output(3, GPIO.LOW)
    time.sleep(1)
    GPIO.setup(3, GPIO.IN)
    while (GPIO.input(3) == GPIO.LOW):
        count += 1
    return count

try:
    while True:
        value = rc_time()
        print(value)
        if (value >4000):
            GPIO.output(11, True)
        if (value < 4000):
            GPIO.output(11, False)
        
except KeyboardInterrupt:
    pass

finally:
    GPIO.cleanup()