import os
import struct
import time
import select
import socket

# ICMP message types
ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages
ICMP_Type_Unreachable = 11  # ICMP type code for host unreachable
ICMP_Type_Overtime = 3  # ICMP type code for request timeout

ID = 0  # ID of ICMP header
SEQUENCE = 0  # Sequence number of ping request message
ICMP_HEADER_FORMAT = '!bbHHh'  # Format string for unpacking ICMP header


def checksum(data):
    """
    Calculate the checksum for the given data.
    """
    csum = 0
    count_to = (len(data) // 2) * 2
    count = 0
    while count < count_to:
        this_val = data[count + 1] * 256 + data[count]
        csum = csum + this_val
        csum = csum & 0xffffffff
        count = count + 2
    if count_to < len(data):
        csum = csum + data[len(data) - 1]
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def receive_one_ping(icmp_socket, timeout):
    """
    Receive one ICMP ping reply and calculate the delay.
    """
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
        return -3  # TTL overtime/timeout
    elif reply_type == ICMP_Type_Unreachable:
        return -11  # Unreachable
    else:
        print("Request over time")
        return -1


def send_one_ping(icmp_socket, destination_address):
    """
    Send one ICMP ping request.
    """
    icmp_checksum = 0

    # Create ICMP header
    icmp_header = struct.pack(ICMP_HEADER_FORMAT, ICMP_ECHO_REQUEST, 0, icmp_checksum, ID, SEQUENCE)
    time_send = struct.pack('!d', time.time())

    # Calculate ICMP checksum
    icmp_checksum = checksum(icmp_header + time_send)
    icmp_header = struct.pack(ICMP_HEADER_FORMAT, ICMP_ECHO_REQUEST, 0, icmp_checksum, ID, SEQUENCE)

    # Create ICMP packet
    icmp_packet = icmp_header + time_send
    icmp_socket.sendto(icmp_packet, (destination_address, 80))


def do_one_ping(destination_address, timeout):
    """
    Perform one round of ICMP ping.
    """
    # Create raw ICMP socket
    icmp_name = socket.getprotobyname('icmp')
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp_name)

    # Send ping request and receive the response
    send_one_ping(icmp_socket, destination_address)
    total_delay = receive_one_ping(icmp_socket, timeout)

    # Close the ICMP socket
    icmp_socket.close()

    return total_delay


def ping(host, count=4, timeout=1.0):
    """
    Perform multiple rounds of ICMP ping and display statistics.
    """
    send = 0
    lost = 0
    receive = 0
    max_time = 0
    min_time = float('inf')
    sum_time = 0

    # Get the IP address of the host
    des_ip = socket.gethostbyname(host)
    global ID
    ID = os.getpid()

    print(f"\nPinging {host} [{des_ip}]:")
    try:
        # Perform 'count' rounds of ping
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
                print(f"Received from: {des_ip}, delay = {int(delay)}ms")
            else:
                print("Failed to connect. " + ("Target net/host/port/protocol is unreachable."
                                               if delay == -11 else "Request timeout."))
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
        print("\nPing statistics:")
        print(f"Send: {send}, Success: {receive}, Lost: {lost}, Packet loss: {packet_loss:.2f}%.")
        print("\nEstimated round trip time (in ms):")
        print(f"Max time = {int(max_time)}ms, Min time = {int(min_time)}ms, Avg time = {avg_time:.2f}ms")
    else:
        print(f"Send: {send}, Success: {receive}, Lost: {lost}, Packet loss: {packet_loss:.2f}%")


if __name__ == '__main__':
    while True:
        try:
            hostName = input("Input IP/hostname of the host you want to ping: ")
            count_input = int(input("How many times you want to ping (default is 4): ") or 4)
            timeout_input = float(input("Input timeout in seconds (default is 1): ") or 1)
            ping(hostName, count_input, timeout_input)
            break
        except Exception as e:
            print(e)
            continue
