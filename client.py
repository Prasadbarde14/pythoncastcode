import asyncio
import json
import subprocess
import time
import socket
import requests
import cv2
from PIL import Image
import numpy as np
import moviepy.editor as mp
import os

async def download_video(url, coordinates, rotation, writer):

    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open('temp.mp4', 'wb') as f:
                f.write(response.content)
            return await split_and_rotate_video('temp.mp4', coordinates, rotation, writer)

        else:
            return None
    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        return None

async def download_image(url, coordinates, rotation):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open("temp.img", 'wb') as f:
                f.write(response.content)
            print("success_split")
            return await split_and_rotate_img('temp.img', coordinates, rotation)
        else:
            return None
    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        return None

async def split_and_rotate_img(image_path, coordinates, rotation):
    try:
        image = Image.open(image_path)
        O_width, O_height = image.size
        print("o_width:", O_width)
        print("o_height:", O_height)
        image = np.array(image)
        M = cv2.getRotationMatrix2D((O_width / 2, O_height / 2), float(rotation), 1)
        rotated_image = cv2.warpAffine(image, M, (O_width, O_height))
        x1, y1, x2, y2 = coordinates['x1'], coordinates['y1'], coordinates['x2'], coordinates['y2']
        x1, y1, x2, y2 = int(x1 * O_width / 100), int(y1 * O_height / 100), int(x2 * O_width / 100), int(
            y2 * O_height / 100)
        w, h = x2 - x1, y2 - y1
        cropped_image = rotated_image[y1:y2, x1:x2]
        resized_image = cv2.resize(cropped_image, (O_width, O_height))
        s_height, s_width = resized_image.shape[:2]
        print("s_height:", s_height)
        print("s_width:", s_width)
        output_image_path = "rotation.png"
        cv2.imwrite(output_image_path, cv2.cvtColor(resized_image, cv2.COLOR_RGB2BGR))
        print("Rotated and split image created successfully.")
        # client_socket.send("image_split".encode())
        return output_image_path
    except Exception as e:
        print(f"Error rotating and splitting image: {str(e)}")
        return None

async def split_and_rotate_video(video_path, coordinates, rotation, writer):
    try:
        has_audio = mp.VideoFileClip(video_path).audio is not None
        print(has_audio)
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Error opening video file.")
        O_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        O_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print("o_width:", O_width)
        print("o_height:", O_height)
        x1, y1, x2, y2 = coordinates['x1'], coordinates['y1'], coordinates['x2'], coordinates['y2']
        x1, y1, x2, y2 = int(x1 * O_width / 100), int(y1 * O_height / 100), int(x2 * O_width / 100), int(y2 * O_height / 100)
        w, h = x2 - x1, y2 - y1

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        output_path = 'final_video.mp4'
        output = cv2.VideoWriter(output_path, fourcc, 30.0, (O_width, O_height))

        while (cap.isOpened()):
            ret, frame = cap.read()
            if ret == True:
                M = cv2.getRotationMatrix2D((O_width / 2, O_height / 2), float(rotation), 1)
                rotated_frame = cv2.warpAffine(frame, M, (O_width, O_height))
                cropped_frame = rotated_frame[y1:y2, x1:x2]
                resized_frame = cv2.resize(cropped_frame, (O_width, O_height))
                output.write(resized_frame)
            else:
                break
        cap.release()
        output.release()
        if has_audio:
            audio_clip = mp.AudioFileClip(video_path)
            audio_clip.write_audiofile("temp_audio.wav")

            final_output_path = 'final_video_combined.mp4'
            os.system(f"ffmpeg -i {output_path} -i temp_audio.wav -c:v copy -c:a aac {final_output_path}")

            if os.path.exists(final_output_path) and os.path.getsize(final_output_path) > 0:
                print("Final video 'final_video_combined.mp4' successfully created.")
            else:
                print("Error: 'final_video_combined.mp4' was not properly created or is empty.")
                return None

            os.remove("temp_audio.wav")
        else:
            final_output_path = output_path
        writer.write("video_split".encode())
        await writer.drain()

        return final_output_path

    except Exception as e:
        print(f"Error splitting, rotating, and combining video: {str(e)}")
        return None

async def handle_api_calls(reader, writer):
    video_file = None
    image_file = None
    while True:
        try:
            data = await reader.read(4096)
            if not data:
                break
            data_str = data.decode('utf-8')
            data_json = json.loads(data_str)
            print('Received data:', data_str)
            if data_json["device_status"] == "on":
                print('coordinates:', data_json["coordinates"])
                print('content_data:', data_json["content"])
                print('content_type:', data_json["content"]["type"])
                print("rotation:", data_json["rotation"])
                if data_json["content"]["type"] == "video":
                    video_file = await download_video(data_json["content"]["url"], data_json["coordinates"], data_json["rotation"], writer)
                    print(f'Video file: {video_file}')
                    try:
                        while True:
                            play_command = await reader.read(1024)
                            play_command = play_command.decode('utf-8')
                            if play_command.strip().lower() == "play":
                                print("Received play command from server.")
                                await play_video(video_file)
                                break
                            await asyncio.sleep(1)
                    except:
                        print("Failed to download, split, and rotate the video file.")
                elif data_json["content"]["type"] == "image":
                    image_file = await download_image(data_json["content"]["url"], data_json["coordinates"],data_json["rotation"])
                    print(f'Image file: {image_file}')
                    while True:
                        play_command = await reader.read(1024)
                        play_command = play_command.decode('utf-8')
                        if play_command.strip().lower() == "play":
                            print("Received play command from server.")
                            subprocess.Popen(['xdg-open', image_file])
                            print("Image displayed successfully")
                        await asyncio.sleep(1)
            else:
                print('device_status:', data_json["device_status"])
                print("device_ip:", data_json["device_ip"])
                await stop_video()
                video_file = None
        except Exception as e:
            print(f"Error receiving data from server: {str(e)}")
            await asyncio.sleep(5)

async def start_client(ip_address, port):
    reader, writer = await asyncio.open_connection(ip_address, port)
    print(f"Connected to server at {ip_address}:{port}")
    try:
        await handle_api_calls(reader, writer)
    finally:
        writer.close()
        await writer.wait_closed()

async def play_video(video_file):
    print("success")
    subprocess.Popen(['cvlc', '--fullscreen', "--loop", video_file], stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)

async def stop_video():
    subprocess.Popen(['pkill', 'vlc'])

if __name__ == "__main__":
    ip_address = ""
    port = 2020
    asyncio.run(start_client(ip_address, port))