#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试 GEMINI 适配器
"""

import re
from pathlib import Path

def quick_test_parser():
    gemini_file = Path("/Users/xiaoyu/逆天仙途：因果投资万倍返还！/.gemini/GEMINI.md")
    
    with open(gemini_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找剧情日志位置
    log_start = content.find("## **剧情日志**")
    if log_start == -1:
        log_start = content.find("## 剧情日志")
    
    if log_start == -1:
        print("未找到剧情日志")
        return
    
    # 从剧情日志开始到文件结尾
    log_content = content[log_start:]
    print(f"找到剧情日志，长度: {len(log_content)}")
    
    # 查找所有章节
    chapter_pattern = r'### \*\*第(\d+)章[：:\s]*([^*]+)\*\*'
    chapters = re.findall(chapter_pattern, log_content)
    
    print(f"找到章节数量: {len(chapters)}")
    for i, (num, title) in enumerate(chapters[:5]):  # 只显示前5个
        print(f"  第{num}章: {title.strip()}")
    
    if chapters:
        # 测试解析第一个章节的详细内容
        first_chapter_num, first_title = chapters[0]
        
        # 找到这个章节的完整内容
        chapter_start = log_content.find(f"### **第{first_chapter_num}章")
        if chapter_start != -1:
            # 找到下一个章节的开始位置
            next_chapter_match = re.search(r'\n### \*\*第\d+章', log_content[chapter_start + 1:])
            if next_chapter_match:
                chapter_end = chapter_start + 1 + next_chapter_match.start()
                chapter_content = log_content[chapter_start:chapter_end]
            else:
                # 如果没有下一章，取到下一个卷的开始
                next_volume_match = re.search(r'\n## \*\*第\d+卷', log_content[chapter_start + 1:])
                if next_volume_match:
                    chapter_end = chapter_start + 1 + next_volume_match.start()
                    chapter_content = log_content[chapter_start:chapter_end]
                else:
                    chapter_content = log_content[chapter_start:]
            
            print(f"\n第一章内容示例 (前500字符):")
            print(chapter_content[:500])
            
            # 尝试解析其中的剧情进展
            plot_match = re.search(r'\*\s*\*\*剧情进展[：:]?\*\*\s*([^*]+)', chapter_content)
            if plot_match:
                print(f"\n剧情进展: {plot_match.group(1).strip()[:100]}...")
            
            # 尝试解析角色状态
            char_matches = re.findall(r'\*\*([^(]+)\(([^)]+)\)[：:]?\*\*([^*\n]+)', chapter_content)
            print(f"\n找到角色: {len(char_matches)} 个")
            for char_name, level, desc in char_matches[:3]:
                print(f"  {char_name.strip()} ({level.strip()}): {desc.strip()[:50]}...")

if __name__ == "__main__":
    quick_test_parser()