# -*- coding: utf-8 -*-
import random
import math
 # 离线版李雅普诺夫
class Node:
    def __init__(self, id, base_failure_rate):
        self.id = id
        self.base_failure_rate = base_failure_rate

    def __repr__(self):
        return f"Node(id={self.id})"

def calculate_cost(path, distances):
    total_cost = 0
    for i in range(len(path) - 1):
        total_cost += distances[path[i].id][path[i+1].id]
    return total_cost

def dynamic_failure_rate(node, t):
    """
    动态失败率模型：
    - 基础失败率（硬件）
    - 时间相关波动（sin 波模拟干扰）
    - 随机噪声
    """
    time_factor = 0.15 * math.sin(0.1 * t + node.id)  # 干扰周期变化
    noise = random.uniform(-0.05, 0.05)  # 随机噪声
    rate = node.base_failure_rate + time_factor + noise
    return max(0.0, min(1.0, rate))  # 限制在 [0,1]

def simulate_data_collection(path, distances, max_retries=2):
    """
    模拟任务执行
    - max_retries 次失败后跳过节点
    - 返回成功节点列表
    """
    collected_data = []
    attempts = 0
    for t, node in enumerate(path):
        retries = 0
        while retries <= max_retries:
            fail_rate = dynamic_failure_rate(node, t)
            if random.random() > fail_rate:
                collected_data.append(node.id)
                break
            else:
                retries += 1
        attempts += 1
    return collected_data

def lyapunov_optimization(path, distances, V, Q_target, max_retries=2):
    """
    根据动态失败率 + 李雅普诺夫删点
    """
    current_path = path[:]
    best_path = current_path[:]
    best_cost = calculate_cost(current_path, distances)

    for t in range(len(path)):
        current_cost = calculate_cost(current_path, distances)
        Q = max(0, current_cost - Q_target)

        # 随机选一个节点尝试跳过
        node_index = random.randint(0, len(current_path) - 1)
        node = current_path[node_index]

        # 预测失败率
        predicted_fail_rate = dynamic_failure_rate(node, t)
        retry_cost = predicted_fail_rate * max_retries * 5  # 重试代价
        temp_path = current_path[:node_index] + current_path[node_index+1:]
        temp_cost = calculate_cost(temp_path, distances)

        drift = V * ((temp_cost + retry_cost) - current_cost) + Q**2

        if drift < 0:
            current_path = temp_path

        # 更新最佳
        current_cost = calculate_cost(current_path, distances)
        if current_cost < best_cost:
            best_cost = current_cost
            best_path = current_path[:]

    return best_path, best_cost

# ===== 测试部分 =====
if __name__ == "__main__":
    # 生成 100 节点（基础失败率随机）
    nodes = [Node(id=i, base_failure_rate=random.uniform(0.05, 0.3)) for i in range(100)]

    # 随机距离矩阵（模拟 TSP 结果用）
    distances = [[0 if i == j else random.randint(10, 100) for j in range(100)] for i in range(100)]

    # 假设已有最优 TSP 路径（这里只是随机打乱模拟）
    tsp_path = nodes[:]
    random.shuffle(tsp_path)
    tsp_path.append(tsp_path[0])  # 回到起点

    # ===== 不优化 =====
    collected_no_opt = simulate_data_collection(tsp_path, distances)
    success_rate_no_opt = len(collected_no_opt) / len(tsp_path) * 100
    print(f"[无优化] 成功收集 {len(collected_no_opt)} / {len(tsp_path)} 节点，成功率 {success_rate_no_opt:.2f}%")

    # ===== 李雅普诺夫优化 =====
    V = 10
    Q_target = 300
    optimized_path, opt_cost = lyapunov_optimization(tsp_path, distances, V, Q_target)
    optimized_path.append(optimized_path[0])

    collected_opt = simulate_data_collection(optimized_path, distances)
    success_rate_opt = len(collected_opt) / len(optimized_path) * 100
    print(f"[李雅普诺夫优化] 成功收集 {len(collected_opt)} / {len(optimized_path)} 节点，成功率 {success_rate_opt:.2f}%")
