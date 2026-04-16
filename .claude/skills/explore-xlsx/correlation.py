"""
correlation.py — 数值列相关矩阵 + 热力图

用法：
    uv run python -X utf8 .claude/skills/explore-xlsx/correlation.py data/your_file.xlsx
    uv run python -X utf8 .claude/skills/explore-xlsx/correlation.py data/your_file.xlsx --sheet Sheet1 --method spearman

输出：
    output/<文件名>_<sheet>_correlation.csv  —— 相关矩阵
    output/<文件名>_<sheet>_correlation.png  —— 热力图
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from _utils import console, load_sheets, output_path, print_outputs

METHODS = ("pearson", "spearman", "kendall")


def correlate_sheet(
    df: pd.DataFrame, stem: str, sname: str, method: str
) -> list[Path]:
    slug = f"{stem}_{sname}"
    outputs: list[Path] = []

    num_df = df.select_dtypes(include="number").dropna(how="all", axis=1)
    if num_df.shape[1] < 2:
        console.print(f"[yellow]Sheet '{sname}' 数值列不足 2 列，无法计算相关性，跳过。[/yellow]")
        return outputs

    corr = num_df.corr(method=method).round(4)

    # CSV
    csv_path = output_path(slug, "_correlation.csv")
    corr.to_csv(csv_path, encoding="utf-8-sig")
    outputs.append(csv_path)

    # 热力图
    size = max(6, len(corr.columns) * 0.8)
    fig, ax = plt.subplots(figsize=(size, size * 0.85))
    mask = pd.DataFrame(False, index=corr.index, columns=corr.columns)
    # 只显示下三角
    for i in range(len(corr)):
        for j in range(i + 1, len(corr.columns)):
            mask.iloc[i, j] = True

    sns.heatmap(
        corr,
        mask=mask,
        annot=True,
        fmt=".2f",
        cmap="RdYlGn",
        vmin=-1,
        vmax=1,
        linewidths=0.5,
        ax=ax,
        square=True,
    )
    ax.set_title(f"{stem} — {sname}  {method} 相关矩阵", fontsize=12)
    plt.tight_layout()
    png_path = output_path(slug, "_correlation.png")
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    outputs.append(png_path)

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="数值列相关矩阵 + 热力图")
    parser.add_argument("file", type=Path, help="xlsx 文件路径")
    parser.add_argument("--sheet", default=None, help="指定 sheet 名称，默认全部")
    parser.add_argument(
        "--method",
        default="pearson",
        choices=METHODS,
        help="相关系数方法（默认 pearson）",
    )
    args = parser.parse_args()

    sheets = load_sheets(args.file, args.sheet)

    all_outputs: list[Path] = []
    for sname, df in sheets.items():
        outputs = correlate_sheet(df, args.file.stem, sname, args.method)
        all_outputs.extend(outputs)

    print_outputs(all_outputs)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"[red]执行出错：{e}[/red]")
        sys.exit(1)
