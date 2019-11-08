import sys
import threading
import time
from socket import *
from packet import packet

WINDOW_SIZE = 10
TIMEOUT = 0.1
T_DATA = 0
T_ACK = 1
T_EOT = 2

class Receiver(threading.Thread):
  
  def run(self):
    global WINDOW_SIZE
    global client_socket
    global base
    global next_seq_num
    global timer
    global t_end
    global f_ack

    while True:
      data, client_addr = client_socket.recvfrom( 2048 )
      p = packet.parse_udp_data(data)

      f_ack.write(str(p.seq_num) + "\n")

      prev_base = base
      offset = base % packet.SEQ_NUM_MODULO
      seq_num = p.seq_num
      window_end = (offset + WINDOW_SIZE - 1) % packet.SEQ_NUM_MODULO

      if p.type == 2:
        client_socket.close()
        t_end = time.time()
        break

      # check if within valid range
      if seq_num >= offset and seq_num <= window_end:
        base = base + seq_num - offset + 1
      elif offset > window_end and (seq_num <= window_end or seq_num >= offset):
        lock.acquire()
        base = base + seq_num + 1 - offset if offset <= seq_num else \
          base + seq_num + 1 + (packet.SEQ_NUM_MODULO - offset)
        lock.release()
      
      if base > prev_base:
        lock.acquire()
        timer = time.time() if base != next_seq_num else 0
        lock.release()


class Sender(threading.Thread):

  def run(self):
    global WINDOW_SIZE
    global lock
    global emu_addr
    global emu_port
    global base
    global total_packets
    global next_seq_num
    global timer
    global t_start
    global f_seqnum
    
    t_start = time.time()
    while base < total_packets:
      if next_seq_num < total_packets and next_seq_num < base + WINDOW_SIZE:
        new_packet = packet.create_packet(next_seq_num, buffer[next_seq_num])

        client_socket.sendto( new_packet.get_udp_data() , (emu_addr, emu_port))
 
        f_seqnum.write(str(next_seq_num) + "\n")

        lock.acquire()
        next_seq_num = next_seq_num + 1

        if base == next_seq_num:
          timer = time.time()
        lock.release()

      elif timer != 0:
        lock.acquire()
        if (time.time() - timer > 0.1):
          offset = base % packet.SEQ_NUM_MODULO

          # resend packets
          for p in range(base, next_seq_num):
            resent_packet = packet.create_packet(p, buffer[p])
            client_socket.sendto( resent_packet.get_udp_data() , (emu_addr, emu_port))
            f_seqnum.write(str(p) + "\n")

          timer = time.time()
        lock.release()
    
    # send eot
    client_socket.sendto( packet.create_eot(next_seq_num).get_udp_data() , (emu_addr, emu_port))

############# MAIN STARTS HERE #############

def check_args(args):
  if len(args) != 4:
    raise Exception

  try:
    emu_addr = args[0]
    emu_port = int(args[1])
    sender_port = int(args[2])
    file_name = args[3]
  except Exception as e:
    raise e

  return emu_addr, emu_port, sender_port, file_name

# Check if command-line arguments are valid
try:
  emu_addr, emu_port, sender_port, file_name = check_args(sys.argv[1:])
except Exception:
  print("ERROR: invalid number of arguments")
  exit(-1)

# Read file and store into buffer
buffer = []
with open(file_name, "r") as f:
  byte = f.read(500)
  while byte:
    buffer.append(byte)
    byte = f.read(500)

lock = threading.Lock()
next_seq_num = 0
base = 0
total_packets = len(buffer)

timer = 0
t_start = 0
t_end = 0

# Create UDP Socket
client_socket = socket(AF_INET, SOCK_DGRAM)
client_socket.bind(('', sender_port))

# Generate three log files
f_seqnum = open("seqnum.log","w")
f_ack = open("ack.log","w")
f_time = open("time.log","w")

# Init threads
ack_receiver = Receiver()
packet_sender = Sender()

# Start threads
ack_receiver.start()
packet_sender.start()

# Wait for threads to end
try:
  ack_receiver.join()
  packet_sender.join()
except Exception:
  print("ERROR: something happened in threads")

# Record transmission time
f_time.write(str(t_end - t_start) + "\n")

# Close files
f_seqnum.close()
f_ack.close()
f_time.close()
