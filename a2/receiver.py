# Parameters:
#   $1 - hostname for the network emulator
#   $2 - UDP port number used by the link emulator to receive ACKs from the receiver
#   $3 - UDP port number used by the receiver to receive data from the emulator
#   $4 - name of the file into which the received data is written

import sys
import threading
import time
from socket import *
from packet import packet

T_ACK = 0
T_DATA = 1
T_EOT = 2

class Receiver:

  def __init__(self):
    self.packet_num = 0

  def run(self):
    global T_DATA
    global T_EOT
    global server_socket
    global emu_addr
    global emu_port
    global f_output
    global f_arrival

    while True:
      data, server_addr = server_socket.recvfrom( 2048 )
      p = packet.parse_udp_data(data)

      f_arrival.write(str(p.seq_num) + "\n")

      send_packet = None
      if p.type == T_DATA:
        if p.seq_num == self.packet_num % packet.SEQ_NUM_MODULO:          
          f_output.write(p.data) # read and write to file
          self.packet_num += 1
        send_packet = packet.create_ack(self.packet_num - 1)
        if not self.packet_num == 0: # if received atleast one good packet
          server_socket.sendto(send_packet.get_udp_data(), (emu_addr, emu_port))
      elif p.type == T_EOT:
        send_packet = packet.create_eot(self.packet_num)
        server_socket.sendto(send_packet.get_udp_data(), (emu_addr, emu_port))
        break

############# MAIN STARTS HERE #############

def check_args(args):
  if len(args) != 4:
    raise Exception
  try:
    emu_addr = args[0]
    emu_port = int(args[1])
    receiver_port = int(args[2])
    file_name = args[3]
  except Exception as e:
    raise e

  return emu_addr, emu_port, receiver_port, file_name

# Check if command-line arguments are valid
try:
  emu_addr, emu_port, receiver_port, file_name = check_args(sys.argv[1:])
except Exception:
  print("ERROR: invalid number of arguments")
  exit(-1)

# Create UDP Socket
server_socket = socket(AF_INET, SOCK_DGRAM) 
server_socket.bind(('', receiver_port))

# Generate three log files
f_output = open(file_name,"w")
f_arrival = open("arrival.log","w")

# Start receiving
receiver = Receiver()
receiver.run()

# Close socket
server_socket.close()

# Close files
f_output.close()
f_arrival.close()
