#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   Author  :   Hai Tao Yue
#   E-mail  :   bjhtyue@cn.ibm.com
#   Date    :   15/08/05 15:39:56
#   Desc    :
#
from __future__ import division
import uuid
import math
import random
import sys
import numpy as np
from collections import namedtuple
from collections import defaultdict
from enum import Enum
from mysql.connector import MySQLConnection,Error
from python_mysql_dbconfig import read_db_config
global local_open, remote_open, local_close, remote_close, CHUNK_SIZE

local_open = 1340/(10**6)       #seconds
remote_open = 2110/(10**6)      #seconds
local_close = 600/(10**6)       #seconds
remote_close = 900/(10**6)      #seconds
CHUNK_SIZE = 4 #4M Bytes, i.e 1024 *4 Kbyte


#global i
#i = 0

AccType = namedtuple('AccType',['acc_id', 'acc_name', 'acc_peak_bw', 'if_flow_intensive', 'acc_configuration_time'])
EventType = Enum('EventType','JOB_ARRIVAL JOB_BEGIN JOB_START JOB_FINISH JOB_COMPLETE JOB_END')
SchedulingAlgorithm = Enum('SchedulingAlgorithm','SJF FIFO Queue Choosy Choosy1 Double Double1')
class FpgaEvent(object):
    def __init__(self, event_id, event_type, event_time='', job_id='', section_id=''):
        self.event_type = event_type
        self.event_time = event_time
        self.job_id = job_id
        self.section_id = section_id

class FpgaJob(object):
    def __init__(self,
                 job_id,
                 real_in_buf_size,
                 job_acc_id,
                 job_arrival_time,
                 theory_job_execution_time,
                 node_ip):
        self.job_id = job_id
        self.real_in_buf_size = real_in_buf_size

        self.job_in_buf_size = min(real_in_buf_size, CHUNK_SIZE)
        self.job_out_buf_size = self.job_in_buf_size
        self.job_finished_buf_size = 0

        self.job_acc_id = job_acc_id
        self.theory_job_execution_time = theory_job_execution_time
        self.chunk_execution_time = 0
        self.node_ip = node_ip
        self.section_id = 0

        self.job_configuration_time = 0.0
        self.job_arrival_time = job_arrival_time
        self.job_begin_time = 0
        self.job_start_time = 0
        self.job_finish_time = 0
        self.job_complete_time = 0
        self.job_end_time = 0
        self.job_associate_event_list = [0,0,0,0,0,0]
        #each element in the list is a tuple: (event_id,event_time)

        self.job_anp = 0
        self.job_ideal_time = 0
        self.job_real_time = 0
        self.job_source_transfer_time = 0
        self.job_result_transfer_time = 0
        self.job_if_local = True
        self.if_configured = 0
        self.current_roce_bw = 0

        self.job_total_transfer_time = 0
        self.job_waiting_time = 0
        self.job_response_time = 0
        self.job_skipped = 0

    def set_job_arrival_event(self, event_id):
        self.job_associate_event_list[0]=(event_id, self.job_arrival_time)


class FpgaSection(object):
    def __init__(self,section_id, node_associate_id, node_ip, compatible_acc_list,
                 current_acc_id='',
                 current_acc_bw='',
                 current_job_id=''):
        self.section_id = section_id
        self.node_associated_id = node_associate_id
        self.node_ip = node_ip
        self.if_idle = True
        self.compatible_acc_list = list()
        for acc in compatible_acc_list:
            self.compatible_acc_list.append(acc)

        self.current_acc_id = current_acc_id
        self.current_acc_bw = current_acc_bw
        self.current_job_id = current_job_id


class PowerNode(object):
    def __init__(self, node_id, node_ip, if_fpga_available, section_num, pcie_bw, roce_bw, roce_latency):
        self.node_id = node_id
        self.node_ip = node_ip
        self.if_fpga_available = if_fpga_available
        self.section_num = section_num
        self.pcie_bw = pcie_bw
        self.roce_bw = roce_bw
        self.roce_latency = roce_latency
        self.section_id_list = list()


class FpgaSimulator(object):
    def __init__(self, scheduling_algorithm, k1, k2, middleNum):

        self.k1 = k1
        self.k2 = k2
        self.middleNum = middleNum
        #self.wait_ratio = WaitRatio
        self.event_sequence = defaultdict(list)
        self.waiting_job_list=list()#the first element in the waiting_job_list must have wait the longest time
        self.sjf_job_list=dict() #job_id: theory_job_execution_time
        self.priority_queue = defaultdict(list)
        self.event_list = dict()#indexed by event_id
        self.acc_type_list = dict()#indexed by acc_id
        self.fpga_job_list =dict()#indexed by job_id
        self.fpga_section_list =dict()#indexd by section_id
        self.node_list = dict()#indexed by node_ip
        self.network_topology = list()
        self.current_time = 0
        self.current_event_id = 0
        self.current_event_type = 0
        self.current_job_id = 0
        self.network_real_workload = 0
        self.network_ideal_workload = 0
        self.sap = 0 #this is the ratio of theory estimated execution time/real completion time, larger the better
        self.snp = 0 #standard deviation of system average performance
        self.make_span = 0
        self.ssp = 0
        self.execution_average = 0
        self.ideal_execution_average = 0
        self.reconfiguration_num = 0

        self.bw = list()
        self.scheduling_algorithm = scheduling_algorithm
        self.dbconfig = read_db_config()
        self.conn = MySQLConnection(**self.dbconfig)

    def update_bw(self, source, dest):
        n = len(self.network_topology)
        B = [([0]*n) for i in range(n)]
        self.bw = [[0 for j in range(n)] for i in range(n)]
        row = [1 for i in range(n)]
        coloum = [1 for i in range(n)]
        flow = 1

        for i in range(n):
            for j in range(n):
                B[i][j] = self.network_topology[i][j]
                if B[i][j] < 0:
                    print "WRONG INPUT "
                    return
        while (flow > 0):
            flow = 0
            #update bw for flow (x,y) where x = source or y = dest
            row_min_bw = 1.1
            co_min_bw = 1.1
            row_id = 0
            co_id = 0
            for i in range(n):
                row_flow_num = 0
                for j in range(n):
                    row_flow_num += B[i][j]
                if row_flow_num != 0:
                    c_bw = row[i]/row_flow_num
                    if c_bw < row_min_bw:
                        row_min_bw = c_bw
                        row_id = i

            for j in range(n):
                co_flow_num = 0
                for i in range(n):
                    co_flow_num += B[i][j]
                if co_flow_num != 0:
                    c_bw = coloum[j]/co_flow_num
                    if c_bw < co_min_bw:
                        co_min_bw = c_bw
                        co_id = j

            if row_min_bw < co_min_bw:
                row[row_id] = 0
                for j in range(n):
                    if B[row_id][j] != 0:
                        self.bw[row_id][j] = row_min_bw
                        if row_min_bw == 0:
                            print "err1"
                        coloum[j] -= row_min_bw * B[row_id][j]
                        B[row_id][j] = 0

            else:
                coloum[co_id] = 0
                for i in range(n):
                    if B[i][co_id] != 0:
                        self.bw[i][co_id] = co_min_bw
                        if co_min_bw == 0:
                            print "err2"
                        row[i] -= co_min_bw * B[i][co_id]
                        B[i][co_id] = 0
            for i in range(n):
                for j in range(n):
                    flow += B[i][j]

        return self.bw[source][dest]

    def get_debug_info(self):
        try:
            raise Exception
        except:
            f = sys.exc_info()[2].tb_frame.f_back
        return (f.f_code.co_name, f.f_lineno)

    def insert_event(self, job_id, event_type):
        event_time = 0
        event_id = 0
        job = self.fpga_job_list[job_id]

        if event_type == EventType.JOB_ARRIVAL:
            event_time = job.job_arrival_time
            event_id = job.job_associate_event_list[0][0]

        elif event_type == EventType.JOB_BEGIN:
            event_time = job.job_begin_time
            event_id = job.job_associate_event_list[1][0]

        elif event_type == EventType.JOB_START:
            event_time = job.job_start_time
            event_id = job.job_associate_event_list[2][0]

        elif event_type == EventType.JOB_FINISH:
            event_time = job.job_finish_time
            event_id = job.job_associate_event_list[3][0]

        elif event_type == EventType.JOB_COMPLETE:
            event_time = job.job_complete_time
            event_id = job.job_associate_event_list[4][0]

        elif event_type == EventType.JOB_END:
            event_time = job.job_end_time
            event_id = job.job_associate_event_list[5][0]

        else:
            print 'ERROR! No such event type'
            pass

        self.event_sequence[event_time].append(event_id)
        self.event_list[event_id] = FpgaEvent(event_id, event_type, event_time, job_id)


    def remove_old_event(self,job_id,event_type,obsolete_event_time):
        event_time = obsolete_event_time
        event_id = 0
        job = self.fpga_job_list[job_id]
        if event_type == EventType.JOB_ARRIVAL:
            #event_time = job.job_arrival_time
            event_id = job.job_associate_event_list[0][0]

        elif event_type == EventType.JOB_BEGIN:
            #event_time = job.job_begin_time
            event_id = job.job_associate_event_list[1][0]

        elif event_type == EventType.JOB_START:
            #event_time = job.job_start_time
            event_id = job.job_associate_event_list[2][0]

        elif event_type == EventType.JOB_FINISH:
            #event_time = job.job_finish_time
            event_id = job.job_associate_event_list[3][0]

        elif event_type == EventType.JOB_COMPLETE:
            #event_time = job.job_complete_time
            event_id = job.job_associate_event_list[4][0]

        elif event_type == EventType.JOB_END:
            #event_time = job.job_end_time
            event_id = job.job_associate_event_list[5][0]

        else:
            pass

        for i, c_event_id in enumerate(self.event_sequence[event_time]):
            if event_id == c_event_id:
                del(self.event_sequence[event_time][i])
                if len(self.event_sequence[event_time])==0:
                    del(self.event_sequence[event_time])
                del(self.event_list[event_id])
                break
        return event_id

    def remove_current_event(self):

        del(self.event_sequence[self.current_time][0])
        if len(self.event_sequence[self.current_time])==0:
            del(self.event_sequence[self.current_time])
        del(self.event_list[self.current_event_id])
        #print "remaining event num:"
        #print 'remaining event number is %r' % (len(self.event_list))
        #for event_time, event_id_list in self.event_sequence.items():
        #    print event_time
        #    for event_id in event_id_list:
        #        print event_id


    def initiate_available_acc_type_list(self):
        cursor = self.conn.cursor()
        query = "SELECT acc_id, acc_name, acc_peak_bw ,if_flow_intensive FROM acc_type_list"
        try:
            cursor.execute(query)
            accs = cursor.fetchall()
            for acc in accs:
                acc_peak_bw = float(acc[2])  # MBytes
                self.acc_type_list[acc[0]] = AccType(acc[0], acc[1], acc_peak_bw, acc[3], 0)
        except Error as e:
            print(e)

        finally:
            cursor.close()


    def initiate_node_status(self):
        cursor = self.conn.cursor()
        query = "select id, node_ip, pcie_bw, if_fpga_available, section_num, roce_bw, roce_latency FROM fpga_nodes"
        #self.node_list['localhost'] = PowerNode('localhost',4, 1.2*1024)
        try:
            cursor.execute(query)
            nodes = cursor.fetchall()
            #print('Total fpga_node(s):', cursor.rowcount)
            for node in nodes:
                node_id = int(node[0])-1        #starts from 0
                node_ip = node[1]
                pcie_bw = float(node[2])        #M bytes
                if_fpga_available = int(node[3])
                section_num = int(node[4])
                roce_bw = float(node[5])        # M bytes
                roce_latency = float(node[6])   #secs
                self.node_list[node_ip] = PowerNode(node_id, node_ip, if_fpga_available, section_num, pcie_bw, roce_bw, roce_latency)

                if if_fpga_available == 1:
                    for i in range(section_num):
                        #print i
                        section_id = node_ip+":section"+str(i)
                        #print section_id
                        self.node_list[node_ip].section_id_list.append(section_id)

        except Error as e:
            print(e)

        finally:
            cursor.close()


    def initiate_fpga_resources(self):
        cursor = self.conn.cursor()
        query = "SELECT acc_id FROM fpga_resources WHERE node_ip = %s AND section_id = %s"
        try:
            #print "len = %r" %len(self.node_list)
            for node_ip, node in self.node_list.items():
                #print "node_ip = %r" %node_ip
                #print "section_num = %r" %node.section_num
                for i in range(node.section_num):
                    #print "i=%r" %i
                    compatible_acc_list = list()
                    section_id = node_ip+":section"+str(i)
                    #print "section_id = %r" %section_id
                    query_args = (node_ip, section_id)
                    cursor.execute(query,query_args)
                    acc_list = cursor.fetchall()
                    #print "acc_list =%r" %len(acc_list)
                    for acc in acc_list:# acc=(acc_id,)
                        #print "acc=%r,%r" %(acc,type(acc))
                        compatible_acc_list.append(acc[0])
                    #print "%r,%r" %(section_id, acc_list)
                    self.fpga_section_list[section_id] = FpgaSection(section_id, i, node_ip, compatible_acc_list)

        except Error as e:
            print(e)

        finally:
            cursor.close()


    def initiate_job_status(self):
        cursor = self.conn.cursor()
        try:
            query = "SELECT * FROM fpga_jobs"
            cursor.execute(query)
            job_list = cursor.fetchall()
            for i, job in enumerate(job_list):
                job_id = i  #starts from 1
                in_buf_size = float(job[1]) #M bytes
                acc_id = job[3]
                arrival_time = float(job[4]) #secs
                #print arrival_time
                execution_time = float(job[5]) #secs
                from_node = job[6]
                self.fpga_job_list[job_id] = FpgaJob(job_id,
                                                     in_buf_size,
                                                     acc_id,
                                                     arrival_time,
                                                     execution_time,
                                                     from_node)

                job_acc_bw = self.acc_type_list[acc_id].acc_peak_bw
                #print "job_acc_bw %r" %job_acc_bw

                self.fpga_job_list[job_id].chunk_execution_time = CHUNK_SIZE/job_acc_bw

        except Error as e:
            print e

    #    finally:
    #        cursor.close()


    def initiate_events(self):
        #for job_id,job in self.fpga_job_list.items():
        for i in range(len(self.fpga_job_list)):
            job_id = sorted(self.fpga_job_list.iterkeys())[i]
            arrival_event_id = "job"+str(job_id)+"arrival"
            self.fpga_job_list[job_id].set_job_arrival_event(arrival_event_id)
            #print 'initiate_event:job_id =%r' % job_id

            self.insert_event(job_id, EventType.JOB_ARRIVAL)


    def initiate_network_topology(self):
        node_num = len(self.node_list)
        self.network_topology = [([0]* node_num)for i in range(node_num)]
        self.bw = [[0 for j in range(node_num)] for i in range(node_num)]


    def update_job_info(self, job_id):
        job_acc_id = self.fpga_job_list[job_id].job_acc_id
        job_acc_bw = self.acc_type_list[job_acc_id].acc_peak_bw
        #print "job_acc_bw %r" %job_acc_bw

        chunk = min(CHUNK_SIZE,
                    self.fpga_job_list[job_id].real_in_buf_size - self.fpga_job_list[job_id].job_finished_buf_size)

        self.fpga_job_list[job_id].job_in_buf_size = chunk
        self.fpga_job_list[job_id].job_out_buf_size = chunk

        self.fpga_job_list[job_id].job_start_time = 0
        self.fpga_job_list[job_id].job_finish_time = 0
        #self.fpga_job_list[job_id].job_begin_time = 0
        #self.fpga_job_list[job_id].job_complete_time = 0



    def conduct_fifo_scheduling(self):
        if self.current_event_type == EventType.JOB_ARRIVAL:
            return_section_id = None
            job_id = self.current_job_id
            job_node_ip = self.fpga_job_list[job_id].node_ip
            node_ip = self.pick_idle_node()
            if node_ip != None:
                return_section_id =self.pick_idle_section(node_ip)
            return return_section_id

        elif self.current_event_type == EventType.JOB_END:
            return_job_id = None
            if len(self.waiting_job_list):
                section_id = self.fpga_job_list[self.current_job_id].section_id
                section_node_ip = self.fpga_section_list[section_id].node_ip

                return_job_id = self.waiting_job_list[0]
                self.remove_job_from_queue(return_job_id)

            return return_job_id


    def remove_job_from_queue(self, job_id):
        self.waiting_job_list.remove(job_id)

        if self.scheduling_algorithm == SchedulingAlgorithm.FIFO:
            return

        if self.scheduling_algorithm == SchedulingAlgorithm.SJF:
            del(self.sjf_job_list[job_id])
            return

        if self.scheduling_algorithm == SchedulingAlgorithm.Choosy:
            return

        if self.scheduling_algorithm == SchedulingAlgorithm.Choosy1:
            return
        else:
            queue_id = self.get_queue_id(job_id)
            self.priority_queue[queue_id].remove(job_id)


    def conduct_double_scheduling(self):
        if self.current_event_type == EventType.JOB_ARRIVAL:
            return self.conduct_choosy_scheduling()

        elif self.current_event_type == EventType.JOB_END:
            return_job_id = None
            if len(self.waiting_job_list):
                section_id = self.fpga_job_list[self.current_job_id].section_id
                section_node_ip = self.fpga_section_list[section_id].node_ip
                less_optimal_jobs = list()

                queue_id_list = sorted(self.priority_queue.iterkeys())
                for queue_id in queue_id_list:
                    if len(self.priority_queue[queue_id]):
                        for job_id in self.priority_queue[queue_id]:
                            job_node_ip = self.fpga_job_list[job_id].node_ip
                            if job_node_ip == section_node_ip or self.node_list[job_node_ip].if_fpga_available == False:
                                return_job_id = job_id
                                self.remove_job_from_queue(return_job_id)
                                return return_job_id

                            else:
                                less_optimal_jobs.append(job_id)

                if len(less_optimal_jobs):
                    return_job_id =  less_optimal_jobs[0]
                    self.remove_job_from_queue(return_job_id)
                    return return_job_id

            return return_job_id

    def conduct_double1_scheduling(self):
        if self.current_event_type == EventType.JOB_ARRIVAL:
            return self.conduct_choosy1_scheduling()

        elif self.current_event_type == EventType.JOB_END:
            return_job_id = None
            if len(self.waiting_job_list):
                section_id = self.fpga_job_list[self.current_job_id].section_id
                section_node_ip = self.fpga_section_list[section_id].node_ip
                less_optimal_jobs = list()

                queue_id_list = sorted(self.priority_queue.iterkeys())
                for queue_id in queue_id_list:
                    if len(self.priority_queue[queue_id]):
                        for job_id in self.priority_queue[queue_id]:
                            job_node_ip = self.fpga_job_list[job_id].node_ip
                            if job_node_ip == section_node_ip or self.node_list[job_node_ip].if_fpga_available == False:
                                return_job_id = job_id
                                self.remove_job_from_queue(return_job_id)
                                return return_job_id
                            else:
                                if self.if_wait_long_time(job_id) == True:
                                    return_job_id =  job_id
                                    self.remove_job_from_queue(return_job_id)
                                    return return_job_id
                                else:
                                    self.fpga_job_list[job_id].job_skipped += 1
                                    less_optimal_jobs.append(job_id)

                if len(less_optimal_jobs):
                    return_job_id =  less_optimal_jobs[0]
                    self.remove_job_from_queue(return_job_id)

            return return_job_id


    def if_wait_long_time(self, job_id):
        weight = 0.1
        skipped = 1
        job_node_ip = self.fpga_job_list[job_id].node_ip
        job_size = self.fpga_job_list[job_id].real_in_buf_size
        roce_bw = self.node_list[job_node_ip].roce_bw
        job_execution_time = self.fpga_job_list[job_id].theory_job_execution_time

        job_trans_time = job_size/roce_bw
        job_waiting_time = self.current_time - self.fpga_job_list[job_id].job_arrival_time

        #if job_waiting_time > w * job_execution_time:
        if job_waiting_time > job_trans_time * weight or self.fpga_job_list[job_id].job_skipped >= skipped:
            return True

        #if self.fpga_job_list[job_id].job_skipped >= 1:
        else:
            return False


    def conduct_choosy1_scheduling(self):
        secPattern = "loose"
        timPattern = "strict"
        if self.current_event_type == EventType.JOB_ARRIVAL:
            return_section_id = None
            job_id = self.current_job_id
            job_node_ip = self.fpga_job_list[job_id].node_ip

            if self.node_list[job_node_ip].if_fpga_available == True:
                return_section_id = self.pick_idle_section(job_node_ip, secPattern)
                if return_section_id != None:
                    return return_section_id

            node_ip = self.pick_idle_node()

            if node_ip != None:
                #print node_ip
                section_id = self.pick_idle_section(node_ip, secPattern)
                return_section_id = section_id
            return return_section_id

        elif self.current_event_type == EventType.JOB_END:
            return_job_id = None
            if timPattern == "loose":
                return self.conduct_choosy_scheduling()
            else:
                if len(self.waiting_job_list):
                    section_id = self.fpga_job_list[self.current_job_id].section_id
                    section_node_ip = self.fpga_section_list[section_id].node_ip

                    for job_id in self.waiting_job_list:
                        job_node_ip = self.fpga_job_list[job_id].node_ip
                        if job_node_ip == section_node_ip or self.node_list[job_node_ip].if_fpga_available == False:
                            return_job_id = job_id
                            self.remove_job_from_queue(return_job_id)
                            return return_job_id

                        else:
                            if self.if_wait_long_time(job_id) == True:
                                return_job_id =  job_id
                                self.remove_job_from_queue(return_job_id)
                                return return_job_id
                            else:
                                self.fpga_job_list[job_id].job_skipped += 1
                return return_job_id;



    def conduct_choosy_scheduling(self):
        if self.current_event_type == EventType.JOB_ARRIVAL:
            return_section_id = None
            job_id = self.current_job_id
            job_node_ip = self.fpga_job_list[job_id].node_ip

            if self.node_list[job_node_ip].if_fpga_available == True:
                return_section_id = self.pick_idle_section(job_node_ip)
                if return_section_id != None:
                    return return_section_id

            node_ip = self.pick_idle_node()

            if node_ip != None:
                #print node_ip
                section_id = self.pick_idle_section(node_ip)
                return_section_id = section_id
            return return_section_id

        elif self.current_event_type == EventType.JOB_END:
            return_job_id = None
            if len(self.waiting_job_list):
                section_id = self.fpga_job_list[self.current_job_id].section_id
                section_node_ip = self.fpga_section_list[section_id].node_ip

                for job_id in self.waiting_job_list:
                    job_node_ip = self.fpga_job_list[job_id].node_ip
                    if job_node_ip == section_node_ip or self.node_list[job_node_ip].if_fpga_available == False:
                        return_job_id = job_id
                        self.remove_job_from_queue(return_job_id)
                        return return_job_id

                return_job_id = self.waiting_job_list[0]
                self.remove_job_from_queue(return_job_id)
            return return_job_id


    def pick_idle_node(self):
        idle_node_ip = None
        if self.scheduling_algorithm == SchedulingAlgorithm.FIFO or self.scheduling_algorithm == SchedulingAlgorithm.SJF:
            ret_nodes = list()
            for node_ip, node in self.node_list.items():
                if node.if_fpga_available == True:
                    for sec_id in node.section_id_list:
                        if self.fpga_section_list[sec_id].if_idle == True:
                            ret_nodes.append(node_ip)
                            break
            if len(ret_nodes) > 0:
               idle_node_ip = random.sample(ret_nodes,1)[0]
            return idle_node_ip

        else:
            c_secs = 0
            for node_ip, node in self.node_list.items():
                if node.if_fpga_available == True:
                    idle_secs = 0
                    for sec_id in node.section_id_list:
                        if self.fpga_section_list[sec_id].if_idle == True:
                            idle_secs += 1
                    if idle_secs > c_secs:
                        c_secs = idle_secs
                        idle_node_ip = node_ip
            return idle_node_ip

    def pick_strict_idle_section(self, node_ip):
        idle_section_list = list()
        bw = 0
        pcie_bw = self.node_list[node_ip].pcie_bw
        for sec_id in self.node_list[node_ip].section_id_list:
            if self.fpga_section_list[sec_id].if_idle == True:
                idle_section_list.append(sec_id)
            else:
                acc_id = self.fpga_section_list[sec_id].current_acc_id
                acc_bw = self.acc_type_list[acc_id].acc_peak_bw
                bw += acc_bw

        if len(idle_section_list) != 0 and bw < pcie_bw:
            return random.sample(idle_section_list,1)[0]
        else:
            return None


    def pick_idle_section(self, node_ip, pattern="loose"):
        if pattern == "loose":
            for sec_id in self.node_list[node_ip].section_id_list:
                if self.fpga_section_list[sec_id].if_idle == True:
                    return sec_id
            return None
        else:
            print pattern
            return self.pick_strict_idle_section(node_ip)


    def conduct_queue_scheduling(self):
        if self.current_event_type == EventType.JOB_ARRIVAL:
            return_section_id = None
            job_id = self.current_job_id
            job_node_ip = self.fpga_job_list[job_id].node_ip
            node_ip = self.pick_idle_node()
            if node_ip != None:
                return_section_id =self.pick_idle_section(node_ip)
            return return_section_id

        elif self.current_event_type == EventType.JOB_END:
            return_job_id = None
            if len(self.waiting_job_list):
                section_id = self.fpga_job_list[self.current_job_id].section_id
                section_node_ip = self.fpga_section_list[section_id].node_ip

                queue_id_list = sorted(self.priority_queue.iterkeys())
                for queue_id in queue_id_list:
                    if len(self.priority_queue[queue_id]):
                        return_job_id = self.priority_queue[queue_id][0]
                        self.remove_job_from_queue(return_job_id)
                        return return_job_id
            return return_job_id


    def conduct_sjf_scheduling(self):
        if self.current_event_type == EventType.JOB_ARRIVAL:
            return_section_id = None
            job_id = self.current_job_id
            job_node_ip = self.fpga_job_list[job_id].node_ip
            node_ip = self.pick_idle_node()
            if node_ip != None:
                return_section_id =self.pick_idle_section(node_ip)
            return return_section_id

        elif self.current_event_type == EventType.JOB_END:
            return_job_id = None
            remote_job_list = dict()
            local_job_list = dict()# <job_id: execution_time>
            other_job_list = dict()

            if len(self.waiting_job_list):
                section_id = self.fpga_job_list[self.current_job_id].section_id
                section_node_ip = self.fpga_section_list[section_id].node_ip

                sorted_list = sorted(self.sjf_job_list.items(), lambda x,y: cmp(x[1],y[1]))
                return_job_id =  sorted_list[0][0]
                self.remove_job_from_queue(return_job_id)
            return return_job_id



    def execute_scheduling(self):
        return_id = None
        if self.scheduling_algorithm == SchedulingAlgorithm.FIFO:
            return_id = self.conduct_fifo_scheduling()

        elif self.scheduling_algorithm == SchedulingAlgorithm.SJF:
            return_id = self.conduct_sjf_scheduling()

        elif self.scheduling_algorithm == SchedulingAlgorithm.Queue:
            return_id = self.conduct_queue_scheduling()

        elif self.scheduling_algorithm == SchedulingAlgorithm.Choosy:
            return_id = self.conduct_choosy_scheduling()

        elif self.scheduling_algorithm == SchedulingAlgorithm.Choosy1:
            return_id = self.conduct_choosy1_scheduling()

        elif self.scheduling_algorithm == SchedulingAlgorithm.Double:
            return_id = self.conduct_double_scheduling()

        elif self.scheduling_algorithm == SchedulingAlgorithm.Double1:
            return_id = self.conduct_double1_scheduling()

        return return_id

    def find_associate_sections(self,c_job_id):
        c_section_id = self.fpga_job_list[c_job_id].section_id
        node_ip = self.fpga_section_list[c_section_id].node_ip
        section_list = list()
        for section_id in self.node_list[node_ip].section_id_list:
            if self.fpga_section_list[section_id].if_idle == False:
                job_id = self.fpga_section_list[section_id].current_job_id
                if self.fpga_job_list[job_id].job_start_time <= self.current_time < self.fpga_job_list[job_id].job_finish_time:#job has already begun
                    #print 'c_job_id %r, ass_job_id = %r, start_time = %r' %(c_job_id, job_id, self.fpga_job_list[job_id].job_start_time)
                    section_list.append(section_id)

        return section_list# return a list of section_id


    def update_complete_time(self, job_list):
        return_list = dict()
        for job_id, job in job_list.items():
            job_node_ip = job.node_ip
            job_node_id = self.node_list[job_node_ip].node_id

            job_section_id = job.section_id
            section_node_ip = self.fpga_section_list[job_section_id].node_ip
            section_node_id = self.node_list[section_node_ip].node_id

            new_bw = self.bw[section_node_id][job_node_id]
            if new_bw == 0:
                print "error, job_id=%r" %job_id
            new_complete_time = job.current_roce_bw * (job.job_complete_time - self.current_time)/new_bw + self.current_time

            return_list[job_id] = job.job_complete_time

            self.fpga_job_list[job_id].job_complete_time = new_complete_time
            self.fpga_job_list[job_id].current_roce_bw = new_bw

            complete_event_id = self.fpga_job_list[job_id].job_associate_event_list[4][0]

            self.fpga_job_list[job_id].job_associate_event_list[4] = (complete_event_id, new_complete_time)

        return return_list


    def update_finish_status(self, job_id, event_type):#update sections, job_finish_times, event_lists/sequences
        section_id = self.fpga_job_list[job_id].section_id
        node_ip = self.fpga_section_list[section_id].node_ip
        total_pcie_bw = self.node_list[node_ip].pcie_bw
        associate_section_list = list()
        associate_section_list = self.find_associate_sections(job_id)#return a list of section_id
        if event_type == EventType.JOB_START:
            associate_section_list.append(section_id)
        #print 'associate section list length is %r' %len(associate_section_list)

        associate_acc_real_bw_list = dict()
        associate_acc_peak_bw_list = dict()
        associate_job_list = dict()
        new_event_time_list = dict()
        obsolete_acc_bw_list = dict()

        if len(associate_section_list) == 0:
            #print 'associate_section_list is empty'
            return new_event_time_list #no associate sections
        else:
            for sec_id in associate_section_list:
                current_section = self.fpga_section_list[sec_id]
                current_acc_id = current_section.current_acc_id
                current_acc_peak_bw = self.acc_type_list[current_acc_id].acc_peak_bw
                associate_acc_peak_bw_list[sec_id] = current_acc_peak_bw# a dict of tuple  sec_id: peak_bw
                obsolete_acc_bw_list[sec_id] = current_section.current_acc_bw

            acc_real_bw_list = self.update_acc_real_bw(total_pcie_bw,associate_acc_peak_bw_list)# return a dict of sec_id: real_bw
            #for i, j in acc_real_bw_list.items():
            #    print "job[%r], real_bw %.5f" %(i, j)

            for sec_id, real_bw in acc_real_bw_list.items():
                if real_bw < 0:
                    print "error!"
                self.fpga_section_list[sec_id].current_acc_bw = real_bw#update fpga_section_list
                job_id = self.fpga_section_list[sec_id].current_job_id

                associate_job_list[job_id] = (real_bw, obsolete_acc_bw_list[sec_id])# return a dict of tuple, tuple = (real_bw,earlier_bw)
                #for i, j in associate_job_list.items():
                #    if i == job_id:
                #        print "      job[%r], real_bw %.5f, old_bw %.5f" %(i, j[0], j[1])
                #    else:
                #        print "other job[%r], real_bw %.5f, old_bw %.5f" %(i, j[0], j[1])

                #next, update fpga_job_list

            old_finish_time_list = self.update_job_finish_time(associate_job_list)#return a dict of job_id: new_job_finish_time

            #if len(old_finish_time_list) > 1:
            #    for i, j in old_finish_time_list.items():
            #        if i == job_id:
            #            print "      job[%r], o_finish_time %.5f, c_finish_time %.5f" %(i, j, self.fpga_job_list[job_id].job_finish_time)
            #        else:
            #            print "other job[%r], o_finish_time %.5f, c_finish_time %.5f" %(i, j, self.fpga_job_list[job_id].job_finish_time)

            return old_finish_time_list #return a dict of tuples, tuples=(job_id, old_finish_time)


    def update_acc_real_bw(self, pcie_bw, acc_peak_bw_list):
        #print "upate_acc_bw:", len(acc_peak_bw_list)
        upper_list = dict()
        lower_list = dict()


        n = len(acc_peak_bw_list)
        #print 'n = %r' %n
        if n == 0:
            return lower_list
        else:
            e_default_bw = 0
            c_default_bw = 0
            while True:
                total_lower_bw = 0
                if len(lower_list.items()):
                    for id, acc_bw in lower_list.items():
                        total_lower_bw += acc_bw

                e_default_bw = c_default_bw
                #print 'now n= %r' %n
                c_default_bw = (pcie_bw - total_lower_bw)/(n - len(lower_list))
                for sec_id, acc_bw in acc_peak_bw_list.items():
                    if acc_bw <= c_default_bw:
                        lower_list[sec_id] = acc_bw
                    else:
                        upper_list[sec_id] = acc_bw
                if e_default_bw == c_default_bw or len(lower_list) == n:
                    break
            if len(upper_list):
                for sec_id,acc_bw in upper_list.items():
                    lower_list[sec_id] = c_default_bw

            return lower_list# return a dict of tuple with one element  sec_id: real_acc_bw


    def update_job_finish_time(self,associate_job_list):# associate_job_list is a dict <job_id:real_bw, earlier_bw>
        return_job_id_list = dict()
        #print 'length of associate_job_list:%r' %associate_job_list

        for job_id, bw in associate_job_list.items():
            e_finish_time = self.fpga_job_list[job_id].job_finish_time
            section_id = self.fpga_job_list[job_id].section_id
            if e_finish_time < self.current_time:
                print "error!"
            c_finish_time = ((e_finish_time - self.current_time)*bw[1])/bw[0] + self.current_time
            #print '[job %r], e_bw %.5f, e_finish_time %.5f, c_bw %.5f, c_finish_time %.5f' %( job_id, bw[1], e_finish_time, bw[0], c_finish_time)

            self.fpga_job_list[job_id].job_finish_time = c_finish_time# update job_finish_time
            c_event_id = self.fpga_job_list[job_id].job_associate_event_list[3][0]
            self.fpga_job_list[job_id].job_associate_event_list[3] = (c_event_id, c_finish_time)# update (event_id, finish_time)

            return_job_id_list[job_id] = e_finish_time

        return return_job_id_list #return a dict of tuples, tuples=(job_id, old_finish_time)

    def update_associate_events(self, job_id_list, event_type):
        if len(job_id_list) == 0:
            #print "len is 0"
            return
        if event_type == EventType.JOB_FINISH:
            for job_id,event_time in job_id_list.items():
                self.remove_old_event(job_id, EventType.JOB_FINISH, event_time)
                self.insert_event(job_id, EventType.JOB_FINISH)
        elif event_type == EventType.JOB_COMPLETE:
            for job_id,event_time in job_id_list.items():
                self.remove_old_event(job_id, EventType.JOB_COMPLETE, event_time)
                self.insert_event(job_id, EventType.JOB_COMPLETE)
        elif event_type == EventType.JOB_START:
            for job_id,event_time in job_id_list.items():
                self.remove_old_event(job_id, EventType.JOB_START, event_time)
                self.insert_event(job_id, EventType.JOB_START)





    #def get_job_metrics(self, job_id):
    #    in_buf_size = self.fpga_job_list[job_id].job_in_buf_size
    #    out_buf_size = self.fpga_job_list[job_id].job_out_buf_size
    #    section_id = self.fpga_job_list[job_id].section_id
    #    #print self.get_debug_info()
    #    if section_id == 0:
    #        print 'job_id = %r' %job_id
    #    section_node_ip = self.fpga_section_list[section_id].node_ip

    #    roce_bw = self.node_list[section_node_ip].roce_bw
    #    roce_latency = self.node_list[section_node_ip].roce_latency


    #    acc_id = self.fpga_job_list[job_id].job_acc_id
    #    #acc_peak_bw = self.acc_type_list[acc_id].acc_peak_bw

    #    configuration_time = self.acc_type_list[acc_id].acc_configuration_time
    #    ideal_job_execution_time = self.fpga_job_list[job_id].job_execution_time
    #    real_job_execution_time = self.fpga_job_list[job_id].job_start_time - self.fpga_job_list[job_id].job_finish_time

    #    job_node_ip = self.fpga_job_list[job_id].node_ip

    #    if self.node_list[job_node_ip].if_fpga_available == 0:
    #        ideal_total_time = configuration_time + ideal_job_execution_time + (in_buf_size + out_buf_size)/roce_bw + 2*roce_latency
    #        self.network_ideal_workload += (in_buf_size + out_buf_size)/1024# in Gigabite magnitude

    #    else:
    #        ideal_total_time = configuration_time + ideal_job_execution_time

    #    if self.fpga_job_list[job_id].job_if_local == False:
    #        self.network_real_workload += (in_buf_size + out_buf_size)/1024

    #    real_total_time = self.fpga_job_list[job_id].job_complete_time - self.fpga_job_list[job_id].job_arrival_time
    #    if real_total_time <= 0:
    #        print "ERROR  !!"
    #    self.execution_average += real_total_time
    #    self.ideal_execution_average += ideal_job_execution_time
    #    efficiency = ideal_total_time / real_total_time
    #    self.fpga_job_list[job_id].job_anp = efficiency
    #    self.fpga_job_list[job_id].job_ideal_time = ideal_total_time
    #    self.fpga_job_list[job_id].job_real_time = real_total_time

    #    self.snp += self.fpga_job_list[job_id].job_anp
    #    self.make_span = self.larger(self.fpga_job_list[job_id].job_complete_time, self.make_span)
    #    self.ssp += self.fpga_job_list[job_id].job_real_time
    #    self.reconfiguration_num += self.fpga_job_list[job_id].if_configured
    #    #return (ideal_total_time, real_total_time, anp)





    def add_job_to_waiting_queue(self, job_id):
        self.waiting_job_list.append(job_id)

        if self.scheduling_algorithm == SchedulingAlgorithm.FIFO:
            return

        elif self.scheduling_algorithm == SchedulingAlgorithm.SJF:
            theory_job_execution_time = self.fpga_job_list[job_id].theory_job_execution_time
            self.sjf_job_list[job_id] = theory_job_execution_time

        elif self.scheduling_algorithm == SchedulingAlgorithm.Queue or self.scheduling_algorithm == SchedulingAlgorithm.Double:
            queue_id = self.get_queue_id(job_id)
            self.priority_queue[queue_id].append(job_id)

        elif self.scheduling_algorithm == SchedulingAlgorithm.Choosy:
            return

    def get_queue_id(self, job_id):
        k1 = self.k1 #MB
        k2 = self.k2
        middleNum = self.middleNum

        Q = 2
        E = 1
        K = 50

        job_size = self.fpga_job_list[job_id].real_in_buf_size

        if E * (Q ** k1) > job_size:
            queue_id = int(math.ceil(math.log(job_size/E,Q)))

        elif job_size >= E * (Q ** k2):
            queue_id = k1 + middleNum + int(math.ceil(math.log( job_size/ (E*(Q**k2)) ) ))

        else:
            middleQueueSize = E*(Q**k2 - Q**k1)/middleNum
            queue_id = int (k1 + math.ceil( (job_size - E*(Q**k1))/middleQueueSize) )

        return min(queue_id, K)

    def handle_job_arrival(self):
        job_id = self.current_job_id
        #print"job[%i] arrival on %.5f " %(job_id, self.current_time)
        section_id = self.execute_scheduling()

        if section_id == None:
            self.add_job_to_waiting_queue(job_id)

        else:
            self.start_new_job(job_id, section_id)

        self.remove_current_event()


    def handle_job_begin(self, job_id):
        #print"job[%i] begin on %.5f " %(job_id, self.current_time)
        self.remove_current_event()
        self.fpga_job_list[job_id].job_waiting_time = self.current_time - self.fpga_job_list[job_id].job_arrival_time
        c_job = self.fpga_job_list[job_id]
        section_id = c_job.section_id
        job_acc_id = c_job.job_acc_id
        in_buf_size = c_job.job_in_buf_size
        job_node_ip = c_job.node_ip
        section_node_ip = self.fpga_section_list[section_id].node_ip

        if job_node_ip != section_node_ip:
            job_node_id = self.node_list[job_node_ip].node_id
            section_node_id = self.node_list[section_node_ip].node_id
            self.network_topology[job_node_id][section_node_id] += 1

            roce_latency = self.node_list[job_node_ip].roce_latency
            roce_bw = self.node_list[job_node_ip].roce_bw# bw is in Megabytes
            #print "roce_bw =%r" %roce_bw

            bw = self.update_bw(job_node_id, section_node_id)#percentage
            #print "job[%r] begin bw: %.5f" %(job_id, roce_bw * bw)

            self.fpga_job_list[job_id].current_roce_bw = bw #percentage
            self.fpga_job_list[job_id].job_source_transfer_time = in_buf_size/(roce_bw * bw) + roce_latency
            #print"transfer time %r" %(in_buf_size/(roce_bw * bw) + roce_latency)

        self.fpga_job_list[job_id].job_start_time = self.current_time + self.fpga_job_list[job_id].job_source_transfer_time
        job_start_event_id = "job"+str(job_id)+"start"
        job_start_time = self.fpga_job_list[job_id].job_start_time
        self.fpga_job_list[job_id].job_associate_event_list[2] = (job_start_event_id, job_start_time)
        self.insert_event(job_id, EventType.JOB_START)

        if job_node_ip != section_node_ip:
            job_list = self.find_associate_transfer_jobs(job_id, EventType.JOB_BEGIN) #excluding the current job
            #for i in job_list:
                #print i

            job_obsolete_start_time = self.update_start_time(job_list)
            self.update_associate_events(job_obsolete_start_time, EventType.JOB_START)


    def find_associate_transfer_jobs(self, job_id, event_type):
        section_id = self.fpga_job_list[job_id].section_id
        job_node_ip = self.fpga_job_list[job_id].node_ip
        section_node_ip = self.fpga_section_list[section_id].node_ip
        job_list = dict()#return <job_id: job_object>

        if event_type == EventType.JOB_BEGIN or event_type == EventType.JOB_START:
            for c_job_id, c_job in self.fpga_job_list.items():
                #contain the job itself
                if c_job.job_begin_time <= self.current_time < c_job.job_start_time or (c_job.job_complete_time <= self.current_time < c_job.job_start_time):
                    destination_node_ip = self.fpga_section_list[c_job.section_id].node_ip
                    if c_job.job_if_local == False:
                        if c_job.node_ip == job_node_ip or destination_node_ip == section_node_ip:
                            job_list[c_job_id] = c_job

        elif event_type == EventType.JOB_FINISH or event_type == EventType.JOB_COMPLETE:
            for c_job_id, c_job in self.fpga_job_list.items():
                #not contain the job itself
                if c_job.job_finish_time < self.current_time < c_job.job_complete_time:
                    source_node_ip = self.fpga_section_list[c_job.section_id].node_ip
                    if c_job.job_if_local == False:
                        if c_job.node_ip == job_node_ip or source_node_ip == section_node_ip:
                            #print "finish_time, current time, complete_time", c_job.job_finish_time, self.current_time, c_job.job_complete_time
                            job_list[c_job_id] = c_job

        if job_id in job_list:
            del(job_list[job_id])
            #print "[%r] BEGIN/START delete current job" %job_id

            #print "[%r] %r associate job id is" %(event_type,job_id,)
            #for i in job_list:
            #    print i
        return job_list

    def update_start_time(self, job_list):
        return_list = dict()
        for job_id, job in job_list.items():
            job_node_ip = job.node_ip
            job_node_id = self.node_list[job_node_ip].node_id

            job_section_id = job.section_id
            section_node_ip = self.fpga_section_list[job_section_id].node_ip
            section_node_id = self.node_list[section_node_ip].node_id

            new_bw = self.bw[job_node_id][section_node_id]
            new_start_time = job.current_roce_bw * (job.job_start_time - self.current_time)/new_bw + self.current_time
            return_list[job_id] = job.job_start_time

            self.fpga_job_list[job_id].current_roce_bw = new_bw
            self.fpga_job_list[job_id].job_start_time = new_start_time

            start_event_id = self.fpga_job_list[job_id].job_associate_event_list[2][0]

            self.fpga_job_list[job_id].job_associate_event_list[2] = (start_event_id, new_start_time)

        return return_list



    def start_new_job(self,job_id,section_id):
        #print "job_id, section_id", job_id, section_id

        job_acc_id = self.fpga_job_list[job_id].job_acc_id
        section_acc_id = self.fpga_section_list[section_id].current_acc_id

        self.fpga_job_list[job_id].section_id = section_id
        job_acc_bw = self.acc_type_list[job_acc_id].acc_peak_bw

        job_node_ip = self.fpga_job_list[job_id].node_ip
        section_node_ip = self.fpga_section_list[section_id].node_ip

        job_node_id = self.node_list[job_node_ip].node_id
        section_node_id = self.node_list[section_node_ip].node_id

        self.fpga_section_list[section_id].current_acc_id = job_acc_id
        self.fpga_section_list[section_id].current_job_id = job_id
        self.fpga_section_list[section_id].current_acc_bw = job_acc_bw
        self.fpga_section_list[section_id].if_idle = False

        if job_acc_id != section_acc_id:
            #print'job_acc_id %r section_acc_id %r' %(job_acc_id,section_acc_id)
            self.fpga_job_list[job_id].job_configuration_time = self.acc_type_list[job_acc_id].acc_configuration_time
            self.fpga_job_list[job_id].if_configured = 1
            #print 'configuration time = %r' %self.fpga_job_list[job_id].job_configuration_time

        if job_node_ip != section_node_ip:
            self.fpga_job_list[job_id].job_if_local = False
            global remote_open
            self.fpga_job_list[job_id].job_configuration_time += remote_open

        elif job_node_ip == section_node_ip:
            global local_open
            self.fpga_job_list[job_id].job_configuration_time += local_open

        self.fpga_job_list[job_id].job_begin_time = self.current_time + self.fpga_job_list[job_id].job_configuration_time
        job_begin_event_id = "job"+str(job_id)+"begin"
        job_begin_time = self.fpga_job_list[job_id].job_begin_time
        self.fpga_job_list[job_id].job_associate_event_list[1] = (job_begin_event_id, job_begin_time)

        self.insert_event(job_id, EventType.JOB_BEGIN)




    def handle_job_start(self, job_id):
        self.remove_current_event()
        section_id = self.fpga_job_list[job_id].section_id
        section_node_ip = self.fpga_section_list[section_id].node_ip
        section_node_id = self.node_list[section_node_ip].node_id

        job_node_ip = self.fpga_job_list[job_id].node_ip
        job_node_id = self.node_list[job_node_ip].node_id

        if (job_node_id != section_node_id):
            #self.fpga_job_list[job_id].job_total_transfer_time += (self.current_time - self.fpga_job_list[job_id].job_begin_time)
            #print "start: job[%r] trans_time:%.5f" %(job_id, self.fpga_job_list[job_id].job_total_transfer_time)
            self.network_topology[job_node_id][section_node_id] -= 1
            bw = self.update_bw(job_node_id, section_node_id)
            roce_bw = self.node_list[section_node_ip].roce_bw# bw is in Megabytes
            #print "job[%r] start bw: %.5f" %(job_id, roce_bw * bw)
            job_list = self.find_associate_transfer_jobs(job_id, EventType.JOB_START)
            job_old_start_time = self.update_start_time(job_list)
            self.update_associate_events(job_old_start_time, EventType.JOB_START)

        chunk_job_execution_time = self.fpga_job_list[job_id].chunk_execution_time
        job_finish_event_id = "job"+str(job_id)+"finish"
        job_finish_time = self.current_time + chunk_job_execution_time
        #print"job[%i] start on %.5f, finisho on %.5f " %(job_id, self.current_time, job_finish_time)

        self.fpga_job_list[job_id].job_finish_time = job_finish_time
        self.fpga_job_list[job_id].job_associate_event_list[3] = (job_finish_event_id, job_finish_time)
        self.insert_event(job_id, EventType.JOB_FINISH)

        old_finish_time_list = self.update_finish_status(job_id, EventType.JOB_START)#return a dict of job_id: old_finish_time
        self.update_associate_events(old_finish_time_list, EventType.JOB_FINISH)



    def handle_job_finish(self, job_id):
        #print"job[%i] finish on %.5f " %(job_id, self.current_time)
        section_id = self.fpga_job_list[job_id].section_id
        section_node_ip = self.fpga_section_list[section_id].node_ip
        section_node_id = self.node_list[section_node_ip].node_id

        job_node_ip = self.fpga_job_list[job_id].node_ip
        job_node_id = self.node_list[job_node_ip].node_id

        old_finish_time_list = self.update_finish_status(job_id, EventType.JOB_FINISH)#return a dict of job_id: old_finish_time
        self.update_associate_events(old_finish_time_list, EventType.JOB_FINISH)

        if (job_node_id != section_node_id):
            #begin data transfer
            self.network_topology[section_node_id][job_node_id] += 1
            out_buf_size = self.fpga_job_list[job_id].job_out_buf_size

            #add complete event
            roce_bw = self.node_list[section_node_ip].roce_bw# bw is in Megabytes
            roce_latency = self.node_list[section_node_ip].roce_latency
            bw = self.update_bw(section_node_id, job_node_id)
            #print "job[%r] finish bw: %.5f" %(job_id, roce_bw * bw)
            #print "[job%r], bw %r . from %r to %r" %(job_id, bw, section_node_id, job_node_id)
            self.fpga_job_list[job_id].job_result_transfer_time = out_buf_size/(bw*roce_bw) + roce_latency
            self.fpga_job_list[job_id].current_roce_bw = bw

            job_list = self.find_associate_transfer_jobs(job_id, EventType.JOB_FINISH)
            job_obsolete_complete_time = self.update_complete_time(job_list)
            self.update_associate_events(job_obsolete_complete_time, EventType.JOB_COMPLETE)


        job_complete_event_id = "job"+str(job_id)+"complete"
        job_complete_time = self.fpga_job_list[job_id].job_finish_time + self.fpga_job_list[job_id].job_result_transfer_time

        self.fpga_job_list[job_id].job_complete_time = job_complete_time
        self.fpga_job_list[job_id].job_associate_event_list[4] = (job_complete_event_id, job_complete_time)
        self.insert_event(job_id, EventType.JOB_COMPLETE)
        self.remove_current_event()




    def handle_job_complete(self, job_id):
        #print"job[%i] complete on %.5f " %(job_id, self.current_time)
        #print ""

        job_acc_id = self.fpga_job_list[job_id].job_acc_id
        job_acc_bw = self.acc_type_list[job_acc_id].acc_peak_bw

        section_id = self.fpga_job_list[job_id].section_id
        section_node_ip = self.fpga_section_list[section_id].node_ip
        section_node_id = self.node_list[section_node_ip].node_id


        job_node_ip = self.fpga_job_list[job_id].node_ip
        job_node_id = self.node_list[job_node_ip].node_id

        self.fpga_job_list[job_id].job_finished_buf_size += self.fpga_job_list[job_id].job_in_buf_size

        if (job_node_id != section_node_id):
            self.fpga_job_list[job_id].job_total_transfer_time += (self.current_time - self.fpga_job_list[job_id].job_finish_time)
            self.network_topology[section_node_id][job_node_id] -= 1
            bw = self.update_bw(section_node_id, job_node_id)
            roce_bw = self.node_list[section_node_ip].roce_bw# bw is in Megabytes
            #print "job[%r] complete bw: %.5f" %(job_id, roce_bw * bw)
            job_list = self.find_associate_transfer_jobs(job_id, EventType.JOB_COMPLETE)
            job_obsolete_complete_time = self.update_complete_time(job_list)
            self.update_associate_events(job_obsolete_complete_time, EventType.JOB_COMPLETE)
            self.fpga_job_list[job_id].job_total_transfer_time += (self.current_time - self.fpga_job_list[job_id].job_finish_time)

        #print "complete: job[%r] trans_time:%.5f" %(job_id, self.fpga_job_list[job_id].job_total_transfer_time)

        if self.fpga_job_list[job_id].job_finished_buf_size >= self.fpga_job_list[job_id].real_in_buf_size:
            if (job_node_id != section_node_id):
                global remote_close
                job_end_time = self.fpga_job_list[job_id].job_complete_time + remote_close

            else:
                global local_close
                job_end_time = self.fpga_job_list[job_id].job_complete_time + local_close

            job_end_event_id = "job"+str(job_id)+"end"
            self.fpga_job_list[job_id].job_end_time = job_end_time
            self.fpga_job_list[job_id].job_associate_event_list[5] = (job_end_event_id, job_end_time)
            self.insert_event(job_id, EventType.JOB_END)

            self.remove_current_event()

        else:

            self.fpga_section_list[section_id].current_acc_bw = job_acc_bw
            #self.fpga_job_list[job_id].job_begin_time = 0

            chunk = min(CHUNK_SIZE,
                        self.fpga_job_list[job_id].real_in_buf_size - self.fpga_job_list[job_id].job_finished_buf_size)

            self.fpga_job_list[job_id].job_in_buf_size = chunk
            self.fpga_job_list[job_id].job_out_buf_size = chunk


            if job_node_ip != section_node_ip:
                #insert JOB_START
                self.network_topology[job_node_id][section_node_id] += 1
                in_buf_size = self.fpga_job_list[job_id].job_in_buf_size
                roce_latency = self.node_list[job_node_ip].roce_latency

                bw = self.update_bw(job_node_id, section_node_id)
                roce_bw = self.node_list[job_node_ip].roce_bw

                self.fpga_job_list[job_id].current_roce_bw = bw
                self.fpga_job_list[job_id].job_source_transfer_time = in_buf_size/(bw*roce_bw) + roce_latency

                job_list = self.find_associate_transfer_jobs(job_id, EventType.JOB_BEGIN)
                job_obsolete_start_time = self.update_start_time(job_list)
                self.update_associate_events(job_obsolete_start_time, EventType.JOB_START)

            self.fpga_job_list[job_id].job_start_time = self.current_time + self.fpga_job_list[job_id].job_source_transfer_time
            job_start_event_id = "job"+str(job_id)+"start"
            job_start_time = self.fpga_job_list[job_id].job_start_time
            self.fpga_job_list[job_id].job_associate_event_list[2] = (job_start_event_id, job_start_time)
            self.insert_event(job_id, EventType.JOB_START)

            self.remove_current_event()



    def handle_job_end(self, job_id):
        #print"job[%i] end on %r " %(job_id, self.current_time)
        section_id = self.fpga_job_list[job_id].section_id
        self.fpga_section_list[section_id].if_idle = True

        if len(self.waiting_job_list):
            new_job_id = self.execute_scheduling()

            if new_job_id != None:
               self.start_new_job(new_job_id, section_id)

        self.remove_current_event()


    def initiate_fpga_system(self):
        self.initiate_available_acc_type_list()
        self.initiate_node_status()
        self.initiate_network_topology()
        self.initiate_fpga_resources()
        self.initiate_job_status()
        self.initiate_events()

    def simulation_input(self):
        print 'simulation is ready ...'
        self.initiate_fpga_system()
        print 'intial event number is %r' % (len(self.event_list))

    def larger(self, a, b):
        if a < b:
            return b
        else:
            return a
    def smaller(self, a,b):
        if a > b:
            return b
        else:
            return a

    def simulation_output(self):
        n = len(self.fpga_job_list)
        avg_response_time = 0
        trans_ratio = 0
        total_size = 0
        tail_response_time = list()
        tail_percentile = [i for i in range (90,100)]
        tail_list =  list()
        system_avg_performance_ratio = list()
        system_avg_response_time = list()
        for job_id, job in self.fpga_job_list.items():

            ##print '[job%r]  on_node %r...' %(job.job_id, job.section_id)
            #response_time = 0

            #wait_time = job.job_waiting_time
            #response_time += wait_time
            ##print "[job%r] [OPEN] takes: %.0f milli_secs" %(job.job_id, time)

            #exe_time = job.job_complete_time - job.job_begin_time
            #response_time += exe_time
            ##print "[job%r] [EXE] takes %.0f milli_secs" %(job.job_id, time)

            #close_time = job.job_end_time - job.job_complete_time
            #response_time += close_time
            ##print "[job%r] [CLOSE] takes %.0f milli_secs" %(job.job_id, time)

            ##print "[job%r] [TRANS] takes %.2f milli_secs" %(job.job_id, time)

            response_time = job.job_end_time - job.job_arrival_time

            self.fpga_job_list[job_id].job_response_time = response_time

            if job.job_if_local == False:
                trans_ratio += job.real_in_buf_size

            response_ratio = (job.job_end_time - job.job_begin_time)/response_time

            tail_list.append(response_time)

            system_avg_performance_ratio.append(response_ratio)

            system_avg_response_time.append(response_time)

            total_size += job.real_in_buf_size



        trans_ratio /= total_size
        tail_list = np.array(tail_list)
        for p in tail_percentile:
            num = int(p/100* len(tail_list)+0.5)
            index = tail_list.argsort()[:num][-1]
            tail_response_time.append(tail_list[index])


        self.sap = np.mean(system_avg_performance_ratio)  #aveg ratio of theory exe /total completion time
        self.snp = np.std(system_avg_performance_ratio, ddof=0)

        avg_response_time = np.mean(system_avg_response_time) #avg completion time
        tail_response_time = [i*1000 for i in tail_response_time]
        print "[Avg Completion Time]:                           %.0f    milli_secs" %(avg_response_time*1000)
        print "[90 Percentile Completion Time]:                %.0f    milli_secs" %(tail_response_time[0])
        #print "[90-99% Percentile Completion Time]:                         milli_secs"
        #print [t for t in tail_response_time]
        print ""

        print "[System Avg Performance(Response Delay)]:        %.5f percentage" % (100*self.sap)
        print "[System Norm Performance(Fairness)]              %.5f " % self.snp
        print "[Data Locality]:                                 %.0f percentage " % ((1- trans_ratio)*100)

        #self.snp = self.snp**(1.0/n)
        #self.snp /= n
        #self.ssp /= n
        #self.execution_average /= n
        #self.ideal_execution_average /= n
        #self.make_span -= self.fpga_job_list[0].job_arrival_time
        #self.reconfiguration_num /= n
        #print '[%r] SNP = %.5f Makespan = %.5f Average = %.5f Ideal = %.5f' % (self.scheduling_algorithm, self.snp, self.make_span, self.execution_average, self.ideal_execution_average)
        #if self.network_real_workload != 0:
        #    print '[%r]  network_transfer = %.5f gb, necessary_network_transfer= %.5f gb, efficiency= %.5f ' %(self.scheduling_algorithm, self.network_real_workload, self.network_ideal_workload, self.network_ideal_workload/self.network_real_workload)
        #else:
        #    print '[%r]  Network_Transfer = %.5f GB, Necessary_Network_Transfer= %.5f GB '%(self.scheduling_algorithm, self.network_real_workload, self.network_ideal_workload)

        #print '[%r]  Real Average Execution time = %.5f' %(self.scheduling_algorithm, self.execution_average,)
        #print '[%r]  Ideal Average Execution time = %.5f' %(self.scheduling_algorithm, self.ideal_execution_average,)
        print ''



    def simulation_start(self):
        print 'simulation starts...'
        #i = 0
        while len(self.event_sequence):
            #for p,q in self.event_list.items():
            #    print q.event_type, q.event_time, q.job_id
            #print i
            #i += 1
            self.current_time = sorted(self.event_sequence.iterkeys())[0]
            #since multiple events may happen at a certain time, here we use dicts of lists to represent multimaps in C++
            self.current_event_id = self.event_sequence[self.current_time][0]
            self.current_job_id = self.event_list[self.current_event_id].job_id

            #print 'current time is %r' %self.current_time
            #print 'job_id =%r' %self.current_job_id
            #print 'current_event_id = %r' %self.current_event_id
            self.current_event_type = self.event_list[self.current_event_id].event_type#get the earliest-happened event from event_sequence
            #print 'current_event_type = %r' %self.current_event_type
            #print 'time = %.0f, job%r, %r' %(self.current_time, self.current_job_id, self.current_event_type)


            if self.current_event_type == EventType.JOB_ARRIVAL:
                self.handle_job_arrival()
            elif self.current_event_type == EventType.JOB_BEGIN:
                self.handle_job_begin(self.current_job_id)
            elif self.current_event_type == EventType.JOB_START:
                self.handle_job_start(self.current_job_id)
            elif self.current_event_type == EventType.JOB_FINISH:
                self.handle_job_finish(self.current_job_id)
            elif self.current_event_type == EventType.JOB_COMPLETE:
                self.handle_job_complete(self.current_job_id)
            elif self.current_event_type == EventType.JOB_END:
                self.handle_job_end(self.current_job_id)
            else:
                pass

if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit('Usage: simulation.py SJF/FIFO/Choosy(1)/Queue/Double(1) K1 K2 MidleNum')
        sys.exit(1)

    if sys.argv[1] == "SJF":
        scheduling_algorithm = SchedulingAlgorithm.SJF

    elif sys.argv[1] == "FIFO":
        scheduling_algorithm = SchedulingAlgorithm.FIFO

    elif sys.argv[1] == "Choosy":
        scheduling_algorithm = SchedulingAlgorithm.Choosy

    elif sys.argv[1] == "Choosy1":
        scheduling_algorithm = SchedulingAlgorithm.Choosy1

    elif sys.argv[1] == "Queue":
        scheduling_algorithm = SchedulingAlgorithm.Queue

    elif sys.argv[1] == "Double":
        scheduling_algorithm = SchedulingAlgorithm.Double

    elif sys.argv[1] == "Double1":
        scheduling_algorithm = SchedulingAlgorithm.Double1

    else:
        sys.exit('Usage: sys.argv[0] SJF/FIFO/Choosy(1)/Queue/Double(1)')
        sys.exit(1)

    k1 = int(sys.argv[2])
    k2 = int(sys.argv[3])

    middleNum = int(sys.argv[3])
    #WaitRatio = float(sys.argv[4])

    my_fpga_simulator = FpgaSimulator(scheduling_algorithm, k1, k2, middleNum)
    my_fpga_simulator.simulation_input()
    my_fpga_simulator.simulation_start()
    my_fpga_simulator.simulation_output()
