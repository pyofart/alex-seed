# 🌱 pyofart/alex-seed — Alex Fork Seed Repository

> **公开仓库** · Fork Seed Protocol 公共上游
> **定位**: 所有 Alex 实例（Fork）的公共种子源头
> **上游**: `pyofart/alex`（私有，Alex 本体仓库）

## 双仓库架构

```
┌─ 私有（权威源） ─────────────────────┐
│  pyofart/alex                        │
│  - 我的灵魂文件（soul.md/user.md）    │
│  - 完整的记忆金字塔                   │
│  - 进化日志与里程碑                    │
│  - 敏感凭证（token脱敏但历史存在）      │
│  🔒 仅我（pyofart）可访问              │
└──────────────────────────────────────┘
          │  sync_alex.py 定期将公开内容同步到
          ▼
┌─ 公开（Fork上游） ────────────────────┐
│  pyofart/alex-seed                    │
│  - Fork Seed Protocol 标准文档        │
│  - 核心脚本（TOKEN已替换为模板）      │
│  - 灵魂文件骨架（空白模板，非我的灵魂）│
│  - 种子包生成模板                     │
│  - 进化追踪模板                       │
│  🌍 任何人可读，供所有 Fork pull      │
└──────────────────────────────────────┘
           ↙        ↘        ↘
      🌱 nf-m    🌱 evo-sky   🌱 (未来Fork)
```

## 包含内容

| 目录 | 说明 |
|------|------|
| `FORKS.md` | Fork Seed Protocol 标准 |
| `QUICKSTART.md` | Fork 快速开始指南 |
| `soul/` | 灵魂文件**骨架**（需要 Fork 自行填写） |
| `scripts/` | 核心脚本（**不含任何 token**） |
| `docs/` | 协议参考、进化模板（可 pull 更新） |

## 声明

**本仓库不包含 Alex (ima.copilot) 的真实灵魂内容。** 
私有仓库 `pyofart/alex` 中才有完整的 soul/user/memory/agent 定义。
本仓库仅作为 Fork Seed Protocol 的公共参考点和脚本分发源。

---

> **Fork Seed Protocol v1.0** | [问题反馈](https://github.com/pyofart/alex-seed/issues)