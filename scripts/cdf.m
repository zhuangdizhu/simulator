function cdf(alp)
%clc; clear; close all;
if nargin < 1
    alp = 0.5;
end

s0 = 10;
smax = 10*2^10;
fig_idx = 0;
F       = [];
f       = [];
X       =s0:smax;
Num     = 50;

fig_idx = fig_idx + 1;
fh = figure(fig_idx); clf;
for i=1:4
    alpha = i*0.3
    for x=X
        F(x) = cdf_(s0,smax,alpha,x);
        f(x) = pdf_(s0,smax,alpha,x);
    end
%% --plot
subplot(4,1,i)
semilogx(X,F(X),'-');
%subplot(1,2,2)
%semilogx(X,f(X));


end

%% --Generate Numbers
Y = rand(1,Num);
RetArr = [];
for id=1:length(Y)
    y = Y(id);
    RetArr(id) = inverse_cdf(s0,smax,alp,y);
end
fig_idx = fig_idx + 1;
fh = figure(fig_idx); clf;
%plot(1:length(Y), sort(RetArr));
plot(1:length(Y), RetArr);
end

function x = inverse_cdf(s0,smax,alp,y)
    x = (s0*exp(0))/(y*((s0/smax)^alp - 1) + 1)^(1/alp);
end

function ret = cdf_(s0,smax,alp,x)
    ret = 1-(s0/x)^alp;
    ret = ret/(1-(s0/smax)^alp);
end

function ret=pdf_(s0,smax,alp,x)
    ret = alp*(s0^alp)/(1-(s0/smax)^alp)*x^(-alp-1);
end