#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEMINI项目适配器 - 修复版
用于将现有的GEMINI.md格式项目适配到通用Agent系统
"""

import re
import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from novel_writing_agent import (
    NovelWritingAgent, ProjectConfig, CharacterInfo, 
    PlotThread, ChapterSummary
)

class GeminiProjectAdapter:
    """GEMINI项目适配器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.gemini_file = self.project_root / ".gemini" / "GEMINI.md"
        self.outline_file = self.project_root / "故事大纲.md"
        
    def create_agent_from_gemini(self) -> NovelWritingAgent:
        """从GEMINI项目创建Agent"""
        
        # 1. 创建项目配置
        config = ProjectConfig(
            project_name=self.project_root.name,
            author="未知作者",
            genre="网络小说",
            min_word_count=6000,
            target_word_count=8000,
            chapter_naming_pattern="第{num}章 {title}.txt",
            outline_file="故事大纲.md",
            agent_config_file=".gemini/GEMINI.md"
        )
        
        # 2. 初始化Agent
        agent = NovelWritingAgent(str(self.project_root), config)
        agent.save_project_config()
        
        # 3. 导入现有数据
        self.import_data_to_agent(agent)
        
        return agent
    
    def import_data_to_agent(self, agent: NovelWritingAgent):
        """导入GEMINI数据到Agent"""
        
        # 导入章节摘要和角色状态
        summaries = self.parse_gemini_plot_log()
        
        all_characters = {}
        for summary in summaries:
            agent.add_chapter_summary(summary)
            
            # 收集角色信息
            for char_name in summary.characters_involved:
                if char_name not in all_characters:
                    all_characters[char_name] = CharacterInfo(
                        name=char_name,
                        description="从GEMINI导入",
                        current_state={}
                    )
        
        # 更新agent的角色数据
        agent.characters.update(all_characters)
        
        # 分析并创建剧情线索
        threads = self.extract_plot_threads(summaries)
        for thread in threads:
            agent.plot_threads[thread.id] = thread
        
        # 保存数据
        agent.save_characters()
        agent.save_plot_threads()
        agent.save_chapter_summaries()
        
        print(f"成功导入 {len(summaries)} 个章节摘要")
        print(f"成功导入 {len(all_characters)} 个角色")
        print(f"成功导入 {len(threads)} 个剧情线索")
    
    def parse_gemini_plot_log(self) -> List[ChapterSummary]:
        """解析GEMINI.md中的剧情日志"""
        if not self.gemini_file.exists():
            print(f"GEMINI文件不存在: {self.gemini_file}")
            return []
            
        with open(self.gemini_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找剧情日志位置
        log_start = content.find("## **剧情日志**")
        if log_start == -1:
            log_start = content.find("## 剧情日志")
        
        if log_start == -1:
            print("未找到剧情日志部分")
            return []
        
        # 从剧情日志开始到文件结尾
        log_content = content[log_start:]
        print(f"找到剧情日志，长度: {len(log_content)}")
        
        # 查找所有章节 - 兼容多种格式
        chapter_pattern = r'### \\*\\*第(\\d+)章[：:\\s]*([^*]+)\\*\\*'
        chapters = re.findall(chapter_pattern, log_content)
        print(f"找到章节数量: {len(chapters)}")
        
        summaries = []
        for i, (chapter_num, title) in enumerate(chapters):
            # 获取该章节的完整内容
            chapter_content = self.extract_chapter_content(log_content, int(chapter_num), i, chapters)
            summary = self.parse_single_chapter_summary(int(chapter_num), title.strip(), chapter_content)
            if summary:
                summaries.append(summary)
        
        return summaries
    
    def extract_chapter_content(self, log_content: str, chapter_num: int, index: int, all_chapters: List) -> str:
        """提取单个章节的完整内容"""
        # 找到当前章节的开始位置
        chapter_start = log_content.find(f"### **第{chapter_num}章")
        if chapter_start == -1:
            return ""
        
        # 确定章节结束位置
        if index + 1 < len(all_chapters):
            # 不是最后一章，找下一章的开始位置
            next_chapter_num = all_chapters[index + 1][0]
            next_chapter_start = log_content.find(f"### **第{next_chapter_num}章", chapter_start + 1)
            if next_chapter_start != -1:
                return log_content[chapter_start:next_chapter_start].strip()
        
        # 是最后一章或没找到下一章，找下一个卷的开始或文件结尾
        next_volume_match = re.search(r'\\n## \\*\\*第\\d+卷', log_content[chapter_start + 1:])
        if next_volume_match:
            chapter_end = chapter_start + 1 + next_volume_match.start()
            return log_content[chapter_start:chapter_end].strip()
        
        # 取到文件结尾
        return log_content[chapter_start:].strip()
    
    def parse_single_chapter_summary(self, chapter_num: int, title: str, content: str) -> Optional[ChapterSummary]:
        """解析单个章节摘要"""
        try:
            # 提取剧情进展
            plot_match = re.search(r'\\*\\s*\\*\\*剧情进展[：:]?\\*\\*\\s*([^*]+)', content)
            plot_progress = plot_match.group(1).strip() if plot_match else ""
            
            # 提取角色信息
            characters = []
            # 查找角色状态部分
            char_section_match = re.search(r'\\*\\s*\\*\\*角色状态[：:]?\\*\\*\\s*(.*?)(?=\\*\\s*\\*\\*|$)', content, re.DOTALL)
            if char_section_match:
                char_content = char_section_match.group(1)
                # 匹配每个角色的条目
                char_entries = re.findall(r'\\*\\s*\\*\\*([^(（]+)(?:\\s*[（(]([^)）]*)[）)])?\\s*[：:]?\\*\\*', char_content)
                for char_entry in char_entries:
                    char_name = char_entry[0].strip()
                    if char_name and not char_name.startswith('第') and len(char_name) < 20:
                        characters.append(char_name)
            
            # 提取关键事件
            key_events = []
            events_match = re.search(r'\\*\\s*\\*\\*关键线索[：:]?\\*\\*\\s*([^*]+)', content)
            if events_match:
                key_events = [events_match.group(1).strip()]
            
            return ChapterSummary(
                chapter_num=chapter_num,
                title=title,
                content_summary=plot_progress,
                characters_involved=characters,
                plot_threads=[],
                key_events=key_events,
                word_count=0,
                created_time=datetime.now().isoformat()
            )
            
        except Exception as e:
            print(f"解析章节 {chapter_num} 摘要失败: {e}")
            return None
    
    def extract_plot_threads(self, summaries: List[ChapterSummary]) -> List[PlotThread]:
        """从章节摘要中提取剧情线索"""
        threads = []
        thread_id = 1
        
        # 从关键事件中提取线索
        for summary in summaries:
            for event in summary.key_events:
                if len(event) > 10:  # 忽略太短的描述
                    thread = PlotThread(
                        id=f"thread_{thread_id}",
                        description=event,
                        status="active",
                        priority="medium",
                        first_chapter=summary.chapter_num,
                        last_chapter=summary.chapter_num
                    )
                    threads.append(thread)
                    thread_id += 1
        
        return threads

def migrate_gemini_project(project_root: str) -> NovelWritingAgent:
    """迁移GEMINI项目到通用Agent系统"""
    adapter = GeminiProjectAdapter(project_root)
    agent = adapter.create_agent_from_gemini()
    
    # 创建工作流配置
    workflow_config = {
        "workflow_steps": [
            {
                "name": "review",
                "description": "回顾与分析",
                "config": {
                    "context_chapters": 3,
                    "check_outline": True,
                    "check_characters": True,
                    "check_threads": True
                }
            },
            {
                "name": "pre_check", 
                "description": "动笔前检查",
                "config": {
                    "character_motivation_check": True,
                    "plot_consistency_check": True,
                    "thread_planning": True
                }
            },
            {
                "name": "writing",
                "description": "章节创作", 
                "config": {
                    "style": "网文风格",
                    "perspective": "第三人称",
                    "min_words": 6000
                }
            },
            {
                "name": "finalize",
                "description": "收尾与保存",
                "config": {
                    "auto_save": True,
                    "update_log": True,
                    "backup": True
                }
            }
        ]
    }
    
    workflow_file = Path(project_root) / ".agent_data" / "workflow_config.json"
    with open(workflow_file, 'w', encoding='utf-8') as f:
        json.dump(workflow_config, f, ensure_ascii=False, indent=2)
    
    print(f"\\nGEMINI项目已成功迁移到通用Agent系统!")
    print(f"项目路径: {project_root}")
    
    return agent

if __name__ == "__main__":
    # 使用示例
    project_path = "/Users/xiaoyu/逆天仙途：因果投资万倍返还！"
    
    # 迁移现有项目
    agent = migrate_gemini_project(project_path)
    
    # 测试获取数据
    print(f"\\n=== 项目数据概览 ===")
    print(f"最新章节号: {agent.get_latest_chapter_number()}")
    print(f"角色数量: {len(agent.characters)}")
    print(f"剧情线索数量: {len(agent.plot_threads)}")
    
    # 查看最近章节
    print(f"\\n=== 最近章节 ===")
    recent = agent.get_recent_chapters(3)
    for chapter in recent:
        print(f"第{chapter.chapter_num}章: {chapter.title}")
        print(f"  涉及角色: {', '.join(chapter.characters_involved[:5])}")  # 只显示前5个角色
        print(f"  内容摘要: {chapter.content_summary[:100]}...")
        print()
    
    # 查看角色信息
    print(f"\\n=== 主要角色 ===")
    for i, (name, char) in enumerate(list(agent.characters.items())[:10]):  # 只显示前10个
        print(f"{name}: {char.description}")
    
    # 测试创建下一章的流程
    print(f"\\n=== 测试创作流程 ===")
    try:
        next_chapter_num = agent.get_latest_chapter_number() + 1
        print(f"准备创作第{next_chapter_num}章...")
        
        # 只执行前两个步骤来测试
        context = {'agent': agent, 'next_chapter_num': next_chapter_num}
        
        from novel_writing_agent import ReviewStep, PreWritingCheckStep
        
        # 回顾步骤
        review_step = ReviewStep()
        context = review_step.execute(context)
        print("✓ 回顾与分析步骤完成")
        
        # 检查步骤
        check_step = PreWritingCheckStep()
        context = check_step.execute(context)
        print("✓ 动笔前检查步骤完成")
        
        print(f"\\n系统准备就绪，可以开始第{next_chapter_num}章的创作!")
        
    except Exception as e:
        print(f"测试创作流程时出现错误: {e}")