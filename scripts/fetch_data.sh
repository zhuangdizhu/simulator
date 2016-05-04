#!/bin/bash

usage() {
    echo "Example: fetch_data.sh Exp 400 "
}

if [[ "$#" -eq "2" ]]; then
    pattern=$1
    mean=$2
    node=`hostname`
    node="tian03"
    #echo $mean $pattern $node
    t_file="../logInfo/fetched-sim-${pattern}-${mean}.csv"
    s_dir="../logInfo"

    s_file=`ls $s_dir|grep simlog |grep $pattern |grep ${mean}.log`
    echo $s_file

    avgFCT=`grep "Avg_Completion_Time" $s_dir/${s_file} | awk '{print $3}'`
    avgJob=`grep "Avg_Job_Size" $s_dir/${s_file} | awk '{print $3}'`
    SAP=`grep "System_Avg_Performance" $s_dir/${s_file} | awk '{print $5}'`
    SNP=`grep "System_Norm_Performance" $s_dir/${s_file} | awk '{print $3}'`
    DLocal=`grep "Data_Locality" $s_dir/${s_file} |awk '{print $3}'`
    tailFCT=`grep "Percentile_Completion_Time" $s_dir/${s_file} |awk '{print $8}'`

    #echo $avgFCT
    #echo $SAP
    #echo $SNP
    #echo $DLocal
    #echo $tailFCT
    avgJobArray=($avgJob)
    avgFCTArray=($avgFCT)
    SAPArray=($SAP)
    SNPArray=($SNP)
    DLocalArray=($DLocal)
    tailFCTArray=($tailFCT)

    len=${#avgJobArray[@]}
    len=$(($len-1))
    #echo $len

    echo "${avgJobArray},${avgFCTArray},${tailFCTArray},${SAPArray},${SNPArray},${DLocalArray}" > $t_file
    for ((i=1; i<=$len; i++));do
        echo "${avgJobArray[$i]},${avgFCTArray[$i]},${tailFCTArray[$i]},${SAPArray[$i]},${SNPArray[$i]},${DLocalArray[$i]}" >> $t_file
    done
else
    usage
fi

exit
