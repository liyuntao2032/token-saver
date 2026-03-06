# Token节约大师 - OpenClaw Skill 💰

> 智能压缩对话历史，防止上下文溢出，平均节约70% tokens！

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Compatible-green.svg)](https://openclaw.ai)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)

## 🎉 最新更新

### V2.1.0 - 系统服务集成！🔥
- **自动运行**: macOS launchd 系统服务，开机自启动
- **后台监控**: 每2分钟自动检查 session 大小
- **智能压缩**: 超过10,000 tokens 时自动压缩（70%压缩率）
- **白名单保护**: 2小时内的活跃 session 不压缩
- **完整管理**: 提供 CLI 工具管理服务

### V1.1.0 - 性能飞跃！
- **压缩率提升**: 8.33% → 54.43% (提升45.62个百分点)
- **核心技术**: 字段级压缩 + 智能去重
- **优化时间**: 4小时

## 🎯 核心功能

### 1. 自动监控 🤖
后台服务持续监控 session 大小，防止上下文溢出

### 2. 智能压缩 🗜️
超过阈值时自动压缩，保留关键信息（决策、待办、关键词）

### 3. 白名单保护 🛡️
保护活跃 session（2小时内），避免中断正在进行的工作

### 4. 系统服务 ⚙️
macOS launchd 自动启动，无需手动操作

### 5. 完整管理 📋
提供 CLI 工具管理服务（启动、停止、重启、查看日志）

## 📊 性能对比

| 版本 | 压缩率 | 特性 | 推荐度 |
|------|--------|------|--------|
| V1.0 | 8.33% | 基础压缩 | ⭐⭐ |
| V1.1.0 | 54.43% | 性能飞跃 | ⭐⭐⭐ |
| **V2.1.0** | **70%** | **系统服务 + 自动化** | **⭐⭐⭐⭐⭐** |

**V2.1 是最推荐的版本！** 🚀

## 💡 实测效果

### 原始对话（8轮，79 tokens）
```
用户: 我想做一个数据分析项目，预算50万元
AI: 好的，我了解了...
（共8轮对话）
```

### V1.1.0压缩后（36 tokens）
```
预算:50万元 | 工期:3个月 | 技术:Python+Vue.js | 决策:微服务架构 | 待办:数据库设计
```

**节约：54.43% tokens！** 🎉

## 🚀 快速开始

### V2.1.0 推荐方式（自动运行）

```bash
# 1. 克隆仓库
cd ~/.openclaw/workspace/skills
git clone https://github.com/liyuntao2032/token-saver.git token-saver-v2

# 2. 安装为系统服务
cd token-saver-v2/scripts
./token-saver.sh install

# 3. 验证安装
./token-saver.sh status

# 输出示例：
# ✅ 状态: 运行中
# 📋 PID: 73955
# 📝 最近日志: ...
```

### 管理命令

```bash
# 查看状态
./token-saver.sh status

# 查看日志
./token-saver.sh log

# 实时监控日志
./token-saver.sh log -f

# 停止服务
./token-saver.sh stop

# 启动服务
./token-saver.sh start

# 重启服务
./token-saver.sh restart

# 测试压缩功能
./token-saver.sh test

# 卸载服务
./token-saver.sh uninstall
```

### V1.1.0 手动压缩（可选）

```bash
# 使用V1.1.0压缩
python scripts/final_compressor.py

# 使用V1.0压缩
python scripts/compress_context.py --action compress
```

## 📝 更新日志

### v2.1.0 (2026-03-05)
- 🔥 **系统服务集成**: macOS launchd 自动启动
- ✅ **后台监控**: 每2分钟自动检查 session 大小
- ✅ **智能压缩**: 超过10,000 tokens 时自动压缩（70%压缩率）
- ✅ **白名单保护**: 2小时内的活跃 session 不压缩
- ✅ **完整管理**: 提供 CLI 工具管理服务
- ✅ **备份机制**: 压缩前备份原始文件
- ✅ **日志记录**: 完整的运行日志和错误日志

### v2.0.0 (2026-03-05)
- ✨ 改进压缩算法，控制压缩率在70%左右
- ✅ 保留更多上下文信息
- ✅ 添加白名单机制

### v1.1.0 (2026-03-04 23:17)
- ✨ 性能飞跃：压缩率从8.33%提升至54.43%
- ✅ 字段级压缩技术
- ✅ 智能去重算法
- ✅ 极简格式输出

### v1.0.0 (2026-03-04 18:54)
- ✨ 首次发布
- ✅ 对话历史压缩
- ✅ 关键信息提取
- ✅ Token使用统计

## 📄 许可证

MIT License

---

⭐ 如果这个Skill帮到了你，请给一个Star！⭐
