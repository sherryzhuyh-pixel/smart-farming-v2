<template>
  <div class="page-container">
    <!-- 项目选择 -->
    <el-card shadow="never" class="search-bar">
      <el-row :gutter="16" align="middle">
        <el-col :span="8">
          <el-select v-model="selectedProject" placeholder="选择中试项目" style="width: 100%;" @change="loadProjectData">
            <el-option v-for="p in projectList" :key="p.id" :label="p.project_name" :value="p.id" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-tag v-if="projectData?.project" :type="projectData.project.status === 1 ? 'success' : 'info'" size="large">
            {{ projectData.project.status === 1 ? '进行中' : '已完成' }}
          </el-tag>
        </el-col>
        <el-col :span="8" style="text-align: right;">
          <el-button type="primary" :icon="Document" @click="generateReport">生成报告</el-button>
        </el-col>
      </el-row>
    </el-card>

    <div v-if="!projectData" class="empty-state">
      <el-icon size="64"><Stopwatch /></el-icon>
      <p>请选择中试项目查看效果对比</p>
    </div>

    <template v-else>
      <!-- 项目信息 + 进度 -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="12">
          <el-card shadow="never">
            <template #header><span class="section-title">项目信息</span></template>
            <div class="info-item"><label>项目名称：</label>{{ projectData.project.project_name }}</div>
            <div class="info-item"><label>起止日期：</label>{{ projectData.project.start_date }} 至 {{ projectData.project.end_date }}</div>
            <div class="info-item"><label>负责人：</label>{{ projectData.project.responsible_person }}</div>
            <div class="info-item"><label>项目描述：</label>{{ projectData.project.description }}</div>
            <div class="info-item"><label>实验组批次：</label>{{ projectData.experimental_batch?.batch_no }} ({{ projectData.experimental_batch?.batch_name }})</div>
            <div class="info-item"><label>对照组批次：</label>{{ projectData.control_batch?.batch_no }} ({{ projectData.control_batch?.batch_name }})</div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="never">
            <template #header><span class="section-title">项目进度</span></template>
            <el-progress :percentage="projectData.progress_pct" :stroke-width="24" :status="projectData.progress_pct >= 100 ? 'success' : ''" />
            <div style="margin-top: 16px; display: flex; justify-content: space-around;">
              <div class="progress-node" :class="{ active: projectData.progress_pct >= 20 }">
                <el-icon size="24"><CircleCheck /></el-icon>
                <div>方案设计</div>
              </div>
              <div class="progress-node" :class="{ active: projectData.progress_pct >= 40 }">
                <el-icon size="24"><CircleCheck /></el-icon>
                <div>入栏分组</div>
              </div>
              <div class="progress-node" :class="{ active: projectData.progress_pct >= 60 }">
                <el-icon size="24"><CircleCheck /></el-icon>
                <div>中期评估</div>
              </div>
              <div class="progress-node" :class="{ active: projectData.progress_pct >= 80 }">
                <el-icon size="24"><CircleCheck /></el-icon>
                <div>数据采集</div>
              </div>
              <div class="progress-node" :class="{ active: projectData.progress_pct >= 100 }">
                <el-icon size="24"><CircleCheck /></el-icon>
                <div>报告生成</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 核心指标对比表 -->
      <el-card shadow="never" style="margin-top: 20px;">
        <template #header><span class="section-title">核心指标对比</span></template>
        <el-table :data="projectData.indicators" size="small" border>
          <el-table-column prop="indicator_name" label="指标名称" min-width="120" />
          <el-table-column prop="experimental_value" label="实验组">
            <template #default="{ row }">{{ row.experimental_value }} {{ row.unit }}</template>
          </el-table-column>
          <el-table-column prop="control_value" label="对照组">
            <template #default="{ row }">{{ row.control_value }} {{ row.unit }}</template>
          </el-table-column>
          <el-table-column prop="diff" label="差异">
            <template #default="{ row }">
              <span :class="row.diff >= 0 ? 'text-success' : 'text-danger'">{{ row.diff >= 0 ? '+' : '' }}{{ row.diff }} {{ row.unit }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="diff_pct" label="差异率">
            <template #default="{ row }">
              <el-tag :type="row.diff_pct >= 0 ? 'success' : 'danger'" size="small">{{ row.diff_pct >= 0 ? '+' : '' }}{{ row.diff_pct }}%</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 生长曲线对比 -->
      <el-card shadow="never" style="margin-top: 20px;">
        <template #header><span class="section-title">生长曲线对比</span></template>
        <v-chart class="chart" :option="growthCompareOption" autoresize ref="growthChartRef" />
      </el-card>

      <!-- 功能性指标 -->
      <el-card shadow="never" style="margin-top: 20px;" v-if="functionalIndicators.length > 0">
        <template #header><span class="section-title">功能性指标</span></template>
        <el-row :gutter="20">
          <el-col :span="8" v-for="ind in functionalIndicators" :key="ind.id">
            <div class="functional-card">
              <div class="func-name">{{ ind.indicator_name }}</div>
              <div class="func-compare">
                <div class="func-group experimental">
                  <div class="func-label">实验组</div>
                  <div class="func-value">{{ ind.experimental_value }}{{ ind.unit }}</div>
                </div>
                <div class="func-arrow">
                  <el-icon size="20" :color="ind.diff >= 0 ? '#67c23a' : '#f56c6c'"><Top v-if="ind.diff >= 0" /><Bottom v-else /></el-icon>
                  <div :class="ind.diff >= 0 ? 'text-success' : 'text-danger'">{{ ind.diff_pct }}%</div>
                </div>
                <div class="func-group control">
                  <div class="func-label">对照组</div>
                  <div class="func-value">{{ ind.control_value }}{{ ind.unit }}</div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { Document, Stopwatch, CircleCheck, Top, Bottom } from '@element-plus/icons-vue'
import { mockApi } from '@/api/mock'

use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

const selectedProject = ref('')
const projectList = ref([])
const projectData = ref(null)
const growthChartRef = ref(null)

onUnmounted(() => {
  growthChartRef.value?.dispose?.()
})

const functionalIndicators = computed(() => {
  return projectData.value?.indicators?.filter(i => ['硒含量'].includes(i.indicator_name)) || []
})

const growthCompareOption = computed(() => {
  if (!projectData.value) return {}
  const exp = projectData.value.experimental_growth || []
  const ctl = projectData.value.control_growth || []
  const ages = [...new Set([...exp.map(e => e.age_days), ...ctl.map(c => c.age_days)])].sort((a, b) => a - b)

  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['实验组', '对照组'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', name: '日龄(天)', data: ages.map(a => `${a}天`) },
    yAxis: { type: 'value', name: '体重(g)' },
    series: [
      { name: '实验组', type: 'line', smooth: true, data: ages.map(a => exp.find(e => e.age_days === a)?.weight || null), itemStyle: { color: '#409eff' }, areaStyle: { opacity: 0.1 } },
      { name: '对照组', type: 'line', smooth: true, data: ages.map(a => ctl.find(c => c.age_days === a)?.weight || null), itemStyle: { color: '#909399' }, lineStyle: { type: 'dashed' } }
    ]
  }
})

async function loadProjectData(projectId) {
  if (!projectId) { projectData.value = null; return }
  const res = await mockApi.getPilotComparison(projectId)
  projectData.value = res.data
}

function generateReport() {
  ElMessage.info('报告生成功能（PDF导出需后端支持）')
}

onMounted(async () => {
  const res = await mockApi.getPilotProjects()
  projectList.value = res.data.list
  if (projectList.value.length > 0) {
    selectedProject.value = projectList.value[0].id
    await loadProjectData(selectedProject.value)
  }
})
</script>

<style scoped>
.search-bar { margin-bottom: 0; }
.info-item { padding: 6px 0; font-size: 14px; }
.info-item label { color: var(--text-secondary); display: inline-block; width: 100px; }
.chart { width: 100%; height: 380px; }
.progress-node { text-align: center; color: #ccc; }
.progress-node.active { color: #409eff; }
.progress-node .el-icon { margin-bottom: 4px; }
.functional-card { background: #f5f7fa; border-radius: 8px; padding: 16px; text-align: center; }
.func-name { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
.func-compare { display: flex; align-items: center; justify-content: space-between; }
.func-group { flex: 1; }
.func-label { font-size: 12px; color: #999; margin-bottom: 4px; }
.func-value { font-size: 20px; font-weight: 600; }
.func-group.experimental .func-value { color: #409eff; }
.func-group.control .func-value { color: #909399; }
.func-arrow { text-align: center; padding: 0 12px; }
</style>
