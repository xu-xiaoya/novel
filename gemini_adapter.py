#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEMINI项目适配器
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
        for summary in summaries:
            agent.add_chapter_summary(summary)
            
            # 提取角色信息
            for char in summary.characters_involved:
                if char not in agent.characters:
                    agent.characters[char] = CharacterInfo(
                        name=char,
                        description="从GEMINI导入",
                        current_state={}
                    )
        
        # 分析并创建剧情线索
        threads = self.extract_plot_threads(summaries)
        for thread in threads:
            agent.plot_threads[thread.id] = thread
        
        # 保存数据
        agent.save_characters()
        agent.save_plot_threads()
        agent.save_chapter_summaries()
        
        print(f"成功导入 {len(summaries)} 个章节摘要")
        print(f"成功导入 {len(agent.characters)} 个角色")
        print(f"成功导入 {len(threads)} 个剧情线索")
    
    def parse_gemini_plot_log(self) -> List[ChapterSummary]:
        """解析GEMINI.md中的剧情日志"""
        if not self.gemini_file.exists():
            return []
            
        with open(self.gemini_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取剧情日志部分
        log_match = re.search(r'## \*\*剧情日志\*\*(.*?)(?=^##|\n---|\Z)', content, re.MULTILINE | re.DOTALL)
        if not log_match:
            # 尝试不带星号的格式
            log_match = re.search(r'## 剧情日志(.*?)(?=^##|\n---|\Z)', content, re.MULTILINE | re.DOTALL)
            if not log_match:
                print("未找到剧情日志部分")
                return []
        
        log_content = log_match.group(1)
        print(f"找到剧情日志内容，长度: {len(log_content)}")
        print(f"剧情日志内容预览: {repr(log_content[:200])}")
        
        # 解析每个章节摘要
        chapter_pattern = r'### \*\*第(\d+)章[：:：]([^*]+)\*\*\n\n(.*?)(?=\n### |\Z)'
        chapters = re.findall(chapter_pattern, log_content, re.DOTALL)
        print(f"找到章节数量: {len(chapters)}")
        
        if not chapters:
            # 尝试其他可能的模式
            chapter_pattern2 = r'### \*\*第(\d+)章[：:：]([^*]+)\*\*\n\n(.*?)(?=### |\Z)'
            chapters = re.findall(chapter_pattern2, log_content, re.DOTALL)
            print(f"使用备用模式找到章节数量: {len(chapters)}")
        
        summaries = []
        for chapter_num, title, content in chapters:
            summary = self.parse_single_chapter_summary(int(chapter_num), title.strip(), content.strip())
            if summary:
                summaries.append(summary)
        
        return summaries
    
    def parse_single_chapter_summary(self, chapter_num: int, title: str, content: str) -> Optional[ChapterSummary]:
        """解析单个章节摘要"""
        try:
            # 提取剧情进展
            plot_match = re.search(r'\*\s*\*\*剧情进展[：:]?\*\*\s*([^*]+)', content)
            plot_progress = plot_match.group(1).strip() if plot_match else ""
            
            # 提取角色状态
            characters = []
            char_section = re.search(r'\*\s*\*\*角色状态[：:]?\*\*\s*(.*?)(?=\*\s*\*\*|$)', content, re.DOTALL)
            if char_section:
                char_content = char_section.group(1)
                # 匹配 **角色名 (境界):** 描述 的模式
                char_pattern = r'\*\*([^(（]+)(?:\s*[（(]([^)）]*)[）)])?\s*[：:]\*\*([^*\n]+)'
                char_matches = re.findall(char_pattern, char_content)
                
                for char_name, cultivation, status in char_matches:
                    char_name = char_name.strip()
                    if char_name:
                        characters.append(char_name)
            
            # 提取关键事件
            key_events = []
            events_match = re.search(r'\*\s*\*\*关键线索[：:]?\*\*\s*([^*]+)', content)
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
    
    def create_workflow_config(self) -> Dict:
        """创建工作流配置"""
        return {
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

def migrate_gemini_project(project_root: str) -> NovelWritingAgent:
    """迁移GEMINI项目到通用Agent系统"""
    adapter = GeminiProjectAdapter(project_root)
    agent = adapter.create_agent_from_gemini()
    
    # 创建工作流配置
    workflow_config = adapter.create_workflow_config()
    workflow_file = Path(project_root) / ".agent_data" / "workflow_config.json"
    with open(workflow_file, 'w', encoding='utf-8') as f:
        json.dump(workflow_config, f, ensure_ascii=False, indent=2)
    
    print(f"GEMINI项目已成功迁移到通用Agent系统!")
    print(f"项目路径: {project_root}")
    
    return agent

if __name__ == "__main__":
    # 使用示例
    project_path = "/Users/xiaoyu/逆天仙途：因果投资万倍返还！"
    
    # 迁移现有项目
    agent = migrate_gemini_project(project_path)
    
    # 测试获取数据
    print(f"\n最新章节号: {agent.get_latest_chapter_number()}")
    print(f"角色数量: {len(agent.characters)}")
    print(f"剧情线索数量: {len(agent.plot_threads)}")
    
    # 查看最近章节
    recent = agent.get_recent_chapters(2)
    for chapter in recent:
        print(f"第{chapter.chapter_num}章: {chapter.title}")
        print(f"  涉及角色: {', '.join(chapter.characters_involved)}")
        print(f"  内容摘要: {chapter.content_summary[:100]}...")
        print()