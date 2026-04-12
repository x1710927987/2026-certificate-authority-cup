# Question 2 Base Model

这个目录存放 2026 年认证杯 C 题第二问基础模型的主脚本与运行结果。

基础模型的目标是：
- 在固定基础参数下，比较 4 条扫描路径方案的热风险表现；
- 输出后续可视化和灵敏度分析所需的结构化数据；
- 给出时间、热历程、单元级风险、层级风险和方案级综合评价结果。

当前比较的 4 条路径方案为：
- `row_major`
- `serpentine`
- `center_out`
- `minimum_time`（来自问题一的最小时间路径）

基础材料固定为：
- `PA12`

材料热物性数据读取自：
- [激光粉末床相关五种材料热物性汇总表.md](D:\Users\24932\Desktop\C_data\question_2\激光粉末床相关五种材料热物性汇总表.md)

区间数据在代码中统一取中位数。

## 核心脚本

主脚本：
- [basic_model_for_question_2.py](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\basic_model_for_question_2.py)

它完成的主要工作包括：

1. 读取输入数据
- `part_geometry.csv`
- `local_geometry_relations.csv`
- `machine_params.json`
- `thermal_params.json`
- `baseline_paths.csv`
- `question_1_results.json`
- 材料热物性汇总表

2. 构造 4 条路径方案
- 3 条基准路径直接来自 `baseline_paths.csv`
- `minimum_time` 路径来自问题一结果文件

3. 用 `row_major` 做阈值标定
- 先按题面原始热贡献模型计算扫描时刻热风险
- 再按改进模型计算对应热状态
- 用分位数对齐法得到基础模型中的 `H_thres`

4. 对每条路径、每一层计算全过程热历程
- 重建每个扫描事件的完成时刻
- 计算所有单元在每个事件时刻的热状态
- 形成全过程热历程表

5. 计算单元级风险指标
- `mu`：热循环影响指数
- `xi`：成型不稳定性指数
- `theta`：局部高温指数
- `phi`：邻域热分布不均匀性指数

6. 计算层级、元件级和方案级汇总结果
- 层内时间
- 元件级汇总
- 整任务总时间
- 一级指标 `R_theta / R_mu / R_xi / R_phi`
- 综合风险排序

7. 输出适合后续分析的结构化文件

## 输出文件说明

### 1. 总结果文件

文件：
- [question_2_base_results.json](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\question_2_base_results.json)

作用：
- 保存基础模型的总体配置和最终汇总结果。

主要内容：
- 基础材料信息
- 参考材料尺度
- 热模型参数
- `H_thres` 标定结果
- 调度顺序
- 各方案总体结果
- 一级与二级权重摘要

适合用途：
- 作为第二问基础模型的总说明文件
- 用于论文中“参数设定”“模型结果总表”的复核

### 2. 方案级总汇总表

文件：
- [scheme_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\scheme_overall_summary.csv)

作用：
- 对 4 条路径方案给出整任务层面的最终比较结果。

主要字段：
- 总空走距离
- 总空走时间
- 总扫描时间
- 总激光开启时间
- 总任务时间
- `mu_mean / xi_mean / theta_mean / phi_mean`
- `R_theta / R_mu / R_xi / R_phi`
- `weighted_sum_total_risk`
- `topsis_score`
- 两种排序结果

适合用途：
- 论文中“4 种路径方案总体比较表”
- 方案比较柱状图
- 风险-时间二维比较图

### 3. 元件级汇总表

文件：
- [scheme_part_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\scheme_part_summary.csv)

作用：
- 分别对 `part_A` 和 `part_B` 汇总不同路径方案的风险与时间结果。

适合用途：
- 比较不同零件在相同路径方案下的敏感性
- 论文中“不同结构零件差异分析”

### 4. 层级汇总表

文件：
- [scheme_layer_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\scheme_layer_summary.csv)

作用：
- 给出每条方案在每一层上的时间和风险汇总。

主要字段：
- `travel_distance_mm`
- `travel_time_s`
- `scan_time_s`
- `laser_on_time_s`
- `layer_total_time_s`
- 各类单元级指标的均值、头部 10% 均值、极大值
- 一级风险指标
- 层级综合风险分数

适合用途：
- 层级柱状图
- 代表层筛选
- 研究哪些层最危险

### 5. 单元级风险明细表

文件：
- [cell_risk_details.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\cell_risk_details.csv)

作用：
- 保存每个单元在每条路径方案下的详细风险指标。

主要字段：
- 单元位置与类型
- `is_thin`
- `is_hole`
- `S_j`
- `mu`
- `xi`
- `theta`
- `phi`
- 扫描时热状态
- 峰值热状态
- 最终热状态

适合用途：
- 热风险空间分布图
- 结构脆弱区叠加图
- 单元级箱线图、小提琴图、热图

### 6. 全过程热历程表

文件：
- [heat_history_records.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\heat_history_records.csv)

作用：
- 保存“每个事件时刻、每个目标单元”的热状态，是问题二最重要的时序明细数据。

主要字段：
- 方案名
- 层号
- 事件步号
- 当前事件对应的扫描单元
- 事件时刻
- 目标单元编号
- `heat_state`
- 是否超过阈值

适合用途：
- 单元热历程曲线图
- 全层平均/峰值热状态演化图
- 超阈值单元数随时间变化图
- 热分布离散度随时间变化图

说明：
- 这个文件体积较大，但它是后续所有时间演化图的直接数据源。

### 7. 路径步骤表

文件：
- [scheme_path_steps.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\scheme_path_steps.csv)

作用：
- 保存 4 条路径方案在每层的访问顺序和时间信息。

主要字段：
- `visit_step`
- `cell_id`
- `travel_distance_mm`
- `travel_time_s`
- `scan_time_s`
- `laser_on_time_s`
- `scan_completion_time_s`

适合用途：
- 路径图
- 扫描顺序编号图
- 事件时间轴重建
- 将路径与热历程结果对齐

### 8. 阈值标定参考表

文件：
- [threshold_alignment_reference.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\threshold_alignment_reference.csv)

作用：
- 记录 `row_major` 参考路径下，原始模型热风险与改进模型热状态的对应关系。

主要字段：
- `original_scan_risk`
- `improved_scan_risk`
- `H_crit`
- `quantile_q`
- `H_thres`

适合用途：
- 论文中“分位数对齐法”解释
- 阈值标定复核

### 9. 权重汇总表

文件：
- [evaluation_weights_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\evaluation_weights_summary.csv)

作用：
- 保存综合评价中实际使用的权重。

内容包括：
- 一级主观权重
- 二级熵权法得到的客观权重

适合用途：
- 论文中“综合评价模型权重设置说明”
- 后续主观权重场景灵敏度分析的基准参考

### 10. 材料属性汇总表

文件：
- [material_properties_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\material_properties_summary.csv)

作用：
- 汇总 5 种材料的基础热物性中位值与原始区间信息。

适合用途：
- 检查材料读取是否正确
- 后续材料灵敏度分析的输入底表

### 11. Excel 工作簿

文件：
- [question_2_base_results.xlsx](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\question_2_base_results.xlsx)

说明：
- 只有安装 `openpyxl` 后才会自动生成。
- 它会把关键结果表放到不同 sheet 中，方便直接人工查看。

如果当前没有这个文件，说明本机未安装 `openpyxl`，但不影响 CSV / JSON 输出。

## 推荐的论文使用方式

建议你在论文中这样使用这些结果：

### 用于“模型建立”
- `question_2_base_results.json`
- `threshold_alignment_reference.csv`
- `evaluation_weights_summary.csv`

主要说明：
- 基础参数如何设定
- `H_thres` 如何标定
- 综合评价如何构造

### 用于“方案比较”
- `scheme_overall_summary.csv`
- `scheme_part_summary.csv`
- `scheme_layer_summary.csv`

主要说明：
- 4 种路径方案在总时间和热风险上的差异
- 不同零件、不同层的表现差异

### 用于“空间分布分析”
- `cell_risk_details.csv`

主要说明：
- 哪些区域风险最高
- 热风险是否集中在薄壁、孔边等敏感结构

### 用于“时间演化分析”
- `heat_history_records.csv`
- `scheme_path_steps.csv`

主要说明：
- 热状态如何随扫描推进而累积
- 哪些路径更容易造成反复受热和持续高温

## 运行说明

在项目根目录下运行：

```powershell
python D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\basic_model_for_question_2.py
```

## 依赖说明

基础运行不强制额外安装第三方库。

如果希望额外生成 Excel 工作簿，需要安装：

```powershell
pip install openpyxl
```

## 当前基础模型口径

- 基础材料：`PA12`
- 参考材料尺度：5 种材料总体中位参考值
- `A0 = 4`
- `A1 = 1`
- `gamma = 0.5`
- `L0 = 4 mm`
- `S_j^{type} = 1 + lambda_1 I_thin + lambda_2 I_hole`
- `lambda_1 = 0.35`
- `lambda_2 = 0.25`
- 参考路径固定为：`row_major`

这份 README 对应的是“第二问基础模型”这一阶段，不包含灵敏度分析和可视化脚本本身。
