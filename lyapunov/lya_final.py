import numpy as np
import random
import sys
import os
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from python_tsp.heuristics import solve_tsp_simulated_annealing
import time 

# ==============================================================================
# 1. 配置中心 (Config Center)
# ==============================================================================
class Config:
    def __init__(self, seed=42):
        
        # IOT相关内容   == 物联网数据收集
        self.DATA_TRANSFER_RATE = 500.0  # 数据传输速率 (KB/秒)，相当于0.5 MB/s
        self.DATA_PER_NODE_AVG = 250.0   # 每个节点的平均数据量 (KB)
        self.DATA_PER_NODE_STD = 100.0   # 每个节点数据量的标准差 (KB)
        
        # 目标里程碑也相应地调整为 KB
        # 10MB -> 10240 KB, 15MB -> 15360 KB, etc.
        # 收集数据 10MB  15MB 20MB 25MB 30MB    
        self.TARGET_DATA_MILESTONES = [10240, 15360, 20480, 25600, 30720]
        
        self.MAX_ATTEMPTS = 3      
        self.COMM_TIME = 8       
        self.UAV_SPEED = 5      
        self.UAV_BATTERY_CAPACITY = 1600.0
        self.ENERGY_PER_METER_FLIGHT = 0.1
        self.ENERGY_PER_SECOND_HOVER = 0.6
        self.LYAPUNOV_V = 2.0 # 经过调优的V值
        self.LYAPUNOV_THRESHOLD = 0.0 # 经过调优的阈值
        self.TSP_ALPHA = 0.995
        self.SEED = seed
        self.COORDS_FILE_PATH = None
        
        random.seed(self.SEED)
        np.random.seed(self.SEED)

# ==============================================================================
# 2. 模拟环境 (Simulation Environment)
# ==============================================================================
class SimulationEnvironment:
    def __init__(self, config: Config):
        self.config = config
        self.coords = self._load_coords()
        self.num_nodes = len(self.coords)
        self.distances = self._compute_distances()
        self.node_values = self._generate_node_values()
        self.node_data_payloads = self._generate_node_data()     # 物联网节点数据加载
    def _load_coords(self):
        if not self.config.COORDS_FILE_PATH:
            raise ValueError("必须在Config中指定 COORDS_FILE_PATH！")
        try:
            coords_data = np.loadtxt(self.config.COORDS_FILE_PATH)
            if np.array_equal(coords_data[0], coords_data[-1]):
                return coords_data[:-1]
            return coords_data
        except Exception as e:
            print(f"错误: 加载坐标文件 '{self.config.COORDS_FILE_PATH}' 失败: {e}")
            sys.exit(1)

    def _compute_distances(self):
        # 假设坐标文件已经是真实世界的米制坐标
        return squareform(pdist(self.coords, metric='euclidean'))

    def _generate_node_values(self):
        values = np.ones(self.num_nodes)
        high_value_indices = np.random.choice(self.num_nodes, size=int(0.1 * self.num_nodes), replace=False)
        values[high_value_indices] = 5.0
        return {i: values[i] for i in range(self.num_nodes)}

    def get_communication_success_prob(self, node_index):
        base_prob = 0.65 
        noise = random.uniform(-0.4, 0.4)
        return max(0, min(1, base_prob + noise))

    def get_initial_tsp_path(self):
        """
        不再尝试加载外部文件，总是根据当前加载的坐标文件顺序生成路径。
        """
        # num_nodes 是在 __init__ 中根据加载的 coords 文件计算的
        path_indices = list(range(self.num_nodes))
        # 在末尾加上起点，构成闭环
        path_indices.append(path_indices[0])
        
        return path_indices
    
    def _generate_node_data(self):
        """
        为每个节点随机分配数据量。
        其中，少数“关键节点”的数据量会显著更高。
        关键节点的位置在每次模拟运行时，都会根据当前时间戳随机变化。
        """
        # --- 核心修改开始 ---
        # 1. 创建一个独立的随机数生成器实例
        #    我们使用当前时间的纳秒部分作为种子，以确保高度的随机性。
        current_time_seed = int(time.time_ns() % (2**32 - 1))
        local_rng = np.random.RandomState(seed=current_time_seed)
        # 'rng' stands for Random Number Generator. 
        # 之后所有需要“时间随机性”的操作，都使用 local_rng 而不是 np.random。
        # --- 核心修改结束 ---

        # 2. 生成基础数据量 (使用全局随机数，保证这部分可复现)
        #    这保证了在同一个run_seed下，节点的“基础数据”是一样的
        base_data = np.random.normal(150.0, 50.0, self.num_nodes)
        base_data[base_data < 50.0] = 50.0

        # 3. 使用我们新的、基于时间的随机数生成器，来选择关键节点
        num_critical_nodes = int(self.num_nodes * 0.05) # 5% 的节点是关键节点
        # 使用 local_rng.choice 而不是 np.random.choice
        critical_indices = local_rng.choice(self.num_nodes, num_critical_nodes, replace=False)

        # 4. 为这些关键节点分配海量数据
        # 同样使用 local_rng 来增加这部分的多样性
        critical_data = local_rng.normal(2000.0, 500.0, num_critical_nodes)
        critical_data[critical_data < 1000.0] = 1000.0 # 保证最小的关键数据量
        
        base_data[critical_indices] = critical_data
        
        return {i: base_data[i] for i in range(self.num_nodes)}

# ==============================================================================
# 3. 执行策略 (Execution Strategies)
# ==============================================================================
class ExecutionStrategy:
    # ... [这部分代码与之前版本完全相同，为简洁省略，请从之前版本复制]
    def __init__(self, env: SimulationEnvironment):
        self.env = env
        self.config = env.config

    def execute(self, path):
        raise NotImplementedError

    def _single_communication_attempt(self, node):
        """
        <<< 全新重构的函数 >>>
        模拟对一个节点进行【单次】通信尝试。
        
        返回: (是否成功, 本次尝试总悬停时间, 收集到的数据量)
        """
        # 1. 初始通信握手时间是固定的
        attempt_time = self.config.COMM_TIME
        
        # 2. 检查本次尝试是否成功
        if random.random() < self.env.get_communication_success_prob(node):
            # 通信成功！计算并加上数据下载时间
            data_to_download = self.env.node_data_payloads[node]
            download_time = data_to_download / self.config.DATA_TRANSFER_RATE
            attempt_time += download_time
            return True, attempt_time, data_to_download
        else:
            # 通信失败，只消耗了握手时间，没有下载数据
            return False, attempt_time, 0.0

class BaselineStrategy(ExecutionStrategy):
    # ... [这部分代码与之前版本完全相同，为简洁省略，请从之前版本复制]
    def execute(self, path):
        stats = {'collected_value': 0, 'success_nodes': 0, 'fail_nodes': 0, 'total_time': 0.0, 'energy_consumed': 0.0, 'skipped_nodes': 0}
        trajectory = [(0, 0)] # <<< 新增：初始化轨迹，从(0时间, 0数据)开始
        success_node_set = set()
        total_data_collected = 0.0
        milestone_times = {}

        for i in range(len(path) - 1):
            current_node, next_node = path[i], path[i+1]
            
            # 1. 飞行
            flight_dist = self.env.distances[current_node][next_node]
            flight_energy = flight_dist * self.config.ENERGY_PER_METER_FLIGHT
            flight_time = flight_dist / self.config.UAV_SPEED

            # 检查飞行能量是否足够
            if stats['energy_consumed'] + flight_energy > self.config.UAV_BATTERY_CAPACITY:
                break # 连飞到下一个节点的能量都不够了，任务结束
            
            # 更新飞行后的状态
            stats['energy_consumed'] += flight_energy
            stats['total_time'] += flight_time

            # <<< Baseline核心逻辑：无限重试直到成功或能源耗尽 >>>
            is_success_at_node = False
            total_hover_time_at_node = 0.0
            data_collected_at_node = 0.0

            while True: # 无限循环，代表“执着地”尝试
                # 模拟单次尝试
                is_success, hover_time, data_collected = self._single_communication_attempt(current_node)
                hover_energy = hover_time * self.config.ENERGY_PER_SECOND_HOVER

                # 检查是否有足够能量执行【这次】尝试
                if stats['energy_consumed'] + hover_energy > self.config.UAV_BATTERY_CAPACITY:
                    # 能量不足以完成本次尝试，放弃该节点
                    break # 跳出 while 循环

                # 能量充足，正式消耗时间和能量
                stats['total_time'] += hover_time
                stats['energy_consumed'] += hover_energy
                total_hover_time_at_node += hover_time

                if is_success:
                    # 成功了！记录结果并跳出循环
                    is_success_at_node = True
                    data_collected_at_node = data_collected
                    break # 跳出 while 循环
            
            # <<< 循环结束，根据最终结果更新统计数据 >>>
            if is_success_at_node:
                if current_node not in success_node_set:
                    stats['collected_value'] += self.env.node_values[current_node]
                    stats['success_nodes'] += 1
                    success_node_set.add(current_node)
                
                # 更新IoT数据
                prev_data_total = total_data_collected
                total_data_collected += data_collected_at_node
                
                trajectory.append((stats['total_time'], total_data_collected)) # <<< 新增：记录当前时间点和累计数据量

                # 检查并记录里程碑 (插值计算)
                for milestone in self.config.TARGET_DATA_MILESTONES:
                    if milestone not in milestone_times and total_data_collected >= milestone:
                        overshoot_data = total_data_collected - milestone
                        overshoot_time = overshoot_data / self.config.DATA_TRANSFER_RATE
                        exact_time = stats['total_time'] - overshoot_time
                        milestone_times[milestone] = exact_time
            else:
                # 循环结束了但依然没成功（说明是能量耗尽）
                stats['fail_nodes'] += 1
        
        stats['milestone_times'] = milestone_times
        stats['trajectory'] = trajectory # <<< 新增：将轨迹附加到返回结果中
        return stats

class LyapunovStrategyV4(ExecutionStrategy):
    # ... [这部分代码与之前版本完全相同，为简洁省略，请从之前版本复制]
    def execute(self, path):
        stats = {'collected_value': 0, 'success_nodes': 0, 'fail_nodes': 0, 'total_time': 0.0, 'energy_consumed': 0.0, 'skipped_nodes': 0}
        success_node_set = set()
        backlog = 0.0
        total_data_collected = 0.0
        milestone_times = {}
        
        trajectory = [(0, 0)] # <<< 新增：初始化轨迹，从(0时间, 0数据)开始

        for i in range(len(path) - 1):
            current_node, next_node = path[i], path[i+1]
            
            # 1. 飞行
            flight_dist = self.env.distances[current_node][next_node]
            flight_energy = flight_dist * self.config.ENERGY_PER_METER_FLIGHT
            flight_time = flight_dist / self.config.UAV_SPEED

            if stats['energy_consumed'] + flight_energy > self.config.UAV_BATTERY_CAPACITY:
                break
            
            stats['energy_consumed'] += flight_energy
            stats['total_time'] += flight_time

            # <<< Lyapunov核心逻辑：最多尝试3次，并可提前放弃 >>>
            is_success_at_node = False
            data_collected_at_node = 0.0
            
            for attempt in range(1, self.config.MAX_ATTEMPTS + 1):
                # 模拟单次尝试
                is_success, hover_time, data_collected = self._single_communication_attempt(current_node)
                hover_energy = hover_time * self.config.ENERGY_PER_SECOND_HOVER

                # 检查能量
                if stats['energy_consumed'] + hover_energy > self.config.UAV_BATTERY_CAPACITY:
                    break # 能量不足，无法进行本次尝试，直接放弃该节点

                # 能量充足，消耗资源
                stats['energy_consumed'] += hover_energy
                stats['total_time'] += hover_time
                
                if is_success:
                    is_success_at_node = True
                    data_collected_at_node = data_collected
                    break # 成功，跳出 for 循环

                # 如果失败了，并且还有重试机会，执行Lyapunov决策
                if attempt < self.config.MAX_ATTEMPTS:
                    penalty_of_retrying = self.config.LYAPUNOV_V * backlog - self.env.get_communication_success_prob(current_node)
                    if backlog > 0 and penalty_of_retrying > self.config.LYAPUNOV_THRESHOLD:
                        stats['skipped_nodes'] += 1
                        break # Lyapunov决策：提前放弃，跳出 for 循环
            
            # <<< 循环结束，更新统计数据 >>>
            if is_success_at_node:
                if current_node not in success_node_set:
                    stats['collected_value'] += self.env.node_values[current_node]
                    stats['success_nodes'] += 1
                    success_node_set.add(current_node)
                
                total_data_collected += data_collected_at_node
                backlog = max(0, backlog - self.env.node_values[current_node])
                trajectory.append((stats['total_time'], total_data_collected)) # <<< 新增：记录当前时间点和累计数据量

                # 检查并记录里程碑
                for milestone in self.config.TARGET_DATA_MILESTONES:
                    if milestone not in milestone_times and total_data_collected >= milestone:
                        overshoot_data = total_data_collected - milestone
                        overshoot_time = overshoot_data / self.config.DATA_TRANSFER_RATE
                        exact_time = stats['total_time'] - overshoot_time
                        milestone_times[milestone] = exact_time
            else:
                # 循环结束仍未成功（可能是3次用完、能量耗尽或提前放弃）
                stats['fail_nodes'] += 1
                backlog += 1
        
        stats['milestone_times'] = milestone_times
        stats['trajectory'] = trajectory # <<< 新增：将轨迹附加到返回结果中
        return stats

# ==============================================================================
# 4. 主程序入口 (Main Entry Point) - 批量运行并保存结果
# ==============================================================================
if __name__ == "__main__":
    
    # --- 实验配置 ---
    # 1. 指定包含所有规模子文件夹的根数据目录
    ROOT_DATA_DIR = './data' 
    
    results_data = []
    results_trajectory = [] # <<< 新增一个列表，专门用于存储轨迹数据
    
    # 2. (可选) 指定一个白名单，只运行特定的规模。如果为空列表，则运行所有找到的规模。
    #    例如: SCALES_TO_RUN = [50, 100] 只会运行 node50 和 node100 文件夹
    SCALES_TO_RUN = [] # 空列表代表运行所有

    # 3. 每个数据文件，重复运行多少次来消除随机性
    NUM_RUNS_PER_FILE = 5 
    
    # 4. 结果保存文件名
    RESULTS_CSV_FILE = 'simulation_results2.csv'
    # ----------------

    # --- 智能扫描和文件收集 ---
    all_tasks = [] # 创建一个任务列表
    
    # 遍历根目录下的所有条目
    for scale_folder_name in sorted(os.listdir(ROOT_DATA_DIR)):
        # 从文件夹名中提取数字作为规模 (scale)
        try:
            scale = int(''.join(filter(str.isdigit, scale_folder_name)))
        except ValueError:
            print(f"警告: 文件夹 '{scale_folder_name}' 的名字不包含数字，跳过。")
            continue
            
        # 如果设置了白名单，就只运行白名单里的规模
        if SCALES_TO_RUN and scale not in SCALES_TO_RUN:
            continue
        
        scale_folder_path = os.path.join(ROOT_DATA_DIR, scale_folder_name)
        
        # 确保它是一个目录
        if os.path.isdir(scale_folder_path):
            # 遍历该规模文件夹下的所有 .txt 文件
            for file_name in sorted(os.listdir(scale_folder_path)):
                if file_name.endswith('.txt'):
                    coord_file_path = os.path.join(scale_folder_path, file_name)
                    # 将任务信息（规模，文件路径）添加到列表中
                    all_tasks.append({'scale': scale, 'coord_file': coord_file_path})
    
    if not all_tasks:
        print(f"错误: 在目录 '{ROOT_DATA_DIR}' 下没有找到任何有效的场景文件。请检查文件结构。")
        sys.exit(1)

    print(f"扫描完成！共找到 {len(all_tasks)} 个独立的场景文件，将在 {len(set(t['scale'] for t in all_tasks))} 个不同规模下运行。")
    # -----------------------------------

    results_data = []
    
    # 遍历所有收集到的任务
    for i, task in enumerate(all_tasks):
        scale = task['scale']
        coord_file = task['coord_file']
        scene_name = os.path.splitext(os.path.basename(coord_file))[0]

        print("\n" + "="*50)
        print(f"正在处理任务 {i+1}/{len(all_tasks)}: 规模={scale}, 文件='{scene_name}.txt'")
        print("="*50)
        
        # 对每个文件运行多次
        for j in range(NUM_RUNS_PER_FILE):
            current_seed = 42 + i * NUM_RUNS_PER_FILE + j
            config = Config(seed=current_seed)
            config.COORDS_FILE_PATH = coord_file
            config.NUM_NODES = scale # 自动设置正确的节点数
            
            # --- 运行模拟 ---
            env = SimulationEnvironment(config)
            tsp_path = env.get_initial_tsp_path()
            
            bl_strategy = BaselineStrategy(env)
            bl_stats = bl_strategy.execute(tsp_path)
            
            ly_strategy = LyapunovStrategyV4(env)
            ly_stats = ly_strategy.execute(tsp_path)
            
            for time_point, data_point in bl_stats.get('trajectory', []):
                results_trajectory.append({
                    'num_nodes': scale,
                    'strategy': 'Baseline',
                    'run_seed': current_seed,
                    'time': time_point,
                    'collected_data_kb': data_point
                })

            for time_point, data_point in ly_stats.get('trajectory', []):
                results_trajectory.append({
                    'num_nodes': scale,
                    'strategy': 'LyapunovV5',
                    'run_seed': current_seed,
                    'time': time_point,
                    'collected_data_kb': data_point
                })

            bl_stats_original = {k: v for k, v in bl_stats.items() if k != 'milestone_times'}
            ly_stats_original = {k: v for k, v in ly_stats.items() if k != 'milestone_times'}
            
            results_data.append({'num_nodes': scale, 'strategy': 'Baseline', 'run_seed': current_seed, **bl_stats_original})
            results_data.append({'num_nodes': scale, 'strategy': 'LyapunovV5', 'run_seed': current_seed, **ly_stats_original})

            # 2. 专门为IoT图表，以“长格式”记录里程碑数据
            for milestone, time_val in bl_stats.get('milestone_times', {}).items():
                results_data.append({
                    'num_nodes': scale,
                    'strategy': 'Baseline',
                    'run_seed': current_seed,
                    'collected_data_kb': milestone, 
                    'time_to_collect': time_val
                })
            for milestone, time_val in ly_stats.get('milestone_times', {}).items():
                results_data.append({
                    'num_nodes': scale,
                    'strategy': 'LyapunovV5',
                    'run_seed': current_seed,
                    'collected_data_kb': milestone,
                    'time_to_collect': time_val
                })
            # <<<------------------------------------------- >>>

    # --- 将所有详细结果保存到CSV文件 ---
    df_results = pd.DataFrame(results_data)
    df_results.to_csv(RESULTS_CSV_FILE, index=False)
    
    print("\n" + "="*60)
    print(f"所有实验完成！详细结果已保存到: {RESULTS_CSV_FILE}")
    print("="*60)
    
    print("\n正在计算和保存IoT场景的聚合结果以供绘图使用...")

# 1. 筛选出所有IoT相关的数据行
iot_df_raw = df_results[df_results['collected_data_kb'].notna()].copy()

if not iot_df_raw.empty:
    # 2. 将数据量从 KB 转换为 MB (计算步骤)
    iot_df_raw['collected_data_mb'] = iot_df_raw['collected_data_kb'] / 1024.0

    # 3. 按【策略, 节点数, 目标数据量(MB)】分组，计算【任务时间】的平均值 (核心计算)
    agg_iot_df = iot_df_raw.groupby(
        ['strategy', 'num_nodes', 'collected_data_mb']
    )['time_to_collect'].mean().reset_index()

    # 4. 为了清晰，重命名包含平均值的列
    agg_iot_df.rename(columns={'time_to_collect': 'avg_time_to_collect'}, inplace=True)
    
    # 5. 定义新的聚合结果文件名并保存
    AGGREGATED_IOT_CSV_FILE = 'iot_aggregated_results.csv'
    agg_iot_df.to_csv(AGGREGATED_IOT_CSV_FILE, index=False)
    
if results_trajectory:
    df_trajectory = pd.DataFrame(results_trajectory)
    TRAJECTORY_CSV_FILE = 'simulation_trajectory.csv'
    df_trajectory.to_csv(TRAJECTORY_CSV_FILE, index=False)
    print(f"性能轨迹数据已成功保存到: {TRAJECTORY_CSV_FILE}")
    
    print(f"IoT场景的聚合平均值已成功计算并保存到: {AGGREGATED_IOT_CSV_FILE}")
    print("现在画图脚本可以直接使用这个文件，无需再做任何计算。")
else:
    print("警告: 在详细结果中未找到IoT相关数据，无法生成聚合文件。")