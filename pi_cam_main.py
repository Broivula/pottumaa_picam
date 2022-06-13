import io
import cv2
import os
import numpy
import requests
import datetime
import time
import asyncio
from queue import Queue
from pi_cam_networking import Pi_Cam_Networking
from threading import Thread
from camera import _PiCamera
from dotenv import dotenv_values
from error_logging import handle_error_log

config = dotenv_values(".env")
pi_cam = _PiCamera()
net = Pi_Cam_Networking()



def MovementDetection():
	with picamera.PiCamera() as camera2:
		camera2.resolution=(1280, 720)
		stream = io.BytesIO()  #creates a memory stream for the photos
		#camera.resolution = (1280, 720)

		camera2.capture(stream, format="jpeg")
		#convert the captured stream of pictures into a numpy array
		image_1_buff = numpy.fromstring(stream.getvalue(), dtype=numpy.uint8)
		#make an opencv image out of this
		image1 = cv2.imdecode(image_1_buff, 1)
		#convert to grayscale
		gray = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
		#invert the image
		inverted = (255-gray)

		time.sleep(0.5)

		#now capture the screen again
		stream2 = io.BytesIO()
		camera2.capture(stream2, format="jpeg", resize=(1280, 720))
		image_2_buff = numpy.fromstring(stream2.getvalue(), dtype=numpy.uint8)
		image2 = cv2.imdecode(image_2_buff, 1)
		gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
		cv2.imwrite("inverted2.jpg", gray2)
		inverted2 = (255-gray2)

		difference = cv2.subtract(inverted, inverted2)

		matrix = numpy.fromstring(difference, dtype=numpy.uint8)
		mean = matrix.mean()
		print(mean)
		if mean > 5.0:
			print("something is moving!")
			cv2.imwrite("movement.jpg", image1)
			cv2.imwrite("movement2.jpg", image2)
		



def camera_thread(cam_que):
    pi_cam.startMainCameraLoop(cam_que)
    print("cam thread here!")

def networking_thread(networking_que):
    print("networking thread here!")
    net.generate_token()
    while True:
        data = networking_que.get()
        net.UploadAPicture(data)

def socket_thread(cam_que):
    print("socket thrad reporting for duty!")
    net.init_socket(pi_cam, cam_que)

async def camera_que(cam_que):
    while 1:
        data = cam_que.get()
        pi_cam.startPicturePipeline()

def main():
    try:
        print("starting main..")
        net_op_que = Queue()
        cam_pic_que = Queue()
        pi_cam.assign_networking_queue(net_op_que)
        cam_thread_holder = Thread(target = camera_thread, args=(cam_pic_que,))
        networking_thread_holder = Thread(target = networking_thread, args=(net_op_que, ))
        socket_thread_holder = Thread(target = socket_thread, args=(cam_pic_que,))
        networking_thread_holder.setDaemon(True)
        networking_thread_holder.start()
        socket_thread_holder.start()
        cam_thread_holder.start()
        net_op_que.join()
        cam_pic_que.join()
        print("now here.")
        net.set_net_que(net_op_que)
        asyncio.run(camera_que(cam_pic_que))

        print("threads started..")
        
    except Exception as err:
        handle_error_log(__file__, str(err))


if __name__=="__main__":
    main()
