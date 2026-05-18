---
description: AI 驱动的 xlsx 数据分析。按用户意图生成 uv inline script，覆盖结构探索、统计、聚合、筛选、排序、可视化等全部分析需求。
allowed-tools: Bash, Read, Write, Glob
---

# xlsx

唯一的 xlsx 分析 skill。所有任务通过 **uv inline script**（PEP 723）完成：用 Write 工具把脚本写入 `output/s_<session_id>/_tmp.py`，运行后立即删除。不在 `.claude/skills/` 下创建任何 `.py` 文件。

**`<session_id>` 是 6 位 hex（如 `a3f9b2`）**，首次执行分析前用 `uv run python -c "import secrets; print(secrets.token_hex(3))"` 生成，整个 Claude Code session 内复用。生成后 `mkdir -p output/s_<session_id>/`。所有路径占位符（包括 `_tmp.py`、`OUT`、产物文件名）写脚本时都要替换成实际值。详见 `CLAUDE.md` 的「多 Claude Code 并发隔离」节。

## 触发条件

**触发**：用户提到 xlsx / Excel / `data/` 下的文件，或任何数据分析意图——看看、概况、画图、筛选、导出、统计、对比、排名、相关性、汇总、趋势、分布、Top N 等。

**不触发**：通用编程问题、与 xlsx 无关的任务、要求修改 skill 本身。

## 执行步骤

1. **确认目标文件**：用 Glob 列出 `data/*.xlsx`
   - 1 个 → 直接用
   - 多个且未指定 → 列出文件名让用户选
   - 0 个 → 提示用户放文件后再试，停止
2. **首次接触新文件**且用户意图不是"我已经知道要画什么"时，先跑**模板 1（结构探索）**，向用户报告 sheet 数、行数、列名、数值/类别列、缺失情况
3. **选模板**（见下方代码模板节），把内容写入 `output/s_<session_id>/_tmp.py`，**只改参数、路径占位符与必要逻辑**，运行
4. **运行 + 清理**：`uv run python -X utf8 output/s_<session_id>/_tmp.py && rm output/s_<session_id>/_tmp.py`
5. **汇报**：列出本次新生成的 `output/s_<session_id>/` 下的文件（写完整路径），**并给 3–5 条结论性 bullet**（如"购买合同占 62%"、"产品 3 销量最高"——不是"已生成 X.png"）

## 代码契约

所有 inline script 必须满足：

- **PEP 723 header**，按需声明依赖
- **中文字体**（涉及绘图时）：
  ```python
  import matplotlib
  matplotlib.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
  matplotlib.rcParams["axes.unicode_minus"] = False
  ```
- **输出路径**：`output/s_<session_id>/<文件名>_<描述>.<ext>`，`Path("output/s_<session_id>").mkdir(parents=True, exist_ok=True)`
- **CSV**：`encoding="utf-8-sig"`（Excel 直接打开不乱码）
- **PNG**：`dpi=150, bbox_inches="tight"` + `plt.tight_layout()`
- **大文件**（> 50000 行）：`df.sample(10000, random_state=42)`，汇报时注明已抽样
- **错误处理**：用 try/except 捕获到顶层，`console.print` 红色 + `sys.exit(1)`，让 stderr 暴露给 agent

## 代码模板

下面 6 个模板都是开箱可跑的完整 inline script。把模板内容写入 `output/s_<session_id>/_tmp.py`，按用户需求改参数、并把 `OUT = Path("output/s_<session_id>")` 里的占位符替换为实际 session id。

### 模板 1：结构探索

用于了解文件有哪些 sheet、列名、类型、缺失率、数值分布、类别高频值。

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "openpyxl", "rich", "tabulate"]
# ///
import sys
from pathlib import Path
import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()
FILE = Path("data/<文件名>.xlsx")   # ← 改这里
OUT = Path("output/s_<session_id>"); OUT.mkdir(parents=True, exist_ok=True)

try:
    sheets = pd.read_excel(FILE, sheet_name=None, engine="openpyxl")
    lines = [f"# 文件结构报告：{FILE.name}\n"]
    for sname, df in sheets.items():
        lines += [f"## Sheet: `{sname}`\n", f"- 行数：{len(df)}", f"- 列数：{len(df.columns)}\n"]

        tbl = Table(title=f"Sheet: {sname}", show_lines=True)
        for c in ("列名", "类型", "非空", "缺失率"):
            tbl.add_column(c)
        lines += ["### 列详情\n", "| 列名 | 类型 | 非空 | 缺失 | 缺失率 |", "|---|---|---|---|---|"]
        for col in df.columns:
            miss = df[col].isna().sum()
            rate = f"{miss/len(df)*100:.1f}%" if len(df) else "N/A"
            lines.append(f"| {col} | {df[col].dtype} | {df[col].notna().sum()} | {miss} | {rate} |")
            tbl.add_row(str(col), str(df[col].dtype), str(df[col].notna().sum()), rate)
        console.print(tbl)
        lines.append("")

        num_cols = df.select_dtypes(include="number").columns.tolist()
        if num_cols:
            lines += ["### 数值列描述统计\n", df[num_cols].describe().round(4).to_markdown(), ""]

        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if cat_cols:
            lines.append("### 类别列前 5 高频值\n")
            for col in cat_cols:
                lines.append(f"**{col}**")
                for v, c in df[col].value_counts().head(5).items():
                    lines.append(f"- `{v}`：{c} 次")
                lines.append("")

    report = OUT / f"{FILE.stem}_report.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"\n[green]报告已写入 {report}[/green]")
except Exception as e:
    console.print(f"[red]执行出错：{e}[/red]")
    sys.exit(1)
```

### 模板 2：聚合分析

按一列或多列 groupby，对数值列做 sum / mean / count / median / min / max。

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "openpyxl", "rich", "tabulate"]
# ///
import sys
from pathlib import Path
import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()
FILE = Path("data/<文件名>.xlsx")     # ← 改这里
SHEET = None                           # None = 第一个 sheet
BY = ["合同类型"]                       # ← 分组列（可多列）
COLS = None                            # None = 全部数值列；或 ["总金额", "购买数量"]
AGG = "sum"                            # sum / mean / count / median / min / max

OUT = Path("output/s_<session_id>"); OUT.mkdir(parents=True, exist_ok=True)

try:
    df = pd.read_excel(FILE, sheet_name=SHEET, engine="openpyxl")
    missing = [c for c in BY if c not in df.columns]
    if missing:
        console.print(f"[red]分组列不存在：{missing}，实际列：{df.columns.tolist()}[/red]")
        sys.exit(1)

    num_cols = df.select_dtypes(include="number").columns.tolist()
    cols = [c for c in (COLS or num_cols) if c in num_cols]
    if not cols:
        console.print("[red]没有可聚合的数值列[/red]"); sys.exit(1)

    grouped = df.groupby(BY)[cols].agg(AGG).round(4).reset_index()
    slug = f"{FILE.stem}_by_{'_'.join(BY)}_{AGG}"
    out = OUT / f"{slug}.csv"
    grouped.to_csv(out, index=False, encoding="utf-8-sig")

    preview = grouped.head(10)
    tbl = Table(title=f"聚合预览（{AGG}，共 {len(grouped)} 行）", show_lines=True)
    for c in preview.columns:
        tbl.add_column(str(c), style="cyan" if c in BY else "white")
    for _, row in preview.iterrows():
        tbl.add_row(*[str(v) for v in row])
    console.print(tbl)
    console.print(f"[green]→ {out}[/green]")
except Exception as e:
    console.print(f"[red]执行出错：{e}[/red]")
    sys.exit(1)
```

### 模板 3：条件筛选 / 排序 / TopN

支持多条件 AND（数值比较、字符串 contains / startswith、日期范围 between），可选排序与 TopN。

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "openpyxl", "rich", "tabulate"]
# ///
import sys
from pathlib import Path
import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()
FILE = Path("data/<文件名>.xlsx")     # ← 改这里
SHEET = None

# 条件列表，AND 关系。每条 (列, 运算符, 值)
# 运算符：eq, ne, gt, ge, lt, le, contains, startswith, between
CONDITIONS = [
    ("合同类型", "eq", "购买合同"),
    ("总金额", "gt", 1_000_000),
    # ("合同签约时间", "between", ("2024-01-01", "2024-12-31")),
]
SORT_BY = "总金额"          # None = 不排序
ASC = False                  # 降序
TOP = 10                     # None = 全部

OUT = Path("output/s_<session_id>"); OUT.mkdir(parents=True, exist_ok=True)


def apply_one(df, col, op, val):
    if col not in df.columns:
        raise ValueError(f"列不存在：{col}，实际列：{df.columns.tolist()}")
    s = df[col]
    if op == "between":
        lo, hi = pd.to_datetime(val[0]), pd.to_datetime(val[1])
        s = pd.to_datetime(s, errors="coerce")
        return df[(s >= lo) & (s <= hi)]
    if op == "contains":
        return df[s.astype(str).str.contains(str(val), na=False)]
    if op == "startswith":
        return df[s.astype(str).str.startswith(str(val), na=False)]
    ops = {"eq": s == val, "ne": s != val, "gt": s > val, "ge": s >= val, "lt": s < val, "le": s <= val}
    if op not in ops:
        raise ValueError(f"未知运算符：{op}")
    return df[ops[op]]


try:
    df = pd.read_excel(FILE, sheet_name=SHEET, engine="openpyxl")
    result = df
    for col, op, val in CONDITIONS:
        result = apply_one(result, col, op, val)

    if SORT_BY:
        if SORT_BY not in result.columns:
            console.print(f"[red]排序列不存在：{SORT_BY}[/red]"); sys.exit(1)
        result = result.sort_values(SORT_BY, ascending=ASC)
    if TOP:
        result = result.head(TOP)

    if result.empty:
        console.print("[yellow]没有满足条件的行，请调整条件[/yellow]"); sys.exit(0)

    cond_slug = "_".join(f"{c}_{o}_{v}" for c, o, v in CONDITIONS)[:80]
    slug = f"{FILE.stem}_filter_{cond_slug}" + (f"_top{TOP}" if TOP else "")
    out = OUT / f"{slug}.csv"
    result.to_csv(out, index=False, encoding="utf-8-sig")

    preview = result.head(10)
    tbl = Table(title=f"筛选结果（共 {len(result)} 行）", show_lines=True)
    for c in preview.columns:
        tbl.add_column(str(c))
    for _, row in preview.iterrows():
        tbl.add_row(*[str(v) for v in row])
    console.print(tbl)
    console.print(f"[green]→ {out}[/green]")
except Exception as e:
    console.print(f"[red]执行出错：{e}[/red]")
    sys.exit(1)
```

### 模板 4：图表（折线 / 柱状 / 散点）

单一模板用 `KIND` 切换。**柱状图自动检测 X 列重复值并 groupby 聚合**（避免画出多条同名 bar）。折线图同理，X 是时间且有重复时按 X 聚合。

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "openpyxl", "matplotlib", "seaborn", "rich"]
# ///
import sys
from pathlib import Path
import matplotlib
matplotlib.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from rich.console import Console

console = Console()
FILE = Path("data/<文件名>.xlsx")     # ← 改这里
SHEET = None
KIND = "bar"                          # line / bar / scatter
X = "合同类型"
Y = ["总金额"]                          # bar/line 可多列；scatter 只用 Y[0]
HUE = None                            # scatter 着色列（可选）
AGG = "sum"                           # 聚合方式（bar/line 自动聚合时使用）
STACKED = False                       # bar 堆叠
TITLE = None                          # None = 自动生成

OUT = Path("output/s_<session_id>"); OUT.mkdir(parents=True, exist_ok=True)

try:
    df = pd.read_excel(FILE, sheet_name=SHEET, engine="openpyxl")
    miss = [c for c in [X, *Y, *([HUE] if HUE else [])] if c not in df.columns]
    if miss:
        console.print(f"[red]列名不存在：{miss}，实际列：{df.columns.tolist()}[/red]"); sys.exit(1)

    title = TITLE or f"{FILE.stem} — {KIND}"

    if KIND == "scatter":
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.scatterplot(data=df, x=X, y=Y[0], hue=HUE, ax=ax, alpha=0.7)
        ax.set_title(title)
    else:
        plot_df = df[[X, *Y]].copy()
        # X 有重复值 → 自动按 X 聚合
        if plot_df[X].duplicated().any():
            plot_df = plot_df.groupby(X)[Y].agg(AGG).reset_index()
            console.print(f"[cyan]X 列 '{X}' 有重复值，已按 {AGG} 自动聚合[/cyan]")
        plot_df = plot_df.set_index(X)

        if KIND == "bar":
            ax = plot_df.plot(kind="bar", stacked=STACKED,
                              figsize=(max(8, len(plot_df) * 0.4 + 2), 5), colormap="tab10")
        elif KIND == "line":
            fig, ax = plt.subplots(figsize=(10, 5))
            for y in Y:
                ax.plot(plot_df.index, plot_df[y], marker="o", markersize=3, label=y)
            if len(Y) > 1: ax.legend()
        else:
            console.print(f"[red]未知 KIND：{KIND}[/red]"); sys.exit(1)

        ax.set_title(title); ax.set_xlabel(X); ax.set_ylabel("值")
        plt.xticks(rotation=30, ha="right")

    plt.tight_layout()
    out = OUT / f"{FILE.stem}_{KIND}.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close("all")
    console.print(f"[green]→ {out}[/green]")
except Exception as e:
    console.print(f"[red]执行出错：{e}[/red]")
    sys.exit(1)
```

### 模板 5：相关性矩阵

pearson / spearman / kendall 三选一，输出 CSV + 下三角热力图。

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "openpyxl", "matplotlib", "seaborn", "rich"]
# ///
import sys
from pathlib import Path
import matplotlib
matplotlib.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from rich.console import Console

console = Console()
FILE = Path("data/<文件名>.xlsx")     # ← 改这里
SHEET = None
METHOD = "pearson"                    # pearson / spearman / kendall

OUT = Path("output/s_<session_id>"); OUT.mkdir(parents=True, exist_ok=True)

try:
    df = pd.read_excel(FILE, sheet_name=SHEET, engine="openpyxl")
    num_df = df.select_dtypes(include="number").dropna(how="all", axis=1)
    if num_df.shape[1] < 2:
        console.print("[yellow]数值列不足 2 列，无法计算相关性[/yellow]"); sys.exit(0)

    corr = num_df.corr(method=METHOD).round(4)
    csv_out = OUT / f"{FILE.stem}_correlation_{METHOD}.csv"
    corr.to_csv(csv_out, encoding="utf-8-sig")

    size = max(6, len(corr.columns) * 0.8)
    fig, ax = plt.subplots(figsize=(size, size * 0.85))
    mask = pd.DataFrame(False, index=corr.index, columns=corr.columns)
    for i in range(len(corr)):
        for j in range(i + 1, len(corr.columns)):
            mask.iloc[i, j] = True
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdYlGn",
                vmin=-1, vmax=1, linewidths=0.5, ax=ax, square=True)
    ax.set_title(f"{FILE.stem} — {METHOD} 相关矩阵")
    plt.tight_layout()
    png_out = OUT / f"{FILE.stem}_correlation_{METHOD}.png"
    plt.savefig(png_out, dpi=150, bbox_inches="tight")
    plt.close("all")

    console.print(f"[green]→ {csv_out}[/green]")
    console.print(f"[green]→ {png_out}[/green]")
except Exception as e:
    console.print(f"[red]执行出错：{e}[/red]")
    sys.exit(1)
```

### 模板 6：自由分析

前 5 个模板都不合适时使用。提供最小骨架，按需自由实现。

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "openpyxl", "matplotlib", "rich"]
# ///
import sys
from pathlib import Path
import matplotlib
matplotlib.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import pandas as pd
from rich.console import Console

console = Console()
FILE = Path("data/<文件名>.xlsx")     # ← 改这里
OUT = Path("output/s_<session_id>"); OUT.mkdir(parents=True, exist_ok=True)

try:
    df = pd.read_excel(FILE, engine="openpyxl")

    # === 按需补全分析逻辑 ===
    # 例：复购客户数
    # repeat = df.groupby("客户ID").size()
    # repeat_customers = (repeat >= 2).sum()
    # console.print(f"复购客户数：{repeat_customers}")
    # =====================

    # 输出到 output/
    # result.to_csv(OUT / f"{FILE.stem}_<描述>.csv", index=False, encoding="utf-8-sig")
except Exception as e:
    console.print(f"[red]执行出错：{e}[/red]")
    sys.exit(1)
```

## 错误处理

- **文件不存在** → 提示用户检查 `data/`，停止执行
- **列名不存在** → 把脚本打印的实际列名展示给用户，让用户重选，不要猜测
- **脚本运行失败（非 0 退出）** → 原样展示 stderr，不擅自修复
- **筛选结果为空** → 告知用户并建议调整条件
- **`rm output/s_<session_id>/_tmp.py` 失败** → 忽略，下次会覆盖

## 运行命令

```bash
# 0. 若本 session 还没有 session_id，先执行：
#    export SID=$(uv run python -c "import secrets; print(secrets.token_hex(3))")
#    mkdir -p output/s_$SID/
#    后续所有路径用 output/s_$SID/ 替代 output/s_<session_id>/
# 1. 用 Write 工具把模板写入 output/s_<session_id>/_tmp.py（修改参数 + 把模板里的 <session_id> 占位符也替换掉）
# 2. 运行 + 立即删除：
uv run python -X utf8 output/s_<session_id>/_tmp.py && rm output/s_<session_id>/_tmp.py
```

Windows bash 不支持 heredoc，**统一走 `output/s_<session_id>/_tmp.py` 路径**。
