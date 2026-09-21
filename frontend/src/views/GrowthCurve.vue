<template>
  <div class="page-container">
    <!-- 搜索栏 -->
    <el-card class="search-bar" shadow="never">
      <el-row :gutter="16" align="middle">
        <el-col :span="6">
          <el-input v-model="searchQuery" placeholder="输入个体编号或扫描耳标" clearable>
            <template #append>
              <el-button :icon="Search" @click="handleSearch" />
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-select v-model="selectedBatch" placeholder="选择批次" clearable @change="handleBatchChange">
            <el-option v-for="b in batchList" :key="b.id" :label="`${b.batch_no} (${b.batch_name})`" :value="b.id" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-radio-group v-model="timeRange" size="small">
            <el-radio-button :value="7">近7天</el-radio-button>
            <el-radio-button :value="30">近30天</el-radio-button>
            <el-radio-button :value="0">全周期</el-radio-button>
          </el-radio-group>
        </el-col>
        <el-col :span="6" style="text-align: right;">
          <el-button type="primary" :icon="Download" @click="exportData">导出CSV</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 主体内容 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 左侧：个体/批次列表 -->
      <el-col :span="6">
        <el-card shadow="never">
          <template #header>
            <span>{{ selectedBatch ? '批次个体列表' : '最近查询' }}</span>
          </template>
          <el-table :data="individualList" size="small" highlight-current-row @row-click="handleRowClick" v-loading="loading.list">
            <el-table-column prop="animal_no" label="个体编号" min-width="140" />
            <el-table-column prop="weight_in" label="入栏体重(g)" width="100">
              <template #default="{ row }">{{ row.weight_in?.toFixed(1) }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="70">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 1 ? 'success' : 'info'">{{ row.status === 1 ? '在养' : '出栏' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 个体信息卡片 -->
        <el-card shadow="never" style="margin-top: 16px;" v-if="currentIndividual">
          <template #header><span>个体信息</span></template>
          <div class="info-item"><label>编号：</label>{{ currentIndividual.animal_no }}</div>
          <div class="info-item"><label>批次：</label>{{ currentIndividual.batch_no }}</div>
          <div class="info-item"><label>品种：</label>{{ currentIndividual.breed_name }}</div>
          <div class="info-item"><label>性别：</label>{{ currentIndividual.gender === 1 ? '公' : '母' }}</div>
          <div class="info-item"><label>入栏日龄：</label>{{ currentIndividual.age_day_in }}天</div>
          <div class="info-item"><label>入栏体重：</label>{{ currentIndividual.weight_in?.toFixed(1) }}g</div>
        </el-card>
      </el-col>

      <!-- 右侧：图表区 -->
      <el-col :span="18">
        <!-- 生长曲线 -->
        <el-card shadow="never" class="chart-container" v-loading="loading.curve">
          <template #header>
            <span class="section-title">体重-日龄生长曲线</span>
            <el-switch v-model="showStdCurve" active-text="显示标准曲线" style="margin-left: 20px;" />
          </template>
          <v-chart v-if="growthData.records.length > 0" class="chart" :option="growthChartOption" autoresize ref="growthChartRef" />
          <div v-else class="empty-state">
            <el-icon size="64"><DataLine /></el-icon>
            <p>请选择个体或批次查看生长曲线</p>
          </div>
        </el-card>

        <!-- 批次体重分布 -->
        <el-card shadow="never" class="chart-container" style="margin-top: 16px;" v-if="selectedBatch && weightDistData.count > 0" v-loading="loading.dist">
          <template #header><span class="section-title">批次体重分布</span></template>
          <el-row :gutter="20">
            <el-col :span="12">
              <v-chart class="chart" :option="boxplotOption" autoresize ref="boxplotChartRef" />
            </el-col>
            <el-col :span="12">
              <v-chart class="chart" :option="histogramOption" autoresize ref="histogramChartRef" />
            </el-col>
          </el-row>
        </el-card>

        <!-- 偏差分析 -->
        <el-card shadow="never" style="margin-top: 16px;" v-if="deviationData.length > 0">
          <template #header><span class="section-title">生长偏差分析</span></template>
          <el-table :data="deviationData" size="small" border>
            <el-table-column prop="age_days" label="日龄" width="80" />
            <el-table-column prop="weight" label="实际体重(g)" width="120" />
            <el-table-column prop="std_weight" label="标准体重(g)" width="120" />
            <el-table-column prop="deviation" label="偏差(g)" width="100">
              <template #default="{ row }">
                <span :class="row.deviation >= 0 ? 'text-success' : 'text-danger'">{{ row.deviation >= 0 ? '+' : '' }}{{ row.deviation }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="deviation_pct" label="偏差率(%)" min-width="120">
              <template #default="{ row }">
                <span :class="row.deviation_pct >= 0 ? 'text-success' : 'text-danger'">{{ row.deviation_pct >= 0 ? '+' : '' }}{{ row.deviation_pct }}%</span>
              </template>
            </el-table-column>
            <el-table-column prop="recorder" label="记录人" width="100" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BoxplotChart, BarChart, CustomChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent, DataZoomComponent, MarkLineComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { Search, Download, DataLine } from '@element-plus/icons-vue'
import { mockApi } from '@/api/mock'

use([CanvasRenderer, LineChart, BoxplotChart, BarChart, CustomChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent, DataZoomComponent, MarkLineComponent])

const searchQuery = ref('')
const selectedBatch = ref('')
const timeRange = ref(0)
const showStdCurve = ref(true)
const batchList = ref([])
const individualList = ref([])
const currentIndividual = ref(null)
const growthData = ref({ records: [], std_curve: [] })
const weightDistData = ref({ count: 0, avg: 0, min: 0, max: 0, q1: 0, median: 0, q3: 0, std: 0 })
const loading = ref({ list: false, curve: false, dist: false })
const growthChartRef = ref(null)
const boxplotChartRef = ref(null)
const histogramChartRef = ref(null)

onUnmounted(() => {
  growthChartRef.value?.dispose?.()
  boxplotChartRef.value?.dispose?.()
  histogramChartRef.value?.dispose?.()
})

onMounted(async () => {
  const res = await mockApi.getBatches()
  batchList.value = res.data.list
})

const deviationData = computed(() => {
  if (!growthData.value.records.length) return []
  return growthData.value.records.map(r => {
    const std = growthData.value.std_curve.find(s => s.age_days === r.age_days)
    const dev = std ? (r.weight - std.std_weight).toFixed(1) : 0
    const devPct = std ? ((dev / std.std_weight) * 100).toFixed(2) : 0
    return { ...r, std_weight: std?.std_weight || '-', deviation: dev, deviation_pct: devPct }
  })
})

const growthChartOption = computed(() => {
  const records = growthData.value.records
  const stdCurve = growthData.value.std_curve
  const ages = [...new Set([...records.map(r => r.age_days), ...stdCurve.map(s => s.age_days)])].sort((a, b) => a - b)

  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['实际体重', '标准体重'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', name: '日龄(天)', data: ages.map(a => `${a}天`) },
    yAxis: { type: 'value', name: '体重(g)', min: 0 },
    series: [
      { name: '实际体重', type: 'line', smooth: true, data: ages.map(a => records.find(r => r.age_days === a)?.weight || null), itemStyle: { color: '#409eff' }, areaStyle: { opacity: 0.1 } },
      { name: '标准体重', type: 'line', smooth: true, data: showStdCurve.value ? ages.map(a => stdCurve.find(s => s.age_days === a)?.std_weight || null) : [], itemStyle: { color: '#67c23a' }, lineStyle: { type: 'dashed' } }
    ]
  }
})

const boxplotOption = computed(() => {
  const d = weightDistData.value
  return {
    tooltip: { trigger: 'item' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: ['批次体重分布'] },
    yAxis: { type: 'value', name: '体重(g)' },
    series: [{ type: 'boxplot', data: [[d.min, d.q1, d.median, d.q3, d.max]], itemStyle: { color: '#409eff', borderColor: '#409eff' } }]
  }
})

const histogramOption = computed(() => {
  const records = growthData.value.records
  const weights = records.map(r => r.weight)
  if (!weights.length) return {}
  const min = Math.min(...weights), max = Math.max(...weights)
  const bins = 8
  const step = (max - min) / bins
  const histData = Array(bins).fill(0)
  weights.forEach(w => {
    const idx = Math.min(Math.floor((w - min) / step), bins - 1)
    histData[idx]++
  })
  const labels = Array.from({ length: bins }, (_, i) => `${(min + i * step).toFixed(0)}-${(min + (i + 1) * step).toFixed(0)}`)

  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: labels, name: '体重区间(g)', axisLabel: { rotate: 30 } },
    yAxis: { type: 'value', name: '个体数' },
    series: [{ type: 'bar', data: histData, itemStyle: { color: '#67c23a' } }]
  }
})

async function handleSearch() {
  loading.value.list = true
  const res = await mockApi.getIndividuals({ keyword: searchQuery.value })
  individualList.value = res.data.list
  loading.value.list = false
  if (individualList.value.length === 1) {
    await selectIndividual(individualList.value[0].id)
  }
}

async function handleBatchChange(batchId) {
  if (!batchId) {
    individualList.value = []
    growthData.value = { records: [], std_curve: [] }
    weightDistData.value = { count: 0 }
    return
  }
  loading.value.list = true
  const res = await mockApi.getIndividuals({ batch_id: batchId })
  individualList.value = res.data.list
  loading.value.list = false

  // 加载批次生长汇总
  loading.value.dist = true
  const distRes = await mockApi.getBatchGrowthSummary(batchId)
  weightDistData.value = distRes.data
  loading.value.dist = false

  // 加载批次生长曲线（取第一个个体）
  if (individualList.value.length > 0) {
    const ind = individualList.value[0]
    await selectIndividual(ind.id)
  }
}

async function handleRowClick(row) {
  await selectIndividual(row.id)
}

async function selectIndividual(animalId) {
  loading.value.curve = true
  const [indRes, curveRes] = await Promise.all([
    mockApi.getIndividualDetail(animalId),
    mockApi.getGrowthCurve({ animal_id: animalId })
  ])
  currentIndividual.value = indRes.data
  growthData.value = curveRes.data
  loading.value.curve = false
}

function exportData() {
  const rows = deviationData.value.map(r => `${r.age_days},${r.weight},${r.std_weight},${r.deviation},${r.deviation_pct},${r.recorder}`).join('\n')
  const csv = `日龄,实际体重(g),标准体重(g),偏差(g),偏差率(%),记录人\n${rows}`
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `生长曲线_${currentIndividual.value?.animal_no || '批次'}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

watch(selectedBatch, handleBatchChange)
</script>

<style scoped>
.search-bar { margin-bottom: 0; }
.info-item { padding: 6px 0; font-size: 14px; }
.info-item label { color: var(--text-secondary); display: inline-block; width: 80px; }
.chart { width: 100%; height: 350px; }
</style>
