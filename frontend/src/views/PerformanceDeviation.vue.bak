<template>
  <div class="page-container">
    <!-- 维度选择 -->
    <el-card shadow="never" class="search-bar">
      <el-row :gutter="16" align="middle">
        <el-col :span="6">
          <el-select v-model="analysisDimension" placeholder="分析维度" @change="handleDimensionChange">
            <el-option label="按批次分析" value="batch" />
            <el-option label="按品种分析" value="breed" />
            <el-option label="按时间分析" value="time" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="selectedTarget" :placeholder="targetPlaceholder" @change="loadData">
            <el-option v-for="opt in targetOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-col>
        <el-col :span="12" style="text-align: right;">
          <el-date-picker v-if="analysisDimension === 'time'" v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" @change="loadData" />
        </el-col>
      </el-row>
    </el-card>

    <!-- KPI偏差卡片 -->
    <el-row :gutter="16" style="margin-top: 20px;" v-if="performanceData">
      <el-col :span="8">
        <el-card shadow="never" :class="['deviation-card', getDeviationClass(performanceData.survival?.deviation)]">
          <div class="deviation-title">成活率偏差</div>
          <div class="deviation-main">
            <span class="deviation-actual">{{ performanceData.survival?.actual }}%</span>
            <span class="deviation-sep">vs</span>
            <span class="deviation-std">{{ performanceData.survival?.standard }}%</span>
          </div>
          <div class="deviation-result">
            <el-tag :type="performanceData.survival?.deviation >= 0 ? 'success' : 'danger'" size="large">
              {{ performanceData.survival?.deviation >= 0 ? '+' : '' }}{{ performanceData.survival?.deviation }}%
              ({{ performanceData.survival?.deviation_pct }}%)
            </el-tag>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" :class="['deviation-card', getDeviationClass(performanceData.adg?.deviation)]">
          <div class="deviation-title">日增重偏差</div>
          <div class="deviation-main">
            <span class="deviation-actual">{{ performanceData.adg?.actual }}g</span>
            <span class="deviation-sep">vs</span>
            <span class="deviation-std">{{ performanceData.adg?.standard }}g</span>
          </div>
          <div class="deviation-result">
            <el-tag :type="performanceData.adg?.deviation >= 0 ? 'success' : 'danger'" size="large">
              {{ performanceData.adg?.deviation >= 0 ? '+' : '' }}{{ performanceData.adg?.deviation }}g
              ({{ performanceData.adg?.deviation_pct }}%)
            </el-tag>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" :class="['deviation-card', getFmrDeviationClass(performanceData.fmr?.deviation)]">
          <div class="deviation-title">料肉比偏差</div>
          <div class="deviation-main">
            <span class="deviation-actual">{{ performanceData.fmr?.actual }}</span>
            <span class="deviation-sep">vs</span>
            <span class="deviation-std">{{ performanceData.fmr?.standard }}</span>
          </div>
          <div class="deviation-result">
            <el-tag :type="performanceData.fmr?.deviation <= 0 ? 'success' : 'danger'" size="large">
              {{ performanceData.fmr?.deviation >= 0 ? '+' : '' }}{{ performanceData.fmr?.deviation }}
              ({{ performanceData.fmr?.deviation_pct }}%)
            </el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 偏差趋势图 -->
    <el-card shadow="never" class="chart-container" style="margin-top: 20px;" v-if="performanceData?.trend?.length > 0">
      <template #header><span class="section-title">偏差率趋势</span></template>
      <v-chart class="chart" :option="trendChartOption" autoresize ref="trendChartRef" />
    </el-card>

    <!-- 达标率 + 偏差分布 -->
    <el-row :gutter="20" style="margin-top: 20px;" v-if="performanceData">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span class="section-title">达标率统计</span></template>
          <v-chart class="chart" :option="gaugeOption" autoresize ref="gaugeChartRef" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span class="section-title">偏差分布</span></template>
          <el-table :data="deviationTableData" size="small" border>
            <el-table-column prop="metric" label="指标" />
            <el-table-column prop="actual" label="实际值" />
            <el-table-column prop="standard" label="标准值" />
            <el-table-column prop="deviation" label="偏差">
              <template #default="{ row }">
                <span :class="row.isGood ? 'text-success' : 'text-danger'">{{ row.deviation >= 0 ? '+' : '' }}{{ row.deviation }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.isGood ? 'success' : 'danger'" size="small">{{ row.isGood ? '达标' : '偏差' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, GaugeChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { mockApi } from '@/api/mock'

use([CanvasRenderer, LineChart, GaugeChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

const analysisDimension = ref('batch')
const selectedTarget = ref('')
const dateRange = ref(null)
const batchList = ref([])
const breedList = ref([{ id: 1, breed_name: 'AA+白羽肉鸡父母代' }, { id: 2, breed_name: 'ROSS308白羽肉鸡' }])
const performanceData = ref(null)
const trendChartRef = ref(null)
const gaugeChartRef = ref(null)

onUnmounted(() => {
  trendChartRef.value?.dispose?.()
  gaugeChartRef.value?.dispose?.()
})

const targetPlaceholder = computed(() => {
  const map = { batch: '选择批次', breed: '选择品种', time: '选择时间范围' }
  return map[analysisDimension.value]
})

const targetOptions = computed(() => {
  if (analysisDimension.value === 'batch') return batchList.value.map(b => ({ value: b.id, label: `${b.batch_no} - ${b.batch_name}` }))
  if (analysisDimension.value === 'breed') return breedList.value.map(b => ({ value: b.id, label: b.breed_name }))
  return []
})

const deviationTableData = computed(() => {
  if (!performanceData.value) return []
  const p = performanceData.value
  return [
    { metric: '成活率', actual: `${p.survival.actual}%`, standard: `${p.survival.standard}%`, deviation: p.survival.deviation, isGood: parseFloat(p.survival.deviation) >= 0 },
    { metric: '日增重', actual: `${p.adg.actual}g`, standard: `${p.adg.standard}g`, deviation: p.adg.deviation, isGood: parseFloat(p.adg.deviation) >= 0 },
    { metric: '料肉比', actual: p.fmr.actual, standard: p.fmr.standard, deviation: p.fmr.deviation, isGood: parseFloat(p.fmr.deviation) <= 0 }
  ]
})

const trendChartOption = computed(() => {
  const trend = performanceData.value?.trend || []
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['成活率偏差', '日增重偏差', '料肉比偏差'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: trend.map(t => t.date) },
    yAxis: { type: 'value', name: '偏差率(%)' },
    series: [
      { name: '成活率偏差', type: 'line', data: trend.map(t => t.survival_dev), itemStyle: { color: '#409eff' } },
      { name: '日增重偏差', type: 'line', data: trend.map(t => t.adg_dev), itemStyle: { color: '#67c23a' } },
      { name: '料肉比偏差', type: 'line', data: trend.map(t => (t.fmr_dev * 100).toFixed(2)), itemStyle: { color: '#e6a23c' } }
    ]
  }
})

const gaugeOption = computed(() => {
  const survival = parseFloat(performanceData.value?.survival?.deviation || 0)
  const adg = parseFloat(performanceData.value?.adg?.deviation || 0)
  const fmr = parseFloat(performanceData.value?.fmr?.deviation || 0)
  const passCount = [survival >= 0, adg >= 0, fmr <= 0].filter(Boolean).length

  return {
    series: [{
      type: 'gauge',
      startAngle: 180, endAngle: 0,
      min: 0, max: 3,
      splitNumber: 3,
      itemStyle: { color: passCount >= 2 ? '#67c23a' : '#e6a23c' },
      progress: { show: true, width: 18 },
      pointer: { show: false },
      axisLine: { lineStyle: { width: 18 } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      title: { offsetCenter: [0, '-20%'], fontSize: 16 },
      detail: { valueAnimation: true, fontSize: 36, offsetCenter: [0, '10%'], formatter: '{value}/3项达标' },
      data: [{ value: passCount, name: '达标率' }]
    }]
  }
})

function getDeviationClass(val) {
  const n = parseFloat(val || 0)
  return n >= 0 ? 'good' : 'bad'
}

function getFmrDeviationClass(val) {
  const n = parseFloat(val || 0)
  return n <= 0 ? 'good' : 'bad'
}

function handleDimensionChange() {
  selectedTarget.value = ''
  performanceData.value = null
}

async function loadData() {
  if (!selectedTarget.value && analysisDimension.value !== 'time') return
  if (analysisDimension.value === 'batch') {
    const res = await mockApi.getBatchPerformance(selectedTarget.value)
    performanceData.value = res.data
  }
}

onMounted(async () => {
  const res = await mockApi.getBatches()
  batchList.value = res.data.list
  if (batchList.value.length > 0) {
    selectedTarget.value = batchList.value[0].id
    await loadData()
  }
})
</script>

<style scoped>
.search-bar { margin-bottom: 0; }
.deviation-card { text-align: center; padding: 10px; }
.deviation-card.good { border-top: 4px solid #67c23a; }
.deviation-card.bad { border-top: 4px solid #f56c6c; }
.deviation-title { font-size: 14px; color: #666; margin-bottom: 12px; }
.deviation-main { margin: 12px 0; }
.deviation-actual { font-size: 28px; font-weight: 600; color: #409eff; }
.deviation-sep { font-size: 14px; color: #999; margin: 0 10px; }
.deviation-std { font-size: 18px; color: #666; }
.deviation-result { margin-top: 12px; }
.chart { width: 100%; height: 300px; }
</style>
