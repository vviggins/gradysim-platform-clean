# Project3: Baseline vs Lyapunov (轻量仿真 / Lightweight Simulation)

## 实验设定 (Setup)
- 场景规模：node50 / node100 / node150 / node200（路径为文件顺序的闭合巡回）。
- 通信/能耗：握手 10s，悬停功率 1.2，飞行成本 0.1/米，速率 500 KB/s，电池 3000（抽象单位）。
- 数据量：整体缩小 10 倍（常规约 15 KB，高价值 ≥250 KB），30% 低质量节点承载大量高价值数据。
- Baseline：盲目重试（最多 20 次），成功率乘 0.6，无先验。
- Lyapunov：有限重试（最多 5 次），至少 2 次后基于在线尝试/队列势决定跳过，无先验失败率。

## 主要发现 (Key Findings)
- **小/中规模（node50/100）：** Lyapunov 显著缩短任务时间并提升时间/能效；Baseline 可能收集略多数据，但在低质量节点浪费时间/能量，Lyapunov 通过机会性跳过减少长尾延迟。
- **大规模（node150/200）：** Baseline 更易出现“通信锁死”（Total_Time 高、效率低）；Lyapunov 保持较短完成时间和更高 KB/s、KB/能耗，代价是跳过部分节点，体现高密度/高干扰下的鲁棒性。
- **轨迹（node100）：** Lyapunov 更快累积数据（曲线更陡），Baseline 依赖后期反复重试；证明在未知失败率下，Lyapunov 提升时间效率且降低长尾风险。

## 输出 (Outputs)
- 结果：`results/lya_summary.csv`，`results/lya_trajectory.csv`（覆盖全部规模与两种策略）。
- 图表（论文风格）：`plots_final/total_time.png`，`data_collected.png`，`eff_time.png`，`eff_energy.png`，`skipped_nodes.png`，`trajectory_node100.png`。
  - 配色：Baseline #FC9E79，Lyapunov #7DCBB2；黑色边框、数值标注、浅色网格。

## 总结 (Takeaway)
Lyapunov 基于在线尝试与队列势的跳过策略，在高干扰/高密度场景有效缓解通信锁死，降低长尾任务时间，并保持有竞争力的收集效率；Baseline 盲目重试在理想节点可收集更多，但在干扰下付出过高时间/能耗代价。

---

## Experiment Setup (English)
- Scales: node50/100/150/200 (closed tour by file order).
- Comm/energy: handshake 10s, hover 1.2 power, flight 0.1 per meter, rate 500 KB/s, battery 3000.
- Payloads: 10x smaller (regular ~15 KB, high-value ≥250 KB), 30% low-quality nodes carry many high-value packets.
- Baseline: blind retries (max 20), success prob *0.6, no prior.
- Lyapunov: bounded retries (max 5), after 2 attempts uses online evidence + backlog to skip, no prior failure rates.

## Key Findings
- **Small/medium (node50/100):** Lyapunov cuts mission time and boosts time/energy efficiency; baseline may gather slightly more data but wastes time/energy on low-quality nodes. Lyapunov reduces tail latency via opportunistic skip.
- **Large (node150/200):** Baseline suffers “communication lock-in” (higher Total_Time, lower efficiency). Lyapunov keeps shorter completion and better KB/s, KB/energy, at the cost of some skips—showing robustness under dense/interference scenarios.
- **Trajectory (node100):** Lyapunov accumulates earlier (steeper curve); baseline catches up later via retries. Demonstrates improved temporal efficiency without prior node failure knowledge.

## Outputs
- Results: `results/lya_summary.csv`, `results/lya_trajectory.csv`.
- Plots: `plots_final/total_time.png`, `data_collected.png`, `eff_time.png`, `eff_energy.png`, `skipped_nodes.png`, `trajectory_node100.png`. Palette baseline #FC9E79, Lyapunov #7DCBB2; black edges, value labels, light grids.

## Takeaway
Lyapunov’s online skip (empirical success + backlog) mitigates lock-in and trims long-tail mission time in dense/low-quality regimes, while keeping competitive data yield on smaller scales; baseline’s blind retries can recover more packets in ideal cases but pay disproportionate time/energy under interference.
