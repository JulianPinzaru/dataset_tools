import argparse
import numpy as np
import scipy.ndimage as pyimg
import os
import imutils
import cv2
import random
import math

# print(cv2.__version__)

def parse_args():
	desc = "Tools to normalize an image dataset" 
	parser = argparse.ArgumentParser(description=desc)

	parser.add_argument('--verbose', action='store_true',
		help='Print progress to console.')

	parser.add_argument('--input_folder', type=str,
		default='./input/',
		help='Directory path to the inputs folder. (default: %(default)s)')

	parser.add_argument('--output_folder', type=str,
		default='./output/',
		help='Directory path to the outputs folder. (default: %(default)s)')

	parser.add_argument('--process_type', type=str,
		default='resize',
		help='Process to use. ["resize","resize_to_rectangle","square","crop_center_square","crop_to_square","canny","canny-pix2pix","crop_square_patch","scale","many_squares","crop","distance"] (default: %(default)s)')

	parser.add_argument('--blur_type', type=str,
		default='none',
		help='Blur process to use. Use with --process_type canny. ["none","gaussian","median"] (default: %(default)s)')

	parser.add_argument('--blur_amount', type=int, 
		default=1,
		help='Amount of blur to apply (use odd numbers). Use with --blur_type.  (default: %(default)s)')

	parser.add_argument('--max_size', type=int, 
		default=512,
		help='Maximum width or height of the output images. (default: %(default)s)')

	parser.add_argument('--height', type=int, 
		default=512,
		help='Maximum height of the output image (for use with --process_type crop). (default: %(default)s)')

	parser.add_argument('--width', type=int, 
		default=512,
		help='Maximum width of output image (for use with --process_type crop). (default: %(default)s)')

	parser.add_argument('--allow_rotating', action='store_true',
		help='Used for resize_to_rectangle to rotate images that are portraits. (default: %(default)s)')

	parser.add_argument('--shift_y', type=int, 
		default=0,
		help='y coordinate shift (for use with --process_type crop). (default: %(default)s)')

	parser.add_argument('--v_align', type=str, 
		default='center',
		help='-vertical alignment options: top, bottom, center (for use with --process_type crop_to_square). (default: %(default)s)')

	parser.add_argument('--h_align', type=str, 
		default='center',
		help='-vertical alignment options: left, right, center (for use with --process_type crop_to_square). (default: %(default)s)')

	parser.add_argument('--shift_x', type=int, 
		default=0,
		help='x coordinate shift (for use with --process_type crop). (default: %(default)s)')

	parser.add_argument('--scale', type=float, 
		default=2.0,
		help='Scalar value. For use with scale process type (default: %(default)s)')

	parser.add_argument('--direction', type=str,
		default='AtoB',
		help='Paired Direction. For use with pix2pix process. ["AtoB","BtoA"] (default: %(default)s)')

	parser.add_argument('--border_type', type=str,
		default='stretch',
		help='Border style to use when using the square process type ["stretch","reflect","solid"] (default: %(default)s)')

	parser.add_argument('--border_color', type=str,
		default='255,255,255',
		help='border color to use with the `solid` border type; use bgr values (default: %(default)s)')

	parser.add_argument('--jpeg_quality', type=int,
		default=100,
		help='the quality for jpeg to be saved; use 90 or 100 for most of the cases (default: %(default)s)')

	# parser.add_argument('--blur_size', type=int, 
	# 	default=3,
	# 	help='Blur size. For use with "canny" process. (default: %(default)s)')

	parser.add_argument('--mirror', action='store_true',
		help='Adds mirror augmentation.')

	parser.add_argument('--rotate', action='store_true',
		help='Adds 90 degree rotation augmentation.')

	parser.add_argument('--file_extension', type=str,
		default='png',
		help='Border style to use when using the square process type ["png","jpg"] (default: %(default)s)')

	feature_parser = parser.add_mutually_exclusive_group(required=False)
	feature_parser.add_argument('--keep_name', dest='name', action='store_true')
	feature_parser.add_argument('--numbered', dest='name', action='store_false')
	parser.set_defaults(name=True)

	args = parser.parse_args()
	return args


def image_resize(image, width = None, height = None, max = None):
	# initialize the dimensions of the image to be resized and
	# grab the image size
	dim = None
	(h, w) = image.shape[:2]

	if max is not None:
		if w > h:
			# produce
			r = max / float(w)
			dim = (max, int(h * r))
		elif h > w:
			r = max / float(h)
			dim = (int(w * r), max)
		else :
			dim = (max, max)

	else: 
		# if both the width and height are None, then return the
		# original image
		if width is None and height is None:
			return image

		# check to see if the width is None
		if width is None:
			# calculate the ratio of the height and construct the
			# dimensions
			r = height / float(h)
			dim = (int(w * r), height)

		# otherwise, the height is None
		else:
			# calculate the ratio of the width and construct the
			# dimensions
			r = width / float(w)
			dim = (width, int(h * r))

	# resize the image
	resized = cv2.resize(image, dim, interpolation = inter)

	# return the resized image
	return resized

def image_resize_to_rectangle(image, target_width=1280, target_height=768, allow_rotating=True):
	assert target_width > target_height

	# initialize the dimensions of the image to be resized and
	# grab the image size
	dim = None
	(h, w) = image.shape[:2]

    if allow_rotating and h > w:
        # why not rotating it ?
        image = imutils.rotate_bound(image, 90)
        (h, w) = image.shape[:2]

	need_to_stretch = h < target_height or w < target_width
	if need_to_stretch: # for smaller images we just do a raw resize dont care about ratio or proprotions
		resized = cv2.resize(image, (target_width, target_height), interpolation = inter)
		return resized

	is_rectangle = True if w > h else False
	is_portrait = True if h > w else False
	is_square = True if h == w else False

	if is_rectangle or is_portrait:
		# Scenarios: 1920x1080, 1440x1024 etc
		ratio = np.amax([target_height / float(h), target_width / float(w)])

		resize_width = math.ceil(ratio * w) if w - target_width < h - target_height else target_width
		resize_height = math.ceil(ratio * h) if w - target_width > h - target_height else target_height 
		dim = (int(resize_width), int(resize_height))
		resized = cv2.resize(image, dim, interpolation = inter)
		(h, w) = resized.shape[:2] # 1365x768

		# Centralize and crop
		to_trim_width = w - target_width
		to_trim_height = h - target_height
		crop_img = resized[
			int(to_trim_height/2) : int(h - to_trim_height/2),
			int(to_trim_width/2) : int(w - to_trim_width/2)
		]
		return crop_img

	if is_square:
		# Scenarios: 1920x1080, 1440x1024 etc
		dim = (target_width, target_width) # keep it square
		resized = cv2.resize(image, dim, interpolation = inter)
		(h, w) = resized.shape[:2] # 1365x768

		# Centralize and crop
		to_trim_width = w - target_width
		to_trim_height = h - target_height
		crop_img = resized[
			int(to_trim_height/2) : int(h - to_trim_height/2),
			int(to_trim_width/2) : int(w - to_trim_width/2)
		]
		return crop_img

	return image


def image_scale(image, scalar = 1.0):
	(h, w) = image.shape[:2]
	dim = (int(w*scalar),int(h*scalar))
	# resize the image
	resized = cv2.resize(image, dim, interpolation = inter)
	
	# return the resized image
	return resized

def arbitrary_crop(img, h_crop,w_crop):
	error = False
	bType = cv2.BORDER_REPLICATE
	if(args.border_type == 'solid'):
		bType = cv2.BORDER_CONSTANT
	elif (args.border_type == 'reflect'):
		bType = cv2.BORDER_REFLECT

	(h, w) = img.shape[:2]
	if(h>h_crop):
		hdiff = int((h-h_crop)/2) + args.shift_y

		if( ((hdiff+h_crop) > h) or (hdiff < 0)):
			print("error! crop settings are too much for this image")
			error = True
		else:
			img = img[hdiff:hdiff+h_crop,0:w]
	if(w>w_crop):
		wdiff = int((w-w_crop)/2) + args.shift_x
		
		if( ((wdiff+w_crop) > w) or (wdiff < 0) ):
			print("error! crop settings are too much for this image")
			error = True
		else:
			img = img[0:h_crop,wdiff:wdiff+w_crop]
	return img, error

def crop_to_square(img):
	(h, w) = img.shape[:2]
	
	cropped = img.copy()
	if w > h:	
		if (args.h_align=='left'):
			print('here first')
			cropped = img[:h,:h]
		elif (args.h_align=='right'):
			cropped = img[0:h, w-h:w]
		else:
			diff = int((w-h)/2)
			cropped = img[0:h, diff:diff+h]
	elif h > w:
		if (args.v_align=='top'):
			cropped = img[:w, :w]
		elif (args.v_align=='bottom'):
			cropped = img[h-w:h, 0:w]
		else:
			diff = int((h-w)/2)
			cropped = img[diff:diff+w, 0:w]
		
	return cropped

def crop_center_square(img, size, interpolation=cv2.INTER_AREA):
	h, w = img.shape[:2]
	min_size = np.amin([h,w])

	# Centralize and crop
	crop_img = img[int(h/2-min_size/2):int(h/2+min_size/2), int(w/2-min_size/2):int(w/2+min_size/2)]
	resized = cv2.resize(crop_img, (size, size), interpolation=interpolation)

	return resized

def crop_square_patch(img, imgSize):
	(h, w) = img.shape[:2]

	rH = random.randint(0,h-imgSize)
	rW = random.randint(0,w-imgSize)
	cropped = img[rH:rH+imgSize,rW:rW+imgSize]

	return cropped

def processCanny(img):
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	
	if(args.blur_type=='gaussian'):
		gray = cv2.GaussianBlur(gray, (args.blur_amount, args.blur_amount), 0)
	elif(args.blur_type=='median'):
		gray = cv2.medianBlur(gray,args.blur_amount)
	gray = cv2.Canny(gray,100,300)

	return gray

def makeResize(img,filename,scale):

	remakePath = args.output_folder + str(scale)+"/"
	if not os.path.exists(remakePath):
		os.makedirs(remakePath)

	img_copy = img.copy()
	img_copy = image_resize(img_copy, max = scale)

	if(args.file_extension == "png"):
		new_file = os.path.splitext(filename)[0] + ".png"
		cv2.imwrite(os.path.join(remakePath, new_file), img_copy, [cv2.IMWRITE_PNG_COMPRESSION, 0])
	elif(args.file_extension == "jpg"):
		new_file = os.path.splitext(filename)[0] + ".jpg"
		cv2.imwrite(os.path.join(remakePath, new_file), img_copy, [cv2.IMWRITE_JPEG_QUALITY, args.jpeg_quality])

	if (args.mirror): flipImage(img_copy,new_file,remakePath)
	if (args.rotate): rotateImage(img_copy,new_file,remakePath)

def makeResizeToRectangle(img,filename,width,height,allow_rotating):
	remakePath = args.output_folder + "-resize_rectangle-"+str(width)+"x"+str(height)+"/"
	if not os.path.exists(remakePath):
		os.makedirs(remakePath)

	img_copy = img.copy()
	img_copy = image_resize_to_rectangle(img_copy, target_width = width, target_height = height, allow_rotating=allow_rotating)

	if(args.file_extension == "png"):
		new_file = os.path.splitext(filename)[0] + ".png"
		cv2.imwrite(os.path.join(remakePath, new_file), img_copy, [cv2.IMWRITE_PNG_COMPRESSION, 0])
	elif(args.file_extension == "jpg"):
		new_file = os.path.splitext(filename)[0] + ".jpg"
		cv2.imwrite(os.path.join(remakePath, new_file), img_copy, [cv2.IMWRITE_JPEG_QUALITY, args.jpeg_quality])

	if (args.mirror): flipImage(img_copy,new_file,remakePath)
	if (args.rotate): rotateImage(img_copy,new_file,remakePath)

def makeDistance(img,filename,scale):
	makePath = args.output_folder + "distance-"+ str(args.max_size)+"/"
	if not os.path.exists(makePath):
		os.makedirs(makePath)

	img_copy = img.copy()
	img_copy = image_resize(img_copy, max = scale)

	BW = img_copy[:,:,0] > 127
	G_channel = pyimg.distance_transform_edt(BW)
	G_channel[G_channel>32]=32
	B_channel = pyimg.distance_transform_edt(1-BW)
	B_channel[B_channel>200]=200
	img_copy[:,:,1] = G_channel.astype('uint8')
	img_copy[:,:,0] = B_channel.astype('uint8')

	if(args.file_extension == "png"):
		new_file = os.path.splitext(filename)[0] + ".png"
		cv2.imwrite(os.path.join(makePath, new_file), img_copy, [cv2.IMWRITE_PNG_COMPRESSION, 0])
	elif(args.file_extension == "jpg"):
		new_file = os.path.splitext(filename)[0] + ".jpg"
		cv2.imwrite(os.path.join(makePath, new_file), img_copy, [cv2.IMWRITE_JPEG_QUALITY, args.jpeg_quality])

	if (args.mirror): flipImage(img_copy,new_file,makePath)
	if (args.rotate): rotateImage(img_copy,new_file,makePath)

def makeScale(img,filename,scale):

	remakePath = args.output_folder + "scale_"+str(scale)+"/"
	if not os.path.exists(remakePath):
		os.makedirs(remakePath)

	img_copy = img.copy()
	
	img_copy = image_scale(img_copy, scale)

	new_file = os.path.splitext(filename)[0] + ".png"
	cv2.imwrite(os.path.join(remakePath, new_file), img_copy, [cv2.IMWRITE_PNG_COMPRESSION, 0])

	if (args.mirror): flipImage(img_copy,new_file,remakePath)
	if (args.rotate): rotateImage(img_copy,new_file,remakePath)


def makeSquare(img,filename,scale):
	sqPath = args.output_folder + "sq-"+str(scale)+"/"
	if not os.path.exists(sqPath):
		os.makedirs(sqPath)

	bType = cv2.BORDER_REPLICATE
	if(args.border_type == 'solid'):
		bType = cv2.BORDER_CONSTANT
	elif (args.border_type == 'reflect'):
		bType = cv2.BORDER_REFLECT
	img_sq = img.copy()
	(h, w) = img_sq.shape[:2]
	if((h < scale) and (w < scale)):
		if(args.verbose): print('skip resize')
	else:
		img_sq = image_resize(img_sq, max = scale)

	bColor = [int(item) for item in args.border_color.split(',')]

	(h, w) = img_sq.shape[:2]
	if(h > w):
		# pad left/right
		diff = h-w
		if(diff%2 == 0):
			img_sq = cv2.copyMakeBorder(img_sq, 0, 0, int(diff/2), int(diff/2), bType,value=bColor)
		else:
			img_sq = cv2.copyMakeBorder(img_sq, 0, 0, int(diff/2)+1, int(diff/2), bType,value=bColor)
	elif(w > h):
		# pad top/bottom
		diff = w-h
		if(diff%2 == 0):
			img_sq = cv2.copyMakeBorder(img_sq, int(diff/2), int(diff/2), 0, 0, bType,value=bColor)
		else:
			img_sq = cv2.copyMakeBorder(img_sq, int(diff/2), int(diff/2)+1, 0, 0, bType,value=bColor)
	else:
		diff = scale-h
		if(diff%2 == 0):
			img_sq = cv2.copyMakeBorder(img_sq, int(diff/2), int(diff/2), int(diff/2), int(diff/2), bType,value=bColor)
		else:
			img_sq = cv2.copyMakeBorder(img_sq, int(diff/2), int(diff/2)+1, int(diff/2), int(diff/2)+1, bType,value=bColor)

	if(args.file_extension == "png"):
		new_file = os.path.splitext(filename)[0] + ".png"
		cv2.imwrite(os.path.join(sqPath, new_file), img_sq, [cv2.IMWRITE_PNG_COMPRESSION, 0])
	elif(args.file_extension == "jpg"):
		new_file = os.path.splitext(filename)[0] + ".jpg"
		cv2.imwrite(os.path.join(sqPath, new_file), img_sq, [cv2.IMWRITE_JPEG_QUALITY, args.jpeg_quality])

	if (args.mirror): flipImage(img_sq,new_file,sqPath)
	if (args.rotate): rotateImage(img_sq,new_file,sqPath)

	
	

def makeCanny(img,filename,scale):
	make_path = args.output_folder + "canny-"+str(scale)+"/"
	if not os.path.exists(make_path):
		os.makedirs(make_path)

	img_copy = img.copy()
	img_copy = image_resize(img_copy, max = scale)
	gray = processCanny(img_copy)

	# save out
	if(args.file_extension == "png"):
		new_file = os.path.splitext(filename)[0] + ".png"
		cv2.imwrite(os.path.join(make_path, new_file), gray, [cv2.IMWRITE_PNG_COMPRESSION, 0])
	elif(args.file_extension == "jpg"):
		new_file = os.path.splitext(filename)[0] + ".jpg"
		cv2.imwrite(os.path.join(make_path, new_file), gray, [cv2.IMWRITE_JPEG_QUALITY, args.jpeg_quality])

	if (args.mirror): flipImage(img_copy,new_file,make_path)
	if (args.rotate): rotateImage(img_copy,new_file,make_path)

def makeCrop(img,filename):
	make_path = args.output_folder + "crop-"+str(args.height)+"x"+str(args.width)+"/"
	if not os.path.exists(make_path):
		os.makedirs(make_path)

	img_copy = img.copy()
	img_copy,error = arbitrary_crop(img_copy,args.height,args.width)

	if (error==False):
		if(args.file_extension == "png"):
			new_file = os.path.splitext(filename)[0] + ".png"
			cv2.imwrite(os.path.join(make_path, new_file), img_copy, [cv2.IMWRITE_PNG_COMPRESSION, 0])
		elif(args.file_extension == "jpg"):
			new_file = os.path.splitext(filename)[0] + ".jpg"
			cv2.imwrite(os.path.join(make_path, new_file), img_copy, [cv2.IMWRITE_JPEG_QUALITY, args.jpeg_quality])

		if (args.mirror): flipImage(img_copy,new_file,make_path)
		if (args.rotate): rotateImage(img_copy,new_file,make_path)
	else:
		if(args.verbose): print(filename+" returned an error")

def makeCropCenterSquare(img,filename,max_size):
	make_path = args.output_folder + "crop-center-square-"+str(max_size)+"/"
	if not os.path.exists(make_path):
		os.makedirs(make_path)
	img_copy = img.copy()
	img_copy = crop_center_square(img_copy, max_size)

	if(args.file_extension == "png"):
		new_file = os.path.splitext(filename)[0] + ".png"
		cv2.imwrite(os.path.join(make_path, new_file), img_copy, [cv2.IMWRITE_PNG_COMPRESSION, 0])
	elif(args.file_extension == "jpg"):
		new_file = os.path.splitext(filename)[0] + ".jpg"
		cv2.imwrite(os.path.join(make_path, new_file), img_copy, [cv2.IMWRITE_JPEG_QUALITY, args.jpeg_quality])

	if (args.mirror): flipImage(img_copy,new_file,make_path)
	if (args.rotate): rotateImage(img_copy,new_file,make_path)

def makeSquareCrop(img,filename,scale):
	make_path = args.output_folder + "sq-"+str(scale)+"/"
	if not os.path.exists(make_path):
		os.makedirs(make_path)

	img_copy = img.copy()
	img_copy = crop_to_square(img_copy)
	img_copy = image_resize(img_copy, max = scale)

	if(args.file_extension == "png"):
		new_file = os.path.splitext(filename)[0] + ".png"
		cv2.imwrite(os.path.join(make_path, new_file), img_copy, [cv2.IMWRITE_PNG_COMPRESSION, 0])
	elif(args.file_extension == "jpg"):
		new_file = os.path.splitext(filename)[0] + ".jpg"
		cv2.imwrite(os.path.join(make_path, new_file), img_copy, [cv2.IMWRITE_JPEG_QUALITY, args.jpeg_quality])

	if (args.mirror): flipImage(img_copy,new_file,make_path)
	if (args.rotate): rotateImage(img_copy,new_file,make_path)

def makeManySquares(img,filename,scale):
	make_path = args.output_folder + "many_squares-"+str(scale)+"/"
	if not os.path.exists(make_path):
		os.makedirs(make_path)

	img_copy = img.copy()
	(h, w) = img_copy.shape[:2]
	img_ratio = h/w

	if(img_ratio >= 1.25):

		#crop images from top and bottom
		crop = img_copy[0:w,0:w]
		crop = image_resize(crop, max = scale)
		new_file = os.path.splitext(filename)[0] + "-1.png"
		cv2.imwrite(os.path.join(make_path, new_file), crop, [cv2.IMWRITE_PNG_COMPRESSION, 0])
		if (args.mirror): flipImage(crop,new_file,make_path)
		if (args.rotate): rotateImage(crop,filename,make_path)

		crop = img_copy[h-w:h,0:w]
		crop = image_resize(crop, max = scale)
		new_file = os.path.splitext(filename)[0] + "-2.png"
		cv2.imwrite(os.path.join(make_path, new_file), crop, [cv2.IMWRITE_PNG_COMPRESSION, 0])
		if (args.mirror): flipImage(crop,new_file,make_path)
		if (args.rotate): rotateImage(crop,filename,make_path)

	elif(img_ratio <= .8):
		#crop images from left and right
		print(os.path.splitext(filename)[0] + ': wide image')
		
		crop = img_copy[0:h,0:h]
		crop = image_resize(crop, max = scale)
		new_file = os.path.splitext(filename)[0] + "-wide1.png"
		cv2.imwrite(os.path.join(make_path, new_file), crop, [cv2.IMWRITE_PNG_COMPRESSION, 0])
		if (args.mirror): flipImage(crop,new_file,make_path)
		if (args.rotate): rotateImage(crop,filename,make_path)

		crop = img_copy[0:h,w-h:w]
		crop = image_resize(crop, max = scale)
		new_file = os.path.splitext(filename)[0] + "-wide2.png"
		cv2.imwrite(os.path.join(make_path, new_file), crop, [cv2.IMWRITE_PNG_COMPRESSION, 0])
		if (args.mirror): flipImage(crop,new_file,make_path)
		if (args.rotate): rotateImage(crop,filename,make_path)

	else:
		img_copy = crop_to_square(img_copy)
		img_copy = image_resize(img_copy, max = scale)
		new_file = os.path.splitext(filename)[0] + ".png"
		cv2.imwrite(os.path.join(make_path, new_file), img_copy, [cv2.IMWRITE_PNG_COMPRESSION, 0])
		if (args.mirror): flipImage(img_copy,new_file,make_path)
		if(args.rotate): rotateImage(img_copy,filename,make_path)
		

def makeSquareCropPatch(img,filename,scale):
	make_path = args.output_folder + "sq-"+str(scale)+"/"
	if not os.path.exists(make_path):
		os.makedirs(make_path)

	img_copy = img.copy()
	img_copy = crop_square_patch(img_copy,args.max_size)

	new_file = os.path.splitext(filename)[0] + ".png"
	cv2.imwrite(os.path.join(make_path, new_file), img_copy, [cv2.IMWRITE_PNG_COMPRESSION, 0])

	if (args.mirror): flipImage(img_copy,new_file,make_path)
	if (args.rotate): rotateImage(img_copy,new_file,make_path)

def makePix2Pix(img,filename,scale,direction="BtoA",value=[0,0,0]):
	img_p2p = img.copy()
	img_p2p = image_resize(img_p2p, max = scale)
	(h, w) = img_p2p.shape[:2]
	bType = cv2.BORDER_CONSTANT
	
	make_path = args.output_folder + "pix2pix-"+str(h)+"/"
	if not os.path.exists(make_path):
		os.makedirs(make_path)

	canny = cv2.cvtColor(processCanny(img_p2p),cv2.COLOR_GRAY2RGB)
	
	if(direction=="BtoA"):
		img_p2p = cv2.copyMakeBorder(img_p2p, 0, 0, w, 0, bType, None, value)
		img_p2p[0:h,0:w] = canny
	
	if(args.file_extension == "png"):
		new_file = os.path.splitext(filename)[0] + ".png"
		cv2.imwrite(os.path.join(make_path, new_file), img_p2p, [cv2.IMWRITE_PNG_COMPRESSION, 0])
	elif(args.file_extension == "jpg"):
		new_file = os.path.splitext(filename)[0] + ".jpg"
		cv2.imwrite(os.path.join(make_path, new_file), img_p2p, [cv2.IMWRITE_JPEG_QUALITY, args.jpeg_quality])

def flipImage(img,filename,path):
	flip_img = cv2.flip(img, 1)
	flip_file = os.path.splitext(filename)[0] + "-flipped.png"
	cv2.imwrite(os.path.join(path, flip_file), flip_img, [cv2.IMWRITE_PNG_COMPRESSION, 0])

def rotateImage(img,filename,path):
	r = img.copy() 
	r = imutils.rotate_bound(r, 90)

	if(args.file_extension == "png"):
		r_file = os.path.splitext(filename)[0] + "-rot90.png"
		cv2.imwrite(os.path.join(path, r_file), r, [cv2.IMWRITE_PNG_COMPRESSION, 0])
	elif(args.file_extension == "jpg"):
		r_file = os.path.splitext(filename)[0] + "-rot90.jpg"
		cv2.imwrite(os.path.join(path, r_file), r, [cv2.IMWRITE_JPEG_QUALITY, args.jpeg_quality])

	r = imutils.rotate_bound(r, 90)
	if(args.file_extension == "png"):
		r_file = os.path.splitext(filename)[0] + "-rot180.png"
		cv2.imwrite(os.path.join(path, r_file), r, [cv2.IMWRITE_PNG_COMPRESSION, 0])
	elif(args.file_extension == "jpg"):
		r_file = os.path.splitext(filename)[0] + "-rot180.jpg"
		cv2.imwrite(os.path.join(path, r_file), r, [cv2.IMWRITE_JPEG_QUALITY, args.jpeg_quality])

	r = imutils.rotate_bound(r, 90)
	if(args.file_extension == "png"):
		r_file = os.path.splitext(filename)[0] + "-rot270.png"
		cv2.imwrite(os.path.join(path, r_file), r, [cv2.IMWRITE_PNG_COMPRESSION, 0])
	elif(args.file_extension == "jpg"):
		r_file = os.path.splitext(filename)[0] + "-rot270.jpg"
		cv2.imwrite(os.path.join(path, r_file), r, [cv2.IMWRITE_JPEG_QUALITY, args.jpeg_quality])

def processImage(img,filename):

	if args.process_type == "resize":	
		makeResize(img,filename,args.max_size)
	if args.process_type == 'resize_to_rectangle':
		makeResizeToRectangle(img,filename,args.width,args.height,args.allow_rotating)
	if args.process_type == "resize_pad":	
		makeResizePad(img,filename,args.max_size)
	if args.process_type == "square":
		makeSquare(img,filename,args.max_size)
	if args.process_type == "crop_to_square":
		makeSquareCrop(img,filename,args.max_size)
	if args.process_type == "crop_center_square":
		makeCropCenterSquare(img,filename,args.max_size)
	if args.process_type == "canny":
		makeCanny(img,filename,args.max_size)
	if args.process_type == "canny-pix2pix":
		makePix2Pix(img,filename,args.max_size)
	if args.process_type == "crop_square_patch":
		makeSquareCropPatch(img,filename,args.max_size)
	if args.process_type == "scale":
		makeScale(img,filename,args.scale)
	if args.process_type == "many_squares":
		makeManySquares(img,filename,args.max_size)
	if args.process_type == "crop":
		makeCrop(img,filename)
	if args.process_type == "distance":
		makeDistance(img,filename,args.max_size)

def main():
	global args
	global count
	global inter
	args = parse_args()
	count = int(0)
	inter = cv2.INTER_CUBIC
	os.environ['OPENCV_IO_ENABLE_JASPER']= "true"

	for root, subdirs, files in os.walk(args.input_folder):
		if(args.verbose): print('--\nroot = ' + root)

		for subdir in subdirs:
			if(args.verbose): print('\t- subdirectory ' + subdir)

		for filename in files:
			file_path = os.path.join(root, filename)
			if(args.verbose): print('\t- file %s (full path: %s)' % (filename, file_path))
			
			img = cv2.imread(file_path)

			if hasattr(img, 'copy'):
				print('processing image: ' + filename)
				if args.name:
					processImage(img,filename)
				else:
					processImage(img,str(count))
				count = count + int(1)


if __name__ == "__main__":
	main()
