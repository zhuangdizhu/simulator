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
import scipy.io as sio
import random
import os
import math
from math import e

class JobInitiator(object):
    def __init__(self, pattern, alpha, node, mean_interval):
        self.acc_type_list = ['AES', 'DTW', 'EC', 'FFT', 'SHA']
        #self.acc_type_list = ['AES']
        self.pattern = pattern
        self.alpha = alpha
        self.mean_interval = mean_interval

        self.path = "../sim_data/"

        try:
            os.remove(self.path+node+"-"+pattern+"-alpha-"+str(alpha)+"-interval-"+str(mean_interval)+".txt")
        except OSError:
            pass
        self.target = open(self.path+node+"-"+pattern+"-alpha-"+str(alpha)+"-interval-"+str(mean_interval)+".txt",'a')

    def generate_job(self, job_num, node, pattern, alpha, mean_interval):

        job_list = [i for i in range(job_num)]
        job_param = dict()

        if self.pattern == "Exp":
            #job_size = [numpy.random.exponential(self.alpha, job_num)
            job_size = [float("%.6f" %numpy.random.exponential(self.alpha)) for i in range(job_num)]
            #job_size = [self.alpha for i in range(job_num)]
            arrival_time = 0
            for i in job_list:
                acc_name = random.sample(self.acc_type_list,1)[0]
                in_buf_size = job_size[i] * 256  #4K bytes
                #arrival_time = self.mean_interval
                arrival_time = float("%.5f" %numpy.random.exponential(self.mean_interval))

                job_param[i] = (acc_name, in_buf_size, arrival_time)

        elif self.pattern == "Power":
            y_list = [float("%.6f" %random.uniform(0,1)) for i in range(job_num)]
            file_path = "../sim_data/"+node+"/"+str(float(alpha))+"-jobsize.mat"

            matConent = sio.loadmat(file_path)
            job_size = matConent['RetArr'][0]
            #print job_size
            #job_size = [float("%.6f" %self.inverse_cdf(alpha,y)) for y in y_list]
            arrival_time = 0
            for i in job_list:
                acc_name = random.sample(self.acc_type_list,1)[0]
                in_buf_size = job_size[i] * 256  #4K bytes
                arrival_time = float("%.5f" %numpy.random.exponential(self.mean_interval))
                job_param[i] = (acc_name, in_buf_size, arrival_time)

        else:
            print "Wrong Distribution Pattern. Pattern should be 'Exp' or 'Power\n"
            return


        for i in sorted(job_param.keys()):
            term = job_param[i]
            self.target.write("%s %s %s \n" %(str(term[0]), str(term[1]), str(term[2])))


    def inverse_cdf(self,alpha,y):
        s0 = 10         #MBytes
        smax = 1024*10     #10GBytes
        x = (s0*(e**0))/(y*((s0/smax)**alpha - 1) + 1)**(1/alpha)
        return x
if __name__ == "__main__":
    if len(sys.argv) != 6:
        print "Usage: "+sys.argv[0]+" <HostName> <Job_num> <Distribution /Exp or Power> <SizeAlpha /MB> <ArrivalAlpha /Seconds>"
        print "Example:"+sys.argv[0]+" tian01 10 Exp 400 1"
        sys.exit(1)

    node = sys.argv[1]
    job_num = int(sys.argv[2])
    pattern = sys.argv[3]
    alpha = float(sys.argv[4])
    mean_interval = float(sys.argv[5])
    job_initiator = JobInitiator(pattern, alpha, node, mean_interval)
    job_initiator.generate_job(job_num, node, pattern, alpha, mean_interval)

