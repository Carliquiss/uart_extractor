class Device:
    
    #Atributos
    name = "device"
    baudrate = 0
    terminal = False
    extra_info = {}
    
    
    def __str__(self):
        """
            Override de print
        """
        output = "Name: " + name + "\n"
        output += "Baudrate: " + str(baudrate) + "\n"
        output += "Terminal:" + str(terminal) + "\n"
        
        return output
    
    #Metodos set/get
    def set_name(self, new_name):
        self.name = new_name
        
    def get_name(self):
        return self.name
    
    def set_baudrate(self, new_baud):
        self.baudrate = new_baud
    
    def get_baudrate(self):
        return self.baudrate
    
    def set_terminal(self):
        self.terminal = True
        
    def if_terminal(self):
        return self.terminal
    
    def add_info(self, key, value): 
        extra_info[key] = value