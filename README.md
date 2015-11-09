BoneSegmentation
=============

Current Build Status for Master Branch
-------

![Current Build Status](https://img.shields.io/shippable/562c7f391895ca447420e213.svg?style=plastic)

Purpose 
-------

Segment the carpal bones from MR images given a set of user defined locations (seed points) within the image. It utilizes the open source [SimpleITK](http://www.simpleitk.org/) library which is a python wrapper for many [ITK](http://www.itk.org/) functions. 

Currently uses the [Confidence Connected Image Filter](http://www.itk.org/SimpleITKDoxygen/html/classitk_1_1simple_1_1ConfidenceConnectedImageFilter.html) along with some post-processing on the segmentation. Pre-processing to enhance edges and decrease the chances of leaking into the background will be added.


Segmentation Example
-------

![Segmentation Example](Documentation/ExampleSegmentation.png?raw=true "Segmentation Example")


Usage
-------


To use as a Sliclet Application:

```
$/path/to/Slicer.exe --no-main-window --python-script /path/to/BoneSegmentation.py 
```

To use as a Slicer Module:

* Open Slicer
* Edit -> Application Settings -> Modules
* Copy and paste both .py (python) files into the module path
* Or add a path to the folder using the "Additional Module Paths:"
* Restart Slicer (the GUI is created on start up so restarting is needed when aded a new module)

Add one fiducial marker (i.e. seed point) for each bone of interest. 

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


