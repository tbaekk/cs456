import java.io.*;
import java.net.*;

public class receiver {
    private static InetAddress emulatorAddr;
    private static int emulatorPort;
    private static int receiverPort;
    private static String fileName;

    private PrintWriter outputLog, arrivalLog;

    DatagramSocket socket;

    private int expect = 0;

    public static void main(String[] args) throws Exception{
        if (args.length != 4) {
            System.err.println("Receiver: invalid number of arguments");
            System.exit(-1);
        }
        // validate emulator port
        try {
            int emuPort = Integer.parseInt(args[1]); 
            int recPort = Integer.parseInt(args[2]); 
        } catch (NumberFormatException e) {
            System.err.println("Receiver: invalid port number given");
            System.exit(-1);
        }

        receiver r = new receiver();

        // init fields
        r.init(args);

        // start receiver
        r.start();

        // close files and sockets
        r.close();
    }

    private void init(String[] args) throws Exception {
        emulatorAddr = InetAddress.getByName(args[0]);
        emulatorPort = Integer.parseInt(args[1]);
        receiverPort = Integer.parseInt(args[2]);
        fileName = args[3];

        socket = new DatagramSocket(receiverPort);

        // create files
        outputLog = new PrintWriter(new BufferedWriter(new FileWriter(fileName)));
        arrivalLog = new PrintWriter(new BufferedWriter(new FileWriter("arrival.log")));
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
        packet dataPacket;
        while(true) {
            byte[] data = new byte[512];
            DatagramPacket receivePacket = new DatagramPacket(data, data.length);

            socket.receive(receivePacket);

            dataPacket = packet.parseUDPdata(receivePacket.getData());

            int type = dataPacket.getType();
            if (type == packet.EOT) {
                // send eot packet
                send( packet.createEOT(dataPacket.getSeqNum()) );
                break;
            } else if (type == packet.DATA) {
                // normal packets
                arrivalLog.println(dataPacket.getSeqNum());

                if (dataPacket.getSeqNum() == expect) {
                    // send acked packet
                    send( packet.createACK(dataPacket.getSeqNum()) );

                    // write data to file
                    byte[] bytes = dataPacket.getData();
                    outputLog.print( new String(bytes) );

                    expect = (expect + 1) % 32;
                } else {
                    /* if packet 0 got lost, don't ACK or log */
                    if (expect == 0) {
                        continue;
                    }
                    /* Wrong packet. Send an ACK for the most recently received correct packet,
                     and discard the currently received packet. */
                    send( packet.createACK((expect-1) % 32) );
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
