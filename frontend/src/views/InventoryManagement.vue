<template>
  <div class="page-container">
    <!-- 操作栏 -->
    <el-card shadow="never" class="search-bar">
      <el-row :gutter="16" align="middle">
        <el-col :span="12">
          <el-button type="primary" :icon="Plus" @click="openInDialog">入库</el-button>
          <el-button type="warning" :icon="Minus" @click="openOutDialog">出库</el-button>
          <el-button :icon="Document">盘点</el-button>
          <el-button :icon="Download">导出</el-button>
        </el-col>
        <el-col :span="12">
          <el-row :gutter="8">
            <el-col :span="8">
              <el-select v-model="filterCategory" placeholder="类别" clearable @change="loadData">
                <el-option label="饲料" :value="1" />
                <el-option label="药品" :value="2" />
                <el-option label="疫苗" :value="3" />
                <el-option label="设备" :value="4" />
              </el-select>
            </el-col>
            <el-col :span="8">
              <el-select v-model="filterStatus" placeholder="状态" clearable @change="loadData">
                <el-option label="正常" :value="1" />
                <el-option label="临期" :value="2" />
                <el-option label="过期" :value="3" />
              </el-select>
            </el-col>
            <el-col :span="8">
              <el-input v-model="filterKeyword" placeholder="搜索物料" clearable @change="loadData">
                <template #append><el-button :icon="Search" @click="loadData" /></template>
              </el-input>
            </el-col>
          </el-row>
        </el-col>
      </el-row>
    </el-card>

    <!-- KPI卡片 -->
    <el-row :gutter="16" style="margin-top: 20px;">
      <el-col :span="6">
        <div class="kpi-card">
          <div class="kpi-label">物料种类</div>
          <div class="kpi-value">{{ summary.total_items }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="kpi-card">
          <div class="kpi-label">预警物料</div>
          <div class="kpi-value text-danger">{{ summary.low_stock_count }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="kpi-card">
          <div class="kpi-label">临期物料</div>
          <div class="kpi-value text-warning">{{ summary.near_expiry_count }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="kpi-card">
          <div class="kpi-label">总库存金额</div>
          <div class="kpi-value">¥{{ totalValue.toLocaleString() }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 库存表格 -->
    <el-card shadow="never" style="margin-top: 20px;">
      <template #header><span class="section-title">库存列表</span></template>
      <el-table :data="inventoryList" size="small" v-loading="loading" border @row-click="showTransactions">
        <el-table-column prop="item_code" label="物料编码" width="120" />
        <el-table-column prop="item_name" label="物料名称" min-width="160" />
        <el-table-column prop="item_category" label="类别" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="categoryType(row.item_category)">{{ categoryText(row.item_category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="当前库存" width="110">
          <template #default="{ row }">
            <span :class="row.quantity < row.safety_stock ? 'text-danger' : ''">{{ row.quantity.toLocaleString() }} {{ row.unit }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="safety_stock" label="安全库存" width="100">
          <template #default="{ row }">{{ row.safety_stock?.toLocaleString() }} {{ row.unit }}</template>
        </el-table-column>
        <el-table-column prop="storage_location" label="存放位置" min-width="140" />
        <el-table-column prop="expiry_date" label="有效期" width="110">
          <template #default="{ row }">
            <span :class="getExpiryClass(row.expiry_date)">{{ row.expiry_date }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="showTransactions(row)">流水</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 出入库弹窗 -->
    <el-dialog v-model="showInOutDialog" :title="inOutType === 1 ? '入库操作' : '出库操作'" width="480px">
      <el-form :model="inOutForm" label-width="100px">
        <el-form-item label="物料">
          <el-select v-model="inOutForm.inventory_id" placeholder="选择物料" style="width: 100%;">
            <el-option v-for="item in inventoryList" :key="item.id" :label="`${item.item_code} - ${item.item_name}`" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="inOutForm.quantity" :min="1" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="inOutForm.remark" type="textarea" rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showInOutDialog = false">取消</el-button>
        <el-button type="primary" @click="submitInOut">确认</el-button>
      </template>
    </el-dialog>

    <!-- 流水抽屉 -->
    <el-drawer v-model="showTransDrawer" :title="`${currentItem?.item_name || ''} - 出入库流水`" size="500px">
      <el-timeline>
        <el-timeline-item
          v-for="t in transactionList"
          :key="t.id"
          :type="t.trans_type === 1 ? 'success' : 'danger'"
          :timestamp="t.trans_date"
        >
          <el-card shadow="never" size="small">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div>
                <el-tag :type="t.trans_type === 1 ? 'success' : 'danger'" size="small">{{ t.trans_type === 1 ? '入库' : '出库' }}</el-tag>
                <span style="margin-left: 8px; font-weight: 600;">{{ Math.abs(t.quantity) }} {{ currentItem?.unit }}</span>
              </div>
              <div style="color: #666; font-size: 13px;">余额: {{ t.balance }}</div>
            </div>
            <div style="margin-top: 8px; color: #999; font-size: 12px;">
              操作人：{{ t.operator }} | {{ t.remark }}
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
      <div v-if="transactionList.length === 0" class="empty-state">
        <p>暂无流水记录</p>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Plus, Minus, Document, Download, Search } from '@element-plus/icons-vue'
import { mockApi } from '@/api/mock'

const filterCategory = ref('')
const filterStatus = ref('')
const filterKeyword = ref('')
const inventoryList = ref([])
const summary = ref({ total_items: 0, low_stock_count: 0, near_expiry_count: 0 })
const loading = ref(false)
const showInOutDialog = ref(false)
const inOutType = ref(1)
const inOutForm = ref({ inventory_id: '', quantity: 1, remark: '' })
const showTransDrawer = ref(false)
const currentItem = ref(null)
const transactionList = ref([])

const totalValue = computed(() => {
  return inventoryList.value.reduce((sum, item) => sum + (item.quantity * 10), 0)
})

const categoryMap = { 1: '饲料', 2: '药品', 3: '疫苗', 4: '设备', 5: '种鸡', 6: '其他' }
const statusMap = { 1: '正常', 2: '临期', 3: '过期', 4: '冻结' }

function categoryText(cat) { return categoryMap[cat] || '其他' }
function categoryType(cat) {
  const map = { 1: 'success', 2: 'danger', 3: 'warning', 4: 'info' }
  return map[cat] || ''
}
function statusText(status) { return statusMap[status] || '未知' }
function statusType(status) {
  const map = { 1: 'success', 2: 'warning', 3: 'danger', 4: 'info' }
  return map[status] || ''
}

function getExpiryClass(expiryDate) {
  const days = Math.ceil((new Date(expiryDate) - new Date()) / 86400000)
  if (days < 0) return 'text-danger'
  if (days <= 30) return 'text-warning'
  return ''
}

async function loadData() {
  loading.value = true
  const params = {}
  if (filterCategory.value) params.item_category = filterCategory.value
  if (filterStatus.value) params.status = filterStatus.value
  if (filterKeyword.value) params.keyword = filterKeyword.value
  const res = await mockApi.getInventory(params)
  inventoryList.value = res.data.list
  summary.value = res.data.summary
  loading.value = false
}

function openInDialog() {
  inOutType.value = 1
  inOutForm.value = { inventory_id: '', quantity: 1, remark: '' }
  showInOutDialog.value = true
}

function openOutDialog() {
  inOutType.value = 2
  inOutForm.value = { inventory_id: '', quantity: 1, remark: '' }
  showInOutDialog.value = true
}

async function submitInOut() {
  if (!inOutForm.value.inventory_id) {
    ElMessage.warning('请选择物料')
    return
  }
  const qty = inOutType.value === 1 ? inOutForm.value.quantity : -inOutForm.value.quantity
  await mockApi.createInventoryTransaction({
    inventory_id: inOutForm.value.inventory_id,
    trans_type: inOutType.value,
    quantity: qty,
    remark: inOutForm.value.remark
  })
  showInOutDialog.value = false
  await loadData()
  ElMessage.success(inOutType.value === 1 ? '入库成功' : '出库成功')
}

async function showTransactions(row) {
  currentItem.value = row
  const res = await mockApi.getInventoryTransactions(row.id)
  transactionList.value = res.data.list
  showTransDrawer.value = true
}

onMounted(loadData)
</script>

<style scoped>
.search-bar { margin-bottom: 0; }
</style>
