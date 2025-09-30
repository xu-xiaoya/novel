# 通用小说写作 Agent 系统

基于四步工作流的通用小说创作框架，可以适配任何小说项目。

## 系统特点

### 🔥 核心优势
- **通用性**: 不耦合具体小说内容，可适配任何题材
- **模块化**: 四个独立的工作流步骤，可自定义替换
- **可配置**: 支持灵活的项目配置和工作流定制
- **数据管理**: 自动管理角色状态、剧情线索、章节摘要
- **质量控制**: 内置逻辑检查和一致性验证

### 🎯 四步工作流
1. **Review (回顾与分析)**: 分析大纲、前文、角色状态、未解线索
2. **PreCheck (动笔前检查)**: 角色动机检查、情节规划、逻辑一致性验证
3. **Writing (章节创作)**: 基于分析结果生成创作提示或直接生成内容
4. **Finalize (收尾保存)**: 保存章节、生成摘要、更新剧情日志

## 快速开始

### 1. 初始化新项目

```python
from novel_writing_agent import NovelWritingAgent, ProjectConfig

# 创建项目配置
config = ProjectConfig(
    project_name="我的玄幻小说",
    author="作者名",
    genre="玄幻",
    min_word_count=3000,
    target_word_count=5000,
    chapter_naming_pattern="第{num}章 {title}.txt"
)

# 初始化项目
agent = NovelWritingAgent.init_project("./my_novel", config)
```

### 2. 设置故事大纲

在项目根目录创建 `故事大纲.md` 文件，编写你的故事大纲。

### 3. 创建章节

```python
# 加载现有项目
agent = NovelWritingAgent("./my_novel")

# 创建下一章
result = agent.create_next_chapter()

# 获取创作提示
prompt = result['chapter_content']
print(prompt)

# 查看保存的章节路径
print(f"章节已保存到: {result['saved_path']}")
```

## 数据结构

### ProjectConfig - 项目配置
```python
@dataclass
class ProjectConfig:
    project_name: str           # 项目名称
    author: str                # 作者
    genre: str                 # 小说类型
    min_word_count: int        # 最小字数
    target_word_count: int     # 目标字数
    max_word_count: int        # 最大字数
    chapter_naming_pattern: str # 章节命名模式
    outline_file: str          # 大纲文件名
    agent_config_file: str     # Agent配置文件名
```

### CharacterInfo - 角色信息
```python
@dataclass
class CharacterInfo:
    name: str                  # 角色名
    description: str           # 角色描述
    current_state: Dict        # 当前状态（境界、位置等）
```

### PlotThread - 剧情线索
```python
@dataclass
class PlotThread:
    id: str                    # 线索ID
    description: str           # 线索描述
    status: str                # 状态: active/resolved/pending
    priority: str              # 优先级: high/medium/low
    first_chapter: int         # 首次出现章节
    last_chapter: int          # 最后更新章节
```

### ChapterSummary - 章节摘要
```python
@dataclass
class ChapterSummary:
    chapter_num: int           # 章节号
    title: str                 # 章节标题
    content_summary: str       # 内容摘要
    characters_involved: List  # 涉及角色
    plot_threads: List         # 相关线索
    key_events: List           # 关键事件
    word_count: int            # 字数
    created_time: str          # 创建时间
```

## 工作流自定义

### 自定义工作流步骤

```python
from novel_writing_agent import WorkflowStep

class CustomWritingStep(WorkflowStep):
    def __init__(self, ai_client):
        super().__init__("custom_writing", "AI自动创作")
        self.ai_client = ai_client
    
    def execute(self, context):
        # 使用AI生成内容
        prompt = self.generate_prompt(context)
        content = self.ai_client.generate(prompt)
        context['chapter_content'] = content
        return context

# 使用自定义工作流
custom_workflow = [
    ReviewStep(),
    PreWritingCheckStep(),
    CustomWritingStep(my_ai_client),
    FinalizeStep()
]

result = agent.create_next_chapter(custom_workflow)
```

### 内容生成器

```python
def my_content_generator(context):
    \"\"\"自定义内容生成器\"\"\"
    review = context['review_result']
    # 基于分析结果生成实际章节内容
    return "生成的章节内容..."

# 创建带自定义生成器的工作流
writing_step = WritingStep(content_generator=my_content_generator)
custom_workflow = [ReviewStep(), PreWritingCheckStep(), writing_step, FinalizeStep()]

result = agent.create_next_chapter(custom_workflow)
```

## API 接口

### 核心方法

```python
# 项目管理
agent = NovelWritingAgent.init_project(path, config)  # 初始化项目
agent = NovelWritingAgent(project_root)               # 加载项目

# 章节创作
result = agent.create_next_chapter()                  # 创建下一章
result = agent.create_next_chapter(custom_workflow)   # 使用自定义工作流

# 数据查询
outline = agent.load_outline()                        # 加载大纲
chapters = agent.get_recent_chapters(count=3)         # 获取最近章节
characters = agent.get_all_characters()               # 获取所有角色
threads = agent.get_active_plot_threads()             # 获取活跃线索
unresolved = agent.find_unresolved_threads()          # 查找未解决线索

# 数据管理
agent.add_character(name, info)                       # 添加角色
agent.add_plot_thread(description, priority)          # 添加线索
agent.update_character_state(name, **kwargs)          # 更新角色状态
```

### 文件结构

```
my_novel/
├── project_config.json      # 项目配置
├── 故事大纲.md              # 故事大纲
├── agent.md                 # Agent配置文件
├── .agent_data/             # Agent数据目录
│   ├── characters.json      # 角色数据
│   ├── plot_threads.json    # 剧情线索
│   ├── chapter_summaries.json # 章节摘要
│   └── agent.log           # 运行日志
├── 第1卷/                   # 章节文件
│   ├── 第1章 开始.txt
│   └── 第2章 成长.txt
└── 第2卷/
    └── ...
```

## 适配现有项目

如果你已经有一个小说项目，可以创建适配器来导入现有数据：

```python
class ProjectAdapter:
    \"\"\"项目适配器\"\"\"
    
    def __init__(self, agent, source_format):
        self.agent = agent
        self.source_format = source_format
    
    def import_existing_data(self):
        \"\"\"导入现有数据\"\"\"
        if self.source_format == "gemini":
            self.import_from_gemini()
        # 可以添加其他格式的支持
    
    def import_from_gemini(self):
        \"\"\"从GEMINI.md格式导入\"\"\"
        # 解析现有的剧情日志
        # 提取角色状态
        # 创建章节摘要
        pass

# 使用适配器
adapter = ProjectAdapter(agent, "gemini")
adapter.import_existing_data()
```

## 扩展功能

### 质量检查插件

```python
class QualityChecker:
    def check_word_count(self, content, min_count):
        return len(content) >= min_count
    
    def check_character_consistency(self, content, characters):
        # 检查角色一致性
        pass
    
    def check_plot_logic(self, content, previous_chapters):
        # 检查情节逻辑
        pass
```

### 数据分析插件

```python
class DataAnalyzer:
    def analyze_writing_progress(self, summaries):
        # 分析写作进度
        pass
    
    def analyze_character_development(self, characters):
        # 分析角色发展
        pass
    
    def analyze_plot_threads(self, threads):
        # 分析情节线索
        pass
```

## 最佳实践

1. **定期备份数据**: Agent会自动保存数据，但建议定期备份整个项目目录
2. **合理设置字数**: 根据你的写作习惯设置合理的字数要求
3. **及时更新线索**: 创作过程中及时添加和更新剧情线索
4. **定制工作流**: 根据你的创作习惯定制工作流步骤
5. **使用版本控制**: 建议使用Git等版本控制工具管理项目

## 注意事项

- 这是一个通用框架，实际的内容生成需要你自己实现或接入AI服务
- 系统会生成创作提示，但不会自动生成章节内容（除非你提供内容生成器）
- 数据都保存在本地，确保项目目录的安全性# novel
