function plotRealRet(inputMean)
%UNTITLED Summary of this function goes here
%   Detailed explanation goes here
if nargin < 1
    fprintf('Please enter the Mean \n');
end
path = '../real_data/fetched/';
fig_idx = 0;
%Patterns = {'Global', 'Remote', 'Local'};
Patterns = {'Local'};
meanFCTs = [];
meanRes = [];
tailFCTs = [];
nums = [2];
for i = 1:length(Patterns)
    MeanFCT = Inf;
    Res = Inf;
    Tail = Inf;
    MeanFCT = 0;
    %Res = 0;
    Tail = 0;
    maxSAP = 0;
    maxCnt = nums(i);
    Pattern = Patterns{i};
    
    for cnt = 1:maxCnt
        fileName = [path num2str(inputMean) '-' Pattern '/' num2str(inputMean) '-' Pattern '.' num2str(cnt) '.csv'];
        ret = load(fileName);

        openT = ret(:,1);
        exeT = ret(:,2);
        closeT = ret(:,3);
        FCT = openT + exeT + closeT;
    
        M = sort(FCT);
        tailFCT = M(length(FCT));
    
        meanOpenT = mean(openT);
        meanExeT = mean(exeT);
    
        meanFCT = mean(FCT);
        
        if meanFCT > tailFCT
            disp(Pattern+'-'+'num2str(cnt)')
        end
   
        if meanOpenT < Res
            Res = meanOpenT;
        end
    
        %if meanFCT < MeanFCT
         %   MeanFCT = meanFCT;
        %end
        MeanFCT = MeanFCT+meanFCT;
        
        %if tailFCT < Tail
         %   Tail = tailFCT;
        %end
        
        Tail = Tail+tailFCT;
    end
    
    MeanFCT = MeanFCT/maxCnt;
    Tail = Tail/maxCnt;
    
    meanFCTs = [meanFCTs MeanFCT];
    meanRes = [meanRes Res];
    tailFCTs = [tailFCTs Tail];
    
end

    meanFCTs = meanFCTs/1000
    meanRes = meanRes/1000
    tailFCTs =tailFCTs/1000
    
    return
    fig_idx = fig_idx + 1;
    fh = figure(fig_idx); clf;
    subplot(2,1,1);
    bar(meanFCTs);
    xlabel('Patterns');
    ylabel('Micro-seconds');
    set(gca,'xtick',1:5,'xticklabel',Patterns);
    title('Average Completion Time');

    
    subplot(2,1,2);
    bar(tailFCTs);
    xlabel('Patterns');
    ylabel('Micro-seconds');
    set(gca,'xtick',1:5,'xticklabel',Patterns);
    title('Tail Completion Time');

end

