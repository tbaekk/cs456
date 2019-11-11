import java.io.*;
import java.net.*;

public class receiver {
    private static final int ACK = 0;
	private static final int DATA = 1;
	private static final int EOT = 2;

    private static InetAddress emulatorAddr;
    private static int emulatorPort;
    private static int receiverPort;
    private static String fileName;

    private PrintWriter outputLog, arrivalLog;

    DatagramSocket socket;

    private int nextSeqNum = 0;

    public static void main(String[] args) throws Exception{
        receiver r = new receiver();

        // init fields
        r.init(args);

        // start receiver
        r.start();

        // close files and sockets
        r.close();
    }

    private void init(String[] args) throws Exception {
        if (args.length != 4) {
            System.err.println("Receiver: invalid number of arguments");
            System.exit(-1);
        }

        emulatorAddr = InetAddress.getByName(args[0]);
        try {
            // validate port numbers
            emulatorPort = Integer.parseInt(args[1]);
            receiverPort = Integer.parseInt(args[2]);
        } catch (NumberFormatException e) {
            System.err.println("Receiver: invalid port number given");
            System.exit(-1);
        }
        fileName = args[3];

        // create socket
        try {
            socket = new DatagramSocket(receiverPort);
        } catch (SocketException e) {
            System.err.println("Receiver: given port is not available");
        }

        // create files
        try {
            outputLog = new PrintWriter(new BufferedWriter(new FileWriter(fileName)));
            arrivalLog = new PrintWriter(new BufferedWriter(new FileWriter("arrival.log")));
        } catch (IOException e) {
            System.err.println("Sender: failed to create files");
        }
    }

    private void close() throws Exception {
        // close files
        try {
            outputLog.close();
            arrivalLog.close();
        } catch (Exception e) {
            System.err.println("Receiver: cannot close files");
        }

        // close socket
        try {
            socket.close();
        } catch (Exception e) {
            System.err.println("Receiver: failed to close socket");
        }
    }

    private void start() throws Exception {
        while(true) {
            byte[] data = new byte[512];
            DatagramPacket receivePacket = new DatagramPacket(data, data.length);

            socket.receive(receivePacket);

            packet dataPacket = packet.parseUDPdata(receivePacket.getData());

            if (dataPacket.getType() == EOT) {
                // send eot packet
                send( packet.createEOT(dataPacket.getSeqNum()) );
                break;
            } else if (dataPacket.getType() == DATA) {
                arrivalLog.println(dataPacket.getSeqNum());

                if (dataPacket.getSeqNum() == nextSeqNum) {
                    // send acked packet
                    send( packet.createACK(dataPacket.getSeqNum()) );

                    // write data to file
                    byte[] bytes = dataPacket.getData();
                    outputLog.print( new String(bytes) );

                    nextSeqNum = (nextSeqNum + 1) % 32;
                } else {
                    if (nextSeqNum == 0) continue;
                    // send ack for most recent packet
                    send( packet.createACK(nextSeqNum - 1) );
                }
            }
        }
    }

    private void send(packet p) throws Exception {
        byte[] data = p.getUDPdata();
        DatagramPacket sendPacket = new DatagramPacket(data, data.length, emulatorAddr, emulatorPort);
        socket.send(sendPacket);
    }
}
