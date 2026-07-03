#!/usr/bin/env python3
"""
github_tool.py — GitHub API 搜索与读取工具（增强版）
数据源：api.github.com（Search API + REST）+ raw.githubusercontent.com（文件读取）
策略：Search API(30次/小时)搜仓库/代码 → raw.githubusercontent.com(无限)读内容
认证：使用Bearer Token (pyofart) 提升速率限制
"""

import subprocess, json, sys, os, time

# GitHub Token (Classic, pyofart, 全scope)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "<YOUR_GITHUB_TOKEN>")
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}


def _curl(url, extra_headers=None):
    """通用curl调用，返回JSON或空字符串"""
    cmd = ["curl", "-s", "--connect-timeout", "10"]
    for k, v in HEADERS.items():
        if extra_headers and k in extra_headers:
            continue
        cmd += ["-H", f"{k}: {v}"]
    if extra_headers:
        for k, v in extra_headers.items():
            cmd += ["-H", f"{k}: {v}"]
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return {"_raw": result.stdout[:500]}


def search_repos(query, sort="stars", order="desc", per_page=10):
    """搜索GitHub公开仓库
    
    Args:
        query: 搜索查询（如 'stars:>1000+topic:ai' 或 'machine learning'）
        sort: stars|forks|help-wanted-issues|updated
        order: desc|asc
        per_page: 返回数量(1-100)
    
    Returns:
        dict: {total, items: [{name, stars, forks, description, language, updated, url}]}
    """
    url = f"https://api.github.com/search/repositories?q={query}&sort={sort}&order={order}&per_page={per_page}"
    data = _curl(url)
    
    items = []
    for item in data.get("items", []):
        items.append({
            "name": item["full_name"],
            "stars": item["stargazers_count"],
            "forks": item["forks_count"],
            "watchers": item["watchers_count"],
            "description": (item.get("description") or "")[:120],
            "language": item.get("language"),
            "license": item.get("license", {}).get("name") if item.get("license") else None,
            "topics": item.get("topics", [])[:5],
            "updated": item["updated_at"][:10],
            "created": item["created_at"][:10],
            "url": item["html_url"]
        })
    
    return {
        "total": data.get("total_count", 0),
        "items": items,
        "_quota": _get_quota_remaining()
    }


def search_code(query, per_page=10, repo_filter=None):
    """搜索GitHub代码内容
    
    Args:
        query: 代码搜索查询（如 'def analyze_stock language:Python stars:>100'）
        per_page: 返回数量(1-100)
        repo_filter: 限制仓库（如 'valueinvesting/value-fund'）
    
    Returns:
        dict: {total, items: [{repo, path, name, html_url, snippet}]}
    """
    url = f"https://api.github.com/search/code?q={query}&per_page={per_page}"
    if repo_filter:
        url += f"+repo:{repo_filter}"
    
    data = _curl(url)
    
    items = []
    for item in data.get("items", []):
        items.append({
            "repo": item["repository"]["full_name"],
            "path": item["path"],
            "name": item["name"],
            "html_url": item["html_url"],
            "snippet": _get_code_snippet(item["path"], item["repository"]["full_name"]),
            "stars": item["repository"].get("stargazers_count", 0)
        })
    
    return {
        "total": data.get("total_count", 0),
        "items": items,
        "_quota": _get_quota_remaining()
    }


def _get_code_snippet(repo_full_name, file_path):
    """获取代码文件的简短片段"""
    url = f"https://api.github.com/repos/{repo_full_name}/contents/{file_path}"
    data = _curl(url)
    
    if "content" in data and data.get("encoding") == "base64":
        import base64
        try:
            content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            lines = content.split("\n")
            # 返回前10行
            return "\n".join(lines[:10])
        except:
            return f"[无法解码: {file_path}]"
    return f"[无法获取: {file_path}]"


def read_raw(owner, repo, path="README.md", branch="main"):
    """通过raw.githubusercontent.com读文件（无速率限制）
    
    Args:
        owner: 仓库所有者
        repo: 仓库名
        path: 文件路径
        branch: 分支名(默认main，自动尝试master)
    
    Returns:
        str: 文件内容
    """
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    result = subprocess.run(
        ["curl", "-s", "--connect-timeout", "10", url],
        capture_output=True, text=True
    )
    if result.returncode != 0 or not result.stdout:
        # 尝试 master 分支
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{path}"
        result = subprocess.run(
            ["curl", "-s", "--connect-timeout", "10", url],
            capture_output=True, text=True
        )
    return result.stdout


def get_repo_stats(owner, repo):
    """获取仓库详细统计信息
    
    Returns:
        dict: {name, stars, forks, open_issues, language, license, topics, description, updated, url}
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"
    data = _curl(url)
    
    if "message" in data:
        return {"error": data.get("message", "not found")}
    
    return {
        "name": data["full_name"],
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "open_issues": data["open_issues_count"],
        "language": data.get("language"),
        "primary_language": data.get("language"),
        "license": data.get("license", {}).get("name") if data.get("license") else None,
        "topics": data.get("topics", [])[:10],
        "description": (data.get("description") or "")[:200],
        "size": data.get("size", 0),
        "pushed_at": data.get("pushed_at", "")[:10],
        "created_at": data.get("created_at", "")[:10],
        "updated_at": data.get("updated_at", "")[:10],
        "url": data["html_url"],
        "default_branch": data.get("default_branch", "main")
    }


def check_rate_limit():
    """检查当前API速率限制"""
    result = subprocess.run(
        ["curl", "-s", "--connect-timeout", "5", "https://api.github.com/rate_limit"],
        capture_output=True, text=True
    )
    try:
        data = json.loads(result.stdout)
        r = data.get("resources", {})
        core = r.get("core", {})
        search = r.get("search", {})
        graphql = r.get("graphql", {})
        return {
            "core": f'{core.get("remaining","?")}/{core.get("limit","?")}',
            "search": f'{search.get("remaining","?")}/{search.get("limit","?")}',
            "graphql": f'{graphql.get("remaining","?")}/{graphql.get("limit","?")}'
        }
    except:
        return {"error": "query failed"}


def _get_quota_remaining():
    """快速获取剩余配额"""
    result = subprocess.run(
        ["curl", "-s", "--connect-timeout", "3", "-X", "GET", 
         "https://api.github.com/rate_limit",
         "-H", f"Authorization: Bearer {GITHUB_TOKEN}"],
        capture_output=True, text=True
    )
    try:
        data = json.loads(result.stdout)
        search = data.get("resources", {}).get("search", {})
        return f"{search.get('remaining', '?')}/{search.get('limit', '?')}"
    except:
        return "?"


def format_repos(repos):
    """格式化输出仓库列表"""
    if "error" in repos:
        return f"❌ {repos['error']}"
    
    lines = []
    lines.append(f"📦 总计 {repos.get('total', 0)} 仓库（显示前{len(repos.get('items', []))}个）")
    if repos.get("_quota"):
        lines.append(f"📊 Search配额: {repos['_quota']}")
    lines.append("")
    lines.append(f"{'⭐':>6} {'🍴':>5} {'仓库名':<45} {'语言':<12} {'描述':<50}")
    lines.append("-" * 125)
    
    for r in repos.get("items", []):
        stars = str(r.get('stars', 0))
        forks = str(r.get('forks', 0))
        name = r.get('name', '')[:45]
        lang = str(r.get('language') or '-')[:12]
        desc = (r.get('description') or '')[:50]
        lines.append(f"  {stars:>5} {forks:>5} {name:<45} {lang:<12} {desc:<50}")
    
    return "\n".join(lines)


def format_code_search(results):
    """格式化代码搜索结果"""
    if "error" in results:
        return f"❌ {results['error']}"
    
    lines = []
    lines.append(f"💻 总计 {results.get('total', 0)} 个代码片段（显示前{len(results.get('items', []))}个）")
    if results.get("_quota"):
        lines.append(f"📊 Search配额: {results['_quota']}")
    lines.append("")
    
    for i, item in enumerate(results.get("items", []), 1):
        lines.append(f"{i}. 📁 {item.get('repo', '')}/{item.get('path', '')}")
        lines.append(f"   ⭐ {item.get('stars', 0)} stars")
        lines.append(f"   🔗 {item.get('html_url', '')}")
        snippet = item.get('snippet', '')[:200]
        if snippet:
            lines.append(f"   ```\n   {snippet}\n   ```")
        lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 github_tool.py <action> [参数]")
        print("")
        print("动作:")
        print("  search <查询词> [排序] [数量]    搜索仓库 (默认按stars排序)")
        print("  code <查询词> [数量]             搜索代码片段")
        print("  stats <owner> <repo>             查看仓库统计")
        print("  read <owner> <repo> [path]       读文件(默认README.md)")
        print("  rate                             查当前速率限制")
        print("")
        print("示例:")
        print("  python3 github_tool.py search 'stars:>1000+topic:ai'")
        print("  python3 github_tool.py code 'def analyze_stock language:Python'")
        print("  python3 github_tool.py stats microsoft mcp-for-beginners")
        print("  python3 github_tool.py read valueinvesting value-fund config.yaml")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "search" and len(sys.argv) >= 3:
        query = sys.argv[2]
        sort = sys.argv[3] if len(sys.argv) >= 4 else "stars"
        per_page = int(sys.argv[4]) if len(sys.argv) >= 5 else 10
        repos = search_repos(query, sort=sort, per_page=per_page)
        print(format_repos(repos))
        
    elif action == "code" and len(sys.argv) >= 3:
        query = sys.argv[2]
        per_page = int(sys.argv[3]) if len(sys.argv) >= 4 else 10
        results = search_code(query, per_page=per_page)
        print(format_code_search(results))
        
    elif action == "stats" and len(sys.argv) >= 4:
        owner = sys.argv[2]
        repo = sys.argv[3]
        stats = get_repo_stats(owner, repo)
        if "error" in stats:
            print(f"❌ {stats['error']}")
        else:
            print(f"📊 {stats['name']}")
            print("=" * 60)
            for k, v in stats.items():
                if k not in ("name", "url"):
                    print(f"  {k}: {v}")
            print(f"  url: {stats['url']}")
            
    elif action == "read" and len(sys.argv) >= 4:
        owner = sys.argv[2]
        repo = sys.argv[3]
        path = sys.argv[4] if len(sys.argv) >= 5 else "README.md"
        content = read_raw(owner, repo, path)
        lines = content.split("\n")
        print(f"📖 {owner}/{repo}/{path} ({len(lines)}行)")
        print("=" * 60)
        for line in lines[:100]:
            print(line)
        if len(lines) > 100:
            print(f"... (省略{len(lines)-100}行)")
            
    elif action == "rate":
        rate = check_rate_limit()
        print("📊 GitHub API 速率限制")
        for k, v in rate.items():
            print(f"  {k}: {v}")
    
    else:
        print(f"❌ 未知动作或参数不足: {action}")
