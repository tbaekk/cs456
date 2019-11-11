# CS456 A2

## Instructions
1. Compile Java files by calling
```
make
```
2. Run nEmulator on machine1 (e.g ubuntu1604-002.student.cs.uwaterloo.ca)
```
./nEmulator-linux386 <emulator's receiving UDP port number in the forward (sender) direction> 
                     <receiver’s network address>
                     <receiver’s receiving UDP port number>
                     <emulator's receiving UDP port number in the backward (receiver) direction>
                     <sender’s network address>
                     <sender’s receiving UDP port number>
                     <maximum delay of the link in units of millisecond>
                     <packet discard probability 0 <= p <= 1 >
                     <verbose-mode>
```
3. Run Receiver on machine2 (e.g ubuntu1604-004.student.cs.uwaterloo.ca)
```
./server.sh <hostname for the network emulator>
            <UDP port number used by the link emulator to receive ACKs from the receiver>
            <UDP port number used by the receiver to receive data from the emulator>
            <input file>
```
4. Run Sender on machine3 (e.g ubuntu1604-008.student.cs.uwaterloo.ca)
```
./client.sh <host address of the network emulator>
            <UDP port number used by the emulator to receive data from the sender>
            <UDP port number used by the sender to receive ACKs from the emulator>
            <output file>
```
