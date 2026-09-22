import client from './client.js'

// Mock fallback removed — all API calls go to real backend

// ==================== 操作类型映射 ====================
const OP_TYPE_MAP = {
  1: '入栏',
  2: '出栏',
  3: '免疫',
  4: '称重',
  5: '转群',
  6: '饲喂',
  7: '清粪',
  8: '消毒',
  9: '巡检',
  10: '其他'
}

function getOperationName(opType) {
  return OP_TYPE_MAP[opType] || `操作(${opType})`
}

// ==================== API 封装 ====================

/**
 * 获取批次列表
 * GET /batches?status=&keyword=&page=1&page_size=20
 */
async function getBatches(params = {}) {

  const { status, keyword, page = 1, page_size = 20 } = params
  const query = new URLSearchParams()
  if (status !== undefined && status !== '') query.append('status', status)
  if (keyword) query.append('keyword', keyword)
  query.append('page', page)
  query.append('page_size', page_size)

  const res = await client.get(`/batches?${query.toString()}`)
  return res
}

/**
 * 获取批次详情
 * GET /batches/{batch_id}
 * 后端返回嵌套对象 breed/house，需扁平化为 breed_name/house_name
 */
async function getBatchDetail(id) {

  const res = await client.get(`/batches/${id}`)
  if (res.data && res.data.breed) {
    res.data.breed_name = res.data.breed.breed_name || res.data.breed_name
    res.data.breed_id = res.data.breed.id || res.data.breed_id
  }
  if (res.data && res.data.house) {
    res.data.house_name = res.data.house.house_name || res.data.house_name
    res.data.house_id = res.data.house.id || res.data.house_id
  }
  return res
}

/**
 * 获取个体列表
 * GET /individuals?batch_id=&keyword=&page=1&page_size=20
 */
async function getIndividuals(params = {}) {

  const { batch_id, keyword, page = 1, page_size = 20 } = params
  const query = new URLSearchParams()
  if (batch_id !== undefined && batch_id !== '') query.append('batch_id', batch_id)
  if (keyword) query.append('keyword', keyword)
  query.append('page', page)
  query.append('page_size', page_size)

  const res = await client.get(`/individuals?${query.toString()}`)
  return res
}

/**
 * 获取个体详情
 * GET /individuals/{id}
 */
async function getIndividualDetail(id) {

  const res = await client.get(`/individuals/${id}`)
  return res.data
}

/**
 * 获取养殖操作记录
 * GET /batches/{id}/operations
 */
async function getBreedingOperations(batchId) {

  const res = await client.get(`/batches/${batchId}/operations`)
  return res.data
}

/**
 * 获取健康记录
 * GET /health/records?batch_id=&page=1&page_size=20
 */
async function getHealthRecords(params = {}) {

  const { batch_id, record_type, page = 1, page_size = 20 } = params
  const query = new URLSearchParams()
  if (batch_id !== undefined && batch_id !== '') query.append('batch_id', batch_id)
  if (record_type !== undefined && record_type !== '') query.append('record_type', record_type)
  query.append('page', page)
  query.append('page_size', page_size)

  const res = await client.get(`/health/records?${query.toString()}`)
  return res
}

/**
 * 获取环境参数
 * GET /environment/records?house_id=&page=1&page_size=20
 * 字段映射：record_time -> record_date
 */
async function getEnvironmentParams(params = {}) {

  const { house_id, page = 1, page_size = 100 } = params
  const query = new URLSearchParams()
  if (house_id !== undefined && house_id !== '') query.append('house_id', house_id)
  query.append('page', page)
  query.append('page_size', page_size)

  const res = await client.get(`/environment/records?${query.toString()}`)
  const list = Array.isArray(res.data)
    ? res.data
    : res.data?.list || []

  const mappedList = list.map(item => ({
    ...item,
    record_date: item.record_time ? item.record_time.slice(0, 10) : item.record_date
  }))

  return {
    code: 0,
    data: {
      list: mappedList,
      pagination: res.pagination || res.data?.pagination
    }
  }
}

/**
 * 获取生长曲线
 * GET /individuals/{animal_id}/growth-curve
 * 映射：growth_data -> records, standard_curve -> std_curve
 * standard_curve 字段 weight -> std_weight
 */
async function getGrowthCurve(params = {}) {

  const { animal_id, batch_id } = params
  let data = { records: [], std_curve: [] }

  if (animal_id) {
    const res = await client.get(`/individuals/${animal_id}/growth-curve`)
    const backendData = res.data || {}

    data.records = (backendData.growth_data || []).map(r => ({
      id: r.id,
      animal_id,
      batch_id: r.batch_id || batch_id,
      record_date: r.record_date,
      age_days: r.age_days,
      weight: r.weight,
      body_length: r.body_length,
      chest_girth: r.chest_girth,
      shank_length: r.shank_length,
      recorder: r.recorder
    }))

    data.std_curve = (backendData.standard_curve || []).map(s => ({
      age_days: s.age_days,
      std_weight: s.weight
    }))
  } else if (batch_id) {
    // 按批次查询时，后端若无此接口则留空（或由组件处理）
    data = { records: [], std_curve: [] }
  }

  return { code: 0, data }
}

/**
 * 用户登录
 * POST /auth/login
 */
async function login(credentials) {
  const resp = await client.post('/auth/login', credentials)
  if (resp.code !== 0) {
    throw new Error(resp.message || '登录失败')
  }
  return resp.data
}

/**
 * 获取批次生长汇总
 * GET /batches/{batch_id}/growth-summary
 * 映射：sample_size -> count, avg_weight -> avg, min_weight -> min, max_weight -> max, std_weight -> std
 * q1 / median / q3 后端无，补 null
 */
async function getBatchGrowthSummary(batchId) {

  const res = await client.get(`/batches/${batchId}/growth-summary`)
  const d = res.data || {}

  return {
    code: 0,
    data: {
      count: d.sample_size ?? 0,
      avg: d.avg_weight ?? 0,
      min: d.min_weight ?? 0,
      max: d.max_weight ?? 0,
      q1: null,
      median: null,
      q3: null,
      std: d.std_weight ?? 0
    }
  }
}

// ==================== Phase 3 新增 API ====================

/**
 * 获取批次性能偏差数据
 * GET /performance/deviation?batch_id=&page=&page_size=
 * 后端返回分析记录列表，映射为前端期望的汇总格式
 */
async function getBatchPerformance(batchId) {

  const res = await client.get(`/performance/deviation?batch_id=${batchId}&page=1&page_size=100`)
  const list = res.data?.list || []
  if (list.length === 0) {
    return { code: 0, data: null }
  }

  // 按日期排序生成趋势数据
  const sorted = [...list].sort((a, b) => new Date(a.analysis_date) - new Date(b.analysis_date))
  const trend = sorted.map(r => ({
    date: r.analysis_date,
    survival_dev: r.survival_deviation_pct,
    adg_dev: r.daily_gain_deviation_pct,
    fmr_dev: r.fmr_deviation_pct
  }))

  // 最新记录作为当前性能汇总
  const latest = list[0]
  const data = {
    batch_id: latest.batch_id,
    batch_no: latest.batch_no,
    survival: {
      actual: latest.actual_survival_rate,
      standard: latest.target_survival_rate,
      deviation: parseFloat((latest.actual_survival_rate - latest.target_survival_rate).toFixed(2)),
      deviation_pct: latest.survival_deviation_pct
    },
    adg: {
      actual: latest.actual_daily_gain,
      standard: latest.target_daily_gain,
      deviation: parseFloat((latest.actual_daily_gain - latest.target_daily_gain).toFixed(2)),
      deviation_pct: latest.daily_gain_deviation_pct
    },
    fmr: {
      actual: latest.actual_feed_meat_ratio,
      standard: latest.target_feed_meat_ratio,
      deviation: parseFloat((latest.actual_feed_meat_ratio - latest.target_feed_meat_ratio).toFixed(3)),
      deviation_pct: latest.fmr_deviation_pct
    },
    trend
  }

  return { code: 0, data }
}

/**
 * 获取中试项目列表
 * GET /pilots
 */
async function getPilotProjects() {

  const res = await client.get('/pilots?page=1&page_size=100')
  return res
}

/**
 * 获取中试项目对比详情
 * 组合 /pilots/{id} 和 /pilots/{id}/comparison
 */
async function getPilotComparison(projectId) {

  const [projectRes, comparisonRes] = await Promise.all([
    client.get(`/pilots/${projectId}`),
    client.get(`/pilots/${projectId}/comparison`)
  ])

  const project = projectRes.data || {}
  const comp = comparisonRes.data || {}

  // 计算项目进度
  let progress_pct = 0
  if (project.start_date && project.end_date) {
    const total = new Date(project.end_date) - new Date(project.start_date)
    const passed = Date.now() - new Date(project.start_date).getTime()
    progress_pct = total > 0 ? Math.min(100, Math.round(passed / total * 100)) : (project.status === 1 ? 50 : 100)
  }

  // 映射指标对比
  const indicators = (comp.comparison || []).map(c => ({
    indicator_name: c.indicator_name,
    experimental_value: c.experiment_avg,
    control_value: c.control_avg,
    unit: '',
    diff: c.difference,
    diff_pct: c.difference_pct
  }))

  // 映射生长曲线
  const experimental_growth = (comp.growth_curve?.experiment || []).map(g => ({
    age_days: g.age_days,
    weight: g.weight
  }))
  const control_growth = (comp.growth_curve?.control || []).map(g => ({
    age_days: g.age_days,
    weight: g.weight
  }))

  // 实验组/对照组批次
  const expBatch = project.experiment_batches?.[0] || null
  const ctlBatch = project.control_batches?.[0] || null

  const data = {
    project: {
      id: project.id,
      project_name: project.project_name,
      start_date: project.start_date,
      end_date: project.end_date,
      status: project.status,
      responsible_person: project.principal,
      description: project.description
    },
    progress_pct,
    indicators,
    experimental_growth,
    control_growth,
    experimental_batch: expBatch ? { batch_no: expBatch.batch_no, batch_name: expBatch.breed_name } : null,
    control_batch: ctlBatch ? { batch_no: ctlBatch.batch_no, batch_name: ctlBatch.breed_name } : null
  }

  return { code: 0, data }
}

/**
 * 获取财务收支记录
 * GET /financial-transactions
 * 同时请求 /financial-transactions/summary 获取分组数据
 */
async function getFinancialTransactions(params = {}) {

  const { start_date, end_date, transaction_type, batch_id, keyword } = params
  const query = new URLSearchParams()
  if (start_date) query.append('start_date', start_date)
  if (end_date) query.append('end_date', end_date)
  if (transaction_type !== undefined && transaction_type !== '') query.append('transaction_type', transaction_type)
  if (batch_id !== undefined && batch_id !== '') query.append('batch_id', batch_id)
  if (keyword) query.append('keyword', keyword)
  query.append('page', '1')
  query.append('page_size', '100')

  const listQuery = query.toString()
  const summaryQuery = listQuery ? `${listQuery}&group_by=month` : 'group_by=month'

  const [listRes, summaryRes] = await Promise.all([
    client.get(`/financial-transactions?${listQuery}`),
    client.get(`/financial-transactions/summary?${summaryQuery}`)
  ])

  const list = listRes.data?.list || []
  const summary = listRes.data?.summary || { total_income: 0, total_expense: 0, net_profit: 0 }
  const grouped_data = summaryRes.data?.grouped_data || []
  const category_breakdown = summaryRes.data?.category_breakdown || []

  return {
    code: 0,
    data: {
      summary,
      list,
      grouped_data,
      category_breakdown,
      pagination: listRes.data?.pagination
    }
  }
}

/**
 * 创建收支记录
 * POST /financial-transactions
 */
async function createTransaction(data) {

  const res = await client.post('/financial-transactions', data)
  return res
}

/**
 * 获取利润排行榜
 * GET /profit/ranking
 */
async function getProfitRanking(params = {}) {

  const { sort_by = 'profit_margin' } = params
  const res = await client.get(`/profit/ranking?sort_by=${sort_by}&page=1&page_size=100`)
  return res
}

/**
 * 溯源码查询
 * GET /traceability/{code}
 */
async function getTraceability(code) {

  const res = await client.get(`/traceability/${encodeURIComponent(code)}`)
  return res
}

/**
 * 获取库存列表
 * GET /inventory
 */
async function getInventory(params = {}) {

  const { item_category, status, keyword } = params
  const query = new URLSearchParams()
  if (item_category !== undefined && item_category !== '') query.append('item_category', item_category)
  if (status !== undefined && status !== '') query.append('status', status)
  if (keyword) query.append('keyword', keyword)
  query.append('page', '1')
  query.append('page_size', '100')

  const res = await client.get(`/inventory?${query.toString()}`)
  return res
}

/**
 * 创建库存流水（出入库）
 * POST /inventory/{inventory_id}/transactions
 */
async function createInventoryTransaction(data) {

  const { inventory_id, trans_type, quantity, remark } = data
  const res = await client.post(`/inventory/${inventory_id}/transactions`, {
    trans_type,
    quantity,
    remark
  })
  return res
}

/**
 * 获取库存流水
 * GET /inventory/{inventory_id}/transactions
 */
async function getInventoryTransactions(inventoryId) {

  const res = await client.get(`/inventory/${inventoryId}/transactions?page=1&page_size=100`)
  return res
}

// ==================== 统一导出 ====================
const api = {
  login,
  getBatches,
  getBatchDetail,
  getIndividuals,
  getIndividualDetail,
  getBreedingOperations,
  getHealthRecords,
  getEnvironmentParams,
  getGrowthCurve,
  getBatchGrowthSummary,
  // Phase 3
  getBatchPerformance,
  getPilotProjects,
  getPilotComparison,
  getFinancialTransactions,
  createTransaction,
  getProfitRanking,
  getTraceability,
  getInventory,
  createInventoryTransaction,
  getInventoryTransactions
}

export default api
