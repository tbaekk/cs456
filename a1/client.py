import sys
from socket import *

def check_args(args):
  if len(args) != 4:
    print("Invalid number of parameters")
    raise Exception
  
  try:
    server_address = args[0]
    n_port = int(args[1])
    req_code = int(args[2])
    message = args[3]

    if not message or not server_address:
      raise error
  except error:
    print("Values missing for required parameters")
  except:
    print("Parameter <n_port> and <req_code> should be integers")
    raise Exception

  return

def tcp_negotiate(server_address, n_port, req_code):
  try:
    tcp_socket = socket(AF_INET, SOCK_STREAM)
    tcp_socket.connect((server_address,n_port))
  except error:
    print("Negotiation port unavailable")

  tcp_socket.send(str(req_code).encode())
  r_port = int(tcp_socket.recv(1024))

  return tcp_socket, r_port

def main(args):
  try:
    check_args(args)

    server_address = args[0]
    n_port = int(args[1])
    req_code = int(args[2])
    message = args[3]
  except Exception:
    exit(-1)

  # 1. Negotiate, over TCP, a communications port
  tcp_socket, r_port = tcp_negotiate(server_address, n_port, req_code)
  if r_port == 0:
    print("Invalid req_code.")
    exit(-1)

  # 2. Retrieving the stored messages from the server
  udp_socket = socket(AF_INET, SOCK_DGRAM)
  udp_socket.sendto("GET".encode(), (server_address, r_port))

  received_message = ""
  while received_message != "NO MSG.":
    received_message = udp_socket.recvfrom(2048)[0].decode()
    print(received_message)

  # 3. Adding a message to the server
  udp_socket.sendto(message.encode(), (server_address, r_port))
  udp_socket.close()

  print()
  input("Press any key to exit.")
  tcp_socket.close()

  exit()

# Run Client
main(sys.argv[1:])