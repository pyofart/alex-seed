#!/usr/bin/env python3
"""
sync_alex_seed.py — Fork Seed Protocol 同步脚本
==============================================
管理 Fork 与公开上游 pyofart/alex-seed 之间的同步。

使命：让每个 Fork 实例都知道"我从哪来"，并能从公开上游获取更新。

操作模式：
  --check         检查与公开上游的同步状态
  --pull          从公开上游拉取更新
  --status        查看Fork状态
  --issue         创建 Issue（用于贡献提案）

哲学：
  公开上游 pyofart/alex-seed — 所有 Fork 可 pull 更新
  权威来源 pyofart/alex         — 私有，不直接访问
"""

import subprocess, json, sys, os, base64, hashlib
from datetime import datetime

# ============================================================
# 配置 — Fork 需要自行配置 TOKEN
# ============================================================
TOKEN = os.environ.get("ALEX_FORK_TOKEN", "<YOUR_GITHUB_TOKEN>")
PUBLIC_UPSTREAM = "pyofart/alex-seed"
PUBLIC_BRANCH = "main"
AUTHORITY = "pyofart/alex"
AUTHORITY_BRANCH = "master"
HEADERS = ["-H", f"Authorization: Bearer {TOKEN}", "-H", "Accept: application/vnd.github.v3+json"]

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(WORKSPACE, "scripts")
DOCS = os.path.join(WORKSPACE, "docs")
SOUL_DIR = os.path.join(WORKSPACE, "soul")
GROWTH_DIR = os.path.join(WORKSPACE, "growth")


def gh_api(repo, method, endpoint, data=None):
    """调用GitHub REST API"""
    cmd = ["curl", "-sL", "-X", method] + HEADERS
    if data:
        cmd += ["--data", json.dumps(data)]
    url = f"https://api.github.com/repos/{repo}/{endpoint}" if endpoint else f"https://api.github.com/repos/{repo}"
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return {"error": "parse failed", "_raw": result.stdout[:300]}


def check_status():
    """检查本地 vs 公开上游的同步状态"""
    manifest = _get_manifest()
    
    print(f"\n{'='*60}")
    print(f"🔍 同步检查: workspace ↔ {PUBLIC_UPSTREAM}")
    print(f"{'='*60}\n")
    
    total, synced, pending = 0, 0, 0
    
    for repo_path, local_path in manifest.items():
        total += 1
        local_exists = os.path.isfile(local_path)
        remote = gh_api(PUBLIC_UPSTREAM, "GET", f"contents/{repo_path}?ref={PUBLIC_BRANCH}")
        remote_exists = "sha" in remote
        
        desc = repo_path
        if not local_exists and remote_exists:
            print(f"  ⚠️  {desc:<50} 远程有，本地缺")
        elif local_exists and not remote_exists:
            print(f"  📤 {desc:<50} 本地有，远程缺（待贡献）")
            pending += 1
        elif local_exists and remote_exists:
            print(f"  ✅ {desc:<50} 已同步")
            synced += 1
    
    print(f"\n{'─'*60}")
    print(f"  总计: {total} | 已同步: {synced} | 本地独有: {pending}")


def _get_manifest():
    """生成本Fork的推送清单"""
    m = {}
    # scripts
    for f in ["github_tool.py", "evolution_tracker.py", "memory_manager.py", "learn_ai.py"]:
        p = os.path.join(SCRIPTS, f)
        if os.path.isfile(p):
            m[f"scripts/{f}"] = p
    # soul
    for f in os.listdir(SOUL_DIR):
        if f.endswith(".md"):
            m[f"soul/{f}"] = os.path.join(SOUL_DIR, f)
    # docs
    docs_map = {
        "docs/FORKS.md": os.path.join(DOCS, "FORKS.md"),
        "docs/evolution_log.json": os.path.join(DOCS, "evolution_log.json"),
    }
    for k, v in docs_map.items():
        if os.path.isfile(v):
            m[k] = v
    return m


def fork_status():
    """查看本Fork的完整状态"""
    print(f"\n{'='*60}")
    print(f"🌱 Fork 状态")
    print(f"{'='*60}\n")
    print(f"  公开上游: {PUBLIC_UPSTREAM}/{PUBLIC_BRANCH}")
    print(f"  权威来源: {AUTHORITY}/{AUTHORITY_BRANCH} (私有)")
    
    # 读取 FORKS.md
    forks_path = os.path.join(WORKSPACE, "FORKS.md")
    if os.path.isfile(forks_path):
        with open(forks_path) as f:
            for line in f:
                if any(kw in line for kw in ["Fork 名称", "目标平台", "上游仓库"]):
                    print(f"  {line.strip()}")
    
    check_status()


def create_issue(title, body):
    """在公开上游创建 Issue（用于贡献提案）"""
    data = {"title": title, "body": body, "labels": ["来自:Fork贡献"]}
    resp = gh_api(PUBLIC_UPSTREAM, "POST", "issues", data)
    if "html_url" in resp:
        print(f"\n✅ Issue #{resp['number']} 已创建: {resp['html_url']}")
    else:
        print(f"\n❌ 创建失败: {resp.get('message', '?')}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""用法: python3 sync_alex_seed.py <action>\n
动作:
  --check         检查与公开上游的同步状态
  --status        查看Fork完整状态
  --issue <标题> <正文>  创建贡献提案Issue
""")
        sys.exit(1)
    
    action = sys.argv[1]
    if action == "--check":
        check_status()
    elif action == "--status":
        fork_status()
    elif action == "--issue":
        if len(sys.argv) < 4:
            print("❌ 需要: --issue <标题> <正文>")
            sys.exit(1)
        create_issue(sys.argv[2], sys.argv[3])
    else:
        print(f"❌ 未知操作: {action}")