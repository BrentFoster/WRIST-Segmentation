from distutils.core import setup
#from distutils.core import setup
# from setuptools import setup

setup(name='BrentsTools',
	version='1.0',
	packages=['BrentPython'],
	install_requires=['SimpleITK >= 0.8.0', 'numpy'],
	license='MIT',
	long_description=open('README.txt').read(),
	)

