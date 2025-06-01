#!/bin/bash
TARGET="proj/ex7"
if [[ "$1" == "trace" ]]; then
    # eval "./traceTest.sh fullTest.log case fullProgram ${@:2}"
    eval "./traceTest.sh fullTest.log case $TARGET ${@:2}"
else
    ./runTest.sh case $TARGET $@
fi