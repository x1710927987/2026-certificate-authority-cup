# Question 2 Sensitivity Analysis

本目录用于存放问题二“热风险评价模型”的灵敏度分析代码、结构化结果文件和图片输出。  
所有脚本都建立在基础模型 [basic_model_for_question_2.py](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\basic_model_for_question_2.py) 的口径之上：

- 路径方案固定比较 `row_major`、`serpentine`、`center_out`、`minimum_time`
- 基础材料默认使用 `PA12`
- 过热阈值 `H_thres` 采用固定参考路径 `row_major` 的分位数对齐法重新估计
- 热风险综合评价同时输出：
  - 加权和法 `weighted_sum_total_risk`
  - `TOPSIS` 贴近度 `topsis_score`

---

## 1. 目录结构

### [model_parameters](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters)
对应“模型参数灵敏度分析”，研究热历程模型本身的参数变化会如何影响方案评价结果。

- [common.py](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\common.py)
  公共工具模块，供 4 个参数脚本复用。
- [A_0](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\A_0)
  自热项强度灵敏度分析。
- [alpha](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\alpha)
  时间衰减系数灵敏度分析。
- [beta](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\beta)
  空间衰减系数灵敏度分析。
- [gamma](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\gamma)
  接触修正系数灵敏度分析。

### [materials](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials)
对应“材料敏感性分析”，研究不同工业常用激光 3D 打印材料下，模型评价结果和方案排序是否稳定。

- [materials.py](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials.py)

### [subjective_weights](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights)
对应“一级主观权重场景灵敏度分析”，研究不同风险偏好下，综合评价结果是否稳健。

- [subjective_weights.py](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights.py)

---

## 2. 三类灵敏度分析分别回答什么问题

### 2.1 模型参数灵敏度
这部分关注：

- 自热项增强后，局部过热风险是否明显放大
- 历史热残余衰减更快或更慢时，方案排序是否变化
- 空间衰减增强或减弱后，局部热不均匀性会不会变得更严重
- 接触修正项变大后，边接触密集区域是否更敏感

这一部分主要回答：
“热历程模型的核心物理参数变化后，结论还稳不稳？”

### 2.2 材料敏感性
这部分关注：

- 换成不同材料后，风险值量级如何变化
- 不同材料的热敏感性因子 `kappa_mat` 如何变化
- 不同材料场景下，四条路径的优劣排序是否稳定

这一部分主要回答：
“模型是否能推广到不同材料场景？”

### 2.3 一级主观权重场景灵敏度
这部分关注：

- 当研究者更强调局部高温、热循环/稳定性、热均匀性时，最终排序是否变化
- 综合评价结果是否依赖某一组特定主观权重

这一部分主要回答：
“结论是否依赖决策偏好？”

---

## 3. 模型参数灵敏度分析

### 3.1 公共脚本

#### [common.py](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\common.py)
作用：

- 动态加载问题二基础模型
- 复用 CSV 写出逻辑
- 复用模型参数灵敏度的绘图逻辑
- 提供 `run_model_parameter_sensitivity(...)` 主流程

这份文件一般不单独运行，由各参数脚本调用。

### 3.2 自热项强度

#### [A_0.py](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\A_0\A_0.py)
分析参数：

- `A_0 ∈ {2, 3, 4, 5, 6}`

说明：

- 研究单元自身直接受热脉冲增强或减弱时，对 `R_theta`、综合风险与排序的影响。

输出文件：

- [a_0_results.json](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\A_0\a_0_results.json)
  总结每个 `A_0` 取值下的最佳方案与阈值信息。
- [a_0_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\A_0\a_0_overall_summary.csv)
  四条路径在每个 `A_0` 取值下的全任务结果。
- [a_0_layer_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\A_0\a_0_layer_summary.csv)
  分层级结果。
- [a_0_threshold_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\A_0\a_0_threshold_summary.csv)
  每个参数值对应的 `H_thres`、量化分位点等。
- [a_0_weight_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\A_0\a_0_weight_summary.csv)
  一级和二级权重信息。
- [a_0_plot.png](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\A_0\a_0_plot.png)
  四指标主图。
- [a_0_plot_threshold.png](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\A_0\a_0_plot_threshold.png)
  `H_thres` 随 `A_0` 的变化图。

适合在论文中说明：

- 自热项增强后，风险排序是否改变
- 局部高温风险是否显著被放大

### 3.3 时间衰减系数

#### [alpha.py](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\alpha\alpha.py)
分析参数：

- `alpha ∈ {0.12, 0.15, 0.18, 0.21, 0.24}`

说明：

- 研究热量时间衰减速度变化时，热残余保留效应如何改变评价结果。

输出文件与 `A_0` 目录结构一致：

- [alpha_results.json](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\alpha\alpha_results.json)
- [alpha_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\alpha\alpha_overall_summary.csv)
- [alpha_layer_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\alpha\alpha_layer_summary.csv)
- [alpha_threshold_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\alpha\alpha_threshold_summary.csv)
- [alpha_weight_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\alpha\alpha_weight_summary.csv)
- [alpha_plot.png](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\alpha\alpha_plot.png)
- [alpha_plot_threshold.png](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\alpha\alpha_plot_threshold.png)

适合在论文中说明：

- 历史热残余持续时间变化后，四种路径的稳健性是否一致

### 3.4 空间衰减系数

#### [beta.py](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\beta\beta.py)
分析参数：

- `beta ∈ {0.05, 0.065, 0.08, 0.095, 0.11}`

说明：

- 研究邻域热传播范围变化后，局部热不均匀性与综合风险如何变化。

输出文件：

- [beta_results.json](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\beta\beta_results.json)
- [beta_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\beta\beta_overall_summary.csv)
- [beta_layer_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\beta\beta_layer_summary.csv)
- [beta_threshold_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\beta\beta_threshold_summary.csv)
- [beta_weight_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\beta\beta_weight_summary.csv)
- [beta_plot.png](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\beta\beta_plot.png)
- [beta_plot_threshold.png](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\beta\beta_plot_threshold.png)

适合在论文中说明：

- 热影响是偏局部还是偏全局时，路径优劣会不会改变

### 3.5 接触修正系数

#### [gamma.py](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\gamma\gamma.py)
分析参数：

- `gamma ∈ {0, 0.25, 0.5, 0.75, 1.0}`

说明：

- 研究接触修正强度变化时，边接触关系较强区域的风险是否更敏感。

输出文件：

- [gamma_results.json](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\gamma\gamma_results.json)
- [gamma_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\gamma\gamma_overall_summary.csv)
- [gamma_layer_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\gamma\gamma_layer_summary.csv)
- [gamma_threshold_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\gamma\gamma_threshold_summary.csv)
- [gamma_weight_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\gamma\gamma_weight_summary.csv)
- [gamma_plot.png](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\gamma\gamma_plot.png)
- [gamma_plot_threshold.png](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\gamma\gamma_plot_threshold.png)

适合在论文中说明：

- 邻接接触程度对局部热传播和方案排序的影响

---

## 4. 材料敏感性分析

### [materials.py](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials.py)
分析对象：

- 全部 5 种工业常用材料：
  - `PA12`
  - `316L`
  - `Ti-6Al-4V`
  - `AlSi10Mg`
  - `Inconel 718`

口径说明：

- 材料数据来自 [激光粉末床相关五种材料热物性汇总表.md](D:\Users\24932\Desktop\C_data\question_2\激光粉末床相关五种材料热物性汇总表.md)
- 区间数据取中位数
- `kappa_mat` 的参考量固定使用 5 种材料总体中位参考值

输出文件：

- [materials_results.json](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials_results.json)
  各材料下最佳方案及阈值对齐结果。
- [materials_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials_overall_summary.csv)
  各材料下四条路径的全任务评价结果。
- [materials_layer_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials_layer_summary.csv)
  各材料下逐层结果。
- [materials_threshold_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials_threshold_summary.csv)
  各材料对应的 `H_thres`、`kappa_mat` 和阈值标定信息。
- [materials_weight_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials_weight_summary.csv)
  权重信息。
- [materials_material_property_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials_material_property_summary.csv)
  五种材料在模型中使用的实际数值与原始区间。
- [materials_results.xlsx](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials_results.xlsx)
  汇总工作簿。

图片：

- [materials_plot.png](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials_plot.png)
  综合风险、`R_theta`、`R_phi`、TOPSIS 的材料对比图。
- [materials_threshold.png](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials_threshold.png)
  `H_thres` 和 `kappa_mat` 的材料对比图。
- [materials_rank_heatmap.png](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials_rank_heatmap.png)
  各材料下方案排序热图。

适合在论文中说明：

- 模型能否推广到不同材料
- 哪些材料场景下路径排序更稳，哪些更敏感

---

## 5. 一级主观权重场景灵敏度分析

### [subjective_weights.py](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights.py)
分析对象：

- `base`
- `hotspot_priority`
- `cycle_stability_priority`
- `uniformity_priority`
- `balanced`

口径说明：

- 热历程模型、阈值对齐和基础材料都保持不变
- 只修改一级主观权重
- 用于检验综合排序是否依赖特定偏好

输出文件：

- [subjective_weights_results.json](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights_results.json)
  场景总览与每种场景下的最佳方案。
- [subjective_weights_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights_overall_summary.csv)
  各场景下四条路径的全任务结果。
- [subjective_weights_layer_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights_layer_summary.csv)
  各场景下逐层结果。
- [subjective_weights_part_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights_part_summary.csv)
  各场景下零件级结果。
- [subjective_weights_weight_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights_weight_summary.csv)
  一级和二级权重汇总。
- [subjective_weights_scenario_summary.csv](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights_scenario_summary.csv)
  每个权重场景的参数定义及最佳方案。
- [subjective_weights_results.xlsx](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights_results.xlsx)
  汇总工作簿。

图片：

- [subjective_weights_plot.png](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights_plot.png)
  各场景下加权和总风险与 TOPSIS 分值变化图。
- [subjective_weights_rank_heatmap.png](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights_rank_heatmap.png)
  加权和、TOPSIS 排名热图。
- [subjective_weights_best_scheme.png](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights_best_scheme.png)
  不同场景下最优方案变化图。

适合在论文中说明：

- 结论是否依赖主观偏好
- 若排序稳定，可证明综合评价稳健
- 若排序变化，则说明不同路径适配不同风险偏好

---

## 6. 推荐的论文使用方式

### 正文建议优先使用

- `model_parameters/*_plot.png`
  用来说明基础热历程模型对核心参数的稳健性
- [materials_plot.png](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials_plot.png)
  用来说明模型在不同材料场景下的适用性
- [materials_rank_heatmap.png](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials_rank_heatmap.png)
  用来说明不同材料下方案排序是否变化
- [subjective_weights_rank_heatmap.png](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights_rank_heatmap.png)
  用来说明结论是否依赖权重偏好

### 附录建议放置

- 所有 `*_layer_summary.csv`
  逐层明细较多，适合做附录表
- 所有 `*_weight_summary.csv`
  更适合作为模型复现依据
- 所有 `*_threshold_summary.csv`
  适合在附录中说明阈值对齐过程
- 所有 `*.xlsx`
  适合作为电子附件或补充材料

---

## 7. 运行依赖

本目录下所有脚本至少依赖：

```powershell
pip install matplotlib
```

如果需要自动导出 `xlsx` 工作簿，还需要：

```powershell
pip install openpyxl
```

---

## 8. 运行顺序建议

1. 先确保问题二基础模型已经运行完成：
   [basic_model_for_question_2.py](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\basic_model_for_question_2.py)
2. 再运行模型参数灵敏度
3. 再运行材料灵敏度
4. 最后运行一级主观权重场景灵敏度

这样做的好处是：

- 所有灵敏度分析都建立在同一套基础口径之上
- 如果后续你调整基础模型，重新跑时也更容易定位变化来源

