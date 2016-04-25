1. set_system.py: generate mysql datasets, so that the simulation process can read
Usage: set_system.py <fpga_node_num> <total_node_num> <NIC_bw> <PCIe_bw>
NIC_BW: MBytes  PCIe_BW: MBytes

2. generate-job.py: generate job events
Usage: generate-job.py <HostName> <Job_num> <Distribution /Exp or Log> <SizeAlpha /MB> <ArrivalAlpha /Seconds>
Input in MBytes.
Output file in 4KBytes.

3. load-job-to-mysql.py: load job events to mysql datasets, so that the simulation process can read 
Usage: ./load-job-to-mysql.py <Distribution> <Alpha> <Interval>

4.simulation.py: the main simulation process

