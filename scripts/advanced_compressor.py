#!/usr/bin/env python3
"""
Token节约大师 V2.0 - 增强版
基于学术研究的先进压缩算法
"""

import json
import re
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from datetime import datetime


class AdvancedContextCompressor:
    """高级对话压缩器 - V2.0"""

    def __init__(self):
        # 实体追踪
        self.entities = {
            'people': set(),
            'projects': set(),
            'dates': set(),
            'numbers': set(),
            'locations': set()
        }

        # 重要性权重
        self.importance_weights = {
            'decision_keywords': 10,  # 决策关键词
            'entity_count': 2,        # 实体数量
            'recency': 5,             # 新近度
            'task_keywords': 7,       # 任务关键词
            'question': 3             # 是否包含问题
        }

        # 关键词分类
        self.decision_keywords = ['决定', '决策', '确认', '采用', '选择', '确定']
        self.task_keywords = ['TODO', '待办', '需要', '要', '必须', '完成']
        self.question_keywords = ['？', '?', '吗', '如何', '怎么', '为什么']

    def compress_advanced(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        高级压缩算法

        策略：
        1. 实体提取和追踪
        2. 重要性评分
        3. 递归摘要
        4. 语义去重
        5. 结构化输出
        """
        original_tokens = self._estimate_tokens(messages)

        # Step 1: 提取实体
        self._extract_entities(messages)

        # Step 2: 评分和分类
        scored_messages = self._score_and_classify(messages)

        # Step 3: 递归摘要
        summary = self._recursive_summarize(scored_messages)

        # Step 4: 语义去重
        deduplicated = self._semantic_deduplicate(summary)

        # Step 5: 结构化输出
        compressed = self._structure_output(deduplicated)

        compressed_tokens = self._estimate_tokens([{'content': compressed}])

        return {
            'compressed': compressed,
            'entities': {k: list(v) for k, v in self.entities.items()},
            'stats': {
                'original_tokens': original_tokens,
                'compressed_tokens': compressed_tokens,
                'saved_tokens': original_tokens - compressed_tokens,
                'compression_ratio': round((1 - compressed_tokens / original_tokens) * 100, 2) if original_tokens > 0 else 0,
                'entities_tracked': sum(len(v) for v in self.entities.values())
            }
        }

    def _extract_entities(self, messages: List[Dict[str, str]]) -> None:
        """提取并追踪实体"""
        for msg in messages:
            content = msg.get('content', '')

            # 提取人名（简单规则）
            people = re.findall(r'[\u4e00-\u9fa5]{2,3}(?:说|认为|决定|建议)', content)
            self.entities['people'].update(people)

            # 提取项目名
            projects = re.findall(r'(?:项目|平台|系统)[：:]\s*([^\s，。]+)', content)
            self.entities['projects'].update(projects)

            # 提取日期
            dates = re.findall(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日号]?', content)
            self.entities['dates'].update(dates)

            # 提取数字（金额、数量等）
            numbers = re.findall(r'\d+(?:\.\d+)?(?:万|千|百|亿)?(?:元|美元|人|次)', content)
            self.entities['numbers'].update(numbers)

    def _score_and_classify(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """评分和分类消息"""
        scored = []

        for i, msg in enumerate(messages):
            content = msg.get('content', '')
            score = 0
            category = 'general'

            # 计算重要性分数
            # 1. 决策关键词
            if any(kw in content for kw in self.decision_keywords):
                score += self.importance_weights['decision_keywords']
                category = 'decision'

            # 2. 实体数量
            entity_count = sum(
                1 for entity_set in self.entities.values()
                for entity in entity_set
                if entity in content
            )
            score += entity_count * self.importance_weights['entity_count']

            # 3. 新近度（越新越重要）
            recency_score = (i / len(messages)) * self.importance_weights['recency']
            score += recency_score

            # 4. 任务关键词
            if any(kw in content for kw in self.task_keywords):
                score += self.importance_weights['task_keywords']
                category = 'task'

            # 5. 是否包含问题
            if any(kw in content for kw in self.question_keywords):
                score += self.importance_weights['question']
                category = 'question'

            scored.append({
                'content': content,
                'score': score,
                'category': category,
                'index': i
            })

        # 按分数排序
        scored.sort(key=lambda x: x['score'], reverse=True)

        return scored

    def _recursive_summarize(self, scored_messages: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """递归摘要 - 分层压缩"""
        summary = {
            'tier1_critical': [],    # 最重要：决策、关键数据
            'tier2_important': [],   # 重要：任务、实体变化
            'tier3_supporting': []   # 支撑：问题、一般信息
        }

        for msg in scored_messages:
            content = msg['content']
            category = msg['category']
            score = msg['score']

            # 分层存储
            if category == 'decision' or score > 15:
                summary['tier1_critical'].append(self._compress_sentence(content))
            elif category in ['task', 'question'] or score > 8:
                summary['tier2_important'].append(self._compress_sentence(content))
            else:
                summary['tier3_supporting'].append(self._compress_sentence(content))

        # 限制每层数量
        summary['tier1_critical'] = summary['tier1_critical'][:10]
        summary['tier2_important'] = summary['tier2_important'][:15]
        summary['tier3_supporting'] = summary['tier3_supporting'][:5]

        return summary

    def _semantic_deduplicate(self, summary: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """语义去重 - 移除相似内容"""
        deduplicated = {}

        for tier, messages in summary.items():
            unique = []
            for msg in messages:
                # 简单的相似度检查
                is_duplicate = False
                for existing in unique:
                    similarity = self._calculate_similarity(msg, existing)
                    if similarity > 0.7:  # 70%相似度阈值
                        is_duplicate = True
                        break

                if not is_duplicate:
                    unique.append(msg)

            deduplicated[tier] = unique

        return deduplicated

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简化版）"""
        # 使用关键词重叠度
        words1 = set(text1)
        words2 = set(text2)

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _compress_sentence(self, text: str, max_length: int = 150) -> str:
        """压缩单个句子"""
        # 移除冗余词汇
        text = re.sub(r'(好的|嗯|那个|这个|就是|然后|所以)', '', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # 限制长度
        if len(text) > max_length:
            text = text[:max_length] + '...'

        return text

    def _structure_output(self, summary: Dict[str, List[str]]) -> str:
        """结构化输出"""
        output_parts = []

        # 实体追踪摘要
        if any(self.entities.values()):
            output_parts.append("## 📊 实体追踪")
            for entity_type, entities in self.entities.items():
                if entities:
                    output_parts.append(f"- {entity_type}: {', '.join(list(entities)[:5])}")
            output_parts.append("")

        # 关键决策（Tier 1）
        if summary['tier1_critical']:
            output_parts.append("## 🎯 关键决策")
            for i, msg in enumerate(summary['tier1_critical'], 1):
                output_parts.append(f"{i}. {msg}")
            output_parts.append("")

        # 重要任务（Tier 2）
        if summary['tier2_important']:
            output_parts.append("## ✅ 重要事项")
            for i, msg in enumerate(summary['tier2_important'], 1):
                output_parts.append(f"- {msg}")
            output_parts.append("")

        # 支撑信息（Tier 3）
        if summary['tier3_supporting']:
            output_parts.append("## 💡 相关信息")
            for msg in summary['tier3_supporting'][:3]:
                output_parts.append(f"- {msg}")

        if not output_parts:
            return "（对话历史已压缩，无关键信息需保留）"

        return '\n'.join(output_parts)

    def _estimate_tokens(self, messages: List[Dict[str, str]]) -> int:
        """估算token数量"""
        total_chars = 0
        for msg in messages:
            total_chars += len(msg.get('content', ''))
        return int(total_chars / 2)


def main():
    """测试V2.0压缩器"""
    # 示例对话
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

    compressor = AdvancedContextCompressor()
    result = compressor.compress_advanced(messages)

    print("=" * 60)
    print("Token节约大师 V2.0 - 高级压缩测试")
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
    print(f"追踪实体数: {result['stats']['entities_tracked']}")
    print("\n实体追踪：")
    for entity_type, entities in result['entities'].items():
        if entities:
            print(f"  {entity_type}: {entities}")


if __name__ == '__main__':
    main()
