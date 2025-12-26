# DeepSeek配置

<cite>
**本文档引用的文件**  
- [deepseek-config.md](file://docs/configuration/deepseek-config.md)
- [deepseek_adapter.py](file://tradingagents/llm_adapters/deepseek_adapter.py)
- [config_service.py](file://app/services/config_service.py)
- [trading_graph.py](file://tradingagents/graph/trading_graph.py)
- [model_capabilities.py](file://app/constants/model_capabilities.py)
- [demo_deepseek_analysis.py](file://examples/demo_deepseek_analysis.py)
- [demo_deepseek_simple.py](file://examples/demo_deepseek_simple.py)
- [init_providers.py](file://app/scripts/init_providers.py)
- [config.py](file://app/core/config.py)
- [startup_validator.py](file://app/core/startup_validator.py)
</cite>

## 目录
1. [概述](#概述)
2. [API密钥配置](#api密钥配置)
3. [模型版本选择](#模型版本选择)
4. [调用参数设置](#调用参数设置)
5. [系统集成流程](#系统集成流程)
6. [认证机制](#认证机制)
7. [响应处理](#响应处理)
8. [实际配置示例](#实际配置示例)
9. [常见问题排查](#常见问题排查)
10. [与其他模型提供商的协同工作](#与其他模型提供商的协同工作)

## 概述

DeepSeek V3是一款性能强大、性价比极高的大语言模型，在推理、代码生成和中文理解方面表现优秀。本指南将详细介绍如何在TradingAgents中配置和使用DeepSeek V3，包括API密钥配置、模型版本选择、调用参数设置、系统集成流程、认证机制和响应处理等内容。

**Section sources**
- [deepseek-config.md](file://docs/configuration/deepseek-config.md#L1-L220)

## API密钥配置

### 获取API密钥

1. **注册DeepSeek账号**
   - 访问 [DeepSeek平台](https://platform.deepseek.com/)
   - 点击"Sign Up"注册账号
   - 使用邮箱或手机号完成注册
   - 验证邮箱或手机号

2. **获取API密钥**
   - 登录DeepSeek控制台
   - 进入"API Keys"页面
   - 点击"Create API Key"
   - 设置密钥名称（如：TradingAgents）
   - 复制生成的API密钥（格式：sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx）

### 环境变量配置

在项目根目录的`.env`文件中添加：

```bash
# DeepSeek V3配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_ENABLED=true
```

**Section sources**
- [deepseek-config.md](file://docs/configuration/deepseek-config.md#L15-L41)
- [demo_deepseek_analysis.py](file://examples/demo_deepseek_analysis.py#L26-L38)
- [demo_deepseek_simple.py](file://examples/demo_deepseek_simple.py#L16-L18)

## 模型版本选择

### 支持的模型

| 模型名称 | 说明 | 适用场景 | 上下文长度 | 推荐度 |
|---------|------|---------|-----------|--------|
| **deepseek-chat** | 通用对话模型 | 股票投资分析、推荐使用 | 128K | ⭐⭐⭐⭐⭐ |
| **deepseek-coder** | 代码专用模型 | 代码生成和分析 | 128K | ⭐⭐⭐⭐ |
| **deepseek-reasoner** | 推理专用模型 | 复杂逻辑推理 | 128K | ⭐⭐⭐ |

### 模型选择建议

- **日常分析**：使用deepseek-chat，通用性强，性价比高
- **逻辑分析**：使用deepseek-coder，逻辑推理能力强
- **深度推理**：使用deepseek-reasoner，复杂问题分析
- **长文本**：优先使用deepseek-chat，支持128K上下文

**Section sources**
- [deepseek-config.md](file://docs/configuration/deepseek-config.md#L43-L52)
- [model_capabilities.py](file://app/constants/model_capabilities.py#L186-L193)
- [config_service.py](file://app/services/config_service.py#L2533-L2542)

## 调用参数设置

### 基础参数

```python
# 推荐的参数设置
adapter = create_deepseek_adapter(
    model="deepseek-chat",
    temperature=0.1,  # 降低随机性，提高一致性
    max_tokens=2000   # 适中的输出长度
)
```

### 高级参数

```python
# 快速分析（成本优先）
config = {
    "temperature": 0.1,
    "max_tokens": 1000,
    "max_debate_rounds": 1
}

# 深度分析（质量优先）
config = {
    "temperature": 0.05,
    "max_tokens": 3000,
    "max_debate_rounds": 2
}
```

### 缓存策略

```python
# 启用缓存减少重复调用
config["enable_cache"] = True
config["cache_ttl"] = 3600  # 1小时缓存
```

**Section sources**
- [deepseek-config.md](file://docs/configuration/deepseek-config.md#L124-L129)
- [usage/deepseek-usage-guide.md](file://docs/usage/deepseek-usage-guide.md#L207-L229)

## 系统集成流程

### Web界面配置

1. 启动Web界面：`streamlit run web/app.py`
2. 进入"配置管理"页面
3. 在"模型配置"中找到DeepSeek模型
4. 填入API Key
5. 启用相应的模型

### CLI使用

```bash
# 启动CLI
python -m cli.main

# 选择DeepSeek V3作为LLM提供商
# 选择DeepSeek模型
# 开始分析
```

### 编程接口

```python
from tradingagents.llm.deepseek_adapter import create_deepseek_adapter

# 创建DeepSeek适配器
adapter = create_deepseek_adapter(model="deepseek-chat")

# 获取模型信息
info = adapter.get_model_info()
print(f"使用模型: {info['model']}")

# 创建智能体
from langchain.tools import tool

@tool
def get_stock_price(symbol: str) -> str:
    """获取股票价格"""
    return f"股票{symbol}的价格信息"

agent = adapter.create_agent(
    tools=[get_stock_price],
    system_prompt="你是股票分析专家"
)

# 执行分析
result = agent.invoke({"input": "分析AAPL股票"})
print(result["output"])
```

**Section sources**
- [deepseek-config.md](file://docs/configuration/deepseek-config.md#L54-L109)
- [demo_deepseek_analysis.py](file://examples/demo_deepseek_analysis.py#L46-L238)
- [demo_deepseek_simple.py](file://examples/demo_deepseek_simple.py#L13-L35)

## 认证机制

### 认证流程

1. **环境变量认证**
   - 从环境变量`DEEPSEEK_API_KEY`读取API密钥
   - 验证API密钥的有效性（排除占位符）
   - 如果环境变量中的API密钥无效，将被忽略

2. **Web界面认证**
   - 在Web界面配置API Key（设置 -> 大模型厂家）
   - 系统会优先使用Web界面配置的API Key

### 认证验证

```python
# 检查配置
from tradingagents.llm.deepseek_adapter import DeepSeekAdapter
print(DeepSeekAdapter.is_available())
```

### 错误处理

```python
if not api_key:
    raise ValueError(
        "DeepSeek API密钥未找到。请在 Web 界面配置 API Key "
        "(设置 -> 大模型厂家) 或设置 DEEPSEEK_API_KEY 环境变量。"
    )
```

**Section sources**
- [deepseek_adapter.py](file://tradingagents/llm_adapters/deepseek_adapter.py#L76-L93)
- [startup_validator.py](file://app/core/startup_validator.py#L94-L96)

## 响应处理

### 响应结构

```python
# 响应包含token使用量
response = {
    "input_tokens": 1500,
    "output_tokens": 800,
    "cost": 0.005,
    "session_id": "deepseek_12345",
    "analysis_type": "stock_analysis"
}
```

### Token统计

```python
# 记录token使用量
if TOKEN_TRACKING_ENABLED and (input_tokens > 0 or output_tokens > 0):
    try:
        usage_record = token_tracker.track_usage(
            provider="deepseek",
            model_name=self.model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            session_id=session_id,
            analysis_type=analysis_type
        )
    except Exception as track_error:
        logger.error(f"⚠️ [DeepSeek] Token统计失败: {track_error}", exc_info=True)
```

### 成本计算

```python
# DeepSeek V3定价
- 输入：¥0.14/百万tokens
- 输出：¥0.28/百万tokens
- 平均：约¥0.21/百万tokens
```

**Section sources**
- [deepseek_adapter.py](file://tradingagents/llm_adapters/deepseek_adapter.py#L127-L185)
- [usage/deepseek-usage-guide.md](file://docs/usage/deepseek-usage-guide.md#L234-L249)

## 实际配置示例

### 基础配置

```bash
# 编辑.env文件
DEEPSEEK_API_KEY=sk-your_deepseek_api_key_here
DEEPSEEK_ENABLED=true
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 高级选项

```python
# 完整的配置示例
config = {
    "llm_provider": "deepseek",
    "llm_model": "deepseek-chat",
    "quick_think_llm": "deepseek-chat",
    "deep_think_llm": "deepseek-chat",
    "backend_url": "https://api.deepseek.com",
    "temperature": 0.1,
    "max_tokens": 2000,
    "enable_cache": True,
    "cache_ttl": 3600,
    "cost_alert_threshold": 10.0,
    "enable_cost_tracking": True
}
```

### Docker配置

```bash
# docker-compose.yml 已自动配置
# 只需在.env文件中设置API密钥即可

# 重启服务应用配置
docker-compose restart web
```

**Section sources**
- [guides/deepseek-usage-guide.md](file://docs/guides/deepseek-usage-guide.md#L68-L83)
- [usage/deepseek-usage-guide.md](file://docs/usage/deepseek-usage-guide.md#L113-L122)

## 常见问题排查

### 常见问题

#### 1. API密钥错误
```
错误：Authentication failed
解决：检查API Key是否正确，确保以sk-开头
```

#### 2. 网络连接问题
```
错误：Connection timeout
解决：检查网络连接，确保可以访问api.deepseek.com
```

#### 3. 配置未生效
```
错误：DeepSeek not enabled
解决：确保DEEPSEEK_ENABLED=true
```

### 调试方法

1. **检查配置**：
```python
from tradingagents.llm.deepseek_adapter import DeepSeekAdapter
print(DeepSeekAdapter.is_available())
```

2. **测试连接**：
```bash
python tests/test_deepseek_integration.py
```

3. **查看日志**：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Section sources**
- [deepseek-config.md](file://docs/configuration/deepseek-config.md#L140-L178)
- [usage/deepseek-usage-guide.md](file://docs/usage/deepseek-usage-guide.md#L298-L334)

## 与其他模型提供商的协同工作

### 智能模型路由

```bash
# 配置智能路由
LLM_SMART_ROUTING=true
LLM_PRIORITY_ORDER=deepseek,qwen,gemini,openai

# 路由策略:
- 常规分析 → DeepSeek V3 (成本优化)
- 复杂推理 → Gemini (推理能力)
- 中文内容 → 通义千问 (中文理解)
- 通用任务 → GPT-4 (综合能力)
```

### 优先级设置策略

1. **成本优先策略**
   - 将DeepSeek设置为最高优先级
   - 用于日常分析和常规任务
   - 最大化成本效益

2. **质量优先策略**
   - 将GPT-4或Claude设置为最高优先级
   - 用于复杂推理和深度分析
   - 确保分析质量

3. **混合策略**
   - 根据任务类型动态选择模型
   - 平衡成本和质量
   - 实现最优性价比

### 协同工作模式

```python
# 多模型协同分析
ta = TradingAgentsGraph(
    selected_analysts=["fundamentals", "market", "news"],
    config=config
)

# 获得综合分析结果
result = ta.run_analysis("AAPL", "2025-01-08")
```

**Section sources**
- [guides/deepseek-usage-guide.md](file://docs/guides/deepseek-usage-guide.md#L137-L148)
- [init_providers.py](file://app/scripts/init_providers.py#L68-L77)