# API参考

<cite>
**本文档引用的文件**
- [main.py](file://app/main.py)
- [analysis.py](file://app/routers/analysis.py)
- [stock_data.py](file://app/routers/stock_data.py)
- [stock_sync.py](file://app/routers/stock_sync.py)
- [auth_db.py](file://app/routers/auth_db.py)
- [websocket_notifications.py](file://app/routers/websocket_notifications.py)
- [notifications.py](file://app/routers/notifications.py)
- [reports.py](file://app/routers/reports.py)
- [favorites.py](file://app/routers/favorites.py)
</cite>

## 目录
1. [简介](#简介)
2. [认证机制](#认证机制)
3. [股票分析API](#股票分析api)
4. [批量分析API](#批量分析api)
5. [股票数据API](#股票数据api)
6. [数据同步API](#数据同步api)
7. [用户管理API](#用户管理api)
8. [WebSocket实时通知API](#websocket实时通知api)
9. [REST通知API](#rest通知api)
10. [报告管理API](#报告管理api)
11. [自选股管理API](#自选股管理api)
12. [API版本控制](#api版本控制)

## 简介
sagacity平台提供了一套全面的RESTful API，用于访问股票分析、数据同步、用户管理和实时通知等功能。本API参考文档详细描述了所有公共API端点，包括HTTP方法、URL路径、请求参数、请求体结构、响应格式和状态码。

API基于FastAPI框架构建，遵循RESTful设计原则，提供JSON格式的响应。所有API端点均以`/api`为前缀，并通过JWT令牌进行认证。

**Section sources**
- [main.py](file://app/main.py#L604-L764)

## 认证机制
sagacity平台使用JWT（JSON Web Token）进行API认证。用户需要先通过登录接口获取访问令牌，然后在后续请求的Authorization头中携带该令牌。

### 登录获取令牌
```http
POST /api/auth/login
```

**请求体**
```json
{
  "username": "string",
  "password": "string"
}
```

**响应**
```json
{
  "success": true,
  "data": {
    "access_token": "string",
    "refresh_token": "string",
    "expires_in": 3600,
    "user": {
      "id": "string",
      "username": "string",
      "email": "string",
      "is_admin": false
    }
  },
  "message": "登录成功"
}
```

### 认证头
所有需要认证的API请求都必须在HTTP头中包含Authorization字段：
```
Authorization: Bearer <access_token>
```

**Section sources**
- [auth_db.py](file://app/routers/auth_db.py#L116-L200)

## 股票分析API
股票分析API允许用户提交单股分析任务，并查询任务状态和结果。

### 提交单股分析
```http
POST /api/analysis/single
```

**请求体**
```json
{
  "symbol": "000001",
  "parameters": {
    "research_depth": 3,
    "analysts": ["market_analyst", "fundamental_analyst"]
  }
}
```

**响应**
```json
{
  "success": true,
  "data": {
    "task_id": "string",
    "symbol": "000001",
    "status": "pending",
    "created_at": "2025-10-28T10:00:00Z"
  },
  "message": "分析任务已在后台启动"
}
```

### 查询任务状态
```http
GET /api/analysis/tasks/{task_id}/status
```

**响应**
```json
{
  "success": true,
  "data": {
    "task_id": "string",
    "status": "completed",
    "progress": 100,
    "start_time": "2025-10-28T10:00:00Z",
    "end_time": "2025-10-28T10:05:00Z",
    "elapsed_time": 300,
    "symbol": "000001"
  },
  "message": "任务状态获取成功"
}
```

### 获取分析结果
```http
GET /api/analysis/tasks/{task_id}/result
```

**响应**
```json
{
  "success": true,
  "data": {
    "analysis_id": "string",
    "stock_symbol": "000001",
    "summary": "string",
    "recommendation": "string",
    "confidence_score": 0.85,
    "risk_level": "中等",
    "key_points": ["string"],
    "reports": {
      "market_report": "string",
      "fundamentals_report": "string"
    },
    "decision": {
      "action": "买入",
      "target_price": 15.5,
      "confidence": 0.9
    }
  },
  "message": "分析结果获取成功"
}
```

**Section sources**
- [analysis.py](file://app/routers/analysis.py#L40-L704)

## 批量分析API
批量分析API支持同时对多个股票进行分析。

### 提交批量分析
```http
POST /api/analysis/batch
```

**请求体**
```json
{
  "symbols": ["000001", "600036"],
  "parameters": {
    "research_depth": 2
  },
  "title": "蓝筹股批量分析",
  "description": "对沪深300成分股进行批量分析"
}
```

**响应**
```json
{
  "success": true,
  "data": {
    "batch_id": "string",
    "total_tasks": 2,
    "submitted_at": "2025-10-28T10:00:00Z"
  },
  "message": "批量分析任务已提交"
}
```

### 查询批量任务列表
```http
GET /api/analysis/tasks
```

**查询参数**
- `status`: 任务状态过滤（可选）
- `limit`: 返回数量限制（默认20）
- `offset`: 偏移量（默认0）

**响应**
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "task_id": "string",
        "symbol": "000001",
        "status": "completed",
        "created_at": "2025-10-28T10:00:00Z"
      }
    ],
    "total": 2,
    "limit": 20,
    "offset": 0
  },
  "message": "任务列表获取成功"
}
```

**Section sources**
- [analysis.py](file://app/routers/analysis.py#L771-L770)

## 股票数据API
股票数据API提供标准化的股票信息访问接口。

### 获取股票基础信息
```http
GET /api/stock-data/basic-info/{symbol}
```

**响应**
```json
{
  "success": true,
  "data": {
    "code": "000001",
    "name": "平安银行",
    "industry": "银行",
    "market": "主板",
    "list_date": "1991-04-03",
    "total_mv": 2500.5,
    "pe": 8.5,
    "pb": 1.2
  },
  "message": "获取成功"
}
```

### 获取实时行情
```http
GET /api/stock-data/quotes/{symbol}
```

**响应**
```json
{
  "success": true,
  "data": {
    "code": "000001",
    "close": 12.5,
    "open": 12.3,
    "high": 12.6,
    "low": 12.2,
    "volume": 150000000,
    "amount": 1875000000,
    "pct_chg": 1.6,
    "trade_date": "2025-10-28"
  },
  "message": "获取成功"
}
```

### 获取股票列表
```http
GET /api/stock-data/list
```

**查询参数**
- `market`: 市场筛选（可选）
- `industry`: 行业筛选（可选）
- `page`: 页码（默认1）
- `page_size`: 每页大小（默认20）

**响应**
```json
{
  "success": true,
  "data": [
    {
      "code": "000001",
      "name": "平安银行",
      "industry": "银行"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "message": "获取成功"
}
```

### 搜索股票
```http
GET /api/stock-data/search
```

**查询参数**
- `keyword`: 搜索关键词（必填）
- `limit`: 返回数量限制（默认10）

**响应**
```json
{
  "success": true,
  "data": [
    {
      "code": "000001",
      "name": "平安银行",
      "industry": "银行"
    }
  ],
  "total": 1,
  "keyword": "平安",
  "source": "tushare",
  "message": "搜索完成"
}
```

**Section sources**
- [stock_data.py](file://app/routers/stock_data.py#L23-L281)

## 数据同步API
数据同步API用于手动触发股票数据的同步操作。

### 同步单个股票
```http
POST /api/stock-sync/single
```

**请求体**
```json
{
  "symbol": "000001",
  "sync_realtime": true,
  "sync_historical": true,
  "sync_financial": true,
  "sync_basic": false,
  "data_source": "tushare",
  "days": 30
}
```

**响应**
```json
{
  "success": true,
  "data": {
    "symbol": "000001",
    "realtime_sync": {
      "success": true,
      "message": "实时行情同步成功"
    },
    "historical_sync": {
      "success": true,
      "records": 30,
      "message": "同步了 30 条历史记录"
    },
    "financial_sync": {
      "success": true,
      "message": "财务数据同步成功"
    },
    "overall_success": true
  },
  "message": "股票 000001 数据同步成功"
}
```

### 批量同步股票
```http
POST /api/stock-sync/batch
```

**请求体**
```json
{
  "symbols": ["000001", "600036"],
  "sync_historical": true,
  "sync_financial": true,
  "sync_basic": false,
  "data_source": "tushare",
  "days": 30
}
```

**响应**
```json
{
  "success": true,
  "data": {
    "total": 2,
    "symbols": ["000001", "600036"],
    "historical_sync": {
      "success_count": 2,
      "error_count": 0,
      "total_records": 60,
      "message": "成功同步 2/2 只股票，共 60 条记录"
    },
    "financial_sync": {
      "success_count": 2,
      "error_count": 0,
      "total_symbols": 2,
      "message": "成功同步 2/2 只股票的财务数据"
    },
    "total_success": 2,
    "total_symbols": 2
  },
  "message": "批量同步完成: 2/2 只股票成功"
}
```

### 获取同步状态
```http
GET /api/stock-sync/status/{symbol}
```

**响应**
```json
{
  "success": true,
  "data": {
    "symbol": "000001",
    "historical_data": {
      "last_sync": "2025-10-28T15:00:00Z",
      "last_date": "2025-10-28",
      "total_records": 10000
    },
    "financial_data": {
      "last_sync": "2025-10-28T14:30:00Z",
      "last_report_period": "2025Q3",
      "total_records": 100
    }
  }
}
```

**Section sources**
- [stock_sync.py](file://app/routers/stock_sync.py#L122-L714)

## 用户管理API
用户管理API提供用户认证、信息管理和密码修改功能。

### 获取当前用户信息
```http
GET /api/auth/me
```

**响应**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "username": "user1",
    "email": "user1@example.com",
    "is_admin": false,
    "preferences": {
      "language": "zh-CN",
      "theme": "dark"
    }
  },
  "message": "获取用户信息成功"
}
```

### 更新用户信息
```http
PUT /api/auth/me
```

**请求体**
```json
{
  "email": "newemail@example.com",
  "preferences": {
    "language": "en-US",
    "theme": "light"
  }
}
```

**响应**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "username": "user1",
    "email": "newemail@example.com",
    "preferences": {
      "language": "en-US",
      "theme": "light"
    }
  },
  "message": "用户信息更新成功"
}
```

### 修改密码
```http
POST /api/auth/change-password
```

**请求体**
```json
{
  "old_password": "oldpass",
  "new_password": "newpass"
}
```

**响应**
```json
{
  "success": true,
  "data": {},
  "message": "密码修改成功"
}
```

**Section sources**
- [auth_db.py](file://app/routers/auth_db.py#L303-L396)

## WebSocket实时通知API
WebSocket API提供实时的任务进度和系统通知推送。

### 连接通知WebSocket
```http
GET /api/ws/notifications?token=<jwt_token>
```

**消息格式**
```json
{
  "type": "notification",
  "data": {
    "id": "notif_123",
    "title": "分析完成",
    "content": "000001 分析任务已完成",
    "type": "analysis",
    "link": "/stocks/000001",
    "created_at": "2025-10-28T10:05:00Z",
    "status": "unread"
  }
}
```

### 连接任务进度WebSocket
```http
GET /api/ws/tasks/{task_id}?token=<jwt_token>
```

**消息格式**
```json
{
  "type": "progress",
  "data": {
    "task_id": "task_123",
    "message": "正在分析...",
    "step": 1,
    "total_steps": 5,
    "progress": 20.0,
    "timestamp": "2025-10-28T10:01:00Z"
  }
}
```

### 获取WebSocket连接统计
```http
GET /api/ws/stats
```

**响应**
```json
{
  "total_users": 1,
  "total_connections": 1,
  "users": {
    "admin": 1
  }
}
```

**Section sources**
- [websocket_notifications.py](file://app/routers/websocket_notifications.py#L109-L268)

## REST通知API
REST通知API提供通知的查询和管理功能。

### 获取通知列表
```http
GET /api/notifications
```

**查询参数**
- `status`: 状态（unread/read/all）
- `type`: 类型（analysis/alert/system）
- `page`: 页码
- `page_size`: 每页大小

**响应**
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "notif_123",
        "title": "分析完成",
        "content": "000001 分析任务已完成",
        "type": "analysis",
        "status": "unread",
        "created_at": "2025-10-28T10:05:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  },
  "message": "ok"
}
```

### 获取未读通知数量
```http
GET /api/notifications/unread_count
```

**响应**
```json
{
  "success": true,
  "data": {
    "count": 1
  }
}
```

### 标记通知为已读
```http
POST /api/notifications/{notif_id}/read
```

**响应**
```json
{
  "success": true,
  "message": "ok"
}
```

**Section sources**
- [notifications.py](file://app/routers/notifications.py#L17-L45)

## 报告管理API
报告管理API用于查询、下载和管理分析报告。

### 获取报告列表
```http
GET /api/reports/list
```

**查询参数**
- `page`: 页码
- `page_size`: 每页数量
- `search_keyword`: 搜索关键词
- `market_filter`: 市场筛选
- `start_date`: 开始日期
- `end_date`: 结束日期
- `stock_code`: 股票代码

**响应**
```json
{
  "success": true,
  "data": {
    "reports": [
      {
        "id": "report_123",
        "analysis_id": "ana_123",
        "title": "000001 分析报告",
        "stock_code": "000001",
        "stock_name": "平安银行",
        "market_type": "A股",
        "status": "completed",
        "created_at": "2025-10-28T10:05:00+08:00",
        "analysis_date": "2025-10-28",
        "summary": "string"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  },
  "message": "报告列表获取成功"
}
```

### 下载报告
```http
GET /api/reports/{report_id}/download
```

**查询参数**
- `format`: 下载格式（markdown/json/docx/pdf）

**响应**
- 返回指定格式的报告文件流

**Section sources**
- [reports.py](file://app/routers/reports.py#L119-L575)

## 自选股管理API
自选股管理API用于管理用户的自选股列表。

### 获取自选股列表
```http
GET /api/favorites
```

**响应**
```json
{
  "success": true,
  "data": [
    {
      "stock_code": "000001",
      "stock_name": "平安银行",
      "market": "A股",
      "added_at": "2025-10-28T10:00:00Z",
      "tags": ["银行", "蓝筹"],
      "notes": "重点关注",
      "alert_price_high": 13.0,
      "alert_price_low": 11.5
    }
  ]
}
```

### 添加自选股
```http
POST /api/favorites
```

**请求体**
```json
{
  "stock_code": "000001",
  "stock_name": "平安银行",
  "market": "A股",
  "tags": ["银行"],
  "notes": "重点关注",
  "alert_price_high": 13.0,
  "alert_price_low": 11.5
}
```

**响应**
```json
{
  "success": true,
  "data": {
    "stock_code": "000001"
  },
  "message": "添加成功"
}
```

### 同步自选股实时行情
```http
POST /api/favorites/sync-realtime
```

**请求体**
```json
{
  "data_source": "tushare"
}
```

**响应**
```json
{
  "success": true,
  "data": {
    "total": 1,
    "success_count": 1,
    "failed_count": 0,
    "symbols": ["000001"],
    "data_source": "tushare",
    "message": "同步完成: 成功 1 只，失败 0 只"
  }
}
```

**Section sources**
- [favorites.py](file://app/routers/favorites.py#L55-L292)

## API版本控制
sagacity平台的API采用语义化版本控制，当前版本为1.0.0。API版本通过以下方式管理：

1. **向后兼容性**：在主要版本号不变的情况下，所有API变更都保持向后兼容。
2. **版本号**：API版本号从VERSION文件读取，并在FastAPI应用中设置。
3. **变更通知**：重大变更会通过系统通知和文档更新提前告知用户。

**Section sources**
- [main.py](file://app/main.py#L74-L82)