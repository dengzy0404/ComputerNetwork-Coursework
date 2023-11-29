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


def checksum(strings):
    csum = 0
    countTo = (len(strings) // 2) * 2
    count = 0
    while count < countTo:
        thisVal = strings[count + 1] * 256 + strings[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2
    if countTo < len(strings):
        csum = csum + strings[len(strings) - 1]
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def receiveOnePing(icmpSocket, ID, timeout):
    timeBeginReceive = time.time()
    whatReady = select.select([icmpSocket], [], [], timeout)
    timeInRecev = time.time() - timeBeginReceive

    if not whatReady[0]:
        return -1  # Timeout

    timeReceived = time.time()
    recPacket, addr = icmpSocket.recvfrom(1024)

    byte_in_double = struct.calcsize("!d")
    timeSent = struct.unpack("!d", recPacket[28: 28 + byte_in_double])[0]
    totalDelay = timeReceived - timeSent

    rec_header = recPacket[20:28]
    replyType, replyCode, replyCkecksum, replyId, replySequence = struct.unpack('!bbHHh', rec_header)

    if ID == replyId and replyType == ICMP_ECHO_REPLY:
        return totalDelay
    elif timeInRecev > timeout or replyType == ICMP_Type_Overtime:
        return -3  # ttl overtime/timeout
    elif replyType == ICMP_Type_Unreachable:
        return -11  # unreachable
    else:
        print("Request over time")
        return -1


def sendOnePing(icmpSocket, destinationAddress, ID):
    icmp_checksum = 0

    icmp_header = struct.pack('!bbHHh', ICMP_ECHO_REQUEST, 0, icmp_checksum, ID, SEQUENCE)
    time_send = struct.pack('!d', time.time())

    icmp_checksum = checksum(icmp_header + time_send)
    icmp_header = struct.pack('!bbHHh', ICMP_ECHO_REQUEST, 0, icmp_checksum, ID, SEQUENCE)

    icmp_packet = icmp_header + time_send
    icmpSocket.sendto(icmp_packet, (destinationAddress, 80))


def doOnePing(destinationAddress, timeout):
    icmpName = socket.getprotobyname('icmp')
    icmp_Socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmpName)

    sendOnePing(icmp_Socket, destinationAddress, ID)
    totalDelay = receiveOnePing(icmp_Socket, ID, timeout)

    icmp_Socket.close()

    return totalDelay


def ping(host, count=4, timeout=1):
    send = 0
    lost = 0
    receive = 0
    maxTime = 0
    minTime = float('inf')
    sumTime = 0
    delay_times = []

    desIp = socket.gethostbyname(host)
    global ID
    ID = os.getpid()

    print(f"Pinging {host} [{desIp}]:")

    try:
        for i in range(count):
            global SEQUENCE
            SEQUENCE = i
            delay = doOnePing(desIp, timeout) * 1000
            send += 1

            if delay > 0:
                receive += 1
                if maxTime < delay:
                    maxTime = delay
                if minTime > delay:
                    minTime = delay
                sumTime += delay
                delay_times.append(delay)
                print("Receive from: " + str(desIp) + ", delay = " + str(int(delay)) + "ms")
            else:
                lost += 1
                print("Fail to connect. ", end="")
                if delay == -11:
                    print("Target net/host/port/protocol is unreachable.")
                elif delay == -3:
                    print("Request overtime.")
                else:
                    print("Request overtime.")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nPing tool terminated by user.")

    if receive != 0:
        avgTime = sumTime / receive
        packet_loss = lost / send * 100.0
        print("\nSend: {0}, success: {1}, lost: {2}, packet loss: {3}%.".format(send, receive, lost, packet_loss))
        print("MaxTime = {0}ms, MinTime = {1}ms, AvgTime = {2}ms".format(int(maxTime), int(minTime), int(avgTime)))
    else:
        print("\nSend: {0}, success: {1}, lost: {2}, packet loss: 0.0%".format(send, receive, lost))


if __name__ == '__main__':
    while True:
        try:
            hostName = input("Input ip/name of the host you want: ")
            count = int(input("How many times you want to detect (default is 4): ") or 4)
            timeout = int(input("Input timeout (default is 1): ") or 1)
            ping(hostName, count, timeout)
            break
        except Exception as e:
            print(e)
            continue
