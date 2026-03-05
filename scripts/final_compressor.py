#!/usr/bin/env python3
"""
Token节约大师 V3.1 - 真正的终极版
极致去重 + 超激进压缩
"""

import json
import re
from typing import List, Dict, Any, Set


class FinalCompressor:
    """最终压缩器 - V3.1"""

    def compress(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """极致压缩"""
        # 合并所有文本
        full_text = '\n'.join([msg.get('content', '') for msg in messages])
        original_tokens = len(full_text) // 2

        # 提取并去重关键信息
        key_data = self._extract_and_dedupe(full_text)

        # 生成压缩输出
        compressed = self._format_ultra_minimal(key_data)
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

    def _extract_and_dedupe(self, text: str) -> Dict[str, str]:
        """提取并彻底去重"""
        data = {}

        # 预算（只保留数字+单位）
        budget_match = re.search(r'(\d+(?:\.\d+)?(?:万|千|百|亿)?元)', text)
        if budget_match:
            data['budget'] = budget_match.group(1)

        # 工期（只保留数字+时间单位）
        deadline_match = re.search(r'(\d+[^，。\n]{0,5}(?:个月|天|周))', text)
        if deadline_match:
            data['deadline'] = deadline_match.group(1)

        # 技术栈（只保留技术名词，去重）
        techs = set()
        tech_patterns = [
            r'Python',
            r'Vue\.js',
            r'React',
            r'Node\.js',
            r'微服务',
            r'PostgreSQL',
            r'MySQL',
            r'Docker'
        ]
        for pattern in tech_patterns:
            if re.search(pattern, text):
                techs.add(pattern.replace('\\', ''))

        if techs:
            data['tech'] = '+'.join(sorted(techs))

        # 决策（只保留核心动词+对象）
        decision_match = re.search(r'(?:决定|确认)[：:\s]*([^\n，。]{3,20})', text)
        if decision_match:
            decision = decision_match.group(1).strip()
            # 进一步简化
            decision = re.sub(r'^(采用|使用|选择)\s*', '', decision)
            data['decision'] = decision

        # 待办（只保留动词+对象）
        todos = set()
        todo_matches = re.findall(r'(?:TODO|待办)[：:\s]*([^\n。]{3,20})', text)
        for todo in todo_matches:
            # 简化
            todo = re.sub(r'^(需要|要)\s*', '', todo)
            todo = re.sub(r'^(完成|实现)\s*', '', todo)
            todos.add(todo)

        if todos:
            data['todos'] = ';'.join(sorted(todos))

        return data

    def _format_ultra_minimal(self, data: Dict[str, str]) -> str:
        """超极简格式化 - 字段级别"""
        if not data:
            return "（无）"

        # 所有信息压缩到最少字符
        parts = []

        if 'budget' in data:
            parts.append(f"预算:{data['budget']}")
        if 'deadline' in data:
            parts.append(f"工期:{data['deadline']}")
        if 'tech' in data:
            parts.append(f"技术:{data['tech']}")
        if 'decision' in data:
            parts.append(f"决策:{data['decision']}")
        if 'todos' in data:
            parts.append(f"待办:{data['todos']}")

        return ' | '.join(parts)


def test_v31():
    """测试V3.1"""
    print("=" * 60)
    print("Token节约大师 V3.1 - 终极压缩对比测试")
    print("=" * 60)

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

    compressor = FinalCompressor()
    result = compressor.compress(messages)

    print("\n【原始对话】")
    print("-" * 60)
    for i, msg in enumerate(messages, 1):
        role = "用户" if msg['role'] == 'user' else "AI"
        print(f"{i}. {role}: {msg['content']}")

    print("\n【压缩结果】")
    print("-" * 60)
    print(result['compressed'])

    print("\n【性能对比】")
    print("=" * 60)
    print(f"原始tokens:     {result['stats']['original_tokens']}")
    print(f"压缩后tokens:   {result['stats']['compressed_tokens']}")
    print(f"节约tokens:     {result['stats']['saved_tokens']}")
    print(f"压缩率:         {result['stats']['compression_ratio']}%")
    print(f"\n提取的关键数据:")
    for key, value in result['key_data'].items():
        print(f"  {key}: {value}")


if __name__ == '__main__':
    test_v31()
