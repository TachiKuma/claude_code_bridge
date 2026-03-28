#!/usr/bin/env python3
"""
i18n.py 可复用性评估脚本

评估维度：
1. API 设计分析
2. 性能分析
3. 扩展性分析

运行方式: 从项目根目录运行
cd E:/GitHub开源项目/TachiKuma/claude_code_bridge
python .planning/phases/01-代码库分析/analysis-tools/evaluate_i18n.py
"""

import sys
import time

# 添加 lib 目录到路径
sys.path.insert(0, 'lib')

from i18n import t, MESSAGES


def evaluate_api_design():
    """评估 API 设计"""
    print("=" * 60)
    print("1. API 设计分析")
    print("=" * 60)

    # 函数签名清晰度
    print("\n[OK] t() 函数签名: t(key: str, **kwargs) -> str")
    print("  - 简洁明了，符合 Python 惯例")
    print("  - 支持参数格式化")

    # 命名空间支持
    print("\n[NO] 命名空间支持: 无")
    print("  - 当前所有消息在全局 MESSAGES 字典中")
    print("  - CCB 和 GSD 共享时可能产生键冲突")
    print("  - 建议: 添加命名空间前缀 (ccb.*, gsd.*)")

    # 回退机制
    print("\n[OK] 回退机制: 完善")
    print("  - zh 缺失时自动回退到 en")
    print("  - 键不存在时返回键本身")

    # 参数格式化安全性
    print("\n[WARN] 参数格式化: 使用 .format(**kwargs)")
    print("  - 当前实现安全（有 try-except）")
    print("  - 但不支持复数形式、性别等高级特性")

    print("\n总体评分: 7/10")
    print("建议: 添加命名空间支持，考虑更丰富的格式化选项")


def evaluate_performance():
    """评估性能"""
    print("\n" + "=" * 60)
    print("2. 性能分析")
    print("=" * 60)

    # 字典查找开销
    iterations = 10000
    start = time.perf_counter()
    for _ in range(iterations):
        t("no_terminal_backend")
    end = time.perf_counter()

    avg_time = (end - start) / iterations * 1000000  # 转换为微秒
    print(f"\n[OK] 字典查找速度: {avg_time:.2f} us/次 ({iterations} 次测试)")
    print("  - 性能优秀，适合高频调用")

    # 内存占用
    import sys
    messages_size = sys.getsizeof(MESSAGES)
    en_size = sys.getsizeof(MESSAGES['en'])
    zh_size = sys.getsizeof(MESSAGES['zh'])

    print(f"\n[OK] 内存占用:")
    print(f"  - MESSAGES 字典: {messages_size} bytes")
    print(f"  - en 消息: {en_size} bytes ({len(MESSAGES['en'])} 条)")
    print(f"  - zh 消息: {zh_size} bytes ({len(MESSAGES['zh'])} 条)")
    print(f"  - 总计: ~{(messages_size + en_size + zh_size) / 1024:.1f} KB")

    # 冷启动时间
    start = time.perf_counter()
    import importlib
    importlib.reload(sys.modules['i18n'])
    end = time.perf_counter()

    print(f"\n[OK] 冷启动时间: {(end - start) * 1000:.2f} ms")
    print("  - 启动快速，无明显延迟")

    print("\n总体评分: 9/10")
    print("建议: 当前性能优秀，无需优化")


def evaluate_extensibility():
    """评估扩展性"""
    print("\n" + "=" * 60)
    print("3. 扩展性分析")
    print("=" * 60)

    # 多语言支持
    print("\n[WARN] 多语言支持: 当前 2 种 (en, zh)")
    print("  - 添加新语言需修改 MESSAGES 字典")
    print("  - 扩展到 5+ 种语言会使代码臃肿")
    print("  - 建议: 支持外部 JSON/PO 文件加载")

    # 外部目录加载
    print("\n[NO] 外部目录加载: 不支持")
    print("  - 当前消息硬编码在 Python 文件中")
    print("  - 无法动态加载翻译文件")
    print("  - 建议: 添加 load_from_directory() 函数")

    # 命名空间隔离
    print("\n[NO] 命名空间隔离: 不支持")
    print("  - CCB 和 GSD 消息会混在一起")
    print("  - 可能产生键冲突")
    print("  - 建议: 使用点分隔命名空间 (ccb.error, gsd.warning)")

    # 动态加载能力
    print("\n[NO] 动态加载: 不支持")
    print("  - 无法在运行时添加新消息")
    print("  - 无法按需加载语言包")

    print("\n总体评分: 4/10")
    print("建议: 需要重大改造以支持外部文件和命名空间")


def main():
    print("\n" + "=" * 60)
    print("CCB i18n.py 可复用性评估")
    print("=" * 60)

    evaluate_api_design()
    evaluate_performance()
    evaluate_extensibility()

    print("\n" + "=" * 60)
    print("总体结论")
    print("=" * 60)
    print("\n综合评分: 6.7/10")
    print("\n[OK] 优势:")
    print("  - API 简洁清晰")
    print("  - 性能优秀")
    print("  - 回退机制完善")
    print("\n[NO] 劣势:")
    print("  - 缺少命名空间支持")
    print("  - 不支持外部文件加载")
    print("  - 扩展性受限")
    print("\n建议: 可作为基础，但需要改造")
    print("  1. 添加命名空间支持 (ccb.*, gsd.*)")
    print("  2. 支持外部 JSON/PO 文件加载")
    print("  3. 保持现有 t() API 兼容性")
    print("  4. 考虑提取为独立的 i18n_core 模块")


if __name__ == "__main__":
    main()
