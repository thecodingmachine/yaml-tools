[![Build Status](https://travis-ci.org/thecodingmachine/yaml-tools.svg?branch=master)](https://travis-ci.org/thecodingmachine/yaml-tools)
[![Coverage Status](https://coveralls.io/repos/github/thecodingmachine/yaml-tools/badge.svg?branch=master)](https://coveralls.io/github/thecodingmachine/yaml-tools?branch=master)

# Yaml-tools

A set of CLI tools to manipulate YAML files (merge, delete, etc...) with comment preservation, based on [ruamel.yaml](http://yaml.readthedocs.io/en/latest/) 

## Getting Started

### Prerequisites
- Python3 (with pip)

### Installing
(For development see section at the end)
```
$ pip install ruamel.yaml
$ export YAML_TOOLS_VERSION=0.0.5
$ sudo wget https://raw.githubusercontent.com/thecodingmachine/yaml-tools/${YAML_TOOLS_VERSION}/src/yaml_tools.py -O /usr/local/bin/yaml-tools
$ sudo chmod +x /usr/bin/local/yaml-tools
```

## Usage
```
$ yaml-tools <command> [<args>] 
```

There are 3 commands at the moment :

### merge
Merges two or more yaml files and preserves the comments.
```
$ yaml-tools merge -i INPUTS [INPUTS ...] [-o OUTPUT]
```
- **INPUTS**: paths to input yaml files, which will be merged from the last to the first.
- **OUTPUT**: path to output yaml file (or sys.stdout by default).

### delete
Deletes one item/block (**and its preceding comments**) from the input yaml file.
```
$ yaml-tools delete PATH_TO_KEY -i INPUT [-o OUTPUT]
```
- **PATH_TO_KEY**: "path" to access the yaml item/block which will be deleted, e.g. `key1 0 key2`
- **INPUT**: path to input yaml file.
- **OUTPUT**: path to output yaml file (or sys.stdout by default).

### normalize-docker-compose
Normalize the input docker-compose file by and converting all key-value string (e.g. 'foo=bar' or '80:8080') 
to key-value dicts inside the services' `ports`, `labels` and `environment` fields,
and finally delete all duplicated volumes (**and its preceding comments**) for each services
```
$ yaml-tools normalize-docker-compose -i INPUT [-o OUTPUT]
```
- **INPUT**: path to input yaml file.
- **OUTPUT**: path to output yaml file (or sys.stdout by default).

### comment (/!\ EXPERIMENTAL)
Comments one item/block from the input yaml file and preserves the comments.

/!\ There are somme issues with comments which are at the end of any intermediate level/block, 
and also commenting the last item from a list, so use it with caution.
```
$ yaml-tools comment PATH_TO_KEY -i INPUT [-o OUTPUT]
```
- **PATH_TO_KEY**: "path" to access the yaml item which will be commented, e.g. `key1 0 key2`
- **INPUT**: path to input yaml file.
- **OUTPUT**: path to output yaml file (or sys.stdout by default).

## Development

### Installing
- Open a terminal console on this project's root folder
- Create a virtual environment with `python -m venv venv` (or `python3 -m venv venv`)
- Activate your venv with `.\venv\Scripts\activate` (Windows) or `source ./venv/bin/activate` (Linux or MacOS)
- Install all required packages with `pip install -r requirements.txt`

## Running tests
```
$ cd src/tests/

$ python -m unittest discover 
or
$ coverage run --rcfile=../../.coveragerc --source=.,.. -m unittest discover && coverage report -m
```
##
