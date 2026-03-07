## Project1 — 无干扰基线（固定失败率）批量实验

定位  
- 基于 `gradysim` 的离线批量仿真，节点规模：50 / 100 / 150 / 200。  
- 参考 Project2/3/4，不涉及在线优化；使用固定的通信失败率（`main.py` 中已设置，作为统一“无干扰”对照）。  
- 输出位于 `results/` 下的 `node50.csv`、`node100.csv`、`node150.csv`、`node200.csv`，每行对应一次路径/数据文件的实验结果。

关键脚本  
- `batch_run_node50.py` / `batch_run_node100.py` / `batch_run_node150.py` / `batch_run_node200.py`：批量跑各规模数据。  
- `main.py` + `protocol_mobile.py`：调度仿真、记录指标。  
- `summarize_results.py`：辅助汇总/整理结果。

拟绘制的图（后续步骤用当前 CSV）：  
- **总时间对比**：x=规模（node50~200），y=平均总任务时间。  
- **能耗对比**：x=规模，y=平均总能耗。  
- **数据收集量**：x=规模，y=平均收集数据量（KB/MB）。  
- **效率指标**：x=规模，y=`data/time`、`data/energy` 等效率。  
- 如需单条轨迹展示，可选取 node100 的一条 `trajectory`（若已记录）绘制时间-累积数据曲线。

运行提醒  
1) 进入目录：`cd Project1/Project5_CollectData`  
2) 批量运行：`python batch_run_node50.py` 等  
3) 结果在 `results/`，随后可按上面列的指标出图。  
