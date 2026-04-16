"""
rank_export.py — 排序 / TopN 导出 CSV

用法：
    uv run python -X utf8 .claude/skills/export-xlsx/rank_export.py data/<文件>.xlsx --by 销售额
    uv run python -X utf8 .claude/skills/export-xlsx/rank_export.py data/<文件>.xlsx --by 利润 --top 20 --asc

输出：
    output/<文件名>_<sheet>_rank_<by>[_top<N>].csv
"""

import argparse
import sys
from pathlib import Path

from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent / "explore-xlsx"))
from _utils import console, load_sheets, output_path, print_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="排序 / TopN 导出 CSV")
    parser.add_argument("file", type=Path)
    parser.add_argument("--by", required=True, help="排序列名")
    parser.add_argument("--top", type=int, default=None, help="只保留前 N 行（默认全部）")
    parser.add_argument("--asc", action="store_true", help="升序（默认降序）")
    parser.add_argument("--sheet", default=None)
    args = parser.parse_args()

    sheets = load_sheets(args.file, args.sheet)
    sname, df = next(iter(sheets.items()))

    if args.by not in df.columns:
        console.print(f"[red]列名不存在：{args.by}，实际列名：{df.columns.tolist()}[/red]")
        sys.exit(1)

    result = df.sort_values(args.by, ascending=args.asc)
    if args.top:
        result = result.head(args.top)

    top_suffix = f"_top{args.top}" if args.top else ""
    slug = f"{args.file.stem}_{sname}_rank_{args.by}{top_suffix}"
    out = output_path(slug, ".csv")
    result.to_csv(out, index=False, encoding="utf-8-sig")

    # 终端预览
    preview = result.head(10)
    direction = "升序" if args.asc else "降序"
    table = Table(
        title=f"排序结果（按 {args.by} {direction}，共 {len(result)} 行，显示前 {len(preview)} 行）",
        show_lines=True,
    )
    for col in preview.columns:
        table.add_column(str(col), style="cyan" if col == args.by else "white")
    for _, row in preview.iterrows():
        table.add_row(*[str(v) for v in row])
    console.print(table)

    print_outputs([out])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"[red]执行出错：{e}[/red]")
        sys.exit(1)
