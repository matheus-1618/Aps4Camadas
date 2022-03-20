from inspect import _void
from operations.datagram import Datagram

import time

class CorrectPack:
    def __init__(self, com):
        self.payload = Datagram()
        self.datagram = b''
        self.com = com

    def __build(self,packIndex):
        "Constroi a mensagem de resposta de sucesso de recebimento dos pacotes enviados ao server"
        self.payload.head(4,18,16,sucessPack=packIndex)
        self.datagram = self.payload.datagram()
    
    def send_confirmation(self,packIndex, restart=False) ->_void:
        """Envia confirmação do recebimento adequado"""
        self.__build(packIndex)
        if restart:
            print(f"[yellow]REENVIANDO: Dados recebidos adequadamente! Envio do pacote {packIndex+1} aprovado!")
        else:
            print(f"[yellow]Dados recebidos adequadamente! Envio do pacote {packIndex+1} aprovado!")
        self.com.sendData(self.datagram)
        time.sleep(.5)