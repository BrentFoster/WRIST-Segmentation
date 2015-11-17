import DICE

# '/Users/Brent/Google Drive/Research/Wrist MRI/Ground Truth/Volunteer2_Segmentation.hdr', 
dice_testing = DICE.DICE()

dice_testing.Execute(\
	'/Users/Brent/Desktop/Segmentations/Volunteer2_GroundTruth.hdr', \
	'/Users/Brent/Desktop/Segmentations/Volunteer2_VIBE_segmentation.hdr')