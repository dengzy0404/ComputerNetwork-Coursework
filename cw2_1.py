import multiprocessing
import socket


def handleReq(clientSocket):
    requestData = clientSocket.recv(1024)
    requestList = requestData.decode().split("\r\n")
    reqHeaderLine = requestList[0]
    print("request line: " + reqHeaderLine)
    fileName = reqHeaderLine.split(" ")[1].replace("/", "")
    try:
        file = open("./" + fileName, 'rb')  # read the corresponding file from disk
        print("fileName: " + fileName)  # 查看文件名
    except FileNotFoundError:
        responseHeader = "HTTP/1.1 404 Not Found\r\n" + \
                         "Server: 127.0.0.1\r\n" + "\r\n"

        responseData = responseHeader + "No such file\nCheck your input\n"

        content = (responseHeader + responseData).encode(encoding="UTF-8")  # send the correct HTTP response error
    else:
        content = file.read()  # store in temporary buffer
        file.close()
    resHeader = "HTTP/1.1 200 OK\r\n"
    fileContent01 = "Server: 127.0.0.1\r\n"
    fileContent02 = content.decode()
    response = resHeader + fileContent01 + "\r\n" + fileContent02  # send the correct HTTP response
    clientSocket.sendall(response.encode(encoding="UTF-8"))


def startServer(serverAddr, serverPort):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((serverAddr, serverPort))
    serverSocket.listen(0)
    while True:
        try:
            print("wait for connecting...")
            print("while true")
            clientSocket, clientAddr = serverSocket.accept()
            print("one connection is established, ", end="")
            print("address is: %s" % str(clientAddr))
            handleProcess = multiprocessing.Process(target=handleReq, args=(clientSocket,))
            handleProcess.start()  # handle request
            clientSocket.close()
            print("client close")
        except Exception as err:
            print(err)
            break
    serverSocket.close()  # while出错了就关掉


if __name__ == '__main__':
    ipAddr = "127.0.0.1"
    port = 8000
    startServer(ipAddr, port)

    # #!/usr/bin/env python3
# # -*- coding: UTF-8 -*-

# import socket
# import threading


# def handleRequest(tcpSocket):
#     # 1. Receive request message from the client on connection socket
#     requestData = tcpSocket.recv(1024)
#     # 2. Extract the path of the requested object from the message (second part of the HTTP header)
#     requestList = requestData.decode().split("\r\n")
#     reqHeaderLine = requestList[0]
#     print("request line: " + reqHeaderLine)
#     fileName = reqHeaderLine.split(" ")[1].replace("/", "")
#     #  3. Read the corresponding file from disk
#     try:
#         file = open("./" + fileName, 'rb')  # read the corresponding file from disk
#         print("fileName: " + fileName)
#         # 4. Store in temporary buffer
#         content = file.read().decode()  # store in temporary buffer
#         file.close()
#         resHeader = "HTTP/1.1 200 OK\r\n" + \
#                     "Server: 127.0.0.1\r\n" + "\r\n"
#         response = (resHeader + content).encode(encoding="UTF-8")  # send the correct HTTP response
#     except FileNotFoundError:
#         content = "404 NOT FOUND\n"
#         resHeader = "HTTP/1.1 404 Not Found\r\n" + \
#                     "Server: 127.0.0.1\r\n" + "\r\n"
#         response = (resHeader + content).encode(encoding="UTF-8")  # send the correct HTTP response error
#         # 5. Send the correct HTTP response error
#         tcpSocket.sendall(response)
#     # 6. Send the content of the file to the socket
#     else:
#         tcpSocket.sendall(response)
#     # 7. Close the connection socket
#     tcpSocket.close()


# def startServer(serverAddress, serverPort):
#     # 1. Create server socket
#     serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     # 2. Bind the server socket to server address and server port
#     serverSocket.bind((serverAddress, serverPort))
#     # 3. Continuously listen for connections to server socket
#     serverSocket.listen(0)
#     # 4. When a connection is accepted, call handleRequest function, passing new connection socket (see
#     # https://docs.python.org/3/library/socket.html#socket.socket.accept)
#     while True:
#         try:
#             print("wait for connecting...")
#             print("while true")
#             tcpSocket, clientAddr = serverSocket.accept()
#             print("one connection is established, ", end="")
#             print("address is: %s" % str(clientAddr))
#             handleThread = threading.Thread(target=handleRequest, args=(tcpSocket,))
#             handleThread.start()
#         except Exception as err:
#             print(err)
#             break
#     #  5. Close server socket
#     serverSocket.close()


# if __name__ == '__main__':
#     while True:
#         try:
#             hostPort = int(input("Input the port you want: "))
#             startServer("", hostPort)
#             break
#         except Exception as e:
#             print(e)
#             continue