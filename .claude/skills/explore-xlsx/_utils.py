"""
_utils.py — explore-xlsx skill 内部共享工具

供同目录脚本 import，不由 agent 直接调用。
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
import pandas as pd
from rich.console import Console

console = Console()

# ── matplotlib 中文字体 ──────────────────────────────────────────────────────
matplotlib.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False


# ── xlsx 读取 ────────────────────────────────────────────────────────────────

def load_sheets(path: Path, sheet_name: str | None = None) -> dict[str, pd.DataFrame]:
    """读取 xlsx，返回 {sheet名: DataFrame} 字典。"""
    if not path.exists():
        console.print(f"[red]文件不存在：{path}[/red]")
        sys.exit(1)
    result = pd.read_excel(path, sheet_name=sheet_name or None, engine="openpyxl")
    if isinstance(result, pd.DataFrame):
        return {sheet_name or "Sheet1": result}
    return result  # type: ignore[return-value]


# ── 输出路径 ─────────────────────────────────────────────────────────────────

def output_path(stem: str, suffix: str) -> Path:
    """生成 output/<stem><suffix>，自动创建 output/ 目录。"""
    out = Path("output")
    out.mkdir(exist_ok=True)
    return out / f"{stem}{suffix}"


# ── 结果汇报 ─────────────────────────────────────────────────────────────────

def print_outputs(paths: list[Path]) -> None:
    """用 rich 打印所有生成的文件路径。"""
    console.print("\n[bold green]已生成文件：[/bold green]")
    for p in paths:
        console.print(f"  {p}")
