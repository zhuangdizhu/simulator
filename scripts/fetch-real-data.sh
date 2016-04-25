#!/bin/bash
usage() {
    echo "Mode Algorithm NodeNum"
}
if [[ "$#" -eq "3" ]]; then
    Mode=$1
    Algorithm=$2
    NodeNum=$3
    for ((i=1;i<=$NodeNum; i=i+1))
    do
        grep "OPEN" real_log/tian0$i-$Mode-$Algorithm.log | awk '{print $5}' >> real_log/tian0$i-$Mode-$Algorithm.txt
        grep "OPEN" real_log/tian0$i-$Mode-$Algorithm.log | awk '{print $7}' >> real_log/tian0$i-$Mode-$Algorithm.txt
        grep "OPEN" real_log/tian0$i-$Mode-$Algorithm.log | awk '{print $9}' >> real_log/tian0$i-$Mode-$Algorithm.txt
    done
else
    usage
fi

exit
