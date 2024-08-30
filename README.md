
# Parse-Yt-Channels

Parse-Yt-Channels 是一个用于解析 YouTube 频道信息的开源工具。它可以帮助开发者从 YouTube 频道中提取和整理信息，便于进一步的数据分析或应用集成。

## 功能简介

- **解析频道信息**：自动提取 YouTube 频道的基本信息，包括频道名称、描述、订阅者数量、视频总数等。
- **数据输出**：以结构化的方式输出解析结果，便于在应用中使用或导出为其他格式。
- **扩展性**：支持定制化的解析逻辑，能够满足特定场景下的需求。

## 项目优势

- **简单易用**：通过简单的调用即可获取所需的频道信息，无需复杂的设置或配置。
- **高效**：采用优化的算法，能够快速解析大量频道数据，适合需要批量处理的场景。
- **开源与可定制**：源代码公开，允许开发者根据自己的需求进行修改和扩展。

## 适用场景

- **数据分析**：适用于需要收集和分析 YouTube 频道数据的场景，如市场研究、竞争分析等。
- **内容聚合**：可以用于内容聚合平台，用于获取并展示多个频道的关键信息。
- **自动化工具**：适合需要从 YouTube 频道中自动提取信息的自动化工具，如爬虫或数据处理脚本。

## 安装指南

### 先决条件

- Python 版本 3.6 及以上
- pip 包管理工具
- 准备好astradb的API信息，包括对应collection
- 准备好ollam环境，其中需要安装两个模型：llama3.1, nomic-embed-text

### 安装步骤

1. 克隆项目代码至本地：

   ```bash
   git clone https://github.com/winglight/Parse-Yt-Channels.git
   ```

2. 进入项目目录：

   ```bash
   cd Parse-Yt-Channels
   ```

3. 安装所需依赖：

   ```bash
   pip install -r requirements.txt
   ```

4. 配置环境变量：

   ```bash
    ASTRA_TOKEN=
    ASTRA_DB_ENDPOINT=
    ASTRA_COLLECTION=youtube_scripts
    CHUNK_SIZE=1000
    CHUNK_OVERLAP=200
    CHANNEL_NAME=
    YOUTUBE_LANG=zh-Hans,zh-Hant,zh-CN
    CHROMA_COLLECTION_NAME=youtube_scripts
    SAVE_DIRECTORY=./data
    OLLAMA_EMBEDDIG_MODEL=nomic-embed-text
    OLLAMA_LLM_MODEL=llama3.1
    OLLAMA_URL=http://localhost:21434
   ```

## 使用指南

### 基本使用

1. 基于命令行运行：

   ```bash
   python main.py CHANNEL_NAME
   ```

## 贡献指南

欢迎贡献代码！如果你有改进或新功能的建议，请提交 Pull Request 或在 Issues 中讨论。

## 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。
