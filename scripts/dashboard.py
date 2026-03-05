#!/usr/bin/env python3
"""
Token节约大师 V2.0 - 实时统计仪表盘
可视化token使用情况
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class TokenDashboard:
    """Token统计仪表盘"""
    
    def __init__(self):
        self.stats_file = Path(__file__).parent / 'token_stats.json'
        self.history_file = Path(__file__).parent / 'compression_history.json'
        
    def display_dashboard(self):
        """显示仪表盘"""
        stats = self._load_stats()
        history = self._load_history()
        
        print("=" * 70)
        print("📊 Token节约大师 V2.0 - 实时统计仪表盘")
        print("=" * 70)
        print(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 核心指标
        print("📈 核心指标")
        print("-" * 70)
        print(f"监控次数:       {stats.get('total_checks', 0):,}")
        print(f"压缩次数:       {stats.get('total_compressions', 0):,}")
        print(f"累计节约tokens: {stats.get('total_tokens_saved', 0):,}")
        print(f"当前tokens:     {stats.get('last_token_count', 0):,}")
        print()
        
        # 效率分析
        if stats.get('total_compressions', 0) > 0:
            avg_savings = stats.get('total_tokens_saved', 0) / stats.get('total_compressions', 1)
            print("⚡ 效率分析")
            print("-" * 70)
            print(f"平均每次节约:   {avg_savings:.0f} tokens")
            print(f"节约率:         {stats.get('total_tokens_saved', 0) / (stats.get('last_token_count', 1) * stats.get('total_compressions', 1)) * 100:.1f}%")
            print()
        
        # 历史趋势
        if history:
            print("📊 最近压缩记录")
            print("-" * 70)
            for record in history[-5:]:  # 显示最近5条
                print(f"[{record.get('time', 'N/A')}]")
                print(f"  压缩率: {record.get('compression_ratio', 0):.1f}%")
                print(f"  节约: {record.get('saved_tokens', 0):,} tokens")
                print()
        
        # 图表（简化版）
        print("📉 Token使用趋势（最近10次检查）")
        print("-" * 70)
        if history:
            recent = history[-10:]
            max_tokens = max(r.get('original_tokens', 0) for r in recent)
            for i, record in enumerate(recent, 1):
                tokens = record.get('original_tokens', 0)
                bar_length = int(tokens / max_tokens * 30) if max_tokens > 0 else 0
                bar = '█' * bar_length
                print(f"{i:2d}. {bar} {tokens:,}")
        else:
            print("暂无历史数据")
        print()
        
        # 建议
        print("💡 优化建议")
        print("-" * 70)
        if stats.get('last_token_count', 0) > 5000:
            print("⚠️  当前tokens较多，建议进行压缩")
        elif stats.get('total_compressions', 0) == 0:
            print("✅ 系统运行良好，暂无需压缩")
        else:
            print("✅ Token使用在正常范围内")
        print()
        
        print("=" * 70)
    
    def _load_stats(self) -> Dict[str, Any]:
        """加载统计数据"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """加载历史记录"""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def add_record(self, original_tokens: int, compressed_tokens: int, compression_ratio: float):
        """添加压缩记录"""
        history = self._load_history()
        
        record = {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'original_tokens': original_tokens,
            'compressed_tokens': compressed_tokens,
            'saved_tokens': original_tokens - compressed_tokens,
            'compression_ratio': compression_ratio
        }
        
        history.append(record)
        
        # 只保留最近100条
        history = history[-100:]
        
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)


def main():
    """主函数"""
    dashboard = TokenDashboard()
    dashboard.display_dashboard()


if __name__ == '__main__':
    main()
