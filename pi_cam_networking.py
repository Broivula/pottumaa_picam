# this module takes care of the networking operations
import asyncio
import requests
import socket
import ssl
import time
ssl.match_hostname = lambda cert, hostname : hostname == 'raspberrypi'
import os
import json
from dotenv import dotenv_values
from error_logging import handle_error_log

init_conn_data = '{"device":1}'
config = dotenv_values(".env")

class Pi_Cam_Networking(object):
    token = None
    net_que = None

    def __init__(self):
        print("networking class init")

    def save_token_env(self, t):
        file = open(".cached", "w")
        file.write(t)
        file.close()


    def generate_token(self):
        try:
            print("generating token..")
            body = {'auth_sec_2':config["AUTH_SEC_2"]}
            headers = {'auth_p1': config["AUTH_P1"], 'auth_sec_2': config["AUTH_SEC_2"],'Authorization': "lkasd"}
            target_url = 'https://'+config["IP"]+':'+config["PORT"]+'/'+config["TOKEN_ROUTE"]
            response = requests.post(target_url, data=body, headers=headers, verify=config["CERT"]) 
            self.token = json.loads(response.text)["token"]
            self.save_token_env(self.token)
        except Exception as err:
            print(err)

    def set_net_que(self, que):
        self.net_que = que
        return

    def UploadAPicture(self, data):
        try:
            image_filename = os.path.basename(data[0])

            multipart_form_data = {
                'image': (image_filename, open(data[0], 'rb'))
            }
            body = {
                'folder': data[1],
            }
            headers = {
                'auth_p1': config["AUTH_P1"],
                'auth_sec_2':config["AUTH_SEC_2"],
                'authorization':"lkasjdoicm " + self.token
            }
            print("now here 2 !!")
            target_url = 'https://'+config["IP"]+':'+config["PORT"]+'/'+config["PICTURE_ROUTE"]
            response = requests.post(target_url, headers=headers, data=body, files=multipart_form_data, verify=config["CERT"]) 
        except Exception as err:
            print("error uploading a picture, waiting 10 seconds before trying again.")
            print("err msg: " + str(err))
            handle_error_log(__file__, str(err))
            time.sleep(10)
            if(self.token == None):
                self.generate_token()
                self.net_que.put(data)
            else:
                self.net_que.put(data)

    def init_socket(self, pi_cam, cam_que):
        try:
            s_socket = socket.socket()
            s_socket.settimeout(10)
            context = ssl.SSLContext()
            context.verify_mode = ssl.CERT_REQUIRED
            context.load_verify_locations(config["CERT"])
            wrapped_socket = context.wrap_socket(s_socket)
            print("wrap done")
            wrapped_socket.connect((config["IP"], int(config["SOCKET_PORT"])))
            print("connection done.")
            wrapped_socket.settimeout(None)
            wrapped_socket.send(init_conn_data.encode())
            print("data sent.")
            while True:
                data = wrapped_socket.recv(1024)
                if len(data) > 0:
                    print(data)
                    decoded_data = str(data.decode('utf-8')).rstrip('\n')
                    if decoded_data == config["SEC_SNAPSHOT_PARAM"]:
                        print("received order to take a picture.")
                        cam_que.put("take_picture")
                else:
                    print("socket connection died, re-establishing in 10 seconds..")
                    time.sleep(10)
                    self.init_socket(pi_cam, cam_que)

        except Exception as err:
            print("socket err: " + str(err))
            print("waiting for 10 seconds before reconnection.")
            handle_error_log(__file__, str(err))
            time.sleep(10)
            self.init_socket(pi_cam, cam_que)


