# xlsx_workbench

AI 驱动的 Excel 文件分析工作台。用户将 xlsx 文件放入 `data/` 目录，通过对话描述分析需求，由 agent 自动完成分析并将结果写入 `output/`。

## 环境

使用 `uv` 管理依赖。运行 Python 脚本时始终使用：

```bash
uv run python -X utf8 .claude/skills/<skill>/<script>.py
```

`-X utf8` 强制 UTF-8 模式，避免 Windows 终端中文乱码。不要使用 `python` 或 `pip` 直接调用。

### AI 临时脚本：uv inline script

当现有脚本无法满足需求，需要临时编写代码时，使用 [uv inline script metadata（PEP 723）](https://docs.astral.sh/uv/guides/scripts/#declaring-script-dependencies)，通过 `uv run` 直接运行，**不得在 `.claude/skills/` 下创建新脚本文件**。

格式：

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "openpyxl", "rich"]
# ///
import sys
...
```

运行方式（将脚本内容写入临时文件后执行，或用 heredoc 传入）：

```bash
uv run -X utf8 - <<'EOF'
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "openpyxl", "rich"]
# ///
import sys
...
EOF
```

> Windows bash 不支持 heredoc，改用 `Write` 工具将脚本写入 `output/_tmp.py`，运行后立即删除：
>
> ```bash
> uv run python -X utf8 output/_tmp.py && rm output/_tmp.py
> ```

## 目录约定

| 目录 | 用途 |
|------|------|
| `data/` | 用户放置 xlsx 输入文件的目录 |
| `output/` | 所有分析结果的输出目录（图表、CSV、报告） |
| `.claude/skills/` | Skills 及其配套 Python 脚本 |

分析脚本与各自的 skill 放在同一目录，不单独设 `scripts/` 目录。

## Skill 选择策略

根据用户意图选择对应 skill，不要在意图明确时多此一举地运行其他 skill：

| 用户意图关键词 | 优先 skill |
|---------------|-----------|
| 探索、看看、有哪些列、数据概况、结构、字段、缺失、分布、相关性 | `explore-xlsx` |
| 画图、折线、柱状、散点、趋势、可视化 | `chart-xlsx` |
| 筛选、排序、导出、前N名、条件过滤、取子集 | `export-xlsx` |

意图不明时默认先用 `explore-xlsx` 获取数据概况，再询问下一步。

## 新主题检测与 output 清理

每轮对话开始前，判断用户是否开启了**新的分析主题**。满足以下任一条件即视为新主题：

- 切换了 xlsx 文件（`data/` 下的目标文件与上一轮不同）
- 分析目标明显转换（如从"探索销售数据"转向"分析用户留存"）
- 用户明确说"重新开始"、"换一个"、"新的分析"

**检测到新主题时**，在执行任何分析前，先用 Glob 列出 `output/` 现有文件，若非空则询问用户：

> `output/` 里有 N 个文件（列出文件名）。开始新分析前要清空吗？

- 用户确认清空 → `rm output/*`（`_tmp.py` 同样删除），然后继续分析
- 用户选择保留 → 直接继续，不删除任何文件

**不触发询问的情况**：
- 同一主题的后续步骤（如先探索再画图）
- `output/` 为空
- 用户本轮请求本身就是"清空 output"

## 大文件处理

行数 > 50000 时，告知用户数据量较大，先对数值列进行抽样分析（`df.sample(10000, random_state=42)`），完成后说明已抽样及样本量。

## 输出汇总

每次分析结束后，列出本次生成的所有 `output/` 文件，格式：

```
output/文件名.csv  — 一句话说明内容
output/文件名.png  — 一句话说明内容
```

