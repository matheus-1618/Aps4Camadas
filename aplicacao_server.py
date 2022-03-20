#!/usr/bin/env python3
#####################################################
# Camada Física da Computação
#Carareto
#11/08/2020
#Aplicação
####################################################

#esta é a camada superior, de aplicação do seu software de comunicação serial UART.
#para acompanhar a execução e identificar erros, construa prints ao longo do código! 


from server.enlace import *
import time
from rich import print
from inspect import _void
import operations.datagram as datagram
from operations.handshake import Handshake
from operations.correct_pack import CorrectPack
from operations.log_maker import Log
from operations.timeout_error import Timeout
from operations.transmission_error import Error

#   python3 -m serial.tools.list_ports

#use uma das 3 opcoes para atribuir à variável a porta usada
#serialName = "/dev/tty"           # Ubuntu (variacao de)
#serialName = "/dev/tty.usbmodem1411" # Mac    (variacao de)
serialName = "COM5"                  # Windows(variacao de)

jsonfile = "./files/recebido.json"
pngfile = "./files/recebido.png"

file = pngfile
class Server:
    def __init__(self,serialname):
        self.EOP = 0xAABBCCDD.to_bytes(4,byteorder="big")
        self.port = serialname
        self.com1 = enlace(self.port)
        self.currentPack = 0
        self.totalPackets = 0
        self.datagrams = []
        self.timerFlag = False
        self.handshake = Handshake("server",self.com1,10)
        self.correctPack = CorrectPack(self.com1)
        self.error = Error(self.com1)
        self.timeout = Timeout("server",self.com1)
        self.log = Log("Server")
        self.log_content = ""
        self.bytes = b''
        self.head = b''
        self.sizeHead = 0
        self.com1.enable()
        

    def nextPack(self)->_void:
        """Método de incrementação do pack a ser enviado"""
        self.currentPack+=1

    def setTimer(self)->_void:
        if not self.timerFlag:
            self.timer2 = time.time()

    def readHead(self)->_void:
        """Método que realiza leitura do head do pacote recebido"""
        self.setTimer()
        self.head,self.sizeHead = self.com1.getData(10,timer1 = True, timer2 = self.timer2)
        
    def readPayload(self)->_void:
        """Método que realiza leitura do payload do pacote recebido"""
        self.payload,self.sizepayload = self.com1.getData(self.head[5])

    def readEOP(self)->_void:
        """Método que realiza leitura do EOP do pacote recebido"""
        self.eop,sizeeop = self.com1.getData(4)

    def sacrifice_byte(self)->_void:
        rxBuffer, nRx = self.com1.getData(1)
        self.com1.rx.clearBuffer()
        time.sleep(1) 

    def handShake(self)->bool:
        """Método de asserção do handshake, garantindo previamente a comunicação
        entre client e server"""
        while True:
            try:
                self.sacrifice_byte()   
                print("[yellow]\n-----Esperando handshake do Client-----\n")  
                if self.handshake.receive_handshake(): 
                    self.totalPackets = self.handshake.get_total_packets()
                    self.handshake.contact_client()
                    time.sleep(1)
                    print("[blue]\n--------------------------")
                    print("[blue]Iniciando Recepção")
                    print("[blue]--------------------------\n")
                    return True
                    
                else:
                    print("[red]Recebi algo estranho...")
                    self.com1.disable()
                    return False   

            except KeyboardInterrupt:
                    print("[red]Interrupção Forçada")
                    self.com1.disable()
                    break

            except Exception as erro:
                print(erro)
                self.com1.disable()
                break   

    def sendAcknowledge(self,status)->_void:
        """Método de envio da mensagem de Acknowledge, confirmando se o pacote foi bem recebido
        ou solicitando um possível reenvio"""
        if status=="sucesso":
            self.nextPack()
            self.correctPack.send_confirmation(self.currentPack)
        elif status=="ultimo":
            print("Último Pacote recebido com sucesso\n")
            self.correctPack.send_confirmation(self.currentPack)
            time.sleep(0.8)
        elif status=="sizeError":
            print("\n------------------------------------------------------------")
            print("Recebi arquivo com tamanho diferente...")
            print(f"Recebi algo maior que os {self.sizepayload} bytes esperados...")
            print("Por favor reenvie...")
            print("------------------------------------------------------------\n")
            self.error.send_error(self.currentPack)
            self.com1.rx.clearBuffer()
            time.sleep(1)
        elif status=="packError":
            print("\n---------------------------------------")
            print("Recebi um pacote diferente...")
            print(f"Pacote recebido: {self.head[4]+1}")
            print(f"Pacote esperado: {self.currentPack+1}")
            print("Por favor reenvie")
            print("---------------------------------------\n")
            self.error.send_error(self.currentPack)
            self.com1.rx.clearBuffer()
            time.sleep(1)
        elif status=="repete":
            self.correctPack.send_confirmation(self.currentPack-1)


    def check_current_Pack_is_Right(self)->bool:
        """Método verificação se o pacote informado no head corresponde ao esperado"""
        return self.head[4]==self.currentPack and self.head[0]==3
            

    def check_EOP_in_right_place(self)->bool:
        """Método de verificação da posição do EOP"""
        return self.eop == datagram.Datagram().EOP

    def check_if_is_the_last_pack(self)->bool:
        """Método de verificação se é o último pacote a ser receber"""
        return self.totalPackets==self.currentPack+1

    def mountFile(self)->_void:
        """Método de montagem dos bytes para formação do arquivo"""
        print("Salvando dados no arquivo")
        f = open(file,'wb')
        f.write(self.bytes)
        f.close()

    def receiveFile(self)->_void:
        """Método main. Utiliza todos os métodos acima de maneira a cumprir o propósito do
        projeto"""
        if self.handShake():
            while True:
                try:
                    print(f"Recebendo pacote n°{self.currentPack+1}...")
                    self.readHead()
                    if self.head == [-1]:
                        print("[red]Tempo de requisição esgotado!")
                        self.timeout.send_error()
                        self.com1.disable()
                        exit() 
                    elif self.head == [-2]:
                        self.timerFlag = True
                        self.correctPack.send_confirmation(self.currentPack-1,restart=True)
                    elif self.head[0]==5:
                        print("[red]Tempo de requisição esgotado!")
                        self.com1.disable()
                        exit() 
                    elif self.check_current_Pack_is_Right():
                        self.timerFlag=False
                        self.readPayload()
                        self.readEOP()
                        if self.check_if_is_the_last_pack():
                            if self.check_EOP_in_right_place():
                                self.sendAcknowledge("ultimo")
                                self.bytes+=self.payload
                                print("Encerrando Comunicação...\n")
                                self.mountFile()
                                self.com1.disable()
                                break
                        elif self.check_EOP_in_right_place():
                            self.sendAcknowledge("sucesso")
                            self.bytes+=self.payload
                        else:
                            self.sendAcknowledge("sizeError")
                            continue
                    else:
                        self.timerFlag=False
                        self.sendAcknowledge("packError")
                        continue
                                
                except KeyboardInterrupt:
                    print("Interrupção Forçada")
                    self.com1.disable()
                    break
                except Exception as erro:
                    print(erro)
                    self.com1.disable()
                    break
                
#So roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    s = Server(serialName)
    s.receiveFile()
