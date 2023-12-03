import os
import socket
import hashlib

# Dictionary to store cached file paths
cache_dict = {}

def handleReq(clientSocket):
    # Receive data from the client
    recvData = clientSocket.recv(1024).decode("UTF-8")
    
    # Extract the requested file name from the received data
    fileName = recvData.split()[1].split("//")[1].replace('/', '')
    print("GET request for fileName: " + fileName)

    # Generate a hash for caching
    cache_key = hashlib.md5(fileName.encode()).hexdigest()
    filePath = "./cache/" + cache_key

    # Check if the file is cached
    if cache_key in cache_dict:
        print("File is found in proxy server and cache.")
        # Send the cached file to the client
        with open(cache_dict[cache_key], 'rb') as cached_file:
            responseMsg = cached_file.read()
            clientSocket.sendall(responseMsg)
        print("Send, done.")
    else:
        print("File is not in cache. Sending request to server...")
        try:
            # Connect to the destination server
            proxyClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            serverName = fileName.split(":")[0]
            proxyClientSocket.connect((serverName, 80))
            
            # Forward the client's request to the server
            proxyClientSocket.sendall(recvData.encode("UTF-8"))
            # Receive the response from the server
            responseMsg = proxyClientSocket.recv(4096)
            
            print("File is found in server.")
            # Send the response to the client
            clientSocket.sendall(responseMsg)
            print("Send, done.")

            # Cache the response
            if not os.path.exists("./cache"):
                os.makedirs("./cache")
            cache_dict[cache_key] = filePath
            with open(filePath, 'wb') as cache_file:
                cache_file.write(responseMsg)
            print("Cache, done.")
        except Exception as e:
            print("Connect timeout or other error: {0}".format(e))


def startProxy(port):
    # Set up the proxy server socket
    proxyServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxyServerSocket.bind(("", port))
    proxyServerSocket.listen(0)
    
    while True:
        try:
            print("Proxy is waiting for connecting...")
            # Accept client connection
            clientSocket, addr = proxyServerSocket.accept()
            print("Connect established")
            # Handle the client's request
            handleReq(clientSocket)
            clientSocket.close()
        except Exception as e:
            print("Error: {0}".format(e))
            break
    proxyServerSocket.close()


if __name__ == '__main__':
    # Get user input for the port number
    while True:
        try:
            port = int(input("Choose a port number over 1024: "))
        except ValueError:
            print("Please input an integer rather than {0}".format(type(port)))
            continue
        else:
            if port <= 1024:
                print("Please input an integer greater than 1024")
                continue
            else:
                break
    # Start the proxy server
    startProxy(port)
