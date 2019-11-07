import sys

def check_args(args):
  if len(args) != 4:
    raise Exception

  try:
    emulator_addr = args[0]
    emulator_port = int(args[1])
    receiver_port = int(args[2])
    file_name = args[3]
  except:
    raise Exception

  return emulator_addr, emulator_port, receiver_port, file_name

def main(args):
  try:
    emulator_addr, emulator_port, receiver_port, file_name = check_args(args)
  except Exception:
    exit(-1)
  
# Parameters:
#   $1 - hostname for the network emulator
#   $2 - UDP port number used by the link emulator to receive ACKs from the receiver
#   $3 - UDP port number used by the receiver to receive data from the emulator
#   $4 - name of the file into which the received data is written
main(sys.argv[1:])
