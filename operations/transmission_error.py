from inspect import _void
from operations.datagram import Datagram
import time

class Error:
    def __init__(self,com):
        self.datagram = Datagram()
        self.com = com

    def __buildError(self,index)->_void:
        "Constroi o pacote de erro para envio ao client, método privado"
        self.datagram.head(6,18,16,packRestart=index)
    
    def send_error(self,index) ->_void:
        """Envia ao client a mensagem avisando do erro e o pacote de renicio"""
        self.__buildError(index)
        self.com.sendData(self.datagram.datagram())
        time.sleep(.5)