clc;
close all
clear all;

% 查找文件夹下所有符合和后缀要求的文件名
fileList=dir('C:\Users\y1064\Desktop\ÐÂ½¨ÎÄ¼þ¼Ð');  %À©Õ¹Ãû
count=1;
for ff=1:length(fileList)
    f=fileList(ff).name;
    if length(f)>4 & f(end-3:end)=='.mat'
        f
        plotPic(f);
    end
end

function plotPic(f)
    data=load(f);
    X = data.StrokeSequenceX;
    Y = data.StrokeSequenceY;
    Num = data.StrokeNum;
    count=1;
    for i=1:Num
        for j=1:length(X(i,:))
            if X(i,j)~=0
    %            scatter(X(i,j),Y(i,j));
                x(count)=X(i,j);
                y(count)=length(X(i,:))-Y(i,j);
                count=count+1;
            end
        end
    end
    figure()
    set(0,'DefaultFigureVisible', 'off') %²»»­Í¼Ö±½Ó±£´æ
    scatter(x,y);
    saveas(gcf,strcat(f(1:end-4),'.jpg'))  % 保存图片
end