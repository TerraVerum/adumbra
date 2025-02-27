# Xray Reconstruction and Layer Segmentation Tool

![Graphical interface](./interface.jpg)

A tool for converting 3D X-ray PCB volumes into 2D layer renderings. These individual
layers can be annoated through [S3A](https://github.com/TerraVerum/s3a) to indicate
netlist-specific information.

## Installation

Installation can be accomplished using pip:

```bash
# Clone this repo
git clone https://github.com/TerraVerum/xrayrecon.git

# Change directory to be inside the repo
cd xrayrecon

# Create conda env and activate it
conda create -n xrayrecon python=3.10 # only necessary first time, does not work with python 3.12 yet.
conda activate xrayrecon

# Install the package from the top-level directory of the repo
pip install -e .
```

## Running the App

The app can be started by running `main.py`:

```bash
python ./xrayrecon/main.py [--datafile /path/to/datafile.npy]

# Or, if xrayrecon is installed:
python -m xrayrecon.main [--datafile /path/to/datafile.npy]
```

If you have a folder with PCB data and slice information, uncomment the lines that read
in those files and run `main.py`.

Note you can run the other files for the purposes indicated in their filenames:

- convert (convert tif to .npy irrc)
- layerseg (segment layers)
- main (run GUI to look at segments, inspect the buttons and play around to get a feel for how this works)

Also note that the GUI breaks in WSL2 on Windows - TBD if it runs well on a dedicated linux workstation.
