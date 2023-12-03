import os
import socket
import hashlib

# Dictionary to store cached file paths
cache_dict = {}


def handle_req(client_socket):
    # Receive data from the client
    recv_data = client_socket.recv(1024).decode("UTF-8")
    
    # Extract the requested file name from the received data
    file_name = recv_data.split()[1].split("//")[1].replace('/', '')
    print("GET request for fileName: " + file_name)

    # Generate a hash for caching
    cache_key = hashlib.md5(file_name.encode()).hexdigest()
    file_path = "./cache/" + cache_key

    # Check if the file is cached
    if cache_key in cache_dict:
        print("File is found in proxy server and cache.")
        # Send the cached file to the client
        with open(cache_dict[cache_key], 'rb') as cached_file:
            response_msg = cached_file.read()
            client_socket.sendall(response_msg)
        print("Send, done.")
    else:
        print("File is not in cache. Sending request to server...")
        try:
            # Connect to the destination server
            proxy_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_name = file_name.split(":")[0]
            proxy_client_socket.connect((server_name, 80))
            
            # Forward the client's request to the server
            proxy_client_socket.sendall(recv_data.encode("UTF-8"))
            # Receive the response from the server
            response_msg = proxy_client_socket.recv(4096)
            
            print("File is found in server.")
            # Send the response to the client
            client_socket.sendall(response_msg)
            print("Send, done.")

            # Cache the response
            if not os.path.exists("./cache"):
                os.makedirs("./cache")
            cache_dict[cache_key] = file_path
            with open(file_path, 'wb') as cache_file:
                cache_file.write(response_msg)
            print("Cache, done.")
        except Exception as e:
            print("Connect timeout or other error: {0}".format(e))


def start_proxy(port_num):
    # Set up the proxy server socket
    proxy_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_server_socket.bind(("", port_num))
    proxy_server_socket.listen(0)
    
    while True:
        try:
            print("Proxy is waiting for connecting...")
            # Accept client connection
            client_socket, _ = proxy_server_socket.accept()
            print("Connect established")
            # Handle the client's request
            handle_req(client_socket)
            client_socket.close()
        except Exception as e:
            print("Error: {0}".format(e))
            break
    proxy_server_socket.close()


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
    start_proxy(port)
