#!/usr/bin/env python3
"""
汇总50个节点的20个地图文件的实验结果
"""

import os
import csv
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def main():
    # 设置基础路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    result_base_dir = os.path.join(base_dir, "results")
    
    # 查找所有结果目录
    result_dirs = glob.glob(os.path.join(result_base_dir, "node50_data*"))
    result_dirs.sort()
    
    # 创建汇总数据列表
    summary_data = []
    
    print(f"找到 {len(result_dirs)} 个结果目录")
    
    # 逐个读取每个结果目录的汇总文件
    for result_dir in result_dirs:
        # 提取文件名
        dir_name = os.path.basename(result_dir)
        data_file = dir_name.replace("node50_", "")
        
        # 查找汇总CSV文件
        summary_file = os.path.join(result_dir, f"summary_{data_file}.csv")
        
        if os.path.exists(summary_file):
            print(f"读取: {summary_file}")
            
            # 读取CSV文件
            with open(summary_file, 'r') as f:
                reader = csv.reader(f)
                data = dict(reader)
            
            # 添加到汇总数据
            summary_data.append({
                'Data_File': data_file,
                'Total_Data_Packets': int(data['Total Data Packets']),
                'Total_Waypoints': int(data['Total Waypoints (Nodes)']),
                'Successful_Communications': int(data['Successful Communications']),
                'Failed_Communications': int(data['Failed Communications']),
                'Success_Rate': float(data['Success Rate'].rstrip('%')) / 100,
                'Failure_Rate': float(data['Failure Rate'].rstrip('%')) / 100,
                'Total_Energy_Consumed': float(data['Total Energy Consumed']),
                'Efficiency': float(data['Efficiency (Data per Unit Energy)']),
                'Total_Flight_Distance': float(data['Total Flight Distance']),
                'Total_Communication_Latency': float(data['Total Communication Latency']),
                'Average_Communication_Latency': float(data['Average Communication Latency'])
            })
        else:
            print(f"警告: 找不到汇总文件 {summary_file}")
    
    # 创建DataFrame并保存为CSV
    if summary_data:
        df = pd.DataFrame(summary_data)
        summary_csv = os.path.join(result_base_dir, "node50_summary.csv")
        df.to_csv(summary_csv, index=False)
        print(f"\n汇总数据已保存到: {summary_csv}")
        
        # 计算平均值
        avg_data = {
            'Metric': [
                'Average Success Rate',
                'Average Failure Rate',
                'Average Energy Consumption',
                'Average Efficiency',
                'Average Flight Distance',
                'Average Communication Latency'
            ],
            'Value': [
                f"{df['Success_Rate'].mean():.2%}",
                f"{df['Failure_Rate'].mean():.2%}",
                f"{df['Total_Energy_Consumed'].mean():.2f}",
                f"{df['Efficiency'].mean():.4f}",
                f"{df['Total_Flight_Distance'].mean():.2f}",
                f"{df['Average_Communication_Latency'].mean():.4f}"
            ]
        }
        
        avg_df = pd.DataFrame(avg_data)
        avg_csv = os.path.join(result_base_dir, "node50_averages.csv")
        avg_df.to_csv(avg_csv, index=False)
        print(f"平均数据已保存到: {avg_csv}")
        
        # 生成简单的统计图表
        create_charts(df, result_base_dir)
        
        # 打印统计摘要
        print("\n=== 统计摘要 ===")
        print(f"成功通信率: {df['Success_Rate'].mean():.2%} ± {df['Success_Rate'].std():.2%}")
        print(f"平均能耗: {df['Total_Energy_Consumed'].mean():.2f} ± {df['Total_Energy_Consumed'].std():.2f}")
        print(f"平均效率: {df['Efficiency'].mean():.4f} ± {df['Efficiency'].std():.4f}")
        print(f"平均飞行距离: {df['Total_Flight_Distance'].mean():.2f} ± {df['Total_Flight_Distance'].std():.2f}")
        
    else:
        print("没有找到任何结果数据")

def create_charts(df, result_dir):
    """创建统计图表"""
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
    
    # 创建图表目录
    charts_dir = os.path.join(result_dir, "charts")
    os.makedirs(charts_dir, exist_ok=True)
    
    # 1. 成功率和失败率对比图
    plt.figure(figsize=(10, 6))
    plt.bar(range(len(df)), df['Success_Rate'], alpha=0.7, label='成功率')
    plt.bar(range(len(df)), df['Failure_Rate'], alpha=0.7, label='失败率', bottom=df['Success_Rate'])
    plt.xlabel('实验编号')
    plt.ylabel('比率')
    plt.title('50节点实验成功率和失败率对比')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(charts_dir, 'success_failure_rates.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. 能耗和效率散点图
    plt.figure(figsize=(10, 6))
    plt.scatter(df['Total_Energy_Consumed'], df['Efficiency'], alpha=0.7)
    plt.xlabel('总能耗')
    plt.ylabel('效率 (数据/单位能耗)')
    plt.title('50节点实验能耗与效率关系')
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(charts_dir, 'energy_efficiency_scatter.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. 飞行距离和通信延迟关系
    plt.figure(figsize=(10, 6))
    plt.scatter(df['Total_Flight_Distance'], df['Average_Communication_Latency'], alpha=0.7)
    plt.xlabel('总飞行距离')
    plt.ylabel('平均通信延迟')
    plt.title('50节点实验飞行距离与通信延迟关系')
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(charts_dir, 'distance_latency_scatter.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. 多指标雷达图
    categories = ['成功率', '效率', '飞行距离', '通信延迟']
    
    # 标准化数据（0-1范围）
    success_rate_norm = df['Success_Rate'].values
    efficiency_norm = (df['Efficiency'] - df['Efficiency'].min()) / (df['Efficiency'].max() - df['Efficiency'].min())
    distance_norm = 1 - (df['Total_Flight_Distance'] - df['Total_Flight_Distance'].min()) / (df['Total_Flight_Distance'].max() - df['Total_Flight_Distance'].min())
    latency_norm = 1 - (df['Average_Communication_Latency'] - df['Average_Communication_Latency'].min()) / (df['Average_Communication_Latency'].max() - df['Average_Communication_Latency'].min())
    
    # 计算平均值
    avg_values = [
        np.mean(success_rate_norm),
        np.mean(efficiency_norm),
        np.mean(distance_norm),
        np.mean(latency_norm)
    ]
    
    # 创建雷达图
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]  # 闭合图形
    avg_values += avg_values[:1]  # 闭合图形
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.fill(angles, avg_values, 'b', alpha=0.2)
    ax.plot(angles, avg_values, 'b-', linewidth=2)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_title('50节点实验多指标性能雷达图', size=15)
    plt.savefig(os.path.join(charts_dir, 'performance_radar.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"图表已保存到: {charts_dir}")

if __name__ == "__main__":
    main()