import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

# 从改造后的文件中导入算法类
from GA_refactored import GA
from SA_refactored import SA
from ACO_refactored import ACO

# --- 1. 实验设置 ---
PROBLEM_SIZES = [50, 100, 150, 200]
# 为了保证每次实验数据一致，设置一个随机种子
np.random.seed(42) 

# 生成并存储所有问题的数据
tsp_datasets = {
    size: np.random.rand(size, 2) * 100 for size in PROBLEM_SIZES
}

# 算法超参数设置 (可以根据需要调整)
# 注意：为了公平比较，迭代次数等关键参数应该对不同规模的问题进行调整
# 这里为了演示，我们使用固定的迭代次数
GA_PARAMS = {'iteration': 500, 'num_total': 50}
SA_PARAMS = {'T0': 2000, 'rate': 0.95, 'size': 100}
ACO_PARAMS = {'iter_max': 200, 'm': 50}

# --- 2. 运行实验 ---
results = {}

for size in PROBLEM_SIZES:
    print(f"--- Running experiments for TSP with {size} cities ---")
    data = tsp_datasets[size]
    
    # GA
    print("Running GA...")
    ga_solver = GA(num_city=size, data=data.copy(), **GA_PARAMS)
    ga_len, ga_time = ga_solver.run()
    results[('GA', size)] = {'length': ga_len, 'time': ga_time}
    print(f"GA Result: Length={ga_len:.2f}, Time={ga_time:.4f}s")
    
    # SA
    print("Running SA...")
    sa_solver = SA(num_city=size, data=data.copy(), **SA_PARAMS)
    sa_len, sa_time = sa_solver.run()
    results[('SA', size)] = {'length': sa_len, 'time': sa_time}
    print(f"SA Result: Length={sa_len:.2f}, Time={sa_time:.4f}s")

    # ACO
    print("Running ACO...")
    aco_solver = ACO(num_city=size, data=data.copy(), **ACO_PARAMS)
    aco_len, aco_time = aco_solver.run()
    results[('ACO', size)] = {'length': aco_len, 'time': aco_time}
    print(f"ACO Result: Length={aco_len:.2f}, Time={aco_time:.4f}s")

# --- 3. 整理并保存结果到Excel ---
print("\n--- Generating results table ---")

# 创建一个空的DataFrame以匹配你的Excel格式
rows = []
for size in PROBLEM_SIZES:
    rows.append(f'TSP{size}_Time')
    rows.append(f'TSP{size}_Length')
rows.extend(['Average_Time', 'Average_Length'])

df = pd.DataFrame(index=rows, columns=['GA', 'SA', 'ACO', 'My_Algorithm', 'Optimal_Path', 'Gap (%)'])

# 填充数据
for algo in ['GA', 'SA', 'ACO']:
    times = []
    lengths = []
    for size in PROBLEM_SIZES:
        df.loc[f'TSP{size}_Time', algo] = results[(algo, size)]['time']
        df.loc[f'TSP{size}_Length', algo] = results[(algo, size)]['length']
        times.append(results[(algo, size)]['time'])
        lengths.append(results[(algo, size)]['length'])
    # 计算平均值
    df.loc['Average_Time', algo] = np.mean(times)
    df.loc['Average_Length', algo] = np.mean(lengths)

# 提示手动填写的部分
df['My_Algorithm'] = 'MANUAL_INPUT'
df['Optimal_Path'] = 'MANUAL_INPUT'
df['Gap (%)'] = 'MANUAL_CALC'

# 保存到Excel文件
output_filename = 'result/tsp_experiment_results.xlsx'
df.to_excel(output_filename)
print(f"Results saved to {output_filename}")


# --- 4. 生成性能比较图 ---
print("\n--- Generating performance plot ---")

plt.figure(figsize=(10, 6))

for algo in ['GA', 'SA', 'ACO']:
    times = [results[(algo, size)]['time'] for size in PROBLEM_SIZES]
    plt.plot(PROBLEM_SIZES, times, marker='o', linestyle='-', label=algo)

# 这里为你自己的算法留出位置，你可以取消注释并填充你的数据
# my_algo_times = [TIME_50, TIME_100, TIME_150, TIME_200]
# plt.plot(PROBLEM_SIZES, my_algo_times, marker='s', linestyle='--', label='My_Algorithm')

plt.title('Algorithm Performance Comparison')
plt.xlabel('Problem Size (Number of Cities)')
plt.ylabel('Computation Time (seconds)')
plt.xticks(PROBLEM_SIZES)
plt.legend()
plt.grid(True)
plt.savefig('performance_comparison.png')
plt.show()

print("Performance plot saved to performance_comparison.png")