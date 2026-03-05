#!/usr/bin/env python3
"""
Token节约大师 V2.1 - 优化版
更激进的压缩策略，确保高压缩率
"""

import json
import re
from typing import List, Dict, Any, Tuple
from collections import defaultdict


class OptimizedContextCompressor:
    """优化版对话压缩器 - V2.1"""

    def __init__(self):
        # 关键词分类
        self.decision_keywords = ['决定', '决策', '确认', '采用', '选择', '确定', '确认']
        self.task_keywords = ['TODO', '待办', '需要', '要', '必须', '完成']
        self.important_keywords = ['重要', '关键', '注意', '记住']

        # 冗余词汇（用于移除）
        self.redundant_words = [
            '好的', '嗯', '那个', '这个', '就是', '然后', '所以',
            '明白了', '了解了', '我了解了', '我明白了', '好的，',
            '已记录', '已确认', '，已确认', '，已记录'
        ]

    def compress_optimized(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        优化版压缩算法

        核心策略：
        1. 提取关键信息
        2. 移除所有冗余
        3. 结构化压缩
        4. 智能合并
        """
        original_tokens = self._estimate_tokens(messages)

        # Step 1: 提取核心信息
        core_info = self._extract_core_info(messages)

        # Step 2: 生成超压缩摘要
        compressed = self._generate_ultra_compressed(core_info)

        compressed_tokens = self._estimate_tokens([{'content': compressed}])

        return {
            'compressed': compressed,
            'core_info': core_info,
            'stats': {
                'original_tokens': original_tokens,
                'compressed_tokens': compressed_tokens,
                'saved_tokens': original_tokens - compressed_tokens,
                'compression_ratio': round((1 - compressed_tokens / original_tokens) * 100, 2) if original_tokens > 0 else 0
            }
        }

    def _extract_core_info(self, messages: List[Dict[str, str]]) -> Dict[str, List[str]]:
        """提取核心信息"""
        core = {
            'decisions': [],
            'tasks': [],
            'facts': [],
            'important': []
        }

        for msg in messages:
            content = msg.get('content', '')

            # 清理冗余
            cleaned = self._clean_redundancy(content)

            if not cleaned or len(cleaned) < 5:
                continue

            # 分类提取
            if any(kw in cleaned for kw in self.decision_keywords):
                core['decisions'].append(cleaned)
            elif any(kw in cleaned for kw in self.task_keywords):
                core['tasks'].append(cleaned)
            elif any(kw in cleaned for kw in self.important_keywords):
                core['important'].append(cleaned)
            elif self._contains_facts(cleaned):
                core['facts'].append(cleaned)

        # 去重
        for key in core:
            core[key] = list(set(core[key]))[:5]  # 每类最多5条

        return core

    def _clean_redundancy(self, text: str) -> str:
        """清理冗余内容"""
        # 移除冗余词汇
        for word in self.redundant_words:
            text = text.replace(word, '')

        # 移除重复空格
        text = re.sub(r'\s+', ' ', text).strip()

        # 移除标点符号重复
        text = re.sub(r'([，。！？])\1+', r'\1', text)

        return text

    def _contains_facts(self, text: str) -> bool:
        """判断是否包含事实信息"""
        # 包含数字
        if re.search(r'\d+', text):
            return True
        # 包含时间
        if re.search(r'\d{4}|\d{1,2}月|\d{1,2}日', text):
            return True
        # 包含技术名词
        if any(tech in text for tech in ['Python', 'Vue', 'JavaScript', 'SQL', 'API']):
            return True

        return False

    def _generate_ultra_compressed(self, core_info: Dict[str, List[str]]) -> str:
        """生成超压缩摘要"""
        parts = []

        # 决策（最重要）
        if core_info['decisions']:
            parts.append("## 决策")
            for d in core_info['decisions'][:3]:
                # 进一步压缩
                compressed = self._compress_line(d)
                parts.append(f"- {compressed}")

        # 任务
        if core_info['tasks']:
            parts.append("\n## 待办")
            for t in core_info['tasks'][:3]:
                compressed = self._compress_line(t)
                parts.append(f"- {compressed}")

        # 事实
        if core_info['facts']:
            parts.append("\n## 数据")
            for f in core_info['facts'][:3]:
                compressed = self._compress_line(f)
                parts.append(f"- {compressed}")

        if not parts:
            return "（无关键信息）"

        return '\n'.join(parts)

    def _compress_line(self, text: str, max_len: int = 50) -> str:
        """压缩单行文本"""
        # 移除常见的冗余表达
        text = re.sub(r'(我想|我们|项目|平台|系统)', '', text)
        text = re.sub(r'(需要|要|必须)', ':', text)

        # 限制长度
        if len(text) > max_len:
            # 尝试在标点处截断
            match = re.search(r'^.{0,' + str(max_len) + r'}[，。！？]', text)
            if match:
                text = match.group(0)
            else:
                text = text[:max_len]

        return text.strip()

    def _estimate_tokens(self, messages: List[Dict[str, str]]) -> int:
        """估算token数量"""
        total_chars = 0
        for msg in messages:
            total_chars += len(msg.get('content', ''))
        return int(total_chars / 2)


def main():
    """测试V2.1优化版"""
    # 测试数据
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

    compressor = OptimizedContextCompressor()
    result = compressor.compress_optimized(messages)

    print("=" * 60)
    print("Token节约大师 V2.1 - 优化版测试")
    print("=" * 60)
    print("\n压缩结果：\n")
    print(result['compressed'])
    print("\n" + "=" * 60)
    print("统计信息：")
    print("=" * 60)
    print(f"原始tokens: {result['stats']['original_tokens']}")
    print(f"压缩后tokens: {result['stats']['compressed_tokens']}")
    print(f"节约tokens: {result['stats']['saved_tokens']}")
    print(f"压缩率: {result['stats']['compression_ratio']}%")


if __name__ == '__main__':
    main()
