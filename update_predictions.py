"""
Meta file to make use of the major stages of LIRA in order to do:
    1. Raw Greyscales -> Greyscale archive (get_greyscales.py)
    2. Sample archive -> New trained model (experiment_config.py)
    3. Trained model & Greyscale archive -> Predictions Archive (generate_predictions.py)
    4. Predictions Archive & Greyscale Archive -> Jpg predictions per image per subsection (generate_display_results.py)
    5. Jpg predictions per image per subsection -> Jpg predictions per image (concatenate_results.py)

We have to set the directories again in the arguments because of where this file is positioned. When we have "../" something in one of our files for the directory, it is relative to the parent file calling that function. When that function is here, i.e. not in the normal place, it messes up stuff sometimes.

So use this when you want to update the end predictions, usually will be used once more data is available for the model.
    Use wisely, may take days to complete and could cause problems if interrupted. 
    Uses a lot of processing power for nearly all stages.
    You have been warned.
Good luck, have fun!

-Blake Edwards / Dark Element
"""

import sys

sys.path.append("lira/lira2/src")

import get_greyscales
import get_archive
import lira2_pre_transfer_learning
#import lira2_pre_transfer_learning_rgb

sys.path.append("lira_static")

import generate_predictions
import generate_display_results
import concatenate_results

def main(model_title):
    """
    Get filename of nn from title
    """
    model = model_title.lower().replace(" ", "_")
    
    """
    From our test_slides dir, generate new greyscales.h5 file for later
        (If we want to, and there isn't a massive amount of greyscales we want to avoid)
    """
    print "Getting Greyscales Archive..."
    #get_greyscales.load_greyscales("lira/lira1/data/test_slides", "lira/lira1/data/greyscales.h5")
    get_archive.create_archive("lira/lira1/data/test_slides", "lira/lira1/data/images.h5", rgb=True)

    """
    From our samples.h5 file, train our model and save in saved_networks/`nn`
    """
    print "Training Model..."
    #lira2_pre_transfer_learning.train_model(model, model_dir="lira/lira2/saved_networks", archive_dir="lira/lira2/data/augmented_samples.h5")
    #lira2_pre_transfer_learning_rgb.train_model(model, model_dir="lira/lira2/saved_networks", archive_dir="lira/lira2/data/augmented_samples.h5")


    """
    From our saved model and greyscales, generate new predictions.h5 file
    """
    print "Generating Predictions..."
    #generate_predictions.generate_predictions(model, model_dir = "lira/lira2/saved_networks", img_archive_dir = "lira/lira1/data/greyscales.h5", predictions_archive_dir = "lira/lira1/data/predictions.h5", classification_metadata_dir = "lira_static/classification_metadata.pkl")

    """
    From our new predictions.h5 and greyscales, generate human accessible images for viewing.
    """
    print "Generating Display Results..."
    #generate_display_results.generate_display_results(img_archive_dir = "lira/lira1/data/greyscales.h5", predictions_archive_dir = "lira/lira1/data/predictions.h5", classification_metadata_dir = "lira_static/classification_metadata.pkl", results_dir = "lira_static/results", neighbor_weight=0.8, epochs=0)

    """
    Concatenate results of generating display results, for showing off and/or debugging
    """
    print "Concatenating Results..."
    #concatenate_results.concatenate_results("lira_static/results/", "lira_static/concatenated_results/", classification_metadata_dir="lira_static/classification_metadata.pkl")
    
    """
    At this point we have all we need to open LIRA live again when we want to, so we are done!
    """
    print "Completed! -DE"

main("LIRA MK2 RGB dataset tests")
