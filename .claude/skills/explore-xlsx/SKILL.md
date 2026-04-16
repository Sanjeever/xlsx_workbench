---
description: 用 Python 代码探索 xlsx 文件结构，输出 sheet、列、类型、缺失值、数值统计等信息
allowed-tools: Bash, Read, Glob, Write
---

# explore-xlsx

探索 `data/` 目录中的 xlsx 文件，通过 Python 脚本获取结构和统计信息，结果打印到终端；深入分析阶段按需生成文件到 `output/`。

## 触发条件

**触发**：用户想了解 xlsx 文件"里有什么"——包括列名、行数、数据类型、数值分布、缺失值、类别分组、相关性等任何结构性或统计性问题。关键词示例：探索、看看、结构、有哪些列、分析一下、数据概况、字段。

**不触发**：用户已明确知道要做什么（如"画折线图"、"导出某列"），直接执行即可，无需先跑 inspect。

## 首选库

| 用途 | 库 |
|------|-----|
| 数据处理 | `pandas` |
| xlsx 读写 | `openpyxl`（pandas 后端） |
| 通用图表 | `matplotlib` |
| 统计图表 | `seaborn` |
| 终端输出 | `rich` |

## 输出规范

| 类型 | 路径 | 参数 |
|------|------|------|
| 图表 | `output/<文件名>_<描述>.png` | dpi=150，tight_layout |
| 数据表 | `output/<文件名>_<描述>.csv` | encoding=utf-8-sig |
| 文字报告 | `output/<文件名>_report.md` | — |

完成后用 `rich` 打印输出文件路径列表。

## 临时脚本原则

需要超出现有脚本能力的分析时，用 **uv inline script**（PEP 723）实现，不在 `.claude/skills/` 下创建新文件。将脚本写入 `output/_tmp.py`，运行后立即删除：

```bash
uv run python -X utf8 output/_tmp.py && rm output/_tmp.py
```

脚本开头声明依赖：

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "openpyxl", "rich"]
# ///
```

## 可用脚本

所有脚本位于 `.claude/skills/explore-xlsx/`，统一用 `uv run python -X utf8` 运行。

### inspect_xlsx.py — 文件结构探查（终端 + Markdown 报告）

```
用法：
    uv run python -X utf8 .claude/skills/explore-xlsx/inspect_xlsx.py data/<文件>.xlsx
    uv run python -X utf8 .claude/skills/explore-xlsx/inspect_xlsx.py data/<文件>.xlsx --sheet Sheet1

输出：
    终端：rich 格式的列概览表
    output/<文件名>_report.md：Markdown 结构报告（列类型、缺失率、数值统计、分类高频值）
```

### summary_stats.py — 数值列描述统计 + 分布直方图

```
用法：
    uv run python -X utf8 .claude/skills/explore-xlsx/summary_stats.py data/<文件>.xlsx
    uv run python -X utf8 .claude/skills/explore-xlsx/summary_stats.py data/<文件>.xlsx --sheet Sheet1 --cols 销售额 利润

输出：
    output/<文件名>_<sheet>_stats.csv        描述统计表（含中位数、偏度、峰度）
    output/<文件名>_<sheet>_distribution.png 各列分布直方图（KDE）
```

### correlation.py — 数值列相关矩阵 + 热力图

```
用法：
    uv run python -X utf8 .claude/skills/explore-xlsx/correlation.py data/<文件>.xlsx
    uv run python -X utf8 .claude/skills/explore-xlsx/correlation.py data/<文件>.xlsx --sheet Sheet1 --method spearman

参数：
    --method  pearson（默认）| spearman | kendall

输出：
    output/<文件名>_<sheet>_correlation.csv  相关矩阵
    output/<文件名>_<sheet>_correlation.png  下三角热力图
```

### pivot_export.py — 分组聚合导出 CSV

```
用法：
    uv run python -X utf8 .claude/skills/explore-xlsx/pivot_export.py data/<文件>.xlsx --by 部门
    uv run python -X utf8 .claude/skills/explore-xlsx/pivot_export.py data/<文件>.xlsx --by 部门 季度 --agg mean --cols 销售额 利润

参数：
    --by    分组列名（必填，可多列）
    --agg   sum（默认）| mean | count | median | min | max
    --cols  要聚合的数值列（默认全部）

输出：
    output/<文件名>_<sheet>_by_<分组列>_<agg>.csv
    终端：前 10 行预览
```

## 执行步骤

### 1. 确认目标文件

用 Glob 工具列出 `data/*.xlsx`，不要用内联 Python 代码：

- **只有一个文件** → 直接使用
- **多个文件且用户未指定** → 列出文件名，询问用户选择哪个
- **零个文件** → 告知用户将 xlsx 文件放入 `data/` 目录后再试，停止执行

### 2. 探索文件结构

**优先使用 `inspect_xlsx.py`**，它会同时输出终端摘要和 Markdown 报告：

```bash
uv run python -X utf8 .claude/skills/explore-xlsx/inspect_xlsx.py data/<文件>.xlsx
```

若脚本文件本身不存在，用 **uv inline script** 临时实现（写入 `output/_tmp.py`，运行后删除），不要询问用户是否创建脚本。

### 3. 执行决策

读取 inspect 输出的摘要，向用户报告要点（sheet 数、行数、列名、数值列、缺失情况），然后询问下一步方向：

```
用户请求 → inspect_xlsx.py → 报告摘要 → 询问下一步
   ├─ 分布 / 偏度    → summary_stats.py
   ├─ 列间相关性     → correlation.py
   └─ 按类别汇总     → pivot_export.py
```

### 4. 汇报结果

深入分析完成后，用 `rich` 打印所有生成的输出文件路径，并简要说明每个文件的内容。

## 错误处理

- **脚本退出码非 0**：将 stderr 原文展示给用户，不要猜测或自行修复原因
- **文件路径不存在**：提示用户检查 `data/` 目录，不要尝试创建或下载文件
- **脚本文件本身不存在**：用 uv inline script 临时实现（写入 `output/_tmp.py`，运行后删除），不要询问用户

## 注意事项

- 始终使用 `uv run python -X utf8`，不要直接调用 `python`（`-X utf8` 避免 Windows 中文乱码）
- 所有脚本路径以项目根目录为工作目录运行
- 多个 sheet 默认全部分析，除非用户指定
