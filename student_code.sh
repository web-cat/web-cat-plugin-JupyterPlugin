#!/bin/sh
umask 007
export PYTHONPATH=/plugin/student_dir/pythonlib:/plugin/work:/plugin/work/src
exec /opt/conda/envs/plugin/bin/python -m pythy.runner
