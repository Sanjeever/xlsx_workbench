"""
inspect_xlsx.py — xlsx 文件结构探查

用法：
    uv run python -X utf8 .claude/skills/explore-xlsx/inspect_xlsx.py data/your_file.xlsx
    uv run python -X utf8 .claude/skills/explore-xlsx/inspect_xlsx.py data/your_file.xlsx --sheet Sheet1

输出：
    output/<文件名>_report.md   —— Markdown 结构报告
"""

import argparse
import sys
from pathlib import Path

from rich.table import Table

from _utils import console, load_sheets, output_path, print_outputs


def inspect_file(path: Path, sheet_name: str | None = None) -> Path:
    stem = path.stem
    report_path = output_path(stem, "_report.md")

    sheets = load_sheets(path, sheet_name)

    lines: list[str] = [f"# 文件结构报告：{path.name}\n"]

    for sname, df in sheets.items():
        lines.append(f"## Sheet: `{sname}`\n")
        lines.append(f"- 行数（含标题除外）：{len(df)}")
        lines.append(f"- 列数：{len(df.columns)}\n")

        # 列详情表
        lines.append("### 列详情\n")
        lines.append("| 列名 | 数据类型 | 非空数量 | 缺失数量 | 缺失率 |")
        lines.append("|------|---------|---------|---------|-------|")
        for col in df.columns:
            non_null = df[col].notna().sum()
            missing = df[col].isna().sum()
            rate = f"{missing / len(df) * 100:.1f}%" if len(df) > 0 else "N/A"
            dtype = str(df[col].dtype)
            lines.append(f"| {col} | {dtype} | {non_null} | {missing} | {rate} |")
        lines.append("")

        # 数值列统计
        num_cols = df.select_dtypes(include="number").columns.tolist()
        if num_cols:
            lines.append("### 数值列描述统计\n")
            desc = df[num_cols].describe().round(4)
            lines.append(desc.to_markdown())
            lines.append("")

        # 类别列高频值
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if cat_cols:
            lines.append("### 类别列前 5 高频值\n")
            for col in cat_cols:
                top = df[col].value_counts().head(5)
                lines.append(f"**{col}**")
                for val, cnt in top.items():
                    lines.append(f"- `{val}`：{cnt} 次")
                lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")

    # 终端摘要
    for sname, df in sheets.items():
        table = Table(title=f"Sheet: {sname}", show_lines=True)
        table.add_column("列名", style="cyan")
        table.add_column("类型", style="magenta")
        table.add_column("非空", justify="right")
        table.add_column("缺失率", justify="right")
        for col in df.columns:
            missing = df[col].isna().sum()
            rate = f"{missing / len(df) * 100:.1f}%" if len(df) > 0 else "N/A"
            table.add_row(str(col), str(df[col].dtype), str(df[col].notna().sum()), rate)
        console.print(table)

    print_outputs([report_path])
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="探查 xlsx 文件结构，生成 Markdown 报告")
    parser.add_argument("file", type=Path, help="xlsx 文件路径")
    parser.add_argument("--sheet", default=None, help="指定 sheet 名称，默认读取全部")
    args = parser.parse_args()
    inspect_file(args.file, args.sheet)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"[red]执行出错：{e}[/red]")
        sys.exit(1)
