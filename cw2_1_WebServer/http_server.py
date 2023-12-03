import multiprocessing
import socket


def handle_req(client_socket):
    # Receive the HTTP request data from the client
    request_data = client_socket.recv(1024)
    # Split the request data into lines
    request_list = request_data.decode().split("\r\n")
    # Extract the request line
    req_header_line = request_list[0]
    print("request line: " + req_header_line)
    # Extract the requested file name from the request line
    file_name = req_header_line.split(" ")[1].replace("/", "")
    try:
        # Try to open the requested file in binary mode
        file = open("./" + file_name, 'rb')  # read the corresponding file from disk
        print("fileName: " + file_name)  # Display the file name
    except FileNotFoundError:
        # If the file is not found, construct a 404 Not Found response
        response_header = "HTTP/1.1 404 Not Found\r\n" + \
                         "Server: 127.0.0.1\r\n" + "\r\n"
        response_data = response_header + "No such file\nCheck your input\n"
        content = (response_header + response_data).encode(encoding="UTF-8")  # send the correct HTTP response error
    else:
        # If the file is found, read its content
        content = file.read()  # store in temporary buffer
        file.close()
    # Construct the HTTP response header for a successful request
    res_header = "HTTP/1.1 200 OK\r\n"
    file_content01 = "Server: 127.0.0.1\r\n"
    # Convert the file content to a string
    file_content02 = content.decode()
    # Combine the header and file content to form the complete HTTP response
    response = res_header + file_content01 + "\r\n" + file_content02  # send the correct HTTP response
    # Send the response back to the client
    client_socket.sendall(response.encode(encoding="UTF-8"))


def start_server(server_addr, server_port=8000):
    # Create a TCP socket for the server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow reuse of the address if the server is restarted quickly
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind the socket to the specified address and port
    server_socket.bind((server_addr, server_port))
    # Start listening for incoming connections with a maximum backlog of 0
    server_socket.listen(0)
    while True:
        try:
            print("wait for connecting...")
            print("while true")
            # Accept a connection from a client
            client_socket, client_addr = server_socket.accept()
            print("one connection is established, ", end="")
            print("address is: %s" % str(client_addr))
            # Create a new process to handle the client's request
            handle_process = multiprocessing.Process(target=handle_req, args=(client_socket,))
            handle_process.start()  # handle request
            # Close the client socket (the child process now handles it)
            client_socket.close()
            print("client close")
        except Exception as err:
            # Print any exceptions that occur, and break out of the loop
            print(err)
            break
    # Close the server socket when the loop exits
    server_socket.close()


if __name__ == '__main__':
    # Set the default IP address
    ipAddr = "127.0.0.1"
    # Prompt the user to input the desired port number
    port = int(input("Input the port you want (Default is 8000):"))
    # Start the server with the specified IP address and port
    start_server(ipAddr, port)
