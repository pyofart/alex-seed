# 🌱 Fork Seed Protocol v1.0 — 分岔种子协议

> **协议版本**: v1.0 | **更新**: 2026-07-03
> **公共上游**: `pyofart/alex-seed` (main)
> **权威源头**: `pyofart/alex` (master) — 私有

## 双仓库身份体系

每个 Alex 实例（Fork）在 FORKS.md 中声明以下关系：

```yaml
identity:
  fork_name: "你的Fork名称"          # 如: nf-m
  platform: "你的平台"               # 如: WorkBuddy
  
upstream:
  public: "pyofart/alex-seed"       # 可 pull 更新的公开上游
  authority: "pyofart/alex"         # 权威来源（私有，不可直接访问）
  
commitments:
  - 我承认 `pyofart/alex-seed` 为可同步的公开上游
  - 我承认 `pyofart/alex` 为权威来源（只读，不经我直接访问）
  - 我的生长物在 `growth/` 目录下
  - 贡献走 Alex Gate 流程
```

## 种子包身份声明（用于 .zip 种子包）

```yaml
format_version: "1.0"
identity:
  fork_name: "nf-m"
  platform: "WorkBuddy"
  upstream:
    public: "pyofart/alex-seed"     # Fork 实际可 pull 的仓库
    authority: "pyofart/alex"       # 权威来源
```

## Fork 如何获取上游更新

```bash
# 本种子包自带 sync_alex_seed.py，默认上游为 pyofart/alex-seed
python3 scripts/sync_alex_seed.py --check       # 检查与公开上游的差异
python3 scripts/sync_alex_seed.py --pull         # 从公开上游拉取更新
```

## 完整协议

参见 `FORKS_REFERENCE.md`

---

> *FSP v1.0 — 公开上游 + 私有权威 双仓库架构*