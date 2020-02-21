# Minerva CLI

## Introduction

Minerva command line interface allows uploading and importing microscopy images to Minerva Cloud system.

### Show help

python minerva.py -h

## Import instructions

python minerva.py import -r REPOSITORY_NAME -d DIRECTORY

## Configuration file

Minerva will by default look for a file named minerva.config and load configuration from that file. Arguments given in command line will override values set in the config file. A differently named config file may be given with argument --config configfile