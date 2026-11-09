#!/bin/bash
set -e

export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export PYTHONPATH="$(pwd):${PYTHONPATH}"

python -m pytest -v
