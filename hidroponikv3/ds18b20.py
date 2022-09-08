import time
from w1thermsensor import W1ThermSensor

sensor = W1ThermSensor()

while True:
	temp = sensor.get_temperature()
	print(temp)

	time.sleep(1)
