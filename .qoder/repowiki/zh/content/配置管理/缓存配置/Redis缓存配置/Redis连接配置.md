# Redis连接配置

<cite>
**本文档引用的文件**   
- [redis_client.py](file://app/core/redis_client.py)
- [config.py](file://app/core/config.py)
- [.env.example](file://.env.example)
- [.env.docker](file://.env.docker)
- [config_service.py](file://app/services/config_service.py)
</cite>

## 目录
1. [Redis连接参数配置](#redis连接参数配置)
2. [连接池配置](#连接池配置)
3. [超时设置](#超时设置)
4. [Docker环境配置](#docker环境配置)
5. [环境变量优先级](#环境变量优先级)
6. [错误处理与重试策略](#错误处理与重试策略)

## Redis连接参数配置

Redis连接参数通过系统配置文件进行设置，主要包括主机地址、端口、密码和数据库索引。这些参数在`app/core/config.py`文件中定义为Pydantic模型的字段，具有默认值和类型检查。

在配置文件中，Redis连接参数通过以下环境变量进行设置：
- **REDIS_HOST**: Redis服务器主机地址，默认为`localhost`
- **REDIS_PORT**: Redis服务器端口，默认为`6379`
- **REDIS_PASSWORD**: Redis认证密码，默认为空
- **REDIS_DB**: Redis数据库索引，默认为`0`

这些参数通过`REDIS_URL`属性构建完整的Redis连接URL。当密码存在时，URL格式为`redis://:{password}@{host}:{port}/{db}`；当密码为空时，格式为`redis://{host}:{port}/{db}`。

在`.env.example`文件中提供了配置示例，其中包含必需的Redis连接配置：
```bash
# [REQUIRED] Redis 缓存连接
# 用于缓存、会话管理、实时通知等
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=tradingagents123
REDIS_DB=0
```

**Section sources**
- [config.py](file://app/core/config.py#L57-L61)
- [.env.example](file://.env.example#L25-L28)

## 连接池配置

Redis连接池的配置对系统性能有重要影响。连接池通过`REDIS_MAX_CONNECTIONS`参数控制最大连接数，该参数在`app/core/config.py`中定义，默认值为20。

在`app/core/redis_client.py`中，连接池通过`redis.ConnectionPool.from_url()`方法创建，使用配置文件中的`REDIS_MAX_CONNECTIONS`值作为`max_connections`参数。连接池的配置还包括：
- **retry_on_timeout**: 是否在超时时重试，默认为`True`
- **decode_responses**: 是否自动解码响应为字符串，默认为`True`
- **socket_keepalive**: 是否启用TCP keepalive，默认为`True`
- **health_check_interval**: 健康检查间隔，设置为30秒

TCP keepalive的详细配置包括：
- **TCP_KEEPIDLE**: 60秒后开始发送keepalive探测
- **TCP_KEEPINTVL**: 每10秒发送一次探测
- **TCP_KEEPCNT**: 最多发送3次探测

这些配置有助于维持长连接的稳定性，防止因网络空闲导致的连接中断。

**Section sources**
- [redis_client.py](file://app/core/redis_client.py#L23-L35)
- [config.py](file://app/core/config.py#L62-L63)

## 超时设置

系统对Redis连接设置了多种超时机制以确保稳定性和性能。在`app/core/redis_client.py`中，连接初始化时设置了健康检查间隔为30秒，这意味着每30秒会检查一次连接的健康状态。

在`app/services/config_service.py`中，进行Redis连接测试时设置了5秒的连接超时：
```python
redis_params = {
    "host": host,
    "port": port,
    "decode_responses": True,
    "socket_connect_timeout": 5
}
```

当连接失败时，系统会根据错误信息提供具体的错误处理建议：
- **认证失败**: 提示检查用户名和密码
- **连接被拒绝**: 提示检查主机地址和端口
- **连接超时**: 提示检查网络和防火墙设置
- **权限不足**: 提示检查用户权限配置

这些超时设置确保了系统在Redis服务不可用时能够快速失败并提供有意义的错误信息，而不是无限期等待。

**Section sources**
- [redis_client.py](file://app/core/redis_client.py#L34)
- [config_service.py](file://app/services/config_service.py#L1898)
- [config_service.py](file://app/services/config_service.py#L1826-L1839)

## Docker环境配置

在Docker环境中，Redis配置有特殊处理。系统会检测是否运行在Docker容器中，并根据环境自动调整配置。这种检测通过检查`/.dockerenv`文件是否存在或`DOCKER_CONTAINER`环境变量是否为`true`来实现。

在Docker环境下，当Redis主机配置为`localhost`时，系统会自动将其替换为`redis`，这是Docker服务发现的常见模式。这一逻辑在`app/services/config_service.py`中实现：
```python
if is_docker and host == 'localhost':
    host = 'redis'
    logger.info(f"🐳 检测到 Docker 环境，将 Redis host 从 localhost 改为 redis")
```

`.env.docker`文件提供了Docker环境下的配置示例，其中明确设置了`REDIS_HOST=redis`，并使用了更强的密码：
```bash
# Redis配置（Docker环境使用服务名，带密码）
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=tradingagents123
REDIS_DB=0
REDIS_URL=redis://:tradingagents123@redis:6379/0
REDIS_MAX_CONNECTIONS=50
```

Docker环境下的最大连接数设置为50，高于本地开发环境的20，以适应容器化部署可能面临的更高并发需求。

**Section sources**
- [config_service.py](file://app/services/config_service.py#L1861-L1879)
- [.env.docker](file://.env.docker#L123-L128)

## 环境变量优先级

系统采用分层配置机制，环境变量的优先级高于配置文件中的默认值。这种机制允许在不同部署环境中灵活调整配置，而无需修改代码。

配置优先级从高到低为：
1. 环境变量
2. 配置文件
3. 代码中的默认值

在`app/services/config_service.py`中，系统首先尝试从环境变量获取Redis配置：
```python
env_host = os.getenv('REDIS_HOST')
env_port = os.getenv('REDIS_PORT')
env_password = os.getenv('REDIS_PASSWORD')
env_db = os.getenv('REDIS_DB')
```

如果环境变量存在，则使用环境变量的值；否则使用配置文件中的值。这种设计使得在Docker部署、云环境或CI/CD管道中可以轻松覆盖默认配置。

此外，系统还实现了配置验证功能，可以检查Redis配置是否完整，并在配置缺失时提供详细的错误信息和修复建议。

**Section sources**
- [config_service.py](file://app/services/config_service.py#L1864-L1891)
- [config.py](file://app/core/config.py#L66-L71)

## 错误处理与重试策略

系统实现了完善的Redis连接错误处理和重试机制。在`app/core/redis_client.py`中，`init_redis()`函数使用try-catch块捕获所有连接异常，并记录详细的错误信息：

```python
try:
    # 初始化连接...
    await redis_client.ping()
    logger.info(f"✅ Redis连接成功建立...")
except Exception as e:
    logger.error(f"❌ Redis连接失败: {e}")
    raise
```

当连接失败时，系统会根据错误类型提供具体的诊断信息。例如，在`app/services/config_service.py`中，系统会分析错误消息并返回用户友好的错误描述：
- "认证失败，请检查用户名和密码"
- "连接被拒绝，请检查主机地址和端口"
- "连接超时，请检查网络和防火墙设置"

对于连接超时的情况，系统设置了5秒的连接超时和30秒的健康检查间隔，平衡了快速失败和连接稳定性的需求。

系统还实现了连接泄漏防护机制，确保在连接测试完成后正确关闭连接：
```python
# 测试完成后关闭连接
await redis_client.close()
```

这种全面的错误处理策略确保了系统在Redis服务不可用时能够优雅降级，提供有意义的错误信息，并防止资源泄漏。

**Section sources**
- [redis_client.py](file://app/core/redis_client.py#L44-L46)
- [config_service.py](file://app/services/config_service.py#L1826-L1839)
- [config_service.py](file://app/services/config_service.py#L1921-L1922)