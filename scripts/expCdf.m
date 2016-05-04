function expCdf(s0,alp)
clc; clear; close all;
if nargin < 1
    s0 = 1;
    smax = 2^13;
    alp = 400;
end

fig_idx = 0;
F       = [];
f       = [];
X       =s0:smax;
Num     = 500;
for x=X
    F(x) = cdf_(s0,alp,x);
    f(x) = pdf_(s0,alp,x);
end
%% --plot
fig_idx = fig_idx + 1;
fh = figure(fig_idx); clf;
subplot(1,2,1)
semilogx(X,F(X),'-');
subplot(1,2,2)
semilogx(X,f(X));

%% --Generate Numbers
Y = rand(1,Num);
RetArr = [];
for id=1:length(Y)
    y = Y(id);
    RetArr(id) = inverse_cdf(s0,alp,y);
end
fig_idx = fig_idx + 1;
fh = figure(fig_idx); clf;
%plot(1:length(Y), sort(RetArr));
hist(RetArr);
%x = inverse_cdf(s0,alp,0.95)
end

function x = inverse_cdf(s0,alp,y)
    x = s0 - alp*log(1 - y);
end

function ret = cdf_(s0,alp,x)
    ret = exp(-1/alp*(x-s0));
    ret = 1-ret;
end

function ret=pdf_(s0,alp,x)
    ret = 1/alp*exp(-1/alp*(x-s0));
end