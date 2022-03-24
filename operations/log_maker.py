from operations.datagram import Datagram

from inspect import _void

class Log:
    def __init__(self,origem):
        self.origem = origem

    def build(self,situation,content)->_void:
        """Cria arquivo de log"""
        with open(f"logs/{self.origem}{situation}.txt","w") as log:
            log.write(content)
        