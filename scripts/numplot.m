function numplot()
clc; clear; close all;
%% --Input   
if nargin < 1
    K = 25;              % K =number of priority queues
    lam = 2.5;            % lam = flow arrival rate (number of flows per second)
    B = 2100;           % B =output bandwidth, MBytes (total priority service rate), B>lam*(alp+s0) 
    s0 = 2;             % s0 = minumum flow size, MBytes
    ini = 2;            % ini = E value in the threshold expressions   
    smax = 2^13;
    
    Expalp = 400;       % alpha = average flow size = (alp+s0), MBytes
    Powalp = 0.3;

    Expq = 1.1:0.01:2;     % q = threshold growth ratio
    Powq = 1.1:0.001:max(1.4,nthroot(smax/ini, K-1));

 
end

%% --Variables
fig_idx = 0;
Expqlen = length(Expq);
Powqlen = length(Powq);
kmin = 3;
size = round(inverse_cdf(s0,Expalp,0.95)/K);

DEBUG01 = 1; %%Plot Exp K numbers
DEBUG02 = 1; %%Plot Power K numbers

DEBUG2  = 0; %%Plot Expalp, lam = 1, K = 25
DEBUG3  = 0; %%Plot lam, Expalp = 400

%% --Begin DEBUG2
if DEBUG2 == 1
meanArr = 100:100:1000;
lam = 2;
for alp=meanArr
    FCT = Inf;
    for n = 1: Expqlen
        currQFCT = qfuncExp([ini, Expq(n)],K, alp, B, lam, s0,'exp');
        if currQFCT < FCT
            FCT = currQFCT;
            Debug2Q(alp).FCT = FCT;
            Debug2Q(alp).q = Expq(n);
        end
    end
end
fprintf('Press any key to continue.\n')
pause
for alp=meanArr
    FCT = Inf;
    %for size = round(0.1*alp):round(0.1*alp):alp
       
        currLFCT = qfuncExp(size, K, alp, B, lam, s0, 'linear',size);
        if currLFCT < FCT
            FCT = currLFCT;
            Debug2L(alp).FCT = FCT;
            Debug2L(alp).size = size;
        end
    %end
end
fprintf('Press any key to continue.\n')
pause

for alp=meanArr
    FCT = Inf;
    for n = 1: Expqlen        
        for k1 = 1:K-2
            for k2 = k1+1:K-1
                currFCT = qfuncExp([ini, Expq(n), k1, k2],K, alp, B, lam, s0,'hybrid');
                if  currFCT < FCT
                    Debug2H(alp).k1val = k1;
                    Debug2H(alp).k2val = k2;
                    Debug2H(alp).FCT = currFCT;
                    Debug2H(alp).qval = Expq(n);
                    FCT = currFCT;
                end
            end
        end
    end
end

fprintf('Press any key to continue.\n')
pause

for alp = meanArr
    Debug2Qobj(alp)     = Debug2Q(alp).FCT;
    Debug2Hobj(alp)       = Debug2H(alp).FCT;
    Debug2Lobj(alp)       = Debug2L(alp).FCT;
end

fig_idx = fig_idx + 1;
fh = figure(fig_idx); clf;

figureArray = [];
for i = 1:length(meanArr)
    figureArray(i,1)= Debug2Qobj(meanArr(i));
    figureArray(i,2)= Debug2Hobj(meanArr(i));
    figureArray(i,3)= Debug2Lobj(meanArr(i));
end
%subplot(1,2,1)
tmp = bar(meanArr,figureArray);
%set(tmp(1),'FaceColor',[0 0.7 0.7]);
%set(tmp(2),'FaceColor',[0.2 0.2 0.5]);
set(tmp(3),'FaceColor',[0.5 0.2 0.5]);
%plot(meanArr,Debug2Qobj(meanArr),'r-s');
%hold on;
%plot(meanArr,Debug2Hobj(meanArr),'g-o');
%plot(meanArr,Debug2Lobj(meanArr),'b-*');
            xlabel('Mean','FontSize',12);
            ylabel('FCT','FontSize',12);
            title('FCT under Different Means, Exponential Distribution','FontSize',15);
            legend({'Geometric Queue', 'Hbyrid Queue', 'Linear Queue'},'Location','northwest');
fprintf('Press any key to continue.\n')
pause
end

%% --Begin DEBUG3
if DEBUG3 == 1
alp = 100;
lamArr=1:20;
for lam=lamArr
    FCT = Inf;
    for n = 1: Expqlen
        currQFCT = qfuncExp([ini, Expq(n)],K, alp, B, lam, s0,'exp');
        if currQFCT < FCT
            FCT = currQFCT;
            Debug3Q(lam).FCT = FCT;
            Debug3Q(lam).q = Expq(n);
        end
    end
end
fprintf('Press any key to continue.\n')
pause

for lam=lamArr
    FCT = Inf;
    %for size = round(0.01*alp):round(0.01*alp):alp
        currLFCT = qfuncExp(size, K, alp, B, lam, s0, 'linear',size);
        if currLFCT < FCT
            FCT = currLFCT;
            Debug3L(lam).FCT = FCT;
            Debug3L(lam).size = size;
        end
    %end
end
fprintf('Press any key to continue.\n')
pause

for lam=lamArr
    FCT = Inf;
    for n = 1: Expqlen        
        for k1 = 1:K-2
            for k2 = k1+1:K-1
                currFCT = qfuncExp([ini, Expq(n), k1, k2],K, alp, B, lam, s0,'hybrid');
                if  currFCT < FCT
                    Debug3H(lam).k1val = k1;
                    Debug3H(lam).k2val = k2;
                    Debug3H(lam).FCT = currFCT;
                    Debug3H(lam).qval = Expq(n);
                    FCT = currFCT;
                end
            end
        end
    end
end
fprintf('Press any key to continue.\n')
pause

for lam=lamArr
    Debug3Qobj(lam)     = Debug3Q(lam).FCT;
    Debug3Hobj(lam)       = Debug3H(lam).FCT;
    Debug3Lobj(lam)       = Debug3L(lam).FCT;
end

figureArray = [];
for i = 1:length(lamArr)
    figureArray(i,1)= Debug3Qobj(lamArr(i));
    figureArray(i,2)= Debug3Hobj(lamArr(i));
    figureArray(i,3)= Debug3Lobj(lamArr(i));
end

fig_idx = fig_idx + 1;
fh = figure(fig_idx); clf;
%tmp = bar(lamArr,figureArray);
%set(tmp(3),'FaceColor',[0.5 0.2 0.5]);


plot(lamArr,Debug3Qobj(lamArr),'r-s');
hold on;
plot(lamArr,Debug3Hobj(lamArr),'g-o');
plot(lamArr,Debug3Lobj(lamArr),'b-*');
            xlabel('Flow Arrival Rate','FontSize',12);
            ylabel('FCT','FontSize',12);
            title('FCT under Different Flow Arrival Rate, Exponential Distribution','FontSize',15);
            legend({'Geometric Queue', 'Hbyrid Queue', 'Linear Queue'},'Location','northwest');
fprintf('Press any key to continue.\n')
pause
end

%% --Begin DEBUG 1
if DEBUG01 == 1
for k = kmin:K
    ExpQFCT = Inf;
    for n = 1: Expqlen
        currQFCT = qfuncExp([ini, Expq(n)],k, Expalp, B, lam, s0,'exp');
        if currQFCT < ExpQFCT
            ExpQFCT = currQFCT;
            ExpQ(k).FCT = ExpQFCT;
            ExpQ(k).q = Expq(n);
        end
    end
end
for k = kmin:K
    ExpLFCT = Inf;
    %for size = round(0.1*Expalp):round(0.1*Expalp):Expalp   
        currLFCT = qfuncExp(size, k, Expalp, B, lam, s0, 'linear',size);
        if currLFCT < ExpLFCT
            ExpLFCT = currLFCT;
            ExpL(k).FCT = ExpLFCT;
            ExpL(k).size = size;
        end
    %end
end
for k = kmin:K
    ExpHFCT = Inf;
    for n = 1: Expqlen        
        for k1 = 1:k-2
            for k2 = k1+1:k-1
                currFCT = qfuncExp([ini, Expq(n), k1, k2],k, Expalp, B, lam, s0,'hybrid');
                if  currFCT < ExpHFCT
                    ExpH(k).k1val = k1;
                    ExpH(k).k2val = k2;
                    ExpH(k).FCT = currFCT;
                    ExpH(k).qval = Expq(n);
                    ExpHFCT = currFCT;
                end
            end
        end
    end
end
for k = kmin:K
    ExpQobj(k)      = ExpQ(k).FCT;
    ExpHobj(k)      = ExpH(k).FCT;
    ExpLobj(k)      = ExpL(k).FCT;
end

fig_idx = fig_idx + 1;
fh = figure(fig_idx); clf;
subplot(2,2,1);
plot(kmin:K,ExpQobj(kmin:K),'r-s');
hold on;
plot(kmin:K,ExpHobj(kmin:K),'g-*');
plot(kmin:K,ExpLobj(kmin:K),'b-o');

xlabel('K','FontSize',15);
ylabel('FCT','FontSize',15)
title('FCT under different Ks, Exponential Distribution','FontSize',15);
legend('Geometric Queue', 'Hbyrid Queue', 'Linear Queue');
    
subplot(2,2,3)
x = kmin:K;
plotyy(x,ExpH(x).k1val, x,ExpH(x).qval);
hold on;
plot(x,ExpH(x).k2val);

            
X = sprintf('Maximum Queue Num: %d', K);
disp(X)
[M,I] = min(ExpQobj(kmin:K));
X = sprintf('Exp-Exp:        K=%d, q = %d, FCT is %f.', I+kmin-1, ExpQ(I).q, ExpQ(I).FCT);
disp(X)
[M,I] = min(ExpHobj(kmin:K));
X = sprintf('Exp-Hybrid:     K=%d, k1=%d, k2=%d, q=%d, FCT is %f.',I+kmin-1, ExpH(I).k1val, ExpH(I).k2val, ExpH(I).qval, ExpH(I).FCT);
disp(X)
[M,I] = min(ExpLobj(kmin:K));
X = sprintf('Exp-Linear:     K=%d, size=%f, FCT is %f.', I+kmin-1, ExpL(I).size, ExpL(I).FCT);
disp(X) 
end

%% --Begin DEBGU02
if DEBUG02 == 1
lam = 4;
for k = kmin:K
    %k = K;
    PowerQFCT = Inf;
    for n = 1: Powqlen
        currQFCT = qfuncpower([ini, Powq(n)],k, Powalp, B, lam, s0,smax,'exp');
        if currQFCT < PowerQFCT
            PowerQFCT = currQFCT;
            PowerQ(k).FCT = PowerQFCT;
            PowerQ(k).q = Powq(n);
        end
    end
end
for k = kmin:K
    PowerLFCT = Inf;
    %for size = round(0.1*Powalp):Powalp
        
        currLFCT = qfuncpower(size, k, Powalp, B, lam, s0, smax,'linear',size);
        if currLFCT < PowerLFCT
            PowerLFCT = currLFCT;
            PowerL(k).FCT = PowerLFCT;
            PowerL(k).size = size;
        end
   % end
end
for k = kmin:K
    PowerHFCT = Inf;
    for n = 1: Powqlen        
        for k1 = 1:k-2
            for k2 = k1+1:k-1
                currFCT = qfuncpower([ini, Powq(n), k1, k2],k, Powalp, B, lam, s0,smax,'hybrid');
                if  currFCT < PowerHFCT
                    PowerH(k).k1val = k1;
                    PowerH(k).k2val = k2;
                    PowerH(k).FCT = currFCT;
                    PowerH(k).qval = Powq(n);
                    PowerHFCT = currFCT;
                end
            end
        end
    end
end
for k = kmin:K
    PowerHobj(k)    = PowerH(k).FCT;
    PowerLobj(k)    = PowerL(k).FCT;
    PowerQobj(k)    = PowerQ(k).FCT;
end

subplot(2,2,2);
plot(kmin:K,PowerQobj(kmin:K),'r-s');
hold on;
plot(kmin:K,PowerHobj(kmin:K),'g-*');
plot(kmin:K,PowerLobj(kmin:K),'b-o');
            xlabel('K','FontSize',15);
            ylabel('FCT','FontSize',15);
            title('FCT under Different Ks, Power Distribution');
            legend('Geometric Queue', 'Hbyrid Queue', 'Linear Queue');


   
    [M,I] = min(PowerQobj(kmin:K));
    X = sprintf('Power-Exp:      K=%d, q = %d, FCT is %f.', I+kmin-1, PowerQ(I).q, PowerQ(I).FCT);
    disp(X)
    [M,I] = min(PowerHobj(kmin:K));
    X = sprintf('Power-Hybrid:   K=%d, k1=%d, k2=%d, q=%d, FCT is %f.',I+kmin-1, PowerH(I).k1val, PowerH(I).k2val, PowerH(I).qval, PowerH(I).FCT);
    disp(X)
    [M,I] = min(PowerLobj(kmin:K));
    X = sprintf('Power-Linear:   K=%d, size=%f, FCT is %f.', I+kmin-1, PowerL(I).size, PowerL(I).FCT);
    disp(X) 
end
end
function x = inverse_cdf(s0,alp,y)
    x = s0 - alp*log(1 - y);
end