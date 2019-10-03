import sys
from socket import *

def check_inputs(args):
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
  tcp_socket.close()
  return r_port

def udp_transfer(server_address, r_port, message):
	udp_socket = socket(AF_INET, SOCK_DGRAM)
	udp_socket.sendto(message.encode(), (server_address, r_port))
	received_messages = udp_socket.recvfrom(2048)[0]
	udp_socket.close()
	return received_messages

def main(argv):
  try:
    check_inputs(argv)

    server_address = argv[0]
    n_port = int(argv[1])
    req_code = int(argv[2])
    message = argv[3]
  except Exception:
    exit(-1)

  r_port = tcp_negotiate(server_address, n_port, req_code)
  if r_port == 0:
    print("Invalid req_code.")
    exit(-1)

  received_messages = udp_transfer(server_address, r_port, message)
  print("[{}]: {}".format(r_port, received_messages))

  exit(0)

# Run Client
main(sys.argv[1:])