# Minerva CLI

## Introduction

Minerva command line interface allows uploading and importing/exporting microscopy images to/from Minerva Cloud system.

## Configuration

Minerva will by default look for a file named .minerva in the user's home directory and load configuration from that file. Minerva needs the configuration to be able to connect to the correct Minerva service.

Arguments given in command line will override values set in the config file. Config file location may be overridden with argument --config [PATH]

There is an example config file provided. Copy .minerva.example as $HOME/.minerva, and open the file with a text editor to edit values. All the parameter values can also be set with environment variables.
- MINERVA_REGION = us-east-1 (aws region where Minerva is installed)
- MINERVA_USERNAME = Minerva Username
- MINERVA_PASSWORD = Minerva Password
- MINERVA_ENDPOINT = API Gateway stage URL, e.g. https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/dev
- MINERVA_CLIENT_ID = Cognito App client id for the user pool

### Show help
```
python minerva.py
```
## Import an image to Minerva Cloud
```bash
# Replace <REPOSITORY> with a repository name, and <DIRECTORY> with a path to a directory.
# All images from the directory and its subdirectories will be imported.

python minerva.py import -r <REPOSITORY> -d <DIRECTORY>
```

## Running on O2

### Installation
```bash
# Log in O2 with SSH
# Clone the minerva-cli repository
git clone https://github.com/labsyspharm/minerva-cli.git

# Load necessary modules (you may need to restart bash shell after running this the first time)
module load conda2

# Create conda environment
conda create --name minerva python=3.6
conda activate minerva
pip install -r requirements.txt

# Configure minerva.config
cp .minerva.example ~/.minerva
# Edit the values in config file
nano minerva.config
# It's a good idea to prevent other users from reading your configuration file
chmod 700 ~/.minerva
```

### Import images from ImStor to Minerva Cloud
```bash
# Log in O2 transfer node with SSH (replace ecommonsid with your eCommons user id)
ssh ecommonsid@transfer.rc.hms.harvard.edu
# Copy images from ImStor to scratch space, e.g.
mkdir -p /n/scratch3/$USER/dataset
cp /n/files/ImStor/.../image.ome.tif /n/scratch3/$USER/dataset

# Log in O2 with SSH
ssh ecommons@o2.hms.harvard.edu
# Start interactive O2 session
srun --pty -p interactive --mem 500M -t 0-06:00 /bin/bash

# Activate conda environment
conda activate minerva

# Run Minerva import
# (replace [REPOSITORY] with a repository name)
# All the images from the given directory will be imported
python $HOME/minerva-cli/minerva.py import -r [REPOSITORY] -d /n/scratch3/$USER/dataset
```

### Export OME-TIFF from Minerva Cloud to local disk
```bash
# The following command will export and save the image by its default name, and save only
# the highest pyramid level.
python minerva.py export --id [IMAGE_UUID]
```
