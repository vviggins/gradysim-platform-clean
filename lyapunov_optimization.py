# -*- coding: utf-8 -*-
import random

class Node:
    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return f"Node(id={self.id})"

def calculate_cost(path, distances):
    """计算路径总成本"""
    total_cost = 0
    for i in range(len(path) - 1):
        total_cost += distances[path[i].id][path[i+1].id]
    return total_cost

def dynamic_failure_rate(distance, max_distance, base_rate=0.05, alpha=0.5):
    """
    动态计算失败率:
    base_rate: 基础失败率
    alpha: 距离敏感度
    """
    noise = random.uniform(-0.02, 0.02)  # 模拟信道随机波动
    rate = base_rate + alpha * (distance / max_distance) + noise
    return min(max(rate, 0.0), 1.0)  # 限制在 [0,1] 区间

def simulate_data_collection(path, distances, max_retries=2):
    """模拟数据收集，动态计算失败率，每个节点多次尝试后跳过"""
    collected_data = []
    total_targets = len(path) - 1  # 不包括起点
    max_distance = max(max(row) for row in distances)  # 最大距离

    for i, node in enumerate(path):
        if i == 0:
            continue  # 起点不收集
        distance = distances[path[i-1].id][node.id]
        success = False
        for attempt in range(max_retries):
            fail_rate = dynamic_failure_rate(distance, max_distance)
            if random.random() > fail_rate:
                collected_data.append(node.id)
                print(f"成功从节点 {node.id} 收集数据 (尝试 {attempt+1} 次, 失败率 {fail_rate:.2f})")
                success = True
                break
            else:
                print(f"节点 {node.id} 第 {attempt+1} 次尝试失败 (失败率 {fail_rate:.2f})")
        if not success:
            print(f"节点 {node.id} 多次尝试失败，跳过")

    success_rate = len(collected_data) / total_targets * 100
    return collected_data, success_rate

def lyapunov_optimization(nodes, distances, V, Q_target):
    """李雅普诺夫优化：动态跳过高成本节点"""
    current_path = nodes[:]
    best_path = current_path[:]
    best_cost = calculate_cost(current_path, distances)

    for t in range(100):  # 迭代次数
        current_cost = calculate_cost(current_path, distances)
        Q = max(0, current_cost - Q_target)

        # 随机选择一个节点（非起点）尝试跳过
        if len(current_path) > 2:
            node_index = random.randint(1, len(current_path) - 1)
            temp_path = current_path[:node_index] + current_path[node_index+1:]
        else:
            temp_path = current_path

        temp_cost = calculate_cost(temp_path, distances)
        drift = V * (temp_cost - current_cost) + Q**2

        if drift < 0:
            current_path = temp_path
            print(f"迭代 {t}: 接受跳过节点 {nodes[node_index].id}")

        if calculate_cost(current_path, distances) < best_cost:
            best_path = current_path[:]
            best_cost = calculate_cost(current_path, distances)
            print(f"迭代 {t}: 更新最佳路径，成本为 {best_cost}")

    return best_path, best_cost

# 场景设置
nodes = [Node(id=i) for i in range(5)]
distances = [
    [0, 10, 15, 20, 25],
    [10, 0, 35, 25, 30],
    [15, 35, 0, 30, 20],
    [20, 25, 30, 0, 10],
    [25, 30, 20, 10, 0]
]

# 初始路径（闭环）
initial_path = nodes[:] + [nodes[0]]
initial_cost = calculate_cost(initial_path, distances)
print(f"初始 TSP 路径: {initial_path}")
print(f"初始 TSP 路径成本: {initial_cost}")

# 无李雅普诺夫优化
print("\n=== 无李雅普诺夫优化 ===")
collected_data_no_lyapunov, success_rate_no = simulate_data_collection(initial_path, distances)
print(f"收集到的数据 (无李雅普诺夫优化): {collected_data_no_lyapunov}")
print(f"成功率 (无李雅普诺夫优化): {success_rate_no:.2f}%")

# 使用李雅普诺夫优化
print("\n=== 李雅普诺夫优化 ===")
V = 10
Q_target = 50
optimized_path, optimized_cost = lyapunov_optimization(nodes, distances, V, Q_target)
optimized_path.append(optimized_path[0])
print(f"优化后的 TSP 路径: {optimized_path}")
print(f"优化后的 TSP 路径成本: {optimized_cost}")

collected_data_lyapunov, success_rate_lyapunov = simulate_data_collection(optimized_path, distances)
print(f"收集到的数据 (李雅普诺夫优化): {collected_data_lyapunov}")
print(f"成功率 (李雅普诺夫优化): {success_rate_lyapunov:.2f}%")
