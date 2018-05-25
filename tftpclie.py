#!/usr/bin/env python3

from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog
import ipaddress
import socket
import struct

class TftpClientGui:
    """TFTP Client GUI class"""

    def __init__(self, master, tftpComm):
        """Create the GUI"""
        self.hostIpStr = StringVar()
        self.hostIpStr.trace("w", self.limitIpStringCallback)

        self.portStr = StringVar()
        self.portStr.trace("w", self.limitPortStringCallback)

        self.localFileStr = StringVar()

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

        self.remoteFileTextInput = Entry(master, width=30)
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

    def getTftp(self):
        """Perform get command"""
        self.tftpComm.getTftp(self.hostTextInput.get().strip(), self.remoteFileTextInput.get().strip(), self.localFileTextInput.get().strip())

    def putTftp(self):
        """Perform put command"""
        self.tftpComm.putTftp()

    def breakTftp(self):
        """Break ongoing command"""
        self.tftpComm.breakTftp()

    def showStatistics(self):
        """Show statistics for all transfers"""
        print("Showing statistics")

    def selectLocalFile(self):
        """Called on local file selection button press"""
        self.localFileStr.set(filedialog.asksaveasfilename(initialdir = "/", title = "Select local file", filetypes = ([("All files", "*.*")])))

    def limitIpStringCallback(self, *args):
        """Limits the size of a IP string to 15 chars"""
        if len(root.globalgetvar(args[0])) > 15:
            root.globalsetvar(args[0], (root.globalgetvar(args[0])[:15])) # 15 is the max ip string lenght in ipv4

    def limitPortStringCallback(self, *args):
        """Limits the size of the port string to 5 chars"""
        if len(root.globalgetvar(args[0])) > 5:
            root.globalsetvar(args[0], (root.globalgetvar(args[0])[:5])) # 5 is the max port string lenght

class TftpComm:
    """TFTP Communication class"""
    # TFTP command bytes
    READ = bytes([0x00, 0x01])
    WRITE = bytes([0x00, 0x02])
    DATA = bytes([0x00, 0x03])
    ACK = bytes([0x00, 0x04])
    ERROR = bytes([0x00, 0x05])
    NULLTERM = bytes([0x00])

    def getTftp(self, ip, remoteFilename, localFilename):
        """Perform read request over TFTP"""
        try:
            ipaddress.ip_address(ip)
            print("Getting: " + ip)
        except ValueError:
            print("Error: " + ip + " is not a valid IP") # TODO: Convert this to an error message dialog
            return
        except TypeError as e: 
            print("Unexpected error:", str(e)) # TODO: Convert this to an error message dialog
            return

        with open(localFilename, "wb") as filehandle:
            message = self.createReadRequest(remoteFilename, "octet")

            # print(''.join(['\\x%02x' % b for b in message])) # Use this to print bytes in hex

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Create UDP socket
            sock.settimeout(5.0)
            self.sendMessage(sock, message, (ip, 69))

            expectedBlockNumber = 1;

            while self.acceptData(sock, expectedBlockNumber, filehandle):
                expectedBlockNumber += 1

            print("Done with transmission")

    def putTftp(self):
        print("Putting")

    def breakTftp(self):
        print("Breaking")

    def sendMessage(self, socket, message, server):
        socket.sendto(message, server)

    def acceptData(self, socket, expectedBlockNumber, filehandle):
        data, server = socket.recvfrom(1024)

        if (data[0:2] == self.DATA) and (data[2:4] == struct.pack(">H", expectedBlockNumber)):

            print(data[4:])

            filehandle.write(data[4:]) # Write to file

            message = self.ACK
            message += struct.pack(">H", expectedBlockNumber)
            self.sendMessage(socket, message, server)

            # Returns true on last block
            if len(data[4:]) < 512:
                return False

            return True
        
        elif data[0:2] == self.ERROR:
            print("Error from server") # TODO: Make an error dialog out of this
            # TODO raise here
            return False
        else:
            print("Error")
            # TODO raise here
            return False

    def createReadRequest(self, filename, method):
        return self.READ + filename.encode('ascii') + self.NULLTERM + method.encode('ascii') + self.NULLTERM


# Init TFTP communication
tftpComm = TftpComm()

# Start TKinter
root = Tk()

# Create GUI
my_gui = TftpClientGui(root, tftpComm)

# Run GUI
root.mainloop()

# End of file
