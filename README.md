[![Build Status](https://travis-ci.org/thecodingmachine/yaml-tools.svg?branch=master)](https://travis-ci.org/thecodingmachine/yaml-tools)
[![Coverage Status](https://coveralls.io/repos/github/thecodingmachine/yaml-tools/badge.svg?branch=master)](https://coveralls.io/github/thecodingmachine/yaml-tools?branch=master)

# Yaml-tools

A set of CLI tools to manipulate YAML files (merge, delete, etc...) with comment preservation, based on [ruamel.yaml](http://yaml.readthedocs.io/en/latest/) 

## Getting Started

### Prerequisites
- Python (with pip)

### Installing
(For development see section at the end)
```
$ pip install ruamel.yaml
$ export YAML_TOOLS_VERSION=0.2.0
$ sudo wget https://raw.githubusercontent.com/thecodingmachine/yaml-tools/${YAML_TOOLS_VERSION}/src/yaml_tools.py -O /usr/local/bin/yaml-tools
$ sudo chmod +x /usr/bin/yaml-tools
```

## Usage
```
$ yaml-tools <command> [<args>] 
```

There are only 2 commands at the moments :

### merge
Merge two or more yaml files and preserve the comments
```
$ yaml-tools merge -i INPUTS [INPUTS ...] [-o OUTPUT] [--indent INDENT]
```
- INPUTS: paths to input yaml files, which will be merged from the last to the first.
- OUTPUT: path to output yaml file (or sys.stdout by default).
- INDENT: number of space(s) for each indent.

### delete
Delete one item from the input yaml file
```
$ yaml-tools delete ITEM_PATH -i INPUT [-o OUTPUT] [--indent INDENT]
```
- ITEM_PATH: yaml item to be deleted, e.g. `key1.list[0].key2`
- INPUT: path to input yaml file.
- OUTPUT: path to output yaml file (or sys.stdout by default).
- INDENT: number of space(s) for each indent.

## Development

### Installing
- Open a terminal console on this project's root folder
- Create a virtual environment with `python -m venv venv` (or `python3 -m venv venv`)
- Activate your venv with `.\venv\Scripts\activate` (Windows) or `source ./venv/bin/activate` (Linux or MacOS)
- Install all required packages with `pip install -r requirements.txt`

## Running the tests
```
$ cd src/tests/
$ python -m unittest discover
```
##
