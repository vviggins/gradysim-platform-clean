import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
import numpy as np

# ==============================================================================
# 全局配置 (Global Configuration)
# ==============================================================================
# --- 移除中文字体设置，因为我们现在使用英文 ---
# plt.rcParams['font.sans-serif'] = ['SimHei']
# plt.rcParams['axes.unicode_minus'] = False

LOG_CSV_FILE = 'simulation_log.csv' # 唯一的数据源
OUTPUT_DIR = 'plots_final'          # 使用新的输出文件夹名
# ------------------------------------------------------------------------------

# ==============================================================================
# 绘图函数区 (Plotting Functions)
# ==============================================================================

def plot_custom_bar_comparison(df, x_col, y_col, title, y_label):
    """
    一个完全自定义的、符合你审美要求的对比柱状图函数。
    - 使用你喜欢的柔和配色。
    - 自动计算均值作为柱高，标准差作为误差棒。
    - 在柱顶显示精确的平均值。
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    # --- 使用你喜欢的颜色，并为策略指定固定颜色 ---
    strategy_colors = {
        'Baseline': '#FC9E79',   # 柔和的橙色
        'LyapunovV5': '#7DCBB2'  # 柔和的青色/绿色
    }
    
    strategies = sorted(df['strategy'].unique())
    x_ticks = sorted(df[x_col].unique())
    
    fig, ax = plt.subplots(figsize=(10, 6.5))
    
    num_strategies = len(strategies)
    bar_width = 0.8 / num_strategies
    
    for i, strategy_name in enumerate(strategies):
        # --- 核心改造：在这里进行数据聚合 ---
        # 按 x_col (e.g., num_nodes) 分组，计算 y_col 的均值和标准差
        grouped = df[df['strategy'] == strategy_name].groupby(x_col)[y_col]
        means = grouped.mean().reindex(x_ticks).values
        stds = grouped.std().reindex(x_ticks).fillna(0).values # fillna(0) 防止只有一个数据点时标准差为NaN
        
        # 计算每个柱子的精确位置
        x_positions = np.arange(len(x_ticks)) + i * bar_width - (num_strategies - 1) / 2.0 * bar_width
        
        bars = ax.bar(
            x_positions, means, width=bar_width, 
            label=strategy_name, 
            color=strategy_colors.get(strategy_name, 'grey'), # 从字典获取颜色
            edgecolor='black', alpha=0.9,
            yerr=stds, capsize=5 # <-- 添加误差棒！
        )
        
        # 在柱顶添加数值标签（显示均值）
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2.0, yval + np.sign(yval)*0.1, f'{yval:.2f}', 
                    va='bottom', ha='center', fontsize=9.5, color='black')

    # --- 英文标签和美化 ---
    sns.despine(fig=fig)
    ax.set_xlabel('Problem Size (Number of Nodes)', fontsize=14, labelpad=10)
    ax.set_ylabel(y_label, fontsize=14, labelpad=10)
    ax.set_title(title, fontsize=16, fontweight='bold', pad=15)
    ax.set_xticks(np.arange(len(x_ticks)))
    ax.set_xticklabels([f"TSP-{scale}" for scale in x_ticks])
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.legend(title="Strategy", fontsize=12, frameon=True, facecolor='white', framealpha=0.8)
    ax.grid(axis='y', linestyle='--', linewidth=0.6)
    fig.tight_layout(pad=2.0)
    
    safe_title = "".join(c for c in title if c.isalnum()).lower()
    output_path = os.path.join(OUTPUT_DIR, f'{safe_title}_comparison.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Custom bar chart saved to: {output_path}")
    plt.close(fig)

def plot_milestone_comparison(df_milestone, scales_to_plot):
    """
    绘制“六合一”IoT数据收集时间对比图，风格美化。
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 8))
    
    df_plot = df_milestone[df_milestone['num_nodes'].isin(scales_to_plot)].copy()
    df_plot['collected_data_mb'] = df_plot['collected_data_kb'] / 1024.0

    sns.lineplot(
        data=df_plot,
        x='collected_data_mb',
        y='time_to_collect',
        hue='strategy',
        style='num_nodes',
        markers=True,
        markersize=8,
        dashes=False,
        palette={'Baseline': '#E69F00', 'LyapunovV5': '#56B4E9'},
        linewidth=2.5,
        ax=ax
    )
    
    sns.despine(fig=fig)

    ax.set_xlabel('Target Data Volume (MB)', fontsize=14, labelpad=10)
    ax.set_ylabel('Average Time to Collect (s)', fontsize=14, labelpad=10)
    ax.set_title('Data Collection Efficiency across Strategies and Scales', fontsize=16, fontweight='bold', pad=15)
    ax.tick_params(axis='both', which='major', labelsize=12)
    # 优化图例
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles=handles, labels=labels, title="Strategy (Scale)", fontsize=11, frameon=True, facecolor='white', framealpha=0.7)
    ax.grid(True, which='both', linestyle='--', linewidth=0.6)
    fig.tight_layout(pad=2.0)
    
    output_path = os.path.join(OUTPUT_DIR, 'iot_milestone_comparison.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {output_path}")
    plt.close(fig)

def plot_performance_trajectory(df_trajectory, scale):
    """
    绘制性能轨迹图，自动带置信区间，风格美化。
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 8))

    df_scale = df_trajectory[df_trajectory['num_nodes'] == scale].copy()
    df_scale['collected_data_mb'] = df_scale['collected_data_kb'] / 1024.0

    sns.lineplot(
        data=df_scale,
        x='time',
        y='collected_data_mb',
        hue='strategy',
        palette={'Baseline': '#D55E00', 'LyapunovV5': '#0072B2'}, # 使用更具对比度的颜色
        linewidth=2.8,
        ax=ax,
        errorbar='sd'  # 正确的用法，显示标准差
    )
    
    sns.despine(fig=fig)

    ax.set_xlabel('Mission Time (s)', fontsize=14, labelpad=10)
    ax.set_ylabel('Cumulative Data Collected (MB)', fontsize=14, labelpad=10)
    ax.set_title(f'Data Collection Trajectory for TSP-{scale} Scenario', fontsize=16, fontweight='bold', pad=15)
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.legend(title="Strategy", fontsize=12, loc='lower right', frameon=True, facecolor='white', framealpha=0.8)
    ax.grid(True, which='both', linestyle='--', linewidth=0.6)
    fig.tight_layout(pad=2.0)

    output_path = os.path.join(OUTPUT_DIR, f'performance_trajectory_tsp_{scale}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {output_path}")
    plt.close(fig)

# ==============================================================================
# 主程序入口 (Main Entry Point)
# ==============================================================================
if __name__ == '__main__':
    try:
        df_log = pd.read_csv(LOG_CSV_FILE)
    except FileNotFoundError:
        print(f"Error: Log file '{LOG_CSV_FILE}' not found. Please run the simulation script first.")
        sys.exit(1)
        
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print(f"Successfully loaded data from '{LOG_CSV_FILE}'. Starting plotting process...")

    # --- 1. 使用你自定义的函数绘制最终指标对比图 ---
    df_final = df_log[df_log['record_type'] == 'final_stats'].copy()
    if not df_final.empty:
        print("\n--- Generating final metric comparison charts (custom style) ---")
        metrics_to_plot = {
            'total_time': ('Total Mission Time Comparison', 'Average Total Time (s)'),
            'energy_consumed': ('Total Energy Consumption', 'Average Energy Consumed'),
            'collected_value': ('Total Collected Value', 'Average Collected Value'),
            'success_nodes': ('Successful Nodes Visited', 'Average Successful Nodes')
        }
        for col, (title, ylabel) in metrics_to_plot.items():
            if col in df_final.columns:
                # 调用你自定义的、美化过的柱状图函数
                plot_custom_bar_comparison(df_final, 'num_nodes', col, title, ylabel)
    
    # --- 2. 绘制 "6-in-1" 里程碑图 (保持不变) ---
    df_milestone = df_log[df_log['record_type'] == 'milestone'].copy()
    if not df_milestone.empty:
        print("\n--- Generating IoT milestone comparison chart ---")
        plot_milestone_comparison(df_milestone, scales_to_plot=[100, 150, 200])
        
    # --- 3. 绘制性能轨迹图 (保持不变) ---
    df_trajectory = df_log[df_log['record_type'] == 'trajectory'].copy()
    if not df_trajectory.empty:
        print("\n--- Generating performance trajectory charts ---")
        scales_for_trajectory = sorted(df_trajectory['num_nodes'].unique())
        for scale in scales_for_trajectory:
             if scale in [100, 150, 200]:
                plot_performance_trajectory(df_trajectory, scale)
                
    print("\nAll plotting tasks completed!")