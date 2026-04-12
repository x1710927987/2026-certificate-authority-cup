# Question 1 README

本目录用于完成认证杯数学建模大赛 C 题第一问的建模、结果敏感性分析、解结构敏感性分析，以及论文所需可视化。

第一问的核心任务是：

- 对每一个打印层，优化扫描单元的访问顺序；
- 在“逐层交替打印 `part_A` 与 `part_B`”的调度规则下，统计整任务总时间；
- 分析结果对设备参数和边界约束变化的敏感性；
- 输出可直接用于论文插图和结果表格的数据。

---

## 1. 目录结构总览

```text
question_1/
├─ basic_model_result_for_question_1/
│  ├─ basic_model_for_question_1.py
│  ├─ question_1_results.json
│  ├─ question_1_layer_summary.csv
│  └─ question_1_path_steps.csv
├─ sensitivity_analysis/
│  ├─ idle_running_speed/
│  ├─ laser_on/
│  ├─ intra-part_distance/
│  ├─ fixed_starting_point/
│  ├─ fixed_endpoint/
│  └─ return_to_warehouse/
├─ visualization/
│  ├─ visualization_common.py
│  ├─ base_geometry_optimal_path.py
│  ├─ baseline_scheme_comparison.py
│  ├─ time_breakdown_visualization.py
│  ├─ structural_sensitivity_path_comparison.py
│  └─ visualization_sources_and_outputs.md
└─ README.md
```

---

## 2. 关键算法说明

### 2.1 基础模型：`basic_model_result_for_question_1/basic_model_for_question_1.py`

这是第一问最核心的求解脚本。

#### 算法思想

1. 以单层为单位抽取全部扫描单元。
2. 读取 `local_geometry_relations.csv` 中给出的有向空走距离 `travel_distance_mm`。
3. 将“开放式最短访问路径问题”转化为“带虚拟节点的闭环问题”：
   - 引入虚拟节点 `0`；
   - 虚拟节点到任意真实节点、任意真实节点到虚拟节点的代价记为 0；
   - 用 OR-Tools 的 `AddCircuit` 精确求解；
   - 删除虚拟节点后恢复真实开放路径。
4. 对每层计算：
   - 空走距离与空走时间；
   - 扫描时间；
   - 激光开启等待时间；
   - 层内总时间。
5. 按 “A1, B1, A2, B2, ..., A6, B6” 的规则组织打印顺序。
6. 整任务时间由三部分组成：
   - 全部层的层内时间之和；
   - 层间切换时间之和；
   - 零件间转移时间之和。

#### 该脚本在论文中的作用

- 用于“问题一模型建立”部分；
- 用于说明开放路径优化模型的求解方式；
- 用于提供后续所有敏感性分析与可视化的基准结果。

---

### 2.2 结果敏感性分析脚本

这一类脚本**不重新优化路径结构**，而是在基础模型结果上分析时间结果对参数变化的响应。

#### `sensitivity_analysis/idle_running_speed/idle_running_speed.py`

分析对象：空走速度 \(v_{travel}\)

- 参数集合：`1200, 1500, 1800, 2100, 2400 mm/s`
- 思路：保持最优路径不变，仅重算空走时间和总任务时间

论文用途：

- 放在“结果敏感性分析”中；
- 说明设备空走能力变化时，路径优化结果的时间收益是否稳定。

#### `sensitivity_analysis/laser_on/laser_on.py`

分析对象：激光开启延迟 \(t_{on}\)

- 参数集合：`0.005, 0.01, 0.015, 0.02, 0.03 s`
- 思路：保持路径不变，重算各层等待时间和总任务时间

论文用途：

- 放在“结果敏感性分析”中；
- 说明固定启动开销增大后，路径优化的相对收益是否被削弱。

#### `sensitivity_analysis/intra-part_distance/intra-part_distance.py`

分析对象：零件间转移距离

- 参数集合：`20, 25, 30, ..., 100 mm`
- 思路：保持层内路径不变，仅重新计算零件间转移时间

论文用途：

- 放在“结果敏感性分析”中；
- 说明整任务总时间对零件间转移距离设定是否敏感。

---

### 2.3 解结构敏感性分析脚本

这一类脚本会**重新求解路径**，因为边界条件变化会直接改变最优路径结构。

#### `sensitivity_analysis/fixed_starting_point/fixed_starting_point.py`

分析对象：固定起点规则

- 对每一层，让每个 `cell` 轮流作为固定起点；
- 每次都重新求解最优开放路径；
- 与基础模型比较时间增量和路径差异率。

论文用途：

- 放在“解结构敏感性分析”中；
- 说明起点受限时，最优路径结构是否发生显著变化。

#### `sensitivity_analysis/fixed_endpoint/fixed_endpoint.py`

分析对象：固定终点规则

- 对每一层，让每个 `cell` 轮流作为固定终点；
- 每次都重新求解最优开放路径；
- 与基础模型比较时间增量和路径差异率。

论文用途：

- 放在“解结构敏感性分析”中；
- 说明终点受限时，最优路径尾部结构如何变化。

#### `sensitivity_analysis/return_to_warehouse/return_to_warehouse.py`

分析对象：回仓规则

- 仓位固定为 `(0, 0) mm`；
- 每层末单元扫描结束后必须回仓；
- 将回仓距离作为末端附加代价加入目标函数并重新求解。

论文用途：

- 放在“解结构敏感性分析”中；
- 说明当工艺要求层末回仓时，模型结论是否仍然稳定。

---

### 2.4 可视化脚本

#### `visualization/visualization_common.py`

公共工具模块，负责：

- 读取基础模型结果、几何数据、基准路径和敏感性分析结果；
- 提供路径指标计算；
- 提供带固定起点、固定终点、回仓规则的统一求解接口。

它本身不是论文插图脚本，而是其他可视化脚本的公共依赖。

#### `visualization/base_geometry_optimal_path.py`

生成三张基础模型图：

- 单层几何离散图；
- 最优路径图；
- 访问序号图。

论文用途：

- 放在“问题描述”与“基础模型结果展示”部分；
- 用于说明几何输入是什么，模型输出路径长什么样。

#### `visualization/baseline_scheme_comparison.py`

生成基准方案与最优方案的对比图与指标表：

- `row_major`
- `serpentine`
- `center_out`
- `optimal`

论文用途：

- 放在“方案比较”部分；
- 用于证明本文求得的最优方案确实优于题目给定的基准策略。

#### `visualization/time_breakdown_visualization.py`

生成时间构成相关图片：

- 每层时间分解堆叠图；
- 整任务时间分解图。

论文用途：

- 放在“结果分析”部分；
- 用于说明总时间由哪些部分组成，以及优化主要作用在哪个时间分量上。

#### `visualization/structural_sensitivity_path_comparison.py`

针对解结构敏感性分析，绘制“基础路径 vs 变化规则路径”的对比图：

- 固定起点；
- 固定终点；
- 回仓规则。

论文用途：

- 放在“解结构敏感性分析”部分；
- 用于直观展示约束变化是否会显著改变最优路径形状。

---

## 3. 结果文件说明

### 3.1 基础模型结果文件

#### `basic_model_result_for_question_1/question_1_results.json`

这是第一问最完整的基础结果文件，记录：

- 设备参数；
- 打印调度顺序；
- 每层最优路径；
- 每层起点、终点；
- 每层空走、扫描、等待时间；
- 整任务时间分解；
- 零件间转移距离与转移时间。

论文用途：

- 作为第一问所有表格和统计量的总数据源；
- 可用于撰写“模型结果汇总”“总任务时间计算”“附录数据说明”。

#### `basic_model_result_for_question_1/question_1_layer_summary.csv`

按层汇总的结果表，字段更精炼，适合直接画图：

- 每层单元数；
- 每层空走距离；
- 每层空走时间；
- 每层扫描时间；
- 每层等待时间；
- 每层总时间。

论文用途：

- 用于绘制堆叠柱状图；
- 用于制作按层比较的表格。

#### `basic_model_result_for_question_1/question_1_path_steps.csv`

按访问步序记录每层路径：

- 第几层；
- 第几步；
- 访问到哪个 `cell_id`。

论文用途：

- 用于路径图、访问序号图、路径重建图；
- 用于附录中给出完整路径结果。

---

### 3.2 结果敏感性分析输出文件

#### `idle_running_speed/idle_running_speed_summary.csv`

记录不同空走速度下：

- 总任务时间；
- 旅行相关时间；
- 参数变化下的时间结果。

论文用途：

- 制作“空走速度敏感性折线图”；
- 支撑“设备空走能力变化下结果是否稳定”的论述。

#### `idle_running_speed/idle_running_speed_layer_details.csv`

更细的逐层结果表。

论文用途：

- 用于附录；
- 如需分析哪一层对空走速度更敏感，可直接使用。

#### `laser_on/laser_on_summary.csv`

记录不同激光开启延迟下的总任务时间与层内时间结果。

论文用途：

- 制作“激光开启延迟敏感性折线图”；
- 支撑“固定启动成本变化对优化收益的影响”的论述。

#### `laser_on/laser_on_layer_details.csv`

逐层明细表。

论文用途：

- 适合放附录或做局部层分析。

#### `intra-part_distance/intra_part_distance_summary.csv`

记录不同零件间转移距离取值下的总任务时间结果。

论文用途：

- 制作“零件间转移距离参数扫描图”；
- 支撑“整任务时间对零件间距离设定的敏感性分析”。

---

### 3.3 解结构敏感性分析输出文件

#### `fixed_starting_point/fixed_starting_point_details.csv`

逐层、逐候选起点的明细表，记录：

- 固定起点是哪一个单元；
- 新的总时间；
- 与基础模型相比的时间增量；
- 路径差异率。

论文用途：

- 可支撑“固定起点规则对路径结构影响”的细粒度分析；
- 适合附录表格。

#### `fixed_starting_point/fixed_starting_point_summary.csv`

按层汇总固定起点敏感性结果，记录：

- 最优固定起点；
- 最差固定起点；
- 平均时间增量；
- 平均路径差异率。

论文用途：

- 用于正文中的汇总表与箱线图、折线图说明。

#### `fixed_endpoint/fixed_endpoint_details.csv`

逐层、逐候选终点的明细表。

论文用途：

- 用于分析固定终点约束如何影响尾部路径结构；
- 适合附录。

#### `fixed_endpoint/fixed_endpoint_summary.csv`

固定终点敏感性的按层汇总表。

论文用途：

- 用于正文中的结构敏感性结果展示。

#### `return_to_warehouse/return_to_warehouse_summary.csv`

记录每层在回仓规则下的：

- 回仓距离；
- 回仓时间；
- 新总时间；
- 时间增量；
- 路径差异率。

论文用途：

- 直接用于“回仓规则敏感性”分析；
- 可支持回仓代价与路径变化的结论。

#### `return_to_warehouse/return_to_warehouse_path_steps.csv`

记录回仓规则下重新求得的每层路径。

论文用途：

- 用于绘制“基础路径 vs 回仓路径”图；
- 可放附录。

---

## 4. 图片文件说明与论文用途

### 4.1 基础模型图

#### `visualization/base_geometry_optimal_path/representative_layer_geometry.png`

作用：

- 展示代表层的扫描单元空间分布；
- 区分不同单元类型。

适合放在论文：

- “问题描述”或“模型输入说明”部分。

说明重点：

- 模型的几何输入是什么；
- 单层路径优化是建立在哪种离散单元结构上的。

#### `visualization/base_geometry_optimal_path/representative_layer_optimal_path.png`

作用：

- 展示代表层的最优访问路径；
- 标出起点和终点。

适合放在论文：

- “基础模型求解结果”部分。

说明重点：

- 最优路径是否连续、紧凑；
- 起点和终点如何自然形成。

#### `visualization/base_geometry_optimal_path/representative_layer_visit_order.png`

作用：

- 展示每个单元的访问顺序。

适合放在论文：

- “路径结构说明”部分；
- 或附录中详细展示一个代表层。

说明重点：

- 最优路径不是随机结果，而是有明显访问逻辑的。

---

### 4.2 方案比较图

#### `visualization/baseline_scheme_comparison/baseline_vs_optimal_path_part_A.png`
#### `visualization/baseline_scheme_comparison/baseline_vs_optimal_path_part_B.png`

作用：

- 将三种基准方案与最优方案并排比较。

适合放在论文：

- “方案比较”部分。

说明重点：

- 最优方案是否减少了长跳跃；
- 相比基准方案是否更连贯。

#### `visualization/baseline_scheme_comparison/baseline_vs_optimal_metrics.png`

作用：

- 比较不同方案的总空走距离和层内总时间。

适合放在论文：

- “基准方案比较结果”部分。

说明重点：

- 最优方案在目标函数值上到底优了多少；
- 与基准方案相比改进是否显著。

#### `visualization/baseline_scheme_comparison/baseline_vs_optimal_metrics.csv`

作用：

- 记录上图对应的数值。

适合放在论文：

- 作为图的配套表格；
- 或放入附录。

---

### 4.3 时间分解图

#### `visualization/time_breakdown_visualization/layer_time_breakdown_stacked.png`

作用：

- 展示每层时间由扫描、等待、空走三部分组成。

适合放在论文：

- “结果分析”部分。

说明重点：

- 每层时间结构是什么；
- 第一问优化主要作用于空走时间这一部分。

#### `visualization/time_breakdown_visualization/total_task_time_decomposition.png`

作用：

- 展示整任务总时间由层内、层间、零件间三部分组成。

适合放在论文：

- “总时间模型与结果汇总”部分。

说明重点：

- 第一问虽然重点是单层优化，但整任务时间统计是完整保留的。

---

### 4.4 解结构敏感性路径图

#### `visualization/structural_sensitivity_path_comparison/fixed_starting_point_path_comparison.png`

作用：

- 比较基础模型路径与“固定起点规则”下的路径。

适合放在论文：

- “解结构敏感性分析”部分。

说明重点：

- 起点受限时，路径前段如何变化；
- 整体路径是否仍然稳定。

#### `visualization/structural_sensitivity_path_comparison/fixed_endpoint_path_comparison.png`

作用：

- 比较基础模型路径与“固定终点规则”下的路径。

适合放在论文：

- “解结构敏感性分析”部分。

说明重点：

- 终点受限时，路径尾部结构是否明显改变。

#### `visualization/structural_sensitivity_path_comparison/return_to_warehouse_path_comparison.png`

作用：

- 比较基础模型路径与“回仓规则”下的路径。

适合放在论文：

- “解结构敏感性分析”部分。

说明重点：

- 当层末必须回仓时，最优终点是否向仓位靠拢；
- 模型路径结构是否发生整体重排。

---

## 5. 推荐的论文使用顺序

如果按论文写作逻辑组织，建议引用顺序如下：

1. 先用 `representative_layer_geometry.png` 说明几何输入；
2. 再用 `representative_layer_optimal_path.png` 和 `representative_layer_visit_order.png` 展示基础模型结果；
3. 接着用 `baseline_vs_optimal_path_part_A.png`、`baseline_vs_optimal_path_part_B.png` 和 `baseline_vs_optimal_metrics.png` 比较基准方案与最优方案；
4. 然后用 `layer_time_breakdown_stacked.png` 与 `total_task_time_decomposition.png` 解释总时间的组成；
5. 最后用结果敏感性分析图和解结构敏感性路径图说明模型稳健性。

---

## 6. 依赖说明

本目录中主要脚本依赖以下开源库：

```bash
pip install ortools matplotlib
```

如果只运行基础模型求解与结构敏感性分析，需要 `ortools`。  
如果要绘图，还需要 `matplotlib`。

---

## 7. 附加说明

`visualization/visualization_sources_and_outputs.md` 中还列出了新增可视化的“数据源-图片输出”对照表，适合在维护图表时快速查阅。
