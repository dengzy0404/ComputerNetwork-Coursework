# --coding:utf-8--

import socket
import os
import struct
import time
import select

# ICMP echo_request
TYPE_ECHO_REQUEST = 8
CODE_ECHO_REQUEST_DEFAULT = 0
# ICMP echo_reply
TYPE_ECHO_REPLY = 0
CODE_ECHO_REPLY_DEFAULT = 0
# ICMP overtime
TYPE_ICMP_OVERTIME = 11
CODE_TTL_OVERTIME = 0
# ICMP unreachable
TYPE_ICMP_UNREACHED = 3

MAX_HOPS = 30  # set max hops-30
TRIES = 3  # detect 3 times

# Timeout
TIMEOUT = 2.0  # default timeout


# Function to calculate checksum for ICMP packet
def check_sum(strings):
    csum = 0
    count_to = (len(strings) // 2) * 2
    count = 0
    while count < count_to:
        this_val = strings[count + 1] * 256 + strings[count]
        csum = csum + this_val
        csum = csum & 0xffffffff
        count = count + 2
    if count_to < len(strings):
        csum = csum + strings[len(strings) - 1]
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


# Function to get host information by its address
def get_host_info(host_addr):
    try:
        host_info = socket.gethostbyaddr(host_addr)
    except socket.error:
        display = '{0}'.format(host_addr)
    else:
        display = '{0} ({1})'.format(host_addr, host_info[0])
    return display


# Function to construct an ICMP datagram
def build_packet():
    my_checksum = 0
    my_id = os.getpid()
    my_seq = 1
    my_header = struct.pack("bbHHh", TYPE_ECHO_REQUEST, CODE_ECHO_REQUEST_DEFAULT, my_checksum, my_id, my_seq)
    my_data = struct.pack("d", time.time())
    package = my_header + my_data
    my_checksum = check_sum(package)
    my_checksum = socket.htons(my_checksum)
    my_header = struct.pack("bbHHh", TYPE_ECHO_REQUEST, CODE_ECHO_REQUEST_DEFAULT, my_checksum, my_id, 1)
    ip_package = my_header + my_data
    return ip_package


# Function to create an ICMP socket with a specified TTL (Time-to-Live)
def create_icmp_socket(ttl):
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
    icmp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))
    icmp_socket.settimeout(TIMEOUT)
    return icmp_socket


# Function to send an ICMP packet to the specified hostname
def send_icmp_packet(icmp_socket, hostname):
    icmp_package = build_packet()
    icmp_socket.sendto(icmp_package, (hostname, 0))


# Function to receive an ICMP response
def receive_icmp_response(icmp_socket):
    try:
        ip_package, ip_info = icmp_socket.recvfrom(1024)
        return ip_package, ip_info
    except socket.timeout:
        print(" Request timed out.")
        return b'', None


# Function to process the received ICMP response
def process_icmp_response(ip_package, ip_info):
    icmp_header = ip_package[20:28]
    after_type, _, _, _, _ = struct.unpack("bbHHh", icmp_header)
    output = get_host_info(ip_info[0])

    if after_type == TYPE_ICMP_UNREACHED:
        print(" Wrong! Unreachable net/host/port!")
        return True
    elif after_type == TYPE_ICMP_OVERTIME:
        print(f" {output}")
        return False
    elif after_type == 0:
        print(f" {output}\n Program run over!")
        return True


# Function to print the response time
def print_response_time(during_time):
    print("    *    " if during_time >= TIMEOUT or during_time == 0
          else " {:>4.0f} ms ".format(during_time * 1000), end="")


# Main function to perform the traceroute
def main(hostname):
    global MAX_HOPS, TRIES, TIMEOUT  # Use global variables

    print(f"Routing to {hostname} [{socket.gethostbyname(hostname)}] "
          f"(max hops(TTL) = {MAX_HOPS}, detect tries = {TRIES})")

    for ttl in range(1, MAX_HOPS + 1):  # Modify this line to use user-inputted maximum hops
        print(f"{ttl:2d}", end="")
        for tries in range(TRIES):
            icmp_socket = create_icmp_socket(ttl)

            send_icmp_packet(icmp_socket, hostname)

            start_time = time.time()
            select.select([icmp_socket], [], [], TIMEOUT)
            end_time = time.time()
            during_time = end_time - start_time

            print_response_time(during_time)

            if tries == TRIES - 1:
                ip_package, ip_info = receive_icmp_response(icmp_socket)
                if ip_info is not None:
                    if process_icmp_response(ip_package, ip_info):
                        return


# Entry point of the script
if __name__ == "__main__":
    while True:
        try:
            ip = input("Please input an IP address: ")
            timeout_input = input("Input the timeout you want (in seconds): ")

            if timeout_input:
                TIMEOUT = float(timeout_input)

            custom_settings = input("Customize MAX_HOPS (Default is 30) and TRIES (Default is 3)? (y/n): ")
            if custom_settings.lower() == 'y':
                MAX_HOPS = int(input("Enter max hops: "))
                TRIES = int(input("Enter detect tries: "))

            main(ip)
            break
        except Exception as e:
            print(e)
            continue
