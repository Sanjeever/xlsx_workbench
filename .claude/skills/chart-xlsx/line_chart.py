"""
line_chart.py — 折线图（趋势 / 时序）

用法：
    uv run python -X utf8 .claude/skills/chart-xlsx/line_chart.py data/<文件>.xlsx --x 日期 --y 销售额
    uv run python -X utf8 .claude/skills/chart-xlsx/line_chart.py data/<文件>.xlsx --x 日期 --y 销售额 利润 --sheet Sheet1

输出：
    output/<文件名>_<sheet>_line.png
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent.parent / "explore-xlsx"))
from _utils import console, load_sheets, output_path, print_outputs


def plot_line(
    path: Path,
    x_col: str,
    y_cols: list[str],
    sheet_name: str | None,
    title: str | None,
) -> list[Path]:
    sheets = load_sheets(path, sheet_name)
    sname, df = next(iter(sheets.items()))

    missing = [c for c in [x_col, *y_cols] if c not in df.columns]
    if missing:
        console.print(f"[red]列名不存在：{missing}，实际列名：{df.columns.tolist()}[/red]")
        sys.exit(1)

    fig, ax = plt.subplots(figsize=(10, 5))
    for y in y_cols:
        ax.plot(df[x_col], df[y], marker="o", markersize=3, label=y)

    ax.set_xlabel(x_col)
    ax.set_ylabel("值")
    ax.set_title(title or f"{path.stem} — {sname} 折线图")
    if len(y_cols) > 1:
        ax.legend()
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    out = output_path(f"{path.stem}_{sname}", "_line.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return [out]


def main() -> None:
    parser = argparse.ArgumentParser(description="折线图")
    parser.add_argument("file", type=Path)
    parser.add_argument("--x", required=True, help="X 轴列名")
    parser.add_argument("--y", nargs="+", required=True, help="Y 轴列名（可多列）")
    parser.add_argument("--sheet", default=None)
    parser.add_argument("--title", default=None)
    args = parser.parse_args()

    outputs = plot_line(args.file, args.x, args.y, args.sheet, args.title)
    print_outputs(outputs)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"[red]执行出错：{e}[/red]")
        sys.exit(1)
