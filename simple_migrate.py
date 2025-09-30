#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版 GEMINI 适配器测试
"""

import re
from novel_writing_agent import NovelWritingAgent, ProjectConfig, ChapterSummary
from datetime import datetime

def test_and_migrate():
    project_root = "/Users/xiaoyu/逆天仙途：因果投资万倍返还！"
    gemini_file = project_root + "/.gemini/GEMINI.md"
    
    # 读取GEMINI文件
    with open(gemini_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到剧情日志
    log_start = content.find("## **剧情日志**")
    if log_start == -1:
        log_start = content.find("## 剧情日志")
    
    log_content = content[log_start:]
    print(f"剧情日志长度: {len(log_content)}")
    
    # 简化的章节匹配
    chapters = []
    lines = log_content.split('\n')
    
    current_chapter = None
    current_content = []
    
    for line in lines:
        # 检查是否是章节标题行
        chapter_match = re.match(r'### \*\*第(\d+)章[：:\s]*([^*]+)\*\*', line)
        if chapter_match:
            # 保存上一章
            if current_chapter:
                chapters.append((current_chapter[0], current_chapter[1], '\n'.join(current_content)))
            
            # 开始新章节
            current_chapter = (int(chapter_match.group(1)), chapter_match.group(2).strip())
            current_content = []
        elif current_chapter:
            current_content.append(line)
    
    # 保存最后一章
    if current_chapter:
        chapters.append((current_chapter[0], current_chapter[1], '\n'.join(current_content)))
    
    print(f"找到章节: {len(chapters)} 个")
    
    # 创建Agent配置
    config = ProjectConfig(
        project_name="逆天仙途：因果投资万倍返还！",
        author="作者",
        genre="玄幻",
        min_word_count=6000,
        target_word_count=8000
    )
    
    # 初始化Agent
    agent = NovelWritingAgent(project_root, config)
    agent.save_project_config()
    
    # 导入章节数据
    for chapter_num, title, content in chapters:
        # 解析剧情进展
        plot_match = re.search(r'\*\s*\*\*剧情进展[：:]?\*\*\s*([^*]+)', content)
        plot_progress = plot_match.group(1).strip() if plot_match else ""
        
        # 解析角色
        characters = []
        char_matches = re.findall(r'\*\*([^(（]+)(?:\s*[（(]([^)）]*)[）)])?[：:]?\*\*', content)
        for char_match in char_matches:
            char_name = char_match[0].strip()
            if char_name and not char_name.startswith('第') and len(char_name) < 15:
                characters.append(char_name)
        
        # 解析关键线索
        key_events = []
        clue_match = re.search(r'\*\s*\*\*关键线索[：:]?\*\*\s*([^*]+)', content)
        if clue_match:
            key_events = [clue_match.group(1).strip()]
        
        # 创建摘要
        summary = ChapterSummary(
            chapter_num=chapter_num,
            title=title,
            content_summary=plot_progress,
            characters_involved=characters[:5],  # 限制角色数量
            key_events=key_events,
            word_count=0,
            created_time=datetime.now().isoformat()
        )
        
        agent.add_chapter_summary(summary)
        
        # 添加角色到Agent
        for char_name in characters[:5]:
            if char_name not in agent.characters:
                from novel_writing_agent import CharacterInfo
                agent.characters[char_name] = CharacterInfo(
                    name=char_name,
                    description="从GEMINI导入"
                )
    
    # 保存数据
    agent.save_characters()
    
    print(f"\n=== 迁移完成 ===")
    print(f"导入章节: {len(chapters)} 个")
    print(f"导入角色: {len(agent.characters)} 个")
    print(f"最新章节号: {agent.get_latest_chapter_number()}")
    
    # 显示最近章节
    print(f"\n=== 最新章节 ===")
    recent = agent.get_recent_chapters(3)
    for chapter in recent:
        print(f"第{chapter.chapter_num}章: {chapter.title}")
        print(f"  角色: {', '.join(chapter.characters_involved)}")
        print(f"  摘要: {chapter.content_summary[:80]}...")
        print()
    
    return agent

if __name__ == "__main__":
    agent = test_and_migrate()