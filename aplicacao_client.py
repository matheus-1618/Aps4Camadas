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
from rich import print
from inspect import _void
import operations.datagram as datagram
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
        self.caso = int(input("""Qual o caso deseja simular?
        1 - Caso de Sucesso de Transmissão ou TIMEOUT
        2 - Caso de erro de pacote
        3 - Caso de erro de tamanho do payload\n """))
        
        self.com1.enable()

    def nextPack(self)->_void:
        """Método de incrementação do pack a ser enviado"""
        self.currentPack+=1

    def sacrifice_byte(self)->_void:
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
                #time.sleep(5)
                answer = self.handshake.receive_handshake()
                if answer == "erro":
                    answer = input("\nServidor inativo. Tentar novamente? S/N ")
                    self.com1.rx.clearBuffer()
                    if answer.lower()=="s":
                        continue
                    else:
                        print("Encerrando comunicação...")
                        self.com1.disable()
                        break
                if answer:
                    print("[green]\n--------------------------")
                    print("[green]Iniciando Transmissão")
                    print("[green]--------------------------\n")
                    return True
                else:
                    print("Recebi algo estranho...")
                    self.com1.disable()
                    break

            except KeyboardInterrupt:
                    print("Interrupção Forçada")
                    self.com1.disable()
                    break
            except Exception as erro:
                print(erro)
                self.com1.disable()
                break

    
    def setTimer(self)->_void:
        if not self.timerFlag:
            self.timer2 = time.time()

    def readAcknowledge(self)->_void:
        """Método de leitura do acknowledge advindo do server, e redireciona para
        ação a se tomar"""
        self.setTimer()
        self.acknowledge,_ = self.com1.getData(14,timer1=True,timer2=self.timer2)

        if self.acknowledge == [-2]: #Caso de envio novamente do pacote por falta de inteiração do pacote
            self.timerFlag = True
            print(f"[yellow]\n\nEnviando novamente pacote nº{self.currentPack} devido ausência de resposta.")
            self.com1.sendData(self.datagrams[self.currentPack-1])
        elif self.acknowledge == [-1]: #Caso de finalizar conexão por timeout
            print("[red]Tempo de requisição esgotado!")
            self.timeout.send_error()
            self.com1.disable()
            exit() 
        elif self.acknowledge[0]==4 and self.acknowledge[1]==18 and self.acknowledge[2]==16 and self.acknowledge[-4:] == self.EOP:
            self.timerFlag = False
            self.lastSucessPack = self.acknowledge[7]
            self.sendCurrentpack()
        elif self.acknowledge[0]==6 and self.acknowledge[1]==18 and self.acknowledge[2]==16 and self.acknowledge[-4:] == self.EOP:
            self.timerFlag = False
            self.packToRestart = self.acknowledge[6]
            self.sendPackaagain()

        elif self.acknowledge[0]==5:
            print("[red]Tempo de requisição esgotado!")
            self.com1.disable()
            exit() 
        else:
            print("Ocorreu um erro bastante estranho...")
            print("Encerrando comunicação")
            self.com1.disable()
            exit() 

    def lastPack(self)->bool:
        """Método de verificação se o pacote é o último a ser enviado"""
        return self.currentPack==len(self.datagrams)

    def isPackError(self)->bool:
        """Método de verificação se é o caso de erro de envio do pacote"""
        return self.caso==2 and (self.currentPack==3 or self.currentPack==7)

    def isPayloadError(self)->bool:
        """Método de verificação se é o caso de erro de envio do tamanho do payload"""
        return self.caso==3 and self.currentPack==4
    
    def isFirstPack(self)->bool:
        """Método de verificação se o pacote é o primeiro a ser enviado"""
        return self.currentPack==0

    def casoErroPacote(self)->_void:
        """Método que implementa o caso de envio errado de um número de pacote no head
        ao esperado pelo server (em termos de sucessividade)"""
        self.acknowledge, sizeAck = self.com1.getData(10)
        if self.acknowledge == packagetool.Acknowledge().buildAcknowledge("ok")[:10]:
            self.acknowledge, sizeAck = self.com1.getData(5)
            if self.acknowledge == packagetool.Acknowledge().buildAcknowledge("ok")[10:]:
                print("Acknowledge recebido! Autorizado envio do próximo pacote!                      ")
                print(f"Enviando Pacote n°{self.currentPack+1}...             \n")
                self.com1.sendData(self.datagrams[self.currentPack+2])
                time.sleep(.8)
                self.nextPack()

    def casoErroPayload(self)->_void:
        """Método que implementa o caso de envio incorreto do tamanho do payload
        informado no head em relação ao trnasmitido no pacote"""
        self.acknowledge, sizeAck = self.com1.getData(10)
        if self.acknowledge == packagetool.Acknowledge().buildAcknowledge("ok")[:10]:
            self.acknowledge, sizeAck = self.com1.getData(5)
            if self.acknowledge == packagetool.Acknowledge().buildAcknowledge("ok")[10:]:
                print("Acknowledge recebido! Autorizado envio do próximo pacote!                      ")
                print(f"Enviando Pacote n°{self.currentPack+1}...                               \n")
                lista = list(self.datagrams[self.currentPack])
                lista[7]=36
                lista = bytes(lista)
                self.com1.sendData(lista)
                time.sleep(.8)
                self.nextPack()
    
    def sendCurrentpack(self)->_void:
        """Método de envio do pacote atual"""
        print("Acknowledge recebido! Autorizado envio do próximo pacote!                      ")
        print(f"Enviando Pacote n°{self.currentPack+1}...                               \n")
        self.com1.sendData(self.datagrams[self.currentPack])
        time.sleep(.1)
        self.nextPack()


    def sendPackaagain(self)->_void:
        """Método de reenvio do pacote alertado como enviado incorretamente ao
        servidor"""
        print("-------------------------------------------------------------------------")
        print(f"Ocorreu algum erro durante a transmissão do pacote nº {self.packToRestart}...")
        print("Reenviando ao server...")
        print("--------------------------------------------------------------------------\n")
        self.com1.sendData(self.datagrams[self.packToRestart])
        self.currentPack = self.packToRestart
        time.sleep(2)

    def sendFile(self)->_void:
        """Método main. Utiliza todos os métodos acima de maneira a cumprir o propósito do
        projeto"""
        self.buildDatagrams()
        if self.handShake():
            print(f"Estaremos enviando {len(self.datagrams)} pacotes...")
            while True:
                try:
                    if self.isFirstPack():
                        self.sendCurrentpack()

                    elif self.isPackError():
                        self.casoErroPacote()
                        
                    elif self.isPayloadError():
                        self.casoErroPayload()
                        
                    elif self.lastPack():
                        print("Último pacote enviado\n")
                        print("Encerrando comunicação...")
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

        
    #so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    c = Client(serialName,file)
    c.sendFile()
