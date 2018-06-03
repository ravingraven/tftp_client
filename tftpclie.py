#!/usr/bin/env python3

from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog

import configparser

import threading
from time import sleep

import ipaddress
import socket
import struct

class TftpClientGui:
    """TFTP Client GUI class"""

    def __init__(self, master, tftpComm):
        """Create the GUI"""
        self.hostIpStr = StringVar()
        self.hostIpStr.trace("w", self.ipStringCallback)

        self.portStr = StringVar()
        self.portStr.trace("w", self.portStringCallback)

        self.localFileStr = StringVar()
        self.localFileStr.trace("w", self.localFileStrCallback)

        self.remoteFileStr = StringVar()
        self.remoteFileStr.trace("w", self.remoteFileStrCallback)

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

        self.blockSizeLabel = Label(master, text="Block Size")
        self.blockSizeLabel.grid(sticky="W", row=4, column=1, padx=5, pady=5)

        self.blockSize = StringVar(master)
        self.blockSize.set("1")

        self.blockSizeSelect = OptionMenu(master, self.blockSize, "1", "2", "3")
        self.blockSizeSelect.grid(sticky="W", row=4, column=2, padx=5, pady=5)

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
        config.read('config.ini')
        self.hostIpStr.set(config.get('gui', 'ip', fallback=''))
        self.portStr.set(config.get('gui', 'port', fallback=''))
        self.localFileStr.set(config.get('gui', 'localFile', fallback=''))
        self.remoteFileStr.set(config.get('gui', 'remoteFile', fallback=''))

    def getTftp(self):
        """Perform get command"""
        self.tftpComm.transferTftp(self.hostTextInput.get().strip(), self.portTextInput.get().strip(), self.remoteFileTextInput.get().strip(), self.localFileTextInput.get().strip(), True, self.progressBar)

    def putTftp(self):
        """Perform put command"""
        self.tftpComm.transferTftp(self.hostTextInput.get().strip(), self.portTextInput.get().strip(), self.remoteFileTextInput.get().strip(), self.localFileTextInput.get().strip(), False, self.progressBar)

    def breakTftp(self):
        """Break ongoing command"""
        self.tftpComm.breakTftp()

    def showStatistics(self):
        """Show statistics for all transfers"""
        print("Showing statistics")

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

    def writeConfig(self, config, section, key, value):
        """Write configuration to disk"""
        if section not in config.sections():
            self.config.add_section(section)

        config.set(section, key, value)

        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)

class TftpComm:
    """TFTP Communication classA thread is used to read or write files asynchronously from the GUI"""
    # TFTP command opcodes
    READ = bytes([0x00, 0x01])
    WRITE = bytes([0x00, 0x02])
    DATA = bytes([0x00, 0x03])
    ACK = bytes([0x00, 0x04])
    ERROR = bytes([0x00, 0x05])
    NULLTERM = bytes([0x00])

    def __init__(self):
        # Set this to true to stop the ongoing threads
        self.stopTransfer = False

    def transferThread(self, ip, port, remoteFilename, filehandle, read, stop, progressBar):
        """Thread that accepts or sends data to the server. Use the stop lambda to stop it. Takes care of it own resources"""
        if read:
            self.acceptDataStateMachine(ip, port, remoteFilename, filehandle, stop, progressBar)
        else:
            self.sendDataStateMachine(ip, port, remoteFilename, filehandle, stop, progressBar)
        filehandle.close()

    def transferTftp(self, ip, port, remoteFilename, localFilename, read, progressBar):
        """Sanitize input and perform the TFTP transfer"""
        fileOptions = "" # Options for opening the file

        try:
            ipaddress.ip_address(ip)
            print("Getting: " + ip)
        except ValueError:
            print("Error: " + ip + " is not a valid IP") # TODO: Convert this to an error message dialog
            return
        except TypeError as e:
            print("Unexpected error:", str(e)) # TODO: Convert this to an error message dialog
            return

        if read:
            fileOptions = "wb"
        else:
            fileOptions = "rb"

        filehandle = open(localFilename, fileOptions)

        # print(''.join(['\\x%02x' % b for b in message])) # Use this to print bytes in hex

        self.stopTransfer = False
        thread = threading.Thread(target=self.transferThread, args = [ip, port, remoteFilename, filehandle, read, lambda: self.stopTransfer, progressBar])
        thread.start()

        print("Done with transmission")

    def breakTftp(self):
        print("Breaking") # TODO: Remove debugs/turn to log
        self.stopTransfer = True # Trigger a lambda to stop the ongoing thread

    def sendMessage(self, sock, message, server):
        sock.sendto(message, server)

    def sendDataStateMachine(self, ip, port, remoteFilename, filehandle, stop, progressBar):
        # Open a connection to the server and prime the socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Create UDP socket
        sock.settimeout(5.0)

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

        # Break if stopped from the outside
        while stop() == False:
            print(state)
            print(expectedBlockNumber)
            print(firstBlock)

            if state == "send_request":
                # Send a WRQ
                message = self.createWriteRequest(remoteFilename, "octet")
                self.sendMessage(sock, message, (ip, int(port)))
                state = "wait_for_ack"

            elif state == "wait_for_ack":
                # Wait for an ACK
                data, server = sock.recvfrom(1024)
                print(data)

                # Check for ACK message from server
                if (data[0:2] == self.ACK) and (data[2:4] == struct.pack(">H", expectedBlockNumber)):
                    state = "send_block"
                    expectedBlockNumber += 1

                elif data[0:2] == self.ERROR:
                    print("Error from server") # TODO: Make an error dialog out of this
                    # TODO raise here
                    return False
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
                    self.sendMessage(sock, message, server)
                else:
                    sock.close()
                    break

                progressBar["value"] = expectedBlockNumber
                state = "wait_for_ack"
                continue
            else:
                print("Error, unkonwn state")
                print(state)
                sock.close()
                break

    def acceptDataStateMachine(self, ip, port, remoteFilename, filehandle, stop, progressBar):
        """State machine used to accept data from the server"""

        # Open a connection to the server and prime the socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Create UDP socket
        sock.settimeout(5.0)

        # Handle progress bar
        progressBar.mode = "indeterminate"
        progressBar.start(10)

        # Init the state machine
        state = "send_request"
        firstBlock = True
        lastBlockReceived = False
        expectedBlockNumber = 1

        while stop() == False:
            print(state)
            print(expectedBlockNumber)
            print(firstBlock)
            #progressBar.step(1)

            if state == "send_request":
                # Send RRQ
                message = self.createReadRequest(remoteFilename, "octet")
                self.sendMessage(sock, message, (ip, int(port)))

                state = "wait_for_block"
                continue

            elif state == "wait_for_block":
                # wait for the first block
                data, server = sock.recvfrom(1024)
                print(data[4:]) # TODO: Remove debugs/turn to log

                if (data[0:2] == self.DATA) and (data[2:4] == struct.pack(">H", expectedBlockNumber)):
                    filehandle.write(data[4:]) # Write to file

                    # Handle last block specially
                    if len(data[4:]) < 512:
                        lastBlockReceived = True
                    state = "send_ack"
                    continue

                elif data[0:2] == self.ERROR:
                    print("Error from server") # TODO: Make an error dialog out of this
                    # TODO raise here
                    return False
                elif firstBlock:
                    state = "send_request"
                    continue
                else:
                    state = "send_ack"
                    continue

            elif state == "send_ack":
                # Create and send an ACK package TODO: Make a fuction for this
                message = self.ACK
                message += struct.pack(">H", expectedBlockNumber)
                self.sendMessage(sock, message, server)
                expectedBlockNumber += 1
                firstBlock = False

                if lastBlockReceived:
                    sock.close()
                    progressBar.stop()
                    break

                state = "wait_for_block"

            else:
                print("Error, unkonwn state")
                print(state)
                sock.close()
                progressBar.stop()
                break

    def createReadRequest(self, filename, method):
        return self.READ + filename.encode('ascii') + self.NULLTERM + method.encode('ascii') + self.NULLTERM

    def createWriteRequest(self, filename, method):
        return self.WRITE + filename.encode('ascii') + self.NULLTERM + method.encode('ascii') + self.NULLTERM

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
