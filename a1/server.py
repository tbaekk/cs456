import sys
from thread import *
from socket import *

GET = "GET"
TERMINATE = "TERMINATE"
global_queue = []
client_messages = []

def check_req_code(args):
  if len(args) != 1:
    print("Invalid number of parameters")
    raise Exception

  try:
    req_code = int(args[0])
  except:
    print("Parameter <req_code> should be an integer")
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

def start_communication(connection_socket, server_socket, req_code):
  # 1. Negotiate, over TCP, a communications port
  client_req_code = connection_socket.recv(1024).decode()
  
  if not int(client_req_code) == req_code:
    print("Invalid request code received from client")
    connection_socket.send("0".encode())
    connection_socket.close()
    return
  
  # Create UDP socket
  transmission_socket, r_port = gen_udp_socket()
  message = str(r_port)

  connection_socket.send(message.encode())
  connection_socket.close()

  # 2. Transfer message back to client over UDP or store message
  while True:
    message, client_addr = transmission_socket.recvfrom(2048)
    if message == GET:
      for msg in client_messages:
        transmission_socket.sendto(msg.encode(), client_addr)
      transmission_socket.sendto("NO MSG.".encode(), client_addr)
    elif message == TERMINATE:
      global_queue.append(message)
      break
    else:
      client_messages.append("[{}]: {}".format(r_port, message))
      break

  transmission_socket.close()

def main(argv):
  try:
    req_code = check_req_code(argv)
  except Exception:
    exit(-1)

  # Create TCP socket
  server_socket, n_port = gen_tcp_socket()
  print("SERVER_PORT={}".format(n_port))

  while True:
    connection_socket, addr = server_socket.accept()
    if TERMINATE in global_queue:
      break
    # Start new thread after new connection is accepted
    start_new_thread(start_communication, (connection_socket, server_socket, req_code,))

  exit()

# Run Server
main(sys.argv[1:])
