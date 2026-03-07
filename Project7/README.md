# Project7：系统规模可扩展性（本项目版）

## 目的
考察用户/节点数量扩大时，本算法在人均性能与人均队列上的伸缩能力。

## 设置
- 自变量：系统规模 I ∈ {2, 5, 10, 15, 20, 25}（按场景可扩展）。  
- 因变量：人均性能（能耗/延迟 per user）与人均队列长度（bits per user）。
- 固定：V 取推荐值，单用户负载分布保持一致；带宽/信道/功率上限等共用同一组环境参数。

## 步骤
1) 固定随机种子与环境；逐个 I 运行到稳态。  
2) 记录人均性能与人均队列。  
3) 绘制 I vs 人均性能、人均队列曲线，关注增长斜率与饱和点。

## 输出
- 数据表：I, 人均性能, 人均队列。  
- 图：I vs 性能/队列。

## 判据
人均指标随规模仅缓慢上升或保持平稳，无显著恶化，表明可扩展性良好。 

----------------------------------------
补充实验方案（中文友好版）

1) 规模列表：I ∈ {2, 5, 10, 15, 20, 25}；固定 V=推荐值、单用户负载分布一致，其余环境不变；每个 I 跑 ≥5 随机种子。
2) 指标：人均性能（能耗/延迟 per user）、人均队列（bits per user）。可选记录标准差/置信区间。
3) 运行流程：
   - 对每个 I 执行 run_once(num_users=I, seed) -> (avg_cost_per_user, avg_queue_per_user)；
   - 写入 CSV：I,seed,avg_cost_per_user,avg_queue_per_user；
   - 聚合 project7_agg.csv：按 I 统计均值/方差；
   - 绘制 I vs 人均性能、I vs 人均队列折线，输出 project7_scalability.png，关注斜率。
4) 输出规划（建议目录）：
   - 原始：Project7/result/project7_raw.csv
   - 聚合：Project7/result/project7_agg.csv
   - 图：Project7/result/project7_scalability.png
5) 绘图风格：统一配色（性能实线、队列虚线），标注可能的饱和点/折点，保持网格和图例清晰。
