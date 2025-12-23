# import subprocess
# import csv

# # 要测试的种子集合
# seeds = [1, 2, 3, 10, 20, 42, 99, 123, 2025]

# # 输出 CSV 文件名
# output_csv = "experiment_results.csv"

# # 写表头
# with open(output_csv, mode="w", newline="", encoding="utf-8-sig") as f:
#     writer = csv.writer(f)
#     writer.writerow([
#         "SEED",
#         "Baseline_成功节点数", "Baseline_失败节点数", "Baseline_尝试次数", "Baseline_成功率", "Baseline_总时间",
#         "Lyapunov_成功节点数", "Lyapunov_失败节点数", "Lyapunov_跳过节点数", "Lyapunov_尝试次数", "Lyapunov_成功率", "Lyapunov_总时间"
#     ])

# # 批量运行实验
# for seed in seeds:
#     # 调用 lya4.py，并传递 SEED 环境变量
#     result = subprocess.run(
#         ["python", "lya4.py", str(seed)],
#         capture_output=True,
#         text=True
#     )

#     output = result.stdout.splitlines()

#     # 提取 baseline 和 lyapunov 的结果
#     baseline_line = [line for line in output if line.startswith("Baseline") or line.startswith("=== Baseline")]
#     lyapunov_line = [line for line in output if line.startswith("Online Lyapunov") or line.startswith("=== Online")]

#     # 这里要注意：你原来 lya4.py 打印的格式里，有详细数据行，比如：
#     # 成功节点数: 80, 失败节点数: 20, 总尝试次数: 147, 成功率: 0.8000, 总时间: xxx
#     # 所以我们要解析那一行

#     baseline_data = [line for line in output if "成功节点数" in line and "Baseline" not in line][0]
#     lyapunov_data = [line for line in output if "成功节点数" in line and "Lyapunov" not in line][0]

#     def parse_line(line):
#         # 把 "成功节点数: 80, 失败节点数: 20, ..." 转换成数字列表
#         parts = [p.strip() for p in line.split(",")]
#         numbers = []
#         for p in parts:
#             val = p.split(":")[-1].strip()
#             try:
#                 numbers.append(float(val))
#             except ValueError:
#                 numbers.append(val)
#         return numbers

#     baseline_vals = parse_line(baseline_data)
#     lyapunov_vals = parse_line(lyapunov_data)

#     # 写入 CSV
#     with open(output_csv, mode="a", newline="", encoding="utf-8-sig") as f:
#         writer = csv.writer(f)
#         writer.writerow([seed] + baseline_vals + lyapunov_vals)

# print(f"实验完成，结果已保存到 {output_csv}")
import subprocess
import csv
from tqdm import tqdm

# 控制最大 SEED 值
x = 30   # 修改这个变量就行，比如 20 就会跑 1~20

# 自动生成 1~x 的种子列表
seeds = list(range(1, x + 1))

# 输出 CSV 文件名
output_csv = "experiment_results.csv"

# 写表头
with open(output_csv, mode="w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow([
        "SEED",
        "Baseline_成功节点数", "Baseline_失败节点数", "Baseline_尝试次数", "Baseline_成功率", "Baseline_总时间",
        "Lyapunov_成功节点数", "Lyapunov_失败节点数", "Lyapunov_跳过节点数", "Lyapunov_尝试次数", "Lyapunov_成功率", "Lyapunov_总时间"
    ])

def parse_line(line):
    # 把 "成功节点数: 80, 失败节点数: 20, ..." 转换成数字列表
    parts = [p.strip() for p in line.split(",")]
    numbers = []
    for p in parts:
        val = p.split(":")[-1].strip()
        try:
            numbers.append(float(val))
        except ValueError:
            numbers.append(val)
    return numbers

# 批量运行实验
for seed in tqdm(seeds, desc="运行实验进度", unit="seed"):
    # 调用 lya4.py，并传递 SEED 参数
    result = subprocess.run(
        ["python", "lya4.py", str(seed)],
        capture_output=True,
        text=True
    )

    output = result.stdout.splitlines()

    # 把所有包含“成功节点数”的行抓出来
    data_lines = [line for line in output if "成功节点数" in line]

    # 假设顺序固定：第一条是 baseline，第二条是 lyapunov
    if len(data_lines) < 2:
        print(f"[警告] Seed {seed} 输出不完整，跳过。")
        continue

    baseline_data = data_lines[0]
    lyapunov_data = data_lines[1]

    baseline_vals = parse_line(baseline_data)
    lyapunov_vals = parse_line(lyapunov_data)

    # 写入 CSV
    with open(output_csv, mode="a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([seed] + baseline_vals + lyapunov_vals)

print(f"\n 实验完成，结果已保存到 {output_csv}")
