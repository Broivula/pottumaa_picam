# this file gets run on a separate thread
# its job is to take a picture when commanded
# save it to a folder
# and tell networker to upload it
import numpy as np
import io
import cv2
import picamera
import time
import datetime
import os
import pi_cam_networking
import asyncio

from fractions import Fraction
from error_logging import handle_error_log

class _PiCamera(object):
    networking_que = None
    inUse = False
    cycle_time = 3600
    cam_que = None

    def __init__(self):
        print("camera init.")

    def GetTime(self):
            return str(datetime.datetime.now()).split(" ")[-1].split(".")[0].split(":")[0]

    def startMainCameraLoop(self, cam_que):
        self.cam_que = cam_que
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        future = asyncio.ensure_future(self.mainCameraLoop())
        loop.run_until_complete(future)


    def assign_networking_queue(self,net_que):
        self.networking_que = net_que

    def checkBrightness(self):
        stream = io.BytesIO()
        with picamera.PiCamera() as camera:
            camera.start_preview()
            time.sleep(2)
            camera.capture(stream, format='jpeg')
        data = np.fromstring(stream.getvalue(), dtype=np.uint8)
        image = cv2.imdecode(data, 1)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        b_mean = hsv[...,2].mean()
        print("test brigtness: " + str(b_mean) + " and time: " + self.GetTime() )
        return b_mean


    def TakeDaylightPicture(self):
            with picamera.PiCamera() as camera:
                    print("starting the function to take a normal picture..")
                    camera.resolution=(1280, 720)
                    print("camera instatiated, wait a few seconds for the auto exposure to kick in.")
                    time.sleep(4)
                    date =str(datetime.datetime.now()).split(" ")[0]
                    tempEuroDate = date.split("-")
                    euroDate = "potato-" + tempEuroDate[2] + '-' + tempEuroDate[1] + '-' + tempEuroDate[0]
                    current_time = str(datetime.datetime.now().time()).split(".")[0].replace(":", "_")
                    if os.path.isdir('uploads/potato_field/'+euroDate) != True:
                            os.mkdir('uploads/potato_field/'+euroDate)


                    camera.annotate_text =" "+ euroDate + ' - ' + current_time.replace("_", ":") + " "
                    camera.annotate_background = True
                    camera.capture('uploads/potato_field/'+euroDate+'/'+ euroDate+'-'+current_time, format="png")
                   # result = pi_cam_networking.UploadAPicture('uploads/potato_field/'+euroDate+'/'+ euroDate+'-'+current_time, 'uploads/potato_field/'+euroDate)
                    self.networking_que.put(('uploads/potato_field/'+euroDate+'/'+ euroDate+'-'+current_time, 'uploads/potato_field/'+euroDate))
                   # print(result)
                    #camera.close()
                    return

    def isCameraInUse(self):
        return self.inUse

    def TakeNightlightPicture(self, light_settings):
            with picamera.PiCamera() as camera:
                    print("starting the function for night light picture")
                    start_time = time.time()
                    camera.resolution = (1280, 720)
                    camera.framerate = Fraction(1,6)
                    print("setting the shutterspeed to long exposure, also iso to 800")
                    camera.shutter_speed  = light_settings["s_speed"]
                    camera.exposure_mode = 'off'
                    camera.iso = 800
                    print("printing extra info")
                    print("exp speed")
                    print(caamera.exposure_speed)
                    print("shutter speed")
                    print(camera.shutter_speed)
                    print("a small delay to calculate the light..")

                   # while camera.analog_gain < 1 or camera.digital_gain < 1:
                   #         print("camera analog gain: "+ str(float(camera.analog_gain)))
                   #         print("camera digital gain: "+ str(float(camera.digital_gain)))
                   #         time.sleep(0.5)

                    date =str(datetime.datetime.now()).split(" ")[0]
                    tempEuroDate = date.split("-")
                    euroDate = "potato-" + tempEuroDate[2] + '-' + tempEuroDate[1] + '-' + tempEuroDate[0]
                    current_time = str(datetime.datetime.now().time()).split(".")[0].replace(":", "_")
                    if os.path.isdir('uploads/potato_field/'+euroDate) != True:
                            os.mkdir('uploads/potato_field/'+euroDate)

                    camera.annotate_text =" "+ euroDate + ' - ' + current_time.replace("_", ":") + " "
                    camera.annotate_background = True
                    print("now starting to gather light..")
                    camera.capture('uploads/potato_field/'+euroDate+'/'+ euroDate+'-'+current_time, format="png")
                    print("picture taken, now setting the framerate back to 1..")
                    # framerate set back to one to prevent the friggin kernel from freezing
                    camera.framerate = 1
                    print("uploading the picture..")
                    self.networking_que.put(('uploads/potato_field/'+euroDate+'/'+ euroDate+'-'+current_time, 'uploads/potato_field/'+euroDate))
                    return

    def startPicturePipeline(self):
        try:
            self.inUse = True
            print("starting picture pipeline..")
            brightness = self.checkBrightness()
            # on some night time photos, it's still gathering too much light - which produces overlit pictures
            # function determineBetterLigth should ease this issue
            if brightness < 70:
                self.TakeNightlightPicture(self.determineBetterLight(brightness))
            else:
                self.TakeDaylightPicture()
            self.inUse = False
        except Exception as err:
            print('error in the picture pipeline process. error msg: ')
            print(err)
            handle_error_log(__file__, str(err))

    def determineBetterLight(self, value):
        if value > 45:
            return {"s_speed":2000000}    # as in low amount of light gathering
        elif value > 25:
            return {"s_speed":4000000}     
        else:
            return {"s_speed":6000000} 

   
    async def mainCameraLoop(self):
        counter = 0
        while 1:
            curtime = int(self.GetTime())
            if counter > 12:
                os.system('sudo reboot')
            else:
                self.cam_que.put("take_picture")
                counter += 1
                await asyncio.sleep(self.cycle_time)
