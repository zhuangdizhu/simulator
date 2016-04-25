#!/bin/bash
usage() {
    echo "Usage:    ./group-job.sh [Pattern] [JobNum] [NodeNum] [Ratio] [PCIE_BW] "
    echo "Example:  ./group-job.sh Small 10 4 0.5 2000"
}

if [[ "$#" -eq "5" ]]; then
    Pattern=$1
    JobNum=$2
    NodeNum=$3
    Ratio=$4
    PCIeBW=$5
    rm -rf job_data
    mkdir job_data

    for((i=1;i<=$NodeNum; i=i+1))
    do
        ./generate-job.py $JobNum $Pattern tian0$i $PCIeBW $Ratio
    done

    ./set_job.py $Pattern

else
    usage
fi
exit
