<template>
  <div class="page-container">
    <!-- KPI卡片 -->
    <el-row :gutter="16">
      <el-col :span="6">
        <div class="kpi-card">
          <div class="kpi-label">总利润</div>
          <div class="kpi-value" :class="totalProfit >= 0 ? 'text-success' : 'text-danger'">{{ formatMoney(totalProfit) }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="kpi-card">
          <div class="kpi-label">盈利批次</div>
          <div class="kpi-value text-success">{{ profitCount }}</div>
          <div class="kpi-sub">/ {{ profitList.length }} 批次</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="kpi-card">
          <div class="kpi-label">平均毛利率</div>
          <div class="kpi-value">{{ avgMargin }}%</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="kpi-card">
          <div class="kpi-label">平均ROI</div>
          <div class="kpi-value">{{ avgRoi }}%</div>
        </div>
      </el-col>
    </el-row>

    <!-- 利润排名 + 单只分析 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <span class="section-title">批次利润排名</span>
            <el-radio-group v-model="sortBy" size="small" style="margin-left: 20px;" @change="loadData">
              <el-radio-button value="gross_profit">按利润</el-radio-button>
              <el-radio-button value="profit_margin">按毛利率</el-radio-button>
              <el-radio-button value="roi">按ROI</el-radio-button>
            </el-radio-group>
          </template>
          <el-table :data="profitList" size="small" highlight-current-row @row-click="handleRowClick" border>
            <el-table-column type="index" label="排名" width="60">
              <template #default="{ $index }">
                <el-tag v-if="$index < 3" :type="$index === 0 ? 'danger' : $index === 1 ? 'warning' : 'success'" size="small">{{ $index + 1 }}</el-tag>
                <span v-else>{{ $index + 1 }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="batch_no" label="批次编号" min-width="140" />
            <el-table-column prop="breed_name" label="品种" width="140" />
            <el-table-column prop="total_revenue" label="总收入" width="120">
              <template #default="{ row }">{{ formatMoney(row.total_revenue) }}</template>
            </el-table-column>
            <el-table-column prop="total_cost" label="总成本" width="120">
              <template #default="{ row }">{{ formatMoney(row.total_cost) }}</template>
            </el-table-column>
            <el-table-column prop="gross_profit" label="毛利润" width="120">
              <template #default="{ row }">
                <span :class="row.gross_profit >= 0 ? 'text-success' : 'text-danger'">{{ formatMoney(row.gross_profit) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="profit_margin" label="毛利率" width="90">
              <template #default="{ row }">
                <span :class="row.profit_margin >= 0 ? 'text-success' : 'text-danger'">{{ row.profit_margin }}%</span>
              </template>
            </el-table-column>
            <el-table-column prop="roi" label="ROI" width="80">
              <template #default="{ row }">
                <span :class="row.roi >= 0 ? 'text-success' : 'text-danger'">{{ row.roi }}%</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never">
          <template #header><span class="section-title">单只成本/收入分析</span></template>
          <div v-if="selectedBatchProfit">
            <div class="detail-item">
              <label>批次：</label>{{ selectedBatchProfit.batch_no }}
            </div>
            <el-divider />
            <div class="detail-metric">
              <div class="metric-row">
                <span class="metric-label">单只成本</span>
                <span class="metric-value text-danger">¥{{ selectedBatchProfit.cost_per_bird }}</span>
              </div>
              <el-progress :percentage="Math.min(100, selectedBatchProfit.cost_per_bird / 3)" :show-text="false" color="#f56c6c" />
            </div>
            <div class="detail-metric">
              <div class="metric-row">
                <span class="metric-label">单只收入</span>
                <span class="metric-value text-success">¥{{ selectedBatchProfit.revenue_per_bird }}</span>
              </div>
              <el-progress :percentage="Math.min(100, selectedBatchProfit.revenue_per_bird / 3)" :show-text="false" color="#67c23a" />
            </div>
            <div class="detail-metric">
              <div class="metric-row">
                <span class="metric-label">单只利润</span>
                <span class="metric-value" :class="selectedBatchProfit.profit_per_bird >= 0 ? 'text-success' : 'text-danger'">¥{{ selectedBatchProfit.profit_per_bird }}</span>
              </div>
              <el-progress :percentage="50 + parseFloat(selectedBatchProfit.profit_per_bird)" :show-text="false" :color="selectedBatchProfit.profit_per_bird >= 0 ? '#67c23a' : '#f56c6c'" />
            </div>
            <el-divider />
            <v-chart class="chart-sm" :option="batchProfitGaugeOption" autoresize ref="gaugeChartRef" />
          </div>
          <div v-else class="empty-state">
            <p>点击左侧批次查看单只分析</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 利润趋势图 -->
    <el-card shadow="never" style="margin-top: 20px;">
      <template #header><span class="section-title">利润对比图</span></template>
      <v-chart class="chart" :option="profitBarOption" autoresize ref="profitBarRef" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, GaugeChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { mockApi } from '@/api/mock'

use([CanvasRenderer, BarChart, GaugeChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

const sortBy = ref('gross_profit')
const profitList = ref([])
const selectedBatchProfit = ref(null)
const profitBarRef = ref(null)
const gaugeChartRef = ref(null)

onUnmounted(() => {
  profitBarRef.value?.dispose?.()
  gaugeChartRef.value?.dispose?.()
})

const totalProfit = computed(() => profitList.value.reduce((sum, p) => sum + p.gross_profit, 0))
const profitCount = computed(() => profitList.value.filter(p => p.gross_profit > 0).length)
const avgMargin = computed(() => {
  if (!profitList.value.length) return 0
  return (profitList.value.reduce((sum, p) => sum + parseFloat(p.profit_margin), 0) / profitList.value.length).toFixed(2)
})
const avgRoi = computed(() => {
  if (!profitList.value.length) return 0
  return (profitList.value.reduce((sum, p) => sum + parseFloat(p.roi), 0) / profitList.value.length).toFixed(2)
})

const profitBarOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  legend: { data: ['收入', '成本', '利润'] },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: profitList.value.map(p => p.batch_no) },
  yAxis: { type: 'value', name: '金额(元)' },
  series: [
    { name: '收入', type: 'bar', data: profitList.value.map(p => p.total_revenue), itemStyle: { color: '#67c23a' } },
    { name: '成本', type: 'bar', data: profitList.value.map(p => p.total_cost), itemStyle: { color: '#f56c6c' } },
    { name: '利润', type: 'bar', data: profitList.value.map(p => p.gross_profit), itemStyle: { color: '#409eff' } }
  ]
}))

const batchProfitGaugeOption = computed(() => {
  if (!selectedBatchProfit.value) return {}
  const margin = parseFloat(selectedBatchProfit.value.profit_margin)
  return {
    series: [{
      type: 'gauge',
      startAngle: 180, endAngle: 0,
      min: -50, max: 50,
      axisLine: { lineStyle: { width: 20, color: [[0.5, '#f56c6c'], [1, '#67c23a']] } },
      pointer: { itemStyle: { color: 'auto' } },
      axisTick: { distance: -20, length: 8 },
      splitLine: { distance: -20, length: 20 },
      axisLabel: { distance: -15, fontSize: 12 },
      detail: { valueAnimation: true, formatter: '{value}%', fontSize: 30, offsetCenter: [0, '-10%'] },
      data: [{ value: margin, name: '毛利率' }]
    }]
  }
})

function formatMoney(val) {
  return val ? `¥${parseFloat(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '¥0.00'
}

function handleRowClick(row) {
  selectedBatchProfit.value = row
}

async function loadData() {
  const res = await mockApi.getProfitRanking({ sort_by: sortBy.value })
  profitList.value = res.data.list
  if (profitList.value.length > 0 && !selectedBatchProfit.value) {
    selectedBatchProfit.value = profitList.value[0]
  }
}

onMounted(loadData)
</script>

<style scoped>
.detail-item { padding: 6px 0; font-size: 14px; }
.detail-item label { color: var(--text-secondary); }
.detail-metric { margin: 16px 0; }
.metric-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.metric-label { font-size: 14px; color: #666; }
.metric-value { font-size: 20px; font-weight: 600; }
.chart { width: 100%; height: 320px; }
.chart-sm { width: 100%; height: 200px; }
</style>
