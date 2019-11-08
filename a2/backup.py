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
    global T_EOT
    global lock
    global client_socket
    global unacked_packets
    global timer
    global end_of_transmission
    global f_ack

    while True:
      data, client_addr = client_socket.recvfrom(2048)
      p = packet.parse_udp_data(data)

      if p.type == T_EOT:
        lock.acquire()
        end_of_transmission = True
        lock.release()
        break
      
      # Record seq_num for acked packets
      f_ack.write(str(p.seq_num) + "\n")

      lock.acquire()
      duplicate = True
      i = 0
      for i in range(len(unacked_packets)):
        if unacked_packets[i].seq_num == p.seq_num:
          duplicate = False
          break
        if not duplicate:
          if i == 0:
            unacked_packets.pop(i)
            timer.pop(i)
          else:
            unacked_packets = unacked_packets[i:]
            timer = timer[i:]
      lock.release()

class Sender(threading.Thread):

  def __init__(self):
    super(Sender, self).__init__()
    self.seq_num = 0

  def send(self, p):
    global client_socket
    global unacked_packets
    global timer
    global emu_addr
    global emu_port
    global f_seqnum

    unacked_packets.append(p)
    
    client_socket.sendto(p.get_udp_data(), (emu_addr, emu_port))

    # Add time
    timer.append(time.time())
    # Record seq_num
    f_seqnum.write(str(p.seq_num) + "\n")

  def run(self):
    global WINDOW_SIZE
    global TIMEOUT
    global lock
    global client_socket
    global unacked_packets
    global timer
    global buffer
    global emu_addr
    global emu_port
    
    num_packets = len(buffer)
    for i in range(num_packets):
      new_packet = packet.create_packet(self.seq_num, buffer[i])
      self.seq_num += 1
      print("SENDER: seq_num={}".format(self.seq_num))
      print("SENDER: timer={}".format(timer))
      print("SENDER: unacked_packets={}".format(unacked_packets))
      while True:
        lock.acquire()
        # print("SENDER: len(unacked_packets)={}".format(len(unacked_packets)))
        if len(unacked_packets) < 10:
          self.send(new_packet)
          lock.release()
          break
        elif time.time() - timer[0] > TIMEOUT:
          timer.clear()
          # Resend all unacked packets
          for unacked_packet in unacked_packets:
            self.send(unacked_packet)
          unacked_packets.clear()
        lock.release()
    print("SENDER: Sent all packets")
    # Wait for all acked packets
    while True:
      lock.acquire()
      if len(unacked_packets) == 0: break
      if time.time() - timer[0] > TIMEOUT:
        # Resend all unacked packets
        resend = []
        for unacked_packet in unacked_packets:
          resend.append(unacked_packet)
        timer.clear()
        unacked_packets.clear()
        for p in resend:
          self.send(p)
      lock.release()
    print("SENDER: Received all acked packets")
    # Send EOT when all acked packets received
    eot_packet = packet.create_eot(self.seq_num)
    client_socket.sendto(eot_packet.get_udp_data(), (emu_addr, emu_port))


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

lock = threading.Lock()
unacked_packets = []
timer = []
end_of_transmission = False

# Read file and store into buffer
buffer = []
with open(file_name, "r") as f:
  byte = f.read(500)
  while byte:
    buffer.append(byte)
    byte = f.read(500)

# Create UDP Socket
client_socket = socket(AF_INET, SOCK_DGRAM)
client_socket.bind(('', sender_port))

# Generate three log files
f_seqnum = open("seqnum.log","w")
f_ack = open("ack.log","w")

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

# Close files
f_seqnum.close()
f_ack.close()
