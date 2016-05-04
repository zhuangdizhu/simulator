function generate_power_job(alp, JobNum, NodeNum)
clc; clear; close all;
if nargin < 1
    alp        = 0.5;
    JobNum     = 50;
    NodeNum     =10;
end
s0 = 10;
smax = 10*2^10;
fig_idx = 0;
DEBUG = 0;
F       = [];
f       = [];
X       =s0:smax;

%% --Generate Numbers
for i =1:NodeNum
    Y = rand(1,JobNum);
    RetArr = [];
	for id=1:length(Y)
        y = Y(id);
        RetArr(id) = inverse_cdf(s0,smax,alp,y);
    end
    if DEBUG == 1
        fig_idx = fig_idx + 1;
        fh = figure(fig_idx); clf;
        plot(1:length(Y), RetArr);
    end
    str = ['/Users/zhuzhuangdi/Documents/myCodes/simulator/sim_data/tian0' num2str(i) '/' num2str(alp) '-jobsize.mat'];
    save(str,'RetArr')
end

end

function x = inverse_cdf(s0,smax,alp,y)
    x = (s0*exp(0))/(y*((s0/smax)^alp - 1) + 1)^(1/alp);
end