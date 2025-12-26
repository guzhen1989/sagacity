# 调度任务管理API

<cite>
**本文档引用文件**  
- [scheduler.py](file://app/routers/scheduler.py)
- [scheduler_service.py](file://app/services/scheduler_service.py)
- [init_scheduler_metadata.py](file://scripts/init_scheduler_metadata.py)
- [scheduler.ts](file://frontend/src/api/scheduler.ts)
- [data_sources.py](file://tradingagents/constants/data_sources.py)
</cite>

## 目录
1. [简介](#简介)
2. [核心功能](#核心功能)
3. [API端点详解](#api端点详解)
4. [任务类型与数据源配置](#任务类型与数据源配置)
5. [任务元数据与存储结构](#任务元数据与存储结构)
6. [权限与安全机制](#权限与安全机制)
7. [错误响应码](#错误响应码)
8. [实际应用示例](#实际应用示例)
9. [最佳实践](#最佳实践)

## 简介

调度任务管理API为系统提供了完整的定时任务管理能力，支持对数据同步、批量分析等关键任务的全生命周期管理。该API基于APScheduler构建，实现了任务的创建、更新、启用/禁用和删除等核心功能，同时提供了丰富的监控和管理接口。

系统通过RESTful API暴露调度器功能，允许管理员用户对定时任务进行精细化控制。所有任务操作都会被记录到MongoDB数据库中，便于审计和故障排查。API设计遵循标准的HTTP协议规范，返回结构化的JSON响应，便于前端集成和自动化脚本调用。

**Section sources**
- [scheduler.py](file://app/routers/scheduler.py#L1-L530)
- [scheduler_service.py](file://app/services/scheduler_service.py#L1-L1161)

## 核心功能

调度任务管理API提供以下核心功能：

- **任务列表管理**：获取所有定时任务的列表，包括任务ID、名称、状态和下次执行时间等基本信息。
- **任务状态控制**：支持暂停和恢复任务执行，允许管理员根据需要临时停止或重新启用任务。
- **手动触发执行**：提供手动触发接口，允许管理员在非预定时间立即执行任务，支持强制执行模式。
- **执行历史追踪**：记录每个任务的执行历史，包括成功、失败和错过的执行记录，便于问题排查。
- **统计与健康检查**：提供调度器的运行统计信息和健康状态检查，帮助监控系统整体运行状况。
- **元数据管理**：支持为任务设置自定义的触发器名称和备注，提高任务的可识别性和管理效率。

这些功能共同构成了一个完整的任务管理解决方案，确保了数据同步和批量处理任务的可靠性和可控性。

**Section sources**
- [scheduler.py](file://app/routers/scheduler.py#L39-L335)
- [scheduler_service.py](file://app/services/scheduler_service.py#L67-L220)

## API端点详解

### 任务管理端点

#### 获取任务列表 (GET /scheduler/jobs)
获取所有定时任务的列表。

**请求示例**:
```http
GET /api/scheduler/jobs
Authorization: Bearer {token}
```

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": "tushare_quotes_sync",
      "name": "tushare_quotes_sync",
      "next_run_time": "2025-10-15T09:05:00",
      "paused": false,
      "trigger": "cron[minute='*/5', ...]",
      "display_name": "Tushare-实时行情同步",
      "description": "从Tushare数据源同步实时行情数据。交易日9:00-15:00每5分钟执行一次。"
    }
  ],
  "message": "获取到 15 个定时任务"
}
```

#### 暂停任务 (POST /scheduler/jobs/{job_id}/pause)
暂停指定任务的执行。

**请求示例**:
```http
POST /api/scheduler/jobs/tushare_quotes_sync/pause
Authorization: Bearer {token}
```

#### 恢复任务 (POST /scheduler/jobs/{job_id}/resume)
恢复已暂停任务的执行。

**请求示例**:
```http
POST /api/scheduler/jobs/tushare_quotes_sync/resume
Authorization: Bearer {token}
```

#### 手动触发任务 (POST /scheduler/jobs/{job_id}/trigger)
手动触发任务执行，支持强制执行模式。

**请求示例**:
```http
POST /api/scheduler/jobs/tushare_quotes_sync/trigger?force=true
Authorization: Bearer {token}
```

**参数说明**:
- `force`: 是否强制执行（跳过交易时间检查等），默认为false

#### 获取任务详情 (GET /scheduler/jobs/{job_id})
获取指定任务的详细信息。

**请求示例**:
```http
GET /api/scheduler/jobs/tushare_quotes_sync
Authorization: Bearer {token}
```

### 执行历史与统计

#### 获取任务执行历史
获取指定任务的执行历史记录。

**请求示例**:
```http
GET /api/scheduler/jobs/tushare_quotes_sync/history?limit=20&offset=0
Authorization: Bearer {token}
```

**查询参数**:
- `limit`: 返回数量限制 (1-100)
- `offset`: 偏移量

#### 获取统计信息
获取调度器的运行统计信息。

**请求示例**:
```http
GET /api/scheduler/stats
Authorization: Bearer {token}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_jobs": 15,
    "running_jobs": 14,
    "paused_jobs": 1,
    "scheduler_running": true,
    "scheduler_state": 1
  },
  "message": "获取统计信息成功"
}
```

#### 健康检查
检查调度器的健康状态。

**请求示例**:
```http
GET /api/scheduler/health
Authorization: Bearer {token}
```

**Section sources**
- [scheduler.py](file://app/routers/scheduler.py#L39-L530)
- [scheduler.ts](file://frontend/src/api/scheduler.ts#L1-L233)

## 任务类型与数据源配置

### 预定义任务类型

系统预定义了多种任务类型，主要分为数据同步和状态检查两大类：

#### 数据同步任务
- **基础信息同步**: 每日同步股票基础信息，包括代码、名称、上市日期等。
- **实时行情同步**: 在交易时段定期同步实时行情数据。
- **历史数据同步**: 交易日收盘后同步历史K线数据。
- **财务数据同步**: 定期同步上市公司财务报表数据。

#### 状态检查任务
- **数据源状态检查**: 定期检查数据源的连接状态和API调用额度。

### 数据源注册机制

系统支持多种数据源的注册和管理，通过`DataSourceRegistry`实现统一管理：

```python
# 数据源注册表示例
DATA_SOURCE_REGISTRY: Dict[str, DataSourceInfo] = {
    # Tushare数据源
    DataSourceCode.TUSHARE: DataSourceInfo(
        code=DataSourceCode.TUSHARE,
        name="Tushare",
        display_name="Tushare",
        provider="Tushare",
        description="专业的A股数据接口，提供高质量的历史数据和实时行情",
        supported_markets=["a_shares"],
        requires_api_key=True,
        is_free=False,
        official_website="https://tushare.pro",
        documentation_url="https://tushare.pro/document/2",
        features=["历史行情", "实时行情", "财务数据", "基本面数据", "新闻公告"],
    ),
    
    # AKShare数据源
    DataSourceCode.AKSHARE: DataSourceInfo(
        code=DataSourceCode.AKSHARE,
        name="AKShare",
        display_name="AKShare",
        provider="AKShare",
        description="开源金融数据库，提供基础股票信息和行情数据",
        supported_markets=["a_shares", "us_stocks", "hk_stocks"],
        requires_api_key=False,
        is_free=True,
        features=["基础信息", "实时行情", "历史数据"]
    )
}
```

### 数据源优先级配置

系统支持配置数据源的优先级，实现自动fallback机制：

1. **Tushare** (优先级1): 专业金融数据API，提供最全面的财务指标
2. **AKShare** (优先级2): 开源金融数据库，提供基础股票信息
3. **BaoStock** (优先级3): 免费证券数据平台，提供历史数据

当主数据源不可用时，系统会自动切换到备用数据源，确保数据获取的连续性。

**Section sources**
- [init_scheduler_metadata.py](file://scripts/init_scheduler_metadata.py#L1-L211)
- [data_sources.py](file://tradingagents/constants/data_sources.py#L75-L109)

## 任务元数据与存储结构

### 任务元数据存储

系统使用MongoDB的`scheduler_metadata`集合存储任务的扩展元数据：

**字段结构**:
- `job_id`: 任务ID (主键)
- `display_name`: 触发器名称（自定义显示名称）
- `description`: 备注（任务详细描述）
- `updated_at`: 更新时间

**索引**:
```javascript
db.scheduler_metadata.createIndex({"job_id": 1}, {unique: true})
```

### 执行历史存储

`scheduler_history`集合用于存储任务的执行历史和操作记录：

**字段结构**:
- `job_id`: 任务ID
- `action`: 操作类型 (pause/resume/trigger/execute)
- `status`: 状态 (success/failed)
- `error_message`: 错误信息（如果有）
- `timestamp`: 时间戳

**索引**:
```javascript
db.scheduler_history.createIndex({"job_id": 1, "timestamp": -1})
db.scheduler_history.createIndex({"timestamp": -1})
db.scheduler_history.createIndex({"status": 1})
```

### 执行记录存储

`scheduler_executions`集合存储详细的执行记录：

**字段结构**:
- `_id`: 执行记录ID (MongoDB ObjectId)
- `job_id`: 任务ID
- `job_name`: 任务名称
- `status`: 执行状态 (running/success/failed/missed)
- `scheduled_time`: 计划执行时间
- `execution_time`: 实际执行耗时（毫秒）
- `timestamp`: 记录时间戳
- `return_value`: 返回值
- `error_message`: 错误信息
- `traceback`: 错误堆栈
- `progress`: 进度百分比
- `progress_message`: 进度消息
- `current_item`: 当前处理项
- `total_items`: 总处理项数
- `processed_items`: 已处理项数
- `updated_at`: 更新时间
- `is_manual`: 是否手动触发
- `cancel_requested`: 取消请求标记

**Section sources**
- [scheduler_service.py](file://app/services/scheduler_service.py#L941-L1026)
- [init_scheduler_metadata.py](file://scripts/init_scheduler_metadata.py#L15-L93)

## 权限与安全机制

### 权限控制

系统实施严格的权限控制机制，确保只有授权用户才能执行敏感操作：

- **查看权限**: 所有登录用户都可以查看任务列表和详情
- **管理权限**: 仅管理员可以执行以下操作：
  - 暂停/恢复任务
  - 手动触发任务
  - 更新任务元数据
  - 取消任务执行

**权限检查示例**:
```python
# 检查管理员权限
if not user.get("is_admin"):
    raise HTTPException(status_code=403, detail="仅管理员可以更新任务元数据")
```

### 操作审计

所有管理操作都会被记录到`scheduler_history`集合中，便于审计和追踪：

- **操作类型**: pause, resume, trigger, execute
- **状态记录**: success, failed
- **时间戳**: 精确到毫秒的操作时间
- **错误信息**: 失败操作的详细错误描述

### 冲突检测与唯一性约束

系统通过以下机制确保任务管理的完整性：

1. **任务ID唯一性**: 每个任务ID在系统中必须唯一，通过MongoDB的唯一索引保证。
2. **并发控制**: 使用异步锁机制防止同一任务的并发操作冲突。
3. **状态一致性**: 在执行状态转换时，系统会验证当前状态是否允许目标操作。

**Section sources**
- [scheduler.py](file://app/routers/scheduler.py#L74-L76)
- [scheduler_service.py](file://app/services/scheduler_service.py#L118-L128)

## 错误响应码

API返回标准的HTTP状态码和详细的错误信息：

| 状态码 | 错误类型 | 说明 |
|--------|---------|------|
| 200 | OK | 请求成功 |
| 400 | Bad Request | 请求参数错误 |
| 403 | Forbidden | 权限不足 |
| 404 | Not Found | 资源不存在 |
| 500 | Internal Server Error | 服务器内部错误 |

**错误响应示例**:
```json
{
  "success": false,
  "message": "暂停任务 tushare_quotes_sync 失败: 任务不存在",
  "data": null
}
```

**常见错误场景**:
- **404错误**: 请求的任务ID不存在
- **403错误**: 非管理员用户尝试执行管理操作
- **500错误**: 调度器服务内部错误或数据库连接问题

**Section sources**
- [scheduler.py](file://app/routers/scheduler.py#L53-L54)
- [scheduler_service.py](file://app/services/scheduler_service.py#L125-L128)

## 实际应用示例

### 配置Tushare数据同步任务

通过API配置Tushare数据源的定时同步任务：

```python
# 创建Tushare实时行情同步任务
import requests

url = "http://localhost:8000/api/scheduler/jobs/tushare_quotes_sync/trigger"
headers = {
    "Authorization": "Bearer your_token_here",
    "Content-Type": "application/json"
}

# 强制执行模式
response = requests.post(f"{url}?force=true", headers=headers)

if response.status_code == 200:
    print("Tushare实时行情同步任务已触发")
else:
    print(f"任务触发失败: {response.json()}")
```

### 配置AkShare数据同步任务

配置AkShare数据源的批量同步任务：

```python
# 获取AkShare任务执行统计
import requests

url = "http://localhost:8000/api/scheduler/jobs/akshare_quotes_sync/execution-stats"
headers = {
    "Authorization": "Bearer your_token_here"
}

response = requests.get(url, headers=headers)
stats = response.json()

print(f"总执行次数: {stats['data']['total']}")
print(f"成功次数: {stats['data']['success']}")
print(f"失败次数: {stats['data']['failed']}")
print(f"平均执行时间: {stats['data']['avg_execution_time']}ms")
```

### 任务依赖关系管理

虽然当前系统未直接支持任务依赖，但可以通过以下方式实现类似功能：

1. **串行执行**: 通过脚本按顺序触发相关任务
2. **条件触发**: 根据前一个任务的执行结果决定是否触发后续任务
3. **状态检查**: 在任务执行前检查依赖任务的状态

```python
# 串行执行示例：先同步基础信息，再同步行情数据
def sync_data_sequence():
    # 1. 触发基础信息同步
    trigger_job("basics_sync_service")
    
    # 2. 等待基础信息同步完成
    wait_for_completion("basics_sync_service")
    
    # 3. 触发行情数据同步
    trigger_job("quotes_ingestion_service")
```

**Section sources**
- [init_scheduler_metadata.py](file://scripts/init_scheduler_metadata.py#L26-L68)
- [scheduler.ts](file://frontend/src/api/scheduler.ts#L205-L233)

## 最佳实践

### 任务配置建议

1. **合理设置执行频率**: 根据数据源的API限制和业务需求设置合适的执行间隔。
2. **使用描述性名称**: 为任务设置清晰的`display_name`和`description`，便于识别和管理。
3. **监控执行状态**: 定期检查任务的执行历史和统计信息，及时发现和解决问题。
4. **备份重要配置**: 定期备份任务配置和元数据，防止意外丢失。

### 故障排查指南

1. **任务未执行**: 检查任务是否被暂停，确认调度器是否正常运行。
2. **执行失败**: 查看执行历史中的错误信息，检查相关服务和数据库连接。
3. **性能问题**: 分析执行耗时，优化任务逻辑或调整执行频率。
4. **数据不一致**: 检查多个数据源的同步状态，确认fallback机制是否正常工作。

### 安全注意事项

1. **保护API密钥**: 确保Tushare等需要API密钥的数据源配置安全。
2. **限制管理员权限**: 仅授予必要人员管理员权限，减少安全风险。
3. **定期审计**: 定期检查操作历史，发现异常操作及时处理。
4. **备份恢复**: 建立完善的备份和恢复机制，确保系统可靠性。

**Section sources**
- [init_scheduler_metadata.py](file://scripts/init_scheduler_metadata.py#L15-L93)
- [scheduler_service.py](file://app/services/scheduler_service.py#L221-L400)