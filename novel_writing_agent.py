#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用小说写作 Agent 系统
基于四步工作流的自动化小说创作框架
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from pathlib import Path
from abc import ABC, abstractmethod
import logging

@dataclass
class ProjectConfig:
    """项目配置"""
    project_name: str
    author: str
    genre: str  # 小说类型：玄幻、都市、科幻等
    min_word_count: int = 3000
    target_word_count: int = 5000
    max_word_count: int = 8000
    chapter_naming_pattern: str = "第{num}章 {title}.txt"
    workflow_config_file: str = "workflow.json"
    outline_file: str = "故事大纲.md"
    agent_config_file: str = "agent.md"

@dataclass 
class CharacterInfo:
    """角色信息"""
    name: str
    description: str = ""
    current_state: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class PlotThread:
    """剧情线索"""
    id: str
    description: str
    status: str = "active"  # active, resolved, pending
    priority: str = "medium"  # high, medium, low
    first_chapter: int = 0
    last_chapter: int = 0
    
@dataclass
class ChapterSummary:
    """章节摘要"""
    chapter_num: int
    title: str
    content_summary: str
    characters_involved: List[str] = field(default_factory=list)
    plot_threads: List[str] = field(default_factory=list)
    key_events: List[str] = field(default_factory=list)
    word_count: int = 0
    created_time: str = field(default_factory=lambda: datetime.now().isoformat())

class WorkflowStep(ABC):
    """工作流步骤抽象基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行步骤"""
        pass

class ReviewStep(WorkflowStep):
    """回顾与分析步骤"""
    
    def __init__(self):
        super().__init__("review", "回顾与分析前文内容")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行回顾步骤"""
        agent = context['agent']
        next_chapter = context['next_chapter_num']
        
        # 获取项目大纲
        outline = agent.load_outline()
        
        # 获取最近章节
        recent_chapters = agent.get_recent_chapters(count=3)
        
        # 获取角色状态
        characters = agent.get_all_characters()
        
        # 获取活跃线索
        active_threads = agent.get_active_plot_threads()
        
        # 查找未解决的线索
        unresolved_threads = agent.find_unresolved_threads()
        
        review_result = {
            'outline': outline,
            'recent_chapters': recent_chapters,
            'characters': characters,
            'active_threads': active_threads,
            'unresolved_threads': unresolved_threads,
            'next_chapter_num': next_chapter
        }
        
        context['review_result'] = review_result
        return context

class PreWritingCheckStep(WorkflowStep):
    """动笔前检查步骤"""
    
    def __init__(self):
        super().__init__("pre_check", "动笔前的逻辑检查")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行检查步骤"""
        review_result = context['review_result']
        
        # 角色动机检查
        character_check = self.check_character_motivations(review_result)
        
        # 情节线索规划
        plot_planning = self.plan_plot_threads(review_result)
        
        # 逻辑一致性检查  
        consistency_check = self.check_consistency(review_result)
        
        check_result = {
            'character_check': character_check,
            'plot_planning': plot_planning,
            'consistency_check': consistency_check,
            'warnings': [],
            'suggestions': []
        }
        
        context['check_result'] = check_result
        return context
    
    def check_character_motivations(self, review_result: Dict) -> Dict:
        """检查角色动机"""
        # 可以根据具体需求实现
        return {'status': 'passed', 'notes': []}
    
    def plan_plot_threads(self, review_result: Dict) -> Dict:
        """规划情节线索"""
        # 可以根据具体需求实现
        return {'planned_threads': [], 'threads_to_resolve': []}
    
    def check_consistency(self, review_result: Dict) -> Dict:
        """检查一致性"""
        # 可以根据具体需求实现
        return {'status': 'passed', 'issues': []}

class WritingStep(WorkflowStep):
    """章节创作步骤"""
    
    def __init__(self, content_generator: Callable = None):
        super().__init__("writing", "章节内容创作")
        self.content_generator = content_generator
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行写作步骤"""
        if self.content_generator:
            # 使用自定义内容生成器
            content = self.content_generator(context)
        else:
            # 使用默认的内容生成提示
            content = self.generate_content_prompt(context)
        
        context['chapter_content'] = content
        return context
    
    def generate_content_prompt(self, context: Dict[str, Any]) -> str:
        """生成内容创作提示"""
        review = context['review_result']
        check = context['check_result']
        
        prompt = f"""
基于以下信息创作第{review['next_chapter_num']}章：

## 故事背景
{review['outline'][:500]}...

## 最近章节情况
"""
        
        for chapter in review['recent_chapters'][-2:]:
            prompt += f"- 第{chapter.chapter_num}章: {chapter.content_summary}\n"
        
        prompt += f"""
## 主要角色状态
"""
        for char_name, char_info in review['characters'].items():
            prompt += f"- {char_name}: {char_info.description}\n"
        
        prompt += f"""
## 需要处理的线索
"""
        for thread in review['unresolved_threads']:
            prompt += f"- {thread.description} (优先级: {thread.priority})\n"
        
        prompt += f"""
## 创作要求
- 字数要求: 不少于3000字
- 保持角色一致性
- 推进主要情节
- 处理至少一个未解决线索
        """
        
        return prompt

class FinalizeStep(WorkflowStep):
    """收尾与保存步骤"""
    
    def __init__(self):
        super().__init__("finalize", "收尾与保存章节")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行收尾步骤"""
        agent = context['agent']
        chapter_num = context['review_result']['next_chapter_num']
        content = context.get('chapter_content', '')
        
        # 生成章节标题（如果没有提供）
        if 'chapter_title' not in context:
            context['chapter_title'] = f"第{chapter_num}章"
        
        # 保存章节文件
        saved_path = agent.save_chapter(chapter_num, context['chapter_title'], content)
        
        # 创建章节摘要
        summary = self.create_chapter_summary(context)
        agent.add_chapter_summary(summary)
        
        # 更新剧情日志
        agent.update_plot_log(summary)
        
        context['saved_path'] = saved_path
        context['chapter_summary'] = summary
        
        return context
    
    def create_chapter_summary(self, context: Dict[str, Any]) -> ChapterSummary:
        """创建章节摘要"""
        review = context['review_result']
        content = context.get('chapter_content', '')
        
        # 简单的摘要生成（可以用更复杂的方法）
        summary_text = content[:200] + "..." if len(content) > 200 else content
        
        return ChapterSummary(
            chapter_num=review['next_chapter_num'],
            title=context.get('chapter_title', ''),
            content_summary=summary_text,
            word_count=len(content),
            characters_involved=[],  # 可以通过分析内容提取
            plot_threads=[],  # 可以通过分析内容提取
            key_events=[]  # 可以通过分析内容提取
        )

class NovelWritingAgent:
    """通用小说写作 Agent"""
    
    def __init__(self, project_root: str, config: Optional[ProjectConfig] = None):
        self.project_root = Path(project_root)
        self.config = config or self.load_project_config()
        
        # 创建数据目录
        self.data_dir = self.project_root / ".agent_data"
        self.data_dir.mkdir(exist_ok=True)
        
        # 初始化日志
        self.setup_logging()
        
        # 数据存储文件
        self.characters_file = self.data_dir / "characters.json"
        self.plot_threads_file = self.data_dir / "plot_threads.json"
        self.chapter_summaries_file = self.data_dir / "chapter_summaries.json"
        
        # 加载数据
        self.characters = self.load_characters()
        self.plot_threads = self.load_plot_threads()
        self.chapter_summaries = self.load_chapter_summaries()
        
        # 初始化工作流
        self.workflow = self.create_default_workflow()
        
    def setup_logging(self):
        """设置日志"""
        log_file = self.data_dir / "agent.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_project_config(self) -> ProjectConfig:
        """加载项目配置"""
        config_file = self.project_root / "project_config.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return ProjectConfig(**data)
        else:
            # 默认配置
            return ProjectConfig(
                project_name=self.project_root.name,
                author="未知作者",
                genre="通用"
            )
    
    def save_project_config(self):
        """保存项目配置"""
        config_file = self.project_root / "project_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.config), f, ensure_ascii=False, indent=2)
    
    def create_default_workflow(self) -> List[WorkflowStep]:
        """创建默认工作流"""
        return [
            ReviewStep(),
            PreWritingCheckStep(), 
            WritingStep(),
            FinalizeStep()
        ]
    
    def load_characters(self) -> Dict[str, CharacterInfo]:
        """加载角色数据"""
        if self.characters_file.exists():
            with open(self.characters_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {name: CharacterInfo(**char_data) for name, char_data in data.items()}
        return {}
    
    def save_characters(self):
        """保存角色数据"""
        data = {name: asdict(char) for name, char in self.characters.items()}
        with open(self.characters_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_plot_threads(self) -> Dict[str, PlotThread]:
        """加载剧情线索"""
        if self.plot_threads_file.exists():
            with open(self.plot_threads_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {tid: PlotThread(**thread_data) for tid, thread_data in data.items()}
        return {}
    
    def save_plot_threads(self):
        """保存剧情线索"""
        data = {tid: asdict(thread) for tid, thread in self.plot_threads.items()}
        with open(self.plot_threads_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_chapter_summaries(self) -> List[ChapterSummary]:
        """加载章节摘要"""
        if self.chapter_summaries_file.exists():
            with open(self.chapter_summaries_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [ChapterSummary(**summary_data) for summary_data in data]
        return []
    
    def save_chapter_summaries(self):
        """保存章节摘要"""
        data = [asdict(summary) for summary in self.chapter_summaries]
        with open(self.chapter_summaries_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_outline(self) -> str:
        """加载故事大纲"""
        outline_file = self.project_root / self.config.outline_file
        if outline_file.exists():
            with open(outline_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def get_latest_chapter_number(self) -> int:
        """获取最新章节号"""
        if self.chapter_summaries:
            return max(summary.chapter_num for summary in self.chapter_summaries)
        return 0
    
    def get_recent_chapters(self, count: int = 3) -> List[ChapterSummary]:
        """获取最近章节"""
        if not self.chapter_summaries:
            return []
        sorted_summaries = sorted(self.chapter_summaries, key=lambda x: x.chapter_num, reverse=True)
        return sorted_summaries[:count]
    
    def get_all_characters(self) -> Dict[str, CharacterInfo]:
        """获取所有角色"""
        return self.characters
    
    def get_active_plot_threads(self) -> List[PlotThread]:
        """获取活跃线索"""
        return [thread for thread in self.plot_threads.values() if thread.status == "active"]
    
    def find_unresolved_threads(self) -> List[PlotThread]:
        """查找未解决线索"""
        latest_chapter = self.get_latest_chapter_number()
        unresolved = []
        
        for thread in self.plot_threads.values():
            if thread.status == "active" and (latest_chapter - thread.last_chapter) > 3:
                unresolved.append(thread)
        
        return sorted(unresolved, key=lambda x: x.priority == "high", reverse=True)
    
    def save_chapter(self, chapter_num: int, title: str, content: str) -> Path:
        """保存章节文件"""
        filename = self.config.chapter_naming_pattern.format(num=chapter_num, title=title)
        
        # 根据章节号确定保存目录（可以自定义逻辑）
        volume_dir = self.determine_volume_directory(chapter_num)
        if not volume_dir.exists():
            volume_dir.mkdir(parents=True)
        
        chapter_file = volume_dir / filename
        with open(chapter_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"章节已保存: {chapter_file}")
        return chapter_file
    
    def determine_volume_directory(self, chapter_num: int) -> Path:
        """确定章节保存目录"""
        # 默认按每20章一卷
        volume_num = (chapter_num - 1) // 20 + 1
        return self.project_root / f"第{volume_num}卷"
    
    def add_chapter_summary(self, summary: ChapterSummary):
        """添加章节摘要"""
        # 移除相同章节号的旧摘要
        self.chapter_summaries = [s for s in self.chapter_summaries if s.chapter_num != summary.chapter_num]
        self.chapter_summaries.append(summary)
        self.chapter_summaries.sort(key=lambda x: x.chapter_num)
        self.save_chapter_summaries()
    
    def update_plot_log(self, summary: ChapterSummary):
        """更新剧情日志到agent配置文件"""
        agent_file = self.project_root / self.config.agent_config_file
        
        # 生成新的日志条目
        log_entry = f"""
### **第{summary.chapter_num}章：{summary.title}**

* **剧情进展:** {summary.content_summary}
* **角色状态:** 
* **关键线索:** 
"""
        
        if agent_file.exists():
            with open(agent_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 在剧情日志部分添加新条目
            if "## 剧情日志" in content:
                content = content.replace("## 剧情日志", f"## 剧情日志{log_entry}")
            else:
                content += f"\n\n## 剧情日志{log_entry}"
                
            with open(agent_file, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def create_next_chapter(self, custom_workflow: Optional[List[WorkflowStep]] = None) -> Dict[str, Any]:
        """创建下一章节"""
        workflow = custom_workflow or self.workflow
        next_chapter_num = self.get_latest_chapter_number() + 1
        
        context = {
            'agent': self,
            'next_chapter_num': next_chapter_num
        }
        
        self.logger.info(f"开始创作第{next_chapter_num}章...")
        
        # 执行工作流
        for step in workflow:
            self.logger.info(f"执行步骤: {step.name}")
            try:
                context = step.execute(context)
            except Exception as e:
                self.logger.error(f"步骤 {step.name} 执行失败: {e}")
                raise
        
        self.logger.info(f"第{next_chapter_num}章创作完成!")
        return context
    
    @classmethod
    def init_project(cls, project_root: str, config: ProjectConfig) -> 'NovelWritingAgent':
        """初始化新项目"""
        project_path = Path(project_root)
        project_path.mkdir(parents=True, exist_ok=True)
        
        # 创建项目配置文件
        agent = cls(project_root, config)
        agent.save_project_config()
        
        # 创建基础文件结构
        (project_path / config.outline_file).touch()
        (project_path / config.agent_config_file).touch()
        
        agent.logger.info(f"项目已初始化: {project_root}")
        return agent

if __name__ == "__main__":
    # 使用示例
    config = ProjectConfig(
        project_name="我的小说",
        author="作者名",
        genre="玄幻"
    )
    
    # 初始化项目
    agent = NovelWritingAgent.init_project("./test_novel", config)
    
    # 创建章节（这会生成创作提示，需要人工或AI完成实际写作）
    result = agent.create_next_chapter()
    print("创作提示:", result.get('chapter_content', ''))