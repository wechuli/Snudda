#! /bin/bash

# loop over strings and replace morphologies

for dir in ./cellspecs/fs/*    # list directories in the form "/tmp/dirname/"
do
    # get dir only
    d2=`echo $dir | cut -c 16-`
    #d2='../Johannes_model_repo/StriatumNetwork/model/'$dir
    d3='../Alex_model_repo/models/optim/'$d2'/morphology'
    f1=$dir'/*.swc'
    f2=$d3'/*.swc'
    ls $f1
    ls $f2
    diff -y $f1 $f2 > "diff"$c".txt"
    echo 
    #gedit $f1 $f2 &
    cp $f2 $f1
    let c=$c+1
done
