# CS456 A2

## Instructions
To run the receivr: java receiver <host_address> <udp_port> <sender_port>
- <host_address>: host address of the network emulator
- <UDP port number used by the emulator to receive data from the sender>\
- <UDP port number used by the sender to receive ACKs from the emulator>\
- <name of the file to be transferred>
To run the client: ./client.sh <server_address> <n_port> <req_code> <msg>

## Parameters
<server_address>: string, the IP address of the server \
<n_port>: int, the negotiation port number of the server \
<req_code>: int, user-specified \
\<msg>: string, a string that you want to send
