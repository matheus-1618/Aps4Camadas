#!/usr/bin/env python3
#####################################################
# Camada Física da Computação
#Carareto
#11/08/2020
#Aplicação
####################################################

import json
from sys import argv


from client.enlace import *
import time
import os
from termcolor import colored
os.system('color')
from inspect import _void
from datetime import datetime
from operations.handshake import Handshake
from operations.packages_builder import PackageBuilder
from operations.log_maker import Log
from operations.timeout_error import Timeout

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python3 -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

#use uma das 3 opcoes para atribuir à variável a porta usada
#serialName = "/dev/tty0"           # Ubuntu (variacao de)
#serialName = "/dev/tty.usbmodem1411" # Mac    (variacao de)
serialName = "COM3"                  # Windows(variacao de)

jsonfile = "./files/notes.json"
pngfile = "./files/image.png"

file = pngfile
class Client:
    def __init__(self,serialname,filepath):
        self.EOP = 0xAABBCCDD.to_bytes(4,byteorder="big")
        self.port = serialname
        self.com1 = enlace(self.port)
        self.filepath = filepath
        self.currentPack = 0
        self.lastSucessPack = 0
        self.packToRestart = 0
        self.timer2 = time.time()
        self.timerFlag = False
        self.datagrams = []
        self.acknowledge = b''
        self.handshake = Handshake("client",self.com1,10)
        self.timeout = Timeout("client",self.com1)
        self.log = Log("Client")
        self.log_content = ""
        self.flag1 = True 
        self.flag2 = False
        self.flag3 = False 
        self.flag4 = False 
        self.flag5 = False
        self.caso = int(input("""Qual o caso deseja simular?
        1 - Caso de Sucesso de Transmissão ou TIMEOUT
        2 - Caso de erro de pacote
        3 - Caso de erro de tamanho do payload\n """))
        self.com1.enable()

    def nextPack(self)->_void:
        """Método de incrementação do pack a ser enviado"""
        self.currentPack+=1

    def sacrifice_byte(self)->_void:
        """Método de envio do byte sacríficio"""
        time.sleep(.2)
        self.com1.sendData(b'00')
        self.com1.rx.clearBuffer()
        time.sleep(1) 

    def buildDatagrams(self)->_void:
        """Método de construção dos datagramas ao receber o caminho do arquivo a ser 
        transmitido"""
        datagramsConstructor = PackageBuilder(self.filepath)
        self.datagrams = datagramsConstructor.build()

    def handShake(self)->bool:
        """Método de asserção do handshake, garantindo previamente a comunicação
        entre client e server"""
        while True:
            try:
                self.sacrifice_byte()
                self.handshake.contact_server((len(self.datagrams)))
                time.sleep(5)
                answer = self.handshake.receive_handshake()
                if answer:
                    print(colored("\n---------------->Iniciando Transmissão\n","magenta"))
                    return True
                else:
                    self.flag3 = True
                    self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /envio/1/{15}\n'
                    answer = input("\nServidor inativo. Tentar novamente? S/N ")
                    self.com1.rx.clearBuffer()
                    if answer.lower()=="s":
                        continue
                    else:
                        print("Encerrando comunicação...")
                        self.com1.disable()
                        break

            except KeyboardInterrupt:
                    print("\n---------------->Interrupção Forçada")
                    self.com1.disable()
                    break
            except Exception as erro:
                print(erro)
                self.com1.disable()
                break

    
    def setTimer(self)->_void:
        """Reseta o segundo timer"""
        if not self.timerFlag:
            self.timer2 = time.time()

    def readAcknowledge(self)->_void:
        """Método de leitura do acknowledge advindo do server, e redireciona para
        ação a se tomar"""
        self.setTimer()
        self.acknowledge,_ = self.com1.getData(14,timer1=True,timer2=self.timer2)

        if self.acknowledge == [-2]: #Caso de envio novamente do pacote por falta de inteiração do pacote
            self.timerFlag = True
            self.flag1 = False
            self.flag5=True
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /reenvio(fios retirados)/3/{len(self.datagrams[self.currentPack-1])}/{self.currentPack}\n'
            print(colored(f"\n[Tipo 3]Enviando novamente pacote nº{self.currentPack} devido ausência de resposta.\n","yellow"))
            self.com1.sendData(self.datagrams[self.currentPack-1])
        elif self.acknowledge == [-1]: #Caso de finalizar conexão por timeout
            print(colored("\n---------------->Tempo de requisição esgotado!\n","red"))
            self.timeout.send_error()
            self.flag1 = False
            self.flag4 = True
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /envio(timeout)/5/{14}\n'
            raise Exception
        elif self.acknowledge[0]==4 and self.acknowledge[1]==18 and self.acknowledge[2]==16 and self.acknowledge[-4:] == self.EOP:
            self.timerFlag = False
            self.lastSucessPack = self.acknowledge[7]
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /receb/4/{len(self.acknowledge)}\n'
            self.sendCurrentpack()
        elif self.acknowledge[0]==6 and self.acknowledge[1]==18 and self.acknowledge[2]==16 and self.acknowledge[-4:] == self.EOP:
            self.flag2 = True 
            self.flag1 = False
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /receb/6/{len(self.acknowledge)}\n'
            self.timerFlag = False
            self.packToRestart = self.acknowledge[6]
            self.sendPackaagain()

        elif self.acknowledge[0]==5:
            print(colored("---------------->Tempo de requisição esgotado!\n","red"))
            self.com1.disable()
            raise Exception
            
        else:
            print("---------------->Ocorreu um erro bastante estranho...")
            print("---------------->Encerrando comunicação")
            self.com1.disable()
            exit() 

    def lastPack(self)->bool:
        """Método de verificação se o pacote é o último a ser enviado"""
        return self.currentPack==len(self.datagrams)

    def isPackError(self)->bool:
        """Método de verificação se é o caso de erro de envio do pacote"""
        return self.caso==2 and (self.currentPack==7)

    def isPayloadError(self)->bool:
        """Método de verificação se é o caso de erro de envio do tamanho do payload"""
        return self.caso==3 and self.currentPack==4
    
    def isFirstPack(self)->bool:
        """Método de verificação se o pacote é o primeiro a ser enviado"""
        return self.currentPack==0

    def casoErroPacote(self)->_void:
        """Método que implementa o caso de envio errado de um número de pacote no head
        ao esperado pelo server (em termos de sucessividade)"""
        self.acknowledge,_ = self.com1.getData(14,timer1=True,timer2=self.timer2)
        if self.acknowledge[0]==4 and self.acknowledge[1]==18 and self.acknowledge[2]==16 and self.acknowledge[-4:] == self.EOP:
            self.timerFlag = False
            self.lastSucessPack = self.acknowledge[7]
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /receb/4/{len(self.acknowledge)}\n'
            self.com1.sendData(self.datagrams[self.currentPack+1])
            time.sleep(.1)
            self.currentPack-=1
            self.caso=1
            print(colored("[Tipo 4] Autorizado envio do próximo pacote!                      ",'green'))
            print(colored(f"[Tipo 3]Enviando Pacote n°{self.currentPack+1}...                               \n","blue"))
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /envio/3/{len(self.datagrams[self.currentPack])}/{self.currentPack+1}\n'

    def casoErroPayload(self)->_void:
        """Método que implementa o caso de envio incorreto do tamanho do payload
        informado no head em relação ao trnasmitido no pacote"""
        self.acknowledge,_ = self.com1.getData(14,timer1=True,timer2=self.timer2)
        if self.acknowledge[0]==4 and self.acknowledge[1]==18 and self.acknowledge[2]==16 and self.acknowledge[-4:] == self.EOP:
            self.timerFlag = False
            self.lastSucessPack = self.acknowledge[7]
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /receb/4/{len(self.acknowledge)}\n'
            lista = list(self.datagrams[self.currentPack])
            lista[5]=36
            lista = bytes(lista)
            self.com1.sendData(lista)
            time.sleep(.1)
            self.currentPack-=1
            self.caso=1
            print(colored("[Tipo 4] Autorizado envio do próximo pacote!                      ",'green'))
            print(colored(f"[Tipo 3]Enviando Pacote n°{self.currentPack+1}...                               \n","blue"))
            self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /envio/3/{len(self.datagrams[self.currentPack])}/{self.currentPack+1}\n'
                       
    
    def sendCurrentpack(self)->_void:
        """Método de envio do pacote atual"""
        print(colored("[Tipo 4] Autorizado envio do próximo pacote!                      ",'green'))
        print(colored(f"[Tipo 3]Enviando Pacote n°{self.currentPack+1}...                               \n","blue"))
        self.log_content+=f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} /envio/3/{len(self.datagrams[self.currentPack])}/{self.currentPack+1}\n'
        self.com1.sendData(self.datagrams[self.currentPack])
        time.sleep(.1)
        self.nextPack()


    def sendPackaagain(self)->_void:
        """Método de reenvio do pacote alertado como enviado incorretamente ao
        servidor"""
        print(colored(f"\n-->Ocorreu algum erro durante a transmissão do pacote nº {self.packToRestart}...\n[Tipo 3]Reenviando ao server...\n","red"))
        self.com1.sendData(self.datagrams[self.packToRestart])
        self.currentPack = self.packToRestart
        time.sleep(2)

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

    def sendFile(self)->_void:
        """Método main. Utiliza todos os métodos acima de maneira a cumprir o propósito do
        projeto"""
        self.buildDatagrams()
        if self.handShake():
            print(colored(f"\n---------------->Estaremos enviando {len(self.datagrams)} pacotes\n","magenta"))
            while True:
                try:
                    if self.isFirstPack():
                        self.sendCurrentpack()

                    elif self.isPackError():
                        self.casoErroPacote()
                        
                    elif self.isPayloadError():
                        self.casoErroPayload()
                        
                    elif self.lastPack():
                        print(colored("[Tipo 3]Último pacote enviado\n","yellow"))
                        print(colored("\n---------------->Encerrando Comunicação\n","red"))
                        self.com1.disable()
                        break
                    else:
                        self.readAcknowledge()
        
                except KeyboardInterrupt:
                    print("Interrupção Forçada")
                    self.com1.disable()
                    break
                except Exception as erro:
                    print(erro)
                    self.com1.disable()
                    break

if __name__ == "__main__":
    c = Client(serialName,file)
    c.sendFile()
    c.writeLog()
