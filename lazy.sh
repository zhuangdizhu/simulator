#! /bin/bash

for ((i=1;i<=3; i=i+1))
do
    rm -rf Pattern2$i
    mkdir Pattern2$i
    touch Pattern2$i/mixed.log
    ./set_system.py $i 10 20
    ./simulation.py FIFO 9 11 6 >> Pattern2$i/mixed.log 
    ./simulation.py SJF 9 11 6 >> Pattern2$i/mixed.log 
    ./simulation.py Queue 9 11 6 >> Pattern2$i/mixed.log 
    ./simulation.py Choosy 9 11 6 >> Pattern2$i/mixed.log 
    ./simulation.py Double 9 11 6 >> Pattern2$i/mixed.log 
done
