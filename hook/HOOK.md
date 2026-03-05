---
name: token-saver
description: "Intelligent session compression to save tokens before context overflow"
homepage: https://github.com/liyuntao2032/token-saver
metadata:
  {
    "openclaw":
      {
        "emoji": "💰",
        "events": ["heartbeat", "command:compact"],
        "requires": { "config": ["workspace.dir"] },
        "install": [{ "id": "bundled", "kind": "skill", "label": "Token Saver V2.1" }],
      },
  }
---

# Token Saver Hook

Automatically compresses session history when approaching context window limits to save tokens and prevent overflow errors.

## What It Does

When triggered (via heartbeat or /compact command):

1. **Monitors session size** - Tracks current token count in active session
2. **Predicts overflow** - Calculates when context window will be exceeded
3. **Intelligent compression** - Compresses old messages while preserving:
   - Recent messages (configurable, default: 10)
   - Important keywords (决策, TODO, 重要, etc.)
   - Active sessions (< 2 hours old)
4. **Replaces original** - Backs up and replaces the session file
5. **Saves tokens** - Reduces token usage by ~70% while keeping context

## Compression Strategy

### Whitelist Protection
Sessions are **NOT** compressed if:
- Modified within last 2 hours
- Contains protected keywords: "Token节约大师", "正在开发"

### Smart Retention
Always preserves:
- Last N messages (default: 10)
- Messages with decision keywords: 决定, 确认, 采用
- Messages with task keywords: TODO, 待办, 需要
- Messages with important keywords: 重要, 关键, 注意

### Compression Ratio
- Target: 70% compression (keeps 30% of original tokens)
- Adaptive: Adjusts based on content importance
- Safe: Never exceeds 75% to preserve context

## Configuration

Add to your `~/.openclaw/openclaw.json`:

```json
{
  "hooks": {
    "internal": {
      "entries": {
        "token-saver": {
          "enabled": true,
          "threshold": 10000,
          "interval": 120,
          "compression_settings": {
            "max_compression_ratio": 0.7,
            "keep_recent_messages": 10,
            "preserve_keywords": ["重要", "决策", "TODO", "待办"]
          },
          "whitelist": {
            "enabled": true,
            "max_session_age_hours": 2,
            "preserve_if_contains": ["Token节约大师", "正在开发"]
          }
        }
      }
    }
  }
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `threshold` | number | 10000 | Minimum tokens to trigger compression |
| `interval` | number | 120 | Check interval in seconds (for heartbeat) |
| `max_compression_ratio` | number | 0.7 | Maximum compression (0.7 = 70% reduction) |
| `keep_recent_messages` | number | 10 | Number of recent messages to keep |
| `preserve_keywords` | array | [...] | Keywords that prevent message compression |
| `max_session_age_hours` | number | 2 | Protect sessions younger than this |
| `preserve_if_contains` | array | [...] | Keywords that prevent session compression |

## Output

When compression occurs:

1. **Backup created**: `~/.openclaw/workspace/skills/token-saver-v2/scripts/backups/<session>_<timestamp>.jsonl.backup`
2. **Report saved**: `~/.openclaw/workspace/skills/token-saver-v2/scripts/compressed/<session>_<timestamp>_report.txt`
3. **Session replaced**: Original session file now contains compressed version

### Example Report

```markdown
# 会话压缩摘要（智能模式）
时间: 2026-03-05 16:15:23
消息数: 150
最大压缩率: 70%
目标保留tokens: 30000
重要信息tokens: 5000
剩余可用tokens: 25000
平均消息tokens: 200
实际保留消息: 125

## 关键实体
2026-03-05, Token节约大师, V2.1, 70%

## 决策
1. 采用方案1：改进V2.1
2. 确认集成到OpenClaw hooks

## 最近对话（最后10条）
[2026-03-05 16:15:00] [user] 方案1：改进 V2.1（推荐）
[2026-03-05 16:14:55] [assistant] 好的爸爸！开始改进...
```

## Manual Trigger

You can manually trigger compression:

```bash
python3 /path/to/token-saver-v2/scripts/service.py test
```

## Disable

To disable this hook:

```bash
openclaw hooks disable token-saver
```

Or in config:

```json
{
  "hooks": {
    "internal": {
      "entries": {
        "token-saver": { "enabled": false }
      }
    }
  }
}
```

## Requirements

- Python 3.8+
- OpenClaw workspace configured
- Sessions stored in `~/.openclaw/agents/main/sessions/`

## Benefits

- ✅ **Prevents overflow** - Stops `model_context_window_exceeded` errors
- ✅ **Saves money** - Reduces token usage by 70%
- ✅ **Preserves context** - Keeps important information
- ✅ **Automatic** - Runs in background via heartbeats
- ✅ **Safe** - Always backs up before compressing

## Troubleshooting

### Compression not triggering?
- Check if session is in whitelist (recent or contains protected keywords)
- Verify threshold is reached (use `/status` to see token count)
- Ensure hook is enabled in config

### Lost important context?
- Increase `keep_recent_messages`
- Add keywords to `preserve_keywords`
- Disable whitelist temporarily

### Session still too large?
- Reduce `max_compression_ratio` to 0.8 (80% compression)
- Decrease `keep_recent_messages`
- Run manual compression with `python service.py test`
