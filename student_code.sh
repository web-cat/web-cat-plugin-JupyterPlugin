#!/bin/sh
export PYTHONPATH=/plugin/student_home:/plugin/work:/plugin/work/src
exec /opt/conda/envs/plugin/bin/python -m pythy.runner
