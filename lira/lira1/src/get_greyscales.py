"""
Archives all images as greyscales from our data_dir directory,
    in a .h5 file.

Usually, these images are quite large.

-Blake Edwards / Dark Element
"""

import os, sys
import numpy as np
import cv2
import h5py

def recursive_get_paths(img_dir):
    paths = []
    for (path, dirs, fnames) in os.walk(img_dir):
        for fname in fnames:
            paths.append((os.path.join(path, fname), fname))
    return paths

def load_greyscales(data_dir, archive_dir):

    print "Getting Image Paths..."
    sample_path_infos = recursive_get_paths(data_dir)

    #Open our archive
    print "Creating Archive..."
    with h5py.File(archive_dir, "w") as hf:

        #Loop through samples
        for sample_i, sample_path_info in enumerate(sample_path_infos):
            sample_path, sample_fname = sample_path_info

            sys.stdout.write("\rGetting Greyscale of Image #%i:%s" % (sample_i, sample_fname))
            sys.stdout.flush()

            #Get greyscale version of img
            img = cv2.imread(sample_path, 0)

            #Archive greyscale
            hf.create_dataset(str(sample_i), data=img)

    print ""#flush formatting

#load_greyscales("../data/test_slides", "../data/greyscales.h5")
