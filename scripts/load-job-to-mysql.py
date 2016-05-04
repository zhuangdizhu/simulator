#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   Author  :   Hai Tao Yue
#   E-mail  :   bjhtyue@cn.ibm.com
#   Date    :   15/08/14 16:11:52
#   Desc    :
#
from __future__ import division
import sys
import numpy
import random
import os, errno
from mysql.connector import MySQLConnection,Error
from python_mysql_dbconfig import read_db_config



class JobInitiator(object):
    def __init__(self):
        self.dbconfig = read_db_config()
        self.conn = MySQLConnection(**self.dbconfig)
        self.job_node_list = list()
        self.fpga_available_node_list = list()
        self.fpga_non_available_node_list = list()
        self.acc_list = dict()


    def create_job_table(self):

        cursor = self.conn.cursor()
        try:
            query = "SELECT acc_id, acc_name, acc_peak_bw FROM acc_type_list"
            cursor.execute(query)
            accs = cursor.fetchall()
            for acc in accs:
                acc_id = acc[0]
                acc_name = acc[1]
                acc_peak_bw = float(acc[2])  # MBytes
                self.acc_list[acc_name] = (acc_id, acc_peak_bw)


            query = "SELECT node_ip FROM fpga_nodes"
            cursor.execute(query)
            node_tuple = cursor.fetchall()
            for node in node_tuple:
                self.job_node_list.append(node[0])
            #print node[0]

            query = "SELECT node_ip FROM fpga_nodes WHERE if_fpga_available = 1"
            cursor.execute(query)
            node_tuple = cursor.fetchall()
            for node in node_tuple:
                self.fpga_available_node_list.append(node[0])
            #print 'len = %r' %len(self.fpga_available_node_list)

            query = "SELECT node_ip FROM fpga_nodes WHERE if_fpga_available = 0"
            cursor.execute(query)
            node_tuple = cursor.fetchall()
            for node in node_tuple:
                self.fpga_non_available_node_list.append(node[0])

            query1 = "DROP TABLE IF EXISTS `fpga_jobs`"

            query2 = "CREATE TABLE `fpga_jobs`("\
                    "`job_id` int(11) NOT NULL,"\
                    "`in_buf_size` varchar(40) NOT NULL,"\
                    "`out_buf_size` varchar(40) NOT NULL,"\
                    "`acc_id` varchar(40) NOT NULL,"\
                    "`arrival_time` varchar(40) NOT NULL,"\
                    "`execution_time` varchar(40) NOT NULL,"\
                    "`from_node` varchar(40) NOT NULL,"\
                    "PRIMARY KEY (`job_id`))ENGINE=InnoDB  DEFAULT CHARSET=latin1"
            cursor.execute(query1)
            cursor.execute(query2)
        except Error as e:
            print e
        finally:
            cursor.close()



    def load_job(self, path, pattern, alpha, interval, nodeNum):
        query = "INSERT INTO fpga_jobs(job_id, in_buf_size, out_buf_size, acc_id, arrival_time, execution_time, from_node)"\
                "VALUES(%s, %s, %s, %s, %s, %s, %s)"
        cursor = self.conn.cursor()
        job_index = 0
        node_index = 3
        node_index = 0
        for root, dirs, files in os.walk(path):
            for file_name in files:
                for i in range(1,int(nodeNum)+1):
                #for i in range(4,int(nodeNum)+4):
                    node = "tian0"+str(i)
                    if node+"-"+pattern+"-alpha-"+str(float(alpha))+"-interval-"+str(float(interval))+".txt" in file_name:
                        print file_name
                        node_index += 1

                        file_path = os.path.join(root, file_name)
                        f = open(file_path, "r")
                        lines=f.readlines()
                        f.close()

                        arrival_time = 0
                        from_node = "tian0"+str(node_index)
                        for line in lines:
                            job_param = line.split()

                            in_buf_size = float(job_param[1])*4/1024 #M Bytes
                            out_buf_size = in_buf_size

                            acc_id = self.acc_list[job_param[0]][0]

                            arrival_time +=float(job_param[2])        # seconds

                            acc_bw = self.acc_list[job_param[0]][1]          # M bytes

                            execution_time = in_buf_size/acc_bw    # seconds

                            job_index += 1
                            job_id = str(job_index)

                            query_args=(job_id, str(in_buf_size), str(out_buf_size), acc_id, str(arrival_time), str(execution_time), from_node)
                            cursor.execute(query,query_args)
                            self.conn.commit()
            cursor.close()






if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit("Usage: "+sys.argv[0]+" <Distribution> <Alpha> <Interval> <NodeNum>")
        sys.exit(1)

    pattern = sys.argv[1]
    alpha = sys.argv[2]
    interval = sys.argv[3]
    nodeNum = sys.argv[4]
    job_initiator = JobInitiator()
    job_initiator.create_job_table()
    job_initiator.load_job("../sim_data", pattern, alpha, interval, nodeNum)


