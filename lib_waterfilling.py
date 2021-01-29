# -*- coding: utf-8 -*-
"""
2021.01.29 注水法进行功率分配 VS. CVXPY优化库解优化问题进行功率分配
注水法代码参考 https://pyphysim.readthedocs.io/en/latest/_modules/pyphysim/comm/waterfilling.html
*注水法比优化法约快5倍*
"""

import numpy as np

def waterfilling(Channels, TotalPower, NoisePower):
    """ 注水算法进行功率分配
        Channels: 信道增益
        TotalPower: 待分配的总发射功率
        NoisePower: 接收端的噪声功率
    
    Returns:
        Powers: optimum powers (分配的功率)
        mu: water level (水位)
    """
    ### 降序排列信道增益
    Channels_SortIndexes = np.argsort(Channels)[::-1]
    Channels_Sorted = Channels[Channels_SortIndexes]
    """
    计算接触最差信道的水位，对这个最差的信道分配零功率。
    此后，按此水位为每个信道分配功率，
        如果功率之和少于总功率，则均分剩余功率给各个信道（增加水位）；
        如果功率之和多于总功率，则移除最坏信道，重复操作
    """
    N_Channels = Channels.size ## 总信道数
    N_RemovedChannels = 0  ## 移除的信道数
    ## 按最差信道计算最低水位
    WaterLevel = NoisePower / (np.log2(np.e)*Channels_Sorted[N_Channels-N_RemovedChannels-1])
    Powers = WaterLevel - (NoisePower /Channels_Sorted[np.arange(0, N_Channels - N_RemovedChannels)])
    
    ## 当功率之和多于总功率时，移除最坏信道，直至总功率够分
    while (sum(Powers)>TotalPower) and (N_RemovedChannels<N_Channels):
        N_RemovedChannels += 1
        WaterLevel = NoisePower / (np.log2(np.e)*Channels_Sorted[N_Channels-N_RemovedChannels-1])
        Powers = WaterLevel - (NoisePower /Channels_Sorted[np.arange(0, N_Channels - N_RemovedChannels)])
    
    ## 将剩余的功率均分给各个(剩余的)信道
    Power_Remine = TotalPower-np.sum(Powers)
    Powers_Opt_Temp = Powers + Power_Remine/(N_Channels - N_RemovedChannels)
    
    ## 将功率分配情况按原信道顺序排列
    Powers_Opt = np.zeros([N_Channels])
    Powers_Opt[Channels_SortIndexes[np.arange(0, N_Channels-N_RemovedChannels)]] = Powers_Opt_Temp
    
    WaterLevel = Powers_Opt_Temp[0] + NoisePower / (np.log2(np.e)*Channels_Sorted[0])
    
    return Powers_Opt, WaterLevel


if __name__ == '__main__':
    """  测试代码
    """
    beta_LoS = 30
    alpha_LoS = 2
    
    def cal_distance(Pos1, Pos2):
        """计算两点之间的距离 2-范数"""
        return np.linalg.norm(Pos1-Pos2,2)
    
    def cal_channel(distance):
        """计算信道增益
            Channel_gain = Beta* d^-alpha
        """
        Beta = 10**(-beta_LoS/10)
        return Beta/np.power(distance,alpha_LoS)
    
    import cvxpy as cp
    def cal_data_rate(Power, ChannelGain, BandWidth):
        """ 计算信息速率 以 r = log2(1+ channel/noise*power)  的形式"""
        return BandWidth/np.log(2)*cp.log(1+ ChannelGain/power_Noise*Power)
    
    
    Users = np.array([(352, 149, 0), (411, 63, 0), (490, 44, 0)])  ## 多个用户的位置
    power_UAV = 1000
    power_Noise = 1e-8
    
    random_positions = []
    for rrr in range(500):
        x,y = np.random.random(2)*500
        random_positions.append(np.array([x,y,50]))
    
    import time
    """注水法求解，统计计算时间"""
    t_start = time.time()
    results_waterfilling = []
    for rrr in range(500):
        pos_UAV = random_positions[rrr]
        ### 求信道
        channels = []
        for i in range(len(Users)):
            d = cal_distance(pos_UAV, Users[i])  # 常数
            channels.append(cal_channel(d))
        ### 注水法功率分配
        powers,mu = waterfilling(np.array(channels), power_UAV, power_Noise)
        ### 计算总通信速率
        rates = [ cal_data_rate(powers[i], channels[i], 1) for i in range(len(channels))]
        total_rate = cp.sum(rates).value
        
        results_waterfilling.append([powers,total_rate])
        #    print(total_rate)
    print(time.time()-t_start)
    
    """优化法求解，统计计算时间"""
    power_users = cp.Variable(shape=len(Users), nonneg=True) ### UAV 分配给用户的功率
    channels = cp.Parameter(3)
    rates = [ cal_data_rate(powers[i], channels[i], 1) for i in range(channels.size)]
    ### 构造优化问题
    obj = cp.Maximize(cp.sum(rates))
    constraints = [
        cp.sum(power_users) == power_UAV,  # 无人机功率约束
        ]
    prob = cp.Problem(obj, constraints)
    
    
    t_start = time.time()
    results_programming = []
    for rrr in range(500):
        pos_UAV = random_positions[rrr]
        channels_temp = []
        for i in range(len(Users)):
            d = cal_distance(pos_UAV, Users[i])  # 常数
            channels_temp.append(cal_channel(d))
        
        ### 信道赋给优化问题的参数
        channels.value = channels_temp
        ### 求解问题
        prob.solve()
        results_programming.append([power_users.value, obj.value])
    #    print(power_users.value)
    #    print(obj.value)
    print(time.time()-t_start)
    
    """ 均分功率 （作为基准）"""
    results_average = []
    for rrr in range(500):
        pos_UAV = random_positions[rrr]
        channels = []
        for i in range(len(Users)):
            d = cal_distance(pos_UAV, Users[i])  # 常数
            channels.append(cal_channel(d))
        powers = [1000/3]*3
        rates = [ cal_data_rate(powers[i], channels[i], 1) for i in range(len(channels))]
        total_rate = cp.sum(rates).value
        results_average.append([powers, total_rate])
    
    import matplotlib.pyplot as plt
    rates_waterfilling = np.array([rate for p,rate in results_waterfilling])
    rates_programming = np.array([rate for p,rate in results_programming])
    rates_average = np.array([rate for p,rate in results_average])
#    plt.plot(rates_programming-rates_waterfilling)
    plt.plot(rates_waterfilling-rates_average)
    
    
    # for i in range(len(rates_waterfilling)):
    #     if rates_waterfilling[i]-rates_average[i]<1e-4:
    #         print(i)
#    plt.plot(rates_programming)
#    plt.plot(rates_waterfilling)
#    plt.plot(rates_average)