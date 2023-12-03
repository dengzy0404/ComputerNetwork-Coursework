import os
import socket

def send_request(host, port, path="/"):
    # Create a TCP socket for the client
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Establish a connection to the server at the specified host and port
    client_socket.connect((host, port))

    # Formulate the HTTP GET request with the provided path
    request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"

    # Send the HTTP request to the server
    client_socket.sendall(request.encode(encoding="UTF-8"))

    # Receive the HTTP response from the server (up to 4096 bytes)
    response = client_socket.recv(4096)
    # Print the decoded response to the console
    print(response.decode())

    # Close the socket connection
    client_socket.close()

if __name__ == "__main__":
    # Set the default server IP address
    server_ip = "127.0.0.1"
    # Prompt the user to input the desired server port number
    server_port = int(input("Input the port you want (Default is 8000):"))

    # Specify the path for the HTTP GET request (change this to the desired file path)
    request_path = "/index.html"  # Use a relative path or adjust accordingly

    # Send an HTTP GET request to the server with the specified parameters
    send_request(server_ip, server_port, request_path)
