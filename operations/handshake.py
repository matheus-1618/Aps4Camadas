from inspect import _void
from operations.datagram import Datagram
from termcolor import colored
import os
os.system('color')
import time

class Handshake:
    def __init__(self, origem, com, fileId):
        self.origem = origem
        self.numberOfPackages = 0
        self.com = com
        self.fileId = fileId
        self.totalPackets = 0
        self.datagram = Datagram()

    def __buildHandshake(self)->_void:
        "Constroi o handshake para envio, método privado"
        if self.origem=="client":
            self.datagram.head(1,16,18,numberOfPackages=self.numberOfPackages,fileId=self.fileId)
            self.datagram.payload(bytes([self.fileId]))
        elif self.origem=="server":
            self.datagram.head(2,18,16,fileId=self.fileId)
            self.datagram.payload(bytes([self.fileId]))
        
    def contact_server(self, numberOfPackages) ->_void:
        "Envia handshake para server"
        self.numberOfPackages = numberOfPackages
        self.__buildHandshake()
        """Client envia mensagem de inicio de conexão para o server"""
        print(colored("\n---------------->Convidando servidor para conexão\n","blue"))
        self.com.sendData(self.datagram.datagram())
        time.sleep(.5)

    def contact_client(self) ->_void:
        """Server envia mensagem de inicio de conexão para o server, confirmando conexão"""
        self.__buildHandshake()
        print(colored("\n---------------->Enviando confirmação de recebimento ao Client\n","blue"))
        self.com.sendData(self.datagram.datagram())
        time.sleep(.5)

    def get_total_packets(self)->int:
        """Retorna o total de pacotes a serem enviados para o server"""
        return self.totalPackets

    def receive_handshake(self)->bool:
        """Organiza recepção do handshake de acordo com a origem do envio"""
        data,_ = self.com.getData(15)
        if data==[-1]:
            return False

        if self.origem=="server":
            if data[0]==1 and data[1]==16 and data[2]==18 and data[10]==self.fileId:
                self.totalPackets = data[3]
                print(colored("\n---------------->Handshake Recebido com sucesso!\n","green"))
                return True
            return False

        else:
            if data[0]==2 and data[1]==18 and data[2]==16 and data[10]==self.fileId:
                print(colored("\n---------------->Handshake Enviado com sucesso!\n","green"))
                return True
            return False







