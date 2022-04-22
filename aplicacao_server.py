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
from datetime import datetime
import os
from termcolor import colored
os.system('color')
from inspect import _void
import operations.datagram as datagram
from operations.handshake import Handshake
from operations.correct_pack import CorrectPack
from operations.log_maker import Log
from operations.timeout_error import Timeout
from operations.transmission_error import Error
from crc16 import crc16xmodem #linux 
from crccheck.crc import Crc16 #Windows ou mac

#   python3 -m serial.tools.list_ports

#use uma das 3 opcoes para atribuir à variável a porta usada
#serialName = "/dev/tty"           # Ubuntu (variacao de)
#serialName = "/dev/tty.usbmodem1411" # Mac    (variacao de)
#serialName = "COM6"                  # Windows(variacao de)
serialName = "/dev/ttyACM1"

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
        self.flag1 = True 
        self.flag2 = False
        self.flag3 = False 
        self.flag4 = False 
        self.flag5 = False
        self.bytes = b''
        self.head = b''
        self.payload = b''
        self.sizeHead = 0
        self.crc_calc = b''
        self.com1.enable()
        

    def nextPack(self)->_void:
        """Método de incrementação do pack a ser enviado"""
        self.currentPack+=1

    def setTimer(self)->_void:   
        """Método que ativa o timeout"""
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
        """Método que faz o envio do byte de sacrifício no início"""
        rxBuffer, nRx = self.com1.getData(1)
        self.com1.rx.clearBuffer()
        time.sleep(1) 

    def handShake(self)->bool:
        """Método de asserção do handshake, garantindo previamente a comunicação
        entre client e server"""
        while True:
            try:
                self.sacrifice_byte()   
                print(colored("\n---------------->Esperando handshake do Client\n","yellow"))  
                if self.handshake.receive_handshake(): 
                    self.totalPackets = self.handshake.get_total_packets()
                    time.sleep(3)
                    self.handshake.contact_client()
                    time.sleep(1)
                    print(colored("\n---------------->Iniciando Recepção\n","blue"))  
                    return True
                else:
                    print(colored("\n---------------->Tempo de requisição esgotado!\n","red"))
                    self.flag1 = False 
                    self.flag3 = True
                    self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /envio(timeout)/5/{14}\n'
                    self.com1.disable()
                    raise Exception

            except KeyboardInterrupt:
                    print(colored("\n---------------->Interrupção Forçada","red"))
                    self.com1.disable()
                    break

            except Exception as erro:
                print(erro)
                self.com1.disable()
                break   

    def writeLog(self):
        """Escreve o log de informação de acordo com a situaão ocorrida"""
        print(colored("\n---------------->Criando arquivos de log\n","cyan"))
        if self.flag1:
            self.log.build(1,self.log_content)
        if self.flag2:
            self.log.build(2,self.log_content)
        if self.flag3:
            self.log.build(3,self.log_content)
        if self.flag4:
            self.log.build(4,self.log_content)
        if self.flag5:
            self.log.build(5,self.log_content)

    def sendAcknowledge(self,status)->_void:
        """Método de envio da mensagem de Acknowledge, confirmando se o pacote foi bem recebido
        ou solicitando um possível reenvio"""
        if status=="sucesso":
            self.nextPack()
            self.correctPack.send_confirmation(self.currentPack)
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /receb/3/{len(self.head+self.payload+self.EOP)}\n'
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /envio/4/{14}\n'
        elif status=="ultimo":
            print(colored("[Tipo 4]Último Pacote recebido com sucesso\n","red"))
            self.correctPack.send_confirmation(self.currentPack)
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /receb/3/{len(self.head+self.payload+self.EOP)}\n'
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /envio/4/{14}\n'
            time.sleep(0.8)
        elif status=="sizeError":
            print(colored(f"\n---------------->Recebi algo maior que os {self.sizepayload} bytes esperados...","red"))
            print(colored("\n---------------->Por favor reenvie...\n","red"))
            self.flag1 = False 
            self.flag2 = True
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /receb/3/{len(self.head+self.payload+self.EOP)}\n'
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /envio/6/{14}\n'
            self.error.send_error(self.currentPack)
            self.com1.rx.clearBuffer()
            time.sleep(1)
        elif status=="crcError":
            print(colored(f"\n---------------->CRC ERRADO.\nESPERADO: {self.head[8:10]}\nCALCULADO: {self.crc_calc}","red"))
            print(colored("\n---------------->Por favor reenvie...\n","red"))
            self.flag1 = False 
            self.flag2 = True
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /receb/3/{len(self.head+self.payload+self.EOP)}\n'
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /envio/6/{14}\n'
            self.error.send_error(self.currentPack)
            self.com1.rx.clearBuffer()
            time.sleep(1)
        elif status=="packError":
            print(colored(f"---------------->Pacote recebido: {self.head[4]+1}","red"))
            print(colored(f"---------------->Pacote esperado: {self.currentPack+1}","red"))
            print(colored("---------------->Por favor reenvie\n","red"))
            self.flag1 = False 
            self.flag2 = True
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /receb/3/{len(self.head+self.payload+self.EOP)}\n'
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /envio/6/{14}\n'
            self.error.send_error(self.currentPack)
            self.com1.rx.clearBuffer()
            time.sleep(1)
        elif status=="repete":
            self.correctPack.send_confirmation(self.currentPack-1)


    def check_current_Pack_is_Right(self)->bool:
        """Método verificação se o pacote informado no head corresponde ao esperado"""
        return self.head[4]==self.currentPack and self.head[0]==3

    def check_crc(self)->bool:
        self.crc_calc = crc16xmodem(self.payload).to_bytes(2,byteorder="big")
        #self.crc_calc = Crc16.calc(self.payload).to_bytes(2,byteorder="big")
        return self.crc_calc == self.head[8:10]
            

    def check_EOP_in_right_place(self)->bool:
        """Método de verificação da posição do EOP"""
        return self.eop == datagram.Datagram().EOP

    def check_if_is_the_last_pack(self)->bool:
        """Método de verificação se é o último pacote a ser receber"""
        return self.totalPackets==self.currentPack+1

    def mountFile(self)->_void:
        """Método de montagem dos bytes para formação do arquivo"""
        print(colored("---------------->Salvando dados no arquivo","cyan"))
        f = open(file,'wb')
        f.write(self.bytes)
        f.close()

    def receiveFile(self)->_void:
        """Método main. Utiliza todos os métodos acima de maneira a cumprir o propósito do
        projeto"""
        if self.handShake():
            while True:
                try:
                    print(colored(f"[Tipo 3]Recebendo pacote n°{self.currentPack+1}...","blue"))
                    self.readHead()
                    if self.head == [-1]:
                        print(colored("\n---------------->Tempo de requisição esgotado!","red"))
                        self.flag1 = False 
                        self.flag4 = True
                        self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /envio(timeout)/5/{14}\n'
                        self.timeout.send_error()
                        self.com1.disable()
                        raise Exception

                    elif self.head == [-2]:
                        time.sleep(1)
                        self.timerFlag = True
                        self.flag1 = False 
                        self.flag5 = True
                        self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /reenvio(fios retirados)/4/{14}\n'
                        self.correctPack.send_confirmation(self.currentPack-1,restart=True)
                    elif self.head[0]==5:
                        print(colored("\n---------------->Tempo de requisição esgotado!","red"))
                        self.flag1 = False 
                        self.flag4 = True
                        self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /receb(timeout)/5/{14}\n'
                        self.com1.disable()
                        raise Exception
                         
                    elif self.check_current_Pack_is_Right():
                        self.timerFlag=False
                        self.readPayload()
                        self.readEOP()

                        if not self.check_crc():
                            self.sendAcknowledge("crcError")
                            continue
                        
                        if self.check_if_is_the_last_pack():
                            if self.check_EOP_in_right_place():
                                self.sendAcknowledge("ultimo")
                                self.bytes+=self.payload
                                print(colored("\n---------------->Encerrando Comunicação...\n","red"))
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
                    print("\n---------------->Interrupção Forçada")
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
    s.writeLog()
