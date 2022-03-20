from inspect import _void
from operations.datagram import Datagram
import time

class Timeout:
    def __init__(self,origem,com):
        self.datagram = Datagram()
        self.origem = origem 
        self.com = com

    def __buildTimeout(self)->_void:
        "Constroi o Timeout para envio, método privado"
        if self.origem=="client":
            self.datagram.head(5,16,18)
        elif self.origem=="server":
            self.datagram.head(5,18,16)
    
    def send_error(self)->_void:
        self.__buildTimeout()
        self.com.sendData(self.datagram.datagram())
        time.sleep(.05)