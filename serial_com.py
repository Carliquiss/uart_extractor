import serial
import re
import sys
import os

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
        Parse output from read_data to delete ansi code
    """
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    result = ansi_escape.sub('', output).replace("\r", "")
    
    final_output = ""
    for line in result.split("\n"):
        if line == "" or line == "[root@OpenWrt]" or line == "/ # ":
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
        For autofinding the correct baudrate of the device (reads the terminal ports until there are valid ascii code on it)
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
            print(Fore.RED + "Not valid")
            
            
    if final_baudrate != 0:
        
        if valid_baudrates != 1: 
            print("\n\n" + Back.RED + "Found multiple valid baudrates, possible error but It will try with the last baudrate found (usually it is the correct one)")
        
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
        print(Fore.GREEN + " ------> Got terminal ✓\n")
        return True
    
    else:
        print(Fore.RED + " ------> No terminal X")
        return False



def ducks():
    print(Fore.CYAN + "\n\nBye bye...")
    print(Fore.CYAN +
        """
          _      _      _
        <(.)__ <(.)__ <(.)__
         (___/  (___/  (___/..........
        """)


def find_user(ser):
    user_info = send_command(ser, "id")
    
    if "found" in user_info.split():
        user_info = send_command(ser, "echo $USER")

    
    return user_info.split("\n")[0]



def print_info(info):
    
    for item in info:
        try: 
            print(Fore.YELLOW + item + ": " + Fore.WHITE + info[item])
            
        except:
            pass



def check_services(ser):
    """
        Check if differents services as ssh exist on the device
    """
    print(Back.CYAN + "\n")
    print(Fore.CYAN + "+------------------------+")
    print(Fore.CYAN + "|    CHECKING SERVICES   |")
    print(Fore.CYAN + "+------------------------+")
    
    services_info = {}
    usr_bin = send_command(ser, "ls /usr/bin/")
    
    if "ssh" in usr_bin.split():
        
        print(Fore.GREEN + "-----> SSH FOUND ✓")
        services_info["ssh"] = True
    
    else:
        print(Fore.RED + "-----> NO SSH FOUND X")
        services_info["ssh"] = False


    if "scp" in usr_bin.split():
        
        print(Fore.GREEN + "-----> SCP FOUND ✓")
        services_info["scp"] = True
    
    else:
        print(Fore.RED + "-----> NO SCP FOUND X")
        services_info["scp"] = False
        
        
    
    lighttpd_info = send_command(ser, "ls /etc/lighttpd/lighttpd2.conf")
    
    if "/etc/lighttpd/lighttpd2.conf" in lighttpd_info.split("\n"):
        
        print(Fore.GREEN + "-----> LIGHTTPD FOUND ✓")
        services_info["lighttpd"] = True
    
    else:
        print(Fore.RED + "-----> NO LIGHTTPD FOUND X")
        services_info["lighttpd"] = False
        
    
    return services_info
        


def get_info(ser):
    """
        Execute differents commands to get general info about the device
    """
    
    print(Back.CYAN + "\n") 
    print(Fore.CYAN + "+------------------------+")
    print(Fore.CYAN + "|  CHECKING DEVICE INFO  |")
    print(Fore.CYAN + "+------------------------+")
    
    device_info = {}
    
    device_info["system"]     = send_command(ser, "uname -a").split("\n")[0]
    device_info["user"]       = find_user(ser)
    device_info["partitions"] = send_command(ser, "cat /proc/mtd")
    device_info["busybox"]    = send_command(ser, "busybox")    
    
    return device_info
    


def extract_rootfs(ser):
    
    partitions_info = send_command(ser, "cat /proc/mtd").split("\n")    
    
    for partition in partitions_info: 
        partition = partition.split()
        
        if len(partition) == 4:
            
            dev = partition[0].replace(":","")
            name = partition[3].replace('"',"")
            
            if name == "rootfs":
                partition_block = "mtdblock" + dev[-1]
                send_command(ser, "dd if=/dev/" + partition_block + " of=/tmp/" + name + ".bin bs=4096")
            


def mod_lighttpd(ser):
    """
        If lighttpd is installed in the system, this method change the settings to mount /tmp folder in order to read/write easily on the device
    """
    
    line_to_mod = send_command(ser, "cat /etc/lighttpd/lighttpd2.conf | grep server.upload-dirs").split("\n")[0]
    send_command(ser, "cp /etc/lighttpd/lighttpd2.conf /etc/lighttpd/lighttpd2.conf.old")
    send_command(ser, """sed 's#{}#server.upload-dirs          = ( "/tmp" )#' /etc/lighttpd/lighttpd2.conf > /etc/lighttpd/modded_lighttd2.conf""".format(line_to_mod))
    send_command(ser, "cp /etc/lighttpd/modded_lighttd2.conf /etc/lighttpd/lighttpd2.conf")
        
    line_to_check = send_command(ser, "cat /etc/lighttpd/lighttpd2.conf | grep server.upload-dirs").split("\n")[0]
    
    if line_to_check == """server.upload-dirs          = ( "/tmp" )""":
        print(Fore.CYAN + "Lighttp modded to mount /tmp")
        
    else:
        print(Fore.RED + "Some errors during the process of trying to mount /tmp")
            


def check_networking(ser):
    os.system("ifconfig eth0")


def scp_to_raspi(ser):
    
    send_command(ser, "scp /tmp/rootfs.bin pi@{}:/home/pi/")
    
    

def test_mode():
    
    try: 
        baudrate = sys.argv[2]
        print(Fore.GREEN + "Baudrate: " + baudrate)
        
        ser = serial.Serial ("/dev/ttyS0", baudrate)
        
        if check_if_terminal(ser):
                        
            servicios = check_services(ser)
            
            print_info(get_info(ser))
            print_info(servicios)
            
            extract_rootfs(ser)
            
            if servicios["scp"]:
                print("Copying rootfs partition to the Raspberry Pi")  
        
            get_terminal(ser)
            ducks()
    
    except Exception as error:
        print(Fore.RED + "Bad argument")
        print(error)



def direct_terminal_mode():
    
    try: 
        baudrate = 57600
        print(Fore.GREEN + "Baudrate: " + baudrate)
        
        ser = serial.Serial ("/dev/ttyS0", baudrate)
        
        print_info(get_info(ser))
        print_info(check_services(ser))
        
        get_terminal(ser)
        ducks()
    
    except Exception as error:
        print(Fore.RED + "Bad argument")
        print(error)
    
    


def auto_mode():

    baudrate = find_baudrate()
    
    ser = serial.Serial ("/dev/ttyS0", baudrate)
        
    if baudrate != 0:         
            
            
        print("\n● Please wait 30 seconds just to be sure the device is fully booted")
        sleep(30)
            
        print("● Checking if there is terminal access:", end = "")
            
        if check_if_terminal(ser):
                        
            servicios = check_services(ser)
            
            print_info(get_info(ser))
            print_info(servicios)
            
            extract_rootfs(ser)
            
            if servicios["scp"]:
                print("Copying rootfs partition to the Raspberry Pi")  
                
            response = input("\nDo you want to open the terminal? (Y/N) ")
                
            if response.upper() == "Y":
                get_terminal(ser)                
                
            ducks()
        
    else:
        print(Fore.RED + "No valid baudrate found, quitting the program..." )



def main():
    
    if len(sys.argv) >= 2:
        
        if sys.argv[1] == "-t" or sys.argv[1] == "--terminal":
            direct_terminal_mode()
        
        if sys.arv[1] == "-d" or sys.argv[1] == "--debug":
            test_mode()
        
    else: 
        auto_mode()



if __name__ == "__main__":
    main()




    


