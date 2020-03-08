import serial
import re

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
   
    
def parse_output(output):
    """
        Parse output from read_data if there is ansi code
    """
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    result = ansi_escape.sub('', output).replace("\r", "")
    
    final_output = ""
    for line in result.split("\n"):
        if line == "" or line == "[root@OpenWrt]":
            pass
        else:
            final_output += line + "\n"
            
    return final_output
            
    
            

def send_command(ser, command):
    """
        Send any command and get the result
    """
    write_data(ser, command)
    return parse_output(read_data(ser))



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
    
    valid_baudrates = 0
    for baud in baudrates:
        
        try:
            print(Fore.YELLOW + "Testing " + str(baud) + "->", end = " ")
            test_serial.baudrate = baud
            read_data(test_serial)
            
            final_baudrate = baud
            print(Fore.GREEN + "OK")
            valid_baudrates += 1
            
        except Exception as e: 
            print(Fore.RED + "No valid")
            
    if final_baudrate != 0:
        
        if valid_baudrates != 1: 
            print("\n\n" + Back.RED + "Found multiple valid baudrates, possible error but It will try with the last baudrate found")
        
        print(Fore.GREEN + "\n\nBaudrate to work with: " + str(final_baudrate))
        
    else:
        
        final_baudrate = 0
 
 
    return final_baudrate


def get_terminal(ser):
    """
        Gives the user access to the device terminal
    """
    command = ""
    
    while command != "exit from terminal":
        command = input(">> ")
        print(send_command(ser, command), end = "")
        
        
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



def get_info(ser):
    
    system_info     = send_command(ser, "uname -a")
    user_info       = send_command(ser, "id")
    partitions_info = send_command(ser, "cat /proc/mtd")
    binaries_info   = send_command(ser, "ls /bin")
    busybox_info    = send_command(ser, "busybox")
    
        
    print(Fore.YELLOW + "System: " + Fore.WHITE + system_info)
    print(Fore.YELLOW + "User and Group: " + Fore.WHITE + user_info)
    print(Fore.YELLOW + "Partitions: " + Fore.WHITE + partitions_info)
    #print(Fore.YELLOW + "Binaries: " + Fore.WHITE + binaries_info)
    print(Fore.YELLOW + "Busybox: " + Fore.WHITE + busybox_info)
        


def mod_lighttpd(ser):
    
    result = send_command(ser, "ls /etc/lighttpd/lighttpd2.conf")
    
    if "/etc/lighttpd/lighttpd2.conf" in result.split("\n"):
        print(Fore.GREEN + "Found lighttpd service")
        
        line_to_mod = send_command(ser, "cat /etc/lighttpd/lighttpd2.conf | grep server.upload-dirs").split("\n")[0]
        send_command(ser, "cp /etc/lighttpd/lighttpd2.conf /etc/lighttpd/lighttpd2.conf.old")
        send_command(ser, """sed 's#{}#server.upload-dirs          = ( "/tmp" )#' /etc/lighttpd/lighttpd2.conf > /etc/lighttpd/modded_lighttd2.conf""".format(line_to_mod))
        send_command(ser, "cp /etc/lighttpd/modded_lighttd2.conf /etc/lighttpd/lighttpd2.conf")
        
        line_to_check = send_command(ser, "cat /etc/lighttpd/lighttpd2.conf | grep server.upload-dirs").split("\n")[0]
    
        if line_to_check == """server.upload-dirs          = ( "/tmp" )""":
            print(Fore.CYAN + "Lighttp modded to mount /tmp")
        
        else:
            print(Fore.RED + "Some errores during the process of trying to mount /tmp")
            
    
    else:
        print(Fore.RED + "No lighttpd service found")
    


def main():
    
    
    baudrate = find_baudrate()
    
    if baudrate != 0:
        
        ser = serial.Serial ("/dev/ttyS0", baudrate)    
        
        print("\n[] - Please wait 15 seconds just to be sure the device is fully booted")
        sleep(15)
        
        print("[] - Checking if there is terminal access")
        
        if check_if_terminal(ser):
            
            get_info(ser)
            mod_lighttpd(ser)
            
            response = input("\nDo you want to open the terminal? (Y/N) ")
            
            if response.upper() == "Y":
                get_terminal(ser)
                
            
            print(Fore.CYAN + "\n\nBye bye...")
            ducks()
            
    
    else:
        print(Fore.RED + "No valid baudrate found, quitting the program..." )



if __name__ == "__main__":
    main()




    


