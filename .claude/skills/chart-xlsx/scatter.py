"""
scatter.py — 散点图（变量关系）

用法：
    uv run python -X utf8 .claude/skills/chart-xlsx/scatter.py data/<文件>.xlsx --x 销售额 --y 利润
    uv run python -X utf8 .claude/skills/chart-xlsx/scatter.py data/<文件>.xlsx --x 销售额 --y 利润 --hue 部门

输出：
    output/<文件名>_<sheet>_scatter.png
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, str(Path(__file__).parent.parent / "explore-xlsx"))
from _utils import console, load_sheets, output_path, print_outputs


def plot_scatter(
    path: Path,
    x_col: str,
    y_col: str,
    hue_col: str | None,
    sheet_name: str | None,
    title: str | None,
) -> list[Path]:
    sheets = load_sheets(path, sheet_name)
    sname, df = next(iter(sheets.items()))

    check_cols = [x_col, y_col] + ([hue_col] if hue_col else [])
    missing = [c for c in check_cols if c not in df.columns]
    if missing:
        console.print(f"[red]列名不存在：{missing}，实际列名：{df.columns.tolist()}[/red]")
        sys.exit(1)

    fig, ax = plt.subplots(figsize=(7, 5))
    sns.scatterplot(data=df, x=x_col, y=y_col, hue=hue_col, ax=ax, alpha=0.7)
    ax.set_title(title or f"{path.stem} — {sname}  {x_col} vs {y_col}")
    plt.tight_layout()

    out = output_path(f"{path.stem}_{sname}", "_scatter.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return [out]


def main() -> None:
    parser = argparse.ArgumentParser(description="散点图")
    parser.add_argument("file", type=Path)
    parser.add_argument("--x", required=True, help="X 轴数值列")
    parser.add_argument("--y", required=True, help="Y 轴数值列")
    parser.add_argument("--hue", default=None, help="分组着色列（可选）")
    parser.add_argument("--sheet", default=None)
    parser.add_argument("--title", default=None)
    args = parser.parse_args()

    outputs = plot_scatter(args.file, args.x, args.y, args.hue, args.sheet, args.title)
    print_outputs(outputs)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"[red]执行出错：{e}[/red]")
        sys.exit(1)
