"""
股票数据服务层 - 统一数据访问接口
基于现有MongoDB集合，提供标准化的数据访问服务
"""
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_mongo_db
from app.models.stock_models import (
    StockBasicInfoExtended, 
    MarketQuotesExtended,
    MarketInfo,
    MarketType,
    ExchangeType,
    CurrencyType
)

logger = logging.getLogger(__name__)


class StockDataService:
    """
    股票数据服务 - 统一数据访问层
    基于现有集合扩展，保持向后兼容
    """
    
    def __init__(self):
        self.basic_info_collection = "stock_basic_info"
        self.market_quotes_collection = "market_quotes"
    
    async def get_stock_basic_info(
        self,
        symbol: str,
        source: Optional[str] = None
    ) -> Optional[StockBasicInfoExtended]:
        """
        获取股票基础信息
        Args:
            symbol: 6位股票代码
            source: 数据源 (tushare/akshare/baostock/multi_source)，默认优先级：tushare > multi_source > akshare > baostock
        Returns:
            StockBasicInfoExtended: 扩展的股票基础信息
        """
        try:
            db = get_mongo_db()
            symbol6 = str(symbol).zfill(6)

            # 🔥 构建查询条件
            query = {"$or": [{"symbol": symbol6}, {"code": symbol6}]}

            if source:
                # 指定数据源
                query["source"] = source
                doc = await db[self.basic_info_collection].find_one(query, {"_id": 0})
            else:
                # 🔥 未指定数据源，按优先级查询
                source_priority = ["tushare", "multi_source", "akshare", "baostock"]
                doc = None

                for src in source_priority:
                    query_with_source = query.copy()
                    query_with_source["source"] = src
                    doc = await db[self.basic_info_collection].find_one(query_with_source, {"_id": 0})
                    if doc:
                        logger.debug(f"✅ 使用数据源: {src}")
                        break

                # 如果所有数据源都没有，尝试不带 source 条件查询（兼容旧数据）
                if not doc:
                    doc = await db[self.basic_info_collection].find_one(
                        {"$or": [{"symbol": symbol6}, {"code": symbol6}]},
                        {"_id": 0}
                    )
                    if doc:
                        logger.warning(f"⚠️ 使用旧数据（无 source 字段）: {symbol6}")

            if not doc:
                return None

            # 数据标准化处理
            standardized_doc = self._standardize_basic_info(doc)

            return StockBasicInfoExtended(**standardized_doc)

        except Exception as e:
            logger.error(f"获取股票基础信息失败 symbol={symbol}, source={source}: {e}")
            return None
    
    async def get_market_quotes(self, symbol: str) -> Optional[MarketQuotesExtended]:
        """
        获取实时行情数据
        Args:
            symbol: 6位股票代码
        Returns:
            MarketQuotesExtended: 扩展的实时行情数据
        """
        try:
            db = get_mongo_db()
            symbol6 = str(symbol).zfill(6)

            # 从现有集合查询 (优先使用symbol字段，兼容code字段)
            doc = await db[self.market_quotes_collection].find_one(
                {"$or": [{"symbol": symbol6}, {"code": symbol6}]},
                {"_id": 0}
            )

            if not doc:
                return None

            # 数据标准化处理
            standardized_doc = self._standardize_market_quotes(doc)

            return MarketQuotesExtended(**standardized_doc)

        except Exception as e:
            logger.error(f"获取实时行情失败 symbol={symbol}: {e}")
            return None
    
    async def get_stock_list(
        self,
        market: Optional[str] = None,
        industry: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        source: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> Tuple[List[StockBasicInfoExtended], int]:  # 返回股票列表和总数
        """
        获取股票列表
        Args:
            market: 市场筛选
            industry: 行业筛选
            search: 搜索关键词（代码或名称）
            page: 页码
            page_size: 每页大小
            source: 数据源（可选），默认使用优先级最高的数据源
            sort_by: 排序字段（可选），支持 symbol, name, market, industry, total_mv, pe, pb, close, pct_chg 等
            sort_order: 排序顺序（可选），'asc' 为升序，'desc' 为降序，默认为升序
        Returns:
            List[StockBasicInfoExtended]: 股票列表
        """
        try:
            db = get_mongo_db()

            # 🔥 获取数据源优先级配置
            if not source:
                from app.core.unified_config import UnifiedConfigManager
                config = UnifiedConfigManager()
                data_source_configs = await config.get_data_source_configs_async()

                # 提取启用的数据源，按优先级排序
                enabled_sources = [
                    ds.type.lower() for ds in data_source_configs
                    if ds.enabled and ds.type.lower() in ['tushare', 'akshare', 'baostock']
                ]

                if not enabled_sources:
                    enabled_sources = ['tushare', 'akshare', 'baostock']

                source = enabled_sources[0] if enabled_sources else 'tushare'

            # 构建查询条件
            query = {"source": source}  # 🔥 添加数据源筛选
            if market:
                query["market"] = market
            if industry:
                query["industry"] = industry
            
            # 🔥 添加搜索条件
            if search:
                search_conditions = []
                # 如果是6位数字，按代码精确匹配
                if search.isdigit() and len(search) == 6:
                    search_conditions.append({"symbol": search})
                else:
                    # 按名称模糊匹配
                    search_conditions.append({"name": {"$regex": search, "$options": "i"}})
                    # 如果包含数字，也尝试代码匹配
                    if any(c.isdigit() for c in search):
                        search_conditions.append({"symbol": {"$regex": search}})
                
                # 将搜索条件添加到查询中
                if search_conditions:
                    if len(query) > 1:  # 如果已经有其他条件
                        query = {"$and": [query, {"$or": search_conditions}]}
                    else:
                        query["$or"] = search_conditions

            # 默认排序：按symbol升序
            sort_field = 'symbol'
            sort_direction = 1
            
            # 验证排序字段是否合法，防止注入攻击
            # 基础信息字段
            basic_info_fields = {
                'symbol': 'symbol',
                'name': 'name',
                'market': 'market',
                'industry': 'industry',
                'total_mv': 'total_mv',
                'pe': 'pe',
                'pb': 'pb',
            }
            
            # 实时行情字段
            market_quote_fields = {
                'close': 'close',
                'pct_chg': 'pct_chg',
            }
            
            # 检查排序字段
            if sort_by:
                if sort_by in basic_info_fields:
                    sort_field = basic_info_fields[sort_by]
                    sort_direction = -1 if sort_order == 'desc' else 1
                elif sort_by in market_quote_fields:
                    # 行情字段将在聚合管道中处理
                    sort_field = sort_by
                    sort_direction = -1 if sort_order == 'desc' else 1
                else:
                    # 默认按symbol排序
                    sort_field = 'symbol'
                    sort_direction = -1 if sort_order == 'desc' else 1
            else:
                # 默认排序
                sort_field = 'symbol'
                sort_direction = 1

            skip = (page - 1) * page_size
            
            if sort_by in market_quote_fields:
                # 使用聚合管道来处理跨集合的排序
                pipeline = [
                    # 匹配基础信息
                    {"$match": query},
                    # 左连接行情数据
                    {
                        "$lookup": {
                            "from": self.market_quotes_collection,
                            "let": {"symbol": "$symbol", "code": "$code"},
                            "pipeline": [
                                {
                                    "$match": {
                                        "$expr": {
                                            "$or": [
                                                {"$eq": ["$symbol", "$$symbol"]},
                                                {"$eq": ["$code", "$$symbol"]},
                                                {"$eq": ["$symbol", "$$code"]},
                                                {"$eq": ["$code", "$$code"]}
                                            ]
                                        }
                                    }
                                },
                                # 排除行情集合中的_id字段
                                {
                                    "$project": {
                                        "_id": 0
                                    }
                                }
                            ],
                            "as": "quote_info"
                        }
                    },
                    # 展开行情数据并安全地提取第一个元素
                    {
                        "$addFields": {
                            "quote": {
                                "$cond": {
                                    "if": {"$gt": [{"$size": "$quote_info"}, 0]},
                                    "then": {"$arrayElemAt": ["$quote_info", 0]},
                                    "else": None
                                }
                            }
                        }
                    },
                    # 安全地添加行情字段到基础信息
                    {
                        "$addFields": {
                            "close": {"$ifNull": ["$quote.close", None]},
                            "pct_chg": {"$ifNull": ["$quote.pct_chg", None]}
                        }
                    },
                    # 移除临时字段
                    {
                        "$unset": ["quote_info", "quote"]
                    },
                    # 排序 - 使用动态字段名
                    {
                        "$sort": {sort_field: sort_direction}
                    },
                    # 跳过记录
                    {
                        "$skip": skip
                    },
                    # 限制返回数量
                    {
                        "$limit": page_size
                    },
                    # 明确指定需要的字段，排除所有_id字段
                    {
                        "$project": {
                            "_id": 0
                        }
                    }
                ]
                
                # 执行聚合查询
                cursor = db[self.basic_info_collection].aggregate(pipeline)
                docs = await cursor.to_list(length=page_size)
                
                # 数据标准化处理
                result = []
                for doc in docs:
                    standardized_doc = self._standardize_basic_info(doc)
                    result.append(StockBasicInfoExtended(**standardized_doc))
            else:
                # 使用普通查询（基础信息字段排序）
                cursor = db[self.basic_info_collection].find(
                    query,
                    {"_id": 0}
                ).sort(sort_field, sort_direction).skip(skip).limit(page_size)

                docs = await cursor.to_list(length=page_size)

                # 数据标准化处理
                result = []
                for doc in docs:
                    standardized_doc = self._standardize_basic_info(doc)
                    
                    # 获取对应的行情数据
                    symbol = standardized_doc.get('symbol')
                    if symbol:
                        market_quote = await db[self.market_quotes_collection].find_one(
                            {"$or": [{"symbol": symbol}, {"code": symbol}]},
                            {"_id": 0}
                        )
                        if market_quote:
                            # 将行情数据添加到基础信息中
                            standardized_doc['close'] = market_quote.get('close')
                            standardized_doc['pct_chg'] = market_quote.get('pct_chg')
                    
                    result.append(StockBasicInfoExtended(**standardized_doc))

            # 计算总数
            total = await db[self.basic_info_collection].count_documents(query)
            
            return result, total
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return [], 0
    
    async def update_stock_basic_info(
        self,
        symbol: str,
        update_data: Dict[str, Any],
        source: str = "tushare"
    ) -> bool:
        """
        更新股票基础信息
        Args:
            symbol: 6位股票代码
            update_data: 更新数据
            source: 数据源 (tushare/akshare/baostock)，默认 tushare
        Returns:
            bool: 更新是否成功
        """
        try:
            db = get_mongo_db()
            symbol6 = str(symbol).zfill(6)

            # 添加更新时间
            update_data["updated_at"] = datetime.utcnow()

            # 确保symbol字段存在
            if "symbol" not in update_data:
                update_data["symbol"] = symbol6

            # 🔥 确保 code 字段存在
            if "code" not in update_data:
                update_data["code"] = symbol6

            # 🔥 确保 source 字段存在
            if "source" not in update_data:
                update_data["source"] = source

            # 🔥 执行更新 (使用 code + source 联合查询)
            result = await db[self.basic_info_collection].update_one(
                {"code": symbol6, "source": source},
                {"$set": update_data},
                upsert=True
            )

            return result.modified_count > 0 or result.upserted_id is not None

        except Exception as e:
            logger.error(f"更新股票基础信息失败 symbol={symbol}, source={source}: {e}")
            return False
    
    async def update_market_quotes(
        self,
        symbol: str,
        quote_data: Dict[str, Any]
    ) -> bool:
        """
        更新实时行情数据
        Args:
            symbol: 6位股票代码
            quote_data: 行情数据
        Returns:
            bool: 更新是否成功
        """
        try:
            db = get_mongo_db()
            symbol6 = str(symbol).zfill(6)

            # 添加更新时间
            quote_data["updated_at"] = datetime.utcnow()

            # 🔥 确保 symbol 和 code 字段都存在（兼容旧索引）
            if "symbol" not in quote_data:
                quote_data["symbol"] = symbol6
            if "code" not in quote_data:
                quote_data["code"] = symbol6  # code 和 symbol 使用相同的值

            # 执行更新 (使用symbol字段作为查询条件)
            result = await db[self.market_quotes_collection].update_one(
                {"symbol": symbol6},
                {"$set": quote_data},
                upsert=True
            )

            return result.modified_count > 0 or result.upserted_id is not None

        except Exception as e:
            logger.error(f"更新实时行情失败 symbol={symbol}: {e}")
            return False
    
    def _standardize_basic_info(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化股票基础信息数据
        将现有字段映射到标准化字段
        """
        # 保持现有字段不变
        result = doc.copy()

        # 获取股票代码 (优先使用symbol，兼容code)
        symbol = doc.get("symbol") or doc.get("code", "")
        result["symbol"] = symbol

        # 兼容旧字段
        if "code" in doc and "symbol" not in doc:
            result["code"] = doc["code"]
        
        # 生成完整代码 (优先使用已有的full_symbol)
        if "full_symbol" not in result or not result["full_symbol"]:
            if symbol and len(symbol) == 6:
                # 根据代码判断交易所
                if symbol.startswith(('60', '68', '90')):
                    result["full_symbol"] = f"{symbol}.SS"
                    exchange = "SSE"
                    exchange_name = "上海证券交易所"
                elif symbol.startswith(('00', '30', '20')):
                    result["full_symbol"] = f"{symbol}.SZ"
                    exchange = "SZSE"
                    exchange_name = "深圳证券交易所"
                else:
                    result["full_symbol"] = f"{symbol}.SZ"  # 默认深交所
                    exchange = "SZSE"
                    exchange_name = "深圳证券交易所"
            else:
                exchange = "SZSE"
                exchange_name = "深圳证券交易所"
        else:
            # 从full_symbol解析交易所
            full_symbol = result["full_symbol"]
            if ".SS" in full_symbol or ".SH" in full_symbol:
                exchange = "SSE"
                exchange_name = "上海证券交易所"
            else:
                exchange = "SZSE"
                exchange_name = "深圳证券交易所"
            
            # 添加市场信息
            result["market_info"] = {
                "market": "CN",
                "exchange": exchange,
                "exchange_name": exchange_name,
                "currency": "CNY",
                "timezone": "Asia/Shanghai",
                "trading_hours": {
                    "open": "09:30",
                    "close": "15:00",
                    "lunch_break": ["11:30", "13:00"]
                }
            }
        
        # 字段映射和标准化
        result["board"] = doc.get("sse")  # 板块标准化
        result["sector"] = doc.get("sec")  # 所属板块标准化
        result["status"] = "L"  # 默认上市状态
        result["data_version"] = 1

        # 处理日期字段格式转换
        list_date = doc.get("list_date")
        if list_date and isinstance(list_date, int):
            # 将整数日期转换为字符串格式 (YYYYMMDD -> YYYY-MM-DD)
            date_str = str(list_date)
            if len(date_str) == 8:
                result["list_date"] = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            else:
                result["list_date"] = str(list_date)
        elif list_date:
            result["list_date"] = str(list_date)

        return result
    
    def _standardize_market_quotes(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化实时行情数据
        将现有字段映射到标准化字段
        """
        # 保持现有字段不变
        result = doc.copy()
        
        # 获取股票代码 (优先使用symbol，兼容code)
        symbol = doc.get("symbol") or doc.get("code", "")
        result["symbol"] = symbol

        # 兼容旧字段
        if "code" in doc and "symbol" not in doc:
            result["code"] = doc["code"]

        # 生成完整代码和市场标识 (优先使用已有的full_symbol)
        if "full_symbol" not in result or not result["full_symbol"]:
            if symbol and len(symbol) == 6:
                if symbol.startswith(('60', '68', '90')):
                    result["full_symbol"] = f"{symbol}.SS"
                else:
                    result["full_symbol"] = f"{symbol}.SZ"

        if "market" not in result:
            result["market"] = "CN"
        
        # 字段映射
        result["current_price"] = doc.get("close")  # 当前价格
        if doc.get("close") and doc.get("pre_close"):
            try:
                result["change"] = float(doc["close"]) - float(doc["pre_close"])
            except (ValueError, TypeError):
                result["change"] = None
        
        result["data_source"] = "market_quotes"
        result["data_version"] = 1
        
        return result


# 全局服务实例
_stock_data_service = None

def get_stock_data_service() -> StockDataService:
    """获取股票数据服务实例"""
    global _stock_data_service
    if _stock_data_service is None:
        _stock_data_service = StockDataService()
    return _stock_data_service
