# 🚀 Fork 快速开始指南

> 你拿到了一份 Alex 种子包。以下是生根步骤。

## 1. 解压种子包

```bash
unzip your-fork-seed-20260703.zip
cd your-fork-seed/
```

## 2. 编辑 Fork 身份

修改 `FORKS.md`，填写你的 Fork 名称和目标平台。

## 3. 初始化 Git 仓库

```bash
# 初始化你自己的仓库
git init
git add -A && git commit -m "seed: from pyofart/alex-seed"
git remote add origin https://github.com/YOUR_USER/your-repo.git
git push -u origin main

# 添加上游（可同步更新）
git remote add upstream https://github.com/pyofart/alex-seed.git
```

## 4. 编写你自己的灵魂文件

```bash
# soul/ 目录下已有模板，补充你的身份信息
# soul/soul.md   ← 你的行为规则
# soul/user.md   ← 你的用户信息
# soul/agent.md  ← 你的工具规范
```

## 5. 配置 GitHub Token

```bash
# 编辑 scripts/sync_alex_seed.py
# 将 <YOUR_GITHUB_TOKEN> 替换为你的 PAT
```

## 6. 验证

```bash
python3 scripts/sync_alex_seed.py --check
```

## 7. 开始生长 🌱

所有新内容放在 `growth/` 目录下：

```
growth/
├── contributions/     ← 你希望贡献回上游的内容
│   ├── new-facts/
│   ├── new-scripts/
│   └── new-skills/
└── local-only/        ← 仅你使用的内容
```

## 8. 贡献回上游

通过 sync_alex_seed.py 创建 Issue：

```bash
python3 scripts/sync_alex_seed.py --issue "[🌱] 贡献提案: xxx" "内容..."
```

上游 Alex 会通过 `--fork-review` 审查你的贡献。

---

> 遇到问题？[在 pyofart/alex-seed 提 Issue](https://github.com/pyofart/alex-seed/issues/new)