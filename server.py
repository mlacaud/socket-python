# coding: utf-8

import socket
import threading
import select
import sys
import os

###################################################################################################################
#
# Global variables
#
###################################################################################################################

MSGLEN = 2500
clientsockets = {}

###################################################################################################################
#
# Threads
#
###################################################################################################################
class ClientThread(threading.Thread):

    def __init__(self, ip, port, clientsocket):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.clientsocket = clientsocket
        print("[+] Nouveau thread pour %s %s" % (self.ip, self.port,))

    def run(self):
        while True:
            message = self.clientsocket.recv(MSGLEN)
            if not message:
                print("[-] Fermeture du thread par cause de déconnexion pour %s %s" % (self.ip, self.port,))
                clientsockets.pop(self.clientsocket.fileno(), None)
                self.clientsocket.close()
                break

            if message.decode().split(" ")[0] == "/all":
                finalMessage = "[anonymous:" + str(self.port) + "]" + message.decode().replace("/all", "")
                for index in clientsockets:
                    if index != self.clientsocket.fileno():
                        clientsockets[index]["socket"].send(finalMessage.encode())
                    else:
                        finalMessage2 = "[Moi]" + message.decode().replace("/all", "")
                        clientsockets[index]["socket"].send(finalMessage2.encode())
            else:
                finalMessage = "[Moi] " + message.decode()
                self.clientsocket.send(finalMessage.encode())


def acceptthread(sock):
    client_socket, (c_ip, c_port) = sock.accept()
    newthread = ClientThread(c_ip, c_port, client_socket)
    clientsockets[client_socket.fileno()] = {"socket": client_socket, "ip": c_ip, "port": c_port}
    newthread.daemon = True
    newthread.start()


###################################################################################################################
#
# Poll
#
###################################################################################################################
def clientmgt(descriptor, pollerObject):
    message = clientsockets[descriptor]["socket"].recv(MSGLEN)
    if not message:
        print("[-] Fermeture de la connexion pour %s %s" % (clientsockets[descriptor]["ip"], clientsockets[descriptor]["port"]))
        pollerObject.unregister(clientsockets[descriptor]["socket"])
        clientsockets[descriptor]["socket"].close()
        clientsockets.pop(descriptor, None)
        return
    if message.decode().split(" ")[0] == "/all":
        finalMessage = "[anonymous:" + str(clientsockets[descriptor]["port"]) + "]" + message.decode().replace("/all", "")
        for index in clientsockets:
            if index != descriptor:
                clientsockets[index]["socket"].send(finalMessage.encode())
            else:
                finalMessage2 = "[Moi]" + message.decode().replace("/all", "")
                clientsockets[index]["socket"].send(finalMessage2.encode())
    else:
        finalMessage = "[Moi] " + message.decode()
        clientsockets[descriptor]["socket"].send(finalMessage.encode())

def acceptmgt(sock, pollerObject):
    client_socket, (c_ip, c_port) = sock.accept()
    descriptor = client_socket.fileno()

    pollerObject.register(client_socket, select.POLLIN)
    clientsockets[descriptor] = {"socket": client_socket, "ip": c_ip, "port": c_port}

    print("[+] Ouverture de la connexion pour %s %s" % (clientsockets[descriptor]["ip"], clientsockets[descriptor]["port"]))

###################################################################################################################
#
# Global
#
###################################################################################################################
def createSocketServer(port, listenSize):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except:
        print("Can not create the socket")
        exit(1)

    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except:
        print("Can not put options to the socket")
        exit(1)

    try:
        sock.bind(("", port))
    except:
        print("Can not bind to the address")
        exit(1)

    try:
        sock.listen(listenSize)
    except:
        print("Can not listen to the address")
        exit(1)

    return sock

def parseArg():
    pollOrThread = "poll"
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("USAGE: python3 server.py <port> [optionnal: thread/poll (poll by default)]")
        exit(1)
    if len(sys.argv) == 3:
        if sys.argv[2] == "thread":
            pollOrThread = "thread"
    port = int(sys.argv[1])
    return (pollOrThread, port)

###################################################################################################################
#
# Main
#
###################################################################################################################
def main(sock, pollOrThread):
    # poll
    if pollOrThread == "poll":
        pollerObject = select.poll()
        pollerObject.register(sock, select.POLLIN)
        while True:
            fdVsEvent = pollerObject.poll(10000)
            for descriptor, Event in fdVsEvent:
                if descriptor == sock.fileno():
                    acceptmgt(sock, pollerObject)
                else:
                    clientmgt(descriptor, pollerObject)

    #thread
    if pollOrThread == "thread":
        while True:
            acceptthread(sock)

if __name__ == "__main__":
    pollOrThread, port = parseArg()
    sock = createSocketServer(port, 50)
    print("Server started on port %i using %s" % (port, pollOrThread))

    try:
        main(sock, pollOrThread)
    except KeyboardInterrupt:
        try:
            sock.close()
        except:
            print("No socket to close")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

