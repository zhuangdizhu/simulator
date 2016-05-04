function paramplot()
%clc; clear; close all;
%% --Input   
if nargin < 1
    K = 25;              % K =number of priority queues
    B = 2100;           % B =output bandwidth, MBytes (total priority service rate), B>lam*(alp+s0) 
    ini = 2;            % ini = E value in the threshold expressions   
    
    s0 = 2;             % s0 = minumum flow size, MBytes
    smax = 2^13;
    
    
    
    
    Expalp = 400;       %%%%%%%%%%% alpha = average flow size = (alp+s0), MBytes
    Powalp = 0.1;        %%%%%%%%%%%
    lam = 4;            %%%%%%%%%%% lam = flow arrival rate (number of flows per second)
    
    
    
    
    Expq = 1.1:0.01:2;     % q = threshold growth ratio
    Powq = 1.4:0.001:max(1.4,nthroot(smax/ini, K-1));

    Expqlen = length(Expq);
    Powqlen = length(Powq);
end

    PowerHFCT = Inf;
    k1val   = 0;
    k2val   = 0;
    qval    = 0;
    for n = 1: Powqlen        
        for k1 = 1:K-2
            for k2 = k1+1:K-1
                currFCT = qfuncpower([ini, Powq(n), k1, k2],K, Powalp, B, lam, s0,smax,'hybrid');
                if  currFCT < PowerHFCT
                PowerHFCT = currFCT;
                k1val = k1;
                k2val = k2;
                qval = Powq(n);
                end
            end
        end
    end
    disp('alpha, lam:')
    disp([Powalp lam])
    disp('k1, k2, q, FCT:')
    disp([k1val k2val qval PowerHFCT])

end