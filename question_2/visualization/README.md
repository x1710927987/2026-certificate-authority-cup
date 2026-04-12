# Question 2 Visualization

本目录用于存放问题二的可视化脚本、生成图片以及对应的元数据文件。  
整套可视化严格对应 [第二问思路.md](D:\Users\24932\Desktop\C_data\question_2\第二问思路.md) 中“六. 可视化方案”的图号与功能设计。

当前目录已经分为 6 类：

- [common](D:\Users\24932\Desktop\C_data\question_2\visualization\common)
- [mechanism](D:\Users\24932\Desktop\C_data\question_2\visualization\mechanism)
- [spatial](D:\Users\24932\Desktop\C_data\question_2\visualization\spatial)
- [temporal](D:\Users\24932\Desktop\C_data\question_2\visualization\temporal)
- [comparison](D:\Users\24932\Desktop\C_data\question_2\visualization\comparison)
- [sensitivity](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity)

另外提供两个批量运行入口：

- [run_core_visualizations.py](D:\Users\24932\Desktop\C_data\question_2\visualization\run_core_visualizations.py)
  生成正文优先的核心图。
- [run_appendix_visualizations.py](D:\Users\24932\Desktop\C_data\question_2\visualization\run_appendix_visualizations.py)
  生成附录型图。

---

## 1. 数据来源总览

本目录下所有图主要读取以下结果文件：

### 问题二基础模型结果
- [question_2_base_results.json](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\question_2_base_results.json)
- [scheme_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\scheme_overall_summary.csv)
- [scheme_layer_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\scheme_layer_summary.csv)
- [cell_risk_details.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\cell_risk_details.csv)
- [heat_history_records.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\heat_history_records.csv)
- [scheme_path_steps.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\scheme_path_steps.csv)
- [threshold_alignment_reference.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\threshold_alignment_reference.csv)

### 灵敏度分析结果
- [a_0_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\A_0\a_0_overall_summary.csv)
- [alpha_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\alpha\alpha_overall_summary.csv)
- [beta_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\beta\beta_overall_summary.csv)
- [gamma_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\gamma\gamma_overall_summary.csv)
- [materials_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials_overall_summary.csv)
- [subjective_weights_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights_overall_summary.csv)
- [subjective_weights_scenario_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights_scenario_summary.csv)

### 原始几何数据
- [part_geometry.csv](D:\Users\24932\Desktop\C_data\part_geometry.csv)

---

## 2. 公共工具

### [q2_visualization_common.py](D:\Users\24932\Desktop\C_data\question_2\visualization\common\q2_visualization_common.py)
作用：

- 统一读取问题二基础模型和灵敏度分析结果
- 提供代表层自动选择逻辑
- 提供空间热图绘制工具
- 提供路径叠加绘制工具
- 提供热历程序列聚合工具
- 统一保存图片元数据到 `.json`

这份文件不单独对应论文插图，但它是所有可视化脚本的基础支撑层。

---

## 3. 正文优先核心图

这些图是 [第二问思路.md](D:\Users\24932\Desktop\C_data\question_2\第二问思路.md) 里建议优先放在正文的核心图片。

### 图2-1 热历程累积机制示意图
- 脚本：
  [fig2_1_heat_accumulation_mechanism.py](D:\Users\24932\Desktop\C_data\question_2\visualization\mechanism\fig2_1_heat_accumulation_mechanism.py)
- 图片：
  [fig2_1_heat_accumulation_mechanism.png](D:\Users\24932\Desktop\C_data\question_2\visualization\mechanism\fig2_1_heat_accumulation_mechanism.png)
- 元数据：
  [fig2_1_heat_accumulation_mechanism.json](D:\Users\24932\Desktop\C_data\question_2\visualization\mechanism\fig2_1_heat_accumulation_mechanism.json)
- 数据来源：
  不依赖结果表，属于模型机制示意图
- 适合放在：
  正文“问题二模型建立”开头
- 主要说明：
  单元热状态由“自热项 + 历史邻域热输入衰减叠加”共同决定

### 图2-2 分位数对齐法示意图
- 脚本：
  [fig2_2_threshold_alignment.py](D:\Users\24932\Desktop\C_data\question_2\visualization\mechanism\fig2_2_threshold_alignment.py)
- 图片：
  [fig2_2_threshold_alignment.png](D:\Users\24932\Desktop\C_data\question_2\visualization\mechanism\fig2_2_threshold_alignment.png)
- 元数据：
  [fig2_2_threshold_alignment.json](D:\Users\24932\Desktop\C_data\question_2\visualization\mechanism\fig2_2_threshold_alignment.json)
- 数据来源：
  [threshold_alignment_reference.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\threshold_alignment_reference.csv)
- 适合放在：
  正文“过热阈值标定”部分
- 主要说明：
  改进模型中的 `H_thres` 不是主观设定，而是通过 `row_major` 的分位数对齐得到

### 图2-3 代表层最终热积累分布图
- 脚本：
  [fig2_3_final_heat_map.py](D:\Users\24932\Desktop\C_data\question_2\visualization\spatial\fig2_3_final_heat_map.py)
- 图片：
  [fig2_3_final_heat_map.png](D:\Users\24932\Desktop\C_data\question_2\visualization\spatial\fig2_3_final_heat_map.png)
- 元数据：
  [fig2_3_final_heat_map.json](D:\Users\24932\Desktop\C_data\question_2\visualization\spatial\fig2_3_final_heat_map.json)
- 数据来源：
  [part_geometry.csv](D:\Users\24932\Desktop\C_data\part_geometry.csv)
  [cell_risk_details.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\cell_risk_details.csv)
  [scheme_layer_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\scheme_layer_summary.csv)
- 适合放在：
  正文“空间热分布分析”部分
- 主要说明：
  不同路径方案在同一代表层上的最终热积累热点分布差异

### 图2-5 邻域热分布不均匀性指数分布图
- 脚本：
  [fig2_5_phi_map.py](D:\Users\24932\Desktop\C_data\question_2\visualization\spatial\fig2_5_phi_map.py)
- 图片：
  [fig2_5_phi_map.png](D:\Users\24932\Desktop\C_data\question_2\visualization\spatial\fig2_5_phi_map.png)
- 元数据：
  [fig2_5_phi_map.json](D:\Users\24932\Desktop\C_data\question_2\visualization\spatial\fig2_5_phi_map.json)
- 数据来源：
  [part_geometry.csv](D:\Users\24932\Desktop\C_data\part_geometry.csv)
  [cell_risk_details.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\cell_risk_details.csv)
  [scheme_layer_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\scheme_layer_summary.csv)
- 适合放在：
  正文“温度分布不均匀性分析”部分
- 主要说明：
  哪些单元的邻域热分布最不均匀，也就是最容易出现局部热梯度

### 图2-8 全层平均热状态与峰值热状态演化图
- 脚本：
  [fig2_8_heat_evolution.py](D:\Users\24932\Desktop\C_data\question_2\visualization\temporal\fig2_8_heat_evolution.py)
- 图片：
  [fig2_8_heat_evolution.png](D:\Users\24932\Desktop\C_data\question_2\visualization\temporal\fig2_8_heat_evolution.png)
- 元数据：
  [fig2_8_heat_evolution.json](D:\Users\24932\Desktop\C_data\question_2\visualization\temporal\fig2_8_heat_evolution.json)
- 数据来源：
  [heat_history_records.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\heat_history_records.csv)
  [scheme_layer_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\scheme_layer_summary.csv)
- 适合放在：
  正文“热历程演化分析”部分
- 主要说明：
  热积累不是静态结果，而是在整个扫描过程中不断演化；不同路径的演化轨迹明显不同

### 图2-12 全任务热风险指标对比柱状图
- 脚本：
  [fig2_12_global_risk_comparison.py](D:\Users\24932\Desktop\C_data\question_2\visualization\comparison\fig2_12_global_risk_comparison.py)
- 图片：
  [fig2_12_global_risk_comparison.png](D:\Users\24932\Desktop\C_data\question_2\visualization\comparison\fig2_12_global_risk_comparison.png)
- 元数据：
  [fig2_12_global_risk_comparison.json](D:\Users\24932\Desktop\C_data\question_2\visualization\comparison\fig2_12_global_risk_comparison.json)
- 数据来源：
  [scheme_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\scheme_overall_summary.csv)
- 适合放在：
  正文“全局结果比较”部分
- 主要说明：
  四种路径在全任务尺度上的 `R_theta / R_mu / R_xi / R_phi` 差异

### 图2-14 风险-时间 Pareto 散点图
- 脚本：
  [fig2_14_pareto_time_risk.py](D:\Users\24932\Desktop\C_data\question_2\visualization\comparison\fig2_14_pareto_time_risk.py)
- 图片：
  [fig2_14_pareto_time_risk.png](D:\Users\24932\Desktop\C_data\question_2\visualization\comparison\fig2_14_pareto_time_risk.png)
- 元数据：
  [fig2_14_pareto_time_risk.json](D:\Users\24932\Desktop\C_data\question_2\visualization\comparison\fig2_14_pareto_time_risk.json)
- 数据来源：
  [scheme_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\scheme_overall_summary.csv)
- 适合放在：
  正文“效率-质量权衡”部分
- 主要说明：
  时间成本与综合热风险之间的 Pareto 关系

### 图2-21 权重场景-方案排序热图
- 脚本：
  [fig2_21_weight_rank_heatmap.py](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_21_weight_rank_heatmap.py)
- 图片：
  [fig2_21_weight_rank_heatmap.png](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_21_weight_rank_heatmap.png)
- 元数据：
  [fig2_21_weight_rank_heatmap.json](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_21_weight_rank_heatmap.json)
- 数据来源：
  [subjective_weights_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights_overall_summary.csv)
  [subjective_weights_scenario_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights_scenario_summary.csv)
- 适合放在：
  正文“一级主观权重灵敏度分析”部分
- 主要说明：
  最终方案排序是否依赖主观风险偏好

---

## 4. 附录型图

这些图更适合放在附录，或者在正文中作为补充引用。

### 图2-4 代表层高温超阈值分布图
- 脚本：
  [fig2_4_threshold_exceedance_map.py](D:\Users\24932\Desktop\C_data\question_2\visualization\spatial\fig2_4_threshold_exceedance_map.py)
- 图片：
  [fig2_4_threshold_exceedance_map.png](D:\Users\24932\Desktop\C_data\question_2\visualization\spatial\fig2_4_threshold_exceedance_map.png)
- 数据来源：
  [cell_risk_details.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\cell_risk_details.csv)
  [question_2_base_results.json](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\question_2_base_results.json)
- 用于说明：
  哪些单元在最终时刻越过了 `H_thres`

### 图2-6 结构脆弱区与高风险区叠加图
- 脚本：
  [fig2_6_structural_sensitive_overlay.py](D:\Users\24932\Desktop\C_data\question_2\visualization\spatial\fig2_6_structural_sensitive_overlay.py)
- 图片：
  [fig2_6_structural_sensitive_overlay.png](D:\Users\24932\Desktop\C_data\question_2\visualization\spatial\fig2_6_structural_sensitive_overlay.png)
- 数据来源：
  [cell_risk_details.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\cell_risk_details.csv)
  [part_geometry.csv](D:\Users\24932\Desktop\C_data\part_geometry.csv)
- 用于说明：
  高风险区是否集中出现在孔边或薄壁敏感区域

### 图2-7 代表单元热历程曲线图
- 脚本：
  [fig2_7_representative_cell_histories.py](D:\Users\24932\Desktop\C_data\question_2\visualization\temporal\fig2_7_representative_cell_histories.py)
- 图片：
  [fig2_7_representative_cell_histories.png](D:\Users\24932\Desktop\C_data\question_2\visualization\temporal\fig2_7_representative_cell_histories.png)
- 数据来源：
  [heat_history_records.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\heat_history_records.csv)
  [cell_risk_details.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\cell_risk_details.csv)
- 用于说明：
  热点单元、孔边单元、普通单元的热历程差异

### 图2-9 超阈值单元数随时间变化图
- 脚本：
  [fig2_9_exceedance_count_evolution.py](D:\Users\24932\Desktop\C_data\question_2\visualization\temporal\fig2_9_exceedance_count_evolution.py)
- 图片：
  [fig2_9_exceedance_count_evolution.png](D:\Users\24932\Desktop\C_data\question_2\visualization\temporal\fig2_9_exceedance_count_evolution.png)
- 数据来源：
  [heat_history_records.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\heat_history_records.csv)
- 用于说明：
  风险区是逐步累积出现，还是在某些阶段迅速扩张

### 图2-10 热分布离散程度随时间变化图
- 脚本：
  [fig2_10_dispersion_evolution.py](D:\Users\24932\Desktop\C_data\question_2\visualization\temporal\fig2_10_dispersion_evolution.py)
- 图片：
  [fig2_10_dispersion_evolution.png](D:\Users\24932\Desktop\C_data\question_2\visualization\temporal\fig2_10_dispersion_evolution.png)
- 数据来源：
  [heat_history_records.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\heat_history_records.csv)
- 用于说明：
  温度分布不均匀性是否随着路径执行逐渐放大

### 图2-11 代表层热风险指标对比柱状图
- 脚本：
  [fig2_11_representative_layer_metrics.py](D:\Users\24932\Desktop\C_data\question_2\visualization\comparison\fig2_11_representative_layer_metrics.py)
- 图片：
  [fig2_11_representative_layer_metrics.png](D:\Users\24932\Desktop\C_data\question_2\visualization\comparison\fig2_11_representative_layer_metrics.png)
- 数据来源：
  [scheme_layer_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\scheme_layer_summary.csv)
- 用于说明：
  在单层尺度下四条路径的热风险差异

### 图2-13 单元级风险分布箱线图
- 脚本：
  [fig2_13_cell_risk_boxplots.py](D:\Users\24932\Desktop\C_data\question_2\visualization\comparison\fig2_13_cell_risk_boxplots.py)
- 图片：
  [fig2_13_cell_risk_boxplots.png](D:\Users\24932\Desktop\C_data\question_2\visualization\comparison\fig2_13_cell_risk_boxplots.png)
- 数据来源：
  [cell_risk_details.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\cell_risk_details.csv)
- 用于说明：
  风险是否集中在少量极端单元

### 图2-15 到图2-18 模型参数灵敏度折线图
- 脚本：
  - [fig2_15_A0_sensitivity.py](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_15_A0_sensitivity.py)
  - [fig2_16_alpha_sensitivity.py](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_16_alpha_sensitivity.py)
  - [fig2_17_beta_sensitivity.py](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_17_beta_sensitivity.py)
  - [fig2_18_gamma_sensitivity.py](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_18_gamma_sensitivity.py)
- 图片：
  - [fig2_15_A0_sensitivity.png](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_15_A0_sensitivity.png)
  - [fig2_16_alpha_sensitivity.png](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_16_alpha_sensitivity.png)
  - [fig2_17_beta_sensitivity.png](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_17_beta_sensitivity.png)
  - [fig2_18_gamma_sensitivity.png](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_18_gamma_sensitivity.png)
- 数据来源：
  `question_2/sensitivity_analysis/model_parameters/*/*_overall_summary.csv`
- 用于说明：
  `A0 / alpha / beta / gamma` 变化时，方案排序和综合风险是否稳定

### 图2-19 不同材料下综合风险对比图
- 脚本：
  [fig2_19_material_risk_comparison.py](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_19_material_risk_comparison.py)
- 图片：
  [fig2_19_material_risk_comparison.png](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_19_material_risk_comparison.png)
- 数据来源：
  [materials_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials_overall_summary.csv)
- 用于说明：
  不同材料场景下四条路径的综合热风险变化

### 图2-20 材料-路径排序热图
- 脚本：
  [fig2_20_material_rank_heatmap.py](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_20_material_rank_heatmap.py)
- 图片：
  [fig2_20_material_rank_heatmap.png](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_20_material_rank_heatmap.png)
- 数据来源：
  [materials_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials_overall_summary.csv)
- 用于说明：
  材料变化后方案排序是否反转

### 图2-22 权重场景下综合风险柱状图
- 脚本：
  [fig2_22_weighted_risk_by_scenario.py](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_22_weighted_risk_by_scenario.py)
- 图片：
  [fig2_22_weighted_risk_by_scenario.png](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_22_weighted_risk_by_scenario.png)
- 数据来源：
  [subjective_weights_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights_overall_summary.csv)
- 用于说明：
  不同权重场景下综合风险值如何变化

---

## 5. 批量运行方式

### 5.1 正文优先核心图
```powershell
python D:\Users\24932\Desktop\C_data\question_2\visualization\run_core_visualizations.py
```

### 5.2 附录型图
```powershell
python D:\Users\24932\Desktop\C_data\question_2\visualization\run_appendix_visualizations.py
```

---

## 6. 每张图旁边的 `.json` 文件有什么用

每张图都配了一个同名 `.json` 文件，例如：

- [fig2_3_final_heat_map.json](D:\Users\24932\Desktop\C_data\question_2\visualization\spatial\fig2_3_final_heat_map.json)
- [fig2_21_weight_rank_heatmap.json](D:\Users\24932\Desktop\C_data\question_2\visualization\sensitivity\fig2_21_weight_rank_heatmap.json)

这些文件用于记录：

- 图号
- 代表层或代表场景
- 使用的数据指标
- 输出图片路径

它们的作用主要是：

- 方便后续复现
- 方便你在论文或附录中解释“这张图是怎么选出来的”

---

## 7. 推荐的论文放置方式

### 正文建议优先使用
- 图2-1
- 图2-2
- 图2-3
- 图2-5
- 图2-8
- 图2-12
- 图2-14
- 图2-21

### 附录建议使用
- 图2-4
- 图2-6
- 图2-7
- 图2-9
- 图2-10
- 图2-11
- 图2-13
- 图2-15 到 图2-20
- 图2-22

---

## 8. 依赖说明

本目录脚本依赖：

```powershell
pip install matplotlib
```

如果前面的灵敏度分析和基础模型结果已经正常生成，这里的可视化脚本不需要额外安装别的库。

