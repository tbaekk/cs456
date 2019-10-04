import sys
from thread import *
from socket import *

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

def tcp_negotiate(server_socket, req_code):
  waiting = True
  while waiting:
    connection_socket, addr = server_socket.accept()
    client_req_code = connection_socket.recv(1024).decode()
    
    if not int(client_req_code) == req_code:
      print("Invalid request code received from client")
      message = str(0)
    else:
      # Create UDP socket
      transmission_socket, r_port = gen_udp_socket()
      message = str(r_port)
      waiting = False

    connection_socket.send(message.encode())
    connection_socket.close()
  
  return transmission_socket, r_port

def udp_transfer(client_messages, transmission_socket, r_port):
  while True:
    message, client_addr = transmission_socket.recvfrom(2048)
    if message == "TERMINATE":
      raise Exception
    elif message == "GET":
      for msg in client_messages:
        transmission_socket.sendto(msg.encode(), client_addr)
      transmission_socket.sendto("NO MSG.".encode(), client_addr)
    else:
      client_messages.append("[{}]: {}".format(r_port, message))
      break
  return

def main(argv):
  server_on = True
  try:
    req_code = check_req_code(argv)
  except Exception:
    exit(-1)

  # Create TCP socket
  server_socket, n_port = gen_tcp_socket()
  print("SERVER_PORT={}".format(n_port))

  client_messages = []
  while server_on:
    # 1. Negotiate, over TCP, a communications port
    transmission_socket, r_port = tcp_negotiate(server_socket,req_code)

    # 2. Transfer message back to client over UDP or store message
    try:
      udp_transfer(client_messages, transmission_socket, r_port)
    except Exception:
      server_on = False

    transmission_socket.close()

  exit()

# Run Server
main(sys.argv[1:])
