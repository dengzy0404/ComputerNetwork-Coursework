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


# checksum
def check_sum(strings):
    csum = 0
    count_to = (len(strings) / 2) * 2
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


# get host_info by address
def get_host_info(host_addr):
    try:
        host_info = socket.gethostbyaddr(host_addr)
    except socket.error:
        display = '{0}'.format(host_addr)
    else:
        display = '{0} ({1})'.format(host_addr, host_info[0])
    return display


# construct ICMP datagram
def build_packet():
    # primitive checksum
    my_checksum = 0
    # process_id
    my_id = os.getpid()
    # sequence as 1(>0)
    my_seq = 1
    # 2's header
    my_header = struct.pack("bbHHh", TYPE_ECHO_REQUEST, CODE_ECHO_REQUEST_DEFAULT, my_checksum, my_id, my_seq)
    # SYS_time as payload
    my_data = struct.pack("d", time.time())
    # temporary datagram
    package = my_header + my_data
    # true checksum
    my_checksum = check_sum(package)
    # windows-big endian
    my_checksum = socket.htons(my_checksum)
    # repack
    my_header = struct.pack("bbHHh", TYPE_ECHO_REQUEST, CODE_ECHO_REQUEST_DEFAULT, my_checksum, my_id, 1)
    # true datagram
    ip_package = my_header + my_data
    return ip_package


def create_icmp_socket(ttl):
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
    icmp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))
    icmp_socket.settimeout(TIMEOUT)
    return icmp_socket


def send_icmp_packet(icmp_socket, hostname):
    icmp_package = build_packet()
    icmp_socket.sendto(icmp_package, (hostname, 0))


def receive_icmp_response(icmp_socket):
    try:
        ip_package, ip_info = icmp_socket.recvfrom(1024)
        return ip_package, ip_info
    except socket.timeout:
        return b'', None


def process_icmp_response(ip_package, ip_info):
    icmp_header = ip_package[20:28]
    after_type, _, _, _, _ = struct.unpack("bbHHh", icmp_header)
    output = get_host_info(ip_info[0])

    if after_type == TYPE_ICMP_UNREACHED:
        print("Wrong! unreached net/host/port!")
        return True
    elif after_type == TYPE_ICMP_OVERTIME:
        print(f" {output}")
        return False
    elif after_type == 0:
        print(f" {output}\nprogram run over!")
        return True


def print_response_time(during_time):
    print("    *    " if during_time >= TIMEOUT or during_time == 0
          else " {:>4.0f} ms ".format(during_time * 1000), end="")


def detect_and_print_response(icmp_socket):
    try:
        ip_package, ip_info = icmp_socket.recvfrom(1024)
    except socket.timeout:
        print(" request time out")
        return None, None
    return ip_package, ip_info


def main(hostname):
    print(f"routing {hostname}[{socket.gethostbyname(hostname)}](max hops = 30, detect tries = 3)")

    for ttl in range(1, MAX_HOPS):
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
                ip_package, ip_info = detect_and_print_response(icmp_socket)
                if ip_info is not None:
                    if process_icmp_response(ip_package, ip_info):
                        return


if __name__ == "__main__":
    TIMEOUT = 2.0  # default timeout

    while True:
        try:
            ip = input("Please input an IP address: ")
            timeout_input = input("Input timeout you want (in seconds): ")

            if timeout_input:
                TIMEOUT = float(timeout_input)

            main(ip)
            break
        except Exception as e:
            print(e)
            continue
