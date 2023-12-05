import os
import struct
import time
import select
import socket

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages
ICMP_Type_Unreachable = 11  # unacceptable host
ICMP_Type_Overtime = 3  # request overtime
ID = 0  # ID of icmp_header
SEQUENCE = 0  # sequence of ping_request_msg
ICMP_HEADER_FORMAT = '!bbHHh'  # format string head for unpack


def checksum(strings):
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


def receive_one_ping(icmp_socket, timeout):
    time_begin_receive = time.time()
    what_ready = select.select([icmp_socket], [], [], timeout)
    time_in_rcv = time.time() - time_begin_receive

    if not what_ready[0]:
        return -1  # Timeout

    time_received = time.time()
    rec_packet, _ = icmp_socket.recvfrom(1024)

    byte_in_double = struct.calcsize("!d")
    time_sent = struct.unpack("!d", rec_packet[28: 28 + byte_in_double])[0]
    total_delay = time_received - time_sent

    rec_header = rec_packet[20:28]
    reply_type, _, _, reply_id, _ = struct.unpack(ICMP_HEADER_FORMAT, rec_header)

    if ID == reply_id and reply_type == ICMP_ECHO_REPLY:
        return total_delay
    elif time_in_rcv > timeout or reply_type == ICMP_Type_Overtime:
        return -3  # ttl overtime/timeout
    elif reply_type == ICMP_Type_Unreachable:
        return -11  # unreachable
    else:
        print("Request over time")
        return -1


def send_one_ping(icmp_socket, destination_address):
    icmp_checksum = 0

    icmp_header = struct.pack(ICMP_HEADER_FORMAT, ICMP_ECHO_REQUEST, 0, icmp_checksum, ID, SEQUENCE)
    time_send = struct.pack('!d', time.time())

    icmp_checksum = checksum(icmp_header + time_send)
    icmp_header = struct.pack(ICMP_HEADER_FORMAT, ICMP_ECHO_REQUEST, 0, icmp_checksum, ID, SEQUENCE)

    icmp_packet = icmp_header + time_send
    icmp_socket.sendto(icmp_packet, (destination_address, 80))


def do_one_ping(destination_address, timeout):
    icmp_name = socket.getprotobyname('icmp')
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp_name)

    send_one_ping(icmp_socket, destination_address)
    total_delay = receive_one_ping(icmp_socket, timeout)

    icmp_socket.close()

    return total_delay


def ping(host, count=4, timeout=1.0):
    send = 0
    lost = 0
    receive = 0
    max_time = 0
    min_time = float('inf')
    sum_time = 0

    des_ip = socket.gethostbyname(host)
    global ID
    ID = os.getpid()

    print(f"Pinging {host} [{des_ip}]:")

    try:
        for i in range(count):
            global SEQUENCE
            SEQUENCE = i
            delay = do_one_ping(des_ip, timeout) * 1000
            send += 1

            success = delay > 0
            if success:
                receive += 1
                max_time = max(max_time, delay)
                min_time = min(min_time, delay)
                sum_time += delay

            if success:
                print(f"Receive from: {des_ip}, delay = {int(delay)}ms")
            else:
                print("Fail to connect. " + ("Target net/host/port/protocol is unreachable."
                                             if delay == -11 else "Request overtime."))
                lost += 1

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nPing tool terminated by user.")

    if send != 0:
        packet_loss = (lost / send) * 100.0
    else:
        packet_loss = 100.0

    if receive != 0:
        avg_time = sum_time / receive
        print("\nSend: {0}, success: {1}, lost: {2}, packet loss: {3:.2f}%.".format(send, receive, lost, packet_loss))
        print("Max time = {0}ms, Min time = {1}ms, Avg time = {2:.2f}ms".format(
            int(max_time), int(min_time), avg_time))
    else:
        print("\nSend: {0}, Success: {1}, Lost: {2}, Packet loss: {3:.2f}%".format(send, receive, lost, packet_loss))


if __name__ == '__main__':
    while True:
        try:
            hostName = input("Input ip/name of the host you want: ")
            count_input = int(input("How many times you want to detect (default is 4): ") or 4)
            timeout_input = float(input("Input timeout in second (default is 1): ") or 1)
            ping(hostName, count_input, timeout_input)
            break
        except Exception as e:
            print(e)
            continue
