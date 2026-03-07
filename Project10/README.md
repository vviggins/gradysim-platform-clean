# Project10：Lyapunov V 对“数据收集量 vs 飞行时间”的权衡实验

## 目标
在固定场景下，仅调节 Lyapunov 参数 V，观察：
- 左轴：任务总时间（飞行 + 通信）
- 右轴：收集到的数据量（KB/MB）

预期：V 增大 => 容忍更多失败，数据量上升，但总时间增加；V 变小 => 快速跳过，时间下降，数据量减少，形成近似 “X” 型趋势。

## 设计
- 数据集：`data/node100` 下首个 txt（可在脚本中替换）。
- V 取值（log 网格）：[0.1, 0.5, 1, 2, 5, 10, 50, 100]。
- 重复次数：每个 V 跑 5 个随机种子。
- 策略：仅 Lyapunov（复用 `Exp-Doc/My_Lya/simulation.py` 的 `LyapunovStrategyV4`）。

## 输出
- 原始结果：`Project10/result/project10_raw.csv`（V, seed, total_time, energy, collected_data_kb, skipped_nodes 等）。
- 聚合结果：`Project10/result/project10_agg.csv`（均值/方差）。
- 图：`Project10/result/project10_v_tradeoff.png`（双 Y 轴，左=总时间，右=数据量，x=log V）。

## 运行
```bash
python Project10/run_project10.py
```

## 图形风格
采用与 Project3/公共绘图工具一致的配色与 IEEE 友好样式：主轴实线，次轴虚线，含误差棒/图例/单位。***
