#!/usr/bin/env python3
"""知识库索引构建器 - 扫描 .knowledge/ 目录并生成 FTS5、元数据和交叉引用索引

NOTE: This script provides standalone CLI-based index building for offline scenarios.
For runtime use, the knowledge_server module's FirstRunImporter and IncrementalSync
provide equivalent functionality integrated with the API server. Use this script when
you need to build indexes without starting the full server.
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

try:
    import yaml
    _yaml_available = True
except ImportError:
    _yaml_available = False


def _simple_parse_frontmatter(raw):
    meta = {}
    lines = raw.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            i += 1
            continue
        colon = stripped.find(':')
        if colon == -1:
            i += 1
            continue
        key = stripped[:colon].strip()
        val = stripped[colon + 1:].strip()
        if val.startswith('[') and val.endswith(']'):
            inner = val[1:-1]
            items = [x.strip().strip('"').strip("'") for x in inner.split(',')]
            val = [x for x in items if x]
        elif val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        elif val.startswith("'") and val.endswith("'"):
            val = val[1:-1]
        elif val == '':
            list_items = []
            i += 1
            current_item = {}
            while i < len(lines):
                sub = lines[i]
                sub_stripped = sub.strip()
                if not sub.startswith('  ') and not sub.startswith('\t'):
                    break
                if sub_stripped.startswith('- '):
                    if current_item:
                        list_items.append(current_item)
                    current_item = {}
                    sub_content = sub_stripped[2:]
                    sub_colon = sub_content.find(':')
                    if sub_colon != -1:
                        sk = sub_content[:sub_colon].strip()
                        sv = sub_content[sub_colon + 1:].strip().strip('"').strip("'")
                        current_item[sk] = sv
                elif sub_stripped and not sub_stripped.startswith('#'):
                    sub_colon = sub_stripped.find(':')
                    if sub_colon != -1:
                        sk = sub_stripped[:sub_colon].strip()
                        sv = sub_stripped[sub_colon + 1:].strip().strip('"').strip("'")
                        current_item[sk] = sv
                i += 1
            if current_item:
                list_items.append(current_item)
            val = list_items
            meta[key] = val
            continue
        meta[key] = val
        i += 1
    return meta


def parse_frontmatter(text):
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)', text, re.DOTALL)
    if not match:
        return None, text
    raw, body = match.group(1), match.group(2)
    if _yaml_available:
        try:
            meta = yaml.safe_load(raw)
            if not isinstance(meta, dict):
                meta = {}
            return meta, body
        except Exception:
            pass
    meta = _simple_parse_frontmatter(raw)
    return meta, body


def scan_knowledge_dir(knowledge_root, verbose=False):
    """扫描知识库目录，返回 [{path, metadata, body, rel_path}, ...]"""
    entries = []
    root = Path(knowledge_root)
    if not root.is_dir():
        print(f"[错误] 知识库目录不存在: {knowledge_root}")
        return entries
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if not fname.endswith('.md'):
                continue
            fpath = Path(dirpath) / fname
            rel_path = fpath.relative_to(root).as_posix()
            try:
                text = fpath.read_text(encoding='utf-8')
            except Exception as e:
                if verbose:
                    print(f"  [警告] 无法读取 {rel_path}: {e}")
                continue
            meta, body = parse_frontmatter(text)
            if meta is None:
                if verbose:
                    print(f"  [跳过] 无 frontmatter: {rel_path}")
                continue
            entry_id = meta.get('id', fpath.stem)
            entries.append({
                'path': str(fpath),
                'rel_path': rel_path,
                'id': entry_id,
                'metadata': meta,
                'body': body,
            })
            if verbose:
                print(f"  [扫描] {entry_id} <- {rel_path}")
    return entries


def build_fts5_index(entries, output_dir, verbose=False):
    """构建 SQLite FTS5 全文索引（增量更新）"""
    db_path = Path(output_dir) / 'keyword_index.db'
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(
        'CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts '
        'USING fts5(id, title, type, tags, content, path, '
        'tokenize="unicode61")'
    )
    cur.execute(
        'CREATE TABLE IF NOT EXISTS file_mtime '
        '(rel_path TEXT PRIMARY KEY, mtime INTEGER NOT NULL)'
    )
    current_mtimes = {}
    for row in cur.execute('SELECT rel_path, mtime FROM file_mtime'):
        current_mtimes[row[0]] = row[1]
    new_mtimes = {}
    for e in entries:
        try:
            mtime = int(Path(e['path']).stat().st_mtime)
        except OSError:
            mtime = 0
        new_mtimes[e['rel_path']] = mtime
    removed = set(current_mtimes.keys()) - set(new_mtimes.keys())
    for rel_path in removed:
        cur.execute("DELETE FROM knowledge_fts WHERE path = ?", (rel_path,))
        cur.execute("DELETE FROM file_mtime WHERE rel_path = ?", (rel_path,))
        if verbose:
            print(f"  [FTS5] 已移除: {rel_path}")
    changed_or_new = []
    for e in entries:
        old_mtime = current_mtimes.get(e['rel_path'])
        new_mtime = new_mtimes[e['rel_path']]
        if old_mtime is None or old_mtime != new_mtime:
            changed_or_new.append(e)
    count = 0
    for e in changed_or_new:
        meta = e['metadata']
        title = meta.get('id', e['id'])
        ktype = meta.get('type', '')
        tags = meta.get('tags', [])
        tags_str = ' '.join(tags) if isinstance(tags, list) else str(tags)
        content = re.sub(r'[#*`\[\]()>|_-]', ' ', e['body'])
        content = re.sub(r'\s+', ' ', content).strip()
        cur.execute("DELETE FROM knowledge_fts WHERE path = ?", (e['rel_path'],))
        cur.execute(
            'INSERT INTO knowledge_fts(id, title, type, tags, content, path) '
            'VALUES(?, ?, ?, ?, ?, ?)',
            (e['id'], title, ktype, tags_str, content, e['rel_path'])
        )
        cur.execute(
            'INSERT OR REPLACE INTO file_mtime (rel_path, mtime) VALUES (?, ?)',
            (e['rel_path'], new_mtimes[e['rel_path']])
        )
        count += 1
    conn.commit()
    conn.close()
    if verbose:
        print(f"  [FTS5] 已更新 {count} 条记录（增量），总计 {len(entries)} 条 -> {db_path}")
    return count


def build_metadata_index(entries, output_dir, verbose=False):
    """构建元数据 JSON 索引"""
    out_path = Path(output_dir) / 'metadata_index.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    index = {}
    for e in entries:
        meta_copy = dict(e['metadata'])
        meta_copy['_path'] = e['rel_path']
        meta_copy['_id'] = e['id']
        index[e['id']] = meta_copy
    out_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')
    if verbose:
        print(f"  [元数据] 已写入 {len(index)} 条 -> {out_path}")
    return len(index)


def extract_links(body, source_id, source_rel_path):
    """从正文中提取 [text](path) 链接，返回 [(source_id, target_path), ...]"""
    links = []
    source_dir = str(Path(source_rel_path).parent)
    for match in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', body):
        target = match.group(2).strip()
        if target.startswith(('http://', 'https://', '#', 'mailto:')):
            continue
        if not target.startswith('/'):
            target = (Path(source_dir) / target).as_posix()
            target = re.sub(r'/+', '/', target)
        links.append((source_id, target))
    return links


def build_cross_references(entries, output_dir, verbose=False):
    out_path = Path(output_dir) / 'cross_reference.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    id_to_rel = {e['id']: e['rel_path'] for e in entries}
    rel_to_id = {e['rel_path']: e['id'] for e in entries}
    forward = {}
    for e in entries:
        refs_list = []
        links = extract_links(e['body'], e['id'], e['rel_path'])
        if links:
            refs_list.extend([
                {'target_path': t, 'target_id': rel_to_id.get(t, None)}
                for _, t in links
            ])
        meta_refs = e['metadata'].get('references', [])
        if isinstance(meta_refs, list):
            for ref in meta_refs:
                if isinstance(ref, dict) and 'id' in ref:
                    tid = ref['id']
                    refs_list.append({
                        'target_id': tid,
                        'target_path': id_to_rel.get(tid, ''),
                        'relation': ref.get('relation', ''),
                    })
        if refs_list:
            forward[e['id']] = refs_list
    backward = {}
    for src, refs in forward.items():
        for ref in refs:
            tid = ref.get('target_id') or ref['target_path']
            backward.setdefault(tid, []).append({
                'source_id': src,
                'source_path': id_to_rel.get(src, ''),
                'relation': ref.get('relation', ''),
            })
    total_refs = sum(len(v) for v in forward.values())
    result = {
        'forward': forward,
        'backward': backward,
        'summary': {
            'total_forward_refs': total_refs,
            'total_backward_refs': sum(len(v) for v in backward.values()),
        }
    }
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    if verbose:
        print(f"  [交叉引用] 前向 {total_refs} 条，后向 {result['summary']['total_backward_refs']} 条 -> {out_path}")
    return total_refs


def main():
    parser = argparse.ArgumentParser(description='知识库索引构建器')
    parser.add_argument(
        'knowledge_root', nargs='?',
        default=str(Path(__file__).resolve().parent.parent / '.knowledge'),
        help='知识库根目录（默认: 脚本上级目录的 .knowledge/）'
    )
    parser.add_argument(
        '--output-dir', default=None,
        help='索引输出目录（默认: knowledge_root/index）'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='详细输出模式'
    )
    args = parser.parse_args()
    knowledge_root = Path(args.knowledge_root).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else knowledge_root / 'index'
    print(f"=== 知识库索引构建器 ===")
    print(f"知识库目录: {knowledge_root}")
    print(f"输出目录:   {output_dir}")
    if not knowledge_root.is_dir():
        print(f"[错误] 知识库目录不存在: {knowledge_root}")
        sys.exit(1)
    print("\n[1/4] 扫描知识库文件...")
    entries = scan_knowledge_dir(knowledge_root, verbose=args.verbose)
    if not entries:
        print("[警告] 未找到任何含 frontmatter 的 .md 文件，退出。")
        sys.exit(0)
    print(f"  共扫描到 {len(entries)} 个知识条目")
    print("\n[2/4] 构建 FTS5 全文索引...")
    fts_count = build_fts5_index(entries, output_dir, verbose=args.verbose)
    print(f"  已索引 {fts_count} 条记录")
    print("\n[3/4] 构建元数据索引...")
    meta_count = build_metadata_index(entries, output_dir, verbose=args.verbose)
    print(f"  已写入 {meta_count} 条元数据")
    print("\n[4/4] 构建交叉引用索引...")
    ref_count = build_cross_references(entries, output_dir, verbose=args.verbose)
    print(f"  发现 {ref_count} 条交叉引用")
    print("\n=== 构建完成 ===")
    print(f"  总条目数:     {len(entries)}")
    print(f"  已索引条目:   {fts_count}")
    print(f"  交叉引用数:   {ref_count}")
    print(f"  索引位置:     {output_dir}")


if __name__ == '__main__':
    main()
