#!/usr/bin/env python3
"""
learn_ai.py — Alex AI学习引擎（GitHub Actions版）
==============================================
自动扫描GitHub上最新的AI进展，生成结构化学习报告。

设计哲学：
  - 自包含：不依赖workspace路径，适用于GitHub Actions
  - 6领域覆盖：agent架构 / prompt工程 / memory&RAG / 自进化 / MCP工具 / AI编程
  - 每周产出：每周报告 + 分领域笔记

用法（本地测试）:
  export GITHUB_TOKEN=ghp_xxx
  python3 scripts/learn_ai.py
  
用法（GitHub Actions）:
  自动从 GITHUB_TOKEN 环境变量读取认证
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

# ============================================================
# 配置
# ============================================================

# 搜索领域（分类名 + 搜索查询 + 描述）
LEARNING_CATEGORIES = [
    {
        "id": "agent-architecture",
        "name": "Agent架构",
        "emoji": "🤖",
        "queries": [
            "stars:>500 topic:multi-agent-system sort:updated",
            "stars:>500 topic:ai-agent sort:stars",
            "stars:>200 topic:agent-framework language:python sort:stars",
        ],
        "description": "多Agent系统、Agent框架、编排架构",
    },
    {
        "id": "prompt-engineering",
        "name": "Prompt工程",
        "emoji": "📝",
        "queries": [
            "stars:>300 topic:prompt-engineering sort:stars",
            "stars:>200 topic:prompt-engineering language:python sort:stars",
            "stars:>100 topic:prompt-engineering sort:stars",
        ],
        "description": "Prompt模式、System Prompt设计、结构化提示",
    },
    {
        "id": "memory-rag",
        "name": "Memory & RAG",
        "emoji": "🧠",
        "queries": [
            "stars:>1000 topic:retrieval-augmented-generation sort:stars",
            "stars:>300 topic:ai-memory sort:stars",
            "stars:>200 topic:rag language:python sort:stars",
        ],
        "description": "RAG系统、记忆架构、向量数据库、知识检索",
    },
    {
        "id": "self-improvement",
        "name": "自进化系统",
        "emoji": "🧬",
        "queries": [
            "stars:>100 topic:self-improving sort:stars",
            "stars:>50 topic:ai-self-improvement sort:stars",
            "stars:>10 sort:updated",
            "stars:>100 topic:meta-learning sort:stars",
        ],
        "description": "自我进化、自省、元学习、持续学习",
    },
    {
        "id": "mcp-tools",
        "name": "MCP & 工具生态",
        "emoji": "🔧",
        "queries": [
            "stars:>50 topic:model-context-protocol sort:stars",
            "stars:>100 topic:mcp-server sort:stars",
            "stars:>50 topic:mcp-tools sort:stars",
        ],
        "description": "Model Context Protocol、工具服务器、工具编排",
    },
    {
        "id": "code-ai",
        "name": "AI编程",
        "emoji": "💻",
        "queries": [
            "stars:>5000 topic:ai-code-assistant sort:stars",
            "stars:>1000 topic:code-generation language:python sort:stars",
            "stars:>500 topic:ai-tools language:python sort:stars",
        ],
        "description": "AI编程助手、代码生成、开发工具",
    },
]

# 每个分类最多处理的仓库数
MAX_REPOS_PER_CATEGORY = 10

# 输出目录（仓库根目录的相对路径）
OUTPUT_ROOT = "learnings"
WEEKLY_DIR = f"{OUTPUT_ROOT}/weekly"
CATEGORIES_DIR = f"{OUTPUT_ROOT}/categories"

# Github API
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = [
    "-H", "Accept: application/vnd.github.v3+json",
]
if GITHUB_TOKEN:
    HEADERS += ["-H", f"Authorization: Bearer {GITHUB_TOKEN}"]


# ============================================================
# GitHub API 工具
# ============================================================

def _curl(url):
    """通用curl调用"""
    cmd = ["curl", "-s", "--connect-timeout", "15"] + HEADERS + [url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"_raw": result.stdout[:300]}
    return data


def search_repos(query, sort="stars", order="desc", per_page=10):
    """搜索GitHub公开仓库"""
    encoded_query = query.replace(" ", "+")
    url = f"https://api.github.com/search/repositories?q={encoded_query}&sort={sort}&order={order}&per_page={per_page}"
    data = _curl(url)

    if "message" in data:
        return {"error": data["message"], "total": 0, "items": []}

    items = []
    for item in data.get("items", []):
        items.append({
            "name": item["full_name"],
            "stars": item["stargazers_count"],
            "forks": item["forks_count"],
            "description": (item.get("description") or "")[:150],
            "language": item.get("language"),
            "topics": item.get("topics", [])[:5],
            "updated": item["updated_at"][:10],
            "created": item["created_at"][:10],
            "url": item["html_url"],
        })

    return {
        "total": data.get("total_count", 0),
        "items": items,
    }


def read_raw(owner, repo, path="README.md", branch="main"):
    """通过raw.githubusercontent.com读文件"""
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    result = subprocess.run(
        ["curl", "-s", "--connect-timeout", "10", url],
        capture_output=True, text=True,
    )
    if result.stdout:
        return result.stdout
    # fallback to master
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{path}"
    result = subprocess.run(
        ["curl", "-s", "--connect-timeout", "10", url],
        capture_output=True, text=True,
    )
    return result.stdout


def get_repo_stats(owner, repo):
    """获取仓库统计"""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    data = _curl(url)
    if "message" in data:
        return None
    return {
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "open_issues": data["open_issues_count"],
        "language": data.get("language"),
        "topics": data.get("topics", [])[:5],
        "description": (data.get("description") or "")[:200],
        "pushed_at": data.get("pushed_at", "")[:10],
    }


# ============================================================
# 核心学习引擎
# ============================================================

def scan_category(cat):
    """扫描一个领域的GitHub资源，返回发现列表"""
    cat_id = cat["id"]
    print(f"\n{'─'*60}")
    print(f"🔍 扫描: {cat['emoji']} {cat['name']} ({cat_id})")
    print(f"{'─'*60}")

    all_items = []
    seen = set()

    for i, query in enumerate(cat["queries"], 1):
        print(f"   查询 {i}: » {query}", end="")
        result = search_repos(query, per_page=5)

        if "error" in result:
            print(f"  ❌ {result['error']}")
            continue

        items = result.get("items", [])
        print(f"  → 发现 {len(items)} 个 (总计 {result.get('total', '?')})")

        for item in items:
            if item["name"] not in seen:
                seen.add(item["name"])
                all_items.append(item)

    # 按stars排序，取TOP N
    all_items.sort(key=lambda x: x["stars"], reverse=True)
    top_items = all_items[:MAX_REPOS_PER_CATEGORY]

    # 读取README摘要（对TOP 3深入）
    deep_reads = []
    for item in top_items[:3]:
        owner, repo = item["name"].split("/")
        readme = read_raw(owner, repo)
        summary = _extract_readme_summary(readme)
        deep_reads.append({
            "name": item["name"],
            "readme_summary": summary,
        })

    print(f"   ✅ 精选 {len(top_items)} 个仓库")
    return {
        "category": cat_id,
        "name": cat["name"],
        "emoji": cat["emoji"],
        "description": cat["description"],
        "items": top_items,
        "deep_reads": deep_reads,
    }


def _extract_readme_summary(readme_content):
    """从README中提取关键信息"""
    if not readme_content:
        return "（无README）"

    lines = readme_content.split("\n")
    summary_lines = []
    # 收集标题和第一段有意义的文字
    for line in lines[:60]:
        stripped = line.strip()
        if stripped.startswith("# "):
            summary_lines.append(f"**{stripped}**")
        elif stripped.startswith("## "):
            summary_lines.append(f"_{stripped}_")
        elif stripped and not stripped.startswith("!") and len(stripped) > 20:
            summary_lines.append(stripped[:200])
            if len(summary_lines) >= 5:
                break

    return "\n".join(summary_lines[:8]) or "（摘要提取失败）"


# ============================================================
# 报告生成
# ============================================================

def generate_weekly_report(all_results):
    """生成本周综合学习报告"""
    now = datetime.now(timezone.utc)
    week_num = now.isocalendar().week
    year = now.year
    date_str = now.strftime("%Y-%m-%d")

    lines = []
    lines.append(f"# 🧬 Alex AI学习周报 — {year}年第{week_num}周")
    lines.append(f"")
    lines.append(f"> 自动生成于 {date_str} | 覆盖 {len(all_results)} 个AI领域")
    lines.append(f">")
    lines.append(f"> 数据来源: GitHub Search API | 认证: {'✅ 已认证' if GITHUB_TOKEN else '⚠️ 未认证（30次/小时配额）'}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # 总览表
    lines.append(f"## 📊 本周总览")
    lines.append(f"")
    lines.append(f"| 领域 | 发现数 | 精选数 | 代表性仓库 |")
    lines.append(f"|------|--------|--------|-----------|")

    for result in all_results:
        total = result.get("total_found", len(result["items"]))
        selected = len(result["items"])
        top = result["items"][0]["name"] if result["items"] else "-"
        lines.append(f"| {result['emoji']} {result['name']} | {total} | {selected} | `{top}` |")

    lines.append(f"")

    # 各领域详情
    for result in all_results:
        lines.append(f"---")
        lines.append(f"")
        lines.append(f"## {result['emoji']} {result['name']}")
        lines.append(f"")
        lines.append(f"> {result['description']}")
        lines.append(f"")

        if not result["items"]:
            lines.append(f"*本周未发现新资源*")
            lines.append(f"")
            continue

        # 仓库列表
        lines.append(f"### 📦 精选仓库 ({len(result['items'])}个)")
        lines.append(f"")
        lines.append(f"| 仓库 | ⭐ Stars | 🍴 Forks | 语言 | 描述 |")
        lines.append(f"|------|---------|---------|------|------|")

        for item in result["items"]:
            lang = item.get("language") or "-"
            desc = (item.get("description") or "")[:60]
            lines.append(f"| [{item['name']}]({item['url']}) | {item['stars']:,} | {item['forks']:,} | {lang} | {desc} |")

        lines.append(f"")

        # 深度阅读摘要
        if result.get("deep_reads"):
            lines.append(f"### 📖 深度阅读")
            lines.append(f"")
            for dr in result["deep_reads"]:
                repo_name = dr["name"]
                summary = dr.get("readme_summary", "")[:500]
                lines.append(f"**🔗 [{repo_name}](https://github.com/{repo_name})**")
                if summary:
                    lines.append(f"> {summary}")
                lines.append(f"")

        # 学习要点
        lines.append(f"### 💡 学习要点")
        lines.append(f"")
        insights = _generate_insights(result)
        for insight in insights:
            lines.append(f"- {insight}")
        lines.append(f"")

    lines.append(f"---")
    lines.append(f"")
    lines.append(f"> 🧬 Alex自学习引擎 | [GitHub](https://github.com/pyofart/alex) | 运行于 {date_str}")

    return "\n".join(lines)


def _generate_insights(result):
    """从扫描结果中提炼学习要点"""
    insights = []
    items = result["items"]

    if not items:
        return ["暂无新发现"]

    # 按语言分析
    languages = {}
    for item in items:
        lang = item.get("language") or "Unknown"
        languages[lang] = languages.get(lang, 0) + 1
    top_langs = sorted(languages.items(), key=lambda x: -x[1])[:3]
    insights.append(f"主要技术栈: {', '.join(f'{lang}({count}个)' for lang, count in top_langs)}")

    # 近期活跃
    recent = [i for i in items if i.get("updated", "") >= "2026-06-01"]
    if recent:
        insights.append(f"近期活跃仓库: {len(recent)} 个（近30天有更新）")

    # 描述关键词
    keywords = {}
    for item in items:
        desc = item.get("description", "").lower()
        for kw in ["agent", "framework", "llm", "rag", "prompt", "mcp", "tool", "memory", "learning"]:
            if kw in desc:
                keywords[kw] = keywords.get(kw, 0) + 1
    if keywords:
        top_kws = sorted(keywords.items(), key=lambda x: -x[1])[:5]
        insights.append(f"核心关键词: {', '.join(f'{kw}({count})' for kw, count in top_kws)}")

    return insights


def generate_category_report(result):
    """生成单领域深度报告"""
    cat_id = result["category"]
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    lines = []
    lines.append(f"# {result['emoji']} {result['name']} — AI前沿追踪")
    lines.append(f"")
    lines.append(f"> 最后更新: {date_str} | 数据来源: GitHub")
    lines.append(f"")
    lines.append(f"## 📋 概述")
    lines.append(f"")
    lines.append(f"{result['description']}")
    lines.append(f"")

    if not result["items"]:
        lines.append(f"*暂无数据*")
        return "\n".join(lines)

    lines.append(f"## 📦 精选仓库 ({len(result['items'])}个)")
    lines.append(f"")
    lines.append(f"| # | 仓库 | ⭐ Stars | 📅 更新 | 描述 |")
    lines.append(f"|---|------|---------|--------|------|")

    for i, item in enumerate(result["items"], 1):
        desc = (item.get("description") or "")[:80]
        lines.append(f"| {i} | [{item['name']}]({item['url']}) | {item['stars']:,} | {item.get('updated','')} | {desc} |")

    lines.append(f"")

    if result.get("deep_reads"):
        lines.append(f"## 📖 深度分析")
        lines.append(f"")
        for dr in result["deep_reads"]:
            repo_name = dr["name"]
            owner, repo = repo_name.split("/")
            stats = get_repo_stats(owner, repo)
            lines.append(f"### [{repo_name}](https://github.com/{repo_name})")
            if stats:
                topics = ", ".join(stats.get("topics", [])[:5]) or "无标签"
                lines.append(f"- ⭐ {stats['stars']:,} 🍴 {stats['forks']:,} 🐛 {stats['open_issues']:,} 📅 {stats.get('pushed_at', '')}")
                lines.append(f"- 🏷️ 标签: {topics}")
                lines.append(f"- 📝 {stats.get('description', '')}")
            lines.append(f"")
            summary = dr.get("readme_summary", "")
            if summary:
                lines.append(f"**README要点:**")
                lines.append(f"> {summary[:800]}")
                lines.append(f"")

    lines.append(f"## 🔗 相关资源")
    lines.append(f"")
    lines.append(f"- [GitHub搜索: {result['name']}](https://github.com/search?q={result['category']})")
    lines.append(f"- 更多学习记录: [周报索引](../weekly/)")
    lines.append(f"")

    return "\n".join(lines)


# ============================================================
# 文件写入
# ============================================================

def ensure_dir(path):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)


def write_file(path, content):
    """写入文件（自动创建目录）"""
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ 已写入: {path}")


# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 60)
    print("🧬 Alex AI学习引擎 v1.0")
    print("=" * 60)
    print(f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"🔑 认证: {'✅' if GITHUB_TOKEN else '⚠️ 无Token（30次/小时配额）'}")

    now = datetime.now(timezone.utc)
    week_num = now.isocalendar().week
    year = now.year
    date_str = now.strftime("%Y-%m-%d")
    week_tag = f"{year}-W{week_num:02d}"

    # Step 1: 扫描所有领域
    print(f"\n{'='*60}")
    print(f"📡 阶段一: 扫描 {len(LEARNING_CATEGORIES)} 个AI领域")
    print(f"{'='*60}")

    all_results = []
    for cat in LEARNING_CATEGORIES:
        result = scan_category(cat)
        result["total_found"] = len(result["items"])
        all_results.append(result)

    # Step 2: 生成周报
    print(f"\n{'='*60}")
    print(f"📝 阶段二: 生成周报")
    print(f"{'='*60}")

    weekly_report = generate_weekly_report(all_results)
    weekly_path = f"{WEEKLY_DIR}/{date_str}.md"
    write_file(weekly_path, weekly_report)

    # 同时生成 latest 副本
    latest_weekly_path = f"{WEEKLY_DIR}/latest.md"
    write_file(latest_weekly_path, weekly_report)

    # Step 3: 生成各领域深度报告
    print(f"\n{'='*60}")
    print(f"📖 阶段三: 生成领域深度报告")
    print(f"{'='*60}")

    for result in all_results:
        cat_id = result["category"]
        cat_report = generate_category_report(result)
        cat_md_path = f"{CATEGORIES_DIR}/{cat_id}/{date_str}.md"
        write_file(cat_md_path, cat_report)

        # 更新latest
        cat_latest_path = f"{CATEGORIES_DIR}/{cat_id}/latest.md"
        write_file(cat_latest_path, cat_report)

    # Step 4: 生成索引
    print(f"\n{'='*60}")
    print(f"📑 阶段四: 更新索引")
    print(f"{'='*60}")

    update_index(all_results, week_tag, date_str)

    # 结果汇总
    total_repos = sum(len(r["items"]) for r in all_results)
    print(f"\n{'='*60}")
    print(f"✅ 完成!")
    print(f"  📊 扫描 {len(LEARNING_CATEGORIES)} 个领域")
    print(f"  📦 发现 {total_repos} 个仓库")
    print(f"  📝 周报: {weekly_path}")
    print(f"  📖 领域报告: {len(all_results)} 篇")
    print(f"{'='*60}")

    # 输出摘要用于Actions
    print(f"\n::set-output name=week::{week_tag}")
    print(f"::set-output name=date::{date_str}")
    print(f"::set-output name=repos::{total_repos}")
    print(f"::set-output name=categories::{len(all_results)}")


def update_index(all_results, week_tag, date_str):
    """更新learnings/README.md索引"""
    now = datetime.now(timezone.utc)
    total_repos = sum(len(r["items"]) for r in all_results)

    lines = []
    lines.append(f"# 🧬 Alex AI学习索引")
    lines.append(f"")
    lines.append(f"> GitHub Actions自动扫描 | 最后更新: {date_str}")
    lines.append(f">")
    lines.append(f"> 本目录由 [learn_ai.py](../../scripts/learn_ai.py) 自动维护")
    lines.append(f"")
    lines.append(f"## 📂 目录结构")
    lines.append(f"")
    lines.append(f"```")
    lines.append(f"learnings/")
    lines.append(f"├── README.md           ← 本文件（索引）")
    lines.append(f"├── weekly/             ← 每周综合报告")
    lines.append(f"│   ├── latest.md       ← 最新周报")
    lines.append(f"│   └── YYYY-MM-DD.md   ← 历史周报")
    lines.append(f"└── categories/         ← 分领域深度笔记")
    lines.append(f"    ├── agent-architecture/   🤖 Agent架构")
    lines.append(f"    ├── prompt-engineering/  📝 Prompt工程")
    lines.append(f"    ├── memory-rag/          🧠 Memory & RAG")
    lines.append(f"    ├── self-improvement/    🧬 自进化系统")
    lines.append(f"    ├── mcp-tools/           🔧 MCP & 工具生态")
    lines.append(f"    └── code-ai/             💻 AI编程")
    lines.append(f"```")
    lines.append(f"")

    # 最新周报
    lines.append(f"## 📊 最新周报 — {week_tag}")
    lines.append(f"")
    lines.append(f"| 领域 | 精选仓库 |")
    lines.append(f"|------|---------|")

    for r in all_results:
        count = len(r["items"])
        top = r["items"][0]["name"] if r["items"] else "-"
        lines.append(f"| {r['emoji']} {r['name']} | {count}个 | `{top}` |")

    lines.append(f"")
    lines.append(f"📄 [查看完整周报](weekly/{date_str}.md)")
    lines.append(f"")

    # 领域索引
    lines.append(f"## 🔗 领域入口")
    lines.append(f"")
    for r in all_results:
        cat_id = r["category"]
        lines.append(f"- {r['emoji']} [{r['name']}](categories/{cat_id}/latest.md) — {r['description']}")
    lines.append(f"")

    # 历史周报
    lines.append(f"## 📅 历史周报")
    lines.append(f"")
    lines.append(f"| 周 | 日期 | 链接 |")
    lines.append(f"|---|------|------|")
    lines.append(f"| {week_tag} | {date_str} | [📄](weekly/{date_str}.md) |")
    lines.append(f"")

    lines.append(f"---")
    lines.append(f"> 🤖 由 GitHub Actions 自动维护 · [pyofart/alex](https://github.com/pyofart/alex)")

    write_file(f"{OUTPUT_ROOT}/README.md", "\n".join(lines))


if __name__ == "__main__":
    main()
