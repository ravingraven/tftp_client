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
    """TFTP Client GUI class. We use this to draw and handle the GUI"""

    def __init__(self, master, tftpComm):
        """Create the GUI"""
        # Input strings must be declared as StringVars in order to work with them asynchronously
        # Add callbacks to them to do stuff when stuff changes
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

        # Create master object for GUI (needed by Tkinter)
        self.master = master

        # Create TFTP communication object
        self.tftpComm = tftpComm

        # Create a title
        master.title("TFTP Client")

        # Create all the elements of the GUI (labels, buttons, progress bar etc.)
        # USe the grid system as the GUI is fairly simple
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
        # Read the configuration from the ini file
        self.config.read('config.ini')

        # Get the values from the ini and set them to the GUI (use fallbacks)
        self.hostIpStr.set(self.config.get('gui', 'ip', fallback=''))
        self.portStr.set(self.config.get('gui', 'port', fallback=''))
        self.localFileStr.set(self.config.get('gui', 'localFile', fallback=''))
        self.remoteFileStr.set(self.config.get('gui', 'remoteFile', fallback=''))
        self.timeoutStr.set(self.config.get('gui', 'timeout', fallback='10000')) # Fallback for timeout is 10s

    def getTftp(self):
        """Perform get command"""
        # Check the timeout value
        timeout, ignore = self.tryParseFloat(self.timeoutStr.get())

        if timeout is None:
            self.setGui(NORMAL)
            messagebox.showerror("Input Error", "Invalid timeout value")
            return

        self.setGui(DISABLED)
        self.tftpComm.transferTftp(self.hostTextInput.get().strip(),
                                   self.portTextInput.get().strip(),
                                   self.remoteFileTextInput.get().strip(),
                                   self.localFileTextInput.get().strip(),
                                   timeout,
                                   True,
                                   self.progressBar,
                                   self.doneCallback)

    def putTftp(self):
        """Perform put command"""
        self.setGui(DISABLED)
        self.tftpComm.transferTftp(self.hostTextInput.get().strip(),
                                   self.portTextInput.get().strip(),
                                   self.remoteFileTextInput.get().strip(),
                                   self.localFileTextInput.get().strip(),
                                   int(self.timeoutStr.get()),
                                   False,
                                   self.progressBar,
                                   self.doneCallback)

    def doneCallback(self, nPackets, bytesLastPacket, fileSize):
        """Call this function to unlock the GUI after a transfer and record statistics"""
        # Unlock the GUI
        self.setGui(NORMAL)

        # Show the user a message
        messagebox.showinfo("Last transmission statistics", "Packets: " + str(nPackets) + "\n" + "Last packet size: " + str(bytesLastPacket) + "\n" + "File size: " + str(fileSize) + "\n")

        # Read the configuration
        self.config.read('config.ini')
        historic_nPackets = int(self.config.get('statistics', 'historic_nPackets', fallback='0'))
        historic_bytesLastPacket = int(self.config.get('statistics', 'historic_bytesLastPacket', fallback='0'))
        historic_fileSize = int(self.config.get('statistics', 'historic_fileSize', fallback='0'))

        # Update historic numbers
        historic_nPackets += nPackets
        historic_bytesLastPacket += bytesLastPacket
        historic_fileSize += fileSize

        # Write back to configuration
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
        self.config.read('config.ini') # Read existing historical data from ini file and show it
        messagebox.showinfo("Statistics", "Packets: " + self.config.get('statistics', 'last_nPackets', fallback='0') + "\n"
                                        + "Last packet size: " + self.config.get('statistics', 'last_bytesLastPacket', fallback='0') + " bytes\n"
                                        + "File size: " + self.config.get('statistics', 'last_fileSize', fallback='0') + "\n\n"
                                        + "Total packets transferred: " + self.config.get('statistics', 'historic_nPackets', fallback='0') + "\n"
                                        + "Total size of files transferred: " + self.config.get('statistics', 'historic_fileSize', fallback='0') + " bytes\n")

    def selectLocalFile(self):
        """Called on local file selection button press"""
        # Open a dialog to chose a file
        self.localFileStr.set(filedialog.asksaveasfilename(initialdir = "/", title = "Select local file", filetypes = ([("All files", "*.*")])))

    def ipStringCallback(self, *args):
        """Limits the size of a IP string to 15 chars and saves the configuration"""
        if len(root.globalgetvar(args[0])) > 15:
            root.globalsetvar(args[0], (root.globalgetvar(args[0])[:15])) # 15 is the max ip string lenght in ipv4
        self.writeConfig(self.config, 'gui', 'ip', self.hostIpStr.get())

    def portStringCallback(self, *args):
        """Limits the size of the port string to 5 chars and saves the configuration"""
        if len(root.globalgetvar(args[0])) > 5: # Limit to 5 chars
            root.globalsetvar(args[0], (root.globalgetvar(args[0])[:5])) # 5 is the max port string length
        self.writeConfig(self.config, 'gui', 'port', self.portStr.get())

    def localFileStrCallback(self, *args):
        """Callback for when changing the local file input. Just writes to the configuration"""
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
        # Only add section if not already existing
        if section not in config.sections():
            self.config.add_section(section)

        # Set...
        config.set(section, key, value)

        # ...and save
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def tryParseFloat(self, s):
        """Helper function to help sanitize number input"""
        # float() throws if string is not a number, classic Python way of doing this...
        try:
            return(float(s), True)
        except:
            return(None, False)


    def setGui(self, setState):
        """Set the gui state to the state passed as an argument"""
        self.hostTextInput.config(state=setState)
        self.portTextInput.config(state=setState)
        self.localFileTextInput.config(state=setState)
        self.localFileSelectButton.config(state=setState)
        self.remoteFileTextInput.config(state=setState)
        self.timeoutTextInput.config(state=setState)
        self.getButton.config(state=setState)
        self.putButton.config(state=setState)
        self.statisticsButton.config(state=setState)


class TftpComm:
    """TFTP Communication class. A thread is used to read or write files asynchronously from the GUI"""
    # TFTP command opcodes and useful byte values
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
        """Sanitize input and perform the TFTP transfer. Connection arguments are passed along down the line.
           Returns nothing. Thread is responsible for closing passed resources"""
        try:
            ipaddress.ip_address(ip)
        # Show possible errors to the user
        except ValueError:
            messagebox.showerror("Input error", ip + " is not a valid IP")
            doneCallback(0, 0, 0)
            return
        except TypeError as e:
            messagebox.showerror("Error", str(e))
            doneCallback(0, 0, 0)
            return

        # Set file options for either reading or writing
        if read:
            fileOptions = "wb"
        else:
            fileOptions = "rb"

        # Open file
        try:
            filehandle = open(localFilename, fileOptions)
        except:
            messagebox.showerror("Error", "Could not open file")
            doneCallback(0, 0, 0)
            return

        # print(''.join(['\\x%02x' % b for b in message])) # Use this to print bytes in hex

        self.stopTransfer = False # Set the stop lambda to false

        # Setup and start the thread
        thread = threading.Thread(target=self.transferThread, args = [ip, port, remoteFilename, filehandle, timeout, read, lambda: self.stopTransfer, progressBar, doneCallback])
        thread.start()

    def breakTftp(self):
        """Break an ongoing TFTP actioon via the stopTransfer() lambda. This should always work unless the thread is
           in some kind of socket timeout"""
        self.stopTransfer = True  # Trigger a lambda to stop the ongoing thread

    def sendMessage(self, sock, message, server):
        """Send message (data) to socket"""
        sock.sendto(message, server)

    def sendDataStateMachine(self, ip, port, remoteFilename, filehandle, timeout, stop, progressBar, doneCallback):
        """This state machine handles sending data to the server. Sending is simple compared to receiving. It is
           two steps: Sending a request and waiting for an ACK and sending a block and waiting for an ACK. What is
           important here is to keep the connection open after sending all the data to wait for the final ACK.
           Pass server connection strings, local and remote file
           information, a connection timeout, a lambda function used to stop the machine, a Tkinter progressBar object
           and a callback to be called on end as an argument. Does not return anything and takes care of closing
           any passed or open resources"""

        # Init the state machine
        state = "send_request"
        expectedBlockNumber = 0

        # Handle the progress bar
        size = self.getFilesize(filehandle)
        progressBar.mode = "determinate"
        progressBar["value"] = 0
        progressBar["maximum"] = int(size / 512)

        # Initialise statistics counters
        nPackets = 0
        bytesLastPacket = 0
        fileSize = 0

        try:
            # Open a connection to the server and prime the socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Create UDP socket
            sock.settimeout(timeout/1000)

            # Break if stopped from the outside
            while stop() == False:

                if state == "send_request":
                    expectedBlockNumber = 0
                    retries = 0
                    # Break if stopped from the outside
                    while stop() == False:
                        if retries > self.MAX_RECEIVE_RETRIES:
                            raise self.TftpException("Timeout")
                        retries += 1

                        # Send a WRQ
                        try:
                            self.sendMessage(sock, self.createWriteRequest(remoteFilename, "octet"), (ip, int(port)))
                        except:
                            continue

                        try:
                            result, server = self.waitForAck(sock, expectedBlockNumber)
                            if result:
                                progressBar["value"] = expectedBlockNumber
                                expectedBlockNumber += 1
                                state = "send_block"
                                break
                        except self.TftpException as e:
                            # Handle TFTP exception
                            raise

                elif state == "send_block":
                    data = filehandle.read(512)

                    # Send data if available
                    if data:
                        retries = 0
                        while stop() == False:
                            if retries > self.MAX_RECEIVE_RETRIES:
                                raise self.TftpException("Timeout")
                            retries += 1

                            message = self.DATA + struct.pack(">H", expectedBlockNumber) + data
                            try:
                                self.sendMessage(sock, message, server)

                                # Get stuff for statistics
                                nPackets += 1
                                bytesLastPacket = len(message)
                                fileSize += len(data)
                            except Exception as e:
                                continue

                            try:
                                result, server = self.waitForAck(sock, expectedBlockNumber)

                                if result:
                                    progressBar["value"] = expectedBlockNumber
                                    expectedBlockNumber += 1
                                    state = "send_block"
                                    break
                            except self.TftpException as e:
                                # Handle TFTP exception
                                raise
                    else:
                        break

                else:
                    messagebox.showerror("Internal error", "Invalid state")
                    break
            if stop():
                messagebox.showinfo("User action", "Send operation interrupted by user")

        except socket.timeout as e:
            messagebox.showerror("Error", "Connection error: " + e.args[0])
        except socket.error as e:
            messagebox.showerror("Error", "Connection error: " + e.args[0])
        except self.TftpException as e:
            messagebox.showerror("Error", e.args[0])
        except Exception as e:
            messagebox.showerror("Error", "An error has occurred during transfer: " + str(e))
        finally:
            sock.close()
            doneCallback(nPackets, bytesLastPacket, fileSize)
            return


    def acceptDataStateMachine(self, ip, port, remoteFilename, filehandle, timeout, stop, progressBar, doneCallback):
        """State machine used to accept data from the server. Pass server connection strings, local and remote file
           information, a connection timeout, a lambda function used to stop the machine, a Tkinter progressBar object
           and a callback to be called on end as an argument. Does not return anything and takes care of closing
           any passed or open resources"""
        retries = 0
        # Handle progress bar
        progressBar.mode = "indeterminate"
        progressBar.start(10)

        # Init the state machine
        state = "send_request"
        firstBlock = True
        lastBlockReceived = False
        expectedBlockNumber = 1

        # Initialise statistics counters
        nPackets = 0
        bytesLastPacket = 0

        fileSize = 0

        try:
            # Open a connection to the server and prime the socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Create UDP socket
            sock.settimeout(timeout/1000)

            while stop() == False:

                if state == "send_request":
                    firstBlock = True
                    lastBlockReceived = False
                    expectedBlockNumber = 0

                    # Send RRQ
                    try:
                        self.sendMessage(sock, self.createReadRequest(remoteFilename, "octet"), (ip, int(port)))
                    except:
                        continue

                    state = "wait_for_block"
                    continue

                elif state == "wait_for_block":
                    # Wait a block
                    try:
                        data, server = sock.recvfrom(1024)
                    except:
                        if retries < self.MAX_RECEIVE_RETRIES:
                            retries += 1

                            # Either go back to the start or keep waiting for an ack in case of an error
                            if firstBlock:
                                state = "send_request"
                            else:
                                state = "send_ack"
                            continue
                        else:
                            raise

                    expectedBlockNumber += 1

                    # Parse incoming data
                    if (data[0:2] == self.DATA) and (data[2:4] == struct.pack(">H", expectedBlockNumber)):
                        filehandle.write(data[4:]) # Write to file

                        # Handle last block specially
                        if len(data[4:]) < 512: # Block size is always 512
                            lastBlockReceived = True

                        nPackets += 1
                        bytesLastPacket = len(data)
                        fileSize += len(data[4:])

                        state = "send_ack"
                        continue

                    elif data[0:2] == self.ERROR:
                        # Error, show it to the user
                        messagebox.showerror("Server error", "The server has communicated the following error: Code: " + self.decodeErrorMessage(data))
                        break
                    elif firstBlock:
                        state = "send_request"
                    else:
                        state = "send_ack"
                    continue

                elif state == "send_ack":
                    # Create and send an ACK package
                    try:
                        self.sendMessage(sock, self.ACK + struct.pack(">H", expectedBlockNumber), server)
                    except:
                        continue

                    # First block was received
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
            messagebox.showerror("Error", "An error has occurred during transfer")
        finally:
            sock.close()
            progressBar.stop()
            doneCallback(nPackets, bytesLastPacket, fileSize)
            return

    def waitForAck(self, sock, expectedBlockNumber):
        """Waits and handles an incoming TFTP ACK. Pass a connected and valid socket as well as the expected block
           number contained in the ACK as an argument. Returns a tuple of a success value and a server ip/port tuple"""
        # Wait for an ACK
        try:
            data, server = sock.recvfrom(1024)
        except:
            raise

        # Check for ACK message from server
        if data[0:2] == self.ACK:
            if data[2:4] == struct.pack(">H", expectedBlockNumber):
                return True, server
            else:
                # Send an error to the server, this was not the block number we expected
                self.sendMessage(sock, self.ERROR + "Unknown transfer ID".encode('ascii') + self.NULLTERM, server)
                return False, server

        elif data[0:2] == self.ERROR:
            raise self.TftpException("The server has communicated the following error: Code: " + self.decodeErrorMessage(data))
        else:
            return False, server


    def createReadRequest(self, filename, method):
        """Creates a TFTP read request message. Pass the method as an argument"""
        return self.READ + filename.encode('ascii') + self.NULLTERM + method.encode('ascii') + self.NULLTERM

    def createWriteRequest(self, filename, method):
        """Creates a TFTP write request message. Pass the method as an argument"""
        return self.WRITE + filename.encode('ascii') + self.NULLTERM + method.encode('ascii') + self.NULLTERM

    def getFilesize(self, filehandle):
        """This helper function is used to get the file size of a file"""
        filehandle.seek(0,2) # Move the cursor to the end of the file
        size = filehandle.tell() # Tell() will tell us the length in bytes
        filehandle.seek(0) # Move the cursor back to the start of the file
        return size

    def decodeErrorMessage(self, message):
        """This is used for decoding server-side errors"""
        # The error message consists of an error code and an error message. Convert all to strings
        # and return them
        return str(message[2]) + str(message[3]) + " " + message[4:-2].decode("ascii")

    class TftpException(Exception):
        """Base class for raising custom TFTP exceptions"""

# Init TFTP communication
tftpComm = TftpComm()

# Start TKinter
root = Tk()

# Create GUI
my_gui = TftpClientGui(root, tftpComm)

# Run GUI
root.mainloop()

# End of file
