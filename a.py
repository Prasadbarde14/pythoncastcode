import socket

# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# local_ip = '192.168.22.148'

# Bind the socket to a specific address and port
server_address = ('0.0.0.0', 12345)
server_socket.bind(server_address)

# Listen for incoming connections
server_socket.listen()

print("Server is waiting for connections on", server_address)

try:
    while True:
        # Accept a connection
        print("Waiting for a client to connect...")
        client_socket, client_address = server_socket.accept()
        print(f"Connection established with {client_address}")

        # Send data to the client
        message = "Hello, client!"
        client_socket.send(message.encode('utf-8'))
        print(f"Sent message to the client: '{message}'")

        # Close the connection
        client_socket.close()
        print(f"Connection with {client_address} closed.")

except KeyboardInterrupt:
    # Handle keyboard interrupt (Ctrl+C) to gracefully exit the loop
    print("Server shutting down.")

finally:
    # Close the server socket
    print("Waiting for a client to connect...")
    server_socket.close()
