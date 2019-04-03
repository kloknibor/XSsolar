import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
     name='XSsolar',  
     version='0.7',
     py_modules=['XSsolar'] ,
     author="Jorg Janssen & Robin Kolk ",
     author_email="robinkolk@msn.com",
     description="Communication for Mastervolt inverters",
     long_description=long_description,
   long_description_content_type="text/markdown",
     url="https://github.com/kloknibor/XSsolar",
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
 )