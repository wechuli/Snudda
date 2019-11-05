#! /bin/bash

# loop over strings and replace morphologies

for dir in ./cellspecs/lts/*    # list directories in the form "/tmp/dirname/"
do
    # get dir only
    #f1=$dir/prot*.json
    #d2=`echo $dir | cut -c 18-`
    d2='../Johannes_model_repo/StriatumNetwork/model/'$dir
    ls $dir
    #ls $f2
    ls $d2/mechan*.json
    echo 
    #cp $d2/*o*.json $dir
done
