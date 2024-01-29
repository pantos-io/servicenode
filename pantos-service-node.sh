#! /bin/sh

# Python 3 interpreter
python=python3

script_path=`readlink -f "$0"`
src_dir_path=`dirname "$script_path"`

PYTHONPATH="$PYTHONPATH:$src_dir_path" $python -m pantos.servicenode "$@"
