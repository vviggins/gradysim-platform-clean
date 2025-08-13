# -*- coding: utf-8 -*-
import random
# 在线版李雅普诺夫
class Node:
    def __init__(self, id, base_failure_rate):
        self.id = id
        self.base_failure_rate = base_failure_rate  # 基础失败率

    def __repr__(self):
        return f"Node(id={self.id})"

    def get_dynamic_failure_rate(self):
        """动态失败率：基础失败率 + 随机环境波动"""
        noise = random.uniform(-0.1, 0.2)  # -10% ~ +20% 波动
        rate = max(0, min(1, self.base_failure_rate + noise))
        return rate


def calculate_cost(path, distances):
    """计算路径的总成本"""
    total_cost = 0
    for i in range(len(path) - 1):
        total_cost += distances[path[i].id][path[i+1].id]
    return total_cost


def simulate_data_collection(path, distances, max_retries=2):
    """不使用李雅普诺夫，按路径执行任务"""
    collected_data = []
    for node in path:
        attempts = 0
        while attempts <= max_retries:
            fail_rate = node.get_dynamic_failure_rate()
            if random.random() > fail_rate:
                collected_data.append(node.id)
                break
            attempts += 1
    return collected_data


def simulate_data_collection_lyapunov(path, distances, V, Q_target, max_retries=2):
    """在线决策版李雅普诺夫优化"""
    collected_data = []
    current_cost = 0

    for i in range(len(path)-1):
        node = path[i]
        next_node = path[i+1]

        fail_rate = node.get_dynamic_failure_rate()
        Q = max(0, current_cost - Q_target)

        # 计算如果访问这个节点的成本
        visit_cost = distances[node.id][next_node.id]

        # 模拟漂移
        drift = V * visit_cost + Q**2 * fail_rate

        # 漂移过大，跳过该节点
        if drift > V * 5:  # 阈值可调
            continue

        # 尝试多次采集
        attempts = 0
        while attempts <= max_retries:
            if random.random() > fail_rate:
                collected_data.append(node.id)
                break
            attempts += 1

        current_cost += visit_cost

    return collected_data


# ====== 模拟 100 节点场景 ======
# 生成节点
nodes = [Node(i, random.uniform(0.05, 0.3)) for i in range(100)]

# 构造距离矩阵（对称）
distances = [[0 if i == j else random.randint(5, 50) for j in range(100)] for i in range(100)]
for i in range(100):
    for j in range(i+1, 100):
        distances[j][i] = distances[i][j]

# 构造TSP最优路径（假设已经求出）
tsp_path = nodes[:] + [nodes[0]]

# 参数
V = 10
Q_target = 200
max_retries = 2

# 1. 不使用李雅普诺夫
collected_no_opt = simulate_data_collection(tsp_path, distances, max_retries)
success_rate_no_opt = len(collected_no_opt) / len(tsp_path)

# 2. 在线李雅普诺夫优化
collected_opt = simulate_data_collection_lyapunov(tsp_path, distances, V, Q_target, max_retries)
success_rate_opt = len(collected_opt) / len(tsp_path)

# ====== 结果对比 ======
print("=== 不使用李雅普诺夫 ===")
print(f"成功采集节点数: {len(collected_no_opt)} / {len(tsp_path)}")
print(f"成功率: {success_rate_no_opt:.2%}")

print("\n=== 在线李雅普诺夫优化 ===")
print(f"成功采集节点数: {len(collected_opt)} / {len(tsp_path)}")
print(f"成功率: {success_rate_opt:.2%}")

print
