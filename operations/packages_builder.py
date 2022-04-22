from inspect import _void
from operations.datagram import Datagram
from crc16 import crc16xmodem #linux 
from crccheck.crc import Crc16 #Windows ou mac
class PackageBuilder:
    def __init__(self,filepath):
        self.filepath = filepath
        self.bytearray = b''
        self.totalSize = 0
        self.numberOfPayloads = 0
        self.lastPayloadsize = 0
        self.datagram = Datagram()
        self.payloads = []
        self.datagrams = []

    def __buildPayloads(self) ->_void:
        """Constroi lista fracionada do arquivo a ser enviado pelos pacotes de acordo
        com o tamanho máximo de cada payload"""
        with open(self.filepath,"rb") as bytearray:
            bytearray = bytearray.read()
            self.bytearray = bytearray
        self.totalSize = len(self.bytearray)

        if self.totalSize%114 ==0:
            self.numberOfPayloads = int(self.totalSize/114)
        else:
            self.numberOfPayloads = int(self.totalSize/114)+1
            self.lastPayloadsize = self.totalSize - int(self.totalSize/114)*114

        self.__fracionatePayloads()

    def __fracionatePayloads(self) ->_void:
        """Função auxiliar para fracionar os bytes de um arquivo na quantidade de pacotes
        desejados ao envio"""
        for i in range(0,self.numberOfPayloads):
            self.payloads.append(self.bytearray[114*i:114*(i+1)])
    
    def build(self) ->list:
        """Função que monta os envios de datagramas em vários pacotes do arquivo enviado"""
        self.__buildPayloads()
        for i in range(0,self.numberOfPayloads):
            self.datagram.payload(self.payloads[i])
            crc = crc16xmodem(self.payloads[i]).to_bytes(2,byteorder="big")
            #crc = Crc16.calc(self.payloads[i]).to_bytes(2,byteorder="big")
            self.datagram.head(3,16,18,numberOfPackages=self.numberOfPayloads,crc=crc)
            pack = self.datagram.datagram()
            self.datagrams.append(pack)
            self.datagram.nextPackage()
        return self.datagrams