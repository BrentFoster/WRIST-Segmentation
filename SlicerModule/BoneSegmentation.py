import SimpleITK as sitk
import numpy as np

import timeit

class BoneSeg(object):
    """Class of BoneSegmentation. REQUIRED: BoneSeg(MRI_Image,SeedPoint)"""
    def Execute(self, original_image, original_seedPoint, verbose=False, returnSitkImage=True, convertSeedPhyscialFlag=True):

        start_time = timeit.default_timer() 

        self.verbose = verbose # Optional argument to output text to terminal

        # Cast the original_image to UInt 16 just to be safe
        original_image = sitk.Cast(original_image, sitk.sitkUInt16)


        self.image = original_image
        self.original_image = original_image
        self.seedPoint = original_seedPoint
        self.original_seedPoint = original_seedPoint
        self.convertSeedPhyscialFlag = convertSeedPhyscialFlag
        self.returnSitkImage = returnSitkImage        

        # Convert images to type float 32 first
        try:
            self.image = sitk.Cast(self.image, sitk.sitkFloat32)
        except:
            # Convert from numpy array to a SimpleITK image type first then cast
            self.image = sitk.Cast(sitk.GetImageFromArray(self.image), sitk.sitkFloat32)
            self.original_image = self.image # original_image needs to be a SimpleITK image type for later

        # Define what the anatimical prior volume and bounding box is for each carpal bone
        self.DefineAnatomicPrior()

        if self.verbose == True:
            print(' ')
            print('\033[94m' + "Current Seed Point: "),
            print(self.seedPoint)
            print(' ')
            print('\033[94m' + "Rounding and converting to voxel domain: "), 

        # Convert the seed point to image coordinates (from physical) if needed and round
        self.RoundSeedPoint()

        if self.verbose == True:
            print(' ')
            print('\033[94m' + 'Estimating upper sigmoid threshold level')

        # Estimate the threshold level by image intensity statistics
        LowerThreshold = self.EstimateSigmoid()
        self.SetLevelSetLowerThreshold(LowerThreshold)

        # Crop the image so that it considers only a search space around the seed point
        # to speed up computation significantly!
        if self.verbose == True:
            print(' ')
            print('\033[94m' + 'Cropping image')
        self.CropImage()
        # sitk.Show(self.image, 'Post-cropping')

        if self.verbose == True:
            print(' ')
            print('\033[94m' + 'Applying Anisotropic Filter')
        self.apply_AnisotropicFilter()
        # sitk.Show(self.image, 'Post-Anisotropic')

        
        if self.verbose == True:
            elapsed = timeit.default_timer() - start_time
            print(' ')
            print("Elapsed Time (Preprocessing ):" + str(round(elapsed,3)))
    
        # Initilize the level set (only need to do this once)
        if self.verbose == True:
            print(' ')
            print('\033[94m' + 'Initilizing Level Set')
        self.InitilizeLevelSet()
        # sitk.Show(self.EdgePotentialMap, 'Edge Potential Map')

        if self.verbose == True:
            print(' ')
            print('\033[90m' + "Sigmoid shape detection level set by iteration...")
        self.SigmoidLevelSetIterations()
        
        if self.verbose == True:
            print(' ')
            print('\033[96m' + "Finished with seed point "),
            print(self.seedPoint)

        if self.verbose == True:
            print(' ')
            print('\033[93m' + "Running Leakage Check...")
        self.LeakageCheck()

        if self.verbose == True:
            print(' ')
            print('\033[93m' + "Filling Any Holes...")
        # Fill holes prior to uncropping image for much faster computation
        self.HoleFilling()

        # if self.verbose == True:
        #     print(' ')
        #     print('\033[93m' + "Smoothing Label...")
        # self.SmoothLabel()

        if self.verbose == True:
            print(' ')
            print('\033[93m' + "Changing Label Value...")
        self.ChangeLabelValue()

        if self.verbose == True:
            print(' ')
            print('\033[90m' + "Uncropping Image...")
        self.UnCropImage()

        if self.verbose == True:
            print(' ')
            print('\033[97m' + "Exporting Final Segmentation...")
            print(' ')

        if self.returnSitkImage == True:
            # Check the image type first
            self.segImg = sitk.Cast(self.segImg, original_image.GetPixelID())
            # Return a SimpleITK type image
            return  self.segImg 
        else:
            # Return a numpy array image (needed for using multiple logical cores)
            self.segImg = sitk.Cast(self.segImg, sitk.sitkUInt8)
            npImg = sitk.GetArrayFromImage(self.segImg)

            return  npImg

    def ChangeLabelValue(self):
        BoneList = ['Trapezium', 'Trapezoid', 'Scaphoid', 'Capitate', 'Lunate', 'Hamate', 'Triquetrum', 'Pisiform']

        ndx = BoneList.index(self.current_bone)

        # Add one to the ndx because index starts at 0 instead of 1
        ndx = ndx + 1 

        npImg = sitk.GetArrayFromImage(self.segImg)

        print('Unique of npImg is ' + str(np.unique(npImg)))

        npImg[npImg != 0] = ndx

        print('Unique of npImg is now ' + str(np.unique(npImg)))

        # Convert back to SimpleITK image type
        tempImg = sitk.Cast(sitk.GetImageFromArray(npImg), sitk.sitkUInt16)
        tempImg.CopyInformation(self.segImg)

        self.segImg = tempImg

        return self





    def SmoothLabel(self):
        # Smooth the segmentation label image to reduce high frequency artifacts on the boundary
        SmoothFilter = sitk.DiscreteGaussianImageFilter()

        SmoothFilter.SetVariance(0.01)

        self.segImg = SmoothFilter.Execute(self.segImg)

        return self

    def SetDefaultValues(self):
        # Set the default values of all the parameters here
        self.SetScalingFactor(1) #X,Y,Z
       
        self.SeedListFilename = "PointList.txt"
        self.SetMaxVolume(300000) #Pixel counts (TODO change to mm^3) 

        # Anisotropic Diffusion Filter
        self.SetAnisotropicIts(5)
        self.SetAnisotropicTimeStep(0.01)
        self.SetAnisotropicConductance(2)

        # Morphological Operators
        self.fillFilter.SetForegroundValue(1) 
        self.fillFilter.FullyConnectedOff() 
        self.SetBinaryMorphologicalRadius(1)

        # Shape Detection Filter
        self.SetShapeMaxRMSError(0.004)
        self.SetShapeMaxIterations(400)
        self.SetShapePropagationScale(4)
        self.SetShapeCurvatureScale(1)

        # Sigmoid Filter
        self.sigFilter.SetAlpha(0)
        self.sigFilter.SetBeta(120)
        self.sigFilter.SetOutputMinimum(0)
        self.sigFilter.SetOutputMaximum(255)

        # Search Space Window
        # self.SetSearchWindowSize(50)

        # Set current bone and patient gender group
        self.SetCurrentBone('Capitate')
        self.SetPatientGender('Unknown')

        # Set the relaxation on the prior anatomical knowledge contraint
        self.SetAnatomicalRelaxation(0.15)


    def DefineAnatomicPrior(self):
        # The prior anatomical knowledge on the bone volume and dimensions is addeded
        # from Crisco et al. Carpal Bone Size and Scaling in Men Versus Women. J Hand Surgery 2005

        if self.PatientGender == 'Unknown':
            self.Prior_Volumes = {
            'Scaphoid-vol':[2390,673], 'Scaphoid-x':[27, 3.1], 'Scaphoid-y':[16.5,1.8], 'Scaphoid-z':[13.1,1.2], 
            'Lunate-vol':[1810,578], 'Lunate-x':[19.4, 2.3], 'Lunate-y':[18.5,2.2], 'Lunate-z':[13.2,1.7], 
            'Triquetrum-vol':[1341,331], 'Triquetrum-x':[19.7,2], 'Triquetrum-y':[18.5,2.2], 'Triquetrum-z':[13.2,1.7], 
            'Pisiform-vol':[712,219], 'Pisiform-x':[14.7,1.7], 'Pisiform-y':[11.5,1.4], 'Pisiform-z':[9.5,1.1], 
            'Trapezium-vol':[1970,576], 'Trapezium-x':[23.6,2.5], 'Trapezium-y':[16.6,1.8], 'Trapezium-z':[14.6,2.2], 
            'Trapezoid-vol':[1258,321], 'Trapezoid-x':[19.3,1.8], 'Trapezoid-y':[114.4,1.5], 'Trapezoid-z':[11.7,1.0], 
            'Capitate-vol':[3123,743], 'Capitate-x':[26.3,2.3], 'Capitate-y':[19.5,1.9], 'Capitate-z':[15,1.6],  
            'Hamate-vol':[2492,555], 'Hamate-x':[26.1,2.2], 'Hamate-y':[21.6,2], 'Hamate-z':[16,1.4]
            }
        elif self.PatientGender == 'Male':
            self.Prior_Volumes = {
            'Scaphoid-vol':[2903,461], 'Scaphoid-x':[29.3, 2.7], 'Scaphoid-y':[17.8,1.2], 'Scaphoid-z':[14.1,0.9], 
            'Lunate-vol':[2252,499], 'Lunate-x':[20.9,2.2], 'Lunate-y':[20.1,1.8], 'Lunate-z':[14.4,1.3], 
            'Triquetrum-vol':[1579,261], 'Triquetrum-x':[20.9,1.8], 'Triquetrum-y':[14.9,0.7], 'Triquetrum-z':[12.6,0.9], 
            'Pisiform-vol':[854,203], 'Pisiform-x':[15.7,1.4], 'Pisiform-y':[12.3,1.3], 'Pisiform-z':[10,1.2], 
            'Trapezium-vol':[2394,443], 'Trapezium-x':[25.4,1.8], 'Trapezium-y':[17.5,1.8], 'Trapezium-z':[16.1,1.8], 
            'Trapezoid-vol':[1497,237], 'Trapezoid-x':[20.6,1.4], 'Trapezoid-y':[15.5,0.8], 'Trapezoid-z':[12.3,0.7], 
            'Capitate-vol':[3700,563], 'Capitate-x':[28,1.8], 'Capitate-y':[20.8,1.7], 'Capitate-z':[16,1.6],  
            'Hamate-vol':[2940,378], 'Hamate-x':[27.5,1.9], 'Hamate-y':[23,1.8], 'Hamate-z':[16.9,1.2]
            }
        elif self.PatientGender == 'Female':
            self.Prior_Volumes = {
            'Scaphoid-vol':[1877,407], 'Scaphoid-x':[24.8,1.6], 'Scaphoid-y':[15.3,1.5], 'Scaphoid-z':[12.2,0.6], 
            'Lunate-vol':[1368,165], 'Lunate-x':[18,1.1], 'Lunate-y':[16.9,0.8], 'Lunate-z':[11.9,0.8], 
            'Triquetrum-vol':[1103,193], 'Triquetrum-x':[18.5,1.3], 'Triquetrum-y':[13.3,0.6], 'Triquetrum-z':[10.8,0.7], 
            'Pisiform-vol':[569,121], 'Pisiform-x':[13.7,1.4], 'Pisiform-y':[10.7,1], 'Pisiform-z':[8.9,0.7], 
            'Trapezium-vol':[1547,328], 'Trapezium-x':[21.8,1.8], 'Trapezium-y':[15.8,1.5], 'Trapezium-z':[13.1,1.2], 
            'Trapezoid-vol':[1020,191], 'Trapezoid-x':[18,0.9], 'Trapezoid-y':[13.3,1.2], 'Trapezoid-z':[11.1,0.8], 
            'Capitate-vol':[2547,344], 'Capitate-x':[24.6,1.1], 'Capitate-y':[18.2,1], 'Capitate-z':[13.9,0.8],  
            'Hamate-vol':[2045,264], 'Hamate-x':[24.7,1.4], 'Hamate-y':[20.1,0.8], 'Hamate-z':[15,0.9]
            }
        else:
            # Raise an erorr since 
            raise ValueError('Patient gender must be either "Male", "Female", or "Unknown". Value given was ' + self.PatientGender)


        # Allow some relaxation around the anatomical prior knowledge contraint
        # Calculate what the ranges should be for each measure using average and standard deviation and relaxation term
        self.lower_range_volume = (self.Prior_Volumes[self.current_bone + '-vol'][0] - self.Prior_Volumes[self.current_bone + '-vol'][1])*(1-self.AnatomicalRelaxation)
        self.upper_range_volume = (self.Prior_Volumes[self.current_bone + '-vol'][0] + self.Prior_Volumes[self.current_bone + '-vol'][1])*(1+self.AnatomicalRelaxation)

        self.lower_range_x = (self.Prior_Volumes[self.current_bone + '-x'][0] - self.Prior_Volumes[self.current_bone + '-x'][1])*(1-self.AnatomicalRelaxation)
        self.upper_range_x = (self.Prior_Volumes[self.current_bone + '-x'][0] + self.Prior_Volumes[self.current_bone + '-x'][1])*(1+self.AnatomicalRelaxation)

        self.lower_range_y = (self.Prior_Volumes[self.current_bone + '-y'][0] - self.Prior_Volumes[self.current_bone + '-y'][1])*(1-self.AnatomicalRelaxation)
        self.upper_range_y = (self.Prior_Volumes[self.current_bone + '-y'][0] + self.Prior_Volumes[self.current_bone + '-y'][1])*(1+self.AnatomicalRelaxation)

        self.lower_range_z = (self.Prior_Volumes[self.current_bone + '-z'][0] - self.Prior_Volumes[self.current_bone + '-z'][1])*(1-self.AnatomicalRelaxation)
        self.upper_range_z = (self.Prior_Volumes[self.current_bone + '-z'][0] + self.Prior_Volumes[self.current_bone + '-z'][1])*(1+self.AnatomicalRelaxation)

        # Use the bounding box ranges to create a suitable search window for the current particular carpal bone 
        self.searchWindow = np.rint(np.asarray([self.upper_range_x, self.upper_range_y, self.upper_range_z]))

        # Make the search window larger since the seed location won't be exactly in the center of the bone
        self.searchWindow = np.rint(2*self.searchWindow)

        if self.verbose == True:
            print('\033[93m'  + 'Estimated Search Window is ' + str(self.searchWindow))
            print(' ')

        return self

    def ConnectedComponent(self):

        self.segImg = sitk.Cast(self.segImg, 1) #Can't be a 32 bit float
        # self.segImg.CopyInformation(segmentation)

        # Try to remove leakage areas by first eroding the binary and
        # get the labels that are still connected to the original seed location

        # self.segImg = self.erodeFilter.Execute(self.segImg, 0, 1, False)

        # self.segImg = self.connectedComponentFilter.Execute(self.segImg)

        # nda = sitk.GetArrayFromImage(self.segImg)
        # nda = np.asarray(nda)

        # # In numpy an array is indexed in the opposite order (z,y,x)
        # tempseedPoint = self.seedPoint[0]
        # val = nda[tempseedPoint[2]][tempseedPoint[1]][tempseedPoint[0]]

        # # Keep only the label that intersects with the seed point
        # nda[nda != val] = 0 
        # nda[nda != 0] = 1

        # self.segImg = sitk.GetImageFromArray(nda)

        # Undo the earlier erode filter by dilating by same radius
        # self.dilateFilter.SetKernelRadius(3)
        # self.segImg = self.dilateFilter.Execute(self.segImg, 0, 1, False)

        self.segImg = self.fillFilter.Execute(self.segImg)

        # self.segImg = self.erodeFilter.Execute(self.segImg, 0, 1, False)

        

        return self

    def HoleFilling(self):
        # Cast to 16 bit (needed for the fill filter to work)
        self.segImg  = sitk.Cast(self.segImg, sitk.sitkUInt16)

        self.dilateFilter.SetKernelRadius(1)
        self.segImg = self.dilateFilter.Execute(self.segImg, 0, 1, False)
        self.segImg = self.fillFilter.Execute(self.segImg)
        self.segImg = self.erodeFilter.Execute(self.segImg, 0, 1, False)

        return self

    def LeakageCheck(self):
        # Check the image type of self.segImg and image are the same (for Python 3.3 and 3.4)
        # self.segImg = sitk.Cast(self.segImg, segmentation.GetPixelID()) #Can't be a 32 bit float
        # self.segImg.CopyInformation(segmentation)

        # Label Statistics Image Filter can't be 32-bit or 64-bit float
        self.segImg = sitk.Cast(self.segImg, sitk.sitkUInt16)

        # Fill any segmentation holes first
        start_time = timeit.default_timer() 
        self.HoleFilling()
        elapsed = timeit.default_timer() - start_time

        if self.verbose == True:
            print(' ')
            print('FILLING elapsed : ' + str(round(elapsed,3)))
            print(' ')
               
        nda = sitk.GetArrayFromImage(self.segImg)
        nda = np.asarray(nda)

        pix_dims = np.asarray(self.original_image.GetSpacing())

        BoundingBoxFilter = sitk.LabelStatisticsImageFilter()

        # BoundingBoxFilter.Execute(self.original_image, self.segImg)
        # self.segImg = sitk.Cast(self.segImg, self.original_image.GetPixelID()) # Can't be 32-bit float
        BoundingBoxFilter.Execute(self.segImg, self.segImg)

        label = 1 # Only considering one bone in the segmentaiton for now

        BoundingBox = BoundingBoxFilter.GetBoundingBox(label)
        # Need to be consistent with how Crisco 2005 defines their bounding box
        z_size = BoundingBox[1] - BoundingBox[0] 
        x_size = BoundingBox[3] - BoundingBox[2]
        y_size = BoundingBox[5] - BoundingBox[4]

        # Convert to physical units (mm)
        x_size = x_size*pix_dims[0]
        y_size = y_size*pix_dims[1]
        z_size = z_size*pix_dims[2]

        volume = np.prod(pix_dims)*BoundingBoxFilter.GetCount(label)

        # Round to the nearest integer
        x_size = np.around(x_size,1)
        y_size = np.around(y_size,1)
        z_size = np.around(z_size,1)
        volume = np.rint(volume)

        # Create a flag to determine whether the test failed
        # convergence_flag = 0 (passed), 1 (too large), 2 (too small)
        convergence_flag = 0

        if self.verbose == True:
            print('x_size = ' + str(x_size))
            print('y_size = ' + str(y_size))
            print('z_size = ' + str(z_size))
            print('volume = ' + str(volume))

        if (volume > self.lower_range_volume) and (volume < self.upper_range_volume):
            if self.verbose == True:
                print('\033[97m' + "Passed with volume " + str(volume))                
        else:
            # Determine whether the segmentation was too large or too small
            if volume > self.upper_range_volume:
                convergence_flag = 1
            elif volume < self.lower_range_volume:
                convergence_flag = 2

            if self.verbose == True:
                print('\033[96m' + "Failed with volume " + str(volume))
                print('Expected range ' + str(self.lower_range_volume) + ' to ' + str(self.upper_range_volume))
      
        if (x_size > self.lower_range_x) and (x_size < self.upper_range_x):             
            if self.verbose == True:
                print('\033[97m' + "Passed x-bounding box " + str(x_size))
        else:
            if self.verbose == True:
             print('\033[96m' + "Failed x-bounding box " + str(x_size))

        if (y_size > self.lower_range_y) and (y_size < self.upper_range_y):            
            if self.verbose == True:
                print('\033[97m' + "Passed y-bounding box " + str(y_size))
        else:
            if self.verbose == True:
                print('\033[96m' + "Failed y-bounding box " + str(y_size))

        if (z_size > self.lower_range_z) and (z_size < self.upper_range_z):
            if self.verbose == True:
                print('\033[97m' + "Passed z-bounding box " + str(z_size))
        else:
            if self.verbose == True:
                print('\033[96m' + "Failed z-bounding box " + str(z_size))
                print('Expected range ' + str(self.lower_range_z) + ' to ' + str(self.upper_range_z))


        if convergence_flag == 1:
            # Segmentation was determined to be much too large. Lower number of iterations
            print(' ')
            print(' ')
            print('REDOING SEGMENTATION')

            # Shape Detection Filter
            print('Current iterations = ' + str(self.GetShapeMaxIterations()))
            
            # Use 50% less iterations as currently used (since too large of a segmentation)
            # Use a random percent less iterations (between 10% and 60%) 
            # as are currently used (since too small of a segmentation)
            
            MaxIts = np.rint(self.GetShapeMaxIterations()*(1 - (np.random.rand(1)+0.10)/2))
            print('Decreasing iterations to = ' + str(MaxIts))
            self.SetShapeMaxIterations(MaxIts)

            if MaxIts < 10:
                raise Warning('Max Iterations of ' + str(MaxIts) + ' is too low! Stopping now.')
                return self

            # Don't need to redo the pre-processing steps
            start_time = timeit.default_timer() 
            self.SigmoidLevelSetIterations()
            elapsed = timeit.default_timer() - start_time

            if self.verbose == True:
                print('\033[92m' + 'Elapsed Time (processedImage):' + str(round(elapsed,3)))

            # Redo the leakage check (basically iteratively)
            self.LeakageCheck()


        elif convergence_flag == 2:
            # Segmentation was determined to be much too small. Increase number of iterations
            print(' ')
            print(' ')
            print('REDOING SEGMENTATION')

            # Use a random percent more iterations (between 20% and 200%) 
            # as are currently used (since too small of a segmentation)
            MaxIts = np.rint(self.GetShapeMaxIterations()*(1 + (np.random.rand(1)+0.10)/2))

            print('Increasing iterations to = ' + str(MaxIts[0]))
            self.SetShapeMaxIterations(MaxIts)

            if MaxIts > 3000:
                raise Warning('Max Iterations of ' + str(MaxIts) + ' is too high! Stopping now.')
                return self

            # Don't need to redo the pre-processing steps
            start_time = timeit.default_timer() 
            self.SigmoidLevelSetIterations()
            elapsed = timeit.default_timer() - start_time
            
            if self.verbose == True:
                print('\033[92m' + 'Elapsed Time (processedImage):' + str(round(elapsed,3)))
           
           # Redo the leakage check (basically iteratively)
            self.LeakageCheck()

        return self

    def RoundSeedPoint(self):
        tempseedPoint = np.array(self.seedPoint).astype(int) #Just to be safe make it int again
        tempseedPoint = tempseedPoint[0]

        if self.convertSeedPhyscialFlag == True:
            # Convert from physical to image domain
            tempFloat = [float(tempseedPoint[0]), float(tempseedPoint[1]), float(tempseedPoint[2])]

            # Convert from physical units to voxel coordinates
            # tempVoxelCoordinates = self.image.TransformPhysicalPointToContinuousIndex(tempFloat)
            # self.seedPoint = tempVoxelCoordinates
            self.seedPoint = tempFloat

            # Need to round the seedPoints because integers are required for indexing
            ScalingFactor = np.array(self.ScalingFactor)
            tempseedPoint = np.array(self.seedPoint).astype(int)
            tempseedPoint = abs(tempseedPoint)
            tempseedPoint = tempseedPoint/ScalingFactor # Scale the points down as well
            tempseedPoint = tempseedPoint.round() # Need to round it again for Python 3.3

        self.seedPoint = [tempseedPoint]
        self.original_seedPoint = [tempseedPoint]

        return self

    def UnCropImage(self):
        ' Indexing to put the segmentation of the cropped image back into the original MRI '

        # Need the original seed point to know where the cropped volume is in the original image
        cropNdxOne = np.asarray(self.original_seedPoint[0]) - self.searchWindow
        cropNdxTwo = np.asarray(self.original_seedPoint[0]) + self.searchWindow

        original_image_nda = sitk.GetArrayFromImage(self.original_image)
        original_image_nda = np.asarray(original_image_nda)

        seg_img_nda = sitk.GetArrayFromImage(self.segImg)
        seg_img_nda = np.asarray(seg_img_nda)

        original_image_nda = original_image_nda*0;

        original_image_nda[cropNdxOne[2]:cropNdxTwo[2],
                        cropNdxOne[1]:cropNdxTwo[1],
                        cropNdxOne[0]:cropNdxTwo[0]] = seg_img_nda

        # Convert back to SimpleITK image type
        self.segImg = sitk.Cast(sitk.GetImageFromArray(original_image_nda), sitk.sitkUInt16)
        self.segImg.CopyInformation(self.original_image)

        return self

    def CropImage(self):
        ' Crop the input_image around the initial seed point to speed up computation '
        cropFilter = sitk.CropImageFilter()
        addFilter  = sitk.AddImageFilter()

        im_size = np.asarray(self.image.GetSize())

        # Check to make sure the search window size won't go outside of the image dimensions
        for i in range(0,3):
            if self.searchWindow[i] > self.seedPoint[0][i]:
                self.searchWindow[i] = self.seedPoint[0][i]
            if self.searchWindow[i] > im_size[i] - self.seedPoint[0][i]:
                self.searchWindow[i] = im_size[i] - self.seedPoint[0][i]

        cfLowerBound = np.asarray(np.asarray(self.seedPoint[0]) - self.searchWindow, dtype=np.uint32)
        cfUpperBound = np.asarray(im_size - np.asarray(self.seedPoint[0]) - self.searchWindow, dtype=np.uint32)
        
        # These need to be changed to a list using numpy .tolist() for some reason
        cfLowerBound = cfLowerBound.tolist()
        cfUpperBound = cfUpperBound.tolist()
        
        cropFilter.SetLowerBoundaryCropSize(cfLowerBound)
        cropFilter.SetUpperBoundaryCropSize(cfUpperBound)

        self.image = cropFilter.Execute(self.image)

        # The seed point is now in the middle of the search window
        self.seedPoint = [np.asarray(self.searchWindow)]

        return self

    def InitilizeLevelSet(self):
        # Pre-processing for the level-set (e.g. create the edge map) only need to do once
        
        # self.sigFilter.SetBeta(120)
        # self.sigFilter.SetAlpha(0)

        processedImage = self.sigFilter.Execute(self.image) 
        processedImage  = sitk.Cast(processedImage, sitk.sitkUInt16)

        edgePotentialFilter = sitk.EdgePotentialImageFilter()
        gradientFilter = sitk.GradientImageFilter()

        gradImage = gradientFilter.Execute(processedImage)

        processedImage = edgePotentialFilter.Execute(gradImage)

        ''' Create Seed Image '''
        if self.verbose == True:
            print('Starting ShapeDetectionLevelSetImageFilter')
            start_time = timeit.default_timer() 

        # Create the seed image
        nda = sitk.GetArrayFromImage(self.image)
        nda = np.asarray(nda)
        nda = nda*0
        seedPoint = self.seedPoint[0]

        # In numpy an array is indexed in the opposite order (z,y,x)
        nda[seedPoint[2]][seedPoint[1]][seedPoint[0]] = 1

        self.segImg = sitk.Cast(sitk.GetImageFromArray(nda), sitk.sitkUInt16)
        self.segImg.CopyInformation(self.image)

        self.segImg = sitk.BinaryDilate(self.segImg, 3)

        ''' Segmentation '''
        # Signed distance function using the initial seed point (segImg)
        init_ls = sitk.SignedMaurerDistanceMap(self.segImg, insideIsPositive=True, useImageSpacing=True)
        self.init_ls = sitk.Cast(init_ls, sitk.sitkFloat32)

        self.EdgePotentialMap = sitk.Cast(processedImage, sitk.sitkFloat32)

    def SigmoidLevelSetIterations(self):
        ' Run the Shape Detection Level Set Segmentation Method'

        # sitk.Show(self.init_ls, 'self.init_ls')
        # sitk.Show(self.EdgePotentialMap, 'self.EdgePotentialMap')

        self.segImg = self.shapeDetectionFilter.Execute(self.init_ls, self.EdgePotentialMap)
     
        if self.verbose == True:
            print('Done with ShapeDetectionLevelSetImageFilter!')

        self.segImg = self.SegToBinary(self.segImg)
        
        return self

    def __init__(self):
        self.ScalingFactor = []
        self.AnisotropicIts = []
        self.AnisotropicTimeStep = []
        self.AnisotropicConductance = []
        self.ConfidenceConnectedIts = []
        self.ConfidenceConnectedMultiplier = []
        self.ConfidenceConnectedRadius = []
        self.BinaryMorphologicalRadius = []
        self.MaxVolume = []
        self.SeedListFilename = [] 

        ## Initilize the ITK filters ##
        # Filters to down/up sample the image for faster computation
        self.shrinkFilter = sitk.ShrinkImageFilter()
        self.expandFilter = sitk.ExpandImageFilter()

        # Bias field correction
        self.BiasFilter = sitk.N4BiasFieldCorrectionImageFilter()

        # Filter to reduce noise while preserving edgdes
        self.anisotropicFilter = sitk.CurvatureAnisotropicDiffusionImageFilter()
        # Post-processing filters for fillinging holes and to attempt to remove any leakage areas
        self.dilateFilter = sitk.BinaryDilateImageFilter()
        self.erodeFilter = sitk.BinaryErodeImageFilter()
        self.fillFilter = sitk.BinaryFillholeImageFilter()  
        self.connectedComponentFilter = sitk.ScalarConnectedComponentImageFilter()
        self.laplacianFilter = sitk.LaplacianSegmentationLevelSetImageFilter()
        self.thresholdLevelSet = sitk.ThresholdSegmentationLevelSetImageFilter()

        # Initilize the SimpleITK Filters
        self.GradientMagnitudeFilter = sitk.GradientMagnitudeImageFilter()
        self.shapeDetectionFilter = sitk.ShapeDetectionLevelSetImageFilter()
        self.thresholdFilter = sitk.BinaryThresholdImageFilter()
        self.sigFilter = sitk.SigmoidImageFilter()

        # Set the deafult values 
        self.SetDefaultValues()

    def SetAnatomicalRelaxation(self, newRelaxation):
        self.AnatomicalRelaxation = newRelaxation
    def SetCurrentBone(self, newBone):
         self.current_bone = newBone

    def SetPatientGender(self, newGender):
        self.PatientGender= newGender

    def SetShapeMaxIterations(self, MaxIts):
        self.shapeDetectionFilter.SetNumberOfIterations(int(MaxIts))

    def GetShapeMaxIterations(self):
        MaxIts = self.shapeDetectionFilter.GetNumberOfIterations()
        return MaxIts

    # def SetSearchWindowSize(self, searchWindow):
    #     self.searchWindow = [searchWindow, searchWindow, searchWindow]

    def SetShapePropagationScale(self, propagationScale):
        self.shapeDetectionFilter.SetPropagationScaling(-1*propagationScale)

    def SetShapeCurvatureScale(self, curvatureScale):
        self.shapeDetectionFilter.SetCurvatureScaling(curvatureScale)

    def SetShapeMaxRMSError(self, MaxRMSError):
        self.shapeDetectionFilter.SetMaximumRMSError(MaxRMSError)

    def SetLevelSetCurvature(self, curvatureScale):
        self.thresholdLevelSet.SetCurvatureScaling(curvatureScale)
        
    def SetLevelSetPropagation(self, propagationScale):
        self.thresholdLevelSet.SetPropagationScaling(propagationScale)
        
    def SetLevelSetLowerThreshold(self, lowerThreshold):
        self.sigFilter.SetBeta(int(lowerThreshold))
        self.thresholdFilter.SetLowerThreshold(int(lowerThreshold)+1) # Add one so the threshold is greater than Zero
        self.thresholdLevelSet.SetLowerThreshold(int(lowerThreshold))   

    def SetLevelSetUpperThreshold(self, upperThreshold):
        self.sigFilter.SetAlpha(int(upperThreshold))
        self.thresholdFilter.SetUpperThreshold(int(upperThreshold))
        self.thresholdLevelSet.SetUpperThreshold(int(upperThreshold))   
        
    def SetLevelSetError(self,MaxError):        
        self.thresholdLevelSet.SetMaximumRMSError(MaxError)

    def SetImage(self, image):
        self.image = image

    def SefSeedPoint(self, SeedPoint):
        self.SeedPoint = SeedPoint

    def SetScalingFactor(self, ScalingFactor):
        ScalingFactor = [int(ScalingFactor),int(ScalingFactor),int(ScalingFactor)]
        self.ScalingFactor = ScalingFactor
        self.shrinkFilter.SetShrinkFactors(ScalingFactor)
        self.expandFilter.SetExpandFactors(ScalingFactor)

    def SetAnisotropicIts(self, AnisotropicIts):
        self.anisotropicFilter.SetNumberOfIterations(AnisotropicIts)
    
    def SetAnisotropicTimeStep(self, AnisotropicTimeStep):
        self.anisotropicFilter.SetTimeStep(AnisotropicTimeStep)
    
    def SetAnisotropicConductance(self, AnisotropicConductance):
        self.anisotropicFilter.SetConductanceParameter(AnisotropicConductance)

    def SetConfidenceConnectedIts(self, ConfidenceConnectedIts):
        self.ConfidenceConnectedIts = ConfidenceConnectedIts

    def SetConfidenceConnectedMultiplier(self, ConfidenceConnectedMultiplier):
        self.ConfidenceConnectedMultiplier = ConfidenceConnectedMultiplier

    def SetConfidenceConnectedRadius(self, ConfidenceConnectedRadius):
        self.ConfidenceConnectedRadius = ConfidenceConnectedRadius

    def SetBinaryMorphologicalRadius(self, kernelRadius):
        self.erodeFilter.SetKernelRadius(kernelRadius)
        self.dilateFilter.SetKernelRadius(kernelRadius) 

    def SetMaxVolume(self, MaxVolume):
        self.MaxVolume = MaxVolume  

    def SetLaplacianExpansionDirection(self, expansionDirection):       
        self.laplacianFilter.SetReverseExpansionDirection(expansionDirection)

    def SetLaplacianError(self, RMSError):
        self.laplacianFilter.SetMaximumRMSError(RMSError)

    def SetConnectedComponentFullyConnected(self, fullyConnected):
        self.connectedComponentFilter.SetFullyConnected(fullyConnected) 

    def SetConnectedComponentDistance(self, distanceThreshold):
        #Distance = Intensity difference NOT location distance
        self.connectedComponentFilter.SetDistanceThreshold(distanceThreshold) 
   
    def EstimateSigmoid(self):
        ''' Estimate the upper threshold of the sigmoid based on the 
        mean and std of the image intensities '''
        ndaImg = sitk.GetArrayFromImage(self.image)

        # [ndaImg > 25]
        std = np.std(ndaImg) # 30 25
        mean = np.mean(ndaImg)

        # Using a linear model (fitted in Matlab and manually selected sigmoid threshold values)
        # UpperThreshold = 0.899*(std+mean) - 41.3

        UpperThreshold = 0.002575*(std+mean)*(std+mean) - 0.028942*(std+mean) + 36.791614

        if self.verbose == True:
            print('Mean: ' + str(round(mean,2)))
            print('STD: ' + str(round(std,2)))
            print('UpperThreshold: ' + str(round(UpperThreshold,2)))
            print(' ')

        return UpperThreshold

    def FlipImage(self,image):
        #Flip image(s) (if needed)
        flipFilter = sitk.FlipImageFilter()
        flipFilter.SetFlipAxes((False,True,False))
        image = flipFilter.Execute(self.image)
        return image

    def ThresholdImage(self):
        try:
            self.segImg.CopyInformation(self.image)
        except:
            print('Error in copying information from self.image')
        tempImg = self.segImg * self.image
        self.segImg = self.thresholdFilter.Execute(tempImg)
        return self
    
    def scaleDownImage(self):
        self.image = self.shrinkFilter.Execute(self.image)
        return self

    def scaleUpImage(self):
        self.segImg = self.expandFilter.Execute(self.segImg)
        return self

    # Function definitions are below
    def apply_AnisotropicFilter(self):
        self.image = self.anisotropicFilter.Execute(self.image)
        return self

    def savePointList(self):
        try:
            # Save the user defined points in a .txt for automatimating testing (TODO)
            text_file = open(self.SeedListFilename, "r+")
            text_file.readlines()
            text_file.write("%s\n" % self.seedPoint)
            text_file.close()
        except:
            print("Saving to .txt failed...")
        return

    def AddImages(self, imageOne, imageTwo, iteration_num):

        ndaOutput = sitk.GetArrayFromImage(imageOne)
        ndaOutput = np.asarray(ndaOutput) 
        ndaTwo = sitk.GetArrayFromImage(imageTwo)

        ndaTwo = np.asarray(ndaTwo) 
        ndaTwo[ndaTwo != 0] = iteration_num

        ndaOutput = ndaOutput + ndaTwo
        output = sitk.Cast(sitk.GetImageFromArray(ndaOutput), imageOne.GetPixelID())
        output.CopyInformation(imageOne)

        return output

    def SegToBinary(self, image):
        # Want 0 for the background and 1 for the objects
        nda = sitk.GetArrayFromImage(image)
        nda = np.asarray(nda)

        nda[nda < 0] = 0
        nda[nda != 0] = 1
        
        image = sitk.Cast(sitk.GetImageFromArray(nda), self.image.GetPixelID())
        image.CopyInformation(self.image)

        return image


    def BiasFieldCorrection(self): 
        if self.verbose == True:
            print('\033[94m' + 'Bias Field Correction')

        #   Correct for the MRI bias field 
        self.image  = sitk.Cast(self.image, sitk.sitkFloat32)

        input_image_nda = sitk.GetArrayFromImage(self.image)
        input_image_nda = np.asarray(input_image_nda)
        input_image_nda = input_image_nda*0

        mask_img = sitk.Cast(sitk.GetImageFromArray(input_image_nda), sitk.sitkFloat32)
        mask_img.CopyInformation(self.image)

        # test = sitk.OtsuThreshold( self.image, 0, 1, 200 )

        mask_img = sitk.Cast(mask_img, 1) #Can't be a 32 bit float

        print(mask_img.GetPixelID())


        self.image = self.BiasFilter.Execute(self.image, mask_img)
        sitk.Show(self.image, 'post_bias')

        
