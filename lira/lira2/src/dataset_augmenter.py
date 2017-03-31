"""

Quick script to generate an augmented_samples.h5 file of augmented samples.
    Using live_samples.h5 and transformation_handler.py, 
        it creates an augmented_samples.h5 file by applying an arbitrary number of randomly generated
        affine transformation matrices, and also saves these matrices in a transformation_matrices.pkl file.

    Augmenting the original training data is a common practice used to help train neural networks that are
        more robust to changes in their input, so that they can learn to recognize the same sample if it's
        rotated, reflected, and so on.
"""
import numpy as np
import cv2
import h5py, pickle

import transformation_handler
from transformation_handler import *

import dataset_handler
from dataset_handler import *


def balance_dataset(x, y, class_n):
    """
    Arguments:
        x, y: Our dataset, x is input data and y is output data. Both are np arrays.
        class_n: Integer number of classes we have for our model.

    Returns:
        Use this if your dataset is very biased, e.g. 95% one classification, 5% another classification.
        We first shuffle the dataset, 
        Then balance it by removing data from all classifications but the classification with the smallest number of labels,
        so that all classifications have the same number at the end.
    """
    unison_shuffle(x, y)

    """
    Array for our numbers of each class's labeled samples, we assign accordingly
    """
    class_samples = np.zeros((class_n))
    for class_i in range(class_n):
        class_samples[class_i] = np.sum(y==class_i)

    """
    We then get the minority class number
    """
    class_sample_minority = np.min(class_samples)

    """
    Then we get a zeroed array to keep track of each class as we add it to our balanced dataset
    """
    class_sample_incrementer = np.zeros_like(class_samples)

    """
    We then get our dimensions accordingly, and initialise each to zeros
    """
    balanced_x_dims = [int(class_sample_minority*class_n)]
    balanced_x_dims.extend(x.shape[1:])
    balanced_x = np.zeros((balanced_x_dims))
    balanced_y = np.zeros((int(class_sample_minority*class_n)))

    """
    We then loop through, making sure to only add each class class_sample_minority times,
        and no more.
    """
    balanced_i = 0
    for sample_i, sample in enumerate(x):
        if class_sample_incrementer[y[sample_i]] < class_sample_minority:
            class_sample_incrementer[y[sample_i]]+=1
            balanced_x[balanced_i], balanced_y[balanced_i] = sample, y[sample_i]
            balanced_i += 1
    """
    We then return our new dataset
    """
    return balanced_x, balanced_y

def generate_augmented_data(archive_dir, augmented_archive_dir, metadata_dir, class_n, h=80, w=145, sigma=0.1, random_transformation_n=0, border_value=240, static_transformations=True):
    """
    Arguments:
        archive_dir: String where .h5 file is stored containing model's data.
        augmented_archive_dir: String where .h5 file will be stored containing model's augmented data.
        metadata_dir: String where .pkl file will be stored containing transformation matrices after we augment our data
        class_n: Integer number of classes we have for our model.
        h, w: Height and width of each of our samples. Defaults to 80x145 for our LIRA project.
        sigma: Variance parameter to control how large our applied transformations are. Defaults to 0.1
        random_transformation_n: Number of random transformations to generate. Defaults to 0
        border_value: Value to pad missing parts of our image if we transform it off the viewport, 0-255
        static_transformations: Boolean to decide if we want to use our 5 preset transformations for augmentation or not.

    Returns:
        After opening our samples from archive_dir, and initialising and normalising our static transformations if enabled,
            the methods in transformation_handler.py are used for generating and applying our transformations.
        We then store our transformation matrices (static and generated) into our metadata_dir, 
        And store our augmented dataset into our augmented_archive_dir.

    """

    """
    """
    with h5py.File(archive_dir, "r") as hf:
        x = np.array(hf.get("x"))
        y = np.array(hf.get("y"))

    """
    """
    x, y = balance_dataset(x, y, class_n)

    """
    Since our samples are only 2 dimensional, 
        we get the h and w of each sample via the first, 
        and then we reshape so that we have images to properly transform.
    We first reshape our x by the h and w arguments passed in.
    """
    x = np.reshape(x, (-1, h, w))

    if static_transformations:
        """
        If enabled,
        Our preset static transformations are as follows:
            1. Rotate 90 Degrees
            2. Rotate 270 Degrees
            3. Reflect on X-axis
            4. Reflect on Y-axis
            5. Reflect on Origin (combination of X-axis and Y-axis reflections), or a 180-Degree Rotation
        """
        transformation_matrices = np.array(
                [
                    [[0., 1., 0.],
                     [-1., 0., 0.],
                     [0., 0., 1.]], 
                    
                    [[0., -1., 0.],
                     [1., 0., 0.],
                     [0., 0., 1.]],
                    
                    [[1., 0., 0.],
                     [0., -1., 0.],
                     [0., 0., 1.]], 
                    
                    [[-1., 0., 0.], 
                     [0., 1., 0.],
                     [0., 0., 1.]],
                    
                    [[-1., 0., 0.], 
                     [0., -1., 0.], 
                     [0., 0., 1.]]
                ]
             )

        """
        Initialize our normalization matrices.
            To illustrate why we do this, here is an example:
            For a 90-degree rotation:
                Originally:
                    This would normally be about the top-left corner of the image.
                    This is really not what we want, especially if we are combining transformations together.
                    We also by default lose the entire image, as it disappears from frame.
                    So, instead, we want to rotate around the center of the image.
                With Normalization:
                    By moving the image center to the top-left corner as the first transformation, 
                    we can then rotate in this way, so that we can easily apply transformations the 
                    human-understandable and human-manipulatable way.
                    So, we move top left corner so that it is the center, 
                        apply the transformation(s), 
                        and then move the center of the frame so that it is the center again.
                    We do this by dot'ing each of our transformation_matrices with these, 
                        since the composition of any affine transformations can be represented by the dot product
                        of the affine transformation matrices.
        """
        """
        Moves top left corner of frame to center of frame
        """
        top_left_to_center = np.array([[1., 0., .5*w], [0., 1., .5*h], [0.,0.,1.]])

        """
        Moves center of frame to top left corner of frame, the inverse of our previous transformation
        """
        center_to_top_left = np.array([[1., 0., -.5*w], [0., 1., -.5*h], [0.,0.,1.]])

        """
        Then loop through and apply our normalizations
        """
        for transformation_matrix_i, transformation_matrix in enumerate(transformation_matrices):
            transformation_matrices[transformation_matrix_i] = top_left_to_center.dot(transformation_matrix).dot(center_to_top_left)
    else:
        """
        If not enabled, we set our transformation_matrices so that they will be ignored in our augmenting functions in transformation_handler
        """
        transformation_matrices = []

    """
    Use the functions in our transformation_handler to handle our x and y parts of our dataset.
    """
    x, transformation_matrices = generate_2d_transformed_data(x, sigma, random_transformation_n, transformation_matrices, border_value)
    y = generate_transformed_references(y, len(transformation_matrices))

    """
    We are now done augmenting our dataset,
        We now save our transformation matrices to the metadata_dir,
    """
    with open(metadata_dir, "w") as f:
        pickle.dump(transformation_matrices, f)

            
    """
    And finally create our augmented archive and store our transformed x and transformed y there.
    """
    with h5py.File(augmented_archive_dir, "w") as hf:
        hf.create_dataset("x", data=x)
        hf.create_dataset("y", data=y)

generate_augmented_data("../data/live_samples.h5", "../data/augmented_samples.h5", "../data/transformation_matrices.pkl", 7, sigma=0.2, random_transformation_n=5)