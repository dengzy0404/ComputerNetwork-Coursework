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


def startServer(serverAddr, serverPort=8000):
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
    port = int(input("Input the port you want (Default is 8000):"))  # 使用者输入端口号
    startServer(ipAddr, port)
