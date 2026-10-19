# SwissBioPics MCP 服务器

**版本 0.1.0**

> ⚠️ **免责声明**：这是一个**非官方的第三方实现**，并非由 SIB 瑞士生物信息学研究所或 SwissBioPics 团队官方维护。本项目独立开发，与 SwissBioPics 官方无任何关联。SwissBioPics 的所有图像和数据版权归 SIB 所有。

一个 [MCP（模型上下文协议）](https://modelcontextprotocol.io/) 服务器，为 AI 助手提供对 [SwissBioPics](https://www.swissbiopics.org/) 的访问能力——SwissBioPics 是一个用于可视化亚细胞位置数据的免费交互式生物学图像库。

---

## 目录

- [概述](#概述)
- [关于 SwissBioPics](#关于-swissbiopics)
- [功能特性](#功能特性)
- [环境要求](#环境要求)
- [安装](#安装)
- [配置](#配置)
  - [Claude 桌面版](#claude-桌面版)
  - [Cursor](#cursor)
  - [VS Code（Copilot Chat）](#vs-codecopilot-chat)
  - [通用 MCP 客户端](#通用-mcp-客户端)
- [可用工具](#可用工具)
- [使用示例](#使用示例)
- [查询语法](#查询语法)
- [项目结构](#项目结构)
- [开发](#开发)
- [许可与引用](#许可与引用)
- [致谢](#致谢)

---

## 概述

[SwissBioPics](https://www.swissbiopics.org/) 是由 SIB 瑞士生物信息学研究所 Swiss-Prot 团组开发的资源。它提供了一个涵盖所有生命王国的细胞图像交互库——从动物细胞（肌肉细胞、神经元细胞、上皮细胞等）到真菌细胞、植物细胞、古菌细胞，以及各种细菌形态（杆状、球状、螺旋状等）。

本 MCP 服务器通过一组工具将 SwissBioPics 的数据和功能暴露给 AI 助手（如 Claude、ChatGPT 等），使其能够以对话方式查询亚细胞位置数据、细胞类型图像和生物学描述。

> **English Documentation**: [README.md](./README.md)

---

## 关于 SwissBioPics

SwissBioPics 是一个免费的交互式生物学图像库，用于可视化亚细胞位置数据，涵盖所有生命王国的细胞类型。

- **网站**：https://www.swissbiopics.org/
- **许可证**：[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)（知识共享署名 4.0 国际许可）
- **引用文献**：SwissBioPics - an interactive library of cell images for the visualization of subcellular location data. PMID: [35411389](https://pubmed.ncbi.nlm.nih.gov/35411389/)，DOI: [10.1093/database/baac026](https://doi.org/10.1093/database/baac026)
- **NPM 包**：[@swissprot/swissbiopics-visualizer](https://www.npmjs.com/package/@swissprot/swissbiopics-visualizer)
- **开发方**：SIB 瑞士生物信息学研究所 Swiss-Prot 团组

---

## 功能特性

本 MCP 服务器提供以下功能：

1. **🔍 搜索** — 使用高级查询语法（AND、OR、NOT、通配符、模糊搜索、精确短语）搜索亚细胞位置和细胞类型。
2. **💡 自动补全** — 在用户输入时获取搜索建议。
3. **📋 细胞类型列表** — 列出 SwissBioPics 首页上所有可用的细胞类型。
4. **🔬 细胞类型详情** — 通过 ID 或名称获取特定细胞类型的元数据。
5. **🖼️ SVG 获取** — 获取细胞类型的原始 SVG 插图。
6. **📍 位置提取** — 从细胞类型的 SVG 中提取所有亚细胞位置（SL ID、名称、描述）。
7. **📖 位置详情** — 通过 SL 标识符查询特定亚细胞位置的详细描述。
8. **ℹ️ 项目信息** — 获取 SwissBioPics 项目的概况信息。

---

## 环境要求

- **Python 3.10+**（支持 3.10、3.11、3.12、3.13）
- **[uv](https://docs.astral.sh/uv/)** — 快速 Python 包管理器（推荐）或 `pip`
- MCP 兼容客户端（如 Claude 桌面版、Cursor、VS Code Copilot Chat 或其他 MCP 客户端）

---

## 安装

### 方式 A：使用 `uv`（推荐）

```bash
# 克隆仓库
git clone https://github.com/ZengZichao/SwissBioPics-MCP.git
cd SwissBioPics-MCP

# 使用 uv 安装依赖
uv sync
```

### 方式 B：使用 `pip`

```bash
git clone https://github.com/ZengZichao/SwissBioPics-MCP.git
cd SwissBioPics-MCP

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 以开发模式安装
pip install -e .
```

---

## 配置

### Claude 桌面版

编辑 Claude 配置文件：

- **macOS**：`~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**：`%APPDATA%\Claude\claude_desktop_config.json`

添加服务器条目：

```json
{
  "mcpServers": {
    "swissbiopics": {
      "command": "uv",
      "args": [
        "--directory",
        "/绝对路径/到/SwissBioPics-MCP",
        "run",
        "swissbiopics-mcp"
      ]
    }
  }
}
```

> **Windows**：在 JSON 路径中使用双反斜杠（`\\`）或正斜杠（`/`）。请将 `/绝对路径/到/` 替换为您的实际路径，例如 `C:/Users/YourName/Projects/SwissBioPics-MCP`。

如果您使用 `pip` 而非 `uv` 安装，请使用：

```json
{
  "mcpServers": {
    "swissbiopics": {
      "command": "python",
      "args": ["-m", "swissbiopics_mcp.server"],
      "cwd": "/绝对路径/到/SwissBioPics-MCP"
    }
  }
}
```

保存后，重启 Claude 桌面版。

### Cursor

在 Cursor 的 MCP 设置中添加（`Settings → MCP`）：

```json
{
  "mcpServers": {
    "swissbiopics": {
      "command": "uv",
      "args": [
        "--directory",
        "/绝对路径/到/SwissBioPics-MCP",
        "run",
        "swissbiopics-mcp"
      ]
    }
  }
}
```

### VS Code（Copilot Chat）

在工作区或用户设置中的 `.vscode/mcp.json` 中添加：

```json
{
  "servers": {
    "swissbiopics": {
      "command": "uv",
      "args": [
        "--directory",
        "/绝对路径/到/SwissBioPics-MCP",
        "run",
        "swissbiopics-mcp"
      ]
    }
  }
}
```

### 通用 MCP 客户端

本服务器使用 **stdio** 传输协议，可被任何 MCP 兼容客户端启动：

```bash
# 使用 uv 安装
uv run swissbiopics-mcp

# 使用 pip 安装
python -m swissbiopics_mcp.server

# 直接运行
python src/swissbiopics_mcp/server.py
```

---

## 可用工具

| 工具名称 | 描述 |
|----------|------|
| `search_locations` | 使用高级查询语法搜索亚细胞位置和细胞类型。 |
| `get_search_suggestions` | 获取部分搜索查询的自动补全建议。 |
| `get_cell_types` | 列出 SwissBioPics 上所有可用的细胞类型。 |
| `get_cell_type_detail` | 通过 ID 或名称获取特定细胞类型的详情（标题、SVG 文件、URL）。 |
| `get_cell_svg` | 获取细胞类型的原始 SVG 图像内容。 |
| `get_subcellular_locations` | 从细胞类型的 SVG 中提取所有亚细胞位置（SL ID、名称、描述）。 |
| `get_location_detail` | 通过 SL ID 获取特定亚细胞位置的详细描述。 |
| `get_swissbiopics_info` | 获取 SwissBioPics 项目的概况信息。 |

---

## 使用示例

配置服务器后，您可以使用以下示例提示与 AI 助手交互：

### 搜索位置

> *"在 SwissBioPics 中搜索线粒体（mitochondrion）"*

> *"搜索同时包含'内体'和'溶酶体'的细胞类型"*

### 列出细胞类型

> *"SwissBioPics 上有哪些细胞类型？"*

### 获取细胞类型详情

> *"获取细胞类型 8719 的详情"*

> *"展示 SwissBioPics 上的动物细胞（Animal cell）"*

### 获取 SVG

> *"获取动物细胞的 SVG 图像"*

### 探索亚细胞位置

> *"列出动物细胞中的所有亚细胞位置"*

> *"植物细胞中有哪些亚细胞位置？"*

### 查询特定位置

> *"SwissBioPics 中的 SL0173 是什么？"*

> *"获取动物细胞中 SL-0243（分泌型/Secreted）的描述"*

### 获取项目信息

> *"介绍一下 SwissBioPics 项目"*

---

## 查询语法

`search_locations` 工具支持以下查询语法：

| 语法 | 含义 | 示例 |
|------|------|------|
| `词1 词2` | AND — 两个词都必须出现 | `spindle body` |
| `词1 AND 词2` | 显式 AND | `spindle AND body` |
| `词1 OR 词2` | 任一词出现即可 | `SL-0073 OR chromatophore` |
| `"精确短语"` | 精确短语匹配 | `"golgi stack"` |
| `词1 -词2` | NOT — 排除词2 | `endosome -peroxisome` |
| `词1 NOT 词2` | 显式 NOT | `endosome NOT peroxisome` |
| `前缀*` | 通配符前缀 | `bact*` |
| `词~` | 模糊搜索（允许约2个拼写错误） | `rhoptri~`（可找到"rhoptry"） |
| `(…)` | 分组/优先级 | `lumen AND (SL0158 OR wall)` |

---

## 项目结构

```
SwissBioPics-MCP/
├── pyproject.toml                 # 项目元数据和依赖
├── README.md                      # 英文文档
├── README_zh.md                   # 中文文档（本文件）
├── LICENSE                        # MIT 许可证
├── .gitignore                     # Git 忽略规则
├── src/
│   └── swissbiopics_mcp/
│       ├── __init__.py            # 包元数据
│       └── server.py              # MCP 服务器实现
└── tests/
    ├── conftest.py                # Pytest 配置
    ├── test_parsers.py            # 解析函数单元测试
    └── test_tools.py              # MCP 工具函数单元测试
```

---

## 开发

### 环境设置

```bash
# 克隆并以开发模式安装
git clone https://github.com/ZengZichao/SwissBioPics-MCP.git
cd SwissBioPics-MCP
uv sync
```

### 直接运行服务器

```bash
uv run swissbiopics-mcp
```

### 使用 MCP Inspector 调试

```bash
# 使用 uv
uv run mcp dev src/swissbiopics_mcp/server.py

# 或使用 npx
npx @modelcontextprotocol/inspector uv run swissbiopics-mcp
```

### 运行测试

```bash
uv run pytest
```

---

## 许可与引用

### 许可证

本 MCP 服务器代码采用 **MIT 许可证**——详见 [LICENSE](./LICENSE)。

SwissBioPics 的图像和数据采用[知识共享署名 4.0 国际许可（CC BY 4.0）](https://creativecommons.org/licenses/by/4.0/)。使用 SwissBioPics 图像或数据时，请注明 SwissBioPics 为来源。

### 引用

如果您在研究中使用了 SwissBioPics，请引用：

> SwissBioPics - an interactive library of cell images for the visualization of subcellular location data. *Database*. PMID: [35411389](https://pubmed.ncbi.nlm.nih.gov/35411389/)，DOI: [10.1093/database/baac026](https://doi.org/10.1093/database/baac026).

---

## 致谢

- **SwissBioPics** 由 Philippe Le Mercier（内容、图像）、Jerven Bolleman（软件：API/Web 组件）和 Edouard de Castro（软件：编辑器/网站+JS）在 [SIB 瑞士生物信息学研究所](https://www.sib.swiss) [Swiss-Prot 团组](https://www.sib.swiss/alan-bridge-group)开发。
- 获得瑞士联邦政府通过[教育、研究与创新秘书处（SERI）](https://www.sbfi.admin.ch/sbfi/en/home/seri/seri.html)的支持。
- 本 MCP 服务器是独立项目，与 SIB 无官方关联。
