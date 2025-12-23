import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import seaborn as sns

# --- 全局字体设置 (解决中文显示问题) ---
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
# ------------------------------------

# --- 全局配置 ---
RESULTS_CSV_FILE = 'simulation_results2.csv'
OUTPUT_DIR = 'plots_4'
IOT_AGG_CSV_FILE = 'iot_aggregated_results.csv' # <-- 新增这一行
# ----------------

# ==============================================================================
# 函数定义区 (Functions Definitions)
# ==============================================================================

def plot_bar_comparison(df, x_col, y_col, title, y_label):
    """通用的对比柱状图绘图函数 (优化版)。"""
    plt.style.use('seaborn-v0_8-whitegrid')
    colors = plt.get_cmap('Set2').colors   # 更柔和的专业配色
    
    strategies = sorted(df['strategy'].unique())
    x_ticks = sorted(df[x_col].unique())
    
    fig, ax = plt.subplots(figsize=(10, 6.5))
    
    num_strategies = len(strategies)
    bar_width = 0.8 / num_strategies
    
    for i, strategy_name in enumerate(strategies):
        strategy_df = df[df['strategy'] == strategy_name]
        x_positions = np.arange(len(x_ticks)) + i * bar_width - (num_strategies - 1) / 2.0 * bar_width
        y_values = [strategy_df[strategy_df[x_col] == xtick][y_col].values[0] for xtick in x_ticks]
        bars = ax.bar(
            x_positions, y_values, width=bar_width, 
            label=strategy_name, color=colors[i % len(colors)], 
            edgecolor='black', alpha=0.85
        )
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:.2f}', 
                    va='bottom', ha='center', fontsize=9)

    ax.set_xlabel('Problem Size (Nodes)', fontsize=14, labelpad=10)   # 改英文
    ax.set_ylabel(y_label, fontsize=14, labelpad=10)                  # 改英文
    ax.set_title(title, fontsize=16, fontweight='bold', pad=15)
    ax.set_xticks(np.arange(len(x_ticks)))
    ax.set_xticklabels([f"TSP-{scale}" for scale in x_ticks])
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.legend(fontsize=12, frameon=True, facecolor='white', framealpha=0.8, loc='best')
    ax.grid(True, which='both', linestyle='--', linewidth=0.6)
    fig.tight_layout(pad=2.0)
    
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
    output_path = os.path.join(OUTPUT_DIR, f'{safe_title.replace(" ", "_").lower()}_barchart.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"柱状图已成功保存到: {output_path}")
    plt.close(fig)

def plot_line_comparison(df, x_col, y_col, title, y_label):
    """通用的折线对比图绘图函数 (优化版)。"""
    plt.style.use('seaborn-v0_8-whitegrid')
    colors = plt.get_cmap('Set2').colors
    styles = {
        'Baseline':   {'color': colors[0], 'marker': 's', 'linestyle': '--', 'linewidth': 2, 'label': 'Baseline (Offline)'},
        'LyapunovV5': {'color': colors[1], 'marker': 'o', 'linestyle': '-',  'linewidth': 2.2, 'label': 'Lyapunov V5 (Online)'}
    }
    fig, ax = plt.subplots(figsize=(10, 6.5))
    strategy_order = ['Baseline', 'LyapunovV5']
    for strategy_name in strategy_order:
        if strategy_name in df['strategy'].unique():
            strategy_df = df[df['strategy'] == strategy_name]
            style_props = styles.get(strategy_name, {})
            ax.plot(strategy_df[x_col], strategy_df[y_col], markersize=7, **style_props)

    ax.set_xlabel('Problem Size (Nodes)', fontsize=14, labelpad=10)   # 改英文
    ax.set_ylabel(y_label, fontsize=14, labelpad=10)                  # 改英文
    ax.set_title(title, fontsize=16, fontweight='bold', pad=15)
    unique_scales = sorted(df[x_col].unique())
    ax.set_xticks(unique_scales)
    ax.set_xticklabels([f"TSP-{scale}" for scale in unique_scales])
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.legend(fontsize=12, frameon=True, facecolor='white', framealpha=0.8, loc='best')
    ax.grid(True, which='both', linestyle='--', linewidth=0.6)
    fig.tight_layout(pad=2.0)

    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
    output_path = os.path.join(OUTPUT_DIR, f'{safe_title.replace(" ", "_").lower()}_linechart.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"折线图已成功保存到: {output_path}")
    plt.close(fig)
    
# def plot_iot_integrated_comparison(df, x_col='collected_data_kb', y_col='time_to_collect', title='不同策略与规模下的数据收集效率对比'):
#     """“六合一”IoT绘图函数，包含了所有你要求的修改。"""
#     plt.style.use('seaborn-v0_8-whitegrid')
#     fig, ax = plt.subplots(figsize=(12, 8))
# #e41a1c
#     strategy_colors = { 'Baseline': '#377eb8', 'LyapunovV5': '#e41a1c' }
#     scale_styles = {
#         100: {'linestyle': '--', 'marker': 's', 'label_suffix': '(TSP-100)'},
#         150: {'linestyle': ':', 'marker': '^', 'label_suffix': '(TSP-150)'},
#         200: {'linestyle': '-.', 'marker': 'D', 'label_suffix': '(TSP-200)'}
#     }
    
#     scales_to_plot = [100, 150, 200]
#     iot_df = df[(df[x_col].notna()) & (df[y_col].notna()) & (df['num_nodes'].isin(scales_to_plot))].copy()
    
#     if iot_df.empty:
#         print("警告: 未找到指定规模 (100, 150, 200) 的有效IoT数据用于绘制集成图。")
#         return
        
#     iot_df['collected_data_mb'] = iot_df[x_col] / 1024.0
#     x_col_mb = 'collected_data_mb'
#     agg_iot_df = iot_df.groupby(['strategy', 'num_nodes', x_col_mb])[y_col].mean().reset_index()

#     strategies = ['Baseline', 'LyapunovV5']
    
#     for strategy_name in strategies:
#         for scale in scales_to_plot:
#             plot_data = agg_iot_df[(agg_iot_df['strategy'] == strategy_name) & (agg_iot_df['num_nodes'] == scale)]
#             color = strategy_colors.get(strategy_name, 'gray')
#             style = scale_styles.get(scale, {})
#             label = f"{strategy_name} {style.get('label_suffix', '')}"
#             if not plot_data.empty:
#                 ax.plot(plot_data[x_col_mb], plot_data[y_col], color=color, 
#                         linestyle=style['linestyle'], marker=style['marker'], label=label, markersize=7, linewidth=2)

#     ax.set_xlabel('目标收集数据量 (MB)', fontsize=14, labelpad=10)
#     ax.set_ylabel('平均任务时间 (秒)', fontsize=14, labelpad=10)
#     ax.set_title(title, fontsize=16, fontweight='bold', pad=15)
    
#     unique_data_targets_mb = sorted(agg_iot_df[x_col_mb].unique())
#     ax.set_xticks(unique_data_targets_mb)
#     ax.set_xticklabels([f"{target:.0f}" for target in unique_data_targets_mb])
#     ax.tick_params(axis='both', which='major', labelsize=12)
    
#     ax.legend(title="策略 (规模)", fontsize=10, loc='upper left', 
#               bbox_to_anchor=(0.01, 0.99), frameon=True, facecolor='white', framealpha=0.7)
    
#     ax.grid(True, which='both', linestyle='--', linewidth=0.5)
#     fig.tight_layout()
    
#     if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
#     safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
#     output_path = os.path.join(OUTPUT_DIR, f'{safe_title.replace(" ", "_").lower()}_integrated_iot_filtered.png')
    
#     plt.savefig(output_path, dpi=300, bbox_inches='tight')
#     print(f"“六合一”IoT集成图已成功保存到: {output_path}")
#     plt.close(fig)
def plot_iot_integrated_comparison(df_agg, #<-- 注意：传入的是已经聚合好的DataFrame
                                   x_col='collected_data_mb',
                                   y_col='avg_time_to_collect',
                                   title='不同策略与规模下的数据收集效率对比'):
    """
    “纯粹”绘图版（**只负责画图，不进行任何计算**）：
    - 直接使用从 'iot_aggregated_results.csv' 读取的、已聚合的数据。
    - 视觉风格保持不变。
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 8))

    strategy_colors = { 'Baseline': '#7DCBB2', 'LyapunovV5': '#ff7f0e' }
    scale_styles = {
        100: {'linestyle': '--', 'marker': 'o', 'label_suffix': '(TSP-100)'},
        150: {'linestyle': ':',  'marker': '^', 'label_suffix': '(TSP-150)'},
        200: {'linestyle': '-.', 'marker': 'v', 'label_suffix': '(TSP-200)'}
    }

    scales_to_plot = [100, 200] # 从数据中动态获取规模
    strategies = ['Baseline', 'LyapunovV5']

    # 绘图逻辑现在更简单：直接遍历数据进行绘制
    for strategy_name in strategies:
        for scale in scales_to_plot:
            # 直接从聚合好的数据中筛选出要画的这一条线
            plot_data = df_agg[(df_agg['strategy'] == strategy_name) & (df_agg['num_nodes'] == scale)]
            if not plot_data.empty:
                color = strategy_colors.get(strategy_name, 'gray')
                style = scale_styles.get(scale, {})
                label = f"{strategy_name} {style.get('label_suffix', '')}"
                
                ax.plot(
                    plot_data[x_col], plot_data[y_col], # 直接使用传入的列名
                    color=color,
                    linestyle=style['linestyle'],
                    marker=style['marker'],
                    label=label,
                    markersize=7,
                    linewidth=2.2,
                    alpha=0.95
                )

    # --- 坐标轴、标题、图例等美化部分保持不变 ---
    ax.set_xlabel('Target Data Size (MB)', fontsize=14, labelpad=10)
    ax.set_ylabel('Average Task Time (s)', fontsize=14, labelpad=10)
    ax.set_title(title, fontsize=16, fontweight='bold', pad=15)

    unique_data_targets_mb = sorted(df_agg[x_col].unique())
    ax.set_xticks(unique_data_targets_mb)
    ax.set_xticklabels([f"{target:.0f}" for target in unique_data_targets_mb])
    ax.tick_params(axis='both', which='major', labelsize=12)

    ax.legend(
        title="Strategy (Scale)", fontsize=10, loc='upper right',
        frameon=True, facecolor='white', framealpha=0.85
    )

    ax.grid(True, which='both', linestyle='--', linewidth=0.6)
    fig.tight_layout(pad=2.0)

    # 保存逻辑保持不变
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
    output_path = os.path.join(OUTPUT_DIR, f'{safe_title.replace(" ", "_").lower()}_integrated_iot_filtered.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"纯粹绘图版IoT集成图已成功保存到: {output_path}")
    plt.close(fig)
    
def plot_performance_trajectory(df_traj, scale, title_suffix):
    """
    绘制“数据量 vs 时间”的性能轨迹图，自动带置信区间。
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 8))

    # 筛选出特定规模的数据
    df_scale = df_traj[df_traj['num_nodes'] == scale].copy()
    
    if df_scale.empty:
        print(f"警告: 找不到规模为 {scale} 的轨迹数据，跳过绘图。")
        return

    # 单位转换 KB -> MB
    df_scale['collected_data_mb'] = df_scale['collected_data_kb'] / 1024.0

    # 使用 Seaborn 绘图，它会自动处理平均和置信区间
    sns.lineplot(
        data=df_scale,
        x='time',
        y='collected_data_mb',
        hue='strategy',
        palette={'Baseline': '#e41a1c', 'LyapunovV5': '#377eb8'},
        linewidth=2.5,
        ax=ax,
        errorbar='sd' # <--- 修改为新的推荐参数
    )

    ax.set_xlabel('任务时间 (秒)', fontsize=14, labelpad=10)
    ax.set_ylabel('累计收集数据量 (MB)', fontsize=14, labelpad=10)
    ax.set_title(f'不同策略在 {title_suffix} 场景下的数据收集效率', fontsize=16, fontweight='bold', pad=15)
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.legend(title="策略", fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.6)
    fig.tight_layout(pad=2.0)

    # 保存
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    output_path = os.path.join(OUTPUT_DIR, f'performance_trajectory_tsp_{scale}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"性能轨迹图已成功保存到: {output_path}")
    plt.close(fig)
    
    
# ==============================================================================
# 主程序入口 (Main Entry Point)
# ==============================================================================
if __name__ == '__main__':
    try:
        df = pd.read_csv(RESULTS_CSV_FILE)
    except FileNotFoundError:
        print(f"错误: 找不到结果文件 '{RESULTS_CSV_FILE}'。请确认文件名是否正确。")
        sys.exit(1)

    # =========================================================================
    # 第一部分：处理和绘制你原有的5张图 (逻辑已修复且包含完整绘图调用)
    # =========================================================================
    df_original_metrics = df[df['collected_data_kb'].isna()] if 'collected_data_kb' in df.columns else df
    
    if not df_original_metrics.empty:
        print("\n" + "="*50)
        print("正在处理和绘制5张基础对比图...")

        agg_df_mean = df_original_metrics.groupby(['num_nodes', 'strategy']).mean().reset_index()
        agg_df_sum = df_original_metrics.groupby(['num_nodes', 'strategy']).sum().reset_index()
        
        # 安全地合并求和与求平均的数据
        agg_df_final = pd.merge(agg_df_mean, agg_df_sum, 
                                on=['num_nodes', 'strategy'], 
                                suffixes=('_mean', '_sum'), 
                                how='left')
        
        # 安全地计算复合指标
        if 'success_nodes_sum' in agg_df_final.columns and 'fail_nodes_sum' in agg_df_final.columns:
            # 避免除以0的错误
            total_nodes = agg_df_final['success_nodes_sum'] + agg_df_final['fail_nodes_sum']
            agg_df_final['success_rate'] = agg_df_final['success_nodes_sum'].divide(total_nodes).fillna(0) * 100
        
        if 'collected_value_sum' in agg_df_final.columns and 'total_time_sum' in agg_df_final.columns:
            agg_df_final['value_efficiency'] = agg_df_final['collected_value_sum'].divide(agg_df_final['total_time_sum']).fillna(0)

        print("按规模聚合后的最终结果 (原始指标):")
        print(agg_df_final.head())
        
        # <<<--- 关键修复: 使用被merge重命名后的新列名 ('_mean' 后缀) --->>>
        line_metrics = {
            'collected_value_mean': ('数据收集量随规模变化', '平均收集总价值'),
            'success_rate': ('任务成功率随规模变化', '平均成功率 (%)'),
            'value_efficiency': ('价值效率随规模变化', '平均价值效率 (价值/秒)')
        }
        
        bar_metrics = {
            'total_time_mean': ('任务完成时间随规模变化', '平均总时间 (秒)'),
            'energy_consumed_mean': ('任务总能耗随规模变化', '平均总能耗 (能量单位)'),
        }
        # <<<---------------------------------------------------------------->>>

        df_to_plot = agg_df_final[agg_df_final['strategy'].isin(['Baseline', 'LyapunovV5'])]

        # --- 完整的绘图循环 ---
        # 循环绘制折线图
        for y_col, (title, y_label) in line_metrics.items():
            if y_col in df_to_plot.columns:
                # 注意：我们传给绘图函数的y_col是带_mean的，但标签y_label是干净的
                plot_line_comparison(df_to_plot, x_col='num_nodes', y_col=y_col, title=title, y_label=y_label)

        # 循环绘制柱状图
        for y_col, (title, y_label) in bar_metrics.items():
            if y_col in df_to_plot.columns:
                plot_bar_comparison(df_to_plot, x_col='num_nodes', y_col=y_col, title=title, y_label=y_label)
        
        print("5张基础对比图绘制完成。")

    # =========================================================================
    # 第二部分：绘制你全新的“六合一”IoT图 (逻辑独立)
    # =========================================================================
    try:
        # 尝试读取由模拟脚本计算好的聚合数据
        df_iot_agg = pd.read_csv(IOT_AGG_CSV_FILE)
        print("\n" + "="*50)
        print(f"成功读取聚合IoT数据文件 '{IOT_AGG_CSV_FILE}'，正在绘制...")
        # 调用纯粹的绘图函数，传入已聚合的数据
        plot_iot_integrated_comparison(df_agg=df_iot_agg)
        print("="*50)
    except FileNotFoundError:
        # 如果找不到聚合文件，打印一个有用的提示
        print("\n" + "="*50)
        print(f"警告: 未找到IoT聚合结果文件 '{IOT_AGG_CSV_FILE}'。")
        print("请先运行修改后的模拟实验脚本来生成此文件。跳过IoT图的绘制。")
        print("="*50)
        
    try:
        df_trajectory = pd.read_csv('simulation_trajectory.csv')
        for scale in [100, 150, 200]: # 为每个你关心的规模单独画一张轨迹图
            plot_performance_trajectory(df_trajectory, scale, f"TSP-{scale}")
    except FileNotFoundError:
        print("警告: 未找到 'simulation_trajectory.csv' 文件，跳过性能轨迹图绘制。")