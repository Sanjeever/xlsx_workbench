"""
bar_chart.py — 柱状图（分类对比）

用法：
    uv run python -X utf8 .claude/skills/chart-xlsx/bar_chart.py data/<文件>.xlsx --x 部门 --y 销售额
    uv run python -X utf8 .claude/skills/chart-xlsx/bar_chart.py data/<文件>.xlsx --x 部门 --y 销售额 利润 --stacked

输出：
    output/<文件名>_<sheet>_bar.png
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent.parent / "explore-xlsx"))
from _utils import console, load_sheets, output_path, print_outputs


def plot_bar(
    path: Path,
    x_col: str,
    y_cols: list[str],
    sheet_name: str | None,
    stacked: bool,
    title: str | None,
) -> list[Path]:
    sheets = load_sheets(path, sheet_name)
    sname, df = next(iter(sheets.items()))

    missing = [c for c in [x_col, *y_cols] if c not in df.columns]
    if missing:
        console.print(f"[red]列名不存在：{missing}，实际列名：{df.columns.tolist()}[/red]")
        sys.exit(1)

    plot_df = df.set_index(x_col)[y_cols]
    ax = plot_df.plot(
        kind="bar",
        stacked=stacked,
        figsize=(max(8, len(df) * 0.4 + 2), 5),
        colormap="tab10",
    )
    ax.set_title(title or f"{path.stem} — {sname} 柱状图")
    ax.set_xlabel(x_col)
    ax.set_ylabel("值")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    out = output_path(f"{path.stem}_{sname}", "_bar.png")
    ax.get_figure().savefig(out, dpi=150, bbox_inches="tight")
    plt.close("all")
    return [out]


def main() -> None:
    parser = argparse.ArgumentParser(description="柱状图")
    parser.add_argument("file", type=Path)
    parser.add_argument("--x", required=True, help="类别轴列名")
    parser.add_argument("--y", nargs="+", required=True, help="数值列名（可多列）")
    parser.add_argument("--sheet", default=None)
    parser.add_argument("--stacked", action="store_true", help="堆叠柱状图")
    parser.add_argument("--title", default=None)
    args = parser.parse_args()

    outputs = plot_bar(args.file, args.x, args.y, args.sheet, args.stacked, args.title)
    print_outputs(outputs)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"[red]执行出错：{e}[/red]")
        sys.exit(1)
