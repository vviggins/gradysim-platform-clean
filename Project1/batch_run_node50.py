#!/usr/bin/env python3
"""
批量运行50个节点的20个地图文件
"""

import os
import sys
import time
import glob
import importlib
import csv

def main():
    # 设置基础路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "../../data/node50")
    result_base_dir = os.path.join(base_dir, "results")
    
    # 确保结果目录存在
    os.makedirs(result_base_dir, exist_ok=True)
    
    # 获取所有数据文件
    data_files = glob.glob(os.path.join(data_dir, "data*.txt"))
    data_files.sort()  # 按文件名排序
    
    print(f"找到 {len(data_files)} 个数据文件")
    
    # 记录开始时间
    start_time = time.time()
    
    # 初始化全局结果列表
    import main
    main._simulation_results = []
    aggregated_results = []
    
    # 逐个运行每个文件
    for i, data_file in enumerate(data_files):
        print(f"\n处理文件 {i+1}/{len(data_files)}: {os.path.basename(data_file)}")
        
        try:
            # 重新导入main模块以重置全局变量
            if 'main' in sys.modules:
                importlib.reload(sys.modules['main'])
            
            # 重新初始化全局结果列表
            import main
            main._simulation_results = []
            
            # 导入并运行模拟
            from main import run_simulation, _mobile_params
            
            # 设置全局参数
            import main
            node_filename = os.path.basename(data_file).replace('.txt', '')
            result_dir = result_base_dir  # 所有数据都保存在同一个目录中
            main._mobile_params = {"result_dir": result_dir, "node_file": node_filename}
            
            # 运行模拟，不使用可视化（real_time=False）
            run_simulation(real_time=False, node_file_path=data_file, result_dir=result_base_dir)
            print(f"成功完成: {os.path.basename(data_file)}")
            
            # 将本轮结果并入汇总列表
            if hasattr(main, '_simulation_results') and main._simulation_results:
                aggregated_results.extend(main._simulation_results)
        except Exception as e:
            print(f"处理 {os.path.basename(data_file)} 时出错: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # 计算总耗时
    total_time = time.time() - start_time
    print(f"\n批量运行完成！总耗时: {total_time:.2f} 秒")
    
    # 将所有结果保存到一个统一的CSV文件中
    csv_file = os.path.join(result_base_dir, "node50.csv")
    
    # 检查是否有结果数据
    if aggregated_results:
        # 写入CSV文件
        with open(csv_file, "w", newline='', encoding='utf-8') as f:
            fieldnames = [
                "Node_File",
                "Total_Data_Packets",
                "Total_Waypoints",
                "Successful_Communications",
                "Failed_Communications",
                "Success_Rate",
                "Failure_Rate",
                "Total_Energy_Consumed",
                "Efficiency",
                "Total_Flight_Distance",
                "Total_Communication_Latency",
                "Average_Communication_Latency"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in aggregated_results:
                # 格式化数据
                row = {
                    "Node_File": result["Node_File"],
                    "Total_Data_Packets": result["Total_Data_Packets"],
                    "Total_Waypoints": result["Total_Waypoints"],
                    "Successful_Communications": result["Successful_Communications"],
                    "Failed_Communications": result["Failed_Communications"],
                    "Success_Rate": f"{result['Success_Rate']:.2%}",
                    "Failure_Rate": f"{result['Failure_Rate']:.2%}",
                    "Total_Energy_Consumed": result["Total_Energy_Consumed"],
                    "Efficiency": f"{result['Efficiency']:.4f}",
                    "Total_Flight_Distance": result["Total_Flight_Distance"],
                    "Total_Communication_Latency": result["Total_Communication_Latency"],
                    "Average_Communication_Latency": f"{result['Average_Communication_Latency']:.6f}"
                }
                writer.writerow(row)
        
        print(f"结果已保存到: {csv_file}")
        print(f"共保存了 {len(aggregated_results)} 条记录")
    else:
        print("警告: 没有找到任何结果数据")

if __name__ == "__main__":
    main()
