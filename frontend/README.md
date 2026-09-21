# AI智慧养殖系统 V2.0 前端项目

## 项目概述

基于 Vue 3 + Element Plus + Pinia + ECharts 5 + Vite 构建的 AI 智慧养殖系统 V2.0 前端应用，覆盖 8 个 P0 核心页面。

## 技术栈

- **前端框架**: Vue 3 (Composition API)
- **UI 组件库**: Element Plus 2.x
- **状态管理**: Pinia
- **图表库**: ECharts 5 + vue-echarts
- **构建工具**: Vite 5
- **路由**: Vue Router 4
- **样式**: CSS 变量 + Element Plus 主题

## 项目结构

```
smart-farming-v2/
├── public/                 # 静态资源
├── src/
│   ├── api/
│   │   └── mock.js         # Mock API 数据层
│   ├── components/
│   │   ├── AppLayout.vue   # 页面布局框架
│   │   ├── SideNav.vue     # 侧边导航菜单
│   │   └── TopBar.vue      # 顶部用户信息栏
│   ├── router/
│   │   └── index.js        # 路由配置
│   ├── stores/
│   ├── styles/
│   │   └── variables.css   # CSS 变量主题
│   ├── views/
│   │   ├── GrowthCurve.vue        # 页面1: 个体生长曲线
│   │   ├── BatchLifecycle.vue     # 页面2: 批次全生命周期
│   │   ├── PerformanceDeviation.vue # 页面3: 性能偏差看板
│   │   ├── PilotComparison.vue    # 页面4: 中试效果对比
│   │   ├── FinancialManagement.vue # 页面5: 财务收支管理
│   │   ├── ProfitAnalysis.vue     # 页面6: 批次利润分析
│   │   ├── TraceabilityQuery.vue  # 页面7: 溯源查询
│   │   └── InventoryManagement.vue # 页面8: 库存管理
│   ├── App.vue
│   └── main.js
├── index.html
├── package.json
├── vite.config.js
└── README.md
```

## 8个P0页面功能说明

| 页面 | 核心功能 | 图表组件 |
|------|---------|---------|
| 个体生长曲线 | 单只/批次生长曲线、标准曲线叠加、体重分布箱线图+直方图、偏差分析 | ECharts 折线图+箱线图+直方图 |
| 批次全生命周期 | 批次时间轴、KPI卡片、关联数据标签页(个体/操作/环境/健康/死淘/成本) | ECharts 折线图+饼图 |
| 性能偏差看板 | 成活率/日增重/料肉比偏差、趋势图、达标率仪表盘、偏差分布 | ECharts 折线图+仪表盘 |
| 中试效果对比 | 实验组vs对照组指标对比表、生长曲线叠加、项目进度、功能性指标 | ECharts 折线图 |
| 财务收支管理 | 收支流水CRUD、月度趋势组合图、科目占比饼图、批次成本归集 | ECharts 柱状图+折线图+饼图 |
| 批次利润分析 | 利润排名表格、单只成本/收入/利润、毛利率仪表盘、利润对比柱状图 | ECharts 柱状图+仪表盘 |
| 溯源查询 | 溯源码输入/扫码、全链路时间线、完整度评分、分享/打印 | El-Timeline+进度环 |
| 库存管理 | 库存表格、预警徽章(红色/黄色)、出入库操作、流水追溯 | El-Table+El-Timeline |

## 本地开发

### 环境要求
- Node.js >= 18
- npm >= 9

### 安装依赖
```bash
npm install
```

### 启动开发服务器
```bash
npm run dev
```
访问 http://localhost:3000

### 生产构建
```bash
npm run build
```
构建产物输出到 `dist/` 目录

## 部署说明

### 方式一：静态文件部署（推荐）

1. 执行构建
   ```bash
   npm run build
   ```

2. 将 `dist/` 目录下的所有文件部署到任意静态文件服务器
   - Nginx
   - Apache
   - GitHub Pages
   - CDN

3. Nginx 配置示例
   ```nginx
   server {
     listen 80;
     server_name farming.example.com;
     root /var/www/smart-farming-v2/dist;
     index index.html;

     location / {
       try_files $uri $uri/ /index.html;
     }

     location /api {
       proxy_pass http://backend-server:8080;
     }
   }
   ```

### 方式二：Docker 部署

```dockerfile
FROM nginx:alpine
COPY dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### 方式三：开发环境直接运行

```bash
npm install
npm run dev
```

## API 对接说明

当前使用 Mock 数据开发，API 基础路径为 `/api/v2`。

切换至真实后端时：
1. 修改 `vite.config.js` 中的 `proxy` 配置指向实际后端地址
2. 替换 `src/api/mock.js` 为真实的 HTTP 请求层（如 axios）

### 已实现的 Mock API 列表

| API | 方法 | 说明 |
|-----|------|------|
| /batches | GET | 批次列表 |
| /individuals | GET | 个体列表 |
| /individuals/{id}/growth-curve | GET | 生长曲线 |
| /batches/{id}/lifecycle | GET | 批次生命周期 |
| /batches/{id}/performance | GET | 性能偏差 |
| /pilots | GET | 中试项目列表 |
| /pilots/{id}/comparison | GET | 中试效果对比 |
| /financial-transactions | GET/POST | 财务收支 |
| /financial-transactions/summary | GET | 收支汇总 |
| /profit-analysis/ranking | GET | 利润排名 |
| /traceability/{code} | GET | 溯源查询 |
| /inventory | GET/POST | 库存管理 |
| /inventory/{id}/transactions | GET | 库存流水 |

## 状态管理

使用 Pinia 管理全局状态：
- 用户认证状态
- 当前选中批次
- 页面筛选条件

## 响应式布局

- 桌面端：侧边导航 220px + 主内容区自适应
- 表格和图表均支持容器自适应

## 已知问题与后续优化

1. **Element Plus 图标**: 部分图标需确认版本兼容性
2. **代码分割**: 当前打包产物中 ECharts + Element Plus 较大，建议按需加载
3. **Mock 数据**: 当前为静态 Mock，切换真实 API 时需补充错误处理
4. **打印功能**: 溯源报告打印需引入 print-js 等库
5. **二维码扫描**: 当前为模拟扫码，实际需接入扫码设备 SDK

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v2.0.0 | 2026-09-21 | 初版，8个P0页面完整实现 |
