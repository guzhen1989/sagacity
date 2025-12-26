# 股票数据API

<cite>
**本文档引用的文件**   
- [stocks.py](file://app/routers/stocks.py)
- [multi_market_stocks.py](file://app/routers/multi_market_stocks.py)
- [stock_data_service.py](file://app/services/stock_data_service.py)
- [foreign_stock_service.py](file://app/services/foreign_stock_service.py)
- [manager.py](file://app/services/data_sources/manager.py)
- [unified_config.py](file://app/core/unified_config.py)
- [stock_models.py](file://app/models/stock_models.py)
- [cache.py](file://app/routers/cache.py)
</cite>

## 目录
1. [引言](#引言)
2. [核心端点](#核心端点)
3. [多市场股票代码识别与标准化](#多市场股票代码识别与标准化)
4. [数据源优先级与缓存策略](#数据源优先级与缓存策略)
5. [前端调用示例](#前端调用示例)
6. [实时行情更新频率与数据延迟](#实时行情更新频率与数据延迟)
7. [错误处理机制](#错误处理机制)

## 引言
本API提供了一个统一的接口，用于获取A股、港股、美股等多市场股票的基础信息、实时行情和K线数据。API设计遵循RESTful原则，所有端点均需通过Bearer Token进行身份验证。响应数据采用统一的包裹格式，包含`success`、`data`、`message`和`timestamp`字段，确保了接口的稳定性和易用性。

**Section sources**
- [stocks.py](file://app/routers/stocks.py#L1-L10)

## 核心端点

### GET /api/stocks/{symbol}/quote
此端点用于获取指定股票的实时行情数据。它支持A股、港股和美股，并能自动识别市场类型。

**请求参数**:
- `symbol`: 股票代码。对于A股，应为6位数字；对于港股，可以是4-5位数字或带有`.HK`后缀的代码；对于美股，应为纯字母代码。
- `force_refresh`: 布尔值，可选。如果设置为`true`，将强制刷新数据，跳过缓存。

**响应数据结构 (data内)**:
- `code`: 股票代码（6位数字，A股）或标准化代码（如00700.HK）。
- `name`: 股票名称。
- `market`: 市场类型（CN: A股, HK: 港股, US: 美股）。
- `price`: 当前价格（即收盘价close）。
- `change_percent`: 涨跌幅（%）。
- `amount`: 成交额。
- `volume`: 成交量。
- `open`: 开盘价。
- `high`: 最高价。
- `low`: 最低价。
- `prev_close`: 昨收价（估算或从数据源获取）。
- `turnover_rate`: 换手率。
- `amplitude`: 振幅（替代量比，计算方式为(最高价-最低价)/昨收价*100%）。
- `trade_date`: 交易日期。
- `updated_at`: 数据更新时间。

**Section sources**
- [stocks.py](file://app/routers/stocks.py#L66-L212)

### GET /api/stocks/{symbol}/fundamentals
此端点用于获取股票的基础面快照，包括估值指标、财务指标和市值信息。

**请求参数**:
- `symbol`: 股票代码。
- `source`: 字符串，可选。指定数据源（tushare, akshare, baostock, multi_source）。如果不指定，则按优先级自动选择。
- `force_refresh`: 布尔值，可选。如果设置为`true`，将强制刷新数据，跳过缓存。

**响应数据结构 (data内)**:
- `code`: 股票代码。
- `name`: 股票名称。
- `industry`: 所属行业。
- `market`: 交易所（如主板、创业板）。
- `sector`: 板块信息。
- `pe`, `pb`, `pe_ttm`, `pb_mrq`: 市盈率、市净率及其滚动/最新值。
- `ps`, `ps_ttm`: 市销率（动态计算）。
- `roe`: 净资产收益率。
- `debt_ratio`: 负债率。
- `total_mv`: 总市值（优先使用实时计算，降级到静态数据）。
- `circ_mv`: 流通市值。
- `turnover_rate`: 换手率。
- `volume_ratio`: 量比。
- `updated_at`: 数据更新时间。
- `pe_source`: PE数据来源标识。
- `pe_is_realtime`: PE是否为实时计算。
- `pe_updated_at`: PE数据更新时间。
- `mv_is_realtime`: 市值是否为实时计算。

**Section sources**
- [stocks.py](file://app/routers/stocks.py#L215-L418)

### GET /api/stocks/kline
此端点用于获取股票的历史K线数据。

**请求参数**:
- `symbol`: 股票代码。
- `period`: K线周期，可选值为`day`, `week`, `month`, `5m`, `15m`, `30m`, `60m`。
- `limit`: 返回的数据条数，默认为120。
- `adj`: 复权方式，可选值为`none`, `qfq`（前复权）, `hfq`（后复权）。
- `force_refresh`: 布尔值，可选。如果设置为`true`，将强制刷新数据，跳过缓存。

**响应数据结构 (data内)**:
- `code`: 股票代码。
- `period`: K线周期。
- `limit`: 请求的数据条数。
- `adj`: 复权方式。
- `source`: 数据来源。
- `items`: K线数据列表，每个元素包含：
  - `time`: 交易日期（格式为YYYY-MM-DD）。
  - `open`: 开盘价。
  - `high`: 最高价。
  - `low`: 最低价。
  - `close`: 收盘价。
  - `volume`: 成交量。
  - `amount`: 成交额。

**Section sources**
- [stocks.py](file://app/routers/stocks.py#L421-L621)

## 多市场股票代码识别与标准化
系统通过`_detect_market_and_code`函数自动识别和标准化不同市场的股票代码。

**识别逻辑**:
1. **港股 (HK)**:
   - 如果代码以`.HK`结尾，则识别为港股，并移除后缀。
   - 如果代码是4-5位数字，则识别为港股，并补齐到5位。
2. **美股 (US)**:
   - 如果代码是纯字母，则识别为美股。
3. **A股 (CN)**:
   - 如果代码是6位数字，则识别为A股。
   - 默认情况下，任何其他格式的代码都将被当作A股处理。

**标准化逻辑**:
- A股代码会被标准化为6位数字。
- 港股代码会被标准化为5位数字。
- 美股代码保持原样。

此逻辑确保了系统能够无缝处理来自不同市场的股票代码，为用户提供一致的体验。

**Section sources**
- [stocks.py](file://app/routers/stocks.py#L31-L63)

## 数据源优先级与缓存策略

### 数据源优先级
系统支持多个数据源，包括Tushare、AkShare和BaoStock。数据源的优先级可以通过数据库配置进行管理。

**优先级处理逻辑**:
1. **A股**:
   - 在获取基础信息时，系统会按优先级顺序（tushare > multi_source > akshare > baostock）查询`stock_basic_info`集合。
   - 如果所有指定数据源都未找到数据，系统会尝试不带`source`条件的查询，以兼容旧数据。
2. **港股/美股**:
   - 系统从`datasource_groupings`集合中读取配置，按`priority`字段降序排列，确定数据源的调用顺序。
   - 例如，港股的默认优先级为`['yfinance', 'akshare']`，美股的默认优先级为`['yfinance', 'alpha_vantage', 'finnhub']`。

**Section sources**
- [stocks.py](file://app/routers/stocks.py#L124-L143)
- [foreign_stock_service.py](file://app/services/foreign_stock_service.py#L239-L274)

### 缓存策略
系统采用多级缓存策略，以提高性能和减少对外部API的依赖。

**缓存层级**:
1. **MongoDB缓存**:
   - 对于K线数据，系统首先尝试从`stock_daily_quotes`集合中获取。
   - 集合中的数据按`symbol`、`period`和`trade_date`索引，确保查询效率。
2. **外部API降级**:
   - 如果MongoDB中没有数据，系统会降级到外部API，按数据源优先级顺序调用。
   - 为了防止超时，系统为外部API调用设置了10秒的超时保护。
3. **内存/文件缓存**:
   - 对于港股和美股，系统使用统一的缓存系统（`get_cache()`），支持MongoDB、Redis或文件系统作为后端。
   - 缓存时间（TTL）根据数据类型而定，例如港股实时行情为600秒，基础信息为86400秒。

**Section sources**
- [stocks.py](file://app/routers/stocks.py#L500-L529)
- [foreign_stock_service.py](file://app/services/foreign_stock_service.py#L131-L144)

## 前端调用示例
以下是一个使用TypeScript调用`stocks.ts`服务获取个股详情和历史K线数据的示例。

```typescript
// frontend/src/api/stocks.ts
export const stocksApi = {
  async getQuote(symbol: string) {
    return ApiClient.get<QuoteResponse>(`/api/stocks/${symbol}/quote`)
  },
  
  async getFundamentals(symbol: string) {
    return ApiClient.get<FundamentalsResponse>(`/api/stocks/${symbol}/fundamentals`)
  },
  
  async getKline(symbol: string, period: string = 'day', limit: number = 120) {
    return ApiClient.get<KlineResponse>(`/api/stocks/kline`, {
      params: { symbol, period, limit }
    })
  }
}

// 使用示例
async function fetchStockData() {
  const symbol = '600036'
  
  // 获取实时行情
  const quoteRes = await stocksApi.getQuote(symbol)
  console.log('实时行情:', quoteRes.data)
  
  // 获取基础面信息
  const fundRes = await stocksApi.getFundamentals(symbol)
  console.log('基础面:', fundRes.data)
  
  // 获取日K线数据
  const klineRes = await stocksApi.getKline(symbol, 'day', 120)
  console.log('K线数据:', klineRes.data.items)
}
```

**Section sources**
- [stocks.py](file://app/routers/stocks.py#L66-L621)
- [frontend/src/api/stocks.ts](file://frontend/src/api/stocks.ts)

## 实时行情更新频率与数据延迟
系统的实时行情更新频率和数据延迟特性如下：

**更新频率**:
- **A股**:
  - 实时行情数据通过`QuotesIngestionService`服务定期从数据源获取。
  - 更新频率为每6分钟一次，确保在交易时间内（09:30-15:00）以及收盘后缓冲期（15:00-15:30）内持续更新。
- **港股/美股**:
  - 实时行情数据在每次API请求时获取，并根据`force_refresh`参数决定是否跳过缓存。
  - 缓存时间为10分钟，以平衡数据新鲜度和API调用成本。

**数据延迟**:
- **A股**:
  - 由于更新频率为6分钟，数据延迟通常在6分钟以内。
  - 在收盘后缓冲期内，系统会额外获取5次数据，大大降低了错过收盘价的风险。
- **港股/美股**:
  - 数据延迟取决于外部API的响应速度和缓存策略。
  - 在强制刷新模式下，延迟主要由网络请求时间决定。

**Section sources**
- [stocks.py](file://app/routers/stocks.py#L550-L574)
- [utils/trading_time.py](file://app/utils/trading_time.py#L14-L50)

## 错误处理机制
API实现了全面的错误处理机制，以确保在各种异常情况下都能返回有意义的响应。

**主要错误处理场景**:
1. **股票未找到**:
   - 当无法找到指定股票的任何信息时，返回HTTP 404状态码，并附带详细信息。
   - 例如，在`get_quote`端点中，如果`market_quotes`和`stock_basic_info`集合中均无数据，则抛出404异常。
2. **数据源调用失败**:
   - 当调用外部API失败时，系统会捕获异常，记录错误日志，并返回HTTP 500或504状态码。
   - 例如，在`get_kline`端点中，如果外部API调用超时（10秒），则返回504网关超时错误。
3. **参数验证失败**:
   - 对于无效的请求参数（如不支持的`period`），返回HTTP 400状态码。
4. **并发请求去重**:
   - 对于港股和美股，系统使用`asyncio.Lock`为每个`(market, code, data_type)`组合创建独立的锁，防止并发请求重复调用API。
   - 这不仅提高了性能，还避免了因频繁调用而导致的API配额耗尽。

**Section sources**
- [stocks.py](file://app/routers/stocks.py#L103-L108)
- [stocks.py](file://app/routers/stocks.py#L543-L548)
- [foreign_stock_service.py](file://app/services/foreign_stock_service.py#L51-L55)