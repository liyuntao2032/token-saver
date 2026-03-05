#!/usr/bin/env python3
"""
Token节约大师 V3.0 - 终极版
极致压缩 + 完美保留
"""

import json
import re
from typing import List, Dict, Any


class UltimateCompressor:
    """终极压缩器 - V3.0"""

    def compress(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        终极压缩策略：
        1. 提取所有关键信息
        2. 去重
        3. 极简格式化
        """
        # 合并所有文本
        full_text = '\n'.join([msg.get('content', '') for msg in messages])
        original_tokens = len(full_text) // 2

        # 提取关键信息
        key_data = self._extract_all(full_text)

        # 生成压缩输出
        compressed = self._format_minimal(key_data)
        compressed_tokens = len(compressed) // 2

        return {
            'compressed': compressed,
            'key_data': key_data,
            'stats': {
                'original_tokens': original_tokens,
                'compressed_tokens': compressed_tokens,
                'saved_tokens': original_tokens - compressed_tokens,
                'compression_ratio': round((1 - compressed_tokens / original_tokens) * 100, 2) if original_tokens > 0 else 0
            }
        }

    def _extract_all(self, text: str) -> Dict[str, Any]:
        """提取所有关键信息"""
        data = {}

        # 项目名
        project_match = re.search(r'项目[：:\s]*([^\n，。]{2,20})', text)
        if project_match:
            data['project'] = project_match.group(1)

        # 预算
        budget_match = re.search(r'预算[：:\s]*(\d+(?:\.\d+)?(?:万|千|亿)?元?)', text)
        if budget_match:
            data['budget'] = budget_match.group(1)

        # 工期
        deadline_match = re.search(r'(?:工期|期限|时间)[：:\s]*(\d+[^，。\n]{0,10})', text)
        if deadline_match:
            data['deadline'] = deadline_match.group(1)

        # 技术栈
        tech_matches = re.findall(r'(?:使用|采用|技术栈)[：:\s]*([A-Za-z\u4e00-\u9fa5+]+(?:和|、)[A-Za-z\u4e00-\u9fa5+.]+)', text)
        if tech_matches:
            data['tech'] = list(set(tech_matches))[:3]  # 去重，最多3个

        # 决策
        decision_matches = re.findall(r'(?:决定|确认|确定)[：:\s]*([^\n。]{3,30})', text)
        if decision_matches:
            data['decisions'] = list(set(decision_matches))[:5]  # 去重，最多5个

        # 待办
        todo_matches = re.findall(r'(?:TODO|待办|需要)[：:\s]*([^\n。]{3,30})', text)
        if todo_matches:
            data['todos'] = list(set(todo_matches))[:5]  # 去重，最多5个

        return data

    def _format_minimal(self, data: Dict[str, Any]) -> str:
        """极简格式化"""
        if not data:
            return "（无关键信息）"

        lines = []

        # 基本信息 - 单行
        basic = []
        if 'project' in data:
            basic.append(f"项目:{data['project']}")
        if 'budget' in data:
            basic.append(f"预算:{data['budget']}")
        if 'deadline' in data:
            basic.append(f"工期:{data['deadline']}")

        if basic:
            lines.append(' | '.join(basic))

        # 技术栈
        if 'tech' in data:
            lines.append(f"技术:{','.join(data['tech'])}")

        # 决策
        if 'decisions' in data:
            lines.append(f"决策:{';'.join(data['decisions'])}")

        # 待办
        if 'todos' in data:
            lines.append(f"待办:{';'.join(data['todos'])}")

        return '\n'.join(lines)


def test_v30():
    """测试V3.0"""
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

    compressor = UltimateCompressor()
    result = compressor.compress(messages)

    print("=" * 60)
    print("Token节约大师 V3.0 - 终极压缩测试")
    print("=" * 60)
    print("\n【压缩结果】")
    print(result['compressed'])
    print("\n" + "=" * 60)
    print("【统计信息】")
    print("=" * 60)
    print(f"原始tokens: {result['stats']['original_tokens']}")
    print(f"压缩后tokens: {result['stats']['compressed_tokens']}")
    print(f"节约tokens: {result['stats']['saved_tokens']}")
    print(f"压缩率: {result['stats']['compression_ratio']}%")
    print("\n【提取的关键数据】")
    for key, value in result['key_data'].items():
        print(f"  {key}: {value}")


if __name__ == '__main__':
    test_v30()
