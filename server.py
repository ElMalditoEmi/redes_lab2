#!/usr/bin/env python
# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Revisión 2014 Carlos Bederián
# Revisión 2011 Nicolás Wolovick
# Copyright 2008-2010 Natalia Bidart y Daniel Moisset
# $Id: server.py 656 2013-03-18 23:49:11Z bc $

import optparse
import socket
import connection
import logging
from constants import *
# Agregado
import itertools


class file():
    id_iter = itertools.count()
    def __init__(self,name=None,metadata=None):
        self.id = next(self.id_iter)
        self.name = name
        self.metadata = metadata

class Server(object):
    """
    El servidor, que crea y atiende el socket en la dirección y puerto
    especificados donde se reciben nuevas conexiones de clientes.
    """

    def __init__(self, addr=DEFAULT_ADDR, port=DEFAULT_PORT,
                 directory=DEFAULT_DIR):
        print("Serving %s on %s:%s." % (directory, addr, port))
        # ~FALTA~ -> Done: Crear socket del servidor, configurarlo, asignarlo
        # a una dirección y puerto, etc.

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Crear el socket
        self.s.bind((addr,port)) # Vincularlo a la direccion y puerto especificadas
        self.status = None # Debug 
        #self.buffer = ""
        self.c_socket = None
        self.c_address = None
        self.connected = False
        self.available_files = [
            file("a1","512"),
            file("a2","120002"),
            file("a3","1024")
        ]

    def send(self, message, timeout=None):
        """
        Envía el mensaje 'message' al server, seguido por el terminador de
        línea del protocolo.

        Si se da un timeout, puede abortar con una excepción socket.timeout.

        También puede fallar con otras excepciones de socket.
        """
        message += EOL  # Completar el mensaje con un fin de línea
        while message:
            bytes_sent = self.c_socket.send(message.encode("ascii"))
            assert bytes_sent > 0
            message = message[bytes_sent:]

    def send_encoded(self, message, timeout=None):
        """
        Envía el mensaje 'message' al server, seguido por el terminador de
        línea del protocolo.

        Si se da un timeout, puede abortar con una excepción socket.timeout.

        También puede fallar con otras excepciones de socket.
        """
        while message:
            bytes_sent = self.c_socket.send(message.encode("ascii"))
            assert bytes_sent > 0
            message = message[bytes_sent:]

    def send_response_code(self,CODE):
        msg = "{code} {m}".format(code=CODE,m=error_messages[CODE])
        print(msg)
        self.send(msg)

    def send_EOL(self):
        msg = ""
        self.send(msg)
    
    def serve_file_listing(self):
        """
        Envia al cliente ,la lista de archivos disponibles en el servidor
        """
        #El cliente espera primero codigo de respuesta

        #Enviar todos los nombres de archivos disponibles
        self.send_response_code(CODE_OK)
        for i in self.available_files:
            self.send(i.name)

        response = "" #Enviar solo EOL para indicar que ya se enviaron todas las lineas
        self.send(response)

    def serve_file_metadata(self,filename):
        """
        Devuelve el tamaño del archivo
        en bytes como un string ,y con un
        caracter EOL al final

        Ademas de un codigo de error al principio
        """
        found = None
        for i in self.available_files: #Encuentra el primer archivo con ese nombre
            if i.name == filename:
                found = i
                break

        if found != None:
            print("file found!")
            self.send_response_code(CODE_OK)
            self.send(i.metadata)
            return 0

        else:
            print("Couldn't found the file")
            self.send_response_code(BAD_REQUEST)
            response = ""
            self.send(response)
            return 1

    def client_quits(self):
        print("client quitted")
        self.c_address = None
        self.send_response_code(CODE_OK)
        self.c_socket.close()
        self.connected = False

    def request_handler(self,request):
        if EOL in request: # Cleans the request of EOL for parsing
            request, trash = request.split(EOL, 1)
            request.strip()
        
        parse = request.split() # Obtiene una lista de los substrings separados por espacios
        
        print("Client requested: '",request,"'")

        # TODO:agregar control de errores
        if (parse[0] == "get_file_listing" and len(parse) == 1):
            self.serve_file_listing()

        elif (parse[0] == "get_metadata" and len(parse) == 2):
            filename = parse[1]
            self.serve_file_metadata(filename)

        # elif(parse[0] == "get_slice" and len(parse) == 4):
        #     filename = parse[1]
        #     start = parse[2]
        #     end = parse[3]
        #     self.serve_file_slice(filename,start,end)

        elif (parse[0] == "quit"):
            self.client_quits()
        else:
            self.send_response_code(BAD_REQUEST)
            print("Request not served")

        return 0        
        
    def serve(self):
        """
        Loop principal del servidor. Se acepta una conexión a la vez
        y se espera a que concluya antes de seguir.
        """
        self.s.listen(1) # Pone el socket en escucha ,con capacidad de un host
        self.c_socket,self.c_address = self.s.accept() # .connect() devuelve una tupla con el cliente y la direccion client,client_address
        self.connected = True
        while self.connected:
            request = self.c_socket.recv(4086).decode("ascii") # Receives the request from the client
            self.request_handler(request)
        print("WARNING: server wiil keep up listening")
        self.serve()

def main():
    """Parsea los argumentos y lanza el server"""

    parser = optparse.OptionParser()
    parser.add_option(
        "-p", "--port",
        help="Número de puerto TCP donde escuchar", default=DEFAULT_PORT)
    parser.add_option(
        "-a", "--address",
        help="Dirección donde escuchar", default=DEFAULT_ADDR)
    parser.add_option(
        "-d", "--datadir",
        help="Directorio compartido", default=DEFAULT_DIR)

    options, args = parser.parse_args()
    if len(args) > 0:
        parser.print_help()
        sys.exit(1)
    try:
        port = int(options.port)
    except ValueError:
        sys.stderr.write(
            "Numero de puerto invalido: %s\n" % repr(options.port))
        parser.print_help()
        sys.exit(1)

    server = Server(options.address, port, options.datadir)
    server.serve()


if __name__ == '__main__':
    main()
