#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小说写作 Agent 系统
基于 GEMINI.md 流程设计的自动化小说创作工具
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

@dataclass
class CharacterState:
    """角色状态数据类"""
    name: str
    cultivation_level: str
    current_status: str
    location: str
    relationships: Dict[str, str]
    special_items: List[str]
    
@dataclass
class PlotThread:
    """剧情线索数据类"""
    thread_id: str
    description: str
    status: str  # "active", "resolved", "pending"
    first_mentioned_chapter: int
    last_updated_chapter: int
    priority: str  # "high", "medium", "low"

@dataclass
class ChapterSummary:
    """章节摘要数据类"""
    chapter_num: int
    title: str
    plot_progress: str
    character_states: List[CharacterState]
    key_events: List[str]
    plot_threads: List[PlotThread]
    word_count: int
    created_time: str

class NovelAgent:
    """小说写作 Agent 核心类"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.outline_file = self.project_root / "故事大纲.md"
        self.gemini_file = self.project_root / ".gemini" / "GEMINI.md"
        self.data_dir = self.project_root / ".agent_data"
        self.data_dir.mkdir(exist_ok=True)
        
        # 初始化日志
        self.setup_logging()
        
        # 初始化数据存储
        self.characters_file = self.data_dir / "characters.json"
        self.plot_threads_file = self.data_dir / "plot_threads.json"
        self.chapter_summaries_file = self.data_dir / "chapter_summaries.json"
        
        # 加载数据
        self.characters = self.load_characters()
        self.plot_threads = self.load_plot_threads()
        self.chapter_summaries = self.load_chapter_summaries()
        
        # 加载配置
        self.config = self.load_config()
        
    def setup_logging(self):
        """设置日志系统"""
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
        
    def load_config(self) -> Dict:
        """加载配置文件"""
        config_file = self.data_dir / "config.json"
        default_config = {
            "min_word_count": 6000,
            "target_word_count": 8000,
            "max_word_count": 12000,
            "writing_style": "网文风格",
            "perspective": "第三人称",
            "auto_save": True,
            "backup_chapters": True
        }
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = default_config
            self.save_config(config)
            
        return config
        
    def save_config(self, config: Dict):
        """保存配置文件"""
        config_file = self.data_dir / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
    def load_characters(self) -> Dict[str, CharacterState]:
        """加载角色状态数据"""
        if self.characters_file.exists():
            with open(self.characters_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {name: CharacterState(**char_data) for name, char_data in data.items()}
        return {}
        
    def save_characters(self):
        """保存角色状态数据"""
        data = {name: asdict(char) for name, char in self.characters.items()}
        with open(self.characters_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def load_plot_threads(self) -> Dict[str, PlotThread]:
        """加载剧情线索数据"""
        if self.plot_threads_file.exists():
            with open(self.plot_threads_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {tid: PlotThread(**thread_data) for tid, thread_data in data.items()}
        return {}
        
    def save_plot_threads(self):
        """保存剧情线索数据"""
        data = {tid: asdict(thread) for tid, thread in self.plot_threads.items()}
        with open(self.plot_threads_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def load_chapter_summaries(self) -> List[ChapterSummary]:
        """加载章节摘要数据"""
        if self.chapter_summaries_file.exists():
            with open(self.chapter_summaries_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                summaries = []
                for summary_data in data:
                    summary_data['character_states'] = [CharacterState(**cs) for cs in summary_data['character_states']]
                    summary_data['plot_threads'] = [PlotThread(**pt) for pt in summary_data['plot_threads']]
                    summaries.append(ChapterSummary(**summary_data))
                return summaries
        return []
        
    def save_chapter_summaries(self):
        """保存章节摘要数据"""
        data = []
        for summary in self.chapter_summaries:
            summary_dict = asdict(summary)
            data.append(summary_dict)
        with open(self.chapter_summaries_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def get_latest_chapter_number(self) -> int:
        """获取最新章节号"""
        if self.chapter_summaries:
            return max(summary.chapter_num for summary in self.chapter_summaries)
        
        # 从 GEMINI.md 剧情日志中解析
        if self.gemini_file.exists():
            with open(self.gemini_file, 'r', encoding='utf-8') as f:
                content = f.read()
                chapter_pattern = r'### \*\*第(\d+)章'
                chapters = re.findall(chapter_pattern, content)
                if chapters:
                    return max(int(ch) for ch in chapters)
        
        return 0
        
    def get_volume_info(self, chapter_num: int) -> Tuple[str, str]:
        """根据章节号获取卷信息"""
        volume_mapping = {
            range(1, 16): ("第一卷", "青阳崛起"),
            range(16, 31): ("第二卷", "龙潜于渊"),
            range(31, 48): ("第三卷", "名动天下"),
            range(48, 61): ("第四卷", "初临上界"),
            range(61, 79): ("第五卷", "剑冠群雄"),
            range(79, 93): ("第六卷", "圣地风云"),
            range(93, 107): ("第七卷", "远古遗迹"),
            range(107, 126): ("第八卷", "万界天骄战"),
        }
        
        for chapter_range, (volume_name, volume_title) in volume_mapping.items():
            if chapter_num in chapter_range:
                return volume_name, volume_title
                
        return "未知卷", "未知标题"
        
    def find_volume_directory(self, volume_name: str) -> Optional[Path]:
        """查找卷目录"""
        for item in self.project_root.iterdir():
            if item.is_dir() and volume_name in item.name:
                return item
        return None

if __name__ == "__main__":
    # 简单测试
    agent = NovelAgent("/Users/xiaoyu/逆天仙途：因果投资万倍返还！")
    print(f"最新章节: {agent.get_latest_chapter_number()}")
    print(f"项目根目录: {agent.project_root}")