"""
This is the main script for controlling the BASLER Cameras.
"""

import time
from threading import Thread

import cv2
import numpy as np
from pypylon import pylon


# Local module and scripts


class Cameras:
	"""
	This class is used to control the BASLER Cameras.
	"""

	def __init__(self, queue_img0_orig, queue_img0_zoom, queue_img1_orig, queue_img1_zoom,
	             start_flag, flaf_light, flag_light_change, flag_camera_grab, flag_alignment_window):
		"""
		Constructor function which initializes and setups all variables
		and parameters for the class.
		"""
		try:
			# Limits the amount of cameras used for grabbing.
			# The bandwidth used by a FireWire camera device can be limited by adjusting the packet size.
			maxCamerasToUse = 2
			# The exit code of the sample application.
			exitCode = 0
			# Get the transport layer factory.
			self.tlFactory = pylon.TlFactory.GetInstance()
			# Get all attached devices and exit application if no device is found.
			self.devices = self.tlFactory.EnumerateDevices()

			if len(self.devices) == 0:
				raise pylon.RuntimeException("No camera present.")

			# Create an array of instant cameras for the found devices and avoid exceeding a maximum number of
			# devices.
			self.cameras = pylon.InstantCameraArray(min(len(self.devices), maxCamerasToUse))

			# Create and attach all Pylon Devices.
			for i, cam in enumerate(self.cameras):
				cam.Attach(self.tlFactory.CreateDevice(self.devices[i]))
			self.converter = pylon.ImageFormatConverter()

			# converting to opencv bgr format
			self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
			self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
		except Exception as e:
			print('Error in initializing the camera class')
			print(e)

		self.queue_img0_orig = queue_img0_orig
		self.queue_img0_zoom = queue_img0_zoom
		self.queue_img1_orig = queue_img1_orig
		self.queue_img1_zoom = queue_img1_zoom
		self.start_flag = start_flag
		self.flag_light = flaf_light
		self.flag_light_change = flag_light_change
		self.flag_camera_grab = flag_camera_grab
		self.flag_alignment_window = flag_alignment_window
		self.cameras[0].Open()
		self.cameras[0].ExposureAuto.SetValue('Off')
		self.cameras[0].ExposureTime.SetValue(800000)
		self.cameras[1].Open()
		self.cameras[1].ExposureAuto.SetValue('Off')
		self.cameras[1].ExposureTime.SetValue(100000)

		self.thread_read = Thread(target=self.camera_s_d)
		self.thread_read.daemon = True
		self.index_save_image = 0

	def update_cameras(self):
		"""
		This class method sets up the cameras to capture the required images.
		"""
		self.thread_read.start()

		self.cameras.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
		start_time = time.time()
		while self.cameras.IsGrabbing():
			current_time = time.time()
			elapsed_time = current_time - start_time

			# Fetch the raw images from camera
			grabResult0 = self.cameras[0].RetrieveResult(2000, pylon.TimeoutHandling_ThrowException)
			grabResult1 = self.cameras[1].RetrieveResult(2000, pylon.TimeoutHandling_ThrowException)

			image0 = self.converter.Convert(grabResult0)
			img0 = image0.GetArray()
			image1 = self.converter.Convert(grabResult1)
			img1 = image1.GetArray()

			# Original size is 2048 * 2448
			# Resize the original to the required size. Utilize the openCV tool.
			self.img0_orig = img0
			# Define the region to crop: (x, y, width, height)
			crop_region = (1640, 900, 300, 100)
			# Crop the image
			self.img0_zoom = self.img0_orig[crop_region[1]:crop_region[1] + crop_region[3],
			                 crop_region[0]:crop_region[0] + crop_region[2]]

			self.img1_orig = img1
			# Define the region to crop: (x, y, width, height)
			crop_region = (2050, 1000, 300, 100)
			# Crop the image
			self.img1_zoom = self.img1_orig[crop_region[1]:crop_region[1] + crop_region[3],
			                 crop_region[0]:crop_region[0] + crop_region[2]]

			# Acquire the lock and releases after process using context manager
			# To ensure that the marked array is a C-contiguous array

			self.queue_img0_orig.put(np.swapaxes(self.img0_orig, 0, 1))
			self.queue_img1_orig.put(np.swapaxes(self.img1_orig, 0, 1))
			self.queue_img0_zoom.put(np.swapaxes(self.img0_zoom, 0, 1))
			self.queue_img1_zoom.put(np.swapaxes(self.img1_zoom, 0, 1))

			# Store the captured processed image at a desired location.
			# with self.variables.lock_statistics:
			# if elapsed_time >= self.variables.save_meta_interval and self.variables.start_flag:
			# 	start_time = current_time  # Update the start time
			# 	cv2.imwrite(self.variables.path_meta + "/side_%s.png" % self.index_save_image, self.img0_orig)
			# 	cv2.imwrite(self.variables.path_meta + "/side_zoom_%s.png" % self.index_save_image, self.img0_zoom)
			# 	cv2.imwrite(self.variables.path_meta + '/bottom_%s.png' % self.index_save_image, self.img1_orig)
			# 	cv2.imwrite(self.variables.path_meta + '/bottom_zoom_%s.png' % self.index_save_image,
			# 	            self.img1_zoom)
			# 	self.index_save_image += 1
			# 	start_time = time.time()

			grabResult0.Release()
			grabResult1.Release()

			if self.start_flag.value:
				time.sleep(0.5)
			else:
				time.sleep(0.1)

			if self.flag_light_change.value:
				self.flag_light_change.value = False
				self.light_switch()
			# with self.variables.lock_setup_parameters:
			if not self.flag_camera_grab.value:
				break

	def light_switch(self):
		"""
		This class method sets the Exposure time based on a flag.
		"""

		# with self.variables.lock_setup_parameters:
		if not self.flag_light.value:
			self.cameras[0].Open()
			self.cameras[0].ExposureTime.SetValue(400)
			self.cameras[1].Open()
			self.cameras[1].ExposureTime.SetValue(2000)
		elif self.flag_light.value:
			self.cameras[0].Open()
			self.cameras[0].ExposureTime.SetValue(800000)
			self.cameras[1].Open()
			self.cameras[1].ExposureTime.SetValue(100000)

	def close_cameras(self):
		# Stop grabbing
		self.cameras.StopGrabbing()

		# Close camera resources
		for cam in self.cameras:
			cam.Close()

	def camera_s_d(self, ):
		"""
		This class method captures the images through the cameras,
		processes them and displays the processed image.
		"""

		windowName = 'Sample Alignment'

		while True:
			if self.flag_alignment_window.value:

				img0_zoom = cv2.resize(self.img0_orig[850:1050, 1550:1950], dsize=(2448, 1000),
				                       interpolation=cv2.INTER_CUBIC)
				img1_zoom = cv2.resize(self.img1_orig[1020:1170, 1700:2050], dsize=(2448, 1000),
				                       interpolation=cv2.INTER_CUBIC)
				img0_zoom = cv2.drawMarker(img0_zoom, (2120, 600), (0, 0, 255),
				                           markerType=cv2.MARKER_TRIANGLE_UP,
				                           markerSize=80, thickness=2, line_type=cv2.LINE_AA)
				img1_zoom = cv2.drawMarker(img1_zoom, (2120, 560), (0, 0, 255),
				                           markerType=cv2.MARKER_TRIANGLE_UP,
				                           markerSize=80, thickness=2, line_type=cv2.LINE_AA)
				img0_f = np.concatenate((self.img0_orig, img0_zoom), axis=0)
				img1_f = np.concatenate((self.img1_orig, img1_zoom), axis=0)
				vis = np.concatenate((img0_f, img1_f), axis=1)  # Combine 2 images horizontally
				# # Label the window
				cv2.namedWindow(windowName, cv2.WINDOW_NORMAL)
				# Resize the window
				cv2.resizeWindow(windowName, 2500, 1200)
				# displays image in specified window
				cv2.imshow(windowName, vis)
				k = cv2.waitKey(1)
				if k == 27:
					break

			else:
				cv2.destroyAllWindows()
				time.sleep(1)
				pass
			if not self.flag_camera_grab.value:
				break


def cameras_run(queue_img0_orig, queue_img0_zoom, queue_img1_orig, queue_img1_zoom,
                start_flag, flaf_light, flag_light_change, flag_camera_grab, flag_alignment_window):
	"""
	This function is used to run the cameras.

		Args:
			queue_img0_orig: Queue to store the original image from camera 0
			queue_img0_zoom: Queue to store the zoomed image from camera 0
			queue_img1_orig: Queue to store the original image from camera 1
			queue_img1_zoom: Queue to store the zoomed image from camera 1
			start_flag: Flag to start the cameras
			flaf_light: Flag to switch the light
			flag_camera_grab: Flag to grab the images from the cameras
			flag_alignment_window: Flag to display the alignment window
		Return:
			None
	"""
	try:
		camera = Cameras(queue_img0_orig, queue_img0_zoom, queue_img1_orig, queue_img1_zoom,
		                 start_flag, flaf_light, flag_light_change, flag_camera_grab, flag_alignment_window)
		camera.update_cameras()
	finally:
		camera.close_cameras()
