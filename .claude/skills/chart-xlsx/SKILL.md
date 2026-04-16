---
description: 根据用户需求对 xlsx 数据画图，支持折线图、柱状图、散点图，输出 PNG 到 output/
allowed-tools: Bash, Read, Glob, Write
---

# chart-xlsx

读取 `data/` 目录中的 xlsx 文件，调用 Python 脚本生成图表，保存到 `output/`。

## 触发条件

**触发**：用户明确要求画图、绘图、可视化，或描述趋势/对比/关系时。关键词示例：折线图、柱状图、散点图、趋势、对比、走势、画、plot、chart。

**不触发**：用户只想了解数据概况（→ `explore-xlsx`）或导出筛选结果（→ `export-xlsx`）。

## 首选库

| 用途 | 库 |
|------|-----|
| 数据处理 | `pandas` |
| 图表 | `matplotlib` + `seaborn` |
| 终端输出 | `rich` |

## 输出规范

| 类型 | 路径 | 参数 |
|------|------|------|
| 图表 | `output/<文件名>_<描述>.png` | dpi=150，tight_layout |

完成后用 `rich` 打印输出文件路径列表。

## 临时脚本原则

需要超出现有脚本能力的图表时，用 **uv inline script**（PEP 723）实现，不在 `.claude/skills/` 下创建新文件。将脚本写入 `output/_tmp.py`，运行后立即删除：

```bash
uv run python -X utf8 output/_tmp.py && rm output/_tmp.py
```

脚本开头声明依赖：

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "openpyxl", "matplotlib", "seaborn", "rich"]
# ///
```

## 可用脚本

所有脚本位于 `.claude/skills/chart-xlsx/`，统一用 `uv run python -X utf8` 运行。

### line_chart.py — 折线图（趋势/时序）

```
用法：
    uv run python -X utf8 .claude/skills/chart-xlsx/line_chart.py data/<文件>.xlsx --x 日期 --y 销售额
    uv run python -X utf8 .claude/skills/chart-xlsx/line_chart.py data/<文件>.xlsx --x 日期 --y 销售额 利润 --sheet Sheet1

参数：
    --x      X 轴列名（必填）
    --y      Y 轴列名（必填，可多列）
    --sheet  指定 sheet（默认第一个）
    --title  图表标题（默认自动生成）

输出：
    output/<文件名>_<sheet>_line.png
```

### bar_chart.py — 柱状图（分类对比）

```
用法：
    uv run python -X utf8 .claude/skills/chart-xlsx/bar_chart.py data/<文件>.xlsx --x 部门 --y 销售额
    uv run python -X utf8 .claude/skills/chart-xlsx/bar_chart.py data/<文件>.xlsx --x 部门 --y 销售额 利润 --stacked

参数：
    --x        类别轴列名（必填）
    --y        数值列名（必填，可多列）
    --sheet    指定 sheet（默认第一个）
    --stacked  堆叠柱状图（默认并排）
    --title    图表标题（默认自动生成）

输出：
    output/<文件名>_<sheet>_bar.png
```

### scatter.py — 散点图（变量关系）

```
用法：
    uv run python -X utf8 .claude/skills/chart-xlsx/scatter.py data/<文件>.xlsx --x 销售额 --y 利润
    uv run python -X utf8 .claude/skills/chart-xlsx/scatter.py data/<文件>.xlsx --x 销售额 --y 利润 --hue 部门

参数：
    --x      X 轴数值列（必填）
    --y      Y 轴数值列（必填）
    --hue    分组着色列（可选）
    --sheet  指定 sheet（默认第一个）
    --title  图表标题（默认自动生成）

输出：
    output/<文件名>_<sheet>_scatter.png
```

## 执行步骤

### 1. 确认目标文件

用 Glob 工具列出 `data/*.xlsx`：

- **只有一个文件** → 直接使用
- **多个文件且用户未指定** → 列出文件名，询问用户选择哪个
- **零个文件** → 告知用户将 xlsx 文件放入 `data/` 目录后再试，停止执行

### 2. 确认列名

若用户未指定 X/Y 列，先用 `inspect_xlsx.py`（explore-xlsx skill）获取列名后再询问用户，不要猜测列名。

### 3. 选择脚本并执行

| 用户描述 | 脚本 |
|---------|------|
| 趋势、时序、折线、走势 | `line_chart.py` |
| 对比、排名、柱状、条形 | `bar_chart.py` |
| 关系、相关、散点 | `scatter.py` |

若脚本文件不存在，用 **uv inline script** 临时实现（写入 `output/_tmp.py`，运行后删除），不要询问用户是否创建。

### 4. 汇报结果

用 `rich` 打印所有生成的输出文件路径，并简要说明图表内容。

## 错误处理

- **脚本退出码非 0**：将 stderr 原文展示给用户，不要猜测或自行修复原因
- **列名不存在**：明确告知用户列名有误，列出实际列名让用户重新选择
- **脚本文件本身不存在**：说明该功能尚未实现，询问用户是否需要创建该脚本

## 注意事项

- 始终使用 `uv run python -X utf8`，不要直接调用 `python`
- 所有脚本路径以项目根目录为工作目录运行
- 图表必须包含标题、轴标签，中文标签需使用中文字体
