import SimpleITK as sitk
import numpy as np

import timeit

class BoneSeg(object):
    """Class of BoneSegmentation. REQUIRED: BoneSeg(MRI_Image,SeedPoint)"""
    def Execute(self, original_image, original_seedPoint, verbose=False, returnSitkImage=True, convertSeedPhyscialFlag=True):

        start_time = timeit.default_timer() 

        self.verbose = verbose # Optional argument to output text to terminal

        self.image = original_image
        self.seedPoint = original_seedPoint
        self.original_seedPoint = original_seedPoint
        self.convertSeedPhyscialFlag = convertSeedPhyscialFlag

        # Convert images to type float 32 first
        try:
            self.image = sitk.Cast(self.image, sitk.sitkFloat32)
        except:
            # Convert from numpy array to a SimpleITK image type first then cast
            self.image = sitk.Cast(sitk.GetImageFromArray(self.image), sitk.sitkFloat32)
            original_image = self.image # original_image needs to be a SimpleITK image type for later

        # Convert the seed point to image coordinates (from physical) if needed and round
        self.RoundSeedPoint()

        # Crop the image so that it considers only a search space around the seed point
        # to speed up computation significantly!
        if self.verbose == True:
            print('\033[94m' + 'Cropping image')
        self.CropImage()

        if self.verbose == True:
            print('\033[94m' + 'Estimating upper sigmoid threshold level')

        # Estimate the threshold level by image intensity statistics
        LowerThreshold = self.EstimateSigmoid()
        
        self.SetLevelSetLowerThreshold(LowerThreshold)

        if self.verbose == True:
            print('\033[94m' + "Current Seed Point: "),
            print(self.seedPoint)
            print('\033[94m' + "Rounding and converting to voxel domain: "), 

        if self.verbose == True:
            print(self.seedPoint)
            print('\033[90m' + "Scaling image down...")
        self.scaleDownImage()

        if self.verbose == True:
            elapsed = timeit.default_timer() - start_time
            print("Elapsed Time (Preprocessing ):" + str(round(elapsed,3)))

        if self.verbose == True:
            print('\033[90m' + "Sigmoid shape detection level set...")
        self.SigmoidLevelSet()

        if self.verbose == True:
            print('\033[90m' + "Sigmoid shape detection level set by iteration...")

        self.SigmoidLevelSetIterations()

        if self.verbose == True:
            print('\033[90m' + "Scaling image back...")
        self.scaleUpImage()
        
        # if self.verbose == True:
        #     print('\033[93m' + "Filling Segmentation Holes...")
        # self.HoleFilling()

        # if self.verbose == True:
        #     print('\033[90m' + "Dilating image slightly...")
        # self.segImg  = sitk.Cast(self.segImg, sitk.sitkUInt16)
        # self.segImg = self.dilateFilter.Execute(self.segImg, 0, 1, False)

        # if self.verbose == True:
        #     print('\033[90m' + "Eroding image slightly...")
        # self.segImg = self.erodeFilter.Execute(self.segImg, 0, 1, False)

        # if self.verbose == True:
        #     print('\033[93m' + "Filling Segmentation Holes...")
        # self.HoleFilling()

        if self.verbose == True:
            print('\033[96m' + "Finished with seed point "),
            print(self.seedPoint)

        ' Uncrop the image '
        # self.segImg = self.image
        self.UnCropImage(original_image)

        if returnSitkImage == True:
            # Return a SimpleITK type image
            return  self.segImg 
        else:
            # Return a numpy array image (needed for using multiple logical cores)
            self.segImg = sitk.Cast(self.segImg, sitk.sitkUInt8)
            npImg = sitk.GetArrayFromImage(self.segImg)

            return  npImg


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


    def UnCropImage(self, original_image):
        ' Indexing to put the segmentation of the cropped image back into the original MRI '

        # Need the original seed point to know where the cropped volume is in the original image
        cropNdxOne = np.asarray(self.original_seedPoint[0]) - self.searchWindow
        cropNdxTwo = np.asarray(self.original_seedPoint[0]) + self.searchWindow

        original_image_nda = sitk.GetArrayFromImage(original_image)
        original_image_nda = np.asarray(original_image_nda)

        seg_img_nda = sitk.GetArrayFromImage(self.segImg)
        seg_img_nda = np.asarray(seg_img_nda)

        original_image_nda = original_image_nda*0;

        original_image_nda[cropNdxOne[2]:cropNdxTwo[2],
                        cropNdxOne[1]:cropNdxTwo[1],
                        cropNdxOne[0]:cropNdxTwo[0]] = seg_img_nda

        # Convert back to SimpleITK image type
        self.segImg = sitk.Cast(sitk.GetImageFromArray(original_image_nda), sitk.sitkUInt16)
        self.segImg.CopyInformation(original_image)

        return self

    def CropImage(self):
        ' Crop the input_image around the initial seed point to speed up computation '
        cropFilter = sitk.CropImageFilter()
        addFilter = sitk.AddImageFilter()

        im_size = np.asarray(self.image.GetSize())

        # Check to make sure the search window size won't go outside of the image dimensions
        for i in range(0,3):
            print(self.searchWindow[i])
            print(self.seedPoint[0])
            if self.searchWindow[i] > self.seedPoint[0][i]:
                self.searchWindow[i] = self.seedPoint[0][i]
            if self.searchWindow[i] > im_size[i] - self.seedPoint[0][i]:
                self.searchWindow[i] = im_size[i] - self.seedPoint[0][i]

        cfLowerBound = np.asarray(np.asarray(self.seedPoint[0]) - self.searchWindow)
        cfUpperBound = np.asarray(im_size - np.asarray(self.seedPoint[0]) - self.searchWindow)
        
        # These need to be changed to a list using numpy .tolist() for some reason
        cfLowerBound = cfLowerBound.tolist()
        cfUpperBound = cfUpperBound.tolist()
        
        cropFilter.SetLowerBoundaryCropSize(cfLowerBound)
        cropFilter.SetUpperBoundaryCropSize(cfUpperBound)

        self.image = cropFilter.Execute(self.image)

        # The seed point is now in the middle of the search window
        self.seedPoint = [np.asarray(self.searchWindow)]

        return self


    def SigmoidLevelSetIterations(self):
        ''' Pre-processing '''
        start_time = timeit.default_timer() 

        # self.sigFilter.SetBeta(120)
        # self.sigFilter.SetAlpha(0)

        print('GetAlpha')
        print(self.sigFilter.GetAlpha())

        print('GetBeta')
        print(self.sigFilter.GetBeta())

        processedImage = self.sigFilter.Execute(self.image) 
        processedImage  = sitk.Cast(processedImage, sitk.sitkUInt16)

        edgePotentialFilter = sitk.EdgePotentialImageFilter()
        gradientFilter = sitk.GradientImageFilter()

        gradImage = gradientFilter.Execute(processedImage)

        processedImage = edgePotentialFilter.Execute(gradImage)

        elapsed = timeit.default_timer() - start_time
        if self.verbose == True:
            print("Elapsed Time (processedImage):" + str(round(elapsed,3)))

        ''' Create Seed Image '''
        if self.verbose == True:
            print('Starting ShapeDetectionLevelSetImageFilter')
        start_time = timeit.default_timer() 

        # Create the seed image
        nda = sitk.GetArrayFromImage(self.image)
        nda = np.asarray(nda)
        nda = nda*0

        # print('seedPoint = self.seedPoint[0]')
        seedPoint = self.seedPoint[0]
        # print(seedPoint)
        # print('Size of nda')
        # print(nda.shape)
        # print(' ')

        # In numpy an array is indexed in the opposite order (z,y,x)
        nda[seedPoint[2]][seedPoint[1]][seedPoint[0]] = 1

        self.segImg = sitk.Cast(sitk.GetImageFromArray(nda), sitk.sitkUInt16)
        self.segImg.CopyInformation(self.image)

        self.segImg = sitk.BinaryDilate(self.segImg, 3)


        ''' Segmentation '''

        # Signed distance function using the initial seed point (segImg)
        init_ls = sitk.SignedMaurerDistanceMap(self.segImg, insideIsPositive=True, useImageSpacing=True)
        init_ls = sitk.Cast(init_ls, sitk.sitkFloat32)

        processedImage = sitk.Cast(processedImage, sitk.sitkFloat32)

        self.segImg = self.shapeDetectionFilter.Execute(init_ls, processedImage)
     
        if self.verbose == True:
            print('Done with ShapeDetectionLevelSetImageFilter!')

            print(self.shapeDetectionFilter)

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

    def SetDefaultValues(self):
        # Set the default values of all the parameters here
        self.SetScalingFactor(1) #X,Y,Z
       
        self.SeedListFilename = "PointList.txt"
        self.SetMaxVolume(300000) #Pixel counts (TODO change to mm^3) 

        # Morphological Operators
        self.fillFilter.SetForegroundValue(1) 
        self.fillFilter.FullyConnectedOff() 
        self.SetBinaryMorphologicalRadius(1)

        # Shape Detection Filter
        self.SetShapeMaxRMSError(0.001)
        self.SetShapeMaxIterations(1000)
        self.SetShapePropagationScale(4)
        self.SetShapeCurvatureScale(1.1)

        # Sigmoid Filter
        self.sigFilter.SetAlpha(0)
        self.sigFilter.SetBeta(120)
        self.sigFilter.SetOutputMinimum(0)
        self.sigFilter.SetOutputMaximum(255)

        # Search Space Window
        self.SetSearchWindowSize(50)

    def SetShapeMaxIterations(self, MaxIts):
        self.shapeDetectionFilter.SetNumberOfIterations(int(MaxIts))

    def SetSearchWindowSize(self, searchWindow):
        self.searchWindow = [searchWindow, searchWindow, searchWindow]

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

    def HoleFilling(self):
        # Cast to 16 bit (needed for the fill filter to work)
        self.segImg  = sitk.Cast(self.segImg, sitk.sitkUInt16)

        # Apply the filters to the binary image
        self.segImg = self.fillFilter.Execute(self.segImg)

        return self

    def ShapeDetection(self):
        print('Shape Detection Level Set...')

        self.segImg = sitk.Cast(self.segImg, sitk.sitkUInt16)

        # Signed distance function using the initial levelset segmentation
        init_ls = sitk.SignedMaurerDistanceMap(self.segImg, insideIsPositive=True, useImageSpacing=True)

        gradientImage = self.GradientMagnitudeFilter.Execute(self.image)

        shapeBinary = self.shapeDetectionFilter.Execute(init_ls, gradientImage)

        npshapeBinary = np.asarray(sitk.GetArrayFromImage(shapeBinary), dtype='float64')

        npshapeBinary[npshapeBinary > 0.2] = 1 # Make into a binary again
        # npshapeBinary[npshapeBinary < 0] = 0 # Make into a binary again

        npshapeBinary[npshapeBinary != 1] = 0

        self.segImg = sitk.Cast(sitk.GetImageFromArray(npshapeBinary), self.image.GetPixelID())
        self.segImg.CopyInformation(self.image)

        if self.verbose == True:
            print(self.shapeDetectionFilter)
    
    def SigmoidLevelSet(self):
        ''' Pre-processing '''
        processedImage = self.sigFilter.Execute(self.image)
        processedImage  = sitk.Cast(processedImage, sitk.sitkUInt16)

        edgePotentialFilter = sitk.EdgePotentialImageFilter()
        gradientFilter = sitk.GradientImageFilter()

        gradImage = gradientFilter.Execute(processedImage)

        processedImage = edgePotentialFilter.Execute(gradImage)

        #Want 0 for the background and 1 for the objects
        nda = sitk.GetArrayFromImage(processedImage)
        nda = np.asarray(nda)

        nda[nda != 1] = 0

        processedImage = sitk.Cast(sitk.GetImageFromArray(nda), self.image.GetPixelID())
        processedImage.CopyInformation(self.image)

        ''' Create Seed Image '''
        nda = sitk.GetArrayFromImage(self.image)
        nda = np.asarray(nda)
        nda = nda*0

        seedPoint = self.seedPoint[0]

        # In numpy, an array is indexed in the opposite order (z,y,x)
        nda[seedPoint[2]][seedPoint[1]][seedPoint[0]] = 1

        self.segImg = sitk.Cast(sitk.GetImageFromArray(nda), sitk.sitkUInt16)
        self.segImg.CopyInformation(self.image)

        self.segImg = sitk.BinaryDilate(self.segImg, 3)


        ''' Segmentation '''
        # Signed distance function using the initial seed point (segImg)
        init_ls = sitk.SignedMaurerDistanceMap(self.segImg, insideIsPositive=True, useImageSpacing=True)
        init_ls = sitk.Cast(init_ls, sitk.sitkFloat32)

        processedImage = sitk.Cast(processedImage, sitk.sitkFloat32)

        if self.verbose == True:
            print('Starting ShapeDetectionLevelSetImageFilter')
        
        start_time = timeit.default_timer()

        self.segImage  = self.shapeDetectionFilter.Execute(init_ls, processedImage)

        elapsed = timeit.default_timer() - start_time

        if self.verbose == True:
            print("Elapsed Time (secs):" + str(round(elapsed,3)))

            print('Done with ShapeDetectionLevelSetImageFilter!')

            print(self.shapeDetectionFilter)
        

        return self

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


    def LaplacianLevelSet(self):
        # Check the image type of self.segImg and image are the same (for Python 3.3 and 3.4)
        self.segImg = sitk.Cast(self.segImg, self.image.GetPixelID()) #Can't be a 32 bit float
        self.segImg.CopyInformation(self.image)

        # Additional post-processing (Lapacian Level Set Filter)
        # Binary image needs to have a value of 0 and 1/2*(x+1)
        nda = sitk.GetArrayFromImage(self.segImg)
        nda = np.asarray(nda)

        # Fix the intensities of the output of the laplcian; 0 = 1 and ~! 1 is 0 then 1 == x+1
        nda[nda == 1] = 0.5

        self.segImg = sitk.GetImageFromArray(nda)
        self.segImg = sitk.Cast(self.segImg, self.image.GetPixelID())
        self.segImg.CopyInformation(self.image)


        self.segImg = self.laplacianFilter.Execute(self.segImg, self.image)
        if self.verbose == True:
            print(self.laplacianFilter)

        nda = sitk.GetArrayFromImage(self.segImg)
        nda = np.asarray(nda)

        # Fix the intensities of the output of the laplcian; 0 = 1 and ~! 1 is 0 then 1 == x+1
        nda[nda <= 0.3] = 0
        nda[nda != 0] = 1

        self.segImg = sitk.GetImageFromArray(nda)
        self.segImg = sitk.Cast(self.segImg, self.image.GetPixelID())
        self.segImg.CopyInformation(self.image)

        return self


    def ConnectedComponent(self):

        self.segImg = sitk.Cast(self.segImg, 1) #Can't be a 32 bit float
        # self.segImg.CopyInformation(segmentation)

        # Try to remove leakage areas by first eroding the binary and
        # get the labels that are still connected to the original seed location

        self.segImg = self.erodeFilter.Execute(self.segImg, 0, 1, False)

        self.segImg = self.connectedComponentFilter.Execute(self.segImg)

        nda = sitk.GetArrayFromImage(self.segImg)
        nda = np.asarray(nda)

        # In numpy an array is indexed in the opposite order (z,y,x)
        tempseedPoint = self.seedPoint[0]
        val = nda[tempseedPoint[2]][tempseedPoint[1]][tempseedPoint[0]]

        # Keep only the label that intersects with the seed point
        nda[nda != val] = 0 
        nda[nda != 0] = 1

        self.segImg = sitk.GetImageFromArray(nda)

        # Undo the earlier erode filter by dilating by same radius
        self.dilateFilter.SetKernelRadius(3)
        self.segImg = self.dilateFilter.Execute(self.segImg, 0, 1, False)

        return self

    def LeakageCheck(self):

        # Check the image type of self.segImg and image are the same (for Python 3.3 and 3.4)
        # self.segImg = sitk.Cast(self.segImg, segmentation.GetPixelID()) #Can't be a 32 bit float
        # self.segImg.CopyInformation(segmentation)

        nda = sitk.GetArrayFromImage(self.segImg)
        nda = np.asarray(nda)

        volume = len(nda[nda == 1])
        if volume > self.MaxVolume:
            if self.verbose == True:
                print('\033[97m' + "Failed check with volume "),
                print(volume)
                print("Skipping this label")
            # Clearing the label is the same as ignoring it since they're added together later
            nda = nda*0 
            self.segImg = sitk.Cast(sitk.GetImageFromArray(nda), self.segImg.GetPixelID())
            
        else:
            if self.verbose == True:
                print('\033[96m' + "Passed with volume "),
                print(volume)

        return self

    def ThresholdLevelSet(self):
        # Create the seed image
        nda = sitk.GetArrayFromImage(self.image)
        nda = np.asarray(nda)
        nda = nda*0

        seedPoint = self.seedPoint[0]
        if self.verbose == True:
            print(seedPoint)
        # In numpy an array is indexed in the opposite order (z,y,x)
        nda[seedPoint[2]][seedPoint[1]][seedPoint[0]] = 1

        seg = sitk.Cast(sitk.GetImageFromArray(nda), sitk.sitkUInt16)
        seg.CopyInformation(self.image)

        seg = sitk.BinaryDilate(seg, 3)

        init_ls = sitk.SignedMaurerDistanceMap(seg, insideIsPositive=True, useImageSpacing=True)

        threshOutput = self.thresholdLevelSet.Execute(init_ls, self.image)
        if self.verbose == True:
            print(self.thresholdLevelSet)


        nda = sitk.GetArrayFromImage(threshOutput)
        nda = np.asarray(nda)

        # Fix the intensities of the output of the level set; 0 = 1 and ~! 1 is 0 then 1 == x+1
        nda[nda > 0] = 1
        nda[nda < 0] = 0

        self.segImg = sitk.GetImageFromArray(nda)
        self.segImg = sitk.Cast(self.segImg, self.image.GetPixelID())
        self.segImg.CopyInformation(self.image)

        return self
