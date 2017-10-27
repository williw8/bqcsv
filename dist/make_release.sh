#!/bin/bash
if [ 1 == $# ]; then
    mkdir bqcsv
    mkdir bqcsv/csvdb
    mkdir bqcsv/actions
    mkdir bqcsv/actions/join
    mkdir bqcsv/actions/select
    cp ../bqcsv.py bqcsv
    cp ../LICENSE bqcsv
    cp -r ../csvdb/* bqcsv/csvdb
    cp ../actions/* bqcsv/actions
    cp ../actions/join/* bqcsv/actions/join
    cp ../actions/select/* bqcsv/actions/select
    $name = "bqcsv_"
    $name .= $1
    $name .= ".zip" 
    zip -r $name bqcsv
    rm -rf bqcsv 
else
    echo "usage: make_release.sh <version>"
fi
