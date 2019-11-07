import sys
import threading
import time
from socket import *
from packet import packet

WINDOW_SIZE = 10
MAX_DATA_LENGTH = 500

class Sender:
  def __init__(self, emu_addr, emu_port, sender_port, file_name):
    super(Sender, self).__init__()
    self.emu_addr = emu_addr
    self.emu_port = emu_port
    self.sender_port = sender_port
    self.base = 0
    self.next_seq_num = 0
    self.timer = None

  def receive_ack(self, client_socket, file_ack):
    global WINDOW_SIZE

    while True:
      data, clientAddress = client_socket.recvfrom( 2048 )
      p = packet.parse_udp_data(data)
      file_ack.write(str(p.seq_num) + "\n")

      prev_base = self.base
      base_mod = self.base % packet.SEQ_NUM_MODULO
      cur_seq_num = p.seq_num
      windowEnd = (base_mod + WINDOW_SIZE - 1) % packet.SEQ_NUM_MODULO

      if p.type == 2:
        client_socket.close()
        break

      # check if within valid range
      if cur_seq_num >= base_mod and cur_seq_num <= windowEnd:
        self.base = self.base + cur_seq_num - base_mod + 1
      elif base_mod > windowEnd and (cur_seq_num <= windowEnd or cur_seq_num >= base_mod):
        if base_mod <= cur_seq_num:
          self.base = self.base + cur_seq_num + 1 - base_mod
        else:
          self.base = self.base + cur_seq_num + 1 + (packet.SEQ_NUM_MODULO - base_mod)
      
      if self.base > prev_base:
        if self.base != self.next_seq_num:
          self.timer = time.time()
        else:
          self.timer = None

  def start(self, file_name):
    # UDP Socket
    client_socket = socket(AF_INET, SOCK_DGRAM)
    client_socket.bind(('', self.sender_port))

    # generate three log files
    file_seqnum = open("seqnum.log","w+")
    file_ack = open("ack.log","w+")

    # read data from file and store it
    buffer = []
    with open(file_name, "rb") as f:
      byte = f.read(500)
      while byte:
        buffer.append(byte)
        byte = f.read(500)

    # start Acknowledger
    acknowledger = threading.Thread(target=self.receive_ack, args=(client_socket,file_ack,))
    acknowledger.start()

    # start sending packets
    total_packets = len(buffer)
    while not (self.base == total_packets):
      if self.next_seq_num < total_packets \
        and self.next_seq_num < self.base + WINDOW_SIZE:
        packet_to_send = packet.create_packet(self.next_seq_num, buffer[self.next_seq_num])
        
        client_socket.sendto(packet_to_send.get_udp_data(), (self.emu_addr, self.emu_port))
        file_seqnum.write(str(self.next_seq_num) + "\n")

        self.next_seq_num = self.next_seq_num + 1

        if self.base == self.next_seq_num:
          self.timer = time.time()
      elif timer and (time.time() - timer) > 0.1:
        # resend packets
        for i in range(self.base, self.next_seq_num):
          packet_to_send = packet.create_packet(i, buffer[i])

          client_socket.sendto(packet_to_send.get_udp_data(), (self.emu_addr, self.emu_port))
          file_seqnum.write(str(i) + "\n")

        timer = time.time()
    
    # send eot
    client_socket.sendto(packet.create_eot(-1).get_udp_data(), (self.emu_addr, self.emu_port))
    acknowledger.join()

    file_seqnum.close()
    file_ack.close()
    

############# MAIN STARTS HERE #############

def check_args(args):
  if len(args) != 4:
    raise Exception

  try:
    emu_addr = args[0]
    emu_port = int(args[1])
    sender_port = int(args[2])
    file_name = args[3]
  except:
    raise Exception

  return emu_addr, emu_port, sender_port, file_name

def main(args):
  try:
    emu_addr, emu_port, sender_port, file_name = check_args(args)
  except Exception:
    exit(-1)

  sender = Sender(emu_addr, emu_port, sender_port, file_name)

  # start sender class
  sender.start(file_name)

  print("Sender Finished!")

# Parameters:
#   $1 - host address of the network emulator
#   $2 - UDP port number used by the emulator to receive data from the sender
#   $3 - UDP port number used by the sender to receive ACKs from the emulator
#   $4 - name of the file to be transferred
main(sys.argv[1:])
