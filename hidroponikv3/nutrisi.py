import serial
def nutrisi():
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    ser.flush()
    while True:
        try: 
            if ser.in_waiting > 0:
                nutrisi = ser.readline().decode('utf-8').rstrip()
                #nutrisi2 = nutrisi.replace('ppm', '')
                nutrisi3 = int(float(nutrisi))
                print(nutrisi3)
                if nutrisi3 > 0 :
                    break
        except:
            continue
    
    return nutrisi3

nutrisi()