<template>
  <div class="stock-list">
    <!-- 页面标题区 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><List /></el-icon>
        股票列表
      </h1>
      <p class="page-description">
        浏览所有已录入的股票信息
      </p>
    </div>

    <!-- 筛选条件面板 -->
    <el-card class="filter-panel" shadow="never">
      <template #header>
        <div class="card-header">
          <span>筛选条件</span>
          <div class="header-actions">
            <el-button type="text" @click="resetFilters">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </div>
        </div>
      </template>

      <el-form :model="filters" label-width="100px" class="filter-form">
        <el-row :gutter="24">
          <el-col :span="8">
            <el-form-item label="市场类型">
              <el-select v-model="filters.market" placeholder="选择市场" clearable>
                <el-option label="全部" value="" />
                <el-option label="A股" value="A股" />
                <el-option label="港股" value="港股" />
                <el-option label="美股" value="美股" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="行业分类">
              <el-select
                v-model="filters.industry"
                placeholder="选择行业"
                multiple
                collapse-tags
                collapse-tags-tooltip
                clearable
              >
                <el-option
                  v-for="industry in industryOptions"
                  :key="industry.value"
                  :label="industry.label"
                  :value="industry.value"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="搜索">
              <el-input
                v-model="filters.searchKeyword"
                placeholder="输入股票代码或名称"
                clearable
                @keyup.enter="performSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row>
          <el-col :span="24">
            <div class="filter-actions">
              <el-button
                type="primary"
                @click="performSearch"
                :loading="loading"
                size="large"
              >
                <el-icon><Search /></el-icon>
                筛选
              </el-button>
              <el-button @click="resetFilters" size="large">
                重置条件
              </el-button>
            </div>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card v-if="stockList.length > 0 || loading" class="results-panel" shadow="never">
      <template #header>
        <div class="card-header">
          <span>股票列表 ({{ total }}只股票)</span>
        </div>
      </template>

      <el-table
        :data="stockList"
        v-loading="loading"
        stripe
        style="width: 100%"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="symbol" label="股票代码" min-width="120" sortable="custom">
          <template #default="{ row }">
            <el-link
              type="primary"
              @click="viewStockDetail(row)"
              :aria-label="`查看${row.name || row.symbol}详情`"
            >
              {{ row.symbol || row.code }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column prop="name" label="股票名称" min-width="150" sortable="custom" />

        <el-table-column prop="market" label="市场" min-width="100" align="center" sortable="custom">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.market || '-' }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="industry" label="行业" min-width="150" sortable="custom">
          <template #default="{ row }">
            {{ row.industry || '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="total_mv" label="总市值" min-width="130" align="right" sortable="custom">
          <template #default="{ row }">
            {{ formatMarketCap(row.total_mv) }}
          </template>
        </el-table-column>

        <el-table-column prop="pe" label="市盈率" min-width="110" align="right" sortable="custom">
          <template #default="{ row }">
            <span v-if="row.pe !== null && row.pe !== undefined">{{ row.pe.toFixed(2) }}</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="pb" label="市净率" min-width="110" align="right" sortable="custom">
          <template #default="{ row }">
            <span v-if="row.pb !== null && row.pb !== undefined">{{ row.pb.toFixed(2) }}</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="close" label="最新价" min-width="110" align="right" sortable="custom">
          <template #default="{ row }">
            <span v-if="row.close !== null && row.close !== undefined">¥{{ row.close.toFixed(2) }}</span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="pct_chg" label="涨跌幅" min-width="110" align="right" sortable="custom">
          <template #default="{ row }">
            <span v-if="row.pct_chg !== null && row.pct_chg !== undefined" :class="getChangeClass(row.pct_chg)">
              {{ row.pct_chg > 0 ? '+' : '' }}{{ row.pct_chg.toFixed(2) }}%
            </span>
            <span v-else class="text-gray">-</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页器 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 空状态 -->
    <el-empty
      v-else-if="!loading && hasSearched"
      description="未找到符合条件的股票"
      :image-size="200"
    >
      <el-button type="primary" @click="resetFilters">
        重置筛选条件
      </el-button>
    </el-empty>

    <!-- 初始状态提示 -->
    <el-card v-else class="initial-state" shadow="never">
      <el-empty description="请设置筛选条件，点击筛选按钮查询股票" :image-size="200">
        <el-button type="primary" @click="performSearch">
          <el-icon><Search /></el-icon>
          开始筛选
        </el-button>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { List, Search, Refresh } from '@element-plus/icons-vue'
import { stocksApi, type StockInfo, type StockListParams } from '@/api/stocks'
import { screeningApi, type IndustryOption } from '@/api/screening'

// 路由
const router = useRouter()

// 响应式数据
const loading = ref(false)
const hasSearched = ref(false)
const stockList = ref<StockInfo[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 筛选条件
const filters = reactive({
  market: '',
  industry: [] as string[],
  searchKeyword: ''
})
  
// 排序条件
const sortCondition = ref({
  field: '',
  order: ''  // 'ascending' | 'descending' | ''
})

// 行业选项
const industryOptions = ref<IndustryOption[]>([])

// 加载股票列表
const loadStockList = async () => {
  loading.value = true
  try {
    const params: StockListParams = {
      page: currentPage.value,
      page_size: pageSize.value
    }

    // 添加筛选条件
    if (filters.market) {
      params.market = filters.market
    }
    if (filters.industry && filters.industry.length > 0) {
      // 后端支持单个行业字段，前端多选时取第一个（或改为逗号分隔）
      params.industry = filters.industry[0]
    }
    if (filters.searchKeyword) {
      params.search = filters.searchKeyword
    }
    
    // 添加排序条件
    if (sortCondition.value.field && sortCondition.value.order) {
      params.sort_by = sortCondition.value.field
      params.sort_order = sortCondition.value.order === 'ascending' ? 'asc' : 'desc'
    }

    console.log('🔍 调用股票列表API，参数:', params)
    const response = await stocksApi.getStockList(params)
    
    // 处理响应数据 - 根据 StockListResponse 类型定义
    let processedResponse
    if (response && typeof response === 'object') {
      // 检查是否是 Axios 响应格式 { data: StockListResponse, ... }
      if (response.data && typeof response.data === 'object' &&
          'success' in response.data && 'data' in response.data && 'total' in response.data) {
        // Axios 响应格式，data 字段包含 StockListResponse
        processedResponse = response.data
      } else if ('success' in response && 'data' in response && 'total' in response) {
        // 直接是 StockListResponse 格式
        processedResponse = response
      } else {
        // 不符合预期格式
        console.error('API响应格式不符合预期:', response)
        throw new Error('API响应格式错误')
      }
    } else {
      throw new Error('API响应格式错误')
    }
    
    console.log('📥 股票列表API响应:', response)
    console.log('📋 解析后的数据:', processedResponse)
    
    const data = processedResponse as any

    // 处理响应数据
    if (data.success !== false) {
      // 处理数据列表
      if (Array.isArray(data.data)) {
        stockList.value = data.data
      } else if (Array.isArray(data)) {
        // 如果直接返回数组
        stockList.value = data
      } else {
        stockList.value = []
      }
      
      // 处理总数
      if (typeof data.total === 'number') {
        total.value = data.total
      } else if (typeof data.count === 'number') {
        total.value = data.count
      } else {
        // 如果没有total字段，使用数据长度（但这只是当前页）
        total.value = stockList.value.length
      }
      
      hasSearched.value = true
      console.log('📊 股票列表加载成功:', {
        count: stockList.value.length,
        total: total.value,
        currentPage: currentPage.value,
        pageSize: pageSize.value,
        params
      })
    } else {
      console.error('❌ 股票列表API返回错误:', data)
      throw new Error(data.message || '获取股票列表失败')
    }
  } catch (error: any) {
    console.error('加载股票列表失败:', error)
    ElMessage.error(error.message || '加载股票列表失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 加载行业列表
const loadIndustries = async () => {
  try {
    const response = await screeningApi.getIndustries()
    const data = response.data || response
    industryOptions.value = data.industries || []
  } catch (error) {
    console.error('加载行业列表失败:', error)
    // 使用默认行业列表
    industryOptions.value = [
      { label: '银行', value: '银行', count: 0 },
      { label: '证券', value: '证券', count: 0 },
      { label: '保险', value: '保险', count: 0 },
      { label: '房地产', value: '房地产', count: 0 },
      { label: '医药生物', value: '医药生物', count: 0 }
    ]
  }
}

// 执行搜索
const performSearch = () => {
  currentPage.value = 1
  loadStockList()
}

// 重置筛选条件
const resetFilters = () => {
  filters.market = ''
  filters.industry = []
  filters.searchKeyword = ''
  currentPage.value = 1
  // 重置排序条件
  sortCondition.value.field = ''
  sortCondition.value.order = ''
  hasSearched.value = false
  stockList.value = []
  total.value = 0
}

// 查看股票详情
const viewStockDetail = (stock: StockInfo) => {
  router.push({
    name: 'StockDetail',
    params: { code: stock.symbol || stock.code }
  })
}

// 格式化市值
const formatMarketCap = (marketCap: number | undefined): string => {
  if (!marketCap || !Number.isFinite(marketCap)) return '-'
  
  if (marketCap >= 10000) {
    return `${(marketCap / 10000).toFixed(2)}万亿`
  } else {
    return `${marketCap.toFixed(2)}亿`
  }
}

// 获取涨跌幅颜色类名
const getChangeClass = (changePercent: number): string => {
  if (changePercent > 0) return 'text-red'
  if (changePercent < 0) return 'text-green'
  return ''
}

// 分页处理
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadStockList()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadStockList()
}

// 排序处理
const handleSortChange = (params: { prop: string; order: 'ascending' | 'descending' | null }) => {
  if (params.prop && params.order) {
    sortCondition.value.field = params.prop
    sortCondition.value.order = params.order
  } else {
    // 如果取消排序，则清空排序条件
    sortCondition.value.field = ''
    sortCondition.value.order = ''
  }
  
  // 重置到第一页并重新加载数据
  currentPage.value = 1
  loadStockList()
}

// 生命周期
onMounted(() => {
  // 加载行业列表
  loadIndustries()
  // 默认加载第一页数据
  performSearch()  // 使用 performSearch 而不是直接调用 loadStockList，以确保 hasSearched 被设置
})
</script>

<style lang="scss" scoped>
.stock-list {
  .page-header {
    margin-bottom: 24px;

    .page-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 24px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin: 0 0 8px 0;
    }

    .page-description {
      color: var(--el-text-color-regular);
      margin: 0;
    }
  }

  .filter-panel {
    margin-bottom: 24px;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-actions {
        display: flex;
        gap: 8px;
      }
    }

    .filter-form {
      .filter-actions {
        display: flex;
        justify-content: center;
        gap: 16px;
        margin-top: 24px;
      }
    }
  }

  .results-panel {
    .pagination-wrapper {
      display: flex;
      justify-content: center;
      margin-top: 24px;
    }
  }

  .initial-state {
    margin-top: 24px;
    padding: 60px 0;
  }

  .text-red {
    color: #f56c6c;
  }

  .text-green {
    color: #67c23a;
  }

  .text-gray {
    color: var(--el-text-color-placeholder);
  }

  :deep(.el-link) {
    &:hover {
      text-decoration: underline;
    }
  }
}
</style>
