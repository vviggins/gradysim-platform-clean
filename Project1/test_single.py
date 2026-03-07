#!/usr/bin/env python3
"""
测试单个地图文件的运行
"""

import os
import sys
import importlib

def main():
    # 设置基础路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(base_dir, "../../data/node50/data1001.txt")
    result_base_dir = os.path.join(base_dir, "results")
    
    # 确保结果目录存在
    os.makedirs(result_base_dir, exist_ok=True)
    
    # 设置参数
    node_filename = "data1001"
    result_dir = f"{result_base_dir}/node50_{node_filename}"
    os.makedirs(result_dir, exist_ok=True)
    
    print(f"测试文件: {os.path.basename(data_file)}")
    print(f"结果目录: {result_dir}")
    
    # 重新导入main模块以重置全局变量
    if 'main' in sys.modules:
        importlib.reload(sys.modules['main'])
    
    # 导入并设置全局参数
    import main
    main._mobile_params = {"result_dir": result_dir, "node_file": node_filename}
    
    # 运行模拟
    try:
        from main import run_simulation
        run_simulation(real_time=False, node_file_path=data_file, result_dir=result_base_dir)
        print("✅ 测试成功完成")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()