# Google AI配置

<cite>
**本文档引用的文件**   
- [google-ai-setup.md](file://docs/configuration/google-ai-setup.md)
- [google_openai_adapter.py](file://tradingagents/llm_adapters/google_openai_adapter.py)
- [config_service.py](file://app/services/config_service.py)
- [test_google_base_url.py](file://scripts/test_google_base_url.py)
- [google_api_proxy_setup.md](file://docs/integration/google/google_api_proxy_setup.md)
- [token-tracking-guide.md](file://docs/configuration/token-tracking-guide.md)
- [trading_graph.py](file://tradingagents/graph/trading_graph.py)
- [analysis_runner.py](file://web/utils/analysis_runner.py)
</cite>

## 目录
1. [简介](#简介)
2. [认证凭据配置](#认证凭据配置)
3. [项目ID与区域设置](#项目id与区域设置)
4. [Gemini模型集成](#gemini模型集成)
5. [工具调用与流式响应](#工具调用与流式响应)
6. [代理与自定义基础URL](#代理与自定义基础url)
7. [权限管理与配额监控](#权限管理与配额监控)
8. [成本控制建议](#成本控制建议)
9. [路由策略与降级方案](#路由策略与降级方案)

## 简介
本文档详细说明了如何配置Google AI服务，包括认证凭据、项目ID和区域设置的配置方法。文档涵盖了与Gemini等模型的集成方式，包括工具调用和流式响应处理。提供了配置示例，展示如何设置代理和自定义基础URL。同时包含权限管理、配额监控和成本控制建议，以及与其他LLM提供商的路由策略和降级方案。

## 认证凭据配置
Google AI服务的认证凭据配置主要通过API密钥实现。系统支持从环境变量和数据库配置中读取API密钥，并进行有效性验证。

配置方法如下：
1. 在Google AI Studio中创建API密钥
2. 在项目根目录的`.env`文件中添加配置：
```env
GOOGLE_API_KEY=your_google_api_key_here
```
3. 系统会优先使用数据库配置中的API密钥，如果不存在则从环境变量读取

系统会对API密钥进行验证，排除占位符值（如"your_key_here"、"..."等），确保使用的密钥有效。

**Section sources**
- [google-ai-setup.md](file://docs/configuration/google-ai-setup.md#L15-L37)
- [google_openai_adapter.py](file://tradingagents/llm_adapters/google_openai_adapter.py#L51-L86)

## 项目ID与区域设置
Google AI服务的项目ID和区域设置主要通过基础URL（base_url）进行配置。系统支持自定义API端点，允许用户指定不同的区域和部署环境。

默认配置：
- 基础URL: `https://generativelanguage.googleapis.com/v1beta`
- 如果未配置base_url，系统将使用上述默认值

系统会自动处理URL格式：
- 移除末尾的斜杠
- 将`/v1`结尾的URL自动转换为`/v1beta`（Google AI的正确端点）

**Section sources**
- [config_service.py](file://app/services/config_service.py#L3383-L3395)
- [google_openai_adapter.py](file://tradingagents/llm_adapters/google_openai_adapter.py#L100-L134)

## Gemini模型集成
系统支持多种Gemini模型的集成，包括最新版本的Gemini 2.5系列和经典的Gemini 1.5系列。

### 支持的模型
| 模型名称 | 描述 | 上下文长度 | 支持工具调用 |
|--------|------|----------|------------|
| gemini-2.5-pro | 最新旗舰模型，功能强大 | 32768 | 是 |
| gemini-2.5-flash | 最新快速模型 | 32768 | 是 |
| gemini-2.5-flash-lite-preview-06-17 | 超快响应模型 | 32768 | 是 |
| gemini-2.0-flash | 新一代快速模型 | 32768 | 是 |
| gemini-1.5-pro | 强大性能，平衡选择 | 32768 | 是 |
| gemini-1.5-flash | 快速响应，备用选择 | 32768 | 是 |

### 模型选择建议
1. **重要决策**: 推荐使用`gemini-2.5-pro`或`gemini-2.5-pro-002`
2. **日常使用**: 推荐使用`gemini-2.5-flash`或`gemini-2.0-flash`
3. **深度分析**: 使用`gemini-1.5-pro`
4. **快速查询**: 使用`gemini-2.5-flash-lite`或`gemini-1.5-flash`

**Section sources**
- [google-ai-setup.md](file://docs/configuration/google-ai-setup.md#L39-L102)
- [google_openai_adapter.py](file://tradingagents/llm_adapters/google_openai_adapter.py#L295-L348)

## 工具调用与流式响应
系统通过适配器模式实现了Google AI的工具调用功能，解决了Google模型工具调用格式与系统期望不匹配的问题。

### 工具调用实现
1. 创建`ChatGoogleOpenAI`适配器类，继承`ChatGoogleGenerativeAI`
2. 重写生成方法，优化工具调用处理和内容格式
3. 支持绑定工具并进行调用

### 测试工具调用
```python
# 定义测试工具
@tool
def test_news_tool(query: str) -> str:
    """测试新闻工具，返回模拟新闻内容"""
    return f"关于{query}的新闻内容"

# 绑定工具并测试调用
llm_with_tools = llm.bind_tools([test_news_tool])
response = llm_with_tools.invoke("请使用test_news_tool查询'苹果公司'的新闻")
```

系统会追踪工具调用结果，并在日志中记录相关信息。

**Section sources**
- [google_openai_adapter.py](file://tradingagents/llm_adapters/google_openai_adapter.py#L422-L470)
- [google_openai_adapter.py](file://tradingagents/llm_adapters/google_openai_adapter.py#L159-L183)

## 代理与自定义基础URL
系统支持通过代理访问Google AI服务，并允许配置自定义基础URL。

### 代理配置
在`.env`文件中添加代理配置：
```env
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

### 自定义基础URL
支持以下格式的自定义端点：
- `https://generativelanguage.googleapis.com/v1beta`
- `https://generativelanguage.googleapis.com/v1`（自动转换为`/v1beta`）
- 自定义代理地址

系统会根据URL类型进行不同处理：
- Google官方域名：提取域名部分，SDK会自动添加`/v1beta`
- 中转地址：使用完整URL，不添加`/v1beta`

**Section sources**
- [google_api_proxy_setup.md](file://docs/integration/google/google_api_proxy_setup.md#L41-L50)
- [test_google_base_url.py](file://scripts/test_google_base_url.py#L144-L157)

## 权限管理与配额监控
系统实现了完善的权限管理和配额监控机制，确保API调用的安全性和稳定性。

### 权限管理
1. API密钥验证：检查密钥有效性，排除占位符
2. 错误处理：对无效密钥或权限不足的情况提供明确提示
3. 备用方案：当Google AI不可用时，可降级使用其他模型

### 配额监控
系统会自动追踪API调用的token使用量：
- 记录输入和输出token数量
- 关联会话ID和分析类型
- 提供详细的使用统计

**Section sources**
- [google_openai_adapter.py](file://tradingagents/llm_adapters/google_openai_adapter.py#L189-L197)
- [token-tracking-guide.md](file://docs/configuration/token-tracking-guide.md#L9-L13)

## 成本控制建议
系统提供了完整的成本跟踪和控制功能，帮助用户优化使用成本。

### 成本跟踪功能
- 实时记录每次LLM调用的token数量
- 根据供应商定价自动计算使用成本
- 支持JSON文件和MongoDB两种存储方式
- 提供详细的使用统计和成本分析

### 成本控制建议
1. 设置合理的成本警告阈值
2. 定期查看使用统计，优化使用模式
3. 根据需求选择合适的模型（平衡成本和性能）
4. 使用会话ID跟踪特定分析的成本
5. 定期清理旧的使用记录

**Section sources**
- [token-tracking-guide.md](file://docs/configuration/token-tracking-guide.md#L5-L13)
- [token-tracking-guide.md](file://docs/configuration/token-tracking-guide.md#L209-L215)

## 路由策略与降级方案
系统实现了灵活的路由策略和降级方案，确保服务的高可用性。

### 路由策略
1. 配置优先级：模型配置 > 厂家配置 > 默认端点
2. 自动将`/v1`转换为`/v1beta`，避免配置错误
3. 通过`client_options`传递自定义端点给Google AI SDK

### 降级方案
1. **网络问题**: 当Google AI无法访问时，可使用国内可访问的模型（如阿里百炼、DeepSeek）
2. **生产环境**: 推荐使用国内模型或聚合API服务，避免依赖代理
3. **备用选择**: 当主要模型不可用时，自动切换到备用模型

### 生产环境推荐配置
```env
# 使用阿里百炼
DASHSCOPE_API_KEY=your-key
# 或使用DeepSeek
DEEPSEEK_API_KEY=your-key
# 不配置代理
```

**Section sources**
- [google_api_proxy_setup.md](file://docs/integration/google/google_api_proxy_setup.md#L184-L216)
- [test_google_base_url.py](file://scripts/test_google_base_url.py#L153-L157)