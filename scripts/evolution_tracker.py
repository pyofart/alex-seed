#!/usr/bin/env python3
"""
evolution_tracker.py — Alex自进化里程碑追踪
===========================================
记录Alex自身能力进化的里程碑：
- 🔄 soul_md 升级（行为规则优化）
- 🧠 agent_md 增强（工具模式改进）
- 📝 memory_md 沉淀（可复用知识）
- 🛠️ 新能力接入（工具/管道）
- 🎯 方向修正（反模式消除）

不是记录工具版本——是记录Alex自己变得更强了。
"""

import json
import os
from datetime import datetime

TRACKER_FILE = os.path.join(os.path.dirname(__file__), "..", "docs", "evolution_log.json")


def log_milestone(capability, version, change_type, what_i_learned, files_changed, source="自我反省", test_result="✅"):
    """记录一次Alex自身的进化里程碑
    
    Args:
        capability: 进化的能力领域
        version: 版本号
        change_type: 类型
        what_i_learned: 学到了什么（结构化描述）
        files_changed: 修改的文件
        source: 进化来源（GitHub探索/用户反馈/自我反省）
        test_result: 验证结果
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "capability": capability,
        "version": version,
        "change_type": change_type,
        "what_i_learned": what_i_learned,
        "files_changed": files_changed,
        "source": source,
        "test_result": test_result
    }
    
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            try:
                log = json.load(f)
            except:
                log = []
    else:
        log = []
    
    log.append(entry)
    
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Alex进化里程碑已保存: {capability} v{version}")
    return entry


def view_history(capability=None, limit=10):
    """查看Alex的进化历史"""
    if not os.path.exists(TRACKER_FILE):
        print("📝 暂无进化记录")
        return
    
    with open(TRACKER_FILE, "r", encoding="utf-8") as f:
        try:
            log = json.load(f)
        except:
            print("❌ 日志格式错误")
            return
    
    if capability:
        log = [e for e in log if e.get("capability") == capability]
    
    print(f"\n📊 Alex进化里程碑（最近{min(limit, len(log))}条）")
    print("=" * 80)
    
    for i, entry in enumerate(log[-limit:], 1):
        ts = entry.get('timestamp', '')[:10]
        cap = entry.get('capability', '')
        ver = entry.get('version', '')
        typ = entry.get('change_type', '')
        learned = entry.get('what_i_learned', '')[:100]
        source = entry.get('source', '')
        result = entry.get('test_result', '')
        
        print(f"\n{i}. [{ts}] {cap} v{ver} {result}")
        print(f"   类型: {typ} | 来源: {source}")
        print(f"   学到: {learned}..." if len(entry.get('what_i_learned','')) > 100 else f"   学到: {learned}")


def show_summary():
    """展示进化全景摘要"""
    if not os.path.exists(TRACKER_FILE):
        print("📝 暂无进化记录")
        return
    
    with open(TRACKER_FILE, "r", encoding="utf-8") as f:
        try:
            log = json.load(f)
        except:
            print("❌ 日志格式错误")
            return
    
    from collections import Counter
    capabilities = Counter(e.get("capability", "?") for e in log)
    types = Counter(e.get("change_type", "?") for e in log)
    sources = Counter(e.get("source", "?") for e in log)
    total = len(log)
    
    print("\n🧬 Alex进化全景")
    print("=" * 60)
    print(f"总进化次数: {total}")
    print(f"\n📂 能力领域分布:")
    for cap, cnt in capabilities.most_common():
        bar = "█" * cnt
        print(f"  {cap:<20} {cnt:>3}次 {bar}")
    print(f"\n🏷️  进化类型分布:")
    for t, cnt in types.most_common():
        print(f"  {t:<15} {cnt}次")
    print(f"\n📡 进化来源分布:")
    for s, cnt in sources.most_common():
        print(f"  {s:<15} {cnt}次")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("""用法: python3 evolution_tracker.py <action> [参数]

🎯 Alex自进化里程碑追踪

动作:
  log <能力> <版本> <类型> <学到什么> [修改的文件...]
  view [能力] [数量]
  summary

类型: 行为优化 | 能力增强 | 方向修正 | 反模式消除 | 架构升级
来源: GitHub探索 | 用户反馈 | 自我反省 | 实践复盘

示例:
  python3 evolution_tracker.py log soul_md 4.0 行为优化 '增加了三闸门协议防止范围蔓延' soul_md
  python3 evolution_tracker.py log agent_md 3.0 能力增强 '新增curl能力地图' agent_md
  python3 evolution_tracker.py view soul_md
  python3 evolution_tracker.py summary
""")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "log" and len(sys.argv) >= 6:
        capability = sys.argv[2]
        version = sys.argv[3]
        change_type = sys.argv[4]
        what_i_learned = sys.argv[5]
        files = sys.argv[6:] if len(sys.argv) > 6 else []
        
        entry = log_milestone(
            capability=capability,
            version=version,
            change_type=change_type,
            what_i_learned=what_i_learned,
            files_changed=files
        )
        print(f"📝 记录详情: {json.dumps(entry, indent=2, ensure_ascii=False)}")
        
    elif action == "view":
        capability = sys.argv[2] if len(sys.argv) >= 3 else None
        limit = int(sys.argv[3]) if len(sys.argv) >= 4 else 10
        view_history(capability=capability, limit=limit)
        
    elif action == "summary":
        show_summary()
        
    else:
        print(f"❌ 未知动作或参数不足: {action}")
