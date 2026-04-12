# Question 2 Overview

本目录对应认证杯 C 题的**问题二：热风险评价与路径方案比较**。  
这一层 README 的目标是把问题二的全部工作串起来，让你从根目录就能快速定位：

- 建模思路在哪里
- 材料数据从哪里来
- 基础模型代码和输出在哪里
- 灵敏度分析代码和输出在哪里
- 可视化代码和图片在哪里

---

## 1. 目录结构

### 思路与原始支撑文件
- [第二问思路.md](D:\Users\24932\Desktop\C_data\question_2\第二问思路.md)
  问题二的完整建模思路、指标体系、灵敏度分析方案和可视化方案。
- [激光粉末床相关五种材料热物性汇总表.md](D:\Users\24932\Desktop\C_data\question_2\激光粉末床相关五种材料热物性汇总表.md)
  五种常用激光 3D 打印材料的热物性汇总表。问题二中的材料参数直接从这里读取，区间值取中位数。

### 代码与结果目录
- [basic_model_for_question_2](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2)
  问题二基础模型代码与输出。
- [sensitivity_analysis](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis)
  问题二灵敏度分析代码与输出。
- [visualization](D:\Users\24932\Desktop\C_data\question_2\visualization)
  问题二可视化代码与图片。

---

## 2. 问题二在做什么

问题二的核心任务不是重新优化路径，而是：

1. 对 4 条给定路径方案进行统一热风险评价：
   - `row_major`
   - `serpentine`
   - `center_out`
   - `minimum_time`
2. 比较它们在“局部过热、热循环、成型稳定性、热分布不均匀性”等方面的差异
3. 在不同模型参数、不同材料、不同主观风险偏好下，检验结论是否稳健

基础比较对象来自：
- 题目提供的 3 条基准路径
- 问题一得到的最小时间路径

---

## 3. 基础模型

### 目录
- [basic_model_for_question_2](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2)

### 主脚本
- [basic_model_for_question_2.py](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\basic_model_for_question_2.py)

### 基础模型做了什么
- 读取问题一的最优路径和题目给定的 3 条基准路径
- 读取 `part_geometry.csv`、`local_geometry_relations.csv`、`machine_params.json`、`thermal_params.json`
- 读取 [激光粉末床相关五种材料热物性汇总表.md](D:\Users\24932\Desktop\C_data\question_2\激光粉末床相关五种材料热物性汇总表.md)
- 默认基础材料为 `PA12`
- 用 `row_major` 做分位数对齐，得到改进模型的 `H_thres`
- 计算单元级指标：
  - `mu`
  - `xi`
  - `theta`
  - `phi`
- 聚合得到层级、零件级和全任务级指标
- 输出：
  - 原始风险指标
  - 加权和法综合结果
  - `TOPSIS` 综合结果

### 关键输出
- [question_2_base_results.json](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\question_2_base_results.json)
- [scheme_overall_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\scheme_overall_summary.csv)
- [scheme_layer_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\scheme_layer_summary.csv)
- [scheme_part_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\scheme_part_summary.csv)
- [cell_risk_details.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\cell_risk_details.csv)
- [heat_history_records.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\heat_history_records.csv)
- [scheme_path_steps.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\scheme_path_steps.csv)
- [threshold_alignment_reference.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\threshold_alignment_reference.csv)
- [evaluation_weights_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\evaluation_weights_summary.csv)
- [material_properties_summary.csv](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\material_properties_summary.csv)

### 补充说明
这一层的详细解释已经写在：
- [basic_model_for_question_2/README.md](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\README.md)

---

## 4. 灵敏度分析

### 目录
- [sensitivity_analysis](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis)

### 总说明
- [sensitivity_analysis/README.md](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\README.md)

当前灵敏度分析分为 3 类。

### 4.1 模型参数灵敏度
目录：
- [model_parameters](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters)

对应参数：
- `A_0`
- `alpha`
- `beta`
- `gamma`

每个参数都单独有一个脚本和一个输出目录，例如：
- [A_0.py](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\A_0\A_0.py)
- [alpha.py](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\alpha\alpha.py)
- [beta.py](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\beta\beta.py)
- [gamma.py](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\model_parameters\gamma\gamma.py)

每一类都会输出：
- 整体结果 `json`
- 层级结果 `csv`
- 阈值对齐结果 `csv`
- 权重结果 `csv`
- 可视化图片 `png`

### 4.2 材料敏感性
目录：
- [materials](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials)

脚本：
- [materials.py](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\materials\materials.py)

作用：
- 比较 5 种材料下的热风险评价结果
- 保持 `kappa_mat` 的参考量固定为 5 种材料总体中位参考值

### 4.3 一级主观权重场景灵敏度
目录：
- [subjective_weights](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights)

脚本：
- [subjective_weights.py](D:\Users\24932\Desktop\C_data\question_2\sensitivity_analysis\subjective_weights\subjective_weights.py)

作用：
- 研究不同风险偏好场景下，综合排序是否改变

---

## 5. 可视化

### 目录
- [visualization](D:\Users\24932\Desktop\C_data\question_2\visualization)

### 总说明
- [visualization/README.md](D:\Users\24932\Desktop\C_data\question_2\visualization\README.md)

当前可视化已经分为 6 类：
- `common`
- `mechanism`
- `spatial`
- `temporal`
- `comparison`
- `sensitivity`

### 两个批量运行入口
- [run_core_visualizations.py](D:\Users\24932\Desktop\C_data\question_2\visualization\run_core_visualizations.py)
  生成正文优先的核心图。
- [run_appendix_visualizations.py](D:\Users\24932\Desktop\C_data\question_2\visualization\run_appendix_visualizations.py)
  生成附录型图。

### 核心图已经覆盖的图号
- 图2-1
- 图2-2
- 图2-3
- 图2-5
- 图2-8
- 图2-12
- 图2-14
- 图2-21

### 附录型图已经覆盖的图号
- 图2-4
- 图2-6
- 图2-7
- 图2-9
- 图2-10
- 图2-11
- 图2-13
- 图2-15
- 图2-16
- 图2-17
- 图2-18
- 图2-19
- 图2-20
- 图2-22

---

## 6. 推荐使用顺序

如果你要从头复现问题二，我建议按这个顺序：

1. 先看思路  
   [第二问思路.md](D:\Users\24932\Desktop\C_data\question_2\第二问思路.md)

2. 再确认材料数据  
   [激光粉末床相关五种材料热物性汇总表.md](D:\Users\24932\Desktop\C_data\question_2\激光粉末床相关五种材料热物性汇总表.md)

3. 运行基础模型  
   [basic_model_for_question_2.py](D:\Users\24932\Desktop\C_data\question_2\basic_model_for_question_2\basic_model_for_question_2.py)

4. 运行灵敏度分析  
   先 `model_parameters`，再 `materials`，最后 `subjective_weights`

5. 运行可视化  
   先正文核心图，再附录图

---

## 7. 各部分之间怎么衔接

可以把问题二理解成三层：

### 第一层：基础模型
输入路径方案，输出热风险指标和综合评价结果。

### 第二层：灵敏度分析
在基础模型的框架下，改变参数、材料或权重，检验结论稳健性。

### 第三层：可视化
把基础模型和灵敏度分析输出的表格结果转成论文插图：
- 机制解释图
- 空间热分布图
- 时间演化图
- 方案比较图
- 敏感性图

也就是说：
- `basic_model_for_question_2` 负责“算”
- `sensitivity_analysis` 负责“检验稳不稳”
- `visualization` 负责“把结果讲清楚”

---

## 8. 依赖说明

问题二整体目前主要依赖：

```powershell
pip install matplotlib openpyxl
```

说明：
- `matplotlib` 用于出图
- `openpyxl` 用于导出 `xlsx`

如果缺少 `openpyxl`，很多脚本仍然能跑，只是不会写 `xlsx` 文件。

