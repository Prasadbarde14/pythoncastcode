from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import socket
import threading
import signal
import sys
import json
import time


app = FastAPI()

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update this with your frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# class Coordinates(BaseModel):
#     x: int
#     y: int
#     w: int
#     h: int

class Coordinates(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class content_data(BaseModel):
    type:str
    url:str

class DeviceDetails(BaseModel):
    device_name: str
    device_ip: str
    rotation:str
    coordinates: Coordinates
    content_data:content_data

class Payload(BaseModel):
    device_details: List[DeviceDetails]
    content_data: content_data

client_sockets = []

def start_server(ip_address, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((ip_address, port))
    server_socket.listen()

    print(f"Server started on {ip_address}:{port}")
    client_download_status = {}

    try:
        while True:
            conn, addr = server_socket.accept()
            print('client_address : ', addr)
            if conn not in client_sockets:
                client_sockets.append(conn)
                client_download_status[conn] = False  
            handle_client_connection(conn, client_download_status)  
    except KeyboardInterrupt:
        print("Server is shutting down...")
    finally:
        server_socket.close()

def handle_client_connection(conn, client_download_status):
    threading.Thread(target=client_handler, args=(conn, client_download_status), daemon=True).start()

def client_handler(conn, client_download_status):
    try:
        while True:
            data = conn.recv(1024)
            print('data in client handler function', data)
            if not data:
                break
            data_str = data.decode('utf-8')
            print('client handler > true : ', data_str)
            if data_str == "video_split":
                print('client handler > true > if')
                print('client status before : ', client_download_status)
                client_download_status[conn] = True  
                print('client status after : ', client_download_status)
                if all(client_download_status.values()):
                    send_play_command_to_clients()
    except Exception as e:
        print(f"Error handling client connection: {str(e)}")
    finally:
        conn.close()
        if conn in client_sockets:
            client_sockets.remove(conn)
            del client_download_status[conn] 

def send_play_command_to_clients():
    def send_play_command(client_socket):
        try:
            client_socket.send(b"play")
            print("Sent 'play' command to client")
        except Exception as e:
            print(f"Error sending 'play' command to client: {str(e)}")
    threads = []
    for client_socket in client_sockets:
        thread = threading.Thread(target=send_play_command, args=(client_socket,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

def signal_handler(sig, frame):
    global server_thread

    print("Exiting...")

    for client_socket in client_sockets:
        client_socket.close()

    if server_thread:
        server_thread.join()

    sys.exit(0)

def check_client_sockets():
    while True:
        for client_socket in client_sockets[:]:
            try:
                client_socket.send(b"")
            except OSError:
                print(f"Client {client_socket.getpeername()} disconnected")
                client_sockets.remove(client_socket)
        time.sleep(1)  
check_client_thread = threading.Thread(target=check_client_sockets)
check_client_thread.daemon = True  
check_client_thread.start()
server_thread = threading.Thread(target=start_server, args=('192.168.22.124', 2000))
server_thread.start()
signal.signal(signal.SIGINT, signal_handler)


@app.post("/home")
async def home(payload: Payload):
    try:
        device_details = payload.device_details
        global_content = payload.content_data
        print("global_content : ", global_content)
        
        list_size = len(client_sockets)
        print('size of client_sockets : ', list_size)
        
        # Send data to each connected client
        for device_detail in device_details:
            print("device_detail : ", device_detail)
            client_ip = device_detail.device_ip
            coordinates = device_detail.coordinates
            device_content = device_detail.content_data
            print("device_content : ", device_content)
            rotation= device_detail.rotation
            print("rotation:",rotation)
            rotation_to_send = rotation if rotation else rotation == 0
            # print("url:",device_detail.content_data.url)
            if not device_detail.content_data.type and not device_detail.content_data.url:
                content_to_send = global_content
            else:
                content_to_send = device_content
            # content_to_send = device_content if device_content else global_content
            print("content_to_send:",content_to_send)
            client_payload = {
                "coordinates": coordinates.dict(),
                "content": content_to_send.dict(),
                "rotation":rotation_to_send
            }
            client_payload_json = json.dumps(client_payload)
            client_socket = find_client_socket(client_ip)
            
            if client_socket:
                client_socket.send(client_payload_json.encode())
                print("Data sent to client")
            else:
                print(f"No client connected with IP: {client_ip}")
        
        return {"message": "Success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failure: {str(e)}")
    
def find_client_socket(ip):
    for client_socket in client_sockets:
        if client_socket.getpeername()[0] == ip:
            return client_socket
    return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
