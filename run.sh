
#Set netcat to listen on background in order to get rootfs partition
nc -lp 4445 > rootfs.bin &

#Run the script in automatic mode
sudo python3 main.py -a


#If you want to run it on other modes:

#To use direct mode: 		sudo python3 main.py -d 57600 (router naudrate)
#To get just a terminal: 	sudo python3 main.py -t 57600 (router baudrate)

