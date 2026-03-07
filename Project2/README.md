## Project2 — 有干扰、无优化（盲目重试）批量实验

定位  
- 基于 `gradysim` 的批量仿真，节点规模：50 / 100 / 150 / 200。  
- 引入通信干扰/失败率，但不做在线跳过或 Lyapunov 优化；作为“有干扰无优化”对照组。  
- 输出位于 `results/` 下的 `node50.csv`、`node100.csv`、`node150.csv`、`node200.csv`，一行对应一次路径/数据文件的实验结果。

关键脚本  
- `batch_run_node50.py` / `batch_run_node100.py` / `batch_run_node150.py` / `batch_run_node200.py`：批量跑各规模数据。  
- `main.py` + `protocol_mobile.py`：调度仿真、记录指标。  
- `summarize_results.py`：辅助汇总/整理结果。

拟绘制的图（后续步骤用当前 CSV）：  
- **总时间对比**：x=规模（node50~200），y=平均总任务时间。  
- **能耗对比**：x=规模，y=平均总能耗。  
- **数据收集量**：x=规模，y=平均收集数据量（KB/MB）。  
- **效率指标**：x=规模，y=`data/time`、`data/energy` 等效率。  
- **卡滞/重试现象**（若记录了重试/失败次数）：x=规模，y=平均重试次数或失败节点数，用柱状或箱线展示“盲目重试”的开销。

运行提醒  
1) 进入目录：`cd Project2/Project5_CollectData`  
2) 批量运行：`python batch_run_node50.py` 等  
3) 结果在 `results/`，随后按上面列的指标出图。  
