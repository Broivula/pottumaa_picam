import picamera
import time
import datetime
import os
import io
import cv2
import numpy
import threading
import requests
from fractions import Fraction

#camera = picamera.PiCamera(resolution=(1280, 720))

def TakeDaylightPicture():
	with picamera.PiCamera() as camera:
		print("starting the function to take a normal picture..")
		camera.resolution=(1280, 720)
		print("camera instatiated, wait a few seconds for the auto exposure to kick in.")
		time.sleep(30)
		date =str(datetime.datetime.now()).split(" ")[0]
		tempEuroDate = date.split("-")
		euroDate = "potato-" + tempEuroDate[2] + '-' + tempEuroDate[1] + '-' + tempEuroDate[0]
		current_time = str(datetime.datetime.now().time()).split(".")[0].replace(":", "_")
		if os.path.isdir('uploads/potato_field/'+euroDate) != True:
			os.mkdir('uploads/potato_field/'+euroDate)


		camera.annotate_text =" "+ euroDate + ' - ' + current_time.replace("_", ":") + " "
		camera.annotate_background = True
		camera.capture('uploads/potato_field/'+euroDate+'/'+ euroDate+'-'+current_time, format="png")
		UploadAPicture('uploads/potato_field/'+euroDate+'/'+ euroDate+'-'+current_time, 'uploads/potato_field/'+euroDate)
		print("picture taken and uploaded")
		#camera.close()
		return

def TakeNightlightPicture():
	with picamera.PiCamera() as camera:
		print("starting the function for night light picture")
		start_time = time.time()
		camera.resolution = (1280, 720)
		camera.framerate = Fraction(1,6)
		print("setting the shutterspeed to long exposure, also iso to 800")
		camera.shutter_speed  = 6000000
		camera.iso = 800
		print("printing extra info")
		print("exp speed")
		print(camera.exposure_speed)
		print("shutter speed")
		print(camera.shutter_speed)
		print("a small delay to calculate the light..")
		time.sleep(5)
		while camera.analog_gain < 1 or camera.digital_gain < 1:
			time.sleep(0.1)

		camera.exposure_mode = 'off'
		date =str(datetime.datetime.now()).split(" ")[0]
		tempEuroDate = date.split("-")
		euroDate = "potato-" + tempEuroDate[2] + '-' + tempEuroDate[1] + '-' + tempEuroDate[0]
		current_time = str(datetime.datetime.now().time()).split(".")[0].replace(":", "_")
		if os.path.isdir('uploads/potato_field/'+euroDate) != True:
			os.mkdir('uploads/potato_field/'+euroDate)

		camera.annotate_text =" "+ euroDate + ' - ' + current_time.replace("_", ":") + " "
		camera.annotate_background = True
		# Finally, capture an image with a 6s exposure
		print("now starting to gather light..")
		#time.sleep(10)
		camera.capture('uploads/potato_field/'+euroDate+'/'+ euroDate+'-'+current_time, format="png")
		print("picture taken, now setting the framerate back to 1..")
		# framerate set back to one to prevent the friggin kernel from freezing
		camera.framerate = 1
		print("uploading the picture..")
		UploadAPicture('uploads/potato_field/'+euroDate+'/'+ euroDate+'-'+current_time, 'uploads/potato_field/'+euroDate)
		total_time = str(time.time() - start_time).split(".")[0]
		print("whole process took " + total_time + " amount of seconds")
		return



#def VideoStreamFunction():
	# this is a test function to see if video streaming can be implemented.
#	with picamera.PiCamera() as camera:
		# I believe all of this might have to happen inside a loop
#		while True:
			#use the camera to take a the information and transfer it to a stream



def UploadAPicture(image_path, folder_name):
    image_filename = os.path.basename(image_path)

    multipart_form_data = {
        'image': (image_filename, open(image_path, 'rb'))
    }
    body = {
    	'folder': folder_name
    }
    response = requests.post('http://13.ip-51-75-16.eu:2222/post/picture', data=body, files=multipart_form_data) 



def WriteErrorLog (e):
	file = open("error_logs.txt", "w")
	file.write("new error: \n")
	file.write(str(e))
	file.write("\n")
	file.close()


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
		

def GetTime():
	return str(datetime.datetime.now()).split(" ")[-1].split(".")[0].split(":")[0]


def MovementDetectionLoop():
	while True:
		#some code
		MovementDetection()

def MainLoop():
	counter = 0
	while True:
		# function starts, let's check the time of the day and act accordinly 
		# that means we either take a night light photo or a daylight one, bitch
		curtime = int(GetTime())
		if counter > 24:
			os.system('sudo reboot')
		else:
			if curtime > 22 or curtime < 4:
				#it's probably dark, take a night photo
				TakeNightlightPicture()
				#TakeDaylightPicture()
			else:
				#it's daytime, take normal exposure photo
				TakeDaylightPicture()
			#now after all that's done, let's wait approximately an hour
			counter += 1
			time.sleep(3600)



try:
	#movement_detection_loop_thread = threading.Thread(target=MovementDetectionLoop)
	main_loop = threading.Thread(target=MainLoop)
	#movement_detection_loop_thread.start()
	main_loop.start()
	print("threads started..")
	#TakeNightlightPicture()


except Exception as err:
	WriteErrorLog(err)

