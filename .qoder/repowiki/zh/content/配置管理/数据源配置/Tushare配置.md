# Tushare配置

<cite>
**本文档引用的文件**   
- [config_bridge.py](file://app/core/config_bridge.py)
- [tushare.py](file://tradingagents/dataflows/providers/china/tushare.py)
- [tushare_sync_service.py](file://app/worker/tushare_sync_service.py)
- [tushare_config.py](file://tradingagents/config/tushare_config.py)
- [tushare_init.py](file://app/routers/tushare_init.py)
- [tushare_init.py](file://cli/tushare_init.py)
</cite>

## 目录
1. [Tushare API配置](#tushare-api配置)
2. [数据源优先级体系](#数据源优先级体系)
3. [Tushare在数据获取中的应用](#tushare在数据获取中的应用)
4. [配置验证与问题解决](#配置验证与问题解决)
5. [初始化与同步服务](#初始化与同步服务)

## Tushare API配置

Tushare数据源的配置主要通过API令牌（Token）、基础URL和启用状态管理来实现。系统采用多层级配置机制，确保配置的灵活性和可靠性。

### API令牌设置

Tushare的API令牌是访问其数据服务的关键凭证。系统通过以下机制管理令牌：

1. **配置优先级**：系统遵循"数据库配置 > .env文件"的优先级原则。这意味着用户在Web后台修改的配置会优先于`.env`文件中的配置。
2. **令牌来源**：系统首先尝试从数据库读取令牌，如果数据库中未配置，则降级到使用`.env`文件中的`TUSHARE_TOKEN`环境变量。
3. **令牌验证**：系统会验证令牌的有效性，包括检查令牌是否为空、长度是否符合要求（通常为40个字符的十六进制字符串）。

```python
# 从数据库读取Tushare Token
def _get_token_from_database(self) -> Optional[str]:
    try:
        from app.core.database import get_mongo_db
        db = get_mongo_db()
        config_collection = db.system_configs
        
        config_data = config_collection.find_one(
            {"is_active": True},
            sort=[("version", -1)]
        )
        
        if config_data and config_data.get('data_source_configs'):
            for ds_config in config_data['data_source_configs']:
                if ds_config.get('type') == 'tushare':
                    api_key = ds_config.get('api_key')
                    if api_key and not api_key.startswith("your_"):
                        return api_key
    except Exception as e:
        self.logger.debug(f"从数据库读取 Token 失败: {e}")
    
    return None
```

**Section sources**
- [config_bridge.py](file://app/core/config_bridge.py#L187-L193)
- [tushare.py](file://tradingagents/dataflows/providers/china/tushare.py#L40-L86)

### 基础URL配置

Tushare的基础URL默认为`http://api.tushare.pro`，该配置在系统中是固定的，不支持用户自定义修改。系统通过以下方式确保URL的正确性：

1. **硬编码配置**：在数据源配置中，Tushare的endpoint被硬编码为`http://api.tushare.pro`。
2. **配置验证**：系统在初始化时会验证URL的有效性，确保能够正常访问Tushare API。

```python
# Tushare数据源配置
tushare_config = DataSourceConfig(
    name="Tushare",
    type=DataSourceType.TUSHARE,
    api_key=settings.get("tushare_token"),
    endpoint="http://api.tushare.pro",
    enabled=True,
    priority=2,
    description="Tushare专业金融数据接口"
)
```

**Section sources**
- [unified_config.py](file://app/core/unified_config.py#L316-L320)

### 启用/禁用状态管理

Tushare数据源的启用状态可以通过两种方式管理：

1. **环境变量**：通过设置`.env`文件中的`TUSHARE_ENABLED`变量来控制。
2. **数据库配置**：通过Web后台界面修改系统配置中的数据源状态。

系统在启动时会检查Tushare的启用状态，如果未启用，则不会尝试连接Tushare API。

```python
# 检查配置是否有效
def is_valid(self) -> bool:
    if not self.enabled:
        return False
    
    if not self.token:
        return False
    
    # 检查token格式（Tushare token通常是40字符的十六进制字符串）
    if len(self.token) < 30:
        return False
    
    return True
```

**Section sources**
- [tushare_config.py](file://tradingagents/config/tushare_config.py#L48-L60)

## 数据源优先级体系

Tushare在系统中的数据源优先级体系中扮演着重要角色。系统采用多数据源并存的架构，通过优先级机制确保数据获取的可靠性和效率。

### 优先级设计原则

系统的数据源优先级设计遵循以下原则：

1. **数字越大优先级越高**：在数据源配置中，priority值越大表示优先级越高。
2. **数据库配置优先**：用户在Web后台修改的配置优先于`.env`文件中的配置。
3. **动态调整**：系统支持在运行时动态调整数据源优先级。

```python
# 按优先级排序（数字越大优先级越高）
result.sort(key=lambda x: x.priority, reverse=True)
```

### Tushare的优先级位置

在默认配置中，Tushare的优先级设置为2，高于AKShare的优先级1。这意味着在正常情况下，系统会优先使用Tushare获取数据。

```python
# Tushare (如果有配置)
if settings.get("tushare_token"):
    tushare_config = DataSourceConfig(
        name="Tushare",
        type=DataSourceType.TUSHARE,
        api_key=settings.get("tushare_token"),
        endpoint="http://api.tushare.pro",
        enabled=True,
        priority=2,
        description="Tushare专业金融数据接口"
    )
    data_sources.append(tushare_config)
```

**Section sources**
- [unified_config.py](file://app/core/unified_config.py#L318-L320)

## Tushare在数据获取中的应用

Tushare在系统中被广泛应用于每日基础数据、K线数据和新闻数据的获取。系统通过专门的同步服务和数据提供器来实现这些功能。

### 每日基础数据获取

Tushare提供每日基础财务数据接口，系统通过`daily_basic`接口获取这些数据。这些数据包括市盈率(PE)、市净率(PB)、换手率等重要指标。

```python
async def get_daily_basic(self, trade_date: str) -> Optional[pd.DataFrame]:
    """获取每日基础财务数据"""
    if not self.is_available():
        return None
    
    try:
        date_str = trade_date.replace('-', '')
        df = await asyncio.to_thread(
            self.api.daily_basic,
            trade_date=date_str,
            fields='ts_code,total_mv,circ_mv,pe,pb,turnover_rate,volume_ratio,pe_ttm,pb_mrq'
        )
        
        if df is not None and not df.empty:
            self.logger.info(f"✅ 获取每日基础数据: {trade_date} {len(df)}条记录")
            return df
        
        return None
        
    except Exception as e:
        self.logger.error(f"❌ 获取每日基础数据失败 trade_date={trade_date}: {e}")
        return None
```

**Section sources**
- [tushare.py](file://tradingagents/dataflows/providers/china/tushare.py#L597-L618)

### K线数据获取

Tushare提供高质量的K线数据，系统通过`pro_bar`接口获取前复权数据。系统支持日线、周线和月线三种周期的数据获取。

```python
async def get_historical_data(
    self,
    symbol: str,
    start_date: Union[str, date],
    end_date: Union[str, date] = None,
    period: str = "daily"
) -> Optional[pd.DataFrame]:
    """
    获取历史数据
    """
    if not self.is_available():
        return None

    try:
        ts_code = self._normalize_ts_code(symbol)

        # 格式化日期
        start_str = self._format_date(start_date)
        end_str = self._format_date(end_date) if end_date else datetime.now().strftime('%Y%m%d')

        # 周期映射
        freq_map = {
            "daily": "D",
            "weekly": "W",
            "monthly": "M"
        }
        freq = freq_map.get(period, "D")

        # 使用 ts.pro_bar() 函数获取前复权数据
        df = await asyncio.to_thread(
            ts.pro_bar,
            ts_code=ts_code,
            api=self.api,
            start_date=start_str,
            end_date=end_str,
            freq=freq,
            adj='qfq'  # 前复权（与同花顺一致）
        )

        if df is None or df.empty:
            return None

        # 数据标准化
        df = self._standardize_historical_data(df)

        self.logger.info(f"✅ 获取{period}历史数据: {symbol} {len(df)}条记录 (前复权 qfq)")
        return df
        
    except Exception as e:
        return None
```

**Section sources**
- [tushare.py](file://tradingagents/dataflows/providers/china/tushare.py#L511-L579)

### 新闻数据获取

Tushare提供丰富的新闻数据源，系统支持从多个新闻源获取数据，包括新浪财经、东方财富、同花顺等。系统采用优先级排序的新闻源列表，确保获取到最相关的信息。

```python
async def get_stock_news(self, symbol: str = None, limit: int = 10,
                       hours_back: int = 24, src: str = None) -> Optional[List[Dict[str, Any]]]:
    """
    获取股票新闻（需要Tushare新闻权限）
    """
    if not self.is_available():
        return None

    try:
        from datetime import datetime, timedelta

        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)

        start_date = start_time.strftime('%Y-%m-%d %H:%M:%S')
        end_date = end_time.strftime('%Y-%m-%d %H:%M:%S')

        self.logger.debug(f"📰 获取Tushare新闻: symbol={symbol}, 时间范围={start_date} 到 {end_date}")

        # 支持的新闻源列表（按优先级排序）
        news_sources = [
            'sina',        # 新浪财经
            'eastmoney',   # 东方财富
            '10jqka',      # 同花顺
            'wallstreetcn', # 华尔街见闻
            'cls',         # 财联社
            'yicai',       # 第一财经
            'jinrongjie',  # 金融界
            'yuncaijing',  # 云财经
            'fenghuang'    # 凤凰新闻
        ]

        # 如果指定了数据源，优先使用
        if src and src in news_sources:
            sources_to_try = [src]
        else:
            sources_to_try = news_sources[:3]  # 默认尝试前3个源

        all_news = []

        for source in sources_to_try:
            try:
                self.logger.debug(f"📰 尝试从 {source} 获取新闻...")

                # 获取新闻数据
                news_df = await asyncio.to_thread(
                    self.api.news,
                    src=source,
                    start_date=start_date,
                    end_date=end_date
                )
```

**Section sources**
- [tushare.py](file://tradingagents/dataflows/providers/china/tushare.py#L768-L828)

## 配置验证与问题解决

为了确保Tushare配置的正确性和系统的稳定性，系统提供了一系列配置验证和问题解决机制。

### 配置验证方法

系统通过`TushareConfig`类提供详细的配置验证功能，包括：

1. **令牌验证**：检查令牌是否设置、长度是否符合要求。
2. **启用状态验证**：检查Tushare是否已启用。
3. **环境变量调试**：输出环境变量的详细信息，便于诊断问题。

```python
def get_validation_result(self) -> Dict[str, Any]:
    """获取详细的验证结果"""
    result = {
        'valid': False,
        'enabled': self.enabled,
        'token_set': bool(self.token),
        'token_length': len(self.token),
        'issues': [],
        'suggestions': []
    }
    
    # 检查启用状态
    if not self.enabled:
        result['issues'].append("TUSHARE_ENABLED未启用")
        result['suggestions'].append("在.env文件中设置 TUSHARE_ENABLED=true")
    
    # 检查token
    if not self.token:
        result['issues'].append("TUSHARE_TOKEN未设置")
        result['suggestions'].append("在.env文件中设置 TUSHARE_TOKEN=your_token_here")
    elif len(self.token) < 30:
        result['issues'].append("TUSHARE_TOKEN格式可能不正确")
        result['suggestions'].append("检查token是否完整（通常为40字符）")
    
    # 如果没有问题，标记为有效
    if not result['issues']:
        result['valid'] = True
    
    return result
```

**Section sources**
- [tushare_config.py](file://tradingagents/config/tushare_config.py#L62-L90)

### 常见问题解决方案

#### 令牌失效问题

当Tushare令牌失效时，系统会记录相应的错误日志。解决方案包括：

1. **检查令牌有效性**：确保令牌未过期且格式正确。
2. **重新配置令牌**：在Web后台或`.env`文件中更新令牌。
3. **重启服务**：使新的配置生效。

```python
# 诊断Tushare配置问题
def diagnose_tushare_issues():
    """诊断Tushare配置问题"""
    print("🔍 Tushare配置诊断")
    print("=" * 60)
    
    compatibility = check_tushare_compatibility()
    
    # 显示配置状态
    print(f"\n📊 配置状态:")
    validation = compatibility['validation_result']
    print(f"   配置有效: {'✅' if validation['valid'] else '❌'}")
    print(f"   Tushare启用: {'✅' if validation['enabled'] else '❌'}")
    print(f"   Token设置: {'✅' if validation['token_set'] else '❌'}")
    
    # 显示问题
    if validation['issues']:
        print(f"\n⚠️ 发现问题:")
        for issue in validation['issues']:
            print(f"   - {issue}")
    
    # 显示建议
    if validation['suggestions']:
        print(f"\n💡 修复建议:")
        for suggestion in validation['suggestions']:
            print(f"   - {suggestion}")
```

**Section sources**
- [tushare_config.py](file://tradingagents/config/tushare_config.py#L178-L227)

#### 配额限制问题

Tushare API有严格的调用频率限制，系统通过以下机制处理配额限制：

1. **限流错误检测**：系统能够识别Tushare返回的限流错误信息。
2. **速率限制器**：使用`TushareRateLimiter`控制API调用频率。
3. **降级策略**：当Tushare达到调用限制时，系统会自动降级到其他数据源。

```python
def _is_rate_limit_error(self, error_msg: str) -> bool:
    """检测是否为 API 限流错误"""
    rate_limit_keywords = [
        "每分钟最多访问",
        "每分钟最多",
        "rate limit",
        "too many requests",
        "访问频率",
        "请求过于频繁"
    ]
    error_msg_lower = error_msg.lower()
    return any(keyword in error_msg_lower for keyword in rate_limit_keywords)
```

**Section sources**
- [RATE_LIMIT_HANDLING.md](file://docs/integration/rate-limit/RATE_LIMIT_HANDLING.md#L13-L25)

## 初始化与同步服务

系统提供完整的Tushare数据初始化和同步服务，确保数据的完整性和及时性。

### 初始化服务

Tushare初始化服务负责首次部署时的完整数据初始化，包括：

1. **检查数据库状态**：确认数据库是否为空或需要初始化。
2. **同步基础信息**：获取股票基础信息。
3. **同步历史数据**：获取指定时间范围的历史数据。
4. **同步财务数据**：获取财务报表数据。
5. **同步最新行情数据**：获取最新的市场行情。

```python
class TushareInitService:
    """
    Tushare数据初始化服务
    
    负责首次部署时的完整数据初始化：
    1. 检查数据库状态
    2. 初始化股票基础信息
    3. 同步历史数据（可配置时间范围）
    4. 同步财务数据
    5. 同步最新行情数据
    6. 验证数据完整性
    """
    
    def __init__(self):
        self.db = None
        self.sync_service = None
        self.stats = None
    
    async def initialize(self):
        """初始化服务"""
        self.db = get_mongo_db()
        self.sync_service = await get_tushare_sync_service()
        logger.info("✅ Tushare初始化服务准备完成")
    
    async def run_full_initialization(
        self,
        historical_days: int = 365,
        skip_if_exists: bool = True,
        batch_size: int = 100,
        enable_multi_period: bool = False,
        sync_items: List[str] = None
    ) -> Dict[str, Any]:
        """
        运行完整的数据初始化
        """
```

**Section sources**
- [tushare_init_service.py](file://app/worker/tushare_init_service.py#L41-L72)

### 同步服务

Tushare同步服务负责将Tushare数据同步到MongoDB标准化集合，支持：

1. **基础信息同步**：定期同步股票基础信息。
2. **实时行情同步**：同步最新的市场行情数据。
3. **历史数据同步**：同步历史K线数据。
4. **新闻数据同步**：同步最新的新闻数据。

```python
class TushareSyncService:
    """
    Tushare数据同步服务
    负责将Tushare数据同步到MongoDB标准化集合
    """
    
    def __init__(self):
        self.provider = TushareProvider()
        self.stock_service = get_stock_data_service()
        self.historical_service = None  # 延迟初始化
        self.news_service = None  # 延迟初始化
        self.db = get_mongo_db()
        self.settings = settings

        # 同步配置
        self.batch_size = 100  # 批量处理大小
        self.rate_limit_delay = 0.1  # API调用间隔(秒) - 已弃用，使用rate_limiter
        self.max_retries = 3  # 最大重试次数

        # 速率限制器（从环境变量读取配置）
        tushare_tier = getattr(settings, "TUSHARE_TIER", "standard")  # free/basic/standard/premium/vip
        safety_margin = float(getattr(settings, "TUSHARE_RATE_LIMIT_SAFETY_MARGIN", "0.8"))
        self.rate_limiter = get_tushare_rate_limiter(tier=tushare_tier, safety_margin=safety_margin)
```

**Section sources**
- [tushare_sync_service.py](file://app/worker/tushare_sync_service.py#L35-L58)