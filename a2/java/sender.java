/*
Parameter:
    $1 - host address of the network emulator
    $2 - UDP port number used by the emulator to receive data from the sender
    $3 - UDP port number used by the sender to receive ACKs from the emulator
    $4 - name of the file to be transferred
*/

import java.io.*;
import java.net.*;
import java.util.ArrayList;
import java.util.List;
import java.lang.IllegalArgumentException;


public class sender {
  private static final int windowSize = 10;
  private static final int maxDataLength = 500;
  private static final int timeoutLength = 100;
  private static final int SeqNumModulo = 32;

  private int packetsSent = -1;
  private int packetsAcked = -1;

  long startTime;
  boolean isTimerRunning = false;

  private InetAddress emulatorAddr;
  private int emulatorPort;
  private int senderPort;
  private String fileName;

  private List<packet> packets;

  private PrintStream seqNumLog, ackLog;

  private DatagramSocket socket;

  /********************************
    Sender's Ack Receiver Thread
  *********************************/
  public class AckReceiver implements Runnable {

    @Override
    public void run(){
      byte[] data = new byte[512];
      DatagramPacket receivePacket = new DatagramPacket(data, data.length);
      
      packet p;

      /* allow the go() method in main thread some time to set up */
      try {
        Thread.sleep(50);

        while(true) {
          /* receive ACK packets from receiver until EOT */
          socket.receive(receivePacket);
          p = packet.parseUDPdata(data);
          int seqNum = p.getSeqNum();
          int type = p.getType();

          if(type == packet.EOT){
            break;
          }

          ackLog.println(seqNum);

          if (seqNum == packetsAcked){
            /* server didn't receive packets in order. */
            // do nothing, wait for timeout
          } else {
            /* server received some packets in order, so we can move packetsAcked forward */
            int offset = Math.floorMod((seqNum - packetsAcked), SeqNumModulo);
            packetsAcked = packetsAcked + offset;
            if(packetsAcked == packetsSent){
              System.out.println(" Type: fully correct ACK");
              // if all packets currently sent have been Acked, stop timer.
              isTimerRunning = false;
              System.out.println("stop timer! (in ACK thread");
            } else {
              System.out.println(" Type: partly correct ACK");
              // else, restart timer
              startTime = System.currentTimeMillis();
              System.out.println("restart timer! (in ACK thread");
            }
          }
        }
      } catch (Exception e) {
        return;
      }
    }
  }


  /********************************
          Main Starts Here
  *********************************/
  public static void main(String[] args) throws Exception{
    // check if args are valid
    // try {
    //   checkArgs(args);
    // } catch(IllegalArgumentException e) {
    //   System.err.println("Sender: invalid number of arguments");
    //   System.exit(-1);
    // }

    sender packetSender = new sender();

    packetSender.start(args);
  }

  private void start(String[] args) throws Exception {
    emulatorAddr = InetAddress.getByName(args[0]);
    emulatorPort = Integer.parseInt(args[1]);
    senderPort = Integer.parseInt(args[2]);
    fileName = args[3];

    try {
      seqNumLog = new PrintStream(new File("seqnum.log"));
      ackLog = new PrintStream(new File("ack.log"));
    } catch (IOException e) {
      System.err.println("Sender: failed to create log files");
      System.exit(-1);
    }

    try{
      socket = new DatagramSocket(senderPort);
    } catch (SocketException e) {
      System.err.println("Sender: the port is not avaliable");
      System.exit(-1);
    }

    try {
      packets = makePackets();
    } catch(Exception e) {
      System.err.println("Sender: failed to create packets");
      System.exit(-1);
    }

    // init and start thread
    Thread ackReceiver = new Thread(new AckReceiver());
    ackReceiver.start();

    // start send
    run();

    // wait for threads to finish
    try {
      ackReceiver.join();
    } catch (Exception e) {
      System.err.println("Sender: something happened in thread");
    }

    // close files
    seqNumLog.close();
    ackLog.close();

    // close socket
    socket.close();
  }

  private void run() throws Exception {
    while (packetsAcked < packets.size() - 1) {
      System.out.println("packetsAcked = " + packetsAcked);
      System.out.println("packetsSent = " + packetsSent);

      int start = packetsSent + 1;
      int windowSizeLeft = windowSize - (packetsSent - packetsAcked);
      int numOfPacketsLeft = (packets.size() - 1) - packetsSent;
      if (windowSizeLeft > 0 && numOfPacketsLeft > 0) {
        int length = Math.min(windowSizeLeft, numOfPacketsLeft);
        if (!isTimerRunning) {
          startTime = System.currentTimeMillis();
          isTimerRunning = true;
        }
        
        // send packets
        for(int i = start; i < start + length; i++){
          byte data[] = packets.get(i).getUDPdata();
          DatagramPacket sendPacket = new DatagramPacket(data, data.length, emulatorAddr, emulatorPort);
          socket.send(sendPacket);

          System.out.println("packet sent: " + packets.get(i).getSeqNum());

          seqNumLog.println(packets.get(i).getSeqNum());
        }
        packetsSent = start + length - 1;
      } else {
        /* The window is full. Try sending the packets later (let the main thread sleep for a while) */
      }
      /* poll every 30 milliseconds to check whether timeout happened */
      Thread.sleep(30);
      long current_time = System.currentTimeMillis();
      long elapsed_time = current_time - startTime;

      if(elapsed_time >= timeoutLength && isTimerRunning) {
        isTimerRunning = false;
        packetsSent = packetsAcked;
      }
    }
  }

  private ArrayList<packet> makePackets() {
    try {
      FileInputStream fis = new FileInputStream(fileName);

      int seqNum = 0;

      ArrayList<packet> packets = new ArrayList<>();
    
      while(fis.available() > 0) {
        byte[] bytes = new byte[Math.min(maxDataLength, fis.available())];
        fis.read(bytes);
        String data = new String(bytes);

        packets.add(packet.createPacket(seqNum, data));
        seqNum = (seqNum + 1) % 32;
      }
      fis.close();

      return packets;
    } catch(Exception e) {
      System.err.println("Sender: failed to create packets");
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
}
