#!/bin/bash
if [[ "$#" -eq "3" ]]; then
    pattern=$1
    jobNum=$2
    nodeNum=$3
    for ((i=1;i<=$nodeNum; i=i+1))
    do 
        ./generate_job.py $jobNum $pattern tian0$i
    done

    ./set_job.py $pattern

else
    echo "Usage: [Pattern|Small|Median] [JobNum] [NodeNum] "
fi

exit
