import sys, os, time
import numpy as np
import h5py, pickle
import cv2

import static_config
from static_config import StaticConfig

import img_handler
from img_handler import *

import denoise_predictions

def generate_predictions(model, model_dir = "../lira/lira1/src", img_archive_dir = "../lira/lira1/data/greyscales.h5", predictions_archive_dir = "../lira/lira1/data/predictions.h5", classification_metadata_dir = "classification_metadata.pkl"):
    """
    Arguments:
        model: String containing the filename of where our model is stored, to be used for classifying images and obtaining predictions
        model_dir: Filepath of where the code for the model is stored, and where it was trained. Will be used with `model` to obtain where the model is now located 
        img_archive_dir: a string filepath of the .h5 file where the images / greyscales are stored.
        predictions_archive_dir: a string filepath of the .h5 file where the model's predictions on the images/greyscales will be stored.
        classification_metadata_dir: a string filepath of the .pkl file where the model's classification strings and color key for each classification will be stored.

    Returns:
        Goes through each image, divides them into smaller subsections so as not to classify the entire image at once,
        Then goes through the subsections of our image, and divides into our sub_hxsub_w subsections, 
        then classifies each of these using our model stored in the model and model_dir filepaths.
        Then, it stores the predictions into a matrix of integers, or concatenates them onto the pre-existing predictions from previous subsections.
        Once completed with all subsections, these predictions are combined to get one 2d matrix of predictions, which is written to `predictions_archive_dir`.

        Has no return value.
    """

    """
    This is untested with other sizes of subsections.
    """
    sub_h = 80
    sub_w = 145

    """
    Mini batch size, arbitrarily chosen to be 100 because we have enough memory to handle it efficiently
    """
    mb_n = 100

    """
    Epochs, the number of iterations to run our denoising algorithm on each full predictions matrix                                                                                                                                      
    """
    epochs = 2

    """
    Our factors to resize our image by, or divide it into subsections.

    Set this to None to have a dynamic divide factor.
        the threshold is only relevant if it is None.

    Same goes for resize factor.
    """
    dynamic_img_divide_factor = True
    img_divide_factor = None

    dynamic_resize_factor = True
    resize_factor = None

    """
    Enable this if you want to see how long it took to classify each image
        *cough* if you want to show off *cough*
    """
    print_times = False

    """
    Classifications to give to each classification index
    Unfortunately, we need to assign these colors specific to classification, so we can't use the metadata from our samples.h5 archive
    """
    classifications = ["Healthy Tissue", "Type I - Caseum", "Type II", "Empty Slide", "Type III", "Type I - Rim", "Unknown/Other"]

    """
    BGR Colors to give to each classification index
              Pink,          Red,         Green,       Light Grey,      Yellow,        Blue         Purple
    """
    colors = [(255, 0, 255), (0, 0, 255), (0, 255, 0), (200, 200, 200), (0, 255, 255), (255, 0, 0), (244,66,143)]

    """
    Write our classification - color matchup metadata for future use
    """
    f = open(classification_metadata_dir, "w")
    pickle.dump(([classifications, colors]), f)

    """
    Open our saved model
    """
    classifier = StaticConfig(model, model_dir)

    """
    We open our image file, where each image is stored as a dataset with a key of it's index (e.g. '0', '1', ...)
    We also open our predictions file, where we will be writing our predictions in the same manner of our image file,
        so that they have a string index according to the image they came from.
    """
    with h5py.File(img_archive_dir, "r") as img_hf:
        with h5py.File(predictions_archive_dir, "w") as predictions_hf:
            """
            Get image number for iteration
            """
            img_n = len(img_hf.keys())

            """
            Start looping through images
            """
            for img_i in range(img_n):
                """
                Start our timer for this image
                """
                start_time = time.time()

                """
                Get our image, and pad it with necessary zeros so that we never have partial edge problems with the far edges
                """
                img = np.array(img_hf.get(str(img_i)))
                img = pad_img(img.shape[0], img.shape[1], sub_h, sub_w, img)

                """
                Get these for easy reference later, now that our image's dimensions aren't changing
                """
                img_h = img.shape[0]
                img_w = img.shape[1]

                """
                Get our img_divide_factor and resize_factor variables from the dimensions of our image
                """
                if dynamic_img_divide_factor:
                    img_divide_factor = get_relative_factor(img_h, img_divide_factor)
                if dynamic_resize_factor:
                    resize_factor = float(get_relative_factor(img_h, resize_factor))
                
                """
                In order to handle everything easily and correctly, we do the following:
                    Each subsection of our image we get an overlay_predictions matrix of predictions, 
                        which we either insert into the correct row, or concatenate onto the row's pre-existing values
                """
                predictions = [np.array([]) for i in range(img_divide_factor)]

                """
                Here we start looping through rows and columns in our image, 
                and divide our main image into smaller images to handle one at a time, and save memory.
                """
                img_sub_i = 0

                """
                Since this is interacting with a file which has its own progress indicator,
                    we write some blank space to clear the screen of any previous text before writing any of our progress indicator
                """
                sys.stdout.write("\r                                       ")

                for row_i in range(img_divide_factor):
                    for col_i in range(img_divide_factor):
                        sys.stdout.write("\rIMAGE %i, SUBSECTION %i" % (img_i, img_sub_i))
                        sys.stdout.flush()
                            
                        """
                        So we keep track of where we left off with our last prediction.
                        """
                        overlay_prediction_i = 0

                        """
                        Get the next sub-image of our main image
                        """
                        sub_img = get_next_subsection(row_i, col_i, img_h, img_w, sub_h, sub_w, img, img_divide_factor)
                        sub_img_h = sub_img.shape[0]
                        sub_img_w = sub_img.shape[1]

                        """
                        Generate our overlay using the shape of our sub_img, resized down by our final resize factor so as to save memory
                        """
                        overlay = np.zeros(shape=(int(sub_img_h//resize_factor), int(sub_img_w//resize_factor), 3))

                        """
                        Generate vector to store predictions as we loop through our subsections, which we can later reshape to a matrix.
                        """
                        overlay_predictions = np.zeros(((sub_img_h//sub_h)*(sub_img_w//sub_w)))

                        """
                        From our sub_img, get a matrix of subsections in this sub_img.
                        """
                        subs = get_subsections(sub_h, sub_w, sub_img)

                        """
                        Convert this matrix of subsections to a vector of subsections, with each entry being a subsection.
                            This way, we can easily loop through them.
                        """
                        subs = np.reshape(subs, (-1, sub_h, sub_w, 1))

                        """
                        Loop through vector of subsections with step mb_n
                        """
                        for sub_i in xrange(0, len(subs), mb_n):

                            """
                            Get our batch by referencing the right location in our subs with sub_i and mb_n
                            Note: This does get any extra samples, even if len(subs) % mb_n != 0
                            """
                            batch = subs[sub_i:sub_i+mb_n]

                            """
                            Then, we classify the new batch of examples and store in our temporary overlay_predictions array
                            """
                            overlay_predictions[overlay_prediction_i:overlay_prediction_i+batch.shape[0]] = classifier.classify(batch)
                            overlay_prediction_i += batch.shape[0]
                            
                        """
                        Convert our predictions for this subsection into a matrix so we can then concatenate it easily into our final predictions matrix.
                        """
                        overlay_predictions = np.reshape(overlay_predictions, (sub_img_h//sub_h, sub_img_w//sub_w))

                        """
                        Move our overlay_predictions matrix into our final predictions matrix, in the correct row according to row_i.
                            If this is the first column in a row:
                                Insert into row_i
                            If this is not, concatenate onto the correct row.
                        """
                        if col_i == 0:
                            predictions[row_i] = overlay_predictions
                        else:
                            predictions[row_i] = get_concatenated_row((predictions[row_i], overlay_predictions))

                        """
                        Increment total subsection number for display
                        """
                        img_sub_i +=1

                """
                Now that our entire image is done and our rows of concatenated predictions are ready,
                    we combine all the rows into a final matrix by concatenating into a column.
                """
                predictions = get_concatenated_col(predictions)

                """
                Now that all the predictions are together in one matrix, we can properly "view" them all, 
                    and use them with our denoisers.
                We then denoise our predictions using Markov Random Fields.
                """
                predictions = denoise_predictions.denoise_predictions(predictions, len(classifications), epochs)

                """
                Then we store it in our dataset
                """
                predictions_hf.create_dataset(str(img_i), data=predictions)

                """
                Print how long this took, if you want to show off.
                """
                end_time = time.time() - start_time
                if print_times:
                    print "Took %f seconds (%f minutes) to execute on image %i." % (end_time, end_time/60.0, img_i)