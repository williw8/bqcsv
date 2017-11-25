#!/bin/bash
if [ 1 == $# ]; then
    mkdir bqcsv
    mkdir bqcsv/csvdb
    mkdir bqcsv/actions
    mkdir bqcsv/actions/join
    mkdir bqcsv/actions/select
    mkdir bqcsv/actions/colscript
    cp ../bqcsv.py bqcsv
    cp ../LICENSE bqcsv
    cp -r ../csvdb/* bqcsv/csvdb
    cp ../actions/* bqcsv/actions
    cp -r ../actions/join/* bqcsv/actions/join
    cp -r ../actions/select/* bqcsv/actions/select
    cp -r ../actions/colscript/* bqcsv/actions/colscript
    find bqcsv -name "*.pyc" -exec rm \{\} \; -print
    find bqcsv -name "*.git*" -exec rm \{\} \; -print
    name=$(date +%Y%m%d)
    name=$name"_bqcsv_"
    name=$name$1
    name="$name.zip"
    zip -r $name bqcsv
    rm -rf bqcsv 
else
    echo "usage: make_release.sh <version>"
fi
