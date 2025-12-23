import numpy as np
import random
import sys
from scipy.spatial.distance import pdist, squareform
# 真正强大的TSP求解器
from python_tsp.heuristics import solve_tsp_simulated_annealing
import os

# ==============================================================================
# 1. 配置中心 (Config Center) - 增加了坐标和路径文件配置
# ==============================================================================
class Config:
    def __init__(self, seed=42):
        self.SEED = seed
        
        # <<<--- 核心修改: 场景参数现在由外部文件决定 --->>>
        # 指定包含真实坐标的 .txt 文件
        self.COORDS_FILE_PATH = None 
        # (可选) 指定包含预计算路径的 .txt 文件
        self.TOUR_FILE_PATH = None
        # <<<-------------------------------------------->>>
        
        # 物理参数 (这些保持不变)
        self.MAX_ATTEMPTS = 3      
        self.COMM_TIME = 1.0       
        self.UAV_SPEED = 20.0      
        self.UAV_BATTERY_CAPACITY = 2000.0
        self.ENERGY_PER_METER_FLIGHT = 0.1
        self.ENERGY_PER_SECOND_HOVER = 0.5
        self.LYAPUNOV_V = 2.0
        self.TSP_ALPHA = 0.995
        self.COORDS_SCALE = 1000    # 地图比例尺: 1.0 单位 = 1000 米
        random.seed(self.SEED)
        np.random.seed(self.SEED)

# ==============================================================================
# 2. 模拟环境 (Simulation Environment) - 使用数据文件的内在顺序
# ==============================================================================
class SimulationEnvironment:
    def __init__(self, config: Config):
        self.config = config
        self.coords_unit = self._load_coords() # 加载的0-1范围的“单位坐标”
        
        # <<<--- 核心修改 1: 创建真实世界的坐标 ---
        # 将单位坐标乘以比例尺，得到真实世界的米制坐标
        self.coords_real = self.coords_unit * self.config.COORDS_SCALE
        self.num_nodes = len(self.coords_real)
        self.distances = self._compute_distances()
        self.node_values = self._generate_node_values()

    def _load_coords(self):
        if not self.config.COORDS_FILE_PATH:
            raise ValueError("必须在Config中指定 COORDS_FILE_PATH！")
        try:
            print(f"正在从坐标文件加载场景: {self.config.COORDS_FILE_PATH}")
            coords_data = np.loadtxt(self.config.COORDS_FILE_PATH)
            if np.array_equal(coords_data[0], coords_data[-1]):
                return coords_data[:-1]
            return coords_data
        except Exception as e:
            print(f"错误: 加载坐标文件 '{self.config.COORDS_FILE_PATH}' 失败: {e}")
            sys.exit(1)


    def _compute_distances(self):
        # 使用 self.coords_real (米制坐标) 来计算距离
        print(f"场景尺寸: {self.config.COORDS_SCALE}x{self.config.COORDS_SCALE} 米。正在计算真实距离矩阵...")
        return squareform(pdist(self.coords_real, metric='euclidean'))

    def _generate_node_values(self):
        values = np.ones(self.num_nodes)
        high_value_indices = np.random.choice(self.num_nodes, size=int(0.1 * self.num_nodes), replace=False)
        values[high_value_indices] = 5.0
        return {i: values[i] for i in range(self.num_nodes)}

    def get_communication_success_prob(self, node_index):
        base_prob = 0.8 
        noise = random.uniform(-0.2, 0.2)
        return max(0, min(1, base_prob + noise))

    # <<<--- 核心修改：让路径直接等于文件顺序 --->>>
    def get_initial_tsp_path(self):
        """
        不再计算或加载路径，直接返回一个代表文件顺序的路径。
        例如，如果有100个节点，就返回 [0, 1, 2, ..., 99, 0]。
        """
        print(f"使用坐标文件 '{os.path.basename(self.config.COORDS_FILE_PATH)}' 的内置顺序作为飞行路径。")
        # 创建一个从 0 到 n-1 的序列
        path_indices = list(range(self.num_nodes))
        # 在末尾加上起点，构成闭环
        path_indices.append(path_indices[0])
        
        # 计算并打印一下这条路径的长度，供参考
        path_dist = sum(self.distances[path_indices[i]][path_indices[i+1]] for i in range(len(path_indices) - 1))
        print(f"路径总长度: {path_dist:.2f} 米")
        
        return path_indices
    # <<<-------------------------------------------->>>

# ==============================================================================
# 3. 执行策略 (Execution Strategies) - 整合了能量和价值模型
# ==============================================================================
class ExecutionStrategy:
    def __init__(self, env: SimulationEnvironment):
        self.env = env
        self.config = env.config

    def execute(self, path):
        raise NotImplementedError

    def _communicate(self, node):
        success_prob = self.env.get_communication_success_prob(node)
        for attempt in range(1, self.config.MAX_ATTEMPTS + 1):
            if random.random() < success_prob:
                return True, attempt
        return False, self.config.MAX_ATTEMPTS

class BaselineStrategy(ExecutionStrategy):
    """基线策略：严格遵循离线路径，直到能量耗尽"""
    def execute(self, path):
        stats = {'collected_value': 0, 'success_nodes': set(), 'fail': 0, 'total_time': 0.0, 'energy_consumed': 0.0}
        
        for i in range(len(path) - 1):
            current_node, next_node = path[i], path[i+1]
            
            # 检查飞行所需能量
            flight_dist = self.env.distances[current_node][next_node]
            flight_energy = flight_dist * self.config.ENERGY_PER_METER_FLIGHT
            if stats['energy_consumed'] + flight_energy > self.config.UAV_BATTERY_CAPACITY:
                print("基线策略：能量不足以飞往下一个节点，任务中止。")
                break
            
            stats['energy_consumed'] += flight_energy
            stats['total_time'] += flight_dist / self.config.UAV_SPEED
            
            # 通信
            is_success, num_attempts = self._communicate(current_node)
            comm_energy = num_attempts * self.config.COMM_TIME * self.config.ENERGY_PER_SECOND_HOVER
            if stats['energy_consumed'] + comm_energy > self.config.UAV_BATTERY_CAPACITY:
                print("基线策略：通信中能量耗尽，任务中止。")
                stats['total_time'] += (self.config.UAV_BATTERY_CAPACITY - stats['energy_consumed']) / self.config.ENERGY_PER_SECOND_HOVER
                stats['energy_consumed'] = self.config.UAV_BATTERY_CAPACITY
                break

            stats['energy_consumed'] += comm_energy
            stats['total_time'] += num_attempts * self.config.COMM_TIME
            
            if is_success:
                if current_node not in stats['success_nodes']:
                    stats['collected_value'] += self.env.node_values[current_node]
                    stats['success_nodes'].add(current_node)
            else:
                stats['fail'] += 1
        
        return stats

class LyapunovStrategyV2(ExecutionStrategy):
    """李雅普诺夫策略V2：综合考虑积压、节点价值和飞行成本"""
    def execute(self, path):
        stats = {'collected_value': 0, 'success_nodes': set(), 'fail': 0, 'skipped': 0, 'total_time': 0.0, 'energy_consumed': 0.0}
        backlog = 0

        for i in range(len(path) - 1):
            current_node, next_node = path[i], path[i+1]
            
            # 检查是否有足够能量完成一次完整的“飞行+最差情况通信”
            flight_dist = self.env.distances[current_node][next_node]
            min_required_energy = (flight_dist * self.config.ENERGY_PER_METER_FLIGHT) + \
                                (self.config.MAX_ATTEMPTS * self.config.COMM_TIME * self.config.ENERGY_PER_SECOND_HOVER)
            if stats['energy_consumed'] + min_required_energy > self.config.UAV_BATTERY_CAPACITY:
                print("李雅普诺夫策略：剩余能量不足以完成下一个完整任务，提前返航。")
                break

            # 智能决策：综合考虑节点价值和飞行成本
            success_prob = self.env.get_communication_success_prob(current_node)
            expected_value_gain = success_prob * self.env.node_values[current_node]
            time_cost = (flight_dist / self.config.UAV_SPEED) + (self.config.MAX_ATTEMPTS * self.config.COMM_TIME)
            
            # 李雅普诺夫漂移，这次我们最大化 (V*价值 - 积压*时间成本)
            drift = self.config.LYAPUNOV_V * expected_value_gain - backlog * time_cost
            decision_threshold = 0
            if backlog > 0 and drift < decision_threshold: # 阈值可以调整
                stats['skipped'] += 1
                stats['energy_consumed'] += flight_dist * self.config.ENERGY_PER_METER_FLIGHT
                stats['total_time'] += flight_dist / self.config.UAV_SPEED
                continue

            # 执行飞行和通信
            stats['energy_consumed'] += flight_dist * self.config.ENERGY_PER_METER_FLIGHT
            stats['total_time'] += flight_dist / self.config.UAV_SPEED
            
            is_success, num_attempts = self._communicate(current_node)
            comm_energy = num_attempts * self.config.COMM_TIME * self.config.ENERGY_PER_SECOND_HOVER
            stats['energy_consumed'] += comm_energy
            stats['total_time'] += num_attempts * self.config.COMM_TIME
            
            if is_success:
                if current_node not in stats['success_nodes']:
                    stats['collected_value'] += self.env.node_values[current_node]
                    stats['success_nodes'].add(current_node)
                backlog = max(0, backlog - self.env.node_values[current_node]) # 成功，积压减少（高价值点减少更多）
            else:
                stats['fail'] += 1
                backlog += 1 # 失败，积压增加

        return stats

# ==============================================================================
# 4. 实验运行器 (Experiment Runner) - 更新了报告指标
# ==============================================================================
def run_experiment(config: Config):
    print(f"\n--- 实验开始 | 种子: {config.SEED} ---")
    
    env = SimulationEnvironment(config)
    tsp_path = env.get_initial_tsp_path()
    
    print("=== Baseline (无优化) ===")
    baseline_strategy = BaselineStrategy(env)
    baseline_stats = baseline_strategy.execute(tsp_path)
    print(f"成功节点数: {len(baseline_stats['success_nodes'])}, 失败节点数: {baseline_stats['fail']}, "
          f"收集总价值: {baseline_stats['collected_value']:.2f}, "
          f"总时间: {baseline_stats['total_time']:.2f}, "
          f"总能耗: {baseline_stats['energy_consumed']:.2f}")

    print("\n=== Online Lyapunov V2 (智能决策) ===")
    lyapunov_strategy = LyapunovStrategyV2(env)
    lyapunov_stats = lyapunov_strategy.execute(tsp_path)
    print(f"成功节点数: {len(lyapunov_stats['success_nodes'])}, 失败节点数: {lyapunov_stats['fail']}, "
          f"跳过节点数: {lyapunov_stats['skipped']}, "
          f"收集总价值: {lyapunov_stats['collected_value']:.2f}, "
          f"总时间: {lyapunov_stats['total_time']:.2f}, "
          f"总能耗: {lyapunov_stats['energy_consumed']:.2f}")
    
    return baseline_stats, lyapunov_stats


# ==============================================================================
# 5. 主程序入口 (Main Entry Point) - 更新了报告逻辑
# ==============================================================================
if __name__ == "__main__":
    initial_seed = 42
    num_runs = 10
    
    all_baseline_stats = []
    all_lyapunov_stats = []

    for i in range(num_runs):
        config = Config(seed=initial_seed + i)
        config.COORDS_FILE_PATH = "./data/data1.txt" 
        bl_stats, ly_stats = run_experiment(config)
        all_baseline_stats.append(bl_stats)
        all_lyapunov_stats.append(ly_stats)

    def calculate_average_stats(stats_list):
        # 计算所有数值指标的平均值
        avg_stats = {key: np.mean([s[key] for s in stats_list if isinstance(s[key], (int, float))]) for key in stats_list[0]}
        # 单独计算成功率和价值效率
        total_collected_value = np.sum([s['collected_value'] for s in stats_list])
        total_nodes_visited = np.sum([len(s['success_nodes']) + s['fail'] for s in stats_list])
        total_success_nodes = np.sum([len(s['success_nodes']) for s in stats_list])
        
        avg_stats['success_rate'] = total_success_nodes / total_nodes_visited if total_nodes_visited > 0 else 0
        avg_stats['value_per_time'] = total_collected_value / np.sum([s['total_time'] for s in stats_list])
        return avg_stats
    
    avg_bl = calculate_average_stats(all_baseline_stats)
    avg_ly = calculate_average_stats(all_lyapunov_stats)
    
    print("\n" + "="*50)
    print(f"=== 平均结果 ({num_runs}次运行) ===")
    print("="*50)
    print("--- Baseline ---")
    print(f"平均成功率: {avg_bl['success_rate']:.4f}, 平均总时间: {avg_bl['total_time']:.2f}, "
          f"平均收集价值: {avg_bl['collected_value']:.2f}, 价值效率(价值/秒): {avg_bl['value_per_time']:.4f}")
    print("\n--- Lyapunov V2 ---")
    print(f"平均成功率: {avg_ly['success_rate']:.4f}, 平均总时间: {avg_ly['total_time']:.2f}, "
          f"平均收集价值: {avg_ly['collected_value']:.2f}, 平均跳过: {avg_ly.get('skipped', 0):.2f}, "
          f"价值效率(价值/秒): {avg_ly['value_per_time']:.4f}")
    print("="*50)