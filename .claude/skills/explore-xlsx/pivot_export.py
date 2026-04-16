"""
pivot_export.py — 按分组列聚合数值列，导出 CSV

用法：
    uv run python -X utf8 .claude/skills/explore-xlsx/pivot_export.py data/your_file.xlsx --by 部门
    uv run python -X utf8 .claude/skills/explore-xlsx/pivot_export.py data/your_file.xlsx --by 部门 季度 --agg mean --cols 销售额 利润
    uv run python -X utf8 .claude/skills/explore-xlsx/pivot_export.py data/your_file.xlsx --sheet Sheet1 --by 类别 --agg sum

输出：
    output/<文件名>_<sheet>_by_<分组列>_<agg>.csv
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from rich.table import Table

from _utils import console, load_sheets, output_path, print_outputs

AGG_FUNCS = ("sum", "mean", "count", "median", "min", "max")


def pivot_sheet(
    df: pd.DataFrame,
    stem: str,
    sname: str,
    by: list[str],
    agg: str,
    cols: list[str] | None,
) -> list[Path]:
    outputs: list[Path] = []

    # 空 sheet 直接跳过
    if df.empty or df.columns.empty:
        console.print(f"[yellow]Sheet '{sname}' 为空，跳过。[/yellow]")
        return outputs

    # 检查分组列存在
    missing_by = [c for c in by if c not in df.columns]
    if missing_by:
        console.print(f"[red]Sheet '{sname}' 中分组列不存在：{missing_by}，跳过。[/red]")
        return outputs

    # 选取数值列
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if cols:
        bad = [c for c in cols if c not in num_cols]
        if bad:
            console.print(f"[yellow]以下列不是数值列或不存在，已跳过：{bad}[/yellow]")
        num_cols = [c for c in cols if c in num_cols]

    if not num_cols:
        console.print(f"[yellow]Sheet '{sname}' 中没有可聚合的数值列，跳过。[/yellow]")
        return outputs

    grouped = df.groupby(by)[num_cols].agg(agg).round(4).reset_index()

    by_slug = "_".join(by)
    slug = f"{stem}_{sname}_by_{by_slug}_{agg}"
    csv_path = output_path(slug, ".csv")
    grouped.to_csv(csv_path, index=False, encoding="utf-8-sig")
    outputs.append(csv_path)

    # 终端预览（最多 10 行）
    preview = grouped.head(10)
    table = Table(title=f"分组聚合预览（{agg}）—— 前 {len(preview)} 行", show_lines=True)
    for col in preview.columns:
        table.add_column(str(col), style="cyan" if col in by else "white")
    for _, row in preview.iterrows():
        table.add_row(*[str(v) for v in row])
    console.print(table)

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="按分组列聚合数值列，导出 CSV")
    parser.add_argument("file", type=Path, help="xlsx 文件路径")
    parser.add_argument("--sheet", default=None, help="指定 sheet 名称，默认全部")
    parser.add_argument("--by", nargs="+", required=True, help="分组列名（可多列，空格分隔）")
    parser.add_argument(
        "--agg",
        default="sum",
        choices=AGG_FUNCS,
        help="聚合方式（默认 sum）",
    )
    parser.add_argument("--cols", nargs="+", default=None, help="要聚合的数值列（默认全部）")
    args = parser.parse_args()

    sheets = load_sheets(args.file, args.sheet)

    all_outputs: list[Path] = []
    for sname, df in sheets.items():
        outputs = pivot_sheet(df, args.file.stem, sname, args.by, args.agg, args.cols)
        all_outputs.extend(outputs)

    print_outputs(all_outputs)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"[red]执行出错：{e}[/red]")
        sys.exit(1)
