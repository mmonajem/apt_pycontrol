# PyCCAPT 
# A modular, FAIR open-source python atom probe tomography control and calibration software package
![plot](pyccapt/files/logo.png)

Today, the vast majority of atom probe instruments in use are commercial systems with proprietary software. 
This is limiting for many experiments where low-level access to machine control or experiment result data is necessary.
In the beginning this package was implemented for the OXCART atom probe, which is an in-house atom probe. 
The unique feature of OXCART atom probe is that it has a measuring chamber made of titanium to generate a particularly low-hydrogen vacuum.
It was equipped with a highly efficient detector (approx. 80% detection efficiency). 
![plot](pyccapt/files/oxcart.png)
PyCCAPT package provides the basis of a fully FAIR atom probe data collection and analysis chain.  
This repository contains the GUI and control program, which control, visualize, and do the atom probe experiment.
The images below are an overview of the two version of user interface:
![plot](pyccapt/files/oxcart_gui.png)
![plot](pyccapt/files/physic_gui.png)

#  Installation
1- create the virtual environment via Anaconda:
    
    conda create -n myenv 

2- Activate the virtual environment:

    conda activate myenv

3- Install package locally:
    
    pip install -e .

# Edite GUI 

Edite the GUI with Qt-Designer and run command below to create your own GUI
UI (simple or advance) in the GUI module. 

    pyuic5 -x gui_simple_layout.ui -o gui_simple_layout.py. You should then merge the created file with the targeted 

# Running an experiment

modify the congig.json file. Type pyccapt in your command line.

# Citing 
TODO

