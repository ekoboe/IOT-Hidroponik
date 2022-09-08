import serial

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
ser.flush()
try:
    while True: 
        if ser.in_waiting > 0:
            nutrisi = ser.readline().decode('utf-8').rstrip()
            nutrisi3 = int(float(nutrisi))
            print(nutrisi3)
except:
    nutrisi = 0
    print(nutrisi)