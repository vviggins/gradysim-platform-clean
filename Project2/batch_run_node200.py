#!/usr/bin/env python3
"""
批量运行 node200 目录下的所有数据文件。
"""

import os
import sys
import time
import glob
import importlib
import csv


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "../../data/node200")
    result_base_dir = os.path.join(base_dir, "results")

    os.makedirs(result_base_dir, exist_ok=True)

    data_files = glob.glob(os.path.join(data_dir, "data*.txt"))
    data_files.sort()
    print(f"找到 {len(data_files)} 个数据文件")

    start_time = time.time()

    import main
    main._simulation_results = []
    aggregated_results = []

    for i, data_file in enumerate(data_files):
        print(f"\n处理文件 {i+1}/{len(data_files)}: {os.path.basename(data_file)}")
        try:
            if 'main' in sys.modules:
                importlib.reload(sys.modules['main'])

            import main
            main._simulation_results = []

            from main import run_simulation, _mobile_params

            node_filename = os.path.basename(data_file).replace('.txt', '')
            main._mobile_params = {"result_dir": result_base_dir, "node_file": node_filename}

            run_simulation(real_time=False, node_file_path=data_file, result_dir=result_base_dir)
            print(f"成功完成: {os.path.basename(data_file)}")

            if hasattr(main, '_simulation_results') and main._simulation_results:
                aggregated_results.extend(main._simulation_results)
        except Exception as e:
            print(f"处理 {os.path.basename(data_file)} 时出错: {e}")
            import traceback
            traceback.print_exc()
            continue

    total_time = time.time() - start_time
    print(f"\n批量运行完成！总耗时: {total_time:.2f} 秒")

    csv_file = os.path.join(result_base_dir, "node200.csv")
    if aggregated_results:
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
                "Average_Communication_Latency",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in aggregated_results:
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
                    "Average_Communication_Latency": f"{result['Average_Communication_Latency']:.6f}",
                }
                writer.writerow(row)

        print(f"结果已保存到: {csv_file}")
        print(f"共保存了 {len(aggregated_results)} 条记录")
    else:
        print("警告: 没有找到任何结果数据")


if __name__ == "__main__":
    main()
