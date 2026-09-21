<template>
  <div class="page-container">
    <!-- 操作栏 -->
    <el-card shadow="never" class="search-bar">
      <el-row :gutter="16" align="middle">
        <el-col :span="16">
          <el-button type="primary" :icon="Plus" @click="showAddDialog = true">新增记录</el-button>
          <el-button :icon="Upload">导入Excel</el-button>
          <el-button :icon="Download" @click="exportData">导出CSV</el-button>
        </el-col>
        <el-col :span="8" style="text-align: right;">
          <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" @change="loadData" />
        </el-col>
      </el-row>
    </el-card>

    <!-- KPI卡片 -->
    <el-row :gutter="16" style="margin-top: 20px;">
      <el-col :span="6">
        <div class="kpi-card">
          <div class="kpi-label">本月收入</div>
          <div class="kpi-value text-success">{{ formatMoney(summary.total_income) }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="kpi-card">
          <div class="kpi-label">本月支出</div>
          <div class="kpi-value text-danger">{{ formatMoney(summary.total_expense) }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="kpi-card">
          <div class="kpi-label">本月净额</div>
          <div class="kpi-value" :class="summary.net_profit >= 0 ? 'text-success' : 'text-danger'">{{ formatMoney(summary.net_profit) }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="kpi-card">
          <div class="kpi-label">利润率</div>
          <div class="kpi-value">{{ summary.total_income > 0 ? ((summary.net_profit / summary.total_income) * 100).toFixed(2) : 0 }}%</div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="14">
        <el-card shadow="never">
          <template #header><span class="section-title">月度收支趋势</span></template>
          <v-chart class="chart" :option="trendChartOption" autoresize ref="trendChartRef" />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card shadow="never">
          <template #header><span class="section-title">收支科目占比</span></template>
          <v-chart class="chart" :option="pieChartOption" autoresize ref="pieChartRef" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选 + 表格 -->
    <el-card shadow="never" style="margin-top: 20px;">
      <template #header>
        <span class="section-title">收支流水</span>
        <el-row :gutter="12" style="margin-top: 12px;">
          <el-col :span="6">
            <el-select v-model="filterType" placeholder="收支类型" clearable @change="loadData">
              <el-option label="收入" :value="1" />
              <el-option label="支出" :value="2" />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-input v-model="filterKeyword" placeholder="搜索科目/对方" clearable @change="loadData" />
          </el-col>
          <el-col :span="6">
            <el-select v-model="filterBatch" placeholder="关联批次" clearable @change="loadData">
              <el-option v-for="b in batchList" :key="b.id" :label="b.batch_no" :value="b.id" />
            </el-select>
          </el-col>
        </el-row>
      </template>
      <el-table :data="filteredTransactions" size="small" v-loading="loading" max-height="450" border>
        <el-table-column prop="transaction_no" label="流水号" width="160" />
        <el-table-column prop="transaction_date" label="日期" width="110" />
        <el-table-column prop="transaction_type" label="类型" width="70">
          <template #default="{ row }">
            <el-tag :type="row.transaction_type === 1 ? 'success' : 'danger'" size="small">{{ row.transaction_type === 1 ? '收入' : '支出' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="科目" width="120" />
        <el-table-column prop="amount" label="金额(元)" width="120">
          <template #default="{ row }">
            <span :class="row.transaction_type === 1 ? 'text-success' : 'text-danger'">{{ row.transaction_type === 1 ? '+' : '-' }}{{ formatMoney(row.amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="batch_id" label="关联批次" width="140">
          <template #default="{ row }">{{ getBatchNo(row.batch_id) }}</template>
        </el-table-column>
        <el-table-column prop="payee_payer" label="对方" min-width="120" />
        <el-table-column prop="remark" label="备注" min-width="120" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="editRecord(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="deleteRecord(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination style="margin-top: 16px; justify-content: flex-end;" layout="total, prev, pager, next" :total="transactionList.length" :page-size="20" />
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="showAddDialog" :title="editingRecord ? '编辑收支记录' : '新增收支记录'" width="560px">
      <el-form :model="form" label-width="100px" :rules="formRules" ref="formRef">
        <el-form-item label="收支类型" prop="transaction_type">
          <el-radio-group v-model="form.transaction_type">
            <el-radio-button :value="1">收入</el-radio-button>
            <el-radio-button :value="2">支出</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="科目" prop="category">
          <el-input v-model="form.category" placeholder="如：饲料采购、鸡苗销售" />
        </el-form-item>
        <el-form-item label="金额" prop="amount">
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="日期" prop="transaction_date">
          <el-date-picker v-model="form.transaction_date" type="date" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="关联批次">
          <el-select v-model="form.batch_id" placeholder="选择批次" clearable style="width: 100%;">
            <el-option v-for="b in batchList" :key="b.id" :label="b.batch_no" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="对方">
          <el-input v-model="form.payee_payer" placeholder="付款方/收款方" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRecord">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { Plus, Upload, Download } from '@element-plus/icons-vue'
import { mockApi } from '@/api/mock'

use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

const dateRange = ref(null)
const filterType = ref('')
const filterKeyword = ref('')
const filterBatch = ref('')
const transactionList = ref([])
const summary = ref({ total_income: 0, total_expense: 0, net_profit: 0 })
const groupedData = ref([])
const categoryBreakdown = ref([])
const batchList = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const trendChartRef = ref(null)
const pieChartRef = ref(null)

onUnmounted(() => {
  trendChartRef.value?.dispose?.()
  pieChartRef.value?.dispose?.()
})
const editingRecord = ref(null)
const formRef = ref(null)
const form = ref({ transaction_type: 2, category: '', amount: 0, transaction_date: new Date(), batch_id: '', payee_payer: '', remark: '' })

const formRules = {
  transaction_type: [{ required: true, message: '请选择收支类型' }],
  category: [{ required: true, message: '请输入科目' }],
  amount: [{ required: true, message: '请输入金额' }],
  transaction_date: [{ required: true, message: '请选择日期' }]
}

const filteredTransactions = computed(() => {
  let list = [...transactionList.value]
  if (filterType.value) list = list.filter(t => t.transaction_type === filterType.value)
  if (filterKeyword.value) list = list.filter(t => t.category.includes(filterKeyword.value) || t.payee_payer.includes(filterKeyword.value))
  if (filterBatch.value) list = list.filter(t => t.batch_id === filterBatch.value)
  return list.sort((a, b) => b.transaction_date.localeCompare(a.transaction_date))
})

const trendChartOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
  legend: { data: ['收入', '支出', '净额'] },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: groupedData.value.map(d => d.group_key) },
  yAxis: { type: 'value', name: '金额(元)' },
  series: [
    { name: '收入', type: 'bar', data: groupedData.value.map(d => d.income.toFixed(0)), itemStyle: { color: '#67c23a' } },
    { name: '支出', type: 'bar', data: groupedData.value.map(d => d.expense.toFixed(0)), itemStyle: { color: '#f56c6c' } },
    { name: '净额', type: 'line', data: groupedData.value.map(d => d.net_profit.toFixed(0)), itemStyle: { color: '#409eff' } }
  ]
}))

const pieChartOption = computed(() => ({
  tooltip: { trigger: 'item' },
  series: [
    {
      name: '收入', type: 'pie', radius: ['30%', '50%'], center: ['25%', '50%'],
      data: categoryBreakdown.value.filter(c => c.type === 'income').map(c => ({ value: c.amount, name: c.category })),
      label: { show: false }
    },
    {
      name: '支出', type: 'pie', radius: ['30%', '50%'], center: ['75%', '50%'],
      data: categoryBreakdown.value.filter(c => c.type === 'expense').map(c => ({ value: c.amount, name: c.category })),
      label: { show: false }
    }
  ]
}))

function formatMoney(val) {
  return val ? `¥${parseFloat(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '¥0.00'
}

function getBatchNo(batchId) {
  return batchList.value.find(b => b.id === batchId)?.batch_no || '-'
}

async function loadData() {
  loading.value = true
  const params = {}
  if (dateRange.value && dateRange.value[0]) {
    params.start_date = dateRange.value[0].toISOString().slice(0, 10)
    params.end_date = dateRange.value[1].toISOString().slice(0, 10)
  }
  const res = await mockApi.getFinancialTransactions(params)
  transactionList.value = res.data.list
  summary.value = res.data.summary
  groupedData.value = res.data.grouped_data
  categoryBreakdown.value = res.data.category_breakdown
  loading.value = false
}

function editRecord(row) {
  editingRecord.value = row
  form.value = { ...row }
  showAddDialog.value = true
}

function deleteRecord(row) {
  ElMessageBox.confirm('确认删除该记录？', '提示', { type: 'warning' }).then(() => {
    transactionList.value = transactionList.value.filter(t => t.id !== row.id)
    ElMessage.success('删除成功')
  }).catch(() => {})
}

function saveRecord() {
  formRef.value?.validate(valid => {
    if (!valid) return
    if (editingRecord.value) {
      const idx = transactionList.value.findIndex(t => t.id === editingRecord.value.id)
      if (idx >= 0) transactionList.value[idx] = { ...editingRecord.value, ...form.value }
    } else {
      const newRecord = {
        id: Date.now(),
        transaction_no: `FT-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${String(transactionList.value.length + 1).padStart(3, '0')}`,
        ...form.value,
        transaction_date: form.value.transaction_date.toISOString().slice(0, 10)
      }
      transactionList.value.unshift(newRecord)
    }
    showAddDialog.value = false
    editingRecord.value = null
    form.value = { transaction_type: 2, category: '', amount: 0, transaction_date: new Date(), batch_id: '', payee_payer: '', remark: '' }
    ElMessage.success('保存成功')
  })
}

function exportData() {
  const rows = filteredTransactions.value.map(t => `${t.transaction_no},${t.transaction_date},${t.transaction_type === 1 ? '收入' : '支出'},${t.category},${t.amount},${getBatchNo(t.batch_id)},${t.payee_payer},${t.remark}`).join('\n')
  const csv = `流水号,日期,类型,科目,金额,关联批次,对方,备注\n${rows}`
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `财务流水_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  const batchRes = await mockApi.getBatches()
  batchList.value = batchRes.data.list
  await loadData()
})
</script>

<style scoped>
.search-bar { margin-bottom: 0; }
.chart { width: 100%; height: 300px; }
</style>
