import serial
from time import sleep


def read_data(ser): 

    received_data = ser.read()              
    sleep(0.03)
    
    while ser.inWaiting()>0:
        data_left = ser.inWaiting()
        received_data += ser.read(data_left)
        sleep(0.03)
    
    datos_recibidos = received_data.decode("utf-8")
    
    return datos_recibidos

def write_data(ser, command):
    
    WaitBytes = ser.write((command + "\n").encode())
    ser.read(WaitBytes) #To Avoid read the input later and its print on screen


def read_and_print(ser):
    
    data = read_data(ser)    
    lines = data.split("\r\n")
    
    output = ""
    
    for index, line in enumerate(lines):
        output += line
        
        if index == len(lines)-1:
            print(line, end = "")
            
        else: 
            print(line)
            
    return output
            

def send_command(ser, command):

    write_data(ser, command)
    return(read_and_print(ser))




def main():
    
    ser = serial.Serial ("/dev/ttyS0", 57600)    #Open port with baud rate

    command = "ls ../../"
    send_command(ser, command)
        



if __name__ == "__main__":
    main()




    


