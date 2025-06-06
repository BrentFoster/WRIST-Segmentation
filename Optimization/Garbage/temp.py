#Load the Python Packages
import SimpleITK as sitk
import numpy as np

#############################################################################################
###SEGMENTATION CLASS###
#############################################################################################
class BoneSeg(object):
    """Class of BoneSegmentation. REQUIRED: BoneSeg(MRI_Image,SeedPoint)"""
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

        ##Initilize the ITK filters##
        #Filters to down/up sample the image for faster computation
        self.shrinkFilter = sitk.ShrinkImageFilter()
        self.expandFilter = sitk.ExpandImageFilter()
        #Filter to reduce noise while preserving edgdes
        self.anisotropicFilter = sitk.CurvatureAnisotropicDiffusionImageFilter()
        #Post-processing filters for fillinging holes and to attempt to remove any leakage areas
        self.dilateFilter = sitk.BinaryDilateImageFilter()
        self.erodeFilter = sitk.BinaryErodeImageFilter()
        self.fillFilter = sitk.BinaryFillholeImageFilter()  
        self.connectedComponentFilter = sitk.ScalarConnectedComponentImageFilter()
        self.laplacianFilter = sitk.LaplacianSegmentationLevelSetImageFilter()
        self.thresholdLevelSet = sitk.ThresholdSegmentationLevelSetImageFilter()

        #Initilize the SimpleITK Filters
        self.GradientMagnitudeFilter = sitk.GradientMagnitudeImageFilter()
        self.shapeDetectionFilter = sitk.ShapeDetectionLevelSetImageFilter()

        self.sigFilter = sitk.SigmoidImageFilter()

        #Set the deafult values 
        self.SetDefaultValues()

    def SetDefaultValues(self):
        #Set the default values of all the parameters here
        self.SetScalingFactor(2) #X,Y,Z

        # self.SetAnisotropicIts(5)
        # self.SetAnisotropicTimeStep(0.01)
        # self.SetAnisotropicConductance(2)
        # self.SetConfidenceConnectedIts(0)
        # self.SetConfidenceConnectedMultiplier(0.5)
        # self.SetConfidenceConnectedRadius(2)
        # self.SetLaplacianExpansionDirection(True) #Laplacian Level Set
        # self.SetLaplacianError(0.001)
        # self.SetConnectedComponentFullyConnected(True)    
        # self.SetConnectedComponentDistance(0.01) 
        
        self.SeedListFilename = "PointList.txt"
        self.SetMaxVolume(300000) #Pixel counts (TODO change to mm^3)   
        self.SetBinaryMorphologicalRadius(2)
        self.SetLevelSetLowerThreshold(0)
        self.SetLevelSetUpperThreshold(75)
        self.SetLevelSetIts(2500)
        self.SetLevelSetReverseDirection(True)
        self.SetLevelSetError(0.03)
        self.SetLevelSetPropagation(1)
        self.SetLevelSetCurvature(1)

        #Shape Detection Filter
        self.SetShapeMaxRMSError(0.01)
        self.SetShapeMaxIterations(500)
        self.SetShapePropagationScale(-1)
        self.SetShapeCurvatureScale(1)

        #Sigmoid Filter
        self.sigFilter.SetAlpha(0)
        self.sigFilter.SetBeta(80)
        self.sigFilter.SetOutputMinimum(0)
        self.sigFilter.SetOutputMaximum(1)



    def SetShapeMaxIterations(self, MaxIts):
        self.shapeDetectionFilter.SetNumberOfIterations(int(MaxIts))

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
        self.sigFilter.SetAlpha(int(lowerThreshold))
        self.thresholdLevelSet.SetLowerThreshold(int(lowerThreshold))   
        
    def SetLevelSetUpperThreshold(self, upperThreshold):
        self.sigFilter.SetBeta(int(upperThreshold))
        self.thresholdLevelSet.SetUpperThreshold(int(upperThreshold))   
        
    def SetLevelSetIts(self,iterations):
        self.thresholdLevelSet.SetNumberOfIterations(int(iterations))
        
    def SetLevelSetReverseDirection(self, direction):
        self.thresholdLevelSet.SetReverseExpansionDirection(direction)
        
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

#############################################################################################
###Main algorithm execution here###
#############################################################################################
    def Execute(self, image, seedPoint, verbose = False):

        self.verbose = verbose #Optional argument to output text to terminal


        self.image = sitk.Cast(sitk.GetImageFromArray(image), sitk.sitkFloat32)
        #self.image = self.FlipImage(self.image) #Flip the MRI

        self.seedPoint = seedPoint

        #Convert images to float 32 first
        self.image = sitk.Cast(self.image, sitk.sitkFloat32)

        if self.verbose == True:
            print('\033[94m' + "Current Seed Point: "),
            print(self.seedPoint)
            print('\033[94m' + "Rounding and converting to voxel domain: "), 
        self.RoundSeedPoint()

        if self.verbose == True:
            print(self.seedPoint)
            print('\033[90m' + "Scaling image down...")
        self.scaleDownImage()

        # print('\033[92m' + "Applying the Anisotropic Filter...")
        # self.apply_AnisotropicFilter()

        # if self.verbose == True:
            # print("Threshold level set segmentation...")
        # self.ThresholdLevelSet() 

        self.SigmoidLevelSet()


        # print('\033[93m' + "Segmenting via confidence connected...")
        # self.ConfidenceConnectedSegmentation()

        # print('\033[95m' + "Running Laplacian Level Set...")
        # self.LaplacianLevelSet()

        # if self.verbose == True:
        #     print('\033[95m' + "Finding connected regions...")
        # self.ConnectedComponent()

        # if self.verbose == True:
            # print('\033[96m' + "Checking volume for potential leakage... "), #Comma keeps printing on the same line
        # self.LeakageCheck()

        # print('\033[90m' + "Simple threshold operation...")
        # self.ThresholdImage()
        # if (self.shapeDetectionFilter.GetNumberOfIterations > 0):
            # self.ShapeDetection()


        if self.verbose == True:
            print('\033[90m' + "Dilating image slightly...")
        #self.segImg  = sitk.Cast(self.segImg, sitk.sitkUInt16)
        #self.segImg = self.dilateFilter.Execute(self.segImg, 0, 1, False)

        if self.verbose == True:
            print('\033[93m' + "Filling Segmentation Holes...")
        #self.HoleFilling()

        if self.verbose == True:
            print('\033[90m' + "Scaling image back...")
        self.scaleUpImage()

        # print('\033[90m' + "Eroding image slightly...")
        # self.segImg = self.erodeFilter.Execute(self.segImg, 0, 1, False)




        if self.verbose == True:
            print('\033[96m' + "Finished with seed point "),
            print(self.seedPoint)
        
        returningSimpleITKImage = False
        if returningSimpleITKImage == True:
            return  self.segImg  
        else:  
            #Need to seed an array back
            #np.asarray(sitk.GetArrayFromImage(shapeBinary), dtype='float64')
            nda = sitk.GetArrayFromImage(self.segImg)
            nda = np.asarray(nda, dtype=np.int32)
            return nda


#############################################################################################
#############################################################################################

    def FlipImage(self,image):
        #Flip image(s) (if needed)
        flipFilter = sitk.FlipImageFilter()
        flipFilter.SetFlipAxes((False,True,False))
        image = flipFilter.Execute(self.image)
        return image

    def ThresholdImage(self):
        self.segImg.CopyInformation(self.image)
        thresholdFilter = sitk.BinaryThresholdImageFilter()
        thresholdFilter.SetLowerThreshold(1)
        thresholdFilter.SetUpperThreshold(100)
        tempImg = self.segImg * self.image
        self.segImg = thresholdFilter.Execute(tempImg)
        # sitk.Show(self.segImg)
        return self

    def RoundSeedPoint(self):
        tempseedPoint = np.array(self.seedPoint).astype(int) #Just to be safe make it int again
        tempseedPoint = tempseedPoint[0]
        #Convert from physical to image domain
        tempFloat = [float(tempseedPoint[0]), float(tempseedPoint[1]), float(tempseedPoint[2])]
        #Convert from physical units to voxel coordinates
        # tempVoxelCoordinates = self.image.TransformPhysicalPointToContinuousIndex(tempFloat)
        # self.seedPoint = tempVoxelCoordinates
        self.seedPoint = tempFloat

        #Need to round the seedPoints because integers are required for indexing
        ScalingFactor = np.array(self.ScalingFactor)
        tempseedPoint = np.array(self.seedPoint).astype(int)
        tempseedPoint = abs(tempseedPoint)
        tempseedPoint = tempseedPoint/ScalingFactor #Scale the points down as well
        tempseedPoint = tempseedPoint.round() #Need to round it again for Python 3.3

        self.seedPoint = [tempseedPoint]

        return self
    
    def scaleDownImage(self):
        self.image = self.shrinkFilter.Execute(self.image)
        return self

    def scaleUpImage(self):
        self.segImg = self.expandFilter.Execute(self.segImg)
        return self

    #Function definitions are below
    def apply_AnisotropicFilter(self):
        self.image = self.anisotropicFilter.Execute(self.image)
        return self

    def savePointList(self):
        try:
            #Save the user defined points in a .txt for automatimating testing (TODO)
            text_file = open(self.SeedListFilename, "r+")
            text_file.readlines()
            text_file.write("%s\n" % self.seedPoint)
            text_file.close()
        except:
            print("Saving to .txt failed...")
        return

    def HoleFilling(self):
        self.segImg  = sitk.Cast(self.segImg, sitk.sitkUInt16)
        #Apply the filters to the binary image
        self.segImg = self.fillFilter.Execute(self.segImg, True, 1)
        # self.segImg = self.dilateFilter.Execute(self.segImg, 0, 1, False)
        # self.segImg = self.fillFilter.Execute(self.segImg, True, 1)
        # self.segImg = self.erodeFilter.Execute(self.segImg, 0, 1, False)  
        return self

    # def ShapeDetection(self):
    #     print('Shape Detection Level Set...')

    #     self.segImg = sitk.Cast(self.segImg, sitk.sitkUInt16)

    #     #Signed distance function using the initial levelset segmentation
    #     init_ls = sitk.SignedMaurerDistanceMap(self.segImg, insideIsPositive=True, useImageSpacing=True)

    #     gradientImage = self.GradientMagnitudeFilter.Execute(self.image)

    #     shapeBinary = self.shapeDetectionFilter.Execute(init_ls, gradientImage)

    #     npshapeBinary = np.asarray(sitk.GetArrayFromImage(shapeBinary), dtype='float64')

    #     npshapeBinary[npshapeBinary > 0.2] = 1 #Make into a binary again
    #     # npshapeBinary[npshapeBinary < 0] = 0 #Make into a binary again

    #     npshapeBinary[npshapeBinary != 1] = 0

    #     self.segImg = sitk.Cast(sitk.GetImageFromArray(npshapeBinary), self.image.GetPixelID())
    #     self.segImg.CopyInformation(self.image)

    #     #print(self.shapeDetectionFilter)
    
    def SigmoidLevelSet(self):
        ''' Pre-processing '''
        medianFilter = sitk.BinaryMedianImageFilter()
        medianFilter.SetRadius([1,1,1])

        processedImage = self.sigFilter.Execute(self.image)
        if self.verbose == True:
            print(self.sigFilter)

        processedImage  = sitk.Cast(processedImage, sitk.sitkUInt16)

        #processedImage = medianFilter.Execute(processedImage)


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
        ###Create the seed image###
        nda = sitk.GetArrayFromImage(self.image)
        nda = np.asarray(nda)
        nda = nda*0

        seedPoint = self.seedPoint[0]

        #In numpy an array is indexed in the opposite order (z,y,x)
        nda[seedPoint[2]][seedPoint[1]][seedPoint[0]] = 1

        self.segImg = sitk.Cast(sitk.GetImageFromArray(nda), sitk.sitkUInt16)
        self.segImg.CopyInformation(self.image)

        self.segImg = sitk.BinaryDilate(self.segImg, 3)

        ''' Segmentation '''

        #Initilize the SimpleITK Filter
        # shapeDetectionFilter = sitk.ShapeDetectionLevelSetImageFilter()
        # shapeDetectionFilter.SetMaximumRMSError(0.002)
        # shapeDetectionFilter.SetNumberOfIterations(500)
        # shapeDetectionFilter.SetPropagationScaling(-4)
        # shapeDetectionFilter.SetCurvatureScaling(1)


        #Signed distance function using the initial seed point (segImg)
        init_ls = sitk.SignedMaurerDistanceMap(self.segImg, insideIsPositive=True, useImageSpacing=True)
        init_ls  = sitk.Cast(init_ls, sitk.sitkFloat32)

        processedImage  = sitk.Cast(processedImage, sitk.sitkFloat32)

        self.segImage = self.shapeDetectionFilter.Execute(init_ls, processedImage)

        if self.verbose == True:
            print(self.shapeDetectionFilter)

        #Want 0 for the background and 1 for the objects
        nda = sitk.GetArrayFromImage(self.segImage)
        nda = np.asarray(nda)
        
        # nda = nda * 100

        nda[nda < 0] = 0
        nda[nda != 0] = 1
        
        self.segImg = sitk.Cast(sitk.GetImageFromArray(nda), self.image.GetPixelID())
        # self.segImg = sitk.Cast(self.segImg, self.image.GetPixelID())
        self.segImg.CopyInformation(self.image)

        return self


    def LaplacianLevelSet(self):
        #Check the image type of self.segImg and image are the same (for Python 3.3 and 3.4)
        self.segImg = sitk.Cast(self.segImg, self.image.GetPixelID()) #Can't be a 32 bit float
        self.segImg.CopyInformation(self.image)

        #Additional post-processing (Lapacian Level Set Filter)
        #Binary image needs to have a value of 0 and 1/2*(x+1)
        nda = sitk.GetArrayFromImage(self.segImg)
        nda = np.asarray(nda)

        #Fix the intensities of the output of the laplcian; 0 = 1 and ~! 1 is 0 then 1 == x+1
        nda[nda == 1] = 0.5

        self.segImg = sitk.GetImageFromArray(nda)
        self.segImg = sitk.Cast(self.segImg, self.image.GetPixelID())
        self.segImg.CopyInformation(self.image)


        self.segImg = self.laplacianFilter.Execute(self.segImg, self.image)
        if self.verbose == True:
            print(self.laplacianFilter)

        nda = sitk.GetArrayFromImage(self.segImg)
        nda = np.asarray(nda)

        #Fix the intensities of the output of the laplcian; 0 = 1 and ~! 1 is 0 then 1 == x+1
        nda[nda <= 0.3] = 0
        nda[nda != 0] = 1

        self.segImg = sitk.GetImageFromArray(nda)
        self.segImg = sitk.Cast(self.segImg, self.image.GetPixelID())
        self.segImg.CopyInformation(self.image)

        return self


    def ConnectedComponent(self):

        self.segImg = sitk.Cast(self.segImg, 1) #Can't be a 32 bit float
        # self.segImg.CopyInformation(segmentation)

        #Try to remove leakage areas by first eroding the binary and
        #get the labels that are still connected to the original seed location

        self.segImg = self.erodeFilter.Execute(self.segImg, 0, 1, False)

        self.segImg = self.connectedComponentFilter.Execute(self.segImg)

        nda = sitk.GetArrayFromImage(self.segImg)
        nda = np.asarray(nda)

        #In numpy an array is indexed in the opposite order (z,y,x)
        tempseedPoint = self.seedPoint[0]
        val = nda[tempseedPoint[2]][tempseedPoint[1]][tempseedPoint[0]]

        #Keep only the label that intersects with the seed point
        nda[nda != val] = 0 
        nda[nda != 0] = 1

        self.segImg = sitk.GetImageFromArray(nda)

        #Undo the earlier erode filter by dilating by same radius
        self.dilateFilter.SetKernelRadius(3)
        self.segImg = self.dilateFilter.Execute(self.segImg, 0, 1, False)

        # self.segImg = sitk.Cast(self.segImg, segmentation.GetPixelID())
        # self.segImg.CopyInformation(segmentation)

        return self

    def LeakageCheck(self):

        #Check the image type of self.segImg and image are the same (for Python 3.3 and 3.4)
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
            #Clearing the label is the same as ignoring it since they're added together later
            nda = nda*0 
            self.segImg = sitk.Cast(sitk.GetImageFromArray(nda), self.segImg.GetPixelID())
            
        else:
            if self.verbose == True:
                print('\033[96m' + "Passed with volume "),
                print(volume)

        return self

    def ThresholdLevelSet(self):

        ###Create the seed image###
        nda = sitk.GetArrayFromImage(self.image)
        nda = np.asarray(nda)
        nda = nda*0

        seedPoint = self.seedPoint[0]
        if self.verbose == True:
            print(seedPoint)
        #In numpy an array is indexed in the opposite order (z,y,x)
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

        #Fix the intensities of the output of the level set; 0 = 1 and ~! 1 is 0 then 1 == x+1
        nda[nda > 0] = 1
        nda[nda < 0] = 0

        self.segImg = sitk.GetImageFromArray(nda)
        self.segImg = sitk.Cast(self.segImg, self.image.GetPixelID())
        self.segImg.CopyInformation(self.image)

        return self
#############################################################################################

