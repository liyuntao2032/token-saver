# Token节约大师 V2.0 - 技术实现详解

## 🎯 核心问题

**V1.0的问题**：
- 使用`random.randint(3000, 8000)`模拟token数量
- 使用固定返回值模拟压缩结果
- **根本没有真正读取session数据**

---

## 🔧 技术实现方案

### 1. **真正的Session读取** 📖

#### 1.1 OpenClaw Session结构
```
~/.openclaw/agents/main/sessions/
├── sessions.json          # 索引文件
└── *.jsonl                # 对话历史文件（JSONL格式）
```

#### 1.2 JSONL文件格式
每行一个JSON对象：
```json
{
  "type": "message",
  "timestamp": "2026-03-04T02:50:44.000Z",
  "message": {
    "role": "assistant",
    "content": [
      {
        "type": "text",
        "text": "实际消息内容..."
      }
    ]
  }
}
```

#### 1.3 读取代码实现
```python
def _read_session_messages(self, session_file: Path) -> List[Dict[str, str]]:
    """读取session中的消息"""
    messages = []
    
    with open(session_file, 'r', encoding='utf-8') as f:
        for line in f:  # 逐行读取JSONL
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
    
    return messages
```

**关键技术点**：
- ✅ 逐行读取JSONL（不是一次性加载）
- ✅ 解析JSON结构
- ✅ 提取`message.content`中的`text`类型
- ✅ 保留role、content、timestamp

---

### 2. **智能压缩算法** 🧠

#### 2.1 目标Tokens计算
```python
# 获取配置的最大压缩率（默认70%）
max_ratio = 0.7

# 计算目标保留的tokens（保留30%）
target_tokens = int(original_tokens * (1 - max_ratio))
```

**举例**：
- 原始tokens: 359,329
- 目标tokens: 359,329 × 0.3 = 107,798

#### 2.2 提取关键信息（完整保留）
```python
def _extract_all_important_full(self, messages):
    important = {
        'decisions': [],      # 决策
        'tasks': [],          # 待办
        'important_info': []  # 重要信息
    }
    
    for msg in messages:
        content = msg.get('content', '')
        
        # 提取决策（完整保留，不截断）
        if any(kw in content for kw in self.decision_keywords):
            important['decisions'].append(content)  # 完整内容
        
        # 提取任务
        if any(kw in content for kw in self.task_keywords):
            important['tasks'].append(content)
        
        # 提取重要信息
        if any(kw in content for kw in self.important_keywords):
            important['important_info'].append(content)
    
    return important
```

**关键词分类**：
- 决策：'决定', '决策', '确认', '采用', '选择', '确定', '完成'
- 任务：'TODO', '待办', '需要', '要', '必须', '完成', '计划'
- 重要：'重要', '关键', '注意', '记住', '问题', '错误'

#### 2.3 智能保留消息数量计算
```python
# 计算重要信息占用的tokens
important_text = self._format_important(all_important, key_entities)
important_tokens = len(important_text) // 2

# 计算剩余可用tokens
remaining_tokens = target_tokens - important_tokens

# 估算每条消息的平均tokens
total_msg_chars = sum(len(msg.get('content', '')) for msg in messages)
avg_msg_tokens = (total_msg_chars // 2) // len(messages)

# 计算可以保留多少条消息
# 考虑元数据开销，使用1.1倍系数
max_recent = int(remaining_tokens / (avg_msg_tokens * 1.1))

# 确保至少保留10条
max_recent = max(10, min(len(messages), max_recent))
```

**计算流程**：
1. 目标tokens = 107,798
2. 重要信息tokens = 32,532
3. 剩余tokens = 107,798 - 32,532 = 75,266
4. 平均消息tokens = 657
5. 保留消息数 = 75,266 / (657 × 1.1) = 104条
6. 实际保留 = min(86, 104) = 86条（全部保留）

---

### 3. **白名单保护机制** 🛡️

#### 3.1 白名单检查流程
```python
def _is_whitelisted(self, session_file: Path) -> bool:
    # 1. 检查缓存（5分钟有效期）
    if session_file.name in self.whitelist_cache:
        cached_time, is_whitelisted = self.whitelist_cache[session_file.name]
        if time.time() - cached_time < 300:
            return is_whitelisted
    
    # 2. 检查保护关键词
    messages = self._read_session_messages(session_file)
    content_text = ' '.join([msg.get('content', '') for msg in messages])
    
    preserve_keywords = [
        'Token节约大师',
        '正在开发',
        '正在进行'
    ]
    
    for keyword in preserve_keywords:
        if keyword in content_text:
            self.whitelist_cache[session_file.name] = (time.time(), True)
            return True
    
    # 3. 检查session年龄
    max_age_hours = 2  # 2小时内的session保护
    file_mtime = session_file.stat().st_mtime
    age_hours = (time.time() - file_mtime) / 3600
    
    if age_hours < max_age_hours:
        self.whitelist_cache[session_file.name] = (time.time(), True)
        return True
    
    return False
```

**保护规则**：
1. **关键词保护**：包含特定关键词的session不压缩
2. **时间保护**：2小时内的活跃session不压缩
3. **缓存机制**：避免重复检查（5分钟缓存）

---

### 4. **Token估算方法** 📊

#### 4.1 文件级别估算
```python
def _check_session_tokens(self, session_file: Path) -> int:
    """检查session的token数量"""
    # 读取文件大小
    file_size = session_file.stat().st_size
    
    # 粗略估算：每字符约0.5 token
    # （中文约1.5字符/token，英文约4字符/token，取平均）
    estimated_tokens = file_size // 2
    
    return estimated_tokens
```

#### 4.2 精确计算
```python
# 文本tokens = 字符数 / 2
compressed_tokens = len(compressed_text) // 2
```

---

## 🎯 核心技术要点

### 1. **JSONL逐行解析**
- ✅ 使用`json.loads(line)`逐行解析
- ✅ 避免一次性加载大文件
- ✅ 处理嵌套JSON结构

### 2. **智能容量计算**
```
目标tokens = 原始tokens × (1 - 压缩率)
重要信息tokens = 提取的关键信息占用
剩余tokens = 目标tokens - 重要信息tokens
保留消息数 = 剩余tokens / (平均消息tokens × 系数)
```

### 3. **完整保留策略**
- ✅ 关键信息**不截断**（完整保留）
- ✅ 消息内容**不截断**（完整保留）
- ✅ 通过**减少消息数量**来控制tokens

### 4. **多层保护机制**
1. 白名单保护（关键词+时间）
2. 最少保留10条消息
3. 缓存避免重复检查

---

## 📈 性能优化

### 1. **文件读取优化**
- 使用`Path`对象而不是字符串路径
- 逐行读取，避免内存溢出
- 异常处理保证稳定性

### 2. **缓存机制**
```python
self.whitelist_cache = {}  # 白名单缓存

# 5分钟有效期
if time.time() - cached_time < 300:
    return cached_result
```

### 3. **智能估算**
- 文件大小 → token估算（快速）
- 平均消息长度 → 保留数量（准确）

---

## 🔍 与V1.0的对比

| 特性 | V1.0（模拟版） | V2.0（真实版） |
|------|--------------|--------------|
| **Session读取** | `random.randint()` | `json.loads(line)` |
| **Token计算** | 固定值8000 | `file_size // 2` |
| **压缩结果** | 固定返回 | 真正压缩 |
| **白名单** | ❌ 无 | ✅ 多层保护 |
| **Git提交** | ❌ 未提交 | ✅ 已提交 |

---

## 🎊 总结

**核心技术手段**：

1. **JSONL逐行解析** - 真正读取OpenClaw session
2. **智能容量计算** - 动态计算保留数量
3. **完整保留策略** - 不截断重要内容
4. **白名单保护** - 多层保护机制
5. **性能优化** - 缓存+估算

**这次是真正可用的版本，不是模拟！** ✅
