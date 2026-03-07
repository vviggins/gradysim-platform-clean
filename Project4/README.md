## Project4 — Lyapunov 参数敏感性实验

目标：在保持场景和干扰条件不变的情况下，扫参数 `LYA_V`（跳过/重试的权衡力度），观察效率随参数的变化，找出最佳区间。

包含内容：
- `run_lya_param_sweep.py`：基于 node100 数据运行基线（盲目重试）与多组 `LYA_V`（0.5/1/2/3/4）方案，输出到 `results/param_sweep_summary.csv` 与 `param_sweep_trajectory.csv`。
- `plot_param_sweep.py`：将扫参结果可视化，生成 `plots_param/eff_vs_v.png`（效率随参数变化）和 `plots_param/time_data_vs_v.png`（时间与数据量权衡）。

运行方式（在本目录）：
```bash
python run_lya_param_sweep.py
python plot_param_sweep.py
```

指标解释：
- `Eff_Data_Per_Time`: 数据收集效率（KB/s），作为纵轴核心指标。
- `Total_Time`: 总任务时间；`Data_Collected_KB`: 收集的数据量。
- `LYA_V`: Lyapunov 权重，越大越倾向“快跳过、少纠缠”；过大可能导致遗漏收益，过小则过度重试。
