import multiprocessing
import socket

def handleReq(clientSocket):
    # Receive the HTTP request data from the client
    requestData = clientSocket.recv(1024)
    # Split the request data into lines
    requestList = requestData.decode().split("\r\n")
    # Extract the request line
    reqHeaderLine = requestList[0]
    print("request line: " + reqHeaderLine)
    # Extract the requested file name from the request line
    fileName = reqHeaderLine.split(" ")[1].replace("/", "")
    try:
        # Try to open the requested file in binary mode
        file = open("./" + fileName, 'rb')  # read the corresponding file from disk
        print("fileName: " + fileName)  # Display the file name
    except FileNotFoundError:
        # If the file is not found, construct a 404 Not Found response
        responseHeader = "HTTP/1.1 404 Not Found\r\n" + \
                         "Server: 127.0.0.1\r\n" + "\r\n"
        responseData = responseHeader + "No such file\nCheck your input\n"
        content = (responseHeader + responseData).encode(encoding="UTF-8")  # send the correct HTTP response error
    else:
        # If the file is found, read its content
        content = file.read()  # store in temporary buffer
        file.close()
    # Construct the HTTP response header for a successful request
    resHeader = "HTTP/1.1 200 OK\r\n"
    fileContent01 = "Server: 127.0.0.1\r\n"
    # Convert the file content to a string
    fileContent02 = content.decode()
    # Combine the header and file content to form the complete HTTP response
    response = resHeader + fileContent01 + "\r\n" + fileContent02  # send the correct HTTP response
    # Send the response back to the client
    clientSocket.sendall(response.encode(encoding="UTF-8"))

def startServer(serverAddr, serverPort=8000):
    # Create a TCP socket for the server
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow reuse of the address if the server is restarted quickly
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind the socket to the specified address and port
    serverSocket.bind((serverAddr, serverPort))
    # Start listening for incoming connections with a maximum backlog of 0
    serverSocket.listen(0)
    while True:
        try:
            print("wait for connecting...")
            print("while true")
            # Accept a connection from a client
            clientSocket, clientAddr = serverSocket.accept()
            print("one connection is established, ", end="")
            print("address is: %s" % str(clientAddr))
            # Create a new process to handle the client's request
            handleProcess = multiprocessing.Process(target=handleReq, args=(clientSocket,))
            handleProcess.start()  # handle request
            # Close the client socket (the child process now handles it)
            clientSocket.close()
            print("client close")
        except Exception as err:
            # Print any exceptions that occur, and break out of the loop
            print(err)
            break
    # Close the server socket when the loop exits
    serverSocket.close()  # while出错了就关掉

if __name__ == '__main__':
    # Set the default IP address
    ipAddr = "127.0.0.1"
    # Prompt the user to input the desired port number
    port = int(input("Input the port you want (Default is 8000):"))
    # Start the server with the specified IP address and port
    startServer(ipAddr, port)
