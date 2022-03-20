from inspect import _void


class Datagram:
    def __init__(self):
        self.HEAD  = b''
        self.PAYLOAD = b''
        self.EOP = 0xAABBCCDD.to_bytes(4,byteorder="big")
        self.currentPack = 0
        self.dataSize  =  0

    def head(self,tipo,origem,destino,numberOfPackages=0,fileId=0,packRestart=0, sucessPack=0, crc=0) ->_void:
        """
        Recebe inteiro, devolve em byte
        header:
        0-tipo [1:Handshake Client, 2:Handshake Server,3:Envio de dados,4:Dados recebidos corretamente,5:Timeout error,6:Package Error],
        1-ID origem [16:Client, 18:Server],
        2-ID destino [18:Server, 16:Client],
        3-pacotes a serem enviados [número n],
        4-numero do pacote atual [entre 0 e n-1, dado n pacotes],
        5-se HANDSHAKE:id do arquivo; se DADOS:quantidade de bytes no payload atual [entre 0 e 114],
        6-pacote solicitado para recomeço
        7-último pacote recebido com sucesso
        8-CRC
        9-CRC
        """
        self.tipo  = tipo.to_bytes(1,byteorder="big")
        self.origem =  origem.to_bytes(1,byteorder="big")
        self.destino = destino .to_bytes(1,byteorder="big")
        self.numberOfPackages = numberOfPackages.to_bytes(1,byteorder="big")
        currentPack = self.currentPack.to_bytes(1,byteorder="big")
        datasize = self.dataSize.to_bytes(1,byteorder="big")
        fileId = fileId.to_bytes(1,byteorder="big")
        packRestart = packRestart.to_bytes(1,byteorder="big")
        sucessPack = sucessPack.to_bytes(1,byteorder="big")
        crc = crc.to_bytes(2,byteorder="big")

        if self.tipo != 1 or self.tipo !=2:
            self.HEAD = self.tipo+self.origem+self.destino+self.numberOfPackages+currentPack+datasize+packRestart+sucessPack+crc
        else:
            self.HEAD = self.tipo+self.origem+self.destino+self.numberOfPackages+currentPack+fileId+packRestart+sucessPack+crc

    def payload(self, payload) ->_void:
        """Método de definição do payload em um pacote"""
        self.PAYLOAD = payload
        self.dataSize = len(payload)

    def nextPackage(self) ->_void:
        """Método de incrementação no pacote atual a ser enviado"""
        self.currentPack+=1 

    def packIndexError(self,index):
        self.PAYLOAD = index.to_bytes(1,byteorder="big")

    def datagram(self) -> bytes:
        """Método de criação do datagrama conforme especificado"""
        finalDatagram = self.HEAD+self.PAYLOAD+self.EOP
        try:
            assert len(finalDatagram)<=128
            return finalDatagram
        except:
            print("Tamanho acima do esperado")
            return b''
         
    
