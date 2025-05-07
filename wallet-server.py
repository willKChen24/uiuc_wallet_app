import threading
import socket
from wallet import Wallet

wallet = Wallet() # the only global variable you should use

def create_wallet_server(local_port):
    def handle_connection(client_socket, client_address):
        try:
            buffer = "" #reads in the entire message (the message "container")
            
            while True:
                
                data = client_socket.recv(1024) #recv = read in data from the socket (1024 bytes)
                
                if not data: #if data invalid
                    break #break out of the loop
                    
                buffer += data.decode('utf-8') #add the decoded data (actual characters) into the buffer
                
                while '\n' in buffer: #process complete messages (ending with \n)
                    #extract a complete message
                    message, buffer = buffer.split('\n', 1) #store the message and buffer as the buffer split at the 1st newline (1 indicates we only do a split once)
                    
                    #remove any \r characters
                    message = message.replace('\r', '')
                    
                    #skip empty messages
                    if not message:
                        continue
                        
                    #parse the command (EXIT, GET, MOD, etc.)
                    parts = message.split() #split at all whitespaces, so parts is stored as a list of strs
                    command = parts[0] #command is the first word in the message
                    
                    #call appropriate methods/take appropriate actions based on the command word
                    if command == "EXIT":
                        return  # Exit the thread
                        
                    elif command == "GET":
                        resource = parts[1]
                        result = wallet.get(resource)
                        client_socket.send((str(result) + '\n').encode('utf-8')) #need .encode('utf-8') to convert actual string to utf8 so the server "understands" it
                        
                    elif command == "MOD":
                        resource = parts[1]
                        delta = int(parts[2])
                        result = wallet.change(resource, delta)
                        client_socket.send((str(result) + '\n').encode('utf-8'))

                    elif command == "TRY":
                        resource = parts[1]
                        delta = int(parts[2])
                        result = wallet.try_change(resource, delta)
                        client_socket.send((str(result) + '\n').encode('utf-8')) 
                        
                    elif command == "TRAN":
                        #build transaction dictionary
                        transaction_dict = {}
                        for i in range(1, len(parts), 2): #goes from 1 to length of parts-1 with step size 2 to skip every other elem
                            if i+1 < len(parts): #because we only have odd indices (1, 3, 5, etc.), i+1 will always be even
                                resource = parts[i]
                                #parts: "command", "resource1", "delta1", "resource2", "delta2", etc.
                                delta = int(parts[i+1])
                                transaction_dict[resource] = delta #assign the delta values to each resource in the transactiom dict
                                
                        #execute transaction and get result
                        result = wallet.transaction(**transaction_dict)
                        client_socket.send((str(result) + '\n').encode('utf-8'))

        finally:
            #always close the client socket when done
            client_socket.close()
    
    #create a socket for the server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        #set socket option to reuse the address (helpful for debugging)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        #bind to address and port
        server_socket.bind(('', local_port))
        
        #listen for connections
        server_socket.listen(200)
        
        while True:
            #accept connections in a loop
            client_socket, client_address = server_socket.accept() 
            
            #create a new thread for each connection
            client_thread = threading.Thread(
                target=handle_connection,
                args=(client_socket, client_address)
            )
            
            #start the thread
            # client_thread.daemon = True  #allow server to exit if threads are still running
            client_thread.start()
            
    finally:
        #always close the server socket when done
        server_socket.close() 

if __name__ == '__main__':
    # parses command-line arguments, ensuring all implementations are invoked the same way
    import getopt
    import sys

    local_port = 34000
    optlist, args = getopt.getopt(sys.argv[1:], 'p:')
    for arg in optlist:
        if arg[0] == '-p': local_port = int(arg[1])
    print("Launching wallet server on :"+str(local_port))
    create_wallet_server(local_port)
