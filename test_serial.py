'''
UART communication on Raspberry Pi using Pyhton
http://www.electronicwings.com
'''

import serial
from time import sleep


ser = serial.Serial ("/dev/ttyS0", 57600)    #Open port with baud rate

while True:
    
    received_data = ser.readline() 
