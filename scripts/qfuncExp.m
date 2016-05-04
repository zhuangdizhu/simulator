function q = qfuncExp(x, K, alp, B, lam, s0, pattern, qsize)

tvec = zeros(1, K-1);   %workload threshold of queue k;
beta = zeros(1, K);     %fraction of traffic, or utilization of queue k;
mu = zeros(1, K+1);     %flow service rate of queue k;
wvec = zeros(1, K);     %wvec == average watting time for job in queue k;

%   x(1) == the threshold of queue1; E
%   x(2) == q; 
%   x(3) == the lower exponential queue index;k1
%   x(4) == the upper exponential queue index;k2

if nargin < 8 && strcmp(pattern, 'linear')
    disp('qsize should be non zero for linear queue')
    return;
end
%% ----tvec(k): workload threshold of queue k;
if strcmp(pattern, 'exp')
    for k = 1: K-1
        tvec(k) = x(1)*x(2)^(k-1);
    end
elseif strcmp(pattern, 'linear')
    for k = 1: K-1
        tvec(k) = s0 + qsize*k;
    end
elseif strcmp(pattern, 'hybrid')
    for k = 1: K-1
        if k<= x(3)%k1
            tvec(k) = x(1)*x(2)^(k-1);
        elseif k>=x(3)+1 && k<=x(4)
            tvec(k) = x(1)*x(2)^(x(3)-1)+ x(1)*(k-x(3))* (x(2)^(x(4)-1)-x(2)^(x(3)-1))/(x(4)-x(3));
        elseif k>= x(4)+1 %k2+1
            tvec(k) = x(1)*x(2)^(k-1);
        end
    end
end

%% ---beta(k): fraction of traffic, or utilization of queue k;
for k = 1: K
    if k == 1
        beta(k) = 1+s0/alp-exp(-(tvec(k)-s0)/alp)*(1+tvec(k)/alp);
    elseif k>1 && k<K
        beta(k) = exp(-(tvec(k-1)-s0)/alp)*(1+tvec(k-1)/alp)...
            -exp(-(tvec(k)-s0)/alp)*(1+tvec(k)/alp);
    elseif k == K
        beta(k) = exp(-(tvec(k-1)-s0)/alp)*(1+tvec(k-1)/alp);
    end
end

beta = beta*alp/(alp+s0);

%% mu(k): flow service rate of queue k;
for k = 1: K+1
    if k == 1
        mu(k) = B;
    else
        temp = 0;
        for j = 1: k-1
            temp = temp + beta(j);
        end
        mu(k) = B - lam*(alp+s0)*temp;
    end
end

%% wvec(k): average watting time for job in queue k;
for k = 1: K
    if k == 1
        wvec(k) = lam/2/mu(k)/mu(k+1)*(2*alp^2+2*alp*s0+s0^2-exp(-(tvec(k)-s0)/alp)*(2*alp^2+2*alp*tvec(k)+tvec(k)^2));
    elseif k>1 && k<K
        wvec(k) = lam/2/mu(k)/mu(k+1)*(exp(-(tvec(k-1)-s0)/alp)*(tvec(k-1)^2+2*tvec(k-1)*alp+2*alp^2)...
            - exp(-(tvec(k)-s0)/alp)*(tvec(k)^2+2*tvec(k)*alp+2*alp^2));
    elseif k == K
        wvec(k) = lam/2/mu(k)/mu(k+1)*(exp(-(tvec(k-1)-s0)/alp)*(2*alp^2+2*alp*tvec(k-1)+tvec(k-1)^2));
    end
end

%% fin(k): FCT;
fin = 0;
for k = 1: K
    if k == 1
        fin = fin + ( alp+s0- exp((s0-tvec(k))/alp)*(alp+tvec(k)) )/mu(k)...
            +wvec(k)*(1- exp((s0-tvec(k))/alp) );
    elseif k>1 && k<K
        fin = fin + (exp((s0-tvec(k-1))/alp)*(alp+tvec(k-1))-exp((s0-tvec(k))/alp)*(alp+tvec(k)))/mu(k)...
            +wvec(k)*(exp((s0-tvec(k-1))/alp)- exp((s0-tvec(k))/alp) );
        %/alp, mu(k)
    elseif k == K
        fin = fin + exp((s0-tvec(k-1))/alp)*(alp+tvec(k-1))/mu(k)+wvec(k)*exp((s0-tvec(k-1))/alp);
    end
    
end
% alp
q=fin;

end 