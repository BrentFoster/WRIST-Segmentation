import SimpleITK as sitk
import Dice
import numpy as np

def saveLog(filename, logData, HeaderText):
	try:
		#Save computation time in a log file
		text_file = open(filename, "r+")
		text_file.readlines()
		text_file.write("%s\n" % HeaderText)
		text_file.write("%s\n" % logData)
		text_file.close()
	except:
		print("Failed writing log data to .txt file")

Calculate_Hausdorff = False
Calculate_Dice = True
Calculate_Jaccard = False


displayColors = True #Change the color of the output text
if displayColors == True:
	from colorama import init
	from colorama import Fore
	from colorama import Back
	from colorama import Style
	init()

	print(Style.BRIGHT + Fore.YELLOW + 'Starting Dice Calculation...')

ImageFileNames = ("Mac_Automated_vs_MB_Filenames.txt", 
					"Mac_Automated_vs_YA_Filenames.txt", 
					"Mac_MB_vs_YA_Filenames.txt")


# ImageFileNames = ("Mac_Automated_vs_YA_Filenames.txt",)

for k in range(0,len(ImageFileNames)):

	curr_ImageFileNames = ImageFileNames[k]

	print(Style.BRIGHT + Fore.YELLOW + 'Starting with ' + curr_ImageFileNames)

	text_file = open(curr_ImageFileNames, "r")

	Filenames = text_file.read().splitlines()

	Observer_One_Filenames = []
	Observer_Two_Filenames = []

	for i in range(0, len(Filenames)/2):
		Observer_One_Filenames.append(str(Filenames[2*i]))
		Observer_Two_Filenames.append(str(Filenames[2*i + 1]))


	num_obervers = 2
	num_Images = len(Observer_One_Filenames)
	num_Bones  = 8

	# Initilize some variables to hold the output numbers
	dice_values = np.zeros((num_Images, 8))
	jaccard_values = np.zeros((num_Images,8))

	Hausdorff_Distance_values = np.zeros((num_Images, 8))
	AverageHausdorffDistance_values = np.zeros((num_Images, 8))

	for i in range(0, num_Images):
		print(Fore.GREEN + 'Running File Number ' + str(i))
		for k in range(1,num_Bones+1):		
			print(Fore.BLUE + 'Running Label Number ' + str(k))

			Observer_One_SegImg = sitk.ReadImage(Observer_One_Filenames[i])
			Observer_Two_SegImg = sitk.ReadImage(Observer_Two_Filenames[i])

			DiceCalulator = Dice.DiceCalulator()
			DiceCalulator.SetImages(Observer_One_SegImg, Observer_Two_SegImg, label=k)


			if Calculate_Dice == True:			
				dice = DiceCalulator.Calculate()			
				dice = round(dice*100, 2)
				dice_values[i][k-1] = dice
				print(Fore.CYAN  + 'Dice: ' + str(dice_values))

			if Calculate_Jaccard == True:
				jaccard = DiceCalulator.CalculateSITKDice(GetJaccard=True)
				jaccard = round(jaccard*100, 2)
				jaccard_values[i][k-1] = jaccard
				print(Fore.CYAN  + 'Jaccard: ' + str(jaccard_values))		

			if Calculate_Hausdorff == True:
				(Hausdorff_Distance, AverageHausdorffDistance) = DiceCalulator.HausdorffDistance()
				Hausdorff_Distance = round(Hausdorff_Distance, 2)
				AverageHausdorffDistance = round(AverageHausdorffDistance, 2)

				Hausdorff_Distance_values[i][k-1] = (Hausdorff_Distance)
				AverageHausdorffDistance_values[i][k-1] = (AverageHausdorffDistance)

			
				print(Fore.CYAN  + 'Hausdorff Distance: ' + str(Hausdorff_Distance_values))
				print(Fore.CYAN  + 'Average Hausdorff Distance: ' + str(AverageHausdorffDistance_values))
		
	# Save the output to a .txt file
	filename = 'Output_Dice_Values.txt'

	if Calculate_Dice == True:
		saveLog(filename, dice_values, ('Dice for ' + curr_ImageFileNames))

	if Calculate_Hausdorff == True:
		saveLog(filename, Hausdorff_Distance_values, ('Hausdorff Distance for ' + curr_ImageFileNames))
		saveLog(filename, AverageHausdorffDistance_values, ('Mean Hausdorff Distance for ' + curr_ImageFileNames))

	if Calculate_Jaccard == True:
		saveLog(filename, jaccard_values, ('Jaccard Index for ' + curr_ImageFileNames))
		


