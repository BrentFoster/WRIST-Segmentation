import SimpleITK as sitk
import Dice
import numpy as np

text_file = open("Automated_vs_MB_Filenames.txt", "r")
Filenames = text_file.read().splitlines()

Calculate_Hausdorff = False



displayColors = True #Change the color of the output text
if displayColors == True:
	from colorama import init
	from colorama import Fore
	from colorama import Back
	from colorama import Style
	init()

	print(Style.BRIGHT + Fore.YELLOW + 'Starting parameter sensitivity test code ')


Observer_One_Filenames = []
Observer_Two_Filenames = []

for i in range(0, len(Filenames)/2):
	Observer_One_Filenames.append(str(Filenames[2*i]))
	Observer_Two_Filenames.append(str(Filenames[2*i + 1]))


num_obervers = 2
num_Images = len(Observer_One_Filenames)

dice_values = np.zeros((num_Images, 8))
Hausdorff_Distance_values = np.zeros((num_Images, 8))
AverageHausdorffDistance_values = np.zeros((num_Images, 8))


for i in range(0, num_Images):
	print(Fore.GREEN + 'Running File Number ' + str(i))

	for k in range(1,9):		
		print(Fore.BLUE + 'Running Label Number ' + str(k))

		Observer_One_SegImg = sitk.ReadImage(Observer_One_Filenames[i])
		Observer_Two_SegImg = sitk.ReadImage(Observer_Two_Filenames[i])

		DiceCalulator = Dice.DiceCalulator()
		DiceCalulator.SetImages(Observer_One_SegImg, Observer_Two_SegImg, label=k)
		dice = DiceCalulator.Calculate()
		dice = round(dice*100, 2)
		dice_values[i][k-1] = dice

		print(Fore.CYAN  + 'Dice: ' + str(dice_values))

		if Calculate_Hausdorff == True:
			(Hausdorff_Distance, AverageHausdorffDistance) = DiceCalulator.HausdorffDistance()
			Hausdorff_Distance = round(Hausdorff_Distance, 2)
			AverageHausdorffDistance = round(AverageHausdorffDistance, 2)

			Hausdorff_Distance_values[i][k-1] = (Hausdorff_Distance)
			AverageHausdorffDistance_values[i][k-1] = (AverageHausdorffDistance)

		
			print(Fore.CYAN  + 'Hausdorff Distance: ' + str(Hausdorff_Distance_values))
			print(Fore.CYAN  + 'Average Hausdorff Distance: ' + str(AverageHausdorffDistance_values))
	



