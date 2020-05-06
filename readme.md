# Minerva CLI

## Introduction

Minerva command line interface allows uploading and importing microscopy images to Minerva Cloud system.

## Configuration

Minerva will by default look for a file named minerva.config and load configuration from that file. Minerva needs the configuration to be able to connect to the correct Minerva environment.

Arguments given in command line will override values set in the config file. A differently named config file may be given with argument --config configfile

There is an example config file provided. Copy minerva.config.example as minerva.config, and open the file with a text editor to edit values.
### Show help
```
python minerva.py -h
```
## Import instructions
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
cp minerva.config.example minerva.config
# Edit the values in config file
vi minerva.config
# It's a good idea to hide the config file from other users
chmod 700 minerva.config
```

### Import images from ImStor to Minerva Cloud
```bash
# Log in O2 transfer node with SSH (replace ecommons with eCommons user id)
ssh ecommons@transfer.rc.hms.harvard.edu
# Copy images from ImStor to scratch space, e.g.
mkdir -p /n/scratch2/$USER/import
cp /n/files/ImStor/.../image.ome.tif /n/scratch2/$USER/import

# Log in O2 with SSH
ssh ecommons@o2.hms.harvard.edu
# Start interactive O2 session
srun --pty -p interactive --mem 500M -t 0-06:00 /bin/bash

# Activate conda environment
conda activate minerva

# Run Minerva import
# (replace <REPOSITORY> with a repository name)
# All the images from the given directory will be imported
python $HOME/minerva-cli/minerva.py import -r <REPOSITORY> -d /n/scratch2/$USER/import
```

