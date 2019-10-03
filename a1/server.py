import sys
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
    client_req_code = connection_socket.recv(1024)
    
    message = str(0)
    if not int(client_req_code) == req_code:
      print("Invalid request code received from client")
    else:
      # Create UDP socket
      transmission_socket, r_port = gen_udp_socket()
      message = str(r_port)
      waiting = False

    connection_socket.send(message.encode())
    connection_socket.close()
  
  return transmission_socket

def udp_transfer(transmission_socket):
  message, client_addr = transmission_socket.recvfrom(2048)
  transmission_socket.sendto(message, client_addr)
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
    # Begin TCP Negotiation
    transmission_socket = tcp_negotiate(server_socket,req_code)
    # Transfer message through UDP
    udp_transfer(transmission_socket)


# Run Server
main(sys.argv[1:])
