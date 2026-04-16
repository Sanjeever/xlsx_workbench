"""
summary_stats.py — 数值列描述统计 + 分布直方图

用法：
    uv run python -X utf8 .claude/skills/explore-xlsx/summary_stats.py data/your_file.xlsx
    uv run python -X utf8 .claude/skills/explore-xlsx/summary_stats.py data/your_file.xlsx --sheet Sheet1 --cols 销售额 利润

输出：
    output/<文件名>_<sheet>_stats.csv      —— 描述统计表
    output/<文件名>_<sheet>_distribution.png —— 分布直方图
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from _utils import console, load_sheets, output_path, print_outputs


def analyze_sheet(df: pd.DataFrame, stem: str, sname: str, cols: list[str] | None) -> list[Path]:
    slug = f"{stem}_{sname}"
    outputs: list[Path] = []

    num_df = df.select_dtypes(include="number")
    if cols:
        missing = [c for c in cols if c not in num_df.columns]
        if missing:
            console.print(f"[yellow]以下列不是数值列或不存在，已跳过：{missing}[/yellow]")
        num_df = num_df[[c for c in cols if c in num_df.columns]]

    if num_df.empty:
        console.print(f"[yellow]Sheet '{sname}' 中没有可分析的数值列，跳过。[/yellow]")
        return outputs

    # CSV 统计表
    stats = num_df.describe().T
    stats["median"] = num_df.median()
    stats["skew"] = num_df.skew()
    stats["kurt"] = num_df.kurt()
    csv_path = output_path(slug, "_stats.csv")
    stats.to_csv(csv_path, encoding="utf-8-sig")
    outputs.append(csv_path)

    # 分布直方图
    n_cols = min(len(num_df.columns), 4)
    n_rows = (len(num_df.columns) + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
    axes_flat = [axes] if len(num_df.columns) == 1 else (
        axes.flatten() if hasattr(axes, "flatten") else [axes]
    )

    for i, col in enumerate(num_df.columns):
        ax = axes_flat[i]
        sns.histplot(num_df[col].dropna(), kde=True, ax=ax, color="steelblue")
        ax.set_title(col, fontsize=10)
        ax.set_xlabel("")

    for j in range(len(num_df.columns), len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.suptitle(f"{stem} — {sname} 数值分布", fontsize=13, y=1.01)
    plt.tight_layout()
    png_path = output_path(slug, "_distribution.png")
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    outputs.append(png_path)

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="数值列描述统计 + 分布直方图")
    parser.add_argument("file", type=Path, help="xlsx 文件路径")
    parser.add_argument("--sheet", default=None, help="指定 sheet 名称，默认全部")
    parser.add_argument("--cols", nargs="+", default=None, help="指定分析的列名（空格分隔）")
    args = parser.parse_args()

    sheets = load_sheets(args.file, args.sheet)

    all_outputs: list[Path] = []
    for sname, df in sheets.items():
        outputs = analyze_sheet(df, args.file.stem, sname, args.cols)
        all_outputs.extend(outputs)

    print_outputs(all_outputs)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"[red]执行出错：{e}[/red]")
        sys.exit(1)
