BoneSegmentation
=============

Current Build Status for Master Branch
-------

![Current Build Status](https://img.shields.io/shippable/562c7f391895ca447420e213.svg?style=plastic)


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




Create Python Requirements.txt
-------

```
$pipreqs /path/to/project
```

Build Documentation using Sphinx
-------

``` 
cd /Documentation
make html
```

Build Documentation using Doxygen
-------

Use the Doxygen GUI (will use commands later if needed). Sphinx may be preferred


