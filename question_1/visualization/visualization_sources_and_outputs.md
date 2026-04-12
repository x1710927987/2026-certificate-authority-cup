# 问题一新增可视化清单

## 1. 基础模型图

### 脚本
- `base_geometry_optimal_path.py`

### 输出图片
- `representative_layer_geometry.png`
- `representative_layer_optimal_path.png`
- `representative_layer_visit_order.png`

### 主要数据源
- `part_geometry.csv`
- `question_1/basic_model_result_for_question_1/question_1_results.json`
- `question_1/basic_model_result_for_question_1/question_1_path_steps.csv`

## 2. 方案比较图

### 脚本
- `baseline_scheme_comparison.py`

### 输出图片
- `baseline_vs_optimal_path_part_A.png`
- `baseline_vs_optimal_path_part_B.png`
- `baseline_vs_optimal_metrics.png`

### 中间数据输出
- `baseline_vs_optimal_metrics.csv`

### 主要数据源
- `part_geometry.csv`
- `local_geometry_relations.csv`
- `baseline_paths.csv`
- `machine_params.json`
- `question_1/basic_model_result_for_question_1/question_1_path_steps.csv`
- `question_1/basic_model_result_for_question_1/question_1_results.json`

## 3. 时间分解图

### 脚本
- `time_breakdown_visualization.py`

### 输出图片
- `layer_time_breakdown_stacked.png`
- `total_task_time_decomposition.png`

### 主要数据源
- `question_1/basic_model_result_for_question_1/question_1_layer_summary.csv`
- `question_1/basic_model_result_for_question_1/question_1_results.json`

## 4. 解结构敏感性路径图

### 脚本
- `structural_sensitivity_path_comparison.py`

### 输出图片
- `fixed_starting_point_path_comparison.png`
- `fixed_endpoint_path_comparison.png`
- `return_to_warehouse_path_comparison.png`

### 主要数据源
- `part_geometry.csv`
- `local_geometry_relations.csv`
- `question_1/basic_model_result_for_question_1/question_1_path_steps.csv`
- `question_1/sensitivity_analysis/fixed_starting_point/fixed_starting_point_summary.csv`
- `question_1/sensitivity_analysis/fixed_endpoint/fixed_endpoint_summary.csv`
- `question_1/sensitivity_analysis/return_to_warehouse/return_to_warehouse_summary.csv`
