#!/bin/bash
usage() {
    echo "Usage:    ./group-job.sh [Pattern] [Alpha] [NodeNum] [JobNum] [Interval]"
    echo "Example:  ./group-job.sh Exp 400 10 10 4 1"
}

path=""
if [[ "$#" -eq "5" ]]; then
    Pattern=$1
    Alpha=$2
    NodeNum=$3
    JobNum=$4
    Interval=$5

    rm -rf jobInfo
    mkdir jobInfo

    for((i=1;i<=$NodeNum; i=i+1))
    do
        ./generate-job.py tian0$i $JobNum $Pattern $Alpha $Interval
    done

    ./load-job-to-mysql.py $Pattern $Alpha $Interval $NodeNum

else
    usage
fi
exit
