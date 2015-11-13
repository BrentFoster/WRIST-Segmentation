BoneSegmentation
=============

Current Build Status for Master Branch
-------

![Current Build Status](https://img.shields.io/shippable/562c7f391895ca447420e213.svg?style=plastic)

Purpose 
-------

Segment the carpal bones from MR images given a set of user defined locations (seed points) within the image. It utilizes the open source [SimpleITK](http://www.simpleitk.org/) library which is a python wrapper for many [ITK](http://www.itk.org/) functions which are mainly implemented in C++. 

BoneSegmentation currently uses the [Confidence Connected Image Filter](http://www.itk.org/SimpleITKDoxygen/html/classitk_1_1simple_1_1ConfidenceConnectedImageFilter.html) along with some post-processing on the binary image to fill holes/smooth edges. Pre-processing to enhance edges and decrease the chances of leaking into the background will be added.


Segmentation Example
-------

![Segmentation Example](Documentation/ExampleSegmentation.png?raw=true "Segmentation Example")


Usage
-------


To use as a Sliclet Application:

```
$/path/to/Slicer.exe --no-main-window --python-script /path/to/BoneSegmentation.py 
```

* Load image by the **Add Data** button (any Slicer acceptable image format can be used including Analyze and DICOM)
* Enable added fiducial markers (i.e. seed point) by clicking on the *Add Marker* button
* Add one seed point for each bone of interest 
* Select the volume in the **Input Volume** and click on **Compute**
* The segmentation will take ~45 seconds and will appear as a label type image overlaid onto the original image
* Save the segmentation by the **Save Data** button and selecting the corresponding image

To use as a Slicer Module:

* Open Slicer
* Edit -> Application Settings -> Modules
* Copy and paste both .py (python) files into the module path
* Or add a path to the folder using the "Additional Module Paths"
* Restart Slicer (the GUI is created on start up so restarting is needed when aded a new module)
* Use the fiduical marker module to create the seed points
* Select the volume in the **Input Volume** and click on **Compute**
* The segmentation will take ~45 seconds and will appear as a label type image overlaid onto the original image


Install Python Requirements
-------
Install pip (installation manager for adding python libraries)
```
python get-pip.py
```

Use the Requirements.txt to install only the needed libraries. This will also check the version number and update if needed.
```
pip install -r /path/to/requirements.txt
```

Build Commands
-------

Create Python Requirements.txt
-----

```
$pipreqs /path/to/project
```


Build Documentation using Sphinx
-----

``` 
cd /Documentation
make html
```

Build Documentation using Doxygen
-----

Use the Doxygen GUI (will use commands later if needed). Sphinx may be preferred

Version Number
-----

Will be following the [Semantic Versioning convention](http://semver.org/) where a given version number is  MAJOR.MINOR.PATCH, increment when:

0. MAJOR version when you make incompatible API changes,
0. MINOR version when you add functionality in a backwards-compatible manner, and
0. PATCH version when you make backwards-compatible bug fixes.

Additional labels for pre-release and build metadata are available as extensions to the MAJOR.MINOR.PATCH format.

Github Flow
-----

Branches will roughly follow this github work flow with three branches a Master that always contains working code, a release branch when working towards the next version, and a Develop branch for adding and fixing features.




![Example Github Flow](http://2.bp.blogspot.com/-yoWbDW3NmcU/U2Ph7o77BXI/AAAAAAAAAUQ/zlETRqFMHsk/s1600/git_workflow_gitflow.jpg)