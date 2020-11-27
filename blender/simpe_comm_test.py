import serial
import time
import math

ser = serial.Serial("COM10", 115200, timeout=2000)
ser.write("100 f 100 f".encode("UTF-8"))
#time.sleep(1)

delay = 30 / 1000

def transform_function(input):
    return abs(int(math.sin(input*40)*30) + 40)

for i in range(1, 10):
    output = str(transform_function(i)) + " a"
    doubleoutput = output + " " + output + "\n"
    
    print(doubleoutput)
    
    ser.write("700 f 200 f".encode("UTF-8"))
    ser.read(6)
    time.sleep(delay)
    ser.write(doubleoutput.encode("UTF-8"))
    ser.read(6)
    time.sleep(delay)

ser.close()
