"""
filter_export.py — 条件筛选行并导出 CSV

用法：
    uv run python -X utf8 .claude/skills/export-xlsx/filter_export.py data/<文件>.xlsx --col 销售额 --op gt --val 1000
    uv run python -X utf8 .claude/skills/export-xlsx/filter_export.py data/<文件>.xlsx --col 部门 --op eq --val 销售部

输出：
    output/<文件名>_<sheet>_filter_<col>_<op>_<val>.csv
"""

import argparse
import sys
from pathlib import Path

from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent / "explore-xlsx"))
from _utils import console, load_sheets, output_path, print_outputs

OPS = ("eq", "ne", "gt", "ge", "lt", "le", "contains", "startswith")


def apply_filter(df, col: str, op: str, val: str):
    s = df[col]
    # 尝试数值转换
    try:
        num = float(val)
        if op == "eq":
            return df[s == num]
        if op == "ne":
            return df[s != num]
        if op == "gt":
            return df[s > num]
        if op == "ge":
            return df[s >= num]
        if op == "lt":
            return df[s < num]
        if op == "le":
            return df[s <= num]
    except ValueError:
        pass

    # 字符串操作
    if op == "eq":
        return df[s.astype(str) == val]
    if op == "ne":
        return df[s.astype(str) != val]
    if op == "contains":
        return df[s.astype(str).str.contains(val, na=False)]
    if op == "startswith":
        return df[s.astype(str).str.startswith(val, na=False)]
    console.print(f"[red]运算符 '{op}' 不支持字符串类型列的 gt/ge/lt/le 操作[/red]")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="条件筛选行并导出 CSV")
    parser.add_argument("file", type=Path)
    parser.add_argument("--col", required=True, help="筛选列名")
    parser.add_argument("--op", required=True, choices=OPS, help="比较运算符")
    parser.add_argument("--val", required=True, help="比较值")
    parser.add_argument("--sheet", default=None)
    args = parser.parse_args()

    sheets = load_sheets(args.file, args.sheet)
    sname, df = next(iter(sheets.items()))

    if args.col not in df.columns:
        console.print(f"[red]列名不存在：{args.col}，实际列名：{df.columns.tolist()}[/red]")
        sys.exit(1)

    result = apply_filter(df, args.col, args.op, args.val)

    if result.empty:
        console.print(f"[yellow]没有满足条件的行（{args.col} {args.op} {args.val}），请调整条件。[/yellow]")
        sys.exit(0)

    slug = f"{args.file.stem}_{sname}_filter_{args.col}_{args.op}_{args.val}"
    out = output_path(slug, ".csv")
    result.to_csv(out, index=False, encoding="utf-8-sig")

    # 终端预览
    preview = result.head(10)
    table = Table(title=f"筛选结果预览（共 {len(result)} 行，显示前 {len(preview)} 行）", show_lines=True)
    for col in preview.columns:
        table.add_column(str(col), style="cyan" if col == args.col else "white")
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
