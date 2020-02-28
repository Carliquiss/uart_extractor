import serial

from time import sleep
from colorama import init, Fore, Back, Style

init(autoreset=True) #Colorama autoreset


def read_data(ser): 
    """
        Read bytes until there is no more avaliable on the serial port
        and return the result of the read
    """
    received_data = ser.read()              
    sleep(0.1)
    
    while ser.inWaiting()>0:
        data_left = ser.inWaiting()
        received_data += ser.read(data_left)
        sleep(0.1)
    
    datos_recibidos = received_data.decode("utf-8")
    
    return datos_recibidos


def write_data(ser, command):
    """
        Write any command to the device connected through the serial port
    """
    WaitBytes = ser.write((command + "\n").encode())
    ser.read(WaitBytes) #To Avoid read the input later and its print on screen
   
    
def read_and_print(ser):
    """
        Read and (pretty)print all the data received from the serial port
    """
    data = read_data(ser)    
    lines = data.split("\r\n")
    
    output = ""
    
    for index, line in enumerate(lines):
        output += line + "\n"
        
        if index == len(lines)-1:
            print(line, end = "")
            
        else: 
            print(line)
            
    return output
            

def send_command(ser, command):
    """
        Send any command and get the result
    """
    write_data(ser, command)
    return read_data(ser)
    #return(read_and_print(ser))



def find_baudrate():
    """
        To autofind the correct baudrate of the device
    """
    
    print(Fore.CYAN + "+------------------------+")
    print(Fore.CYAN + "|    AUTOFIND BAUDRATE   |")
    print(Fore.CYAN + "+------------------------+")

    
    test_serial = serial.Serial("/dev/ttyS0")
    
    baudrates = [1200, 1800, 2400, 4800, 9600, 38400, 19200, 57600, 115200]
    final_baudrate = 0
    
    for baud in baudrates:
        
        try:
            print(Fore.YELLOW + "Testing " + str(baud) + "->", end = " ")
            test_serial.baudrate = baud
            read_data(test_serial)
            
            final_baudrate = baud
            print(Fore.GREEN + "OK")
            
        except Exception as e: 
            print(Fore.RED + "No valid")
            pass
            
    if final_baudrate != 0:
        print(Fore.GREEN + "\n\nFound baudrate: " + str(final_baudrate))
 
 
    return final_baudrate


def get_terminal(ser):
    command = ""
    
    while command != "exit from terminal":
        command = input(">>")
        print(send_command(ser, command))
        
        
def check_if_terminal(ser):
    """
        Check if a terminal responds 
    """
    
    response = send_command(ser, "echo hola")
    
    if "hola" in response:
        print(Fore.GREEN + "\n     Got terminal :)")
        return True
    
    else:
        print(Fore.RED + "\nNo terminal :(")
        return False



def ducks():
    print(Fore.CYAN +
        """
          _      _      _
        <(.)__ <(.)__ <(.)__
         (___/  (___/  (___/..........
        """)

def main():
    
    baudrate = find_baudrate()
    
    if baudrate != 0: 
        ser = serial.Serial ("/dev/ttyS0", baudrate)    
        
        print("\n[] - Please wait 10 seconds just to be sure the device is fully booted")
        sleep(10)
        
        print("[] - Checking if there is terminal access")
        
        if check_if_terminal(ser):
            response = input("\nDo you want to open the terminal? (Y/N) ")
            
            if response.upper() == "Y":
                get_terminal(ser)
                
            
            print(Fore.CYAN + "\n\nBye bye...")
            ducks()
            
    
    else:
        print(Fore.RED + "No valid baudrate found, quitting the program..." )



if __name__ == "__main__":
    main()




    


