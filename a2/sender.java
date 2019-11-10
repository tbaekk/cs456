import java.io.*;
import java.net.*;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.locks.ReentrantLock;

public class sender {
    private final static int windowSize = 10;
    private final static int maxDataLength = 500;
    private final static int timeoutLength = 100;

    private static InetAddress emulatorAddr;
    private static int emulatorPort;
    private static int senderPort;
    private static String fileName;

    private List<packet> packets;

    private PrintStream seqnumLog, ackLog, timeLog;

    private ReentrantLock lock;

    DatagramSocket socket;

    long startTime;
    boolean timerRunning = false;

    private int packetsSent = -1;
    private int packetsAcked = -1;

    public static void main(String[] args) throws Exception{
        if (args.length != 4) {
            System.err.println("Sender: invalid number of arguments");
            System.exit(-1);
        }
        // validate emulator port
        try {
            int emuPort = Integer.parseInt(args[1]); 
            int recPort = Integer.parseInt(args[2]); 
        } catch (NumberFormatException e) {
            System.err.println("Sender: invalid port number given");
            System.exit(-1);
        }

        sender s = new sender();

        // init fields
        s.init(args);

        // init and start threads
        Thread t1 = new Thread(s.new AckReceiver());
        t1.start();
        
        Thread t2 = new Thread(s.new PacketSender());
        t2.start();

        // wait for threads to finish
        try {
            t1.join();
            t2.join();
        } catch (Exception e) {
            System.err.println("Sender: waiting thread crashed!");
        }

        // close files and sockets
        s.close();
    }

    private void init(String[] args) throws Exception {
        emulatorAddr = InetAddress.getByName(args[0]);
        emulatorPort = Integer.parseInt(args[1]);
        senderPort = Integer.parseInt(args[2]);
        fileName = args[3];

        socket = new DatagramSocket(senderPort);

        // create files
        seqnumLog = new PrintStream(new File("seqnum.log"));
        ackLog = new PrintStream(new File("ack.log"));
        timeLog = new PrintStream(new File("time.log"));

        // make packets
        packets = makePackets();

        // create locks
        lock = new ReentrantLock();
    }

    private void close() throws Exception {
        // close files
        try {
            seqnumLog.close();
            ackLog.close();
            timeLog.close();
        } catch (Exception e) {
            System.err.println("Sender: cannot close files");
        }

        // close socket
        try {
            socket.close();
        } catch (Exception e) {
            System.err.println("Sender: failed to close socket");
        }
    }

    private ArrayList<packet> makePackets() throws Exception {        
        ArrayList<packet> packets = new ArrayList<>();
        FileInputStream fis = new FileInputStream(fileName);
        
        int seqNum = 0;
        while(fis.available() > 0) {
            byte[] bytes = new byte[Math.min(maxDataLength, fis.available())];
            fis.read(bytes);
            String data = new String(bytes);

            packets.add(packet.createPacket(seqNum, data));
            seqNum = (seqNum + 1) % 32;
        }
        fis.close();

        return packets;
    }

    public void send(packet p) throws Exception {
        byte data[] = p.getUDPdata();
        DatagramPacket sendPacket = new DatagramPacket(data, data.length, emulatorAddr, emulatorPort);
        socket.send(sendPacket);
    }

    public void startTimer() throws Exception{
        startTime = System.currentTimeMillis();
    }

    public void stopTimer() throws Exception {
        timerRunning = false;
    }

    /***********************************
            Packet Sender Thread
    ************************************/
    public class PacketSender implements Runnable {
        public void run() {
            try {
                sendPackets();
            } catch(Exception e) {
                e.printStackTrace();
            }
        }

        private void sendPackets() throws Exception {
             /* send packets to the emulator until all packets have been acknowledged */
            while (packetsAcked < packets.size() - 1) {
                int base = packetsSent + 1;
                int windowSizeLeft = windowSize - (packetsSent - packetsAcked);

                if (windowSizeLeft > 0 && (packets.size() - 1) - packetsSent > 0) {
                    int offset = Math.min(windowSizeLeft, (packets.size() - 1) - packetsSent);
                    if (!timerRunning) {
                        lock.lock();
                            startTimer();
                            timerRunning = true;
                        lock.unlock();
                    }

                    for (int i = base; i < base + offset; i++) {
                        send(packets.get(i));
                        seqnumLog.println(packets.get(i).getSeqNum());
                    }

                    lock.lock();
                        packetsSent = base + offset - 1;
                    lock.unlock();
                }

                Thread.sleep(30);
                long currentTime = System.currentTimeMillis();
                long deltaTime = currentTime - startTime;

                if (deltaTime >= timeoutLength && timerRunning) {
                    lock.lock();
                        stopTimer();
                        packetsSent = packetsAcked;
                    lock.unlock();
                }
            }

            // send EOT packet
            packet eotPacket = packet.createEOT(packets.size() % 32);
            send(eotPacket);
        }
    }

    /***********************************
            Ack Receiver Thread
    ************************************/
    public class AckReceiver implements Runnable{
        public void run() {
            try{
                receivePackets();
            } catch(Exception e) {
                e.printStackTrace();
            }
        }

        private void receivePackets() throws Exception {
            byte[] data = new byte[512];
            DatagramPacket receivePacket = new DatagramPacket(data, data.length);

            Thread.sleep(50);

            packet dataPacket;
            while(true) {
                // receive ACKed packets
                socket.receive(receivePacket);
                dataPacket = packet.parseUDPdata(data);

                if (dataPacket.getType() == packet.EOT) {
                    break;
                }

                int seqNum = dataPacket.getSeqNum();
                ackLog.println(seqNum);

                if (seqNum == packetsAcked) {
                    // do nothing, wait for timeout
                } else {
                    int offset = Math.floorMod((seqNum - packetsAcked), 32);

                    lock.lock();
                        packetsAcked = packetsAcked + offset;
                    lock.unlock();

                    lock.lock();
                    if (packetsAcked == packetsSent) {
                        stopTimer();
                    } else {
                        startTimer();
                    }
                    lock.unlock();
                }
            }
        }
    }
}
