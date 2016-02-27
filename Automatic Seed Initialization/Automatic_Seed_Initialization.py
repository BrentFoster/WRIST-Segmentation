


# Roughly segment the hand boundary (use automatic thresholding in SimpleITK)
# Could either hard code the thresholds based on VIBE or use a ITK method

# Use ICP to register the hand surface to the hand model

# Apply the resulting transformation to a set of points in the hand model
# One point for each bone

# Could also do some logic to test whether the seed location is the correct intensity
# Similar to Mansoor TMI paper for the lung segmentation seed location

# Run the carpal bone segmentation code

# Check for leakage (similar to Mansoor TMI paper) 

# If leakage is detected, apply spectral clustering to remove leakage areas