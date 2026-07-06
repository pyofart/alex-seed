#!/usr/bin/env python3
"""
seed-pack.py — Fork Seed Protocol 种子打包脚本
===========================================
将 Fork 工作区打包为可分发的种子包（.zip）。
与 sync_alex_seed.py 互补：一个负责拉取更新，一个负责打包分发。

操作模式：
  --check         检查种子清单
  --pack [路径]   打包为种子包（默认 output/alex-seed-YYYY-MM-DD.zip）
  --manifest      打印当前清单定义

安全设计：
  - 自动检测并排除含 GitHub PAT 的文件（ghp_ + 36位字母数字）
  - 清单明确指定，不扫描整个工作区
  - 不含任何凭证信息

哲学：
  种子包是 Fork 的"可播种快照"——让另一个平台能完整恢复一份 Alex 实例。
"""
import re, json, os, sys, zipfile
from datetime import date

# ============================================================
# 配置
# ============================================================
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUTPUT_DIR = os.path.join(WORKSPACE, "output")

# 种子清单——只打包明确列出的路径，不扫描整个工作区
MANIFEST = {
    "FORKS.md": "FORKS.md",
    "QUICKSTART.md": "QUICKSTART.md",
    "README.md": "README.md",
    "scripts/sync_alex_seed.py": "scripts/sync_alex_seed.py",
    "scripts/seed-pack.py": "scripts/seed-pack.py",
    "scripts/evolution_tracker.py": "scripts/evolution_tracker.py",
    "scripts/memory_manager.py": "scripts/memory_manager.py",
    "scripts/github_tool.py": "scripts/github_tool.py",
    "scripts/learn_ai.py": "scripts/learn_ai.py",
    "soul/soul.example.md": "soul/soul.example.md",
    "soul/user.example.md": "soul/user.example.md",
    "soul/agent.example.md": "soul/agent.example.md",
    "soul/memory.example.md": "soul/memory.example.md",
    "docs/evolution_log.json": "docs/evolution_log.json",
}

# GitHub PAT 正则：ghp_ + 36位以上字母数字
GH_PAT_RE = re.compile(r"ghp_[A-Za-z0-9]{36,}")

# 可选的 excludes：路径模式黑名单（在清单基础上额外过滤）
EXCLUDES = ["scripts/<YOUR_GITHUB_TOKEN>"]


def _has_token(path):
    """检查文件是否包含 GitHub Personal Access Token"""
    try:
        with open(path) as f:
            content = f.read()
        return bool(GH_PAT_RE.search(content))
    except Exception:
        return False


def collect():
    """收集清单中的所有有效文件，排除含 token 的文件"""
    files = []
    skipped = []
    for arcname, relpath in MANIFEST.items():
        full = os.path.join(WORKSPACE, relpath)
        if not os.path.isfile(full):
            skipped.append((arcname, "文件不存在"))
            continue
        if _has_token(full):
            skipped.append((arcname, "包含 Token，已排除"))
            continue
        files.append((arcname, full))
    return files, skipped


def pack(output=None):
    """打包种子包"""
    if not output:
        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        output = os.path.join(DEFAULT_OUTPUT_DIR, f"alex-seed-{date.today()}.zip")

    files, skipped = collect()
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for arcname, full in files:
            zf.write(full, arcname)

    # 输出报告
    print(f"\n{'='*60}")
    print(f"📦 种子包: {output}")
    print(f"{'='*60}\n")
    print(f"  已打包: {len(files)} 文件")
    for arcname, _ in sorted(files):
        print(f"    ✅ {arcname}")
    if skipped:
        print(f"\n  已跳过: {len(skipped)}")
        for name, reason in skipped:
            print(f"    ⚠️  {name:40s} — {reason}")
    print(f"\n  总大小: {os.path.getsize(output):,} 字节")
    print()


def check():
    """检查种子清单状态"""
    files, skipped = collect()
    total = len(MANIFEST)

    print(f"\n{'='*60}")
    print(f"🔍 种子清单检查")
    print(f"{'='*60}\n")
    print(f"  清单总计: {total} 条目")
    print(f"  有效文件: {len(files)}")
    print(f"  已跳过: {len(skipped)}\n")

    for arcname, relpath in MANIFEST.items():
        full = os.path.join(WORKSPACE, relpath)
        if not os.path.isfile(full):
            print(f"    ❌ {arcname:45s} 缺失")
        elif _has_token(full):
            print(f"    🔒 {arcname:45s} 含 Token 已锁定")
        else:
            size = os.path.getsize(full)
            print(f"    ✅ {arcname:45s} {size:>8,} B")


def print_manifest():
    """打印当前清单定义"""
    print(f"\n📋 种子清单定义 ({len(MANIFEST)} 条目):\n")
    for arcname, relpath in sorted(MANIFEST.items()):
        print(f"  {arcname:45s} ← {relpath}")
    print(f"\n排除规则: GH PAT 检测 + {len(EXCLUDES)} 路径黑名单")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""用法: python3 seed-pack.py <动作>

动作:
  --check             检查种子清单状态
  --pack [输出路径]   打包种子包
  --manifest          打印当前清单定义
""")
        sys.exit(1)

    action = sys.argv[1]
    if action == "--check":
        check()
    elif action == "--pack":
        pack(sys.argv[2] if len(sys.argv) > 2 else None)
    elif action == "--manifest":
        print_manifest()
    else:
        print(f"❌ 未知操作: {action}")