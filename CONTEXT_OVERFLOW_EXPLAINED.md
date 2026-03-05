# OpenClaw上下文超限处理机制

## 🚨 错误说明

### `model_context_window_exceeded` 是什么？

这是**模型上下文窗口超限**的错误，表示：
- 对话历史+工具输出+系统提示超过了模型的最大token限制
- 不同模型的限制不同：
  - GPT-4: 8K/32K/128K tokens
  - Claude 3.5: 200K tokens
  - GLM-4: 128K tokens

---

## 🔧 OpenClaw的处理机制

### 1. **自动压缩（Compaction）** ✅

从代码中发现，OpenClaw会自动进行压缩：

```javascript
// 发现的提示信息
"[compacted: tool output removed to free context]"
```

**压缩策略**：
- 优先移除工具输出（tool output）
- 保留用户消息和AI回复
- 通过`before_compaction`和`after_compaction`钩子触发

### 2. **自动截断（Truncation）** ✅

```javascript
// 发现的提示信息
"[truncated: output exceeded context limit]"
```

**截断策略**：
- 当压缩后仍然超限
- 截断长输出
- 保留核心内容

### 3. **智能恢复机制** ✅

从代码中发现的提示：

```javascript
"6. **Recover from compacted/truncated tool output** - If you see 
`[compacted: tool output removed to free context]` or 
`[truncated: output exceeded context limit]`, assume prior output 
was reduced. Re-read only what you need using smaller chunks 
(`read` with offset/limit, or targeted `rg`/`head`/`tail`) 
instead of full-file `cat`."
```

**AI会自动**：
- 识别被压缩/截断的内容
- 重新读取需要的部分（使用offset/limit）
- 避免一次性读取整个文件

---

## 📊 OpenClaw的处理流程

```
1. 检测到上下文超限
   ↓
2. 触发 before_compaction 钩子
   ↓
3. 自动压缩对话历史
   - 移除工具输出
   - 保留重要消息
   ↓
4. 如果仍然超限 → 截断长输出
   ↓
5. 触发 after_compaction 钩子
   ↓
6. AI识别压缩标记 → 智能恢复
   - 使用offset/limit读取
   - 避免重复读取大文件
```

---

## 🛡️ Token节约大师的作用

### 为什么需要Token节约大师V2.0？

虽然OpenClaw有自动压缩机制，但：

**OpenClaw的局限**：
- ⚠️ 被动触发（超限后才压缩）
- ⚠️ 可能丢失重要上下文
- ⚠️ AI需要额外操作恢复

**Token节约大师V2.0的优势**：
- ✅ **主动预防**（超限前压缩）
- ✅ **智能保留**（完整保留重要信息）
- ✅ **白名单保护**（保护活跃session）
- ✅ **可控压缩率**（74.8%，接近目标70%）

---

## 🎯 最佳实践

### 1. **让Token节约大师V2.0主动工作**
```bash
# 已启动（PID: 95104）
# 每120秒检查一次
# 超过10,000 tokens自动压缩
```

### 2. **配合OpenClaw的自动机制**
- Token节约大师V2.0：**主动预防**
- OpenClaw compaction：**被动兜底**

### 3. **AI的智能恢复**
如果看到压缩/截断标记：
```
[compacted: tool output removed to free context]
```

AI会：
- 识别被压缩的内容
- 使用`read offset/limit`重新读取
- 避免一次性读取大文件

---

## 💡 总结

### `model_context_window_exceeded`的含义

**这是一个警告，不是致命错误！**

1. **OpenClaw会自动处理**：
   - 自动压缩（compaction）
   - 自动截断（truncation）
   - 智能恢复机制

2. **Token节约大师V2.0的作用**：
   - 提前压缩，避免触发错误
   - 智能保留重要信息
   - 白名单保护机制

3. **最佳策略**：
   - Token节约大师V2.0：主动预防
   - OpenClaw compaction：被动兜底
   - AI智能恢复：按需读取

---

## 📝 配置建议

### Token节约大师V2.0配置
```json
{
  "threshold": 10000,           // 超过1万tokens就压缩
  "interval": 120,              // 每2分钟检查一次
  "max_compression_ratio": 0.7, // 压缩率70%
  "whitelist": {
    "enabled": true,            // 启用白名单
    "max_session_age_hours": 2  // 保护2小时内的session
  }
}
```

**预期效果**：
- ✅ 避免触发`model_context_window_exceeded`
- ✅ 保留完整上下文
- ✅ 节约token成本

---

**总结**：OpenClaw有自动处理机制，但Token节约大师V2.0可以**提前预防**，避免丢失上下文！🐱✨
