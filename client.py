# coding: utf-8

import socket
import select
import sys
import os

###################################################################################################################
#
# Global variables
#
###################################################################################################################

MSGLEN = 2500

###################################################################################################################
#
# Global & init
#
###################################################################################################################
def initPoll(list):
    pollerObject = select.poll()
    for fd in list:
        pollerObject.register(fd, select.POLLIN)
    return pollerObject

def createSockAndConnect(address):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except:
        print("Error when creating the socket")
        raise

    try:
        sock.connect(address)
    except:
        print("Can not connect to the server")
        raise

    return sock

def parseArgAndVerifyHostname():
    if len(sys.argv) != 3:
        print("USAGE: python3 client.py <hostname> <port>")
        exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    try:
        host = socket.gethostbyname(host)
    except:
        print("Can not resolve server address")
        exit(1)

    return (host, port)

###################################################################################################################
#
# Message/input management
#
###################################################################################################################
def msgmgt(sock):
    response = sock.recv(MSGLEN)
    if not response:
        print("Connection closed by server")
        sock.close()
        exit(0)

    print(response.decode())

def inputmgt(sock):
    message = sys.stdin.readline()
    sock.send(message.encode())
    sys.stdout.write("\033[F")
    if message == "/quit":
        print("Good bye!")
        sock.close()
        exit(0)

###################################################################################################################
#
# Main
#
###################################################################################################################
def main(sock, pollerObject):
    while True:
        fdVsEvent = pollerObject.poll(10000)
        for descriptor, Event in fdVsEvent:
            if descriptor == sock.fileno():
                msgmgt(sock)
            else:
                inputmgt(sock)

if __name__ == "__main__":
    address = parseArgAndVerifyHostname()
    print("Connecting to " + address[0] + " on port " + str(address[1]) + "\n")
    sock = createSockAndConnect(address)
    pollerObject = initPoll([0, sock])

    try:
        main(sock, pollerObject)
    except KeyboardInterrupt:
        try:
            sock.close()
        except:
            print("No socket to close")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)