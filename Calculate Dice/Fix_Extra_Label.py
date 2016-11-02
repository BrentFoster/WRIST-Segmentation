	Observer_Two_SegImg_np = np.asarray(sitk.GetArrayFromImage(Observer_Two_SegImg))

	Observer_Two_SegImg_np[Observer_Two_SegImg_np != 0] = Observer_Two_SegImg_np[Observer_Two_SegImg_np != 0] - 1

	tempImg = sitk.Cast(sitk.GetImageFromArray(Observer_Two_SegImg_np), Observer_Two_SegImg.GetPixelID())
	tempImg.CopyInformation(Observer_Two_SegImg)

	Observer_Two_SegImg = tempImg

	imageWriter = sitk.ImageFileWriter()
	imageWriter.Execute(Observer_Two_SegImg, Observer_Two_Filenames[k], False)
