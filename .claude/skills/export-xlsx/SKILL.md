---
description: 从 xlsx 中按条件筛选行、排序后导出 CSV；支持条件过滤和 TopN 排名
allowed-tools: Bash, Read, Glob, Write
---

# export-xlsx

读取 `data/` 目录中的 xlsx 文件，按用户指定的条件筛选或排序后，将子集导出为 CSV 到 `output/`。

## 触发条件

**触发**：用户要提取数据子集，关键词示例：筛选、过滤、只要、导出、取出、前N名、排名、TopN、大于、等于、条件。

**不触发**：
- 用户要做聚合汇总（→ `explore-xlsx` 的 `pivot_export.py`）
- 用户要画图（→ `chart-xlsx`）
- 用户只想看数据概况（→ `explore-xlsx`）

## 首选库

| 用途 | 库 |
|------|-----|
| 数据处理 | `pandas` |
| 终端输出 | `rich` |

## 输出规范

| 类型 | 路径 |
|------|------|
| 数据表 | `output/<文件名>_<描述>.csv`（encoding=utf-8-sig） |

完成后用 `rich` 打印输出文件路径列表及行数。

## 临时脚本原则

需要超出现有脚本能力的导出逻辑时，用 **uv inline script**（PEP 723）实现，不在 `.claude/skills/` 下创建新文件。将脚本写入 `output/_tmp.py`，运行后立即删除：

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

所有脚本位于 `.claude/skills/export-xlsx/`，统一用 `uv run python -X utf8` 运行。

### filter_export.py — 条件筛选导出

```
用法：
    uv run python -X utf8 .claude/skills/export-xlsx/filter_export.py data/<文件>.xlsx --col 销售额 --op gt --val 1000
    uv run python -X utf8 .claude/skills/export-xlsx/filter_export.py data/<文件>.xlsx --col 部门 --op eq --val 销售部 --sheet Sheet1

参数：
    --col    筛选列名（必填）
    --op     比较运算符（必填）：eq | ne | gt | ge | lt | le | contains | startswith
    --val    比较值（必填）
    --sheet  指定 sheet（默认第一个）

输出：
    output/<文件名>_<sheet>_filter_<col>_<op>_<val>.csv
    终端：前 10 行预览 + 总行数
```

### rank_export.py — 排序 / TopN 导出

```
用法：
    uv run python -X utf8 .claude/skills/export-xlsx/rank_export.py data/<文件>.xlsx --by 销售额
    uv run python -X utf8 .claude/skills/export-xlsx/rank_export.py data/<文件>.xlsx --by 利润 --top 20 --asc --sheet Sheet1

参数：
    --by     排序列名（必填）
    --top    只保留前 N 行（默认全部）
    --asc    升序（默认降序）
    --sheet  指定 sheet（默认第一个）

输出：
    output/<文件名>_<sheet>_rank_<by>[_top<N>].csv
    终端：前 10 行预览 + 总行数
```

## 执行步骤

### 1. 确认目标文件

用 Glob 工具列出 `data/*.xlsx`：

- **只有一个文件** → 直接使用
- **多个文件且用户未指定** → 列出文件名，询问用户选择哪个
- **零个文件** → 告知用户将 xlsx 文件放入 `data/` 目录后再试，停止执行

### 2. 确认列名和条件

若用户未明确指定列名，先用 `inspect_xlsx.py`（explore-xlsx skill）获取列名，再询问用户具体条件。不要猜测列名。

### 3. 选择脚本并执行

| 用户描述 | 脚本 |
|---------|------|
| 筛选、过滤、只要…的行、条件 | `filter_export.py` |
| 排名、排序、前N名、TopN | `rank_export.py` |

若脚本文件不存在，用 **uv inline script** 临时实现（写入 `output/_tmp.py`，运行后删除），不要询问用户是否创建。

### 4. 汇报结果

打印生成的 CSV 路径，并说明：导出了多少行、来自哪个 sheet、满足什么条件。

## 错误处理

- **脚本退出码非 0**：将 stderr 原文展示给用户，不要猜测或自行修复原因
- **列名不存在**：明确告知用户列名有误，列出实际列名让用户重新选择
- **筛选结果为空**：告知用户没有满足条件的行，建议调整条件
- **脚本文件本身不存在**：说明该功能尚未实现，询问用户是否需要创建该脚本

## 注意事项

- 始终使用 `uv run python -X utf8`，不要直接调用 `python`
- 所有脚本路径以项目根目录为工作目录运行
- 导出文件名要包含筛选条件，方便用户识别
