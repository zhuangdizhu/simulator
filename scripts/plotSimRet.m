function plotSimRet()
%UNTITLED Summary of this function goes here
%   Detailed explanation goes here
csvfile = 'csvfile0504-02';                                             %%%%%%%%%%%%%%%%%%%%%
%alpha = [100,400,1000]                                          %%%%%%%%%%%%%%%%%%%%
alpha = [0.3 0.6 0.9 1.2];                                     %%%%%%%%%%%%%%%%%%%%
pattern = 'Power';                                                      %%%%%%%%%%%%%%%%%%%%   
path = '/Users/zhuzhuangdi/Documents/myCodes/simulator/logInfo/';
%lengendstr = {'alpha=100', 'alpha=400', 'alpha=1000'};
lengendstr = {'alpha=0.3','alpha=0.6','alpha=0.9','alpha=1.2'};
fig_idx = 0;
x = {'FIFO', 'SJF', 'Queue', 'Choosy', 'Double'};
for i = 1:length(alpha)
    alp = alpha(i);
    str = path;
    str = [str csvfile '/fetched-sim-' pattern '-' num2str(alp) '.csv']
    ret = load(str);
    
    avgFCTArray(:,i) = ret(:,2);
    tailFCTArray(:,i) = ret(:,3);
    SAPArray(:,i) = ret(:,4);
    DLocalArray(:,i) = ret(:,6);
end
    fig_idx = fig_idx + 1;
    fh = figure(fig_idx); clf;
    subplot(2,2,1);
    bar(avgFCTArray);
    text();
    xlabel('Algorithm');
    ylabel('Milliseconds');
    legend(lengendstr,'Location','northEast');
    set(gca,'xtick',1:5,'xticklabel',x);
    title('Average JCT');

    subplot(2,2,2);
    bar(tailFCTArray);
    xlabel('Algorithm');
    ylabel('Milliseconds');
    set(gca,'xtick',1:5,'xticklabel',x);
    title('95 Percentile Tail JCT');

    subplot(2,2,3);
    bar(SAPArray);
    xlabel('Algorithm');
    ylabel('Percentile');
    set(gca,'xtick',1:5,'xticklabel',x);
    title('System Average Response');

    subplot(2,2,4);
    bar(DLocalArray);
    xlabel('Algorithm');
    ylabel('Percentile');
    set(gca,'xtick',1:5,'xticklabel',x);
    title('Data Locality');
end

