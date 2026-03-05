#!/usr/bin/env python3
"""
Token Saver Hook Handler
OpenClaw internal hook for intelligent session compression
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import re


class TokenSaverHook:
    """Token Saver Hook - OpenClaw internal hook handler"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Default configuration
        self.threshold = self.config.get('threshold', 10000)
        self.compression_settings = self.config.get('compression_settings', {})
        self.whitelist_config = self.config.get('whitelist', {})
        
        # OpenClaw session path
        self.sessions_dir = Path.home() / '.openclaw' / 'agents' / 'main' / 'sessions'
        
        # Output directories
        self.output_dir = Path(__file__).parent.parent / 'scripts'
        self.compressed_dir = self.output_dir / 'compressed'
        self.backup_dir = self.output_dir / 'backups'
        self.compressed_dir.mkdir(exist_ok=True, parents=True)
        self.backup_dir.mkdir(exist_ok=True, parents=True)
        
        # Whitelist cache
        self.whitelist_cache = {}
    
    def handle_event(self, event: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle OpenClaw hook event
        
        Args:
            event: Event name (e.g., 'heartbeat', 'command:compact')
            context: Event context with session info, workspace, etc.
        
        Returns:
            Result dict with status and message
        """
        try:
            # Get current session
            current_session = self._get_current_session()
            
            if not current_session:
                return {
                    'status': 'skip',
                    'message': 'No active session found'
                }
            
            # Check whitelist
            if self._is_whitelisted(current_session):
                return {
                    'status': 'skip',
                    'message': f'Session {current_session.name} is whitelisted'
                }
            
            # Check token count
            token_count = self._estimate_tokens(current_session)
            
            # Decide if compression is needed
            if token_count < self.threshold:
                return {
                    'status': 'skip',
                    'message': f'Session has {token_count} tokens (threshold: {self.threshold})'
                }
            
            # Perform compression
            result = self._compress_session(current_session, token_count)
            
            if result:
                return {
                    'status': 'success',
                    'message': f'Compressed session: saved {result["stats"]["saved_tokens"]} tokens '
                              f'({result["stats"]["compression_ratio"]:.1f}% compression)',
                    'stats': result['stats']
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Compression failed'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Hook error: {str(e)}'
            }
    
    def _get_current_session(self) -> Optional[Path]:
        """Get the most recently modified session file"""
        try:
            sessions = list(self.sessions_dir.glob("*.jsonl"))
            if not sessions:
                return None
            
            # Sort by modification time, get most recent
            sessions.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return sessions[0]
            
        except Exception:
            return None
    
    def _is_whitelisted(self, session_file: Path) -> bool:
        """Check if session should be protected from compression"""
        if not self.whitelist_config.get('enabled', True):
            return False
        
        # Check cache
        cache_key = session_file.name
        if cache_key in self.whitelist_cache:
            cached_time, is_whitelisted = self.whitelist_cache[cache_key]
            if time.time() - cached_time < 300:  # 5 minute cache
                return is_whitelisted
        
        try:
            # Read session content
            content = session_file.read_text(encoding='utf-8')
            
            # Check for protected keywords
            preserve_keywords = self.whitelist_config.get('preserve_if_contains', [])
            for keyword in preserve_keywords:
                if keyword in content:
                    self.whitelist_cache[cache_key] = (time.time(), True)
                    return True
            
            # Check session age
            max_age_hours = self.whitelist_config.get('max_session_age_hours', 2)
            file_mtime = session_file.stat().st_mtime
            age_hours = (time.time() - file_mtime) / 3600
            
            if age_hours < max_age_hours:
                self.whitelist_cache[cache_key] = (time.time(), True)
                return True
            
            self.whitelist_cache[cache_key] = (time.time(), False)
            return False
            
        except Exception:
            return False
    
    def _estimate_tokens(self, session_file: Path) -> int:
        """Estimate token count from file size"""
        try:
            file_size = session_file.stat().st_size
            # Rough estimate: 1 token ≈ 2 characters
            return file_size // 2
        except Exception:
            return 0
    
    def _compress_session(self, session_file: Path, original_tokens: int) -> Optional[Dict[str, Any]]:
        """Compress session file"""
        try:
            # Read messages
            messages = self._read_messages(session_file)
            
            if not messages:
                return None
            
            # Get compression parameters
            max_ratio = self.compression_settings.get('max_compression_ratio', 0.7)
            keep_recent = self.compression_settings.get('keep_recent_messages', 10)
            
            # Calculate target tokens
            target_tokens = int(original_tokens * (1 - max_ratio))
            
            # Compress
            compressed_text = self._compress_messages(messages, target_tokens, keep_recent)
            
            # Generate compressed JSONL
            compressed_jsonl = self._generate_jsonl(messages, compressed_text, keep_recent)
            
            # Calculate new token count
            compressed_tokens = len(compressed_jsonl) // 2
            
            # Backup original
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"{session_file.stem}_{timestamp}.jsonl.backup"
            import shutil
            shutil.copy2(session_file, backup_file)
            
            # Replace with compressed version
            session_file.write_text(compressed_jsonl, encoding='utf-8')
            
            # Save report
            report_file = self.compressed_dir / f"{session_file.stem}_{timestamp}_report.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(compressed_text)
                f.write(f"\n\n--- 压缩统计 ---\n")
                f.write(f"原始tokens: {original_tokens}\n")
                f.write(f"压缩后tokens: {compressed_tokens}\n")
                f.write(f"节约tokens: {original_tokens - compressed_tokens}\n")
                f.write(f"压缩率: {(1 - compressed_tokens/original_tokens)*100:.1f}%\n")
            
            return {
                'compressed_file': str(report_file),
                'backup_file': str(backup_file),
                'stats': {
                    'original_tokens': original_tokens,
                    'compressed_tokens': compressed_tokens,
                    'saved_tokens': original_tokens - compressed_tokens,
                    'compression_ratio': round((1 - compressed_tokens / original_tokens) * 100, 2)
                }
            }
            
        except Exception as e:
            print(f"Compression error: {e}", file=sys.stderr)
            return None
    
    def _read_messages(self, session_file: Path) -> List[Dict[str, str]]:
        """Read messages from session file"""
        messages = []
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        
                        if data.get('type') == 'message':
                            msg = data.get('message', {})
                            role = msg.get('role', '')
                            
                            # Extract text content
                            content_list = msg.get('content', [])
                            text_parts = []
                            
                            for item in content_list:
                                if item.get('type') == 'text':
                                    text_parts.append(item.get('text', ''))
                            
                            if text_parts:
                                messages.append({
                                    'role': role,
                                    'content': ' '.join(text_parts),
                                    'timestamp': data.get('timestamp', '')
                                })
                                
                    except json.JSONDecodeError:
                        continue
                        
        except Exception:
            pass
        
        return messages
    
    def _compress_messages(self, messages: List[Dict[str, str]], 
                          target_tokens: int, 
                          keep_recent: int) -> str:
        """Generate compressed summary"""
        if not messages:
            return "（空会话）"
        
        # Extract important information
        important = self._extract_important(messages)
        
        # Calculate how many messages to keep
        important_tokens = len(str(important)) // 2
        remaining_tokens = max(0, target_tokens - important_tokens)
        
        avg_msg_tokens = sum(len(msg.get('content', '')) for msg in messages) // 2 // len(messages) if messages else 100
        max_recent = int(remaining_tokens / (avg_msg_tokens * 1.1)) if avg_msg_tokens > 0 else 0
        max_recent = max(10, min(len(messages), max_recent))
        
        # Generate output
        lines = []
        lines.append(f"# 会话压缩摘要（智能模式）")
        lines.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"消息数: {len(messages)}")
        lines.append(f"目标保留tokens: {target_tokens}")
        lines.append(f"实际保留消息: {max_recent}")
        lines.append("")
        
        lines.append(important)
        
        # Add recent messages
        recent_count = min(max_recent, len(messages))
        lines.append(f"## 最近对话（最后{recent_count}条）")
        for msg in messages[-recent_count:]:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')[:19] if msg.get('timestamp') else ''
            lines.append(f"[{timestamp}] [{role}] {content}")
        
        return '\n'.join(lines)
    
    def _extract_important(self, messages: List[Dict[str, str]]) -> str:
        """Extract important information from messages"""
        decision_keywords = ['决定', '决策', '确认', '采用', '选择', '确定', '完成']
        task_keywords = ['TODO', '待办', '需要', '要', '必须', '计划']
        important_keywords = self.compression_settings.get('preserve_keywords', ['重要', '关键', '注意'])
        
        decisions = []
        tasks = []
        important_info = []
        
        for msg in messages:
            content = msg.get('content', '')
            
            if any(kw in content for kw in decision_keywords):
                decisions.append(content[:200])  # Keep first 200 chars
            
            if any(kw in content for kw in task_keywords):
                tasks.append(content[:200])
            
            if any(kw in content for kw in important_keywords):
                important_info.append(content[:200])
        
        # Deduplicate
        decisions = list(dict.fromkeys(decisions))[:5]
        tasks = list(dict.fromkeys(tasks))[:5]
        important_info = list(dict.fromkeys(important_info))[:5]
        
        lines = []
        
        if decisions:
            lines.append("## 决策")
            for i, d in enumerate(decisions, 1):
                lines.append(f"{i}. {d}")
            lines.append("")
        
        if tasks:
            lines.append("## 待办任务")
            for i, t in enumerate(tasks, 1):
                lines.append(f"{i}. {t}")
            lines.append("")
        
        if important_info:
            lines.append("## 重要信息")
            for i, info in enumerate(important_info, 1):
                lines.append(f"{i}. {info}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_jsonl(self, messages: List[Dict[str, str]], 
                       compressed_text: str, 
                       keep_recent: int) -> str:
        """Generate OpenClaw-compatible JSONL"""
        jsonl_lines = []
        
        # Add compression summary as system message
        jsonl_lines.append(json.dumps({
            "type": "message",
            "timestamp": datetime.now().isoformat() + "Z",
            "message": {
                "role": "assistant",
                "content": [{
                    "type": "text",
                    "text": f"[Token节约大师压缩摘要]\n\n{compressed_text}"
                }]
            }
        }, ensure_ascii=False))
        
        # Add recent messages
        recent_count = min(keep_recent, len(messages))
        for msg in messages[-recent_count:]:
            jsonl_lines.append(json.dumps({
                "type": "message",
                "timestamp": msg.get('timestamp', ''),
                "message": {
                    "role": msg.get('role', ''),
                    "content": [{
                        "type": "text",
                        "text": msg.get('content', '')
                    }]
                }
            }, ensure_ascii=False))
        
        return '\n'.join(jsonl_lines) + '\n'


# Export for OpenClaw
def handle_event(event: str, context: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    OpenClaw hook entry point
    
    Args:
        event: Event name
        context: Event context
        config: Hook configuration from openclaw.json
    
    Returns:
        Result dict
    """
    hook = TokenSaverHook(config)
    return hook.handle_event(event, context)


# For testing
if __name__ == '__main__':
    # Test the hook
    test_config = {
        'threshold': 10000,
        'compression_settings': {
            'max_compression_ratio': 0.7,
            'keep_recent_messages': 10,
            'preserve_keywords': ['重要', '决策', 'TODO']
        },
        'whitelist': {
            'enabled': True,
            'max_session_age_hours': 2,
            'preserve_if_contains': ['Token节约大师', '正在开发']
        }
    }
    
    result = handle_event('heartbeat', {}, test_config)
    print(json.dumps(result, indent=2, ensure_ascii=False))
