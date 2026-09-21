<template>
  <div class="page-container">
    <!-- 查询区 -->
    <el-card shadow="never" class="search-bar">
      <el-row :gutter="16" align="middle" justify="center">
        <el-col :span="12">
          <el-input v-model="traceCode" placeholder="输入溯源码或扫描耳标二维码" size="large" clearable @keyup.enter="handleQuery">
            <template #append>
              <el-button :icon="Search" type="primary" @click="handleQuery">查询</el-button>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-button size="large" :icon="FullScreen" @click="handleScan">模拟扫码</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 空状态 -->
    <div v-if="!traceData && !querying" class="empty-state">
      <el-icon size="80" color="#dcdfe6"><Search /></el-icon>
      <h3>输入溯源码查询全链路信息</h3>
      <p style="color: #909399;">支持手动输入或扫描二维码</p>
    </div>

    <!-- 查询结果 -->
    <template v-if="traceData">
      <!-- 头部信息 -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="16">
          <el-card shadow="never">
            <template #header>
              <span class="section-title">溯源信息</span>
              <el-tag type="success" style="margin-left: 12px;">{{ traceData.traceability_code }}</el-tag>
            </template>
            <el-descriptions :column="3" border>
              <el-descriptions-item label="个体编号">{{ traceData.animal?.animal_no }}</el-descriptions-item>
              <el-descriptions-item label="品种">{{ traceData.animal?.breed_name }}</el-descriptions-item>
              <el-descriptions-item label="性别">{{ traceData.animal?.gender_text }}</el-descriptions-item>
              <el-descriptions-item label="批次">{{ traceData.batch?.batch_no }}</el-descriptions-item>
              <el-descriptions-item label="鸡舍">{{ traceData.batch?.house_name }}</el-descriptions-item>
              <el-descriptions-item label="负责人">{{ traceData.batch?.responsible_person }}</el-descriptions-item>
              <el-descriptions-item label="入栏日期">{{ traceData.animal?.date_in }}</el-descriptions-item>
              <el-descriptions-item label="溯源完整度" :span="2">
                <el-progress :percentage="parseFloat(traceData.completeness?.completeness_pct)" :status="parseFloat(traceData.completeness?.completeness_pct) >= 80 ? 'success' : 'warning'" />
                {{ traceData.completeness?.covered_stages }}/{{ traceData.completeness?.total_stages }} 节点
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="never">
            <template #header><span class="section-title">完整度评分</span></template>
            <div style="text-align: center; padding: 20px;">
              <el-progress type="dashboard" :percentage="parseFloat(traceData.completeness?.completeness_pct)" :status="parseFloat(traceData.completeness?.completeness_pct) >= 80 ? 'success' : 'warning'" />
              <div style="margin-top: 12px; font-size: 14px; color: #666;">
                已覆盖 {{ traceData.completeness?.covered_stages }} 个阶段
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 时间线 -->
      <el-card shadow="never" style="margin-top: 20px;">
        <template #header><span class="section-title">全链路时间线</span></template>
        <el-timeline>
          <el-timeline-item
            v-for="(node, idx) in traceData.chain"
            :key="idx"
            :type="getNodeType(node.stage)"
            :icon="getNodeIcon(node.stage)"
            :timestamp="node.event_date"
            placement="top"
          >
            <el-card shadow="hover" style="max-width: 600px;">
              <div style="display: flex; align-items: center; gap: 12px;">
                <el-tag :type="getNodeType(node.stage)" size="small">{{ node.stage_text }}</el-tag>
                <h4 style="margin: 0;">{{ node.event_desc }}</h4>
              </div>
              <div style="margin-top: 8px; color: #666; font-size: 13px;">
                <span><el-icon><Location /></el-icon> {{ node.location }}</span>
                <span style="margin-left: 16px;"><el-icon><User /></el-icon> {{ node.operator }}</span>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </el-card>

      <!-- 操作按钮 -->
      <el-row justify="center" style="margin-top: 20px; margin-bottom: 40px;">
        <el-button type="primary" :icon="Share" size="large">分享溯源报告</el-button>
        <el-button :icon="Printer" size="large" style="margin-left: 16px;">打印</el-button>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search, FullScreen, Location, User, Share, Printer } from '@element-plus/icons-vue'
import { mockApi } from '@/api/mock'

const traceCode = ref('')
const traceData = ref(null)
const querying = ref(false)

const nodeTypeMap = {
  1: 'info', 2: 'info', 3: 'warning', 4: 'success', 5: 'primary', 6: 'success', 7: 'danger'
}

const nodeIconMap = {
  1: 'Chicken', 2: 'Egg', 3: 'Clock', 4: 'HomeFilled', 5: 'FirstAidKit', 6: 'Check', 7: 'Sell'
}

function getNodeType(stage) {
  return nodeTypeMap[stage] || 'info'
}

function getNodeIcon(stage) {
  return nodeIconMap[stage] || 'InfoFilled'
}

async function handleQuery() {
  if (!traceCode.value.trim()) {
    ElMessage.warning('请输入溯源码')
    return
  }
  querying.value = true
  traceData.value = null
  try {
    const res = await mockApi.getTraceability(traceCode.value.trim())
    if (res.code === 0) {
      traceData.value = res.data
    } else {
      ElMessage.error(res.message || '未找到该溯源码')
    }
  } catch (e) {
    ElMessage.error('查询失败')
  }
  querying.value = false
}

function handleScan() {
  // 模拟扫码，随机选择一个溯源码
  const codes = [
    'TR-20260315-AA-001-00001',
    'TR-20260315-AA-001-00002',
    'TR-20260315-AA-001-00003'
  ]
  traceCode.value = codes[Math.floor(Math.random() * codes.length)]
  handleQuery()
}
</script>

<style scoped>
.search-bar { margin-bottom: 0; }
.search-bar :deep(.el-input__wrapper) { padding-left: 16px; }
</style>
