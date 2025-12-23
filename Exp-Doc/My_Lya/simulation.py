import numpy as np
import random
import sys
import os
import pandas as pd
from scipy.spatial.distance import pdist, squareform
import time 

# ==============================================================================
# 1. 配置中心 (Config Center) - 强化版
# ==============================================================================
class Config:
    def __init__(self, seed=42):
        # 目标里程碑 (KB)
        self.TARGET_DATA_MILESTONES = [10240, 15360, 20480, 25600, 30720] # 10MB to 30MB
        
        # --- 强化环境以拉开策略差距 ---
        self.DATA_TRANSFER_RATE = 500.0  # KB/s
        self.UAV_SPEED = 20.0            # m/s
        self.UAV_BATTERY_CAPACITY = 3000.0 # 增加电池容量，给策略更多空间
        self.ENERGY_PER_METER_FLIGHT = 0.1
        self.ENERGY_PER_SECOND_HOVER = 0.6
        self.COMM_TIME = 8.0             # 增加单次通信握手时间成本

        # Lyapunov 策略参数
        self.MAX_ATTEMPTS = 3      
        self.LYAPUNOV_V = 2.0
        self.LYAPUNOV_THRESHOLD = 0.0
        
        self.SEED = seed
        self.COORDS_FILE_PATH = None
        
        random.seed(self.SEED)
        np.random.seed(self.SEED)

# ==============================================================================
# 2. 模拟环境 (Simulation Environment) - 强化版
# ==============================================================================
class SimulationEnvironment:
    def __init__(self, config: Config):
        self.config = config
        self.coords = self._load_coords()
        self.num_nodes = len(self.coords)
        self.distances = self._compute_distances()
        self.node_values = self._generate_node_values()
        
        # --- 强化版：先生成恶劣的通信环境 ---
        base_qualities = np.random.uniform(0.7, 1.0, self.num_nodes)
        self.bad_node_indices = np.random.choice(
            self.num_nodes, int(self.num_nodes * 0.3), replace=False
        )
        base_qualities[self.bad_node_indices] *= 0.1 # 信号质量锐减
        self.node_comm_quality = {i: base_qualities[i] for i in range(self.num_nodes)}

        self.node_data_payloads = self._generate_node_data()

    def _load_coords(self):
        # ... (此函数无需修改)
        if not self.config.COORDS_FILE_PATH: raise ValueError("必须指定 COORDS_FILE_PATH！")
        try:
            coords_data = np.loadtxt(self.config.COORDS_FILE_PATH)
            return coords_data[:-1] if np.array_equal(coords_data[0], coords_data[-1]) else coords_data
        except Exception as e:
            print(f"错误: 加载坐标文件 '{self.config.COORDS_FILE_PATH}' 失败: {e}"); sys.exit(1)

    def _compute_distances(self):
        # ... (此函数无需修改)
        return squareform(pdist(self.coords, metric='euclidean'))

    def _generate_node_values(self):
        # ... (此函数无需修改)
        values = np.ones(self.num_nodes)
        high_value_indices = np.random.choice(self.num_nodes, size=int(0.1 * self.num_nodes), replace=False)
        values[high_value_indices] = 5.0
        return {i: values[i] for i in range(self.num_nodes)}
    
    def _generate_node_data(self):
        # --- 强化版：在高风险区域放置高价值数据 ---
        base_data = np.random.normal(150.0, 50.0, self.num_nodes)
        base_data[base_data < 50.0] = 50.0
        if self.bad_node_indices.size > 0:
            num_risky_critical = min(int(len(self.bad_node_indices) * 0.5), int(self.num_nodes * 0.05))
            if num_risky_critical > 0:
                critical_indices = np.random.choice(self.bad_node_indices, num_risky_critical, replace=False)
                critical_data = np.random.normal(4000.0, 800.0, len(critical_indices))
                critical_data[critical_data < 2500.0] = 2500.0
                base_data[critical_indices] = critical_data
        return {i: base_data[i] for i in range(self.num_nodes)}
        
    def get_communication_success_prob(self, node_index):
        # --- 强化版：成功率与固有质量强相关 ---
        base_prob = 0.9 * self.node_comm_quality.get(node_index, 0.5)
        noise = random.uniform(-0.1, 0.1)
        return max(0, min(1, base_prob + noise))

    def get_initial_tsp_path(self):
        # ... (此函数无需修改)
        path_indices = list(range(self.num_nodes))
        path_indices.append(path_indices[0])
        return path_indices

# ==============================================================================
# 3. 执行策略 (Execution Strategies) - (与上一版相同, 此处为简洁省略)
# 请确保这里的 `BaselineStrategy` 和 `LyapunovStrategyV4`
# 是我们之前重构过的、能返回 `trajectory` 的版本。
# 为确保完整性，我在这里重新粘贴一遍，你可以直接替换。
# ==============================================================================
class ExecutionStrategy:
    def __init__(self, env: SimulationEnvironment):
        self.env = env
        self.config = env.config

    def execute(self, path):
        raise NotImplementedError

    def _single_communication_attempt(self, node):
        attempt_time = self.config.COMM_TIME
        if random.random() < self.env.get_communication_success_prob(node):
            data_to_download = self.env.node_data_payloads[node]
            download_time = data_to_download / self.config.DATA_TRANSFER_RATE
            attempt_time += download_time
            return True, attempt_time, data_to_download
        else:
            return False, attempt_time, 0.0

class BaselineStrategy(ExecutionStrategy):
    def execute(self, path):
        stats = {'collected_value': 0, 'success_nodes': 0, 'fail_nodes': 0, 'total_time': 0.0, 'energy_consumed': 0.0, 'skipped_nodes': 0}
        trajectory = [(0, 0)]
        success_node_set = set()
        total_data_collected = 0.0
        milestone_times = {}

        for i in range(len(path) - 1):
            current_node, next_node = path[i], path[i+1]
            flight_dist = self.env.distances[current_node][next_node]
            flight_energy = flight_dist * self.config.ENERGY_PER_METER_FLIGHT
            flight_time = flight_dist / self.config.UAV_SPEED
            if stats['energy_consumed'] + flight_energy > self.config.UAV_BATTERY_CAPACITY: break
            stats['energy_consumed'] += flight_energy; stats['total_time'] += flight_time

            is_success_at_node = False; data_collected_at_node = 0.0
            while True:
                is_success, hover_time, data_collected = self._single_communication_attempt(current_node)
                hover_energy = hover_time * self.config.ENERGY_PER_SECOND_HOVER
                if stats['energy_consumed'] + hover_energy > self.config.UAV_BATTERY_CAPACITY: break
                stats['total_time'] += hover_time; stats['energy_consumed'] += hover_energy
                if is_success:
                    is_success_at_node = True; data_collected_at_node = data_collected; break
            
            if is_success_at_node:
                if current_node not in success_node_set:
                    stats['collected_value'] += self.env.node_values[current_node]; stats['success_nodes'] += 1; success_node_set.add(current_node)
                total_data_collected += data_collected_at_node
                trajectory.append((stats['total_time'], total_data_collected))
                for milestone in self.config.TARGET_DATA_MILESTONES:
                    if milestone not in milestone_times and total_data_collected >= milestone:
                        overshoot = total_data_collected - milestone
                        overshoot_time = overshoot / self.config.DATA_TRANSFER_RATE
                        milestone_times[milestone] = stats['total_time'] - overshoot_time
            else:
                stats['fail_nodes'] += 1
        
        stats['milestone_times'] = milestone_times; stats['trajectory'] = trajectory
        return stats

class LyapunovStrategyV4(ExecutionStrategy):
    def execute(self, path):
        stats = {'collected_value': 0, 'success_nodes': 0, 'fail_nodes': 0, 'total_time': 0.0, 'energy_consumed': 0.0, 'skipped_nodes': 0}
        trajectory = [(0, 0)]
        success_node_set = set(); backlog = 0.0; total_data_collected = 0.0; milestone_times = {}

        for i in range(len(path) - 1):
            current_node, next_node = path[i], path[i+1]
            flight_dist = self.env.distances[current_node][next_node]
            flight_energy = flight_dist * self.config.ENERGY_PER_METER_FLIGHT
            flight_time = flight_dist / self.config.UAV_SPEED
            if stats['energy_consumed'] + flight_energy > self.config.UAV_BATTERY_CAPACITY: break
            stats['energy_consumed'] += flight_energy; stats['total_time'] += flight_time

            is_success_at_node = False; data_collected_at_node = 0.0
            for attempt in range(1, self.config.MAX_ATTEMPTS + 1):
                is_success, hover_time, data_collected = self._single_communication_attempt(current_node)
                hover_energy = hover_time * self.config.ENERGY_PER_SECOND_HOVER
                if stats['energy_consumed'] + hover_energy > self.config.UAV_BATTERY_CAPACITY: break
                stats['energy_consumed'] += hover_energy; stats['total_time'] += hover_time
                if is_success:
                    is_success_at_node = True; data_collected_at_node = data_collected; break
                if attempt < self.config.MAX_ATTEMPTS:
                    penalty = self.config.LYAPUNOV_V * backlog - self.env.get_communication_success_prob(current_node)
                    if backlog > 0 and penalty > self.config.LYAPUNOV_THRESHOLD:
                        stats['skipped_nodes'] += 1; break
            
            if is_success_at_node:
                if current_node not in success_node_set:
                    stats['collected_value'] += self.env.node_values[current_node]; stats['success_nodes'] += 1; success_node_set.add(current_node)
                total_data_collected += data_collected_at_node
                backlog = max(0, backlog - self.env.node_values[current_node])
                trajectory.append((stats['total_time'], total_data_collected))
                for milestone in self.config.TARGET_DATA_MILESTONES:
                    if milestone not in milestone_times and total_data_collected >= milestone:
                        overshoot = total_data_collected - milestone
                        overshoot_time = overshoot / self.config.DATA_TRANSFER_RATE
                        milestone_times[milestone] = stats['total_time'] - overshoot_time
            else:
                stats['fail_nodes'] += 1; backlog += 1
        
        stats['milestone_times'] = milestone_times; stats['trajectory'] = trajectory
        return stats

# ==============================================================================
# 4. 主程序入口 (Main Entry Point) - 全新重构版
# ==============================================================================
if __name__ == "__main__":
    
    # --- 核心配置 ---
    ROOT_DATA_DIR = '../data' 
    SCALES_TO_RUN = [] # 空列表代表运行所有, [50, 100] 只运行特定规模
    NUM_RUNS_PER_FILE = 5 
    LOG_CSV_FILE = 'simulation_log.csv' # 唯一的输出文件

    # --- 智能扫描和文件收集 (无变化) ---
    all_tasks = []
    # ... (此处省略与你原来版本完全相同的扫描代码) ...
    for scale_folder_name in sorted(os.listdir(ROOT_DATA_DIR)):
        try:
            scale = int(''.join(filter(str.isdigit, scale_folder_name)))
        except ValueError: continue
        if SCALES_TO_RUN and scale not in SCALES_TO_RUN: continue
        scale_folder_path = os.path.join(ROOT_DATA_DIR, scale_folder_name)
        if os.path.isdir(scale_folder_path):
            for file_name in sorted(os.listdir(scale_folder_path)):
                if file_name.endswith('.txt'):
                    all_tasks.append({'scale': scale, 'coord_file': os.path.join(scale_folder_path, file_name)})
    if not all_tasks: print(f"错误: 在 '{ROOT_DATA_DIR}' 下未找到任何有效的场景文件。"); sys.exit(1)
    print(f"扫描完成！共找到 {len(all_tasks)} 个独立的场景文件...")

    # --- 统一的日志记录列表 ---
    all_log_records = []
    
    # --- 实验主循环 ---
    for i, task in enumerate(all_tasks):
        scale, coord_file = task['scale'], task['coord_file']
        print(f"\n--- 任务 {i+1}/{len(all_tasks)}: 规模={scale}, 文件='{os.path.basename(coord_file)}' ---")
        
        for j in range(NUM_RUNS_PER_FILE):
            run_seed = 42 + i * NUM_RUNS_PER_FILE + j
            
            config = Config(seed=run_seed); config.COORDS_FILE_PATH = coord_file
            env = SimulationEnvironment(config)
            path = env.get_initial_tsp_path()
            
            strategies = {'Baseline': BaselineStrategy(env), 'LyapunovV5': LyapunovStrategyV4(env)}
            
            for name, instance in strategies.items():
                stats = instance.execute(path)
                
                # 定义一个基础记录，用于共享信息
                base_record = {'num_nodes': scale, 'strategy': name, 'run_seed': run_seed}
                
                # 记录 1: 最终统计 (final_stats)
                final_stats = stats.copy()
                final_stats.pop('milestone_times', None); final_stats.pop('trajectory', None)
                all_log_records.append({**base_record, 'record_type': 'final_stats', **final_stats})
                
                # 记录 2: 里程碑 (milestone)
                for kb, t in stats.get('milestone_times', {}).items():
                    all_log_records.append({**base_record, 'record_type': 'milestone', 'collected_data_kb': kb, 'time_to_collect': t})
                
                # 记录 3: 轨迹 (trajectory)
                for t, kb in stats.get('trajectory', []):
                    all_log_records.append({**base_record, 'record_type': 'trajectory', 'time': t, 'collected_data_kb': kb})

    # --- 将所有记录一次性写入唯一的CSV文件 ---
    df_log = pd.DataFrame(all_log_records)
    df_log.to_csv(LOG_CSV_FILE, index=False)
    
    print("\n" + "="*60)
    print(f"所有实验运行完毕！全部原始数据已保存至: {LOG_CSV_FILE}")
    print("="*60)