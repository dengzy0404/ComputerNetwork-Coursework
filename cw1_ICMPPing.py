import socket
import os
import struct
import time
import select


ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages


def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = string[count + 1] * 256 + string[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(string):
        csum = csum + string[len(string) - 1]
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)

    answer = socket.htons(answer)

    return answer


def receiveOnePing(icmpSocket, ID, timeout):
    timeLeft = timeout
    while True:
        startedSelect = time.time()
        whatReady = select.select([icmpSocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:  # Timeout
            return "Request timed out.", None, None

        timeReceived = time.time()
        recPacket, addr = icmpSocket.recvfrom(1024)

        # Get the TTL from the IP header
        ttl = struct.unpack("!B", recPacket[8:9])[0]

        icmpHeader = recPacket[20:28]
        type, code, checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)

        if packetID == ID:
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            return timeReceived - timeSent, ttl, code

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out.", None, None


def sendOnePing(icmpSocket, destAddr, ID):
    myChecksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    myChecksum = checksum(header + data)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(myChecksum), ID, 1)
    packet = header + data
    icmpSocket.sendto(packet, (destAddr, 1))


def doOnePing(destAddr, timeout):
    icmp = socket.getprotobyname("icmp")
    icmpSocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)

    myID = os.getpid() & 0xFFFF  # Return the current process ID

    sendOnePing(icmpSocket, destAddr, myID)
    delay, ttl, code = receiveOnePing(icmpSocket, myID, timeout)

    icmpSocket.close()
    return delay, ttl, code


def ping(host, timeout=1, count=4):
    destAddr = socket.gethostbyname(host)
    packetSize = struct.calcsize("bbHHh") + struct.calcsize("d")

    print(f"Pinging {host} [{destAddr}] with {packetSize} bytes of data:")

    responses = []
    total_delay = 0
    min_delay = float('inf')
    max_delay = 0
    packet_loss_count = 0

    for _ in range(count):
        delay, ttl, code = doOnePing(destAddr, timeout)

        if code is not None:
            if code == 0:
                if isinstance(delay, float):
                    delay_ms = delay * 1000
                    total_delay += delay_ms
                    responses.append(delay_ms)
                    min_delay = min(min_delay, delay_ms)
                    max_delay = max(max_delay, delay_ms)
                    print(f"Reply from {destAddr}: bytes={packetSize} RRT={delay_ms:.2f}ms TTL={ttl}")
                else:
                    print(f"Reply from {destAddr}: {delay}")
            else:
                packet_loss_count += 1
                print(f"ICMP Error: {code}")

        time.sleep(1)

    # Printing the statistics
    print("\n{} packets transmitted, {} received, {}% packet loss".format(count, len(responses),
                                                                           (packet_loss_count / count) * 100))

    if responses:
        avg_delay = total_delay / len(responses)
        print("Round-trip min/avg/max = {:.2f}/{:.2f}/{:.2f} ms".format(min_delay, avg_delay, max_delay))


if __name__ == '__main__':
    host = input("Enter the IP address or hostname to ping: ")
    timeout = float(input("Enter the timeout value (in seconds): "))
    count = int(input("Enter the number of packets to send: "))
    ping(host, timeout, count)