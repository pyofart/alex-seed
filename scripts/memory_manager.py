#!/usr/bin/env python3
"""
memory_manager.py — Alex 记忆层管理 v3.0
=======================================
L1事实层 + L2场景层 + L0 QA轻量持久化 + Ingest自动化

命令:
  status               查看金字塔全貌
  fact list/create     管理L1事实
  scene list/create    管理L2场景
  search <关键词>      跨层搜索
  evolve               从evolution_log提取事实
  ingest <type> <标题> <正文>  自动化知识吸收（创建事实/场景+更新索引+追加日志）
  qa add/search/list   管理L0对话层
"""

import sys, os, json, glob, re
from datetime import datetime

BASE = os.path.join(os.path.dirname(__file__), "..", "docs", "memory")
FACTS_DIR = os.path.join(BASE, "l1-facts")
SCENES_DIR = os.path.join(BASE, "l2-scenes")
QA_DIR = os.path.join(BASE, "l0-qa")
INDEX_FILE = os.path.join(BASE, "index.md")
LOG_FILE = os.path.join(BASE, "log.md")
EVO_LOG = os.path.join(os.path.dirname(__file__), "..", "docs", "evolution_log.json")
SOUL_DIR = os.path.join(os.path.dirname(__file__), "..", "soul")


def ensure_dirs():
    for d in [FACTS_DIR, SCENES_DIR, QA_DIR]:
        os.makedirs(d, exist_ok=True)


def slugify(text):
    return "".join(c if c.isalnum() else "-" for c in text.lower()).strip("-")[:50]


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


# ============================================================
# L1: 事实层
# ============================================================

def create_fact(title, body, tags=None):
    ensure_dirs()
    tags = tags or []
    slug = slugify(title)
    fname = f"{slug}.md"
    fpath = os.path.join(FACTS_DIR, fname)
    content = f"""---
title: {title}
type: fact
created: {now_str()}
tags: [{', '.join(tags)}]
---
# {title}

{body}

---
*L1事实层 · 原子级跨会话知识*
"""
    with open(fpath, "w") as f:
        f.write(content)
    print(f"✅ L1事实已创建: {fname}")
    return fpath


def list_facts():
    ensure_dirs()
    files = sorted(glob.glob(os.path.join(FACTS_DIR, "*.md")))
    if not files:
        print("  📭 L1无事实记录")
        return []
    print(f"\n📋 L1 事实层 ({len(files)}条)")
    print("-" * 60)
    for f in files:
        name = os.path.basename(f).replace(".md", "")
        with open(f, "r") as fh:
            lines = fh.readlines()
        title = name.replace("-", " ").title()
        preview = ""
        for l in lines:
            l = l.strip()
            if l.startswith("title: "):
                title = l.replace("title: ", "", 1)
            elif l and not l.startswith("---") and not l.startswith("type:") and not l.startswith("created:") and not l.startswith("tags:") and not l.startswith("*L"):
                preview = l[:80]
                break
        print(f"  📄 {title:<50} {preview[:50]}")
    return files


# ============================================================
# L2: 场景层
# ============================================================

def create_scene(title, body, tags=None):
    ensure_dirs()
    tags = tags or []
    slug = slugify(title)
    fname = f"{slug}.md"
    fpath = os.path.join(SCENES_DIR, fname)
    content = f"""---
title: {title}
type: scene
created: {now_str()}
tags: [{', '.join(tags)}]
wikilinks: []
---
# {title}

{body}

---
*L2场景层 · 跨会话可复用经验块*
"""
    with open(fpath, "w") as f:
        f.write(content)
    print(f"✅ L2场景已创建: {fname}")
    return fpath


def list_scenes():
    ensure_dirs()
    files = sorted(glob.glob(os.path.join(SCENES_DIR, "*.md")))
    if not files:
        print("  📭 L2无场景记录")
        return []
    print(f"\n📋 L2 场景层 ({len(files)}条)")
    print("-" * 60)
    for f in files:
        name = os.path.basename(f).replace(".md", "")
        with open(f, "r") as fh:
            lines = fh.readlines()
        title = name.replace("-", " ").title()
        preview = ""
        for l in lines:
            l = l.strip()
            if l.startswith("title: "):
                title = l.replace("title: ", "", 1)
            elif l and not l.startswith("---") and not l.startswith("type:") and not l.startswith("created:") and not l.startswith("tags:") and not l.startswith("wikilinks:") and not l.startswith("*L"):
                preview = l[:80]
                break
        print(f"  📄 {title:<50} {preview[:50]}")
    return files


# ============================================================
# L0: QA轻量持久化层
# ============================================================

def get_session_qa_file():
    """获取当前会话的QA文件路径"""
    ensure_dirs()
    date = today_str()
    return os.path.join(QA_DIR, f"{date}-session.md")


def qa_add(question, answer, tags=None):
    """添加一条QA到当前会话"""
    ensure_dirs()
    tags = tags or []
    qa_file = get_session_qa_file()
    now = now_str()
    
    entry = f"""
## Q: {question}

**A**: {answer}

*{now} | tags: {', '.join(tags) if tags else '—'}*
"""
    # 如果文件不存在，加header
    if not os.path.isfile(qa_file):
        header = f"""# L0 QA · {today_str()}

> 日常会话中的关键问答留存
>
"""
        with open(qa_file, "w") as f:
            f.write(header)
    
    with open(qa_file, "a") as f:
        f.write(entry)
    
    print(f"✅ QA已存档: {question[:50]}...")
    return qa_file


def qa_list(limit=10):
    """列出最近N条QA"""
    ensure_dirs()
    files = sorted(glob.glob(os.path.join(QA_DIR, "*.md")), reverse=True)
    if not files:
        print("  📭 L0无QA记录")
        return
    
    print(f"\n💬 L0 QA层 (最近{limit}条)")
    print("-" * 60)
    count = 0
    for f in files:
        name = os.path.basename(f).replace("-session.md", "")
        with open(f, "r") as fh:
            content = fh.read()
        qas = re.findall(r'## Q: (.*?)\n\n\*\*A\*\*: (.*?)\n', content)
        for q, a in qas[:limit]:
            print(f"  💬 [{name}] Q: {q[:60]}")
            print(f"         A: {a[:80]}")
            count += 1
            if count >= limit:
                return


def qa_search(query):
    """搜索QA记录"""
    ensure_dirs()
    results = []
    for f in sorted(glob.glob(os.path.join(QA_DIR, "*.md"))):
        with open(f, "r") as fh:
            content = fh.read()
        if query.lower() in content.lower():
            qas = re.findall(r'## Q: (.*?)\n\n\*\*A\*\*: (.*?)\n', content)
            for q, a in qas:
                if query.lower() in q.lower() or query.lower() in a.lower():
                    results.append((f, q[:80], a[:120]))
    
    if not results:
        print(f"🔍 未找到包含 \"{query}\" 的QA记录")
        return
    print(f"\n🔍 搜索 \"{query}\" — 找到 {len(results)} 条QA")
    print("-" * 60)
    for f, q, a in results:
        date = os.path.basename(f).replace("-session.md", "")
        print(f"  💬 [{date}] Q: {q}")
        print(f"         A: {a}")


# ============================================================
# Ingest: 自动化知识吸收
# ============================================================

def ingest(type_, title, body, tags=None):
    """自动化知识吸收：创建记录 + 更新索引 + 追加日志
    
    Args:
        type_: 'fact' | 'scene' | 'qa'
        title: 标题
        body: 正文
        tags: 标签列表
    """
    ensure_dirs()
    tags = tags or []
    now = now_str()
    today = today_str()
    
    # Step 1: 创建记录
    if type_ == "fact":
        fpath = create_fact(title, body, tags)
        page_type = "L1事实"
        link = f"l1-facts/{slugify(title)}.md"
    elif type_ == "scene":
        fpath = create_scene(title, body, tags)
        page_type = "L2场景"
        link = f"l2-scenes/{slugify(title)}.md"
    elif type_ == "qa":
        fpath = qa_add(title, body, tags)
        print(f"  (QA已存档到 {os.path.basename(fpath)})")
        return fpath  # QA不更新索引和日志（太频繁）
    else:
        print(f"❌ 未知类型: {type_}，支持: fact|scene|qa")
        return None
    
    slug = slugify(title)
    
    # Step 2: 更新 index.md
    tag_str = ", ".join(tags) if tags else "-"
    today = today_str()
    
    # 找到对应层级的表格区域并插入新行
    if os.path.isfile(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # 确定插入点：在对应表格的最后一行之后
        section_marker = f"## {page_type == 'L2场景' and 'L2 场景层' or 'L1 事实层'}"
        if page_type == "L2场景":
            section_marker = "## L2 场景层"
        else:
            section_marker = "## L1 事实层"
        
        insert_idx = -1
        found_section = False
        for idx, line in enumerate(lines):
            if section_marker in line:
                found_section = True
            if found_section and line.strip().startswith("| ["):
                insert_idx = idx + 1  # after this row
        
        if insert_idx >= 0:
            if page_type == "L1事实":
                new_row = f"| [{title}]({link}) | `{tag_str}` | {today} | - | {body[:60]} |\n"
            else:
                new_row = f"| [{title}]({link}) | `{tag_str}` | {today} | {body[:60]} |\n"
            
            # 检查是否已存在
            if f"({link})" not in "".join(lines):
                lines.insert(insert_idx, new_row)
                with open(INDEX_FILE, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                print(f"  📑 index.md 已更新")
            else:
                print(f"  📑 index.md 已有条目，跳过")
        else:
            print(f"  ⚠️ 未找到{table_name}表格区域，跳过index更新")
    else:
        print(f"  ⚠️ index.md 不存在，跳过更新")
    
    # Step 3: 追加到 log.md
    log_entry = f"\n## [{today}] ingest | {title}\n- 类型: {page_type}\n- 标签: {tag_str}\n- 文件: {link}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)
    print(f"  📝 log.md 已追加")
    
    print(f"\n✅ Ingest完成: {page_type} → {slug}.md + index.md + log.md")
    return fpath


# ============================================================
# 搜索（跨L0+L1+L2）
# ============================================================

def search_all(query):
    """跨L0+L1+L2层搜索"""
    ensure_dirs()
    results = []
    
    # L1 + L2
    for layer_dir, layer_name in [(FACTS_DIR, "L1事实"), (SCENES_DIR, "L2场景")]:
        for f in sorted(glob.glob(os.path.join(layer_dir, "*.md"))):
            with open(f, "r") as fh:
                content = fh.read()
            if query.lower() in content.lower():
                name = os.path.basename(f).replace(".md", "")
                results.append((layer_name, name, content[:120]))
    
    # L0 QA
    for f in sorted(glob.glob(os.path.join(QA_DIR, "*.md"))):
        with open(f, "r") as fh:
            content = fh.read()
        if query.lower() in content.lower():
            qas = re.findall(r'## Q: (.*?)\n', content)
            for q in qas[:3]:
                results.append(("L0 QA", q[:60], f"{os.path.basename(f)}"))
    
    if not results:
        print(f"🔍 未找到包含 \"{query}\" 的记忆")
        return
    
    print(f"\n🔍 搜索 \"{query}\" — 找到 {len(results)} 条")
    print("-" * 60)
    for layer, name, preview in results:
        print(f"  [{layer}] {name}")
        print(f"    {preview.strip()}")


# ============================================================
# 状态总览（含L0 QA）
# ============================================================

def show_status():
    print(f"\n{'='*60}")
    print(f"🧠 Alex 记忆金字塔")
    print(f"{'='*60}")
    
    # L3
    soul_files = glob.glob(os.path.join(SOUL_DIR, "*.md")) if os.path.isdir(SOUL_DIR) else []
    print(f"\n🏛️  L3 人格层 (soul/)")
    print(f"{'─'*60}")
    if soul_files:
        for f in soul_files:
            name = os.path.basename(f)
            print(f"  📄 {name}")
    else:
        print(f"  📄 (平台记忆系统加载)")
    
    # L2
    scene_files = sorted(glob.glob(os.path.join(SCENES_DIR, "*.md")))
    print(f"\n🏘️  L2 场景层 (l2-scenes/)")
    print(f"{'─'*60}")
    for f in scene_files:
        name = os.path.basename(f).replace(".md", "")
        print(f"  📄 {name}")
    if not scene_files:
        print(f"  📭 空")
    
    # L1
    fact_files = sorted(glob.glob(os.path.join(FACTS_DIR, "*.md")))
    print(f"\n🔬 L1 事实层 (l1-facts/)")
    print(f"{'─'*60}")
    for f in fact_files:
        name = os.path.basename(f).replace(".md", "")
        print(f"  📄 {name}")
    if not fact_files:
        print(f"  📭 空")
    
    # L0
    qa_files = sorted(glob.glob(os.path.join(QA_DIR, "*.md")))
    qa_count = 0
    for f in qa_files:
        with open(f, "r") as fh:
            content = fh.read()
        qa_count += len(re.findall(r'## Q:', content))
    print(f"\n💬 L0 对话层 (l0-qa/)")
    print(f"{'─'*60}")
    print(f"  📄 {len(qa_files)} 个会话文件, {qa_count} 条QA")
    
    print(f"\n{'='*60}")
    print(f"总计: L3:{len(soul_files)} + L2:{len(scene_files)} + L1:{len(fact_files)} + L0:{qa_count}条QA")
    print(f"{'='*60}\n")


# ============================================================
# 从 evolution_log 自动提取事实
# ============================================================

def evolve_from_log():
    if not os.path.exists(EVO_LOG):
        print("❌ 无进化日志")
        return
    with open(EVO_LOG, "r") as f:
        try:
            log = json.load(f)
        except:
            print("❌ 日志格式错误")
            return
    
    print(f"\n🧬 从进化日志提取L1事实 ({len(log)}条)...")
    count = 0
    for entry in log:
        cap = entry.get("capability", entry.get("module", "?"))
        ct = entry.get("change_type", "?")
        learned = entry.get("what_i_learned", entry.get("description", ""))
        if learned and len(learned) > 20 and cap != "?":
            # 直接用 ingest 写入（含索引+日志更新）
            ingest("fact",
                   f"进化:{cap}",
                   f"**类型**: {ct}\n**学到**: {learned}\n**时间**: {entry.get('timestamp','')[:10]}",
                   ["auto-extract", ct])
            count += 1
    
    if count:
        print(f"\n✅ 提取 {count} 条L1事实")
    else:
        print("  无需提取")


# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""
用法: python3 memory_manager.py <action> [参数]

🧠 Alex 记忆层管理 v3.0

动作:
  status                    查看记忆金字塔全貌
  fact list                 列出L1事实
  fact create <标题> <正文>  创建L1事实
  scene list                列出L2场景
  scene create <标题> <正文> 创建L2场景
  search <关键词>            跨L0+L1+L2搜索
  evolve                    从evolution_log自动提取L1事实

  ingest <type> <标题> <正文>  [标签...]  自动化知识吸收
    type: fact | scene | qa
    自动: 创建记录 → 更新index.md → 追加log.md

  qa add <问题> <答案> [标签...]    留存关键问答
  qa list [数量]                    列出最近QA
  qa search <关键词>               搜索QA记录

基于 4层金字塔:
  L3 soul/   = 人格层
  L2 scenes/ = 场景层
  L1 facts/  = 事实层
  L0 qa/     = 对话层（新增）
""")
        sys.exit(1)

    action = sys.argv[1]

    if action == "status":
        show_status()

    elif action == "fact":
        sub = sys.argv[2] if len(sys.argv) >= 3 else "list"
        if sub == "list":
            list_facts()
        elif sub == "create" and len(sys.argv) >= 5:
            title = sys.argv[3]
            body = sys.argv[4]
            tags = sys.argv[5:] if len(sys.argv) > 5 else []
            create_fact(title, body, tags)
        else:
            print("❌ 用法: fact create <标题> <正文> [标签...]")

    elif action == "scene":
        sub = sys.argv[2] if len(sys.argv) >= 3 else "list"
        if sub == "list":
            list_scenes()
        elif sub == "create" and len(sys.argv) >= 5:
            title = sys.argv[3]
            body = sys.argv[4]
            tags = sys.argv[5:] if len(sys.argv) > 5 else []
            create_scene(title, body, tags)
        else:
            print("❌ 用法: scene create <标题> <正文> [标签...]")

    elif action == "ingest":
        if len(sys.argv) < 5:
            print("❌ 用法: ingest <type> <标题> <正文> [标签...]")
            sys.exit(1)
        type_ = sys.argv[2]
        title = sys.argv[3]
        body = sys.argv[4]
        tags = sys.argv[5:] if len(sys.argv) > 5 else []
        ingest(type_, title, body, tags)

    elif action == "qa":
        sub = sys.argv[2] if len(sys.argv) >= 3 else "list"
        if sub == "add" and len(sys.argv) >= 5:
            q = sys.argv[3]
            a = sys.argv[4]
            tags = sys.argv[5:] if len(sys.argv) > 5 else []
            qa_add(q, a, tags)
        elif sub == "list":
            limit = int(sys.argv[3]) if len(sys.argv) >= 4 else 10
            qa_list(limit)
        elif sub == "search" and len(sys.argv) >= 4:
            qa_search(" ".join(sys.argv[3:]))
        else:
            print("❌ 用法: qa add <问题> <答案> [标签...] | list [数量] | search <关键词>")

    elif action == "search":
        if len(sys.argv) >= 3:
            search_all(" ".join(sys.argv[2:]))
        else:
            print("❌ 用法: search <关键词>")

    elif action == "evolve":
        evolve_from_log()

    else:
        print(f"❌ 未知操作: {action}")
