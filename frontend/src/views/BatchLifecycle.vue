<template>
  <div class="page-container">
    <!-- 批次选择器 -->
    <el-card shadow="never" class="search-bar">
      <el-row :gutter="16" align="middle">
        <el-col :span="8">
          <el-select v-model="selectedBatch" placeholder="选择批次" style="width: 100%;" @change="loadBatchData">
            <el-option v-for="b in batchList" :key="b.id" :label="`${b.batch_no} - ${b.batch_name}`" :value="b.id" />
          </el-select>
        </el-col>
        <el-col :span="10">
          <el-radio-group v-model="statusFilter" size="small" @change="filterBatches">
            <el-radio-button value="">全部</el-radio-button>
            <el-radio-button :value="1">养殖中</el-radio-button>
            <el-radio-button :value="2">已出栏</el-radio-button>
            <el-radio-button :value="3">已淘汰</el-radio-button>
          </el-radio-group>
        </el-col>
        <el-col :span="6" style="text-align: right;">
          <el-button :icon="Document" @click="exportReport">导出报告</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 空状态 -->
    <div v-if="!batchDetail" class="empty-state">
      <el-icon size="64"><Calendar /></el-icon>
      <p>请选择一个批次查看生命周期</p>
    </div>

    <template v-else>
      <!-- KPI卡片 -->
      <el-row :gutter="16" style="margin-top: 20px;">
        <el-col :span="4" v-for="kpi in kpiList" :key="kpi.label">
          <div class="kpi-card">
            <div class="kpi-label">{{ kpi.label }}</div>
            <div class="kpi-value" :style="{ color: kpi.color }">{{ kpi.value }}</div>
            <div class="kpi-sub" v-if="kpi.sub">{{ kpi.sub }}</div>
          </div>
        </el-col>
      </el-row>

      <!-- 时间轴 + 标签页 -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="8">
          <el-card shadow="never">
            <template #header><span class="section-title">生命周期时间轴</span></template>
            <el-timeline>
              <el-timeline-item
                v-for="(op, idx) in operationList"
                :key="idx"
                :type="idx === 0 ? 'primary' : ''"
                :timestamp="op.operation_date"
              >
                <h4>{{ op.operation_name }}</h4>
                <p style="color: #666; font-size: 13px;">{{ op.detail }}</p>
                <p style="color: #999; font-size: 12px;">操作人：{{ op.operator }}</p>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>

        <el-col :span="16">
          <el-card shadow="never">
            <template #header><span class="section-title">关联数据</span></template>
            <el-tabs v-model="activeTab" type="border-card">
              <!-- 个体 -->
              <el-tab-pane label="个体" name="individual">
                <el-table :data="individualList" size="small" max-height="350">
                  <el-table-column prop="animal_no" label="个体编号" />
                  <el-table-column prop="gender" label="性别" width="70">
                    <template #default="{ row }">{{ row.gender === 1 ? '公' : '母' }}</template>
                  </el-table-column>
                  <el-table-column prop="weight_in" label="入栏体重(g)" width="110">
                    <template #default="{ row }">{{ row.weight_in?.toFixed(1) }}</template>
                  </el-table-column>
                  <el-table-column prop="status" label="状态" width="80">
                    <template #default="{ row }">
                      <el-tag size="small" :type="row.status === 1 ? 'success' : 'info'">{{ row.status === 1 ? '在养' : '出栏' }}</el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </el-tab-pane>

              <!-- 操作 -->
              <el-tab-pane label="操作" name="operation">
                <el-table :data="operationList" size="small" max-height="350">
                  <el-table-column prop="operation_date" label="日期" width="110" />
                  <el-table-column prop="operation_name" label="操作类型" width="100" />
                  <el-table-column prop="detail" label="详情" />
                  <el-table-column prop="operator" label="操作人" width="100" />
                </el-table>
              </el-tab-pane>

              <!-- 环境 -->
              <el-tab-pane label="环境" name="environment">
                <v-chart class="chart" :option="envChartOption" autoresize ref="envChartRef" />
              </el-tab-pane>

              <!-- 健康 -->
              <el-tab-pane label="健康" name="health">
                <el-table :data="healthList" size="small" max-height="350">
                  <el-table-column prop="record_date" label="日期" width="110" />
                  <el-table-column prop="event_name" label="事件" />
                  <el-table-column prop="drug_name" label="药品/疫苗" />
                  <el-table-column prop="veterinarian" label="兽医" width="100" />
                  <el-table-column prop="cost" label="费用(元)" width="100">
                    <template #default="{ row }">{{ row.cost?.toFixed(2) }}</template>
                  </el-table-column>
                </el-table>
              </el-tab-pane>

              <!-- 死淘 -->
              <el-tab-pane label="死淘" name="mortality">
                <el-row :gutter="20">
                  <el-col :span="12">
                    <v-chart class="chart-sm" :option="mortalityPieOption" autoresize ref="mortalityPieRef" />
                  </el-col>
                  <el-col :span="12">
                    <el-statistic title="死淘总数" :value="mortalityCount" value-style="color: #f56c6c; font-size: 32px;" />
                    <el-statistic title="死淘率" :value="mortalityRate" suffix="%" value-style="color: #f56c6c; font-size: 24px; margin-top: 16px;" />
                  </el-col>
                </el-row>
              </el-tab-pane>

              <!-- 成本 -->
              <el-tab-pane label="成本" name="cost">
                <el-row :gutter="20">
                  <el-col :span="12">
                    <v-chart class="chart-sm" :option="costPieOption" autoresize ref="costPieRef" />
                  </el-col>
                  <el-col :span="12">
                    <el-table :data="costList" size="small" show-summary :summary-method="costSummary">
                      <el-table-column prop="type" label="成本类型" />
                      <el-table-column prop="amount" label="金额(元)">
                        <template #default="{ row }">{{ row.amount.toLocaleString() }}</template>
                      </el-table-column>
                      <el-table-column prop="pct" label="占比" width="100">
                        <template #default="{ row }">{{ row.pct }}%</template>
                      </el-table-column>
                    </el-table>
                  </el-col>
                </el-row>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { Document, Calendar } from '@element-plus/icons-vue'
import { mockApi } from '@/api/mock'

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

const selectedBatch = ref('')
const statusFilter = ref('')
const batchList = ref([])
const batchDetail = ref(null)
const individualList = ref([])
const operationList = ref([])
const healthList = ref([])
const environmentList = ref([])
const activeTab = ref('individual')
const envChartRef = ref(null)
const mortalityPieRef = ref(null)
const costPieRef = ref(null)

onUnmounted(() => {
  envChartRef.value?.dispose?.()
  mortalityPieRef.value?.dispose?.()
  costPieRef.value?.dispose?.()
})
const loading = ref(false)

const kpiList = computed(() => {
  if (!batchDetail.value) return []
  const b = batchDetail.value
  const survivalRate = ((b.quantity_current || 0) / b.quantity_initial * 100).toFixed(2)
  const ageDays = Math.ceil((new Date() - new Date(b.date_in)) / 86400000) + b.age_day_in
  return [
    { label: '入栏数量', value: b.quantity_initial?.toLocaleString(), color: '#409eff', sub: '羽' },
    { label: '当前存栏', value: b.quantity_current?.toLocaleString(), color: '#67c23a', sub: '羽' },
    { label: '成活率', value: `${survivalRate}%`, color: survivalRate >= 95 ? '#67c23a' : '#e6a23c' },
    { label: '当前日龄', value: `${ageDays}`, color: '#409eff', sub: '天' },
    { label: '预计出栏', value: b.date_out || '-', color: '#909399' },
    { label: '负责人', value: b.responsible_person || '-', color: '#409eff' }
  ]
})

const mortalityCount = computed(() => {
  if (!batchDetail.value) return 0
  return batchDetail.value.quantity_initial - (batchDetail.value.quantity_current || 0)
})

const mortalityRate = computed(() => {
  if (!batchDetail.value || !batchDetail.value.quantity_initial) return 0
  return ((mortalityCount.value / batchDetail.value.quantity_initial) * 100).toFixed(2)
})

const costList = ref([
  { type: '饲料', amount: 1200000, pct: 60 },
  { type: '药品/疫苗', amount: 50000, pct: 2.5 },
  { type: '人工', amount: 300000, pct: 15 },
  { type: '折旧', amount: 200000, pct: 10 },
  { type: '水电', amount: 150000, pct: 7.5 },
  { type: '其他', amount: 100000, pct: 5 }
])

const envChartOption = computed(() => {
  const data = environmentList.value
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['温度', '湿度', '氨气', 'CO2'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: data.map(d => d.record_date.slice(5)) },
    yAxis: [
      { type: 'value', name: '温度(℃)/湿度(%)', position: 'left' },
      { type: 'value', name: '氨气(ppm)/CO2(ppm)', position: 'right' }
    ],
    series: [
      { name: '温度', type: 'line', data: data.map(d => d.temperature.toFixed(1)), yAxisIndex: 0 },
      { name: '湿度', type: 'line', data: data.map(d => d.humidity.toFixed(1)), yAxisIndex: 0 },
      { name: '氨气', type: 'line', data: data.map(d => d.ammonia.toFixed(1)), yAxisIndex: 1 },
      { name: 'CO2', type: 'line', data: data.map(d => d.co2.toFixed(0)), yAxisIndex: 1 }
    ]
  }
})

const mortalityPieOption = computed(() => ({
  tooltip: { trigger: 'item' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    data: [
      { value: mortalityCount.value, name: '死淘', itemStyle: { color: '#f56c6c' } },
      { value: batchDetail.value?.quantity_current || 0, name: '存活', itemStyle: { color: '#67c23a' } }
    ]
  }]
}))

const costPieOption = computed(() => ({
  tooltip: { trigger: 'item' },
  series: [{
    type: 'pie',
    radius: '60%',
    data: costList.value.map(c => ({ value: c.amount, name: c.type }))
  }]
}))

function costSummary({ data }) {
  const sums = data.reduce((sum, row) => sum + (row.amount || 0), 0)
  return ['合计', sums.toLocaleString(), '100%']
}

onMounted(async () => {
  await filterBatches()
})

async function filterBatches() {
  loading.value = true
  const res = await mockApi.getBatches({ status: statusFilter.value })
  batchList.value = res.data.list
  loading.value = false
}

async function loadBatchData(batchId) {
  if (!batchId) { batchDetail.value = null; return }
  loading.value = true
  const [batchRes, indRes, opRes, healthRes, envRes] = await Promise.all([
    mockApi.getBatchDetail(batchId),
    mockApi.getIndividuals({ batch_id: batchId }),
    mockApi.getBreedingOperations(batchId),
    mockApi.getHealthRecords({ batch_id: batchId }),
    mockApi.getEnvironmentParams({ house_id: 1 })
  ])
  batchDetail.value = batchRes.data
  individualList.value = indRes.data.list
  operationList.value = opRes.data.list
  healthList.value = healthRes.data.list
  environmentList.value = envRes.data.list
  loading.value = false
}

function exportReport() {
  ElMessage.info('报告导出功能（PDF生成需后端支持）')
}
</script>

<style scoped>
.search-bar { margin-bottom: 0; }
.chart { width: 100%; height: 320px; }
.chart-sm { width: 100%; height: 260px; }
.kpi-sub { font-size: 12px; color: #999; }
</style>
