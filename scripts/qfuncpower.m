function q = qfuncpower(x, K, alp, B, lam, s0, smax, pattern, qsize)
% x(1): E    x(2): q    x(3): k1    x(4): k2
tvec = zeros(1, K-1); 
beta = zeros(1, K);
mu = zeros(1, K+1);
wvec = zeros(1, K);
avg = alp*(s0^alp*smax^(1-alp)-s0)/(1-alp)/(1-(s0/smax)^alp);

if nargin < 8 && strcmp(pattern, 'linear')
    disp('qsize should be non zero for linear queue')
    return;
end

if strcmp(pattern, 'hybrid')
for k = 1: K-1
    if k<= x(3)
        tvec(k) = x(1)*x(2)^(k-1);
    elseif k>=x(3)+1 && k<=x(4)
        tvec(k) = x(1)*x(2)^x(3)+ x(1)*(k-x(3))*(x(2)^(x(4)-1)-x(2)^x(3))/(x(4)-x(3));
    elseif k>= x(4)+1
        tvec(k) = x(1)*x(2)^(k-1);
    end
end

elseif strcmp(pattern, 'exp')
    for k = 1: K-1
        tvec(k) = x(1)*x(2)^(k-1);
    end
    
elseif strcmp(pattern, 'linear')
    for k = 1: K-1
        tvec(k) = s0 + qsize*k;
    end
end

for k = 1: K
    if k == 1
        beta(k) = (s0*smax)^alp*(s0*tvec(k))^(-alp)*...
            (s0^alp*tvec(k)-s0*tvec(k)^alp)/...
            (smax*s0^alp-s0*smax^alp);
    elseif k>1 && k<K
        beta(k) = (s0*smax)^alp*(tvec(k-1)*tvec(k))^(-alp)*...
            (tvec(k-1)^alp*tvec(k)-tvec(k-1)*tvec(k)^alp)/...
            (smax*s0^alp-s0*smax^alp);
    elseif k == K
        beta(k) = (s0*smax)^alp*(tvec(k-1)*smax)^(-alp)*...
            (tvec(k-1)^alp*smax-tvec(k-1)*smax^alp)/...
            (smax*s0^alp-s0*smax^alp);
    end
end


for k = 1: K+1
    if k == 1
        mu(k) = B;
    else
        temp = 0;
        for j = 1: k-1
            temp = temp + beta(j);
        end
        mu(k) = B - lam*temp*avg;
    end
end

for k = 1: K
    if k == 1
        wvec(k) = lam*alp*s0^alp*(tvec(k)^(2-alp)-s0^(2-alp))/...
            (2*mu(k)*mu(k+1)*(2-alp)*(1-(s0/smax)^alp));
    elseif k>1 && k<K
        wvec(k) = lam*alp*s0^alp*(tvec(k)^(2-alp)-tvec(k-1)^(2-alp))/...
            (2*mu(k)*mu(k+1)*(2-alp)*(1-(s0/smax)^alp));
    elseif k == K
        wvec(k) = lam*alp*s0^alp*(smax^(2-alp)-tvec(k-1)^(2-alp))/...
            (2*mu(k)*mu(k+1)*(2-alp)*(1-(s0/smax)^alp));
    end
end

fin = 0;
for k = 1: K
    if k == 1
        fin = fin + beta(k)*avg/mu(k)...
            +wvec(k)*((1-(s0/tvec(k))^alp)/(1-(s0/smax)^alp));
    elseif k>1 && k<K
        fin = fin + beta(k)*avg/mu(k)...
            +wvec(k)*((1-(s0/tvec(k))^alp)/(1-(s0/smax)^alp)-...
            (1-(s0/tvec(k-1))^alp)/(1-(s0/smax)^alp));
    elseif k == K
        fin = fin + beta(k)*avg/mu(k)...
            +wvec(k)*(1-(1-(s0/tvec(k-1))^alp)/(1-(s0/smax)^alp));
    end
    
end

q=fin;

end 