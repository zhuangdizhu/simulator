#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   Author  :   Zhuang Di ZHU
#   E-mail  :   zhuangdizhu@yahoo.com
#   Date    :   15/09/28 15:05:07
#   Desc    :
#
from __future__ import division
import sys
import numpy
import random
import os
import math

class JobInitiator(object):
    def __init__(self, pattern, node):
        self.acc_type_list = ['AES','DTW','EC','FFT','SHA']
        self.pattern = pattern
        try:
            os.remove("job_data/"+node+"-"+pattern+".txt")
        except OSError:
            pass
        self.target = open("job_data/"+node+"-"+pattern+".txt",'a')

    def generate_job(self, job_num, Real):
        default_size = 1            #1KB
        ss_size = 1024              #4MB
        s_size  = 1024*256          #1GB
        m_size  = 1024*1024         #4GB
        l_size = 1024*2560          #10GB
        xl_size  = 2048*2560        #20GB


        node_num = 2;
        fpga_node_num = 1;
        pci_bw  = 1600;  #2800MB
        throughput = int(fpga_node_num * pci_bw *256 /node_num)/2


        mixed = {"small":0.5, "median":0.3, "large":0.2}
        job_list = [i for i in range(job_num)]
        job_param = dict()

        if Real == 1:
            scale = 1000000
        else:
            scale = 1

        if self.pattern == "Tiny":
            for i in job_list:
                acc_name = "AES"
                in_buf_size = ss_size
                arrival_time = int(math.ceil((in_buf_size/throughput)))*scale
                job_param[i] = (acc_name, in_buf_size, arrival_time)

        elif self.pattern == "Small":
            for i in job_list:
                acc_name = random.sample(self.acc_type_list,1)[0]
                acc_name = "AES"
                in_buf_size = random.randint(default_size, s_size)
                in_buf_size = s_size
                arrival_time = int(math.ceil((in_buf_size*scale/throughput)))
                arrival_time = int(math.ceil((in_buf_size/throughput)))*scale
                job_param[i] = (acc_name, in_buf_size, arrival_time)

        elif self.pattern == "Median":
            for i in job_list:
                acc_name = random.sample(self.acc_type_list,1)[0]
                acc_name = "AES"
                in_buf_size = random.randint(s_size+1, m_size)
                in_buf_size = m_size
                arrival_time = int(math.ceil((in_buf_size*scale/throughput)))
                arrival_time = int(math.ceil((in_buf_size/throughput)))*scale
                job_param[i] = (acc_name, in_buf_size, arrival_time)

        elif self.pattern == "Large":
            for i in job_list:
                acc_name = random.sample(self.acc_type_list,1)[0]
                acc_name = "AES"
                in_buf_size = random.randint(m_size+1, l_size)
                in_buf_size = l_size
                arrival_time = int(math.ceil((in_buf_size*scale/throughput)))
                arrival_time = int(math.ceil((in_buf_size/throughput)))*scale
                job_param[i] = (acc_name, in_buf_size, arrival_time)

        elif self.pattern == "Super":
            for i in job_list:
                acc_name = random.sample(self.acc_type_list,1)[0]
                acc_name = "AES"
                in_buf_size = random.randint(l_size+1, xl_size)
                in_buf_size = xl_size
                arrival_time = int(math.ceil((in_buf_size*scale/throughput)))
                arrival_time = int(math.ceil((in_buf_size/throughput)))*scale
                job_param[i] = (acc_name, in_buf_size, arrival_time)

        elif self.pattern == "Mixed":
            s_list = random.sample(job_list, int(job_num*mixed["small"]))
            job_list = list(set(job_list).difference(set(s_list)))
            m_list = random.sample(job_list, int(job_num*mixed["median"]))
            job_list = list(set(job_list).difference(set(m_list)))
            l_list = random.sample(job_list, int(job_num*mixed["large"]))
            job_list = list(set(job_list).difference(set(l_list)))
            for i in s_list:
                acc_name = random.sample(self.acc_type_list,1)[0]
                acc_name = "AES"
                in_buf_size = random.randint(default_size, s_size)
                in_buf_size = s_size
                arrival_time = int(math.ceil((in_buf_size*scale/throughput)))
                arrival_time = int(math.ceil((in_buf_size/throughput)))*scale
                job_param[i] = (acc_name, in_buf_size, arrival_time)

            for i in m_list:
                acc_name = random.sample(self.acc_type_list,1)[0]
                acc_name = "AES"
                in_buf_size = random.randint(s_size+1, m_size)
                in_buf_size = m_size
                arrival_time = int(math.ceil((in_buf_size*scale/throughput)))
                arrival_time = int(math.ceil((in_buf_size/throughput)))*scale
                job_param[i] = (acc_name, in_buf_size, arrival_time)

            for i in l_list:
                acc_name = random.sample(self.acc_type_list,1)[0]
                acc_name = "AES"
                in_buf_size = random.randint(m_size+1, l_size)
                in_buf_size = l_size
                arrival_time = int(math.ceil((in_buf_size*scale/throughput)))
                arrival_time = int(math.ceil((in_buf_size/throughput)))*scale
                job_param[i] = (acc_name, in_buf_size, arrival_time)

        else:
            for i in job_list:
                acc_name = random.sample(self.acc_type_list,1)[0]
                acc_name = "AES"
                in_buf_size = random.randint(default_size+1, xl_size)
                arrival_time = int(math.ceil((in_buf_size*scale/throughput)))
                arrival_time = int(math.ceil((in_buf_size/throughput)))*scale
                job_param[i] = (acc_name, in_buf_size, arrival_time)

        for i in sorted(job_param.keys()):
            term = job_param[i]
            self.target.write("%s %s %s \n" %(str(term[0]), str(term[1]), str(term[2])))

        print "job paramters created successfully. Please check 'job_data/%s-%s.txt'" %(node, pattern)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Usage: "+sys.argv[0]+" <Job_num> <Pattern> <Node> <ifReal>"
        print "Example:"+sys.argv[0]+" 10 Large r1 1"
        print "Example:"+sys.argv[0]+" 10 Mixed r1 0"
        sys.exit(1)
    job_num = int(sys.argv[1])
    pattern = sys.argv[2]
    node = sys.argv[3]
    ifReal = int(sys.argv[4])
    job_initiator = JobInitiator(pattern, node)
    job_initiator.generate_job(job_num, ifReal)

