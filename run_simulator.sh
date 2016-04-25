#!/bin/bash
usage() {
    echo "Usage:    ./run_simulator.sh [Pattern] [Algorithm]"
    echo "Example:  ./run_simulator.sh Small FIFO"
}

if [[ "$#" -eq "2" ]]; then
    pattern=$1  #pattern = Small, Median, Large, Mixed
    algorithm=$2 #algorithm = FIFO, Queue, Choosy, Double
    mkdir -p simulate_log
    ./set_job.py $pattern
    #rm -rf simulate_log/$pattern
    #./set_system.py 1 2 10
    mkdir -p simulate_log/$pattern
    rm -rf simulate_log/$pattern/data_log
    ./simulation.py $algorithm 2 6 >> simulate_log/$pattern/data_log

    grep "OPEN" simulate_log/$pattern/data_log | awk '{print $4}' > simulate_log/$pattern/open.txt
    grep "EXE" simulate_log/$pattern/data_log | awk '{print $4}' > simulate_log/$pattern/execute.txt
    grep "CLOSE" simulate_log/$pattern/data_log |awk '{print $4}' > simulate_log/$pattern/close.txt
else
    usage
fi
exit


