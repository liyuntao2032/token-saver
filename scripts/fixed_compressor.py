#!/usr/bin/env python3
"""
Token节约大师 V2.1 - 修复版
真正的超激进压缩
"""

import json
import re
from typing import List, Dict, Any


class UltraCompressor:
    """超激进压缩器 - V2.1"""

    def __init__(self):
        # 关键信息提取模式
        self.patterns = {
            'decision': r'(决定|确认|采用|选择|确定)[：:\s]*([^\n。！？]{5,50})',
            'project': r'项目[：:\s]*([^\n，。]{2,30})',
            'budget': r'预算[：:\s]*(\d+(?:\.\d+)?(?:万|千|百|亿)?元?)',
            'deadline': r'(?:工期|期限|时间)[：:\s]*([^\n，。]{2,20})',
            'tech': r'(?:技术栈|使用|采用)[：:\s]*([^\n，。]{3,50})',
            'todo': r'(?:TODO|待办|需要)[：:\s]*([^\n。！？]{5,50})'
        }

    def compress(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        超激进压缩策略：
        1. 只提取关键信息字段
        2. 移除所有冗余表达
        3. 最小化输出格式
        """
        original_tokens = self._estimate_tokens(messages)

        # 合并所有文本
        full_text = '\n'.join([msg.get('content', '') for msg in messages])

        # 提取关键信息
        key_info = self._extract_key_info(full_text)

        # 生成超简洁输出
        compressed = self._generate_minimal_output(key_info)

        compressed_tokens = len(compressed) // 2

        return {
            'compressed': compressed,
            'key_info': key_info,
            'stats': {
                'original_tokens': original_tokens,
                'compressed_tokens': compressed_tokens,
                'saved_tokens': original_tokens - compressed_tokens,
                'compression_ratio': round((1 - compressed_tokens / original_tokens) * 100, 2) if original_tokens > 0 else 0
            }
        }

    def _extract_key_info(self, text: str) -> Dict[str, List[str]]:
        """提取关键信息"""
        info = {}

        for info_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                # 处理元组（有些正则有多个捕获组）
                if isinstance(matches[0], tuple):
                    info[info_type] = [m[1] if len(m) > 1 else m[0] for m in matches[:3]]
                else:
                    info[info_type] = matches[:3]

        return info

    def _generate_minimal_output(self, key_info: Dict[str, List[str]]) -> str:
        """生成最小化输出"""
        if not key_info:
            return "（无关键信息）"

        lines = []

        # 项目信息
        if 'project' in key_info:
            lines.append(f"项目:{key_info['project'][0]}")

        # 预算
        if 'budget' in key_info:
            lines.append(f"预算:{key_info['budget'][0]}")

        # 工期
        if 'deadline' in key_info:
            lines.append(f"工期:{key_info['deadline'][0]}")

        # 技术栈
        if 'tech' in key_info:
            lines.append(f"技术:{key_info['tech'][0]}")

        # 决策
        if 'decision' in key_info:
            lines.append(f"决策:{key_info['decision'][0]}")

        # 待办
        if 'todo' in key_info:
            for i, item in enumerate(key_info['todo'][:3], 1):
                lines.append(f"待办{i}:{item}")

        return '\n'.join(lines)

    def _estimate_tokens(self, messages: List[Dict[str, str]]) -> int:
        """估算token数量"""
        total_chars = sum(len(msg.get('content', '')) for msg in messages)
        return total_chars // 2


def test_v21():
    """测试V2.1"""
    messages = [
        {'role': 'user', 'content': '我想做一个数据分析项目，预算50万元'},
        {'role': 'assistant', 'content': '好的，我了解了。这是一个数据分析项目，预算50万。'},
        {'role': 'user', 'content': '项目需要在3个月内完成，使用Python和Vue.js'},
        {'role': 'assistant', 'content': '明白了，工期3个月，技术栈是Python和Vue.js。'},
        {'role': 'user', 'content': '我们决定采用微服务架构'},
        {'role': 'assistant', 'content': '好的，已确认使用微服务架构。'},
        {'role': 'user', 'content': 'TODO: 完成数据库设计'},
        {'role': 'assistant', 'content': '已记录待办事项：完成数据库设计。'},
    ]

    compressor = UltraCompressor()
    result = compressor.compress(messages)

    print("=" * 60)
    print("Token节约大师 V2.1 - 超激进压缩测试")
    print("=" * 60)
    print("\n压缩结果：")
    print(result['compressed'])
    print("\n" + "=" * 60)
    print("统计信息：")
    print("=" * 60)
    print(f"原始tokens: {result['stats']['original_tokens']}")
    print(f"压缩后tokens: {result['stats']['compressed_tokens']}")
    print(f"节约tokens: {result['stats']['saved_tokens']}")
    print(f"压缩率: {result['stats']['compression_ratio']}%")
    print("\n提取的关键信息：")
    for key, values in result['key_info'].items():
        print(f"  {key}: {values}")


if __name__ == '__main__':
    test_v21()
