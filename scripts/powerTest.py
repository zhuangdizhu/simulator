#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   Author  :   Zhuang Di ZHU
#   E-mail  :   zhuangdizhu@yahoo.com
#   Date    :   16/04/28 20:26:12
#   Desc    :
#

#Usage:    ./group-job.sh [Pattern] [Alpha] [NodeNum] [JobNum] [Interval]
#Usage: ./set_system.py <fpga_node_num> <total_node_num> <NIC_bw> <PCIe_bw>
#Usage: ./load-job-to-mysql.py <Distribution> <Alpha> <Interval> <NodeNum>

import os
params = list()#alpha: (interval, k1, k2, q)
#params.append((100, 0.125, 1, 21, 1.41))
#params.append((400, 0.5, 1, 21, 1.31))
#params.append((1000,1.25,1, 21, 1.48))
params.append((0.1, 0.5, 1, 24, 1.4))
params.append((0.2, 0.5, 9, 24, 1.414))
params.append((0.3, 0.5, 15, 24, 1.414))
params.append((0.4, 0.5, 1, 2, 1.414))
params.append((0.5, 0.5, 1, 2, 1.414))

algorithms = ['FIFO','SJF','Queue','Choosy','Double']
pattern = "Power"
fpga_node_num = 5
nodeNum = 10
jobNum = 50
pcieBw = 2100
nicBw = 1200
os.system('rm -rf ../logInfo/tmplog')

cmd = "./set_system.py "+str(fpga_node_num)+" "+str(nodeNum)+" "+str(nicBw)+" "+str(pcieBw)+" >> ../logInfo/tmplog"
print cmd
os.system(cmd)

for tuples in params:
    alpha = tuples[0]
    interval = tuples[1]
    k1  = tuples[2]
    k2  = tuples[3]
    q   = tuples[4]
    cmd = "./group-job.sh "+pattern+" "+str(alpha)+" "+str(nodeNum)+" "+str(jobNum)+" "+str(interval)+" >> ../logInfo/tmplog"
    print cmd
    os.system(cmd)

    cmd = "./load-job-to-mysql.py "+pattern+" "+str(alpha)+" "+str(interval)+" "+str(nodeNum)+" >> ../logInfo/tmplog"
    print cmd
    os.system(cmd)

    cmd="rm -rf ../logInfo/simlog-%s-%s.log" %(str(pattern), str(alpha))
    os.system(cmd)
    for al in algorithms:
        cmd="../simulation.py %s %s %s %s >> ../logInfo/simlog-%s-%s.log" %(al, str(k1), str(k2),str(q), str(pattern), str(alpha))
        print cmd
        os.system(cmd)


