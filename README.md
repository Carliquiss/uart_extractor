# Raspberry Pi Router UART Hacking 💻
_A tool to connect a Raspberry Pi to a router through UART obtaining a shell_

## ⚙️ How does it works 

The Raspberry Pi has an UART interface on the GPIO (on Raspbian it can be accessed on /dev/ttyS0 by default) which can be used to connect to a Router with another UART interface (usually obtaining a shell if it's not protected). This tool allows to detect automatically the baudrate of the router in order to get a shell on the device. It also tries to upload a full version of BusyBox (with netcat included) to establish a reverse shell in the IP and Port specified, gets some useful information (like the user, the partitions that exists on the device and the BusyBox version that the router has). Finally, it tries to extract the rootfs partition so it can be analyzed without having to be connected to the router and send some information to a Backend (in this repo you can find the Backend configuration and all the info: https://github.com/Carliquiss/controlboard) to store it on a DB. 

## 🔧 Installing 
First clone the repo: 
```
git clone https://github.com/Carliquiss/uart_extractor
```
Then run the following command to install needed libs:
```
pip3 install -r requirements.txt
```

## ⌨️ Modes 
There are three modes: 

 * **Automatic**: To automatically detect the baudrate of the router and extract all the information explained in the "How does it works" section, inluding uploading the BusyBox binary to the router and extracting the rootfs partition. 
 * **Direct**: Similar to automatic mode, but user has to specify the baudrate. 
 * **Terminal**: If the user only wants to get a terminal on the router knowing the baudrate. 
 
 ## 🚀 Usage 
I recommend that you first view the run.sh file. But if you want to run any of the modes directly with python:
 * Automatic mode: 
```
sudo python3 main.py -a
```
 * Direct mode: 
```
sudo python3 main.py -d 57600 (router baudrate)
```
 * Terminal mode: 
```
sudo python3 main.py -t 57600 (router baudrate)
```
