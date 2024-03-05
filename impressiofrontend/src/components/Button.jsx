import React from 'react'
import axios from 'axios'

function Button() {
  const makeServercall = () => {
    const postData = {
      "device_details": [
          {
              "device_name": "Masoom",
              "device_ip": "192.168.0.106",
              "rotation": "0",
              "coordinates": {
                  "x": 0,
                  "y": 0,
                  "w": 30,
                  "h": 100
              },
              "content_data": {
                  "type": "video", 
                  "url": "https://res.cloudinary.com/doh91aq3h/video/upload/v1707807076/wzx6xqswzxtvpckapq5y.mp4"
              }
          },
          {
              "device_name": "shubham",
              "device_ip": "192.168.0.210",
              "rotation": "90",
              "coordinates": {
                  "x": 30,
                  "y": 0,
                  "w": 30,
                  "h": 100
              },
              "content_data": {
                  "type": "video", 
                  "url": "https://res.cloudinary.com/doh91aq3h/video/upload/v1707807076/wzx6xqswzxtvpckapq5y.mp4"
              }
          },
          {
              "device_name": "shubham",
              "device_ip": "192.168.22.124",
              "rotation": "180",
              "coordinates": {
                  "x": 40,
                  "y": 20,
                  "w": 40,
                  "h": 50
              },
              "content_data": {
                  "type": "image", 
                  "url": "https://media.istockphoto.com/id/1462151146/photo/hands-growing-a-young-plant.jpg?s=2048x2048&w=is&k=20&c=ky5cj_N-nrd8qvbyRuYX-uv8NHltUoScloGoQ10xH2I="
              }
          }
      ],
      "content_data": {
          "type": "", 
          "url": ""
      }
  };

    axios.post('http://localhost:8000/home', postData)
      .then(response => {
        console.log('POST request successful:', response.data);
      })
      .catch(error => {
        console.error('Error making POST request:', error);
      });
  };
  return (
    <button onClick={makeServercall}>Make server call</button>
  )
}

export default Button