/* Main Sender Class
Parameter:
    $1 - host address of the network emulator
    $2 - UDP port number used by the emulator to receive data from the sender
    $3 - UDP port number used by the sender to receive ACKs from the emulator
    $4 - name of the file to be transferred
*/

import java.io.File;
import java.io.FileInputStream;
import java.io.PrintWriter;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.util.Timer;
import java.util.TimerTask;
import java.lang.Exception;

public class Sender {
  private final int maxDataLength = 500;
  private final int windowSize = 10;
  private final int timeoutLength = 100;

  private String emulatorAddr;
  private int emulatorPort;
  private int senderPort;
  private String fileName;

  private DatagramSocket socket;

  private PrintWriter seqLogFile;
  private PrintWriter ackLogFile;

  private Timer timer;

  private int base;
  private int nextSeqNum;
  private int packetNum;

  private Thread receiver;

  private String[] buf;

  public Sender(String[] args) throws Exception {
    this.emulatorAddr = InetAddress.getByName(args[0]);
    this.emulatorPort = Integer.parseInt(args[1]);
    this.senderPort = Integer.parseInt(args[2]);
    this.fileName = args[3];

    seqLogFile = new PrintWriter("seqnum.log");
    ackLogFile = new PrintWriter("ack.log");

    this.socket = new DatagramSocket(senderPort);

    this.base = 0;
    this.nextSeqNum = 0;
    this.packetNum = 0;
  }

  public static void main(String[] args) throws Exception{
    // check if args are valid
    try {
      this.checkArgs(args);
    } catch(IllegalArgumentException e) {
      System.exit(-1);
    }

    // init object and receiver thread
    Sender sender = new Sender(args);
    receiver = new Thread(new ReceiveAck());

    // start sender and sender's receiver
    receiver.start();
    sender.start();
  }

  private void start() throws Exception {
    FileInputStream is = new FileInputStream(fileName);

    // read data
    try {
      buf = new String[(int) Math.ceil((double) is.available() / (double) maxDataLength)];

      int i = 0;
      while(is.available() > 0) {
        byte[] bytes = new byte[Math.min(maxDataLength, is.available())];
        
        is.read(bytes);
        String data = new String(bytes);
        buf[i++] = data;
      }
    } catch(IOException e) {
      e.printStackTrace();
      System.exit(-1);
    }

    // start sending packets
    /* START TIMER */
    while(packetsAcked < buf.length - 1) {
      System.out.println("packetsAcked = " + packetsAcked);
      System.out.println("packetsSent = " + packetsSent);


    }
  }

  private void checkArgs(String[] args) throws Exception {
    if (args.length != 4) {
      throw new IllegalArgumentException();
    }

    // validate emulator port
    try {
      int emuPort = Integer.parseInt(args[1]); 
      int recPort = Integer.parseInt(args[2]); 
    } catch(NumberFormatException e) {
      throw e;
    }
  }

  public class ReceiveAck() implements Runnable {
    public void run() {
      try {
        receiveAcks();
      } catch(Exception e) {
        e.printStackTrace();
      }
    }
  }
}
