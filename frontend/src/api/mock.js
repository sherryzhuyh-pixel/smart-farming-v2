// Mock API 数据层 - 模拟 /api/v2 后端响应

const delay = (ms = 300) => new Promise(r => setTimeout(r, ms))

// ==================== 基础数据 ====================
const breeds = [
  { id: 1, breed_code: 'AA+', breed_name: 'AA+白羽肉鸡父母代', daily_gain_std: 45.5, survival_rate_std: 95.0, feed_meat_ratio: 1.85 },
  { id: 2, breed_code: 'ROSS308', breed_name: 'ROSS308白羽肉鸡', daily_gain_std: 48.2, survival_rate_std: 94.5, feed_meat_ratio: 1.78 },
]

const batches = [
  { id: 2001, batch_no: 'BT-20260315-AA-001', batch_name: 'A区育雏批次-001', breed_id: 1, house_id: 1, quantity_initial: 10000, quantity_current: 9850, date_in: '2026-03-15', date_out: '2026-09-15', age_day_in: 1, status: 1, responsible_person: '张技术员', pilot_flag: 0 },
  { id: 2002, batch_no: 'BT-20260320-AA-002', batch_name: 'A区育雏批次-002', breed_id: 1, house_id: 2, quantity_initial: 8000, quantity_current: 7800, date_in: '2026-03-20', date_out: '2026-09-20', age_day_in: 1, status: 1, responsible_person: '李技术员', pilot_flag: 0 },
  { id: 2003, batch_no: 'BT-20260401-ROSS-001', batch_name: 'B区中试批次-001', breed_id: 2, house_id: 3, quantity_initial: 5000, quantity_current: 4900, date_in: '2026-04-01', date_out: '2026-10-01', age_day_in: 1, status: 1, responsible_person: '王技术员', pilot_flag: 1, pilot_project_id: 1001 },
  { id: 2004, batch_no: 'BT-20260110-AA-003', batch_name: 'A区已出栏批次-001', breed_id: 1, house_id: 1, quantity_initial: 12000, quantity_current: 0, date_in: '2026-01-10', date_out: '2026-07-10', age_day_in: 1, status: 2, responsible_person: '张技术员', pilot_flag: 0 },
]

const houses = [
  { id: 1, house_code: 'A-01', house_name: 'A区育雏舍1号', house_type: 1, capacity: 12000 },
  { id: 2, house_code: 'A-02', house_name: 'A区育雏舍2号', house_type: 1, capacity: 10000 },
  { id: 3, house_code: 'B-01', house_name: 'B区中试舍1号', house_type: 2, capacity: 6000 },
]

// ==================== 个体与生长数据 ====================
function generateGrowthRecords(animalId, batchId, baseWeight, count = 10) {
  const records = []
  let weight = baseWeight
  for (let i = 0; i < count; i++) {
    const age = (i + 1) * 7
    weight += 45 + Math.random() * 20 - 10
    records.push({
      id: 100000 + animalId * 100 + i,
      animal_id: animalId,
      batch_id: batchId,
      record_date: `2026-03-${15 + age}`,
      age_days: age,
      weight: parseFloat(weight.toFixed(1)),
      body_length: 10 + age * 0.3 + Math.random() * 2,
      chest_girth: 8 + age * 0.25 + Math.random() * 1.5,
      shank_length: 3 + age * 0.08 + Math.random() * 0.5,
      recorder: ['张技术员', '李技术员', '王技术员'][Math.floor(Math.random() * 3)]
    })
  }
  return records
}

const individuals = []
for (let i = 1; i <= 20; i++) {
  const batchId = i <= 10 ? 2001 : 2002
  individuals.push({
    id: 3000 + i,
    animal_no: `ET-20260315-${String(i).padStart(5, '0')}`,
    batch_id: batchId,
    house_id: batchId === 2001 ? 1 : 2,
    breed_id: 1,
    gender: i % 2 === 0 ? 1 : 2,
    date_in: '2026-03-15',
    age_day_in: 1,
    weight_in: 42 + Math.random() * 5,
    status: 1,
    traceability_code: `TR-20260315-AA-001-${String(i).padStart(5, '0')}`
  })
}

const allGrowthRecords = []
individuals.forEach(ind => {
  allGrowthRecords.push(...generateGrowthRecords(ind.id, ind.batch_id, ind.weight_in, 12))
})

// ==================== 健康记录 ====================
const healthRecords = [
  { id: 5001, record_type: 1, batch_id: 2001, record_date: '2026-03-22', event_name: '新城疫疫苗首免', drug_name: '新城疫活疫苗(IV系)', veterinarian: '王兽医', cost: 2000, mortality_flag: 0 },
  { id: 5002, record_type: 1, batch_id: 2001, record_date: '2026-04-05', event_name: '禽流感疫苗免疫', drug_name: '禽流感H5+H7疫苗', veterinarian: '王兽医', cost: 3000, mortality_flag: 0 },
  { id: 5003, record_type: 2, batch_id: 2001, record_date: '2026-04-12', event_name: '呼吸道症状诊治', drug_name: '泰乐菌素', drug_dosage: '1g/L饮水', symptom: '咳嗽、打喷嚏', diagnosis: '慢性呼吸道病', treatment_result: 2, veterinarian: '王兽医', cost: 500, mortality_flag: 0 },
  { id: 5004, record_type: 3, batch_id: 2001, record_date: '2026-04-15', event_name: '用药治疗', drug_name: '恩诺沙星可溶性粉', drug_dosage: '50mg/kg体重', veterinarian: '王兽医', cost: 800, mortality_flag: 0 },
  { id: 5005, record_type: 5, batch_id: 2001, record_date: '2026-05-01', event_name: '定期检疫', diagnosis: '检疫合格', veterinarian: '王兽医', cost: 1000, mortality_flag: 0 },
]

// ==================== 养殖操作记录 ====================
const breedingOperations = [
  { id: 6001, batch_id: 2001, operation_type: 1, operation_date: '2026-03-15', operation_name: '入栏', operator: '张技术员', detail: '10000羽AA+鸡苗入栏' },
  { id: 6002, batch_id: 2001, operation_type: 3, operation_date: '2026-03-22', operation_name: '免疫', operator: '王兽医', detail: '新城疫疫苗首免' },
  { id: 6003, batch_id: 2001, operation_type: 4, operation_date: '2026-03-29', operation_name: '称重', operator: '李技术员', detail: '7日龄平均体重82g' },
  { id: 6004, batch_id: 2001, operation_type: 5, operation_date: '2026-04-05', operation_name: '转群', operator: '张技术员', detail: '由育雏舍转入育成舍' },
  { id: 6005, batch_id: 2001, operation_type: 3, operation_date: '2026-04-12', operation_name: '免疫', operator: '王兽医', detail: '禽流感疫苗免疫' },
  { id: 6006, batch_id: 2001, operation_type: 4, operation_date: '2026-04-19', operation_name: '称重', operator: '李技术员', detail: '35日龄平均体重1580g' },
]

// ==================== 环境数据 ====================
const environmentParams = []
for (let i = 0; i < 30; i++) {
  environmentParams.push({
    id: 7000 + i,
    house_id: 1,
    record_date: `2026-04-${String(i + 1).padStart(2, '0')}`,
    temperature: 24 + Math.random() * 4 - 2,
    humidity: 55 + Math.random() * 20 - 10,
    ammonia: 8 + Math.random() * 6,
    co2: 800 + Math.random() * 400
  })
}

// ==================== 财务数据 ====================
const financialTransactions = []
const categories = [
  { cat: '鸡苗采购', type: 2 }, { cat: '饲料采购', type: 2 }, { cat: '药品采购', type: 2 },
  { cat: '设备折旧', type: 2 }, { cat: '人工成本', type: 2 }, { cat: '水电费用', type: 2 },
  { cat: '鸡苗销售', type: 1 }, { cat: '淘汰鸡销售', type: 1 }, { cat: '副产品销售', type: 1 }
]
for (let i = 0; i < 50; i++) {
  const cat = categories[Math.floor(Math.random() * categories.length)]
  const month = Math.floor(Math.random() * 9) + 1
  const day = Math.floor(Math.random() * 28) + 1
  financialTransactions.push({
    id: 8000 + i,
    transaction_no: `FT-2026${String(month).padStart(2, '0')}${String(day).padStart(2, '0')}-${String(i).padStart(3, '0')}`,
    transaction_type: cat.type,
    category: cat.cat,
    amount: cat.type === 1 ? 50000 + Math.random() * 200000 : 10000 + Math.random() * 80000,
    batch_id: [2001, 2002, 2003, 2004][Math.floor(Math.random() * 4)],
    transaction_date: `2026-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
    payee_payer: ['新希望六和', '正大饲料', '温氏集团', '本地经销商'][Math.floor(Math.random() * 4)],
    remark: 'mock数据'
  })
}

// ==================== 利润分析数据 ====================
const profitAnalysis = batches.map(b => {
  const revenue = b.status === 2 ? 2500000 : b.quantity_current * 25
  const cost = b.status === 2 ? 2000000 : b.quantity_current * 20
  const profit = revenue - cost
  return {
    batch_id: b.id,
    batch_no: b.batch_no,
    breed_name: breeds.find(br => br.id === b.breed_id)?.breed_name || '',
    total_revenue: revenue,
    total_cost: cost,
    gross_profit: profit,
    profit_margin: (profit / revenue * 100).toFixed(2),
    cost_per_bird: (cost / b.quantity_initial).toFixed(2),
    revenue_per_bird: (revenue / b.quantity_initial).toFixed(2),
    profit_per_bird: (profit / b.quantity_initial).toFixed(2),
    roi: (profit / cost * 100).toFixed(2)
  }
})

// ==================== 中试项目数据 ====================
const pilotProjects = [
  { id: 1001, project_name: '微藻功能饲料中试', start_date: '2026-04-01', end_date: '2026-10-01', status: 1, responsible_person: '刘中试负责人', description: '评估微藻功能饲料对肉鸡生长性能的影响' }
]

const pilotBatches = [
  { id: 9001, pilot_project_id: 1001, batch_id: 2003, group_type: 1 },
  { id: 9002, pilot_project_id: 1001, batch_id: 2002, group_type: 2 },
]

const pilotIndicators = [
  { id: 10001, pilot_project_id: 1001, indicator_name: '成活率', experimental_value: 98.0, control_value: 97.5, unit: '%' },
  { id: 10002, pilot_project_id: 1001, indicator_name: '日增重', experimental_value: 52.3, control_value: 48.2, unit: 'g' },
  { id: 10003, pilot_project_id: 1001, indicator_name: '料肉比', experimental_value: 1.72, control_value: 1.85, unit: '' },
  { id: 10004, pilot_project_id: 1001, indicator_name: '硒含量', experimental_value: 0.35, control_value: 0.18, unit: 'mg/kg' },
]

// ==================== 库存数据 ====================
const inventoryItems = [
  { id: 70001, item_code: 'FEED-001', item_name: '玉米-东北二等', item_category: 1, item_spec: '水分≤14%，蛋白≥8%', unit: 'kg', quantity: 50000, safety_stock: 10000, storage_location: 'A仓库-3号货架-2层', expiry_date: '2026-09-01', status: 1 },
  { id: 70002, item_code: 'FEED-002', item_name: '豆粕-43%蛋白', item_category: 1, item_spec: '蛋白≥43%', unit: 'kg', quantity: 8000, safety_stock: 5000, storage_location: 'A仓库-2号货架-1层', expiry_date: '2026-08-15', status: 1 },
  { id: 70003, item_code: 'VAC-001', item_name: '新城疫活疫苗(IV系)', item_category: 3, item_spec: '1000羽份/瓶', unit: '瓶', quantity: 50, safety_stock: 200, storage_location: 'B冷库-1号柜', expiry_date: '2026-12-01', status: 1 },
  { id: 70004, item_code: 'DRUG-001', item_name: '恩诺沙星可溶性粉', item_category: 2, item_spec: '10%', unit: '袋', quantity: 100, safety_stock: 50, storage_location: 'C药库-2号柜', expiry_date: '2026-04-15', status: 2 },
  { id: 70005, item_code: 'VAC-002', item_name: '禽流感疫苗(H5+H7)', item_category: 3, item_spec: '500羽份/瓶', unit: '瓶', quantity: 20, safety_stock: 30, storage_location: 'B冷库-2号柜', expiry_date: '2026-03-01', status: 3 },
  { id: 70006, item_code: 'FEED-003', item_name: '微藻功能饲料', item_category: 1, item_spec: '含硒0.5mg/kg', unit: 'kg', quantity: 3000, safety_stock: 1000, storage_location: 'A仓库-5号货架', expiry_date: '2026-10-01', status: 1 },
]

const inventoryTransactions = [
  { id: 80001, inventory_id: 70001, trans_type: 1, trans_date: '2026-03-16', quantity: 10000, balance: 50000, ref_type: 1, operator: '赵仓管', remark: '饲料到货验收合格' },
  { id: 80002, inventory_id: 70001, trans_type: 2, trans_date: '2026-03-20', quantity: -2000, balance: 48000, ref_type: 3, operator: '赵仓管', remark: 'A区育雏舍1号领用' },
  { id: 80003, inventory_id: 70002, trans_type: 1, trans_date: '2026-03-18', quantity: 5000, balance: 8000, ref_type: 1, operator: '赵仓管', remark: '豆粕到货' },
  { id: 80004, inventory_id: 70003, trans_type: 1, trans_date: '2026-03-10', quantity: 100, balance: 50, ref_type: 1, operator: '赵仓管', remark: '疫苗入库' },
]

// ==================== 溯源数据 ====================
const traceabilityChain = [
  { stage: 1, stage_text: '种鸡', event_date: '2025-12-01', event_desc: '父母代种鸡引种', location: '引种基地', operator: '场长' },
  { stage: 2, stage_text: '种蛋', event_date: '2026-02-15', event_desc: '种蛋收集与消毒', location: '产蛋舍', operator: '张技术员' },
  { stage: 3, stage_text: '孵化', event_date: '2026-03-01', event_desc: '入孵21天孵化', location: '孵化厅', operator: '李孵化员' },
  { stage: 4, stage_text: '鸡苗', event_date: '2026-03-15', event_desc: '出壳鸡苗10000羽入栏', location: 'A区育雏舍1号', operator: '张技术员' },
  { stage: 5, stage_text: '养殖', event_date: '2026-03-22', event_desc: '新城疫疫苗首免', location: 'A区育雏舍1号', operator: '王兽医' },
  { stage: 5, stage_text: '养殖', event_date: '2026-04-15', event_desc: '35日龄称重平均1580g', location: 'A区育雏舍1号', operator: '李技术员' },
  { stage: 6, stage_text: '检疫', event_date: '2026-05-01', event_desc: '定期检疫合格', location: '检疫站', operator: '王兽医' },
]

// ==================== API 方法 ====================
export const mockApi = {
  // 批次
  async getBatches(params = {}) {
    await delay()
    let list = [...batches]
    if (params.status) list = list.filter(b => b.status == params.status)
    if (params.keyword) list = list.filter(b => b.batch_no.includes(params.keyword) || b.batch_name.includes(params.keyword))
    return { code: 0, data: { list, pagination: { page: 1, page_size: 20, total: list.length, total_pages: 1 } } }
  },

  async getBatchDetail(id) {
    await delay()
    const batch = batches.find(b => b.id == id)
    const breed = breeds.find(br => br.id === batch?.breed_id)
    const house = houses.find(h => h.id === batch?.house_id)
    return { code: 0, data: { ...batch, breed_name: breed?.breed_name, house_name: house?.house_name } }
  },

  // 个体
  async getIndividuals(params = {}) {
    await delay()
    let list = [...individuals]
    if (params.batch_id) list = list.filter(ind => ind.batch_id == params.batch_id)
    if (params.keyword) list = list.filter(ind => ind.animal_no.includes(params.keyword))
    return { code: 0, data: { list, pagination: { page: 1, page_size: 20, total: list.length } } }
  },

  async getIndividualDetail(id) {
    await delay()
    const ind = individuals.find(i => i.id == id)
    const batch = batches.find(b => b.id === ind?.batch_id)
    const breed = breeds.find(br => br.id === ind?.breed_id)
    return { code: 0, data: { ...ind, batch_no: batch?.batch_no, breed_name: breed?.breed_name } }
  },

  // 生长记录
  async getGrowthCurve(params) {
    await delay()
    let records = allGrowthRecords
    if (params.animal_id) records = records.filter(r => r.animal_id == params.animal_id)
    if (params.batch_id) records = records.filter(r => r.batch_id == params.batch_id)
    records.sort((a, b) => a.age_days - b.age_days)

    const breed = breeds.find(br => br.id === (params.breed_id || 1))
    const stdCurve = records.map(r => ({
      age_days: r.age_days,
      std_weight: parseFloat((42 + r.age_days * (breed?.daily_gain_std || 45)).toFixed(1))
    }))

    return { code: 0, data: { records, std_curve: stdCurve } }
  },

  async getBatchGrowthSummary(batchId) {
    await delay()
    const batchRecords = allGrowthRecords.filter(r => r.batch_id == batchId)
    const weights = batchRecords.map(r => r.weight)
    const avg = weights.reduce((a, b) => a + b, 0) / weights.length
    const min = Math.min(...weights)
    const max = Math.max(...weights)
    const sorted = [...weights].sort((a, b) => a - b)
    const q1 = sorted[Math.floor(sorted.length * 0.25)]
    const median = sorted[Math.floor(sorted.length * 0.5)]
    const q3 = sorted[Math.floor(sorted.length * 0.75)]

    return {
      code: 0,
      data: {
        count: weights.length,
        avg: avg.toFixed(1),
        min, max, q1, median, q3,
        std: Math.sqrt(weights.reduce((sum, w) => sum + (w - avg) ** 2, 0) / weights.length).toFixed(1)
      }
    }
  },

  // 健康记录
  async getHealthRecords(params = {}) {
    await delay()
    let list = [...healthRecords]
    if (params.batch_id) list = list.filter(h => h.batch_id == params.batch_id)
    if (params.record_type) list = list.filter(h => h.record_type == params.record_type)
    return { code: 0, data: { list } }
  },

  // 操作记录
  async getBreedingOperations(batchId) {
    await delay()
    const list = breedingOperations.filter(o => o.batch_id == batchId)
    return { code: 0, data: { list } }
  },

  // 环境数据
  async getEnvironmentParams(params = {}) {
    await delay()
    let list = [...environmentParams]
    if (params.house_id) list = list.filter(e => e.house_id == params.house_id)
    return { code: 0, data: { list } }
  },

  // 财务
  async getFinancialTransactions(params = {}) {
    await delay()
    let list = [...financialTransactions]
    if (params.transaction_type) list = list.filter(t => t.transaction_type == params.transaction_type)
    if (params.batch_id) list = list.filter(t => t.batch_id == params.batch_id)
    if (params.start_date && params.end_date) {
      list = list.filter(t => t.transaction_date >= params.start_date && t.transaction_date <= params.end_date)
    }
    if (params.category) list = list.filter(t => t.category === params.category)

    const totalIncome = list.filter(t => t.transaction_type === 1).reduce((sum, t) => sum + t.amount, 0)
    const totalExpense = list.filter(t => t.transaction_type === 2).reduce((sum, t) => sum + t.amount, 0)

    // 月度汇总
    const monthMap = {}
    list.forEach(t => {
      const month = t.transaction_date.slice(0, 7)
      if (!monthMap[month]) monthMap[month] = { group_key: month, income: 0, expense: 0 }
      if (t.transaction_type === 1) monthMap[month].income += t.amount
      else monthMap[month].expense += t.amount
    })
    const groupedData = Object.values(monthMap).map(m => ({
      ...m,
      net_profit: m.income - m.expense,
      profit_margin: m.income > 0 ? ((m.income - m.expense) / m.income * 100).toFixed(2) : 0
    })).sort((a, b) => a.group_key.localeCompare(b.group_key))

    // 科目占比
    const catMap = {}
    list.forEach(t => {
      if (!catMap[t.category]) catMap[t.category] = { category: t.category, type: t.transaction_type === 1 ? 'income' : 'expense', amount: 0 }
      catMap[t.category].amount += t.amount
    })
    const totalCat = Object.values(catMap).reduce((s, c) => s + c.amount, 0)
    const categoryBreakdown = Object.values(catMap).map(c => ({ ...c, pct: (c.amount / totalCat * 100).toFixed(2) }))

    return {
      code: 0,
      data: {
        summary: { total_income: totalIncome, total_expense: totalExpense, net_profit: totalIncome - totalExpense },
        list,
        grouped_data: groupedData,
        category_breakdown: categoryBreakdown,
        pagination: { page: 1, page_size: 20, total: list.length }
      }
    }
  },

  // 利润
  async getProfitRanking(params = {}) {
    await delay()
    let list = [...profitAnalysis]
    if (params.sort_by === 'profit_margin') list.sort((a, b) => b.profit_margin - a.profit_margin)
    else if (params.sort_by === 'gross_profit') list.sort((a, b) => b.gross_profit - a.gross_profit)
    else if (params.sort_by === 'roi') list.sort((a, b) => b.roi - a.roi)
    else list.sort((a, b) => b.gross_profit - a.gross_profit)

    list.forEach((item, idx) => item.rank = idx + 1)
    return { code: 0, data: { list, pagination: { page: 1, page_size: 20, total: list.length } } }
  },

  async getBatchProfit(batchId) {
    await delay()
    const profit = profitAnalysis.find(p => p.batch_id == batchId)
    return { code: 0, data: profit }
  },

  // 中试
  async getPilotProjects() {
    await delay()
    return { code: 0, data: { list: pilotProjects } }
  },

  async getPilotComparison(projectId) {
    await delay()
    const project = pilotProjects.find(p => p.id == projectId)
    const indicators = pilotIndicators.filter(p => p.pilot_project_id == projectId)
    const expBatch = pilotBatches.find(pb => pb.pilot_project_id == projectId && pb.group_type === 1)
    const ctlBatch = pilotBatches.find(pb => pb.pilot_project_id == projectId && pb.group_type === 2)

    // 生成对比生长曲线
    const expGrowth = []
    const ctlGrowth = []
    let expWeight = 42, ctlWeight = 42
    for (let i = 0; i < 12; i++) {
      const age = (i + 1) * 7
      expWeight += 52 + Math.random() * 10 - 5
      ctlWeight += 48 + Math.random() * 10 - 5
      expGrowth.push({ age_days: age, weight: parseFloat(expWeight.toFixed(1)) })
      ctlGrowth.push({ age_days: age, weight: parseFloat(ctlWeight.toFixed(1)) })
    }

    const totalDays = Math.ceil((new Date(project.end_date) - new Date(project.start_date)) / 86400000)
    const passedDays = Math.ceil((new Date() - new Date(project.start_date)) / 86400000)

    return {
      code: 0,
      data: {
        project,
        progress_pct: Math.min(100, Math.round(passedDays / totalDays * 100)),
        indicators: indicators.map(ind => ({
          ...ind,
          diff: (ind.experimental_value - ind.control_value).toFixed(2),
          diff_pct: ((ind.experimental_value - ind.control_value) / ind.control_value * 100).toFixed(2)
        })),
        experimental_growth: expGrowth,
        control_growth: ctlGrowth,
        experimental_batch: batches.find(b => b.id === expBatch?.batch_id),
        control_batch: batches.find(b => b.id === ctlBatch?.batch_id)
      }
    }
  },

  // 溯源
  async getTraceability(code) {
    await delay()
    const ind = individuals.find(i => i.traceability_code === code)
    if (!ind) return { code: 404, message: '未找到该溯源码' }

    const batch = batches.find(b => b.id === ind.batch_id)
    const breed = breeds.find(br => br.id === ind.breed_id)
    const house = houses.find(h => h.id === ind.house_id)

    const coveredStages = [...new Set(traceabilityChain.map(c => c.stage))].length
    const totalStages = 7

    return {
      code: 0,
      data: {
        traceability_code: code,
        animal: { animal_no: ind.animal_no, breed_name: breed?.breed_name, gender: ind.gender, gender_text: ind.gender === 1 ? '公' : '母', date_in: ind.date_in },
        batch: { batch_no: batch?.batch_no, house_name: house?.house_name, responsible_person: batch?.responsible_person },
        chain: traceabilityChain,
        completeness: { total_stages: totalStages, covered_stages: coveredStages, completeness_pct: (coveredStages / totalStages * 100).toFixed(2) }
      }
    }
  },

  // 库存
  async getInventory(params = {}) {
    await delay()
    let list = [...inventoryItems]
    if (params.item_category) list = list.filter(i => i.item_category == params.item_category)
    if (params.status) list = list.filter(i => i.status == params.status)
    if (params.low_stock) list = list.filter(i => i.quantity < i.safety_stock)
    if (params.near_expiry) {
      const now = new Date()
      list = list.filter(i => {
        const days = Math.ceil((new Date(i.expiry_date) - now) / 86400000)
        return days >= 0 && days <= 30
      })
    }
    if (params.keyword) list = list.filter(i => i.item_name.includes(params.keyword) || i.item_code.includes(params.keyword))

    const lowStockCount = inventoryItems.filter(i => i.quantity < i.safety_stock).length
    const nearExpiryCount = inventoryItems.filter(i => {
      const days = Math.ceil((new Date(i.expiry_date) - new Date()) / 86400000)
      return days >= 0 && days <= 30
    }).length

    return {
      code: 0,
      data: {
        summary: { total_items: inventoryItems.length, low_stock_count: lowStockCount, near_expiry_count: nearExpiryCount },
        list,
        pagination: { page: 1, page_size: 20, total: list.length }
      }
    }
  },

  async getInventoryTransactions(inventoryId) {
    await delay()
    const item = inventoryItems.find(i => i.id == inventoryId)
    const list = inventoryTransactions.filter(t => t.inventory_id == inventoryId)
    return { code: 0, data: { inventory: item, list } }
  },

  async createInventoryTransaction(data) {
    await delay()
    const item = inventoryItems.find(i => i.id == data.inventory_id)
    if (item) {
      item.quantity += data.quantity
      inventoryTransactions.push({
        id: 80000 + inventoryTransactions.length,
        inventory_id: data.inventory_id,
        trans_type: data.trans_type,
        trans_date: new Date().toISOString().slice(0, 10),
        quantity: data.quantity,
        balance: item.quantity,
        ref_type: data.ref_type || 5,
        operator: '当前用户',
        remark: data.remark || ''
      })
    }
    return { code: 0, data: { success: true } }
  },

  // 性能偏差
  async getBatchPerformance(batchId) {
    await delay()
    const batch = batches.find(b => b.id == batchId)
    const breed = breeds.find(br => br.id === batch?.breed_id)

    const actualSurvival = ((batch.quantity_current || batch.quantity_initial) / batch.quantity_initial * 100).toFixed(2)
    const stdSurvival = breed?.survival_rate_std || 95
    const survivalDev = (actualSurvival - stdSurvival).toFixed(2)

    // 模拟日增重
    const actualAdg = (42 + Math.random() * 10).toFixed(2)
    const stdAdg = breed?.daily_gain_std || 45
    const adgDev = (actualAdg - stdAdg).toFixed(2)

    // 模拟料肉比
    const actualFmr = (1.7 + Math.random() * 0.3).toFixed(3)
    const stdFmr = breed?.feed_meat_ratio || 1.85
    const fmrDev = (actualFmr - stdFmr).toFixed(3)

    return {
      code: 0,
      data: {
        batch_id: batchId,
        batch_no: batch?.batch_no,
        breed_name: breed?.breed_name,
        survival: { actual: actualSurvival, standard: stdSurvival, deviation: survivalDev, deviation_pct: ((survivalDev / stdSurvival) * 100).toFixed(2) },
        adg: { actual: actualAdg, standard: stdAdg, deviation: adgDev, deviation_pct: ((adgDev / stdAdg) * 100).toFixed(2) },
        fmr: { actual: actualFmr, standard: stdFmr, deviation: fmrDev, deviation_pct: ((fmrDev / stdFmr) * 100).toFixed(2) },
        trend: Array.from({ length: 10 }, (_, i) => ({
          date: `2026-04-${String(i + 1).padStart(2, '0')}`,
          survival_dev: (Math.random() * 6 - 3).toFixed(2),
          adg_dev: (Math.random() * 10 - 5).toFixed(2),
          fmr_dev: (Math.random() * 0.4 - 0.2).toFixed(3)
        }))
      }
    }
  }
}
