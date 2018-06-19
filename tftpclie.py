#!/usr/bin/env python3

# Import tkinter for GUI
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog
from tkinter import messagebox

# Import configparse for configuration ini file
import configparser

# Import stuff to create threads
import threading
from time import sleep

# Import socket stuff
import ipaddress
import socket
import struct

class TftpClientGui:
    """TFTP Client GUI class"""

    def __init__(self, master, tftpComm):
        """Create the GUI"""
        # TODO: Lock GUI during transfer
        self.hostIpStr = StringVar()
        self.hostIpStr.trace("w", self.ipStringCallback)

        self.portStr = StringVar()
        self.portStr.trace("w", self.portStringCallback)

        self.localFileStr = StringVar()
        self.localFileStr.trace("w", self.localFileStrCallback)

        self.remoteFileStr = StringVar()
        self.remoteFileStr.trace("w", self.remoteFileStrCallback)

        self.timeoutStr = StringVar()
        self.timeoutStr.trace("w", self.timeoutStrCallback)

        self.master = master
        self.tftpComm = tftpComm

        master.title("TFTP Client")

        self.hostLabel = Label(master, text="Host")
        self.hostLabel.grid(sticky="W", row=1, column=1, padx=5, pady=5)

        self.hostTextInput = Entry(master, width=16, textvariable=self.hostIpStr)
        self.hostTextInput.grid(sticky="W", row=1, column=2, padx=5, pady=5)

        self.portLabel = Label(master, text="Port")
        self.portLabel.grid(sticky="W", row=1, column=3, padx=5, pady=5)

        self.portTextInput = Entry(master, width=10, textvariable=self.portStr)
        self.portTextInput.grid(sticky="W", row=1, column=4, padx=5, pady=5)

        self.localFileLabel = Label(master, text="Local File")
        self.localFileLabel.grid(sticky="W", row=2, column=1, padx=5, pady=5)

        self.localFileTextInput = Entry(master, width=30, textvariable = self.localFileStr)
        self.localFileTextInput.grid(sticky="W", row=2, column=2, padx=5, pady=5)

        self.localFileSelectButton = Button(master, text= "...", command=self.selectLocalFile)
        self.localFileSelectButton.grid(sticky="W", row=2, column=3, padx=5, pady=5)

        self.remoteFileLabel = Label(master, text="Remote File")
        self.remoteFileLabel.grid(sticky="W", row=3, column=1, padx=5, pady=5)

        self.remoteFileTextInput = Entry(master, width=30, textvariable = self.remoteFileStr)
        self.remoteFileTextInput.grid(sticky="W", row=3, column=2, padx=5, pady=5)

        self.timeoutLabel = Label(master, text="Timeout")
        self.timeoutLabel.grid(sticky="W", row=4, column=1, padx=5, pady=5)

        self.timeoutTextInput = Entry(master, width=30, textvariable = self.timeoutStr)
        self.timeoutTextInput.grid(sticky="W", row=4, column=2, padx=5, pady=5)

        self.timeoutUnitLabel = Label(master, text="ms")
        self.timeoutUnitLabel.grid(sticky="W", row=4, column=3, padx=5, pady=5)

        self.getButton = Button(master, text="Get", command=self.getTftp)
        self.getButton.grid(sticky="W", row=5, column=1, padx=5, pady=5)

        self.putButton = Button(master, text="Put", command=self.putTftp)
        self.putButton.grid(sticky="W", row=5, column=2, padx=5, pady=5)

        self.breakButton = Button(master, text="Break", command=self.breakTftp)
        self.breakButton.grid(sticky="W", row=5, column=3, padx=5, pady=5)

        self.progressBar = Progressbar(master, orient="horizontal", length=400, mode="determinate")
        self.progressBar.grid(row=6, column=1, columnspan=4, padx=5, pady=5)

        self.statisticsButton = Button(master, text="Statistics", command=self.showStatistics)
        self.statisticsButton.grid(row=7, column=2, padx=5, pady=5)

        # Load config
        self.config = configparser.ConfigParser()
        self.loadConfiguration(self.config)

    def loadConfiguration(self, config):
        """Load configuration from configuration file"""
        self.config.read('config.ini')
        self.hostIpStr.set(self.config.get('gui', 'ip', fallback=''))
        self.portStr.set(self.config.get('gui', 'port', fallback=''))
        self.localFileStr.set(self.config.get('gui', 'localFile', fallback=''))
        self.remoteFileStr.set(self.config.get('gui', 'remoteFile', fallback=''))
        self.timeoutStr.set(self.config.get('gui', 'timeout', fallback=''))

    def getTftp(self):
        """Perform get command"""
        self.setGui(False)
        self.tftpComm.transferTftp(self.hostTextInput.get().strip(), 
                                   self.portTextInput.get().strip(), 
                                   self.remoteFileTextInput.get().strip(), 
                                   self.localFileTextInput.get().strip(), 
                                   int(self.timeoutStr.get()), 
                                   True, 
                                   self.progressBar,
                                   self.doneCallback)

    def putTftp(self):
        """Perform put command"""
        self.setGui(False)
        self.tftpComm.transferTftp(self.hostTextInput.get().strip(), 
                                   self.portTextInput.get().strip(), 
                                   self.remoteFileTextInput.get().strip(), 
                                   self.localFileTextInput.get().strip(), 
                                   int(self.timeoutStr.get()), 
                                   False, 
                                   self.progressBar,
                                   self.doneCallback)

    def doneCallback(self, nPackets, bytesLastPacket, fileSize):
        """Call this function to clean up the GUI after a transfer and record statistics"""
        self.setGui(True)
        messagebox.showinfo("Last transmission statistics", "Packets sent: " + str(nPackets) + "\n" + "Last packet size: " + str(bytesLastPacket) + "\n" + "File size: " + str(fileSize) + "\n")
        self.config.read('config.ini')

        historic_nPackets = int(self.config.get('statistics', 'historic_nPackets', fallback='0'))
        historic_bytesLastPacket = int(self.config.get('statistics', 'historic_bytesLastPacket', fallback='0'))
        historic_fileSize = int(self.config.get('statistics', 'historic_fileSize', fallback='0'))

        historic_nPackets += nPackets
        historic_bytesLastPacket += bytesLastPacket
        historic_fileSize += fileSize

        self.writeConfig(self.config, 'statistics', 'last_nPackets', str(nPackets))
        self.writeConfig(self.config, 'statistics', 'last_bytesLastPacket', str(bytesLastPacket))
        self.writeConfig(self.config, 'statistics', 'last_fileSize', str(fileSize))

        self.writeConfig(self.config, 'statistics', 'historic_nPackets', str(historic_nPackets))
        self.writeConfig(self.config, 'statistics', 'historic_fileSize', str(historic_fileSize))

    def breakTftp(self):
        """Break ongoing command"""
        self.tftpComm.breakTftp()

    def showStatistics(self):
        """Show statistics"""
        self.config.read('config.ini')
        messagebox.showinfo("Statistics", "Packets sent: " + self.config.get('statistics', 'last_nPackets', fallback='0') + "\n" 
                                        + "Last packet size: " + self.config.get('statistics', 'last_bytesLastPacket', fallback='0') + "\n" 
                                        + "File size: " + self.config.get('statistics', 'last_fileSize', fallback='0') + "\n\n"
                                        + "Total packets transferred: " + self.config.get('statistics', 'historic_nPackets', fallback='0') + "\n"
                                        + "Total size of files transferred: " + self.config.get('statistics', 'historic_fileSize', fallback='0') + "\n")

    def selectLocalFile(self):
        """Called on local file selection button press"""
        self.localFileStr.set(filedialog.asksaveasfilename(initialdir = "/", title = "Select local file", filetypes = ([("All files", "*.*")])))

    def ipStringCallback(self, *args):
        """Limits the size of a IP string to 15 chars and saves the configuration"""
        if len(root.globalgetvar(args[0])) > 15:
            root.globalsetvar(args[0], (root.globalgetvar(args[0])[:15])) # 15 is the max ip string lenght in ipv4
        self.writeConfig(self.config, 'gui', 'ip', self.hostIpStr.get())

    def portStringCallback(self, *args):
        """Limits the size of the port string to 5 chars and saves the configuration"""
        if len(root.globalgetvar(args[0])) > 5:
            root.globalsetvar(args[0], (root.globalgetvar(args[0])[:5])) # 5 is the max port string lenght
        self.writeConfig(self.config, 'gui', 'port', self.portStr.get())

    def localFileStrCallback(self, *args):
        self.writeConfig(self.config, 'gui', 'localFile', self.localFileStr.get())

    def remoteFileStrCallback(self, *args):
        """Use this callback to update the configuration each time the user changes it"""
        self.writeConfig(self.config, 'gui', 'remoteFile', self.remoteFileStr.get())

    def timeoutStrCallback(self, *args):
        """Use this callback to update the configuration each time the user changes it and to sanitize the timeout input"""
        if self.tryParseFloat(self.timeoutStr.get()):
            self.writeConfig(self.config, 'gui', 'timeout', self.timeoutStr.get())

    def writeConfig(self, config, section, key, value):
        """Write configuration to disk"""
        if section not in config.sections():
            self.config.add_section(section)

        config.set(section, key, value)

        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def tryParseFloat(self, s):
        """Helper function to help sanitize number input"""
        try:
            return(float(s), True)
        except:
            return(None, False)

    def setGui(self, enable):
        """Set the GUI state"""
        if enable:
            self.enableGui()
        else:
            self.disableGui()


    def disableGui(self):
        """Disable the GUI when transfers happen"""
        self.hostTextInput.config(state=DISABLED)
        self.portTextInput.config(state=DISABLED)
        self.localFileTextInput.config(state=DISABLED)
        self.localFileSelectButton.config(state=DISABLED)
        self.remoteFileTextInput.config(state=DISABLED)
        self.timeoutTextInput.config(state=DISABLED)
        self.getButton.config(state=DISABLED)
        self.putButton.config(state=DISABLED)
        self.statisticsButton.config(state=DISABLED)

    def enableGui(self):
        """Enable the GUI after being disabled"""
        self.hostTextInput.config(state=NORMAL)
        self.portTextInput.config(state=NORMAL)
        self.localFileTextInput.config(state=NORMAL)
        self.localFileSelectButton.config(state=NORMAL)
        self.remoteFileTextInput.config(state=NORMAL)
        self.timeoutTextInput.config(state=NORMAL)
        self.getButton.config(state=NORMAL)
        self.putButton.config(state=NORMAL)
        self.statisticsButton.config(state=NORMAL)


class TftpComm:
    """TFTP Communication class. A thread is used to read or write files asynchronously from the GUI"""
    # TFTP command opcodes
    READ = bytes([0x00, 0x01])
    WRITE = bytes([0x00, 0x02])
    DATA = bytes([0x00, 0x03])
    ACK = bytes([0x00, 0x04])
    ERROR = bytes([0x00, 0x05])
    NULLTERM = bytes([0x00])

    MAX_RECEIVE_RETRIES = 3

    def __init__(self):
        # Set this to true to stop the ongoing threads
        self.stopTransfer = False

    def transferThread(self, ip, port, remoteFilename, filehandle, timeout, read, stop, progressBar, doneCallback):
        """Thread that accepts or sends data to the server. Use the stop lambda to stop it. Takes care of it own resources"""
        if read:
            self.acceptDataStateMachine(ip, port, remoteFilename, filehandle, timeout, stop, progressBar, doneCallback)
        else:
            self.sendDataStateMachine(ip, port, remoteFilename, filehandle, timeout, stop, progressBar, doneCallback)
        filehandle.close()

    def transferTftp(self, ip, port, remoteFilename, localFilename, timeout, read, progressBar, doneCallback):
        """Sanitize input and perform the TFTP transfer"""
        fileOptions = "" # Options for opening the file

        try:
            ipaddress.ip_address(ip)
            print("Getting: " + ip)
        except ValueError:
            messagebox.showerror("Input error", ip + " is not a valid IP")
            return
        except TypeError as e:
            messagebox.showerror("Error", str(e))
            return

        if read:
            fileOptions = "wb"
        else:
            fileOptions = "rb"

        filehandle = open(localFilename, fileOptions)

        # print(''.join(['\\x%02x' % b for b in message])) # Use this to print bytes in hex

        self.stopTransfer = False
        thread = threading.Thread(target=self.transferThread, args = [ip, port, remoteFilename, filehandle, timeout, read, lambda: self.stopTransfer, progressBar, doneCallback])
        thread.start()

        print("Done with transmission")

    def breakTftp(self):
        print("Breaking") # TODO: Remove debugs/turn to log
        self.stopTransfer = True # Trigger a lambda to stop the ongoing thread

    def sendMessage(self, sock, message, server):
        sock.sendto(message, server)

    def sendDataStateMachine(self, ip, port, remoteFilename, filehandle, timeout, stop, progressBar, doneCallback):
        receiveTimeoutCounter = 0
        try:
            # Open a connection to the server and prime the socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Create UDP socket
            sock.settimeout(timeout/1000)

            # Init the state machine
            state = "send_request"
            firstBlock = True
            lastBlock = False
            expectedBlockNumber = 0

            # Handle the progress bar
            size = self.getFilesize(filehandle)
            progressBar.mode = "determinate"
            progressBar["value"] = 0
            progressBar["maximum"] = int(size/512)

            #Initialise statistics counters
            nPackets = 0
            bytesLastPacket = 0
            fileSize = 0

            # Break if stopped from the outside
            while stop() == False:
                print(state)
                print(expectedBlockNumber)
                print(firstBlock)

                if state == "send_request":
                    # Send a WRQ
                    message = self.createWriteRequest(remoteFilename, "octet")
                    try:
                        self.sendMessage(sock, message, (ip, int(port)))
                    except:
                        continue
                    state = "wait_for_ack"

                elif state == "wait_for_ack":
                    # Wait for an ACK
                    try:
                        data, server = sock.recvfrom(1024)
                    except:
                        if receiveTimeoutCounter < self.MAX_RECEIVE_RETRIES:
                            receiveTimeoutCounter += 1
                            continue
                        else:
                            raise
                    print(data)

                    # Check for ACK message from server
                    if (data[0:2] == self.ACK):
                        if (data[2:4] == struct.pack(">H", expectedBlockNumber)):
                            state = "send_block"
                            expectedBlockNumber += 1
                        else:
                            state = "send_error_unexpected_block"
                        continue

                    elif data[0:2] == self.ERROR:
                        messagebox.showerror("Server error", "The server has communicated the following error: Code: " + str(int(data[2:4])) + "Message: " + str(data[4:]))
                        break
                    elif firstBlock:
                        # Repeat WRQ
                        state = "send_request"
                        continue
                    else:
                        # Repeat block
                        state = "send_block"
                        continue

                elif state == "send_block":
                    data = filehandle.read(512)
                    print("data:")
                    print(data)

                    # Send data if available
                    if data:
                        message = self.DATA + struct.pack(">H", expectedBlockNumber) + data
                        try:
                            self.sendMessage(sock, message, server)

                            # Get stuff for statistics
                            nPackets += 1
                            bytesLastPacket = len(message)
                            fileSize += len(data)
                        except:
                            continue
                    else:
                        break

                    progressBar["value"] = expectedBlockNumber
                    state = "wait_for_ack"
                    continue
                elif state == "send_error_unexpected_block":
                    message = self.ERROR + "Unknown transfer ID".encode('ascii') + self.NULLTERM
                    try:
                        self.sendMessage(sock, message, server)
                    except:
                        break # Error messages are a courtesy, just quit if this fails

                else:
                    messagebox.showerror("Internal error", "Invalid state")
                    print(state)
                    break
            if stop():
                messagebox.showinfo("User action", "Send operation interrupted by user")

        except socket.timeout as e:
            messagebox.showerror("Error", "Connection error: " + e.args[0])
        except socket.error as e:
            messagebox.showerror("Error", "Connection error: " + e.args[0])
        except Exception as e:
            messagebox.showerror("Error", "An error has occurred during transfer")
        finally:
            print("Closing socket")
            sock.close()
            doneCallback(nPackets, bytesLastPacket, fileSize)
            return


    def acceptDataStateMachine(self, ip, port, remoteFilename, filehandle, timeout, stop, progressBar, doneCallback):
        """State machine used to accept data from the server"""
        receiveTimeoutCounter = 0
        try:
            # Open a connection to the server and prime the socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Create UDP socket
            sock.settimeout(timeout/1000)

            # Handle progress bar
            progressBar.mode = "indeterminate"
            progressBar.start(10)

            # Init the state machine
            state = "send_request"
            firstBlock = True
            lastBlockReceived = False
            expectedBlockNumber = 1

            #Initialise statistics counters
            nPackets = 0
            bytesLastPacket = 0
            fileSize = 0

            while stop() == False:
                print(state)
                print(expectedBlockNumber)
                print(firstBlock)
                #progressBar.step(1)

                if state == "send_request":
                    # Send RRQ
                    message = self.createReadRequest(remoteFilename, "octet")
                    try:
                        self.sendMessage(sock, message, (ip, int(port)))
                    except:
                        continue

                    state = "wait_for_block"
                    continue

                elif state == "wait_for_block":
                    # Wait for the first block
                    try:
                        data, server = sock.recvfrom(1024)
                    except:
                        if receiveTimeoutCounter < self.MAX_RECEIVE_RETRIES:
                            receiveTimeoutCounter += 1
                            continue
                        else:
                            raise
                    #print("****" + str(data)) # TODO: Remove debugs/turn to log

                    if (data[0:2] == self.DATA) and (data[2:4] == struct.pack(">H", expectedBlockNumber)):
                        filehandle.write(data[4:]) # Write to file

                        # Handle last block specially
                        if len(data[4:]) < 512: # Blocksize is always 512
                            lastBlockReceived = True

                        nPackets += 1
                        bytesLastPacket = len(data)
                        fileSize += len(data[4:])

                        state = "send_ack"
                        continue

                    elif data[0:2] == self.ERROR:
                        messagebox.showerror("Server error", "The server has communicated the following error: Code: " + str(int(data[2:4])) + "Message: " + str(data[4:]))
                        break
                    elif firstBlock:
                        state = "send_request"
                        continue
                    else:
                        state = "send_ack"
                        continue

                elif state == "send_ack":
                    # Create and send an ACK package TODO: Make a function for this
                    message = self.ACK + struct.pack(">H", expectedBlockNumber)
                    try:
                        self.sendMessage(sock, message, server)
                    except:
                        continue
                    expectedBlockNumber += 1
                    firstBlock = False

                    if lastBlockReceived:
                        break

                    state = "wait_for_block"

                else:
                    messagebox.showerror("Internal error", "Invalid state")
                    break
        except socket.timeout as e:
            messagebox.showerror("Error", "Connection error: " + e.args[0])
        except socket.error as e:
            messagebox.showerror("Error", "Connection error: " + e.args[0])
        except Exception as e:
            print("General error") # Create dialog
            messagebox.showerror("Error", "An error has occurred during transfer")
        finally:
            print("Closing socket")
            sock.close()
            progressBar.stop()
            doneCallback(nPackets, bytesLastPacket, fileSize)
            return


    def createReadRequest(self, filename, method):
        return self.READ + filename.encode('ascii') + self.NULLTERM + method.encode('ascii') + self.NULLTERM + "blksize".encode('ascii') + self.NULLTERM

    def createWriteRequest(self, filename, method):
        return self.WRITE + filename.encode('ascii') + self.NULLTERM + method.encode('ascii') + self.NULLTERM + "blksize".encode('ascii') + self.NULLTERM

    def getFilesize(self, filehandle):
        filehandle.seek(0,2) # move the cursor to the end of the file
        size = filehandle.tell()
        filehandle.seek(0) # move the cursor back to the start of the file
        return size

# Init TFTP communication
tftpComm = TftpComm()

# Start TKinter
root = Tk()

# Create GUI
my_gui = TftpClientGui(root, tftpComm)

# Run GUI
root.mainloop()

# End of file
