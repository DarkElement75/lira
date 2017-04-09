"""
This is our script to denoise (remove noise from) predictions generated by our classifier on images.
This is very useful when we have occasional mistaken classifications among many correct classifications, 
    as this will correct many such mistakes.

Further documentation found in each function.

-Blake Edwards / Dark Element
"""
import sys
import numpy as np

def denoise_predictions(src, class_n, epochs):
    """
    Arguments:
        src: np array of shape (h, w), the source image.
        class_n: int number of classes / classifications we will find in our src img.
        epochs: int number of denoising iterations to put our src image through.

    Returns
        For each pixel in our src image, 
            get the nearest neighbor pixels,
            get the cost of each class at this location with our cost function,
            then place the class with the lowest cost at the mirrored location in our destination image.
        Then repeat this process `epochs` number of times
    """
    h, w = src.shape

    costs = np.zeros((class_n))

    """
    Since this is interacting with a file which has its own progress indicator,
        we write some blank space to clear the screen of any previous text before writing any of our progress indicator
    """
    sys.stdout.write("\r                                       ")

    for epoch in range(epochs):
        """
        Each loop, reset our destination image, which will contain the new denoised image.
        """
        dst = np.zeros_like(src)
        sys.stdout.write("\rDenoising Image... %i%%"%(int(float(epoch)/epochs*100)))
        sys.stdout.flush()
        for i in range(h):
            for j in range(w):

                """
                Get indices of neighbors
                """
                neighbors=get_neighbors(i,j,h,w)
                
                """
                Get cost of each class for this pixel in our src img
                """
                for class_i in range(class_n):
                    costs[class_i] = cost(class_i,src[i,j],src,neighbors)

                """
                Assign dst pixel to class with lowest cost.
                """
                dst[i,j] = np.argmin(costs)
        """
        Set src equal to dst, so that we can run this again on the result of the previous loop,
            and continue denoising the image for `epochs` times.
        """
        src = dst
    return dst


def kronecker_delta(a,b):
        """
        Arguments:
            a,b: Two np arrays of the same shape. 

        Returns:
            An integer representation of performing ~(a-b)
            
            The Kronecker Delta function is really useful, but there isn't an actual method in many libraries.
            Fortunately, it's pretty much just ~(a-b), since we want the following behavior:
                kronecker_delta(a,b) = 1 if a == b
                kronecker_delta(a,b) = 0 if a != b
            So we do this, then return the integer representation of our logical op.
            Since I use numpy it holds for scalars and also vectors/matrices.
        """
        return np.logical_not(a-b).astype(int)

def get_neighbors(i,j,h,w):
    """
    Arguments:
        i,j: indices in our image matrix of size h,w
        h,w: size/dims of our image matrix

    Returns:
        neighbors: A list containing the index pairs of each of the neighbors of (i,j).
            For example, if i=0 and j=0, this would return [(0,1), (1,0), (1,1)]
        
            We do this by getting all adjacent neighbors, vertically, diagonally, and horizontally.
            We handle our edge cases by getting all 8 of these neighbors, then looping backwards through the list
                and removing those that aren't inside the bounds of our image.
    """
    neighbors=[(i-1, j-1), (i-1, j), (i-1, j+1), (i, j-1), (i, j+1), (i+1, j-1), (i+1, j), (i+1, j+1)]
    for neighbor_i in range(len(neighbors)-1, -1, -1):#Iterate from len-1 to 0
        sample_i, sample_j = neighbors[neighbor_i]
        if sample_i < 0 or sample_i > h-1 or sample_j < 0 or sample_j > w-1:
            del neighbors[neighbor_i]
    return neighbors

def cost(dst_val,src_val,src,neighbors):
    """
    Arguments:
        dst_val: Possible/Candidate value for the destination pixel. 0 <= dst_val < class_n
        src_val: The value of the source pixel. 0 <= src_val < class_n
        src: np array of shape (h, w), the source image. Used for referencing our neighbor indices
        neighbors: Our neighbor indices of our src pixel. See get_neighbors.

    Returns:
        The cost of placing dst_val as the source pixel's src_val, given src_val and neighbors of src_val.
        The lower the cost, the better a candidate value dst_val is. 
        Gets the values of our neighbors, then does the cost function 
            -kron_delta(dst_val, src_val) + beta*sum(kron_delta(dst_val, neighbor_vals))
        Where beta is a parameter we choose to weigh how much we care about the neighbor values.
        This cost function puts weight on the neighbor values, but also puts importance on the source values so we don't disregard them.
            With this, we get a smoothed image that still looks like the original.
        The cost function also returns lower values the more values that a pixel has in common with it's neighbors, 
            so that a pixel that is completely different has a higher cost, and one that is very similar has a lower cost.
        With these two desirable traits, we have our cost function. We return the cost.
    """
    """
    The values of the neighbor indices of our src pixel. We get these as a vector to speed up the cost computation.
    """
    neighbor_vals = np.array([src[neighbor] for neighbor in neighbors])

    """
    Compute our cost function as follows, using our neighbor value vector to compute the neighbor kronecker deltas simultaneously.
    """
    return -(1 * kronecker_delta(dst_val,src_val) + 10 * np.sum(kronecker_delta(dst_val,neighbor_vals)))

