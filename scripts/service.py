#!/usr/bin/env python3
"""
Token节约大师 V2.1 - 真正节约tokens的版本
生成OpenClaw兼容的JSONL格式，替换原始session
"""

import os
import sys
import json
import time
import signal
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import re


class BackgroundService:
    """后台服务 - 真正节约tokens的版本"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.config = self._load_config(config_file)
        self.running = False
        self.pid_file = Path(__file__).parent / 'token_saver.pid'
        self.log_file = Path(__file__).parent / 'token_saver.log'
        
        # OpenClaw session路径
        self.sessions_dir = Path.home() / '.openclaw' / 'agents' / 'main' / 'sessions'
        self.compressed_dir = Path(__file__).parent / 'compressed'
        self.compressed_dir.mkdir(exist_ok=True)
        
        # 备份目录
        self.backup_dir = Path(__file__).parent / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        
        # 白名单缓存
        self.whitelist_cache = {}
        
    def start(self):
        """启动后台服务"""
        # 检查是否已在运行
        if self._is_running():
            print("❌ Token节约大师已在运行中")
            print(f"   PID: {self._read_pid()}")
            return False
        
        print("=" * 70)
        print("🚀 Token节约大师 V2.1 - 真正节约tokens的版本")
        print("=" * 70)
        print(f"触发阈值: {self.config.get('threshold', 10000):,} tokens")
        print(f"检查间隔: {self.config.get('interval', 120)} 秒")
        print(f"最大压缩率: {self.config.get('compression_settings', {}).get('max_compression_ratio', 0.7) * 100}%")
        print(f"保留消息数: {self.config.get('compression_settings', {}).get('keep_recent_messages', 10)}")
        print(f"白名单: {'启用' if self.config.get('whitelist', {}).get('enabled', True) else '禁用'}")
        print(f"Session目录: {self.sessions_dir}")
        print(f"压缩输出: {self.compressed_dir}")
        print(f"备份目录: {self.backup_dir}")
        print("=" * 70)
        
        # 保存PID
        self._write_pid()
        
        # 设置信号处理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # 启动主循环
        self.running = True
        self._main_loop()
        
        return True
    
    def stop(self):
        """停止后台服务"""
        pid = self._read_pid()
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                print("✅ Token节约大师已停止")
                self._remove_pid()
            except ProcessLookupError:
                print("❌ 进程不存在")
                self._remove_pid()
        else:
            print("❌ Token节约大师未在运行")
    
    def status(self):
        """查看状态"""
        if self._is_running():
            pid = self._read_pid()
            print("=" * 70)
            print("✅ Token节约大师正在运行")
            print("=" * 70)
            print(f"PID: {pid}")
            
            # 显示最近的日志
            if self.log_file.exists():
                print("\n最近日志:")
                print("-" * 70)
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-10:]:
                        print(line.rstrip())
        else:
            print("❌ Token节约大师未运行")
    
    def _main_loop(self):
        """主循环"""
        self._log("后台服务启动 - V2.1 真正节约tokens版本")
        
        try:
            check_count = 0
            compression_count = 0
            
            while self.running:
                check_count += 1
                
                # 获取当前活跃的session
                current_session = self._get_current_session()
                
                if current_session:
                    # 检查白名单
                    if self._is_whitelisted(current_session):
                        self._log(f"检查 #{check_count}: Session {current_session.name} 在白名单中，跳过")
                    else:
                        # 检查token数量
                        token_count = self._check_session_tokens(current_session)
                        
                        self._log(f"检查 #{check_count}: Session {current_session.name}, tokens = {token_count}")
                        
                        # 判断是否需要压缩
                        if token_count >= self.config.get('threshold', 10000):
                            self._log(f"达到阈值，触发压缩")
                            result = self._compress_session(current_session, token_count)
                            compression_count += 1
                            
                            if result:
                                self._log(f"✅ 压缩完成: {result['stats']['saved_tokens']} tokens "
                                        f"(压缩率 {result['stats']['compression_ratio']:.1f}%)")
                                self._log(f"✅ 已替换原始session，节约tokens生效！")
                            else:
                                self._log(f"❌ 压缩失败")
                else:
                    self._log(f"检查 #{check_count}: 没有找到活跃session")
                
                # 等待
                time.sleep(self.config.get('interval', 120))
                
        except Exception as e:
            self._log(f"错误: {str(e)}")
            import traceback
            self._log(traceback.format_exc())
        finally:
            self._log("后台服务停止")
            self._remove_pid()
    
    def _get_current_session(self) -> Optional[Path]:
        """获取当前最活跃的session文件"""
        try:
            # 获取最近修改的jsonl文件
            sessions = list(self.sessions_dir.glob("*.jsonl"))
            if not sessions:
                return None
            
            # 按修改时间排序，取最新的
            sessions.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 检查最近2小时内有更新的session
            import time as t
            recent_threshold = t.time() - 7200  # 2小时内
            
            for session in sessions:
                if session.stat().st_mtime > recent_threshold:
                    return session
            
            return sessions[0]  # 如果没有最近的，返回最新的
            
        except Exception as e:
            self._log(f"获取session失败: {str(e)}")
            return None
    
    def _is_whitelisted(self, session_file: Path) -> bool:
        """检查session是否在白名单中"""
        whitelist_config = self.config.get('whitelist', {})
        
        if not whitelist_config.get('enabled', True):
            return False
        
        # 检查缓存
        if session_file.name in self.whitelist_cache:
            cached_time, is_whitelisted = self.whitelist_cache[session_file.name]
            if time.time() - cached_time < 300:  # 5分钟缓存
                return is_whitelisted
        
        try:
            # 读取session内容检查关键词
            messages = self._read_session_messages(session_file)
            content_text = ' '.join([msg.get('content', '') for msg in messages])
            
            # 检查是否包含保护关键词
            preserve_keywords = whitelist_config.get('preserve_if_contains', [])
            for keyword in preserve_keywords:
                if keyword in content_text:
                    self._log(f"Session包含保护关键词 '{keyword}'，加入白名单")
                    self.whitelist_cache[session_file.name] = (time.time(), True)
                    return True
            
            # 检查session年龄
            max_age_hours = whitelist_config.get('max_session_age_hours', 2)
            file_mtime = session_file.stat().st_mtime
            age_hours = (time.time() - file_mtime) / 3600
            
            if age_hours < max_age_hours:
                self._log(f"Session年龄 {age_hours:.1f}h < {max_age_hours}h，加入白名单")
                self.whitelist_cache[session_file.name] = (time.time(), True)
                return True
            
            self.whitelist_cache[session_file.name] = (time.time(), False)
            return False
            
        except Exception as e:
            self._log(f"白名单检查失败: {str(e)}")
            return False
    
    def _check_session_tokens(self, session_file: Path) -> int:
        """检查session的token数量"""
        try:
            # 读取文件大小作为粗略估算
            file_size = session_file.stat().st_size
            
            # JSONL格式，粗略估算：每字符约0.5 token
            estimated_tokens = file_size // 2
            
            return estimated_tokens
            
        except Exception as e:
            self._log(f"检查tokens失败: {str(e)}")
            return 0
    
    def _compress_session(self, session_file: Path, original_tokens: int) -> Optional[Dict[str, Any]]:
        """压缩session - 真正替换原始文件"""
        try:
            # 读取session内容
            messages = self._read_session_messages(session_file)
            
            if not messages:
                self._log("Session为空，跳过压缩")
                return None
            
            # 获取压缩配置
            compression_settings = self.config.get('compression_settings', {})
            max_ratio = compression_settings.get('max_compression_ratio', 0.7)
            keep_recent = compression_settings.get('keep_recent_messages', 10)
            
            # 计算目标tokens（保留30%的内容）
            target_tokens = int(original_tokens * (1 - max_ratio))
            
            # 执行压缩（自适应）
            compressor = SessionCompressor(
                max_compression_ratio=max_ratio,
                keep_recent_messages=keep_recent,
                preserve_keywords=compression_settings.get('preserve_keywords', []),
                target_tokens=target_tokens
            )
            
            # 1. 生成压缩摘要
            compressed_text = compressor.compress_adaptive(messages)
            
            # 2. 生成OpenClaw兼容的JSONL
            compressed_jsonl = self._generate_compressed_jsonl(messages, compressed_text, keep_recent)
            
            # 3. 计算压缩后tokens
            compressed_tokens = len(compressed_jsonl) // 2
            
            # 4. 备份原始文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"{session_file.stem}_{timestamp}.jsonl.backup"
            shutil.copy2(session_file, backup_file)
            self._log(f"✅ 已备份原始session: {backup_file.name}")
            
            # 5. 替换为压缩版本
            with open(session_file, 'w', encoding='utf-8') as f:
                f.write(compressed_jsonl)
            self._log(f"✅ 已替换原始session为压缩版本")
            
            # 6. 保存压缩报告
            report_file = self.compressed_dir / f"{session_file.stem}_{timestamp}_report.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(compressed_text)
                f.write(f"\n\n--- 压缩统计 ---\n")
                f.write(f"原始tokens: {original_tokens}\n")
                f.write(f"压缩后tokens: {compressed_tokens}\n")
                f.write(f"节约tokens: {original_tokens - compressed_tokens}\n")
                f.write(f"压缩率: {(1 - compressed_tokens/original_tokens)*100:.1f}%\n")
                f.write(f"最大允许压缩率: {max_ratio * 100}%\n")
                f.write(f"保留消息数: {keep_recent}\n")
                f.write(f"压缩时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"备份文件: {backup_file.name}\n")
            
            return {
                'compressed_file': str(report_file),
                'backup_file': str(backup_file),
                'stats': {
                    'original_tokens': original_tokens,
                    'compressed_tokens': compressed_tokens,
                    'saved_tokens': original_tokens - compressed_tokens,
                    'compression_ratio': round((1 - compressed_tokens / original_tokens) * 100, 2) if original_tokens > 0 else 0
                }
            }
            
        except Exception as e:
            self._log(f"压缩失败: {str(e)}")
            import traceback
            self._log(traceback.format_exc())
            return None
    
    def _generate_compressed_jsonl(self, messages: List[Dict[str, str]], 
                                   compressed_text: str, 
                                   keep_recent: int) -> str:
        """生成OpenClaw兼容的JSONL格式"""
        jsonl_lines = []
        
        # 1. 添加压缩摘要作为系统消息（放在最前面）
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
        
        # 2. 添加保留的消息（最近N条）
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
    
    def _read_session_messages(self, session_file: Path) -> List[Dict[str, str]]:
        """读取session中的消息"""
        messages = []
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        
                        # 只处理消息类型
                        if data.get('type') == 'message':
                            msg = data.get('message', {})
                            role = msg.get('role', '')
                            
                            # 提取文本内容
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
                        
        except Exception as e:
            self._log(f"读取session失败: {str(e)}")
        
        return messages
    
    def _log(self, message: str):
        """写入日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """加载配置"""
        config_path = Path(__file__).parent / config_file
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 默认配置
        return {
            'threshold': 10000,
            'interval': 120,
            'auto_start': True,
            'compression_settings': {
                'max_compression_ratio': 0.7,
                'keep_recent_messages': 10,
                'preserve_keywords': ['重要', '决策', 'TODO', '待办']
            },
            'whitelist': {
                'enabled': True,
                'max_session_age_hours': 2,
                'preserve_if_contains': ['Token节约大师', '正在开发']
            }
        }
    
    def _is_running(self) -> bool:
        """检查是否在运行"""
        pid = self._read_pid()
        if pid:
            try:
                os.kill(pid, 0)  # 检查进程是否存在
                return True
            except ProcessLookupError:
                return False
        return False
    
    def _read_pid(self) -> Optional[int]:
        """读取PID"""
        if self.pid_file.exists():
            with open(self.pid_file, 'r') as f:
                return int(f.read().strip())
        return None
    
    def _write_pid(self):
        """写入PID"""
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
    
    def _remove_pid(self):
        """删除PID文件"""
        if self.pid_file.exists():
            self.pid_file.unlink()
    
    def _signal_handler(self, signum, frame):
        """信号处理"""
        self.running = False
        self._log(f"收到停止信号 {signum}")


class SessionCompressor:
    """Session压缩器 - 智能压缩率控制"""
    
    def __init__(self, max_compression_ratio: float = 0.7, 
                 keep_recent_messages: int = 10,
                 preserve_keywords: List[str] = None,
                 target_tokens: int = None):
        self.max_compression_ratio = max_compression_ratio
        self.keep_recent_messages = keep_recent_messages
        self.target_tokens = target_tokens  # 目标保留的tokens数
        
        # 关键词分类
        self.decision_keywords = ['决定', '决策', '确认', '采用', '选择', '确定', '完成']
        self.task_keywords = ['TODO', '待办', '需要', '要', '必须', '完成', '计划']
        self.important_keywords = preserve_keywords or ['重要', '关键', '注意', '记住', '问题', '错误']
    
    def compress_adaptive(self, messages: List[Dict[str, str]]) -> str:
        """自适应压缩 - 确保压缩率不超过限制"""
        if not messages:
            return "（空会话）"
        
        # 先提取所有关键信息（完整保留，不截断）
        all_important = self._extract_all_important_full(messages)
        key_entities = set()
        
        for msg in messages:
            entities = self._extract_entities(msg.get('content', ''))
            key_entities.update(entities)
        
        # 计算关键信息占用的tokens
        important_text = self._format_important(all_important, key_entities)
        important_tokens = len(important_text) // 2
        
        # 计算还能保留多少消息
        if self.target_tokens:
            remaining_tokens = max(0, self.target_tokens - important_tokens)
        else:
            # 如果没有指定target_tokens，默认保留5000 tokens用于消息
            remaining_tokens = 5000
        
        # 估算每条消息的平均tokens（更准确）
        total_msg_chars = sum(len(msg.get('content', '')) for msg in messages)
        avg_msg_tokens = (total_msg_chars // 2) // len(messages) if messages else 100
        
        # 计算可以保留多少条消息
        # 使用更宽松的估算：每条消息的tokens * 1.1（包含元数据）
        max_recent = int(remaining_tokens / (avg_msg_tokens * 1.1)) if avg_msg_tokens > 0 else 0
        
        # 确保至少保留10条，最多保留所有消息
        max_recent = max(10, min(len(messages), max_recent))
        
        # 生成压缩输出
        lines = []
        lines.append(f"# 会话压缩摘要（智能模式）")
        lines.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"消息数: {len(messages)}")
        lines.append(f"最大压缩率: {self.max_compression_ratio * 100}%")
        lines.append(f"目标保留tokens: {self.target_tokens}")
        lines.append(f"重要信息tokens: {important_tokens}")
        lines.append(f"剩余可用tokens: {remaining_tokens}")
        lines.append(f"平均消息tokens: {avg_msg_tokens}")
        lines.append(f"实际保留消息: {max_recent}")
        lines.append("")
        
        lines.append(important_text)
        
        # 添加最近N条消息（完整保留，不截断）
        recent_count = min(max_recent, len(messages))
        lines.append(f"## 最近对话（最后{recent_count}条）")
        for msg in messages[-recent_count:]:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')  # 不截断
            timestamp = msg.get('timestamp', '')[:19] if msg.get('timestamp') else ''
            lines.append(f"[{timestamp}] [{role}] {content}")
        
        return '\n'.join(lines)
    
    def _extract_all_important_full(self, messages: List[Dict[str, str]]) -> Dict[str, List[str]]:
        """提取所有重要信息（完整保留）"""
        important = {
            'decisions': [],
            'tasks': [],
            'important_info': []
        }
        
        for msg in messages:
            content = msg.get('content', '')
            
            # 提取决策（完整保留）
            if any(kw in content for kw in self.decision_keywords):
                important['decisions'].append(content)  # 不截断
            
            # 提取任务（完整保留）
            if any(kw in content for kw in self.task_keywords):
                important['tasks'].append(content)  # 不截断
            
            # 提取重要信息（完整保留）
            if any(kw in content for kw in self.important_keywords):
                important['important_info'].append(content)  # 不截断
        
        # 去重
        for key in important:
            important[key] = list(dict.fromkeys(important[key]))[:10]  # 增加到10条
        
        return important
    
    def _format_important(self, important: Dict[str, List[str]], entities: set) -> str:
        """格式化重要信息"""
        lines = []
        
        if entities:
            lines.append(f"## 关键实体")
            lines.append(', '.join(sorted(entities)[:10]))
            lines.append("")
        
        if important['decisions']:
            lines.append(f"## 决策")
            for i, d in enumerate(important['decisions'], 1):
                lines.append(f"{i}. {d}")  # 完整内容
            lines.append("")
        
        if important['tasks']:
            lines.append(f"## 待办任务")
            for i, t in enumerate(important['tasks'], 1):
                lines.append(f"{i}. {t}")  # 完整内容
            lines.append("")
        
        if important['important_info']:
            lines.append(f"## 重要信息")
            for i, info in enumerate(important['important_info'], 1):
                lines.append(f"{i}. {info}")  # 完整内容
            lines.append("")
        
        return '\n'.join(lines)
    
    def _extract_entities(self, text: str) -> set:
        """提取实体"""
        entities = set()
        
        # 提取项目名
        projects = re.findall(r'(?:项目|平台|系统|工具)[：:]\s*([^\s，。]+)', text)
        entities.update(projects)
        
        # 提取日期
        dates = re.findall(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日号]?', text)
        entities.update(dates)
        
        # 提取数字
        numbers = re.findall(r'\d+(?:\.\d+)?(?:%|tokens?|小时|分钟)', text)
        entities.update(numbers)
        
        return entities


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Token节约大师 V2.1 - 真正节约tokens的版本')
    parser.add_argument('action', choices=['start', 'stop', 'status', 'restart', 'test'],
                       help='操作: start(启动), stop(停止), status(状态), restart(重启), test(测试)')
    
    args = parser.parse_args()
    
    service = BackgroundService()
    
    if args.action == 'start':
        service.start()
    elif args.action == 'stop':
        service.stop()
    elif args.action == 'status':
        service.status()
    elif args.action == 'restart':
        service.stop()
        time.sleep(1)
        service.start()
    elif args.action == 'test':
        # 测试模式：压缩一次当前session
        print("测试模式：压缩当前session")
        current_session = service._get_current_session()
        if current_session:
            print(f"找到session: {current_session.name}")
            
            # 检查白名单
            if service._is_whitelisted(current_session):
                print("⚠️  Session在白名单中，不会被压缩")
                print("提示：如需强制压缩，请修改config.json中的whitelist配置")
                return
            
            token_count = service._check_session_tokens(current_session)
            print(f"预估tokens: {token_count}")
            
            if token_count > 0:
                result = service._compress_session(current_session, token_count)
                if result:
                    print(f"\n✅ 压缩成功！")
                    print(f"压缩报告: {result['compressed_file']}")
                    print(f"备份文件: {result['backup_file']}")
                    print(f"原始tokens: {result['stats']['original_tokens']}")
                    print(f"压缩后tokens: {result['stats']['compressed_tokens']}")
                    print(f"节约tokens: {result['stats']['saved_tokens']}")
                    print(f"压缩率: {result['stats']['compression_ratio']:.1f}%")
                    print(f"\n✅ 已替换原始session，OpenClaw下次启动会读取压缩版本！")
                else:
                    print("❌ 压缩失败")
        else:
            print("❌ 没有找到活跃session")


if __name__ == '__main__':
    main()
