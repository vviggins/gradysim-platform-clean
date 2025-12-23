# import numpy as np
# import random

# # ======================
# # 模拟环境参数
# # ======================
# NUM_NODES = 100
# MAX_ATTEMPTS = 2  # 每个节点最多尝试 2 次通信
# SEED = 42
# random.seed(SEED)
# np.random.seed(SEED)

# # ======================
# # 生成距离矩阵（假设节点随机分布在平面）
# # ======================
# coords = np.random.rand(NUM_NODES, 2) * 100
# distances = np.zeros((NUM_NODES, NUM_NODES))
# for i in range(NUM_NODES):
#     for j in range(NUM_NODES):
#         distances[i, j] = np.linalg.norm(coords[i] - coords[j])

# # ======================
# # 模拟真实环境通信失败率
# # 每个节点的失败率不同，模拟噪声/干扰
# # ======================
# node_failures = {i: random.uniform(0.1, 0.8) for i in range(NUM_NODES)}

# # ======================
# # baseline：无优化
# # ======================
# def baseline_execution(path, distances):
#     success, fail, attempts = 0, 0, 0
#     for node in path:
#         for _ in range(MAX_ATTEMPTS):
#             attempts += 1
#             if random.random() > node_failures[node]:  # 成功通信
#                 success += 1
#                 break
#         else:
#             fail += 1
#     success_rate = success / (success + fail)
#     return success, fail, attempts, success_rate


# # ======================
# # online Lyapunov：在线跳过高风险节点
# # ======================
# def lyapunov_execution(path, distances, V=1.0):
#     success, fail, attempts, skipped = 0, 0, 0, 0
#     backlog = 0  # 李雅普诺夫虚拟队列，记录“任务积压”

#     for node in path:
#         local_success = False
#         for _ in range(MAX_ATTEMPTS):
#             attempts += 1
#             if random.random() > node_failures[node]:  # 成功通信
#                 success += 1
#                 local_success = True
#                 backlog = max(0, backlog - 1)  # 成功后 backlog 减小
#                 break
#         if not local_success:  # 连续失败
#             fail += 1
#             backlog += 1  # 增加虚拟队列

#             # 李雅普诺夫优化：如果 backlog 太大，跳过该点
#             lyapunov_metric = V * backlog - (1 - node_failures[node]) * MAX_ATTEMPTS
#             if lyapunov_metric > 0:  
#                 skipped += 1
#                 continue

#     success_rate = success / (success + fail) if (success + fail) > 0 else 0
#     return success, fail, skipped, attempts, success_rate


# # ======================
# # 生成一条离线 TSP 路径（模拟已有算法输出）
# # 这里直接用随机顺序代替真实 TSP 求解
# # ======================
# tsp_path = list(range(NUM_NODES))
# np.random.shuffle(tsp_path)

# # ======================
# # 对比实验
# # ======================
# print("=== Baseline (无优化) ===")
# s, f, att, rate = baseline_execution(tsp_path, distances)
# print(f"成功节点数: {s}, 失败节点数: {f}, 总尝试次数: {att}, 成功率: {rate:.4f}")

# print("\n=== Online Lyapunov (在线决策) ===")
# s, f, sk, att, rate = lyapunov_execution(tsp_path, distances, V=2.0)
# print(f"成功节点数: {s}, 失败节点数: {f}, 跳过节点数: {sk}, 总尝试次数: {att}, 成功率: {rate:.4f}")


import numpy as np
import random
import sys

# ======================
# 模拟环境参数
# ======================
NUM_NODES = 100
MAX_ATTEMPTS = 2      # 每个节点最多尝试 2 次通信
COMM_TIME = 1.0       # 每次通信尝试耗时
UAV_SPEED = 1.0       # 无人机速度（假设 1 距离单位 / 时间单位）


if len(sys.argv) > 1:
    SEED = int(sys.argv[1])
else:
    SEED = 42
    
random.seed(SEED)
np.random.seed(SEED)

# ======================
# 生成距离矩阵（假设节点随机分布在平面）
# ======================
coords = np.random.rand(NUM_NODES, 2) * 100
distances = np.zeros((NUM_NODES, NUM_NODES))
for i in range(NUM_NODES):
    for j in range(NUM_NODES):
        distances[i, j] = np.linalg.norm(coords[i] - coords[j])

# ======================
# 模拟真实环境通信失败率
# 每个节点的失败率不同，模拟噪声/干扰
# ======================
node_failures = {i: random.uniform(0.4, 0.6) for i in range(NUM_NODES)}

# ======================
# baseline：无优化
# ======================
def baseline_execution(path, distances):
    success, fail, attempts = 0, 0, 0
    total_time = 0.0

    for i in range(len(path) - 1):
        node = path[i]
        next_node = path[i + 1]

        # 飞行时间
        flight_time = distances[node][next_node] / UAV_SPEED
        total_time += flight_time

        # 通信尝试
        for _ in range(MAX_ATTEMPTS):
            attempts += 1
            total_time += COMM_TIME
            if random.random() > node_failures[node]:  # 成功通信
                success += 1
                break
        else:
            fail += 1

    success_rate = success / (success + fail)
    return success, fail, attempts, success_rate, total_time


# ======================
# online Lyapunov：在线跳过高风险节点
# ======================
def lyapunov_execution(path, distances, V=1.0):
    success, fail, attempts, skipped = 0, 0, 0, 0
    backlog = 0  # 李雅普诺夫虚拟队列
    total_time = 0.0

    for i in range(len(path) - 1):
        node = path[i]
        next_node = path[i + 1]

        # 飞行时间
        flight_time = distances[node][next_node] / UAV_SPEED
        total_time += flight_time

        local_success = False
        for _ in range(MAX_ATTEMPTS):
            attempts += 1
            total_time += COMM_TIME
            if random.random() > node_failures[node]:  # 成功通信
                success += 1
                local_success = True
                backlog = max(0, backlog - 1)
                break

        if not local_success:  # 连续失败
            fail += 1
            backlog += 1

            # 李雅普诺夫优化：跳过高风险点
            lyapunov_metric = V * backlog - (1 - node_failures[node]) * MAX_ATTEMPTS
            if lyapunov_metric > 0:
                skipped += 1
                continue

    success_rate = success / (success + fail) if (success + fail) > 0 else 0
    return success, fail, skipped, attempts, success_rate, total_time


# ======================
# 生成一条离线 TSP 路径（模拟已有算法输出）
# ======================
tsp_path = list(range(NUM_NODES))
np.random.shuffle(tsp_path)
tsp_path.append(tsp_path[0])  # 回到起点

# ======================
# 对比实验
# ======================
print("=== Baseline (无优化) ===")
s, f, att, rate, t = baseline_execution(tsp_path, distances)
print(f"成功节点数: {s}, 失败节点数: {f}, 总尝试次数: {att}, 成功率: {rate:.4f}, 总时间: {t:.2f}")

print("\n=== Online Lyapunov (在线决策) ===")
s, f, sk, att, rate, t = lyapunov_execution(tsp_path, distances, V=2.0)
print(f"成功节点数: {s}, 失败节点数: {f}, 跳过节点数: {sk}, 总尝试次数: {att}, 成功率: {rate:.4f}, 总时间: {t:.2f}")
