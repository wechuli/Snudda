#! /bin/bash

# loop over strings and cp/replace files

for dir in ../cellspecs/lts/*    # list directories in the form "/tmp/dirname/"
do
    # get dir only
    d2=`echo $dir | cut -c 17-`
    #echo $d2
    f2='../../Alex_model_repo/models/optim/'$d2'/config/'
    ls $f2
    echo
    #cp $f2 $dir
done
