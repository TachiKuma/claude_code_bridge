#!/usr/bin/env python3
"""CCB Python 代码库字符串扫描器

使用 AST 静态分析提取所有硬编码字符串字面量。
"""

import ast
import json
import sys
from pathlib import Path


class StringExtractor(ast.NodeVisitor):
    """提取 Python 代码中的所有字符串字面量"""

    def __init__(self, filepath):
        self.filepath = filepath
        self.strings = []

    def visit_Constant(self, node):
        """处理 Python 3.8+ 的常量节点（包括字符串）"""
        if isinstance(node.value, str):
            value = node.value
            # 跳过空字符串和单字符字符串
            if len(value) > 1:
                self.strings.append({
                    'file': str(self.filepath),
                    'line': node.lineno,
                    'col': node.col_offset,
                    'value': value
                })
        self.generic_visit(node)


def scan_directory(root_dir):
    """扫描目录下所有 Python 文件"""
    results = []
    root = Path(root_dir)

    for py_file in sorted(root.rglob('*.py')):
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(py_file))
            extractor = StringExtractor(py_file.relative_to(Path.cwd()))
            extractor.visit(tree)
            results.extend(extractor.strings)

        except SyntaxError as e:
            print(f"Warning: Syntax error in {py_file}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Failed to process {py_file}: {e}", file=sys.stderr)

    return results


if __name__ == '__main__':
    # 扫描 lib/ 目录
    lib_dir = Path('lib')

    if not lib_dir.exists():
        print(f"Error: {lib_dir} directory not found", file=sys.stderr)
        sys.exit(1)

    strings = scan_directory(lib_dir)

    # 输出 JSON 格式
    print(json.dumps(strings, ensure_ascii=False, indent=2))

    print(f"# Extracted {len(strings)} strings from CCB codebase", file=sys.stderr)
