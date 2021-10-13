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
    desc = "Tools to normalize an image dataset. Deletes all the image with resolution lower than specified --height and --width." 
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--verbose', action='store_true',
        help='Print progress to console.')

    parser.add_argument('--consider_rotating', action='store_true',
        help='Consider the possibility of rotation before deleting.')

    parser.add_argument('--dry', action='store_true',
        help='Only display images that are gonna be deleted, but do not actually delete them.')

    parser.add_argument('--input_folder', type=str,
        default='./input/',
        help='Directory path to the inputs folder. (default: %(default)s)')

    parser.add_argument('--width', type=int, 
        default=1280,
        help='Maximum width of output image. (default: %(default)s)')

    parser.add_argument('--height', type=int, 
        default=768,
        help='Maximum height of the output image. (default: %(default)s)')

    parser.add_argument('--offset', type=int, 
        default=0,
        help='Forgive offset lower than target width and height. (default: %(default)s)')

    parser.set_defaults(name=True)

    args = parser.parse_args()
    return args

def main():
    global args
    global count
    global inter
    args = parse_args()
    count = int(0)
    inter = cv2.INTER_CUBIC
    os.environ['OPENCV_IO_ENABLE_JASPER']= "true"

    base_dir = ''

    for root, subdirs, files in os.walk(args.input_folder):
        if(args.verbose): print('--\nroot = ' + root)

        if len(subdirs) > 0:
            base_dir = root 
            continue

        for subdir in subdirs:
            if(args.verbose): print('\t- subdirectory ' + subdir)

        current_subdir = os.path.split(root)[1]

        for filename in files:
            to_be_removed = False

            file_path = os.path.join(root, filename)
            if(args.verbose): print('\t- file %s (full path: %s)' % (filename, file_path))
            
            img = cv2.imread(file_path)

            if hasattr(img, 'copy'):
                # print('processing image: ' + filename)
                (h, w) = img.shape[:2]
                if w < h and args.consider_rotating:
                    img = imutils.rotate_bound(img, 90)
                    (h, w) = img.shape[:2]

                if w < args.width - args.offset or h < args.height - args.offset:
                    to_be_removed = True
                    count = count + int(1)
                
                if to_be_removed:
                    if not args.dry:
                        print('removing image: ' + file_path)
                        os.remove(file_path)    
                    else:
                        print('image to remove would be: ' + file_path)
                
    print('Counted {} images marked to be removed'.format(count))

if __name__ == "__main__":
    main()
