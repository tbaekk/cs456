import sys
import queue
import threading
from _thread import *
from socket import *

############# GLOBAL CONSTANTS #############

GET = "GET"
TERMINATE = "TERMINATE"
STATUS_OFF = 0
STATUS_ON = 1

############################################

############# GLOBAL VARIABLES #############

client_messages = []
termination_status = queue.Queue()

############################################


def check_args(args):
  if len(args) != 1:
    raise Exception

  try:
    req_code = int(args[0])
  except:
    raise Exception

  return req_code

def gen_tcp_socket():
  tcp_socket = socket(AF_INET, SOCK_STREAM)
  tcp_socket.bind(('',0))
  tcp_socket.listen(1)
  n_port = tcp_socket.getsockname()[1]
  
  return tcp_socket, n_port

def gen_udp_socket():
  udp_socket = socket(AF_INET, SOCK_DGRAM)
  udp_socket.bind(('',0))
  r_port = udp_socket.getsockname()[1]

  return udp_socket, r_port

def start_socket(connection_socket, req_code):
  r_port = 0
  # 1. Negotiate, over TCP, a communications port
  client_req_code = connection_socket.recv(1024).decode()
  
  # Verify if req_code matches the one sent from client
  if not int(client_req_code) == req_code:
    connection_socket.send(str(r_port).encode())
    connection_socket.close()
    termination_status.put(STATUS_OFF)
    return
  
  # 2. Create UDP socket
  transmission_socket, r_port = gen_udp_socket()

  connection_socket.send(str(r_port).encode())
  connection_socket.close()

  # 3. Handle messages sent from client

  # Transfer message back to client over UDP
  message, client_addr = transmission_socket.recvfrom(2048)

  if message.decode() == GET:
    for msg in client_messages:
      transmission_socket.sendto(msg.encode(), client_addr)
    transmission_socket.sendto("NO MSG.".encode(), client_addr)

  # Store message or termiante server
  message, client_addr = transmission_socket.recvfrom(2048)
  if message.decode() == TERMINATE:
    termination_status.put(STATUS_ON)
  else:
    termination_status.put(STATUS_OFF)
    client_messages.append("[{}]: {}".format(r_port, message.decode()))
    
  transmission_socket.close()

def main(args):
  try:
    req_code = check_args(args)
  except Exception:
    exit(-1)

  # Create TCP socket
  server_socket, n_port = gen_tcp_socket()
  print("SERVER_PORT={}".format(n_port))

  termination_status.put(STATUS_OFF)
  while True:
    if termination_status.get() == STATUS_ON:
      break
    connection_socket, addr = server_socket.accept()
    # Start new thread after new connection is accepted
    start_new_thread(start_socket, (connection_socket,req_code,))
  
  server_socket.close()

# Run Server
main(sys.argv[1:])
