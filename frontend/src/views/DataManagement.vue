<template>
  <div class="data-management">
    <el-page-header title="数据管理" content="基础数据录入与维护" />
    <el-tabs v-model="activeTab" class="mgmt-tabs">
      <!-- 品种管理 -->
      <el-tab-pane label="品种管理" name="breeds">
        <el-row :gutter="12" class="toolbar">
          <el-col :span="6"><el-input v-model="breedFilters.keyword" placeholder="搜索品种名称/编码" clearable @change="loadBreeds" /></el-col>
          <el-col :span="4"><el-button type="primary" @click="openBreedDialog()">+ 新增品种</el-button></el-col>
        </el-row>
        <el-table :data="breedList" v-loading="loading.breeds" stripe>
          <el-table-column prop="breed_code" label="品种编码" width="120" />
          <el-table-column prop="breed_name" label="品种名称" />
          <el-table-column prop="breed_type" label="类型" width="100" />
          <el-table-column prop="origin" label="产地" />
          <el-table-column prop="avg_weight_male" label="公均重(kg)" width="110" />
          <el-table-column prop="avg_weight_female" label="母均重(kg)" width="110" />
          <el-table-column prop="avg_egg_rate" label="产蛋率(%)" width="110" />
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" @click="openBreedDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteBreed(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="breedFilters.page" :page-size="breedFilters.page_size" :total="breedTotal" layout="prev,pager,next" @current-change="loadBreeds" />
      </el-tab-pane>

      <!-- 鸡舍管理 -->
      <el-tab-pane label="鸡舍管理" name="houses">
        <el-row :gutter="12" class="toolbar">
          <el-col :span="6"><el-input v-model="houseFilters.keyword" placeholder="搜索鸡舍名称/编码" clearable @change="loadHouses" /></el-col>
          <el-col :span="4"><el-button type="primary" @click="openHouseDialog()">+ 新增鸡舍</el-button></el-col>
        </el-row>
        <el-table :data="houseList" v-loading="loading.houses" stripe>
          <el-table-column prop="house_code" label="鸡舍编码" width="120" />
          <el-table-column prop="house_name" label="鸡舍名称" />
          <el-table-column prop="house_type" label="类型" width="100" />
          <el-table-column prop="area_sqm" label="面积(m²)" width="100" />
          <el-table-column prop="capacity" label="容量" width="80" />
          <el-table-column prop="location" label="位置" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status===1?'success':'info'">{{ row.status===1?'启用':'停用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" @click="openHouseDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteHouse(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="houseFilters.page" :page-size="houseFilters.page_size" :total="houseTotal" layout="prev,pager,next" @current-change="loadHouses" />
      </el-tab-pane>

      <!-- 批次管理 -->
      <el-tab-pane label="批次管理" name="batches">
        <el-row :gutter="12" class="toolbar">
          <el-col :span="6"><el-input v-model="batchFilters.keyword" placeholder="搜索批次号/名称" clearable @change="loadBatches" /></el-col>
          <el-col :span="4"><el-button type="primary" @click="openBatchDialog()">+ 新增批次</el-button></el-col>
        </el-row>
        <el-table :data="batchList" v-loading="loading.batches" stripe>
          <el-table-column prop="batch_no" label="批次号" width="140" />
          <el-table-column prop="batch_name" label="批次名称" />
          <el-table-column prop="breed_name" label="品种" />
          <el-table-column prop="house_name" label="鸡舍" />
          <el-table-column prop="quantity_initial" label="入栏数" width="90" />
          <el-table-column prop="quantity_current" label="现存数" width="90" />
          <el-table-column prop="date_in" label="入栏日期" width="120" />
          <el-table-column prop="responsible_person" label="负责人" width="100" />
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" @click="openBatchDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteBatch(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="batchFilters.page" :page-size="batchFilters.page_size" :total="batchTotal" layout="prev,pager,next" @current-change="loadBatches" />
      </el-tab-pane>

      <!-- 个体管理 -->
      <el-tab-pane label="个体管理" name="individuals">
        <el-row :gutter="12" class="toolbar">
          <el-col :span="6"><el-input v-model="individualFilters.keyword" placeholder="搜索耳标号/溯源码" clearable @change="loadIndividuals" /></el-col>
          <el-col :span="4"><el-button type="primary" @click="openIndividualDialog()">+ 新增个体</el-button></el-col>
        </el-row>
        <el-table :data="individualList" v-loading="loading.individuals" stripe>
          <el-table-column prop="animal_no" label="耳标号" width="120" />
          <el-table-column prop="batch_no" label="批次号" />
          <el-table-column prop="house_name" label="鸡舍" />
          <el-table-column prop="breed_name" label="品种" />
          <el-table-column prop="gender" label="性别" width="80">
            <template #default="{ row }">
              {{ row.gender===1?'公':row.gender===2?'母':'-' }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.status===1?'success':row.status===2?'warning':'info'">
                {{ {1:'存栏',2:'出栏',3:'死淘'}[row.status]||row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="date_in" label="入栏日期" width="120" />
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" @click="openIndividualDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteIndividual(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="individualFilters.page" :page-size="individualFilters.page_size" :total="individualTotal" layout="prev,pager,next" @current-change="loadIndividuals" />
      </el-tab-pane>

      <!-- 养殖操作 -->
      <el-tab-pane label="养殖操作" name="operations">
        <el-row :gutter="12" class="toolbar">
          <el-col :span="4"><el-button type="primary" @click="openOperationDialog()">+ 新增操作</el-button></el-col>
        </el-row>
        <el-table :data="operationList" v-loading="loading.operations" stripe>
          <el-table-column prop="op_type" label="操作类型" width="100" />
          <el-table-column prop="op_date" label="操作日期" width="120" />
          <el-table-column prop="operator" label="操作人" width="100" />
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column prop="remark" label="备注" show-overflow-tooltip />
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" @click="openOperationDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteOperation(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="operationFilters.page" :page-size="operationFilters.page_size" :total="operationTotal" layout="prev,pager,next" @current-change="loadOperations" />
      </el-tab-pane>

      <!-- 健康记录 -->
      <el-tab-pane label="健康记录" name="health">
        <el-row :gutter="12" class="toolbar">
          <el-col :span="4"><el-button type="primary" @click="openHealthDialog()">+ 新增记录</el-button></el-col>
        </el-row>
        <el-table :data="healthList" v-loading="loading.health" stripe>
          <el-table-column prop="record_date" label="记录日期" width="120" />
          <el-table-column prop="record_type" label="类型" width="100">
            <template #default="{ row }">
              {{ {1:'免疫',2:'治疗',3:'死淘'}[row.record_type]||row.record_type }}
            </template>
          </el-table-column>
          <el-table-column prop="event_name" label="事件名称" />
          <el-table-column prop="drug_name" label="药品" />
          <el-table-column prop="symptom" label="症状" show-overflow-tooltip />
          <el-table-column prop="diagnosis" label="诊断" show-overflow-tooltip />
          <el-table-column prop="veterinarian" label="兽医" width="100" />
          <el-table-column prop="mortality_flag" label="死淘" width="80">
            <template #default="{ row }">
              <el-tag v-if="row.mortality_flag===1" type="danger">是</el-tag>
              <span v-else>否</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" type="danger" @click="deleteHealth(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="healthFilters.page" :page-size="healthFilters.page_size" :total="healthTotal" layout="prev,pager,next" @current-change="loadHealth" />
      </el-tab-pane>

      <!-- 销售管理 -->
      <el-tab-pane label="销售管理" name="sales">
        <el-row :gutter="12" class="toolbar">
          <el-col :span="6"><el-input v-model="saleFilters.customer_name" placeholder="客户名称" clearable @change="loadSales" /></el-col>
          <el-col :span="4"><el-button type="primary" @click="openSaleDialog()">+ 新增订单</el-button></el-col>
        </el-row>
        <el-table :data="saleList" v-loading="loading.sales" stripe>
          <el-table-column prop="order_no" label="订单号" width="140" />
          <el-table-column prop="customer_name" label="客户" />
          <el-table-column prop="order_date" label="日期" width="120" />
          <el-table-column prop="total_quantity" label="数量" width="80" />
          <el-table-column prop="total_amount" label="金额" width="120" />
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.status===1?'success':row.status===2?'warning':'info'">
                {{ {1:'已确认',2:'已发货',3:'已完成'}[row.status]||row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" @click="openSaleDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteSale(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="saleFilters.page" :page-size="saleFilters.page_size" :total="saleTotal" layout="prev,pager,next" @current-change="loadSales" />
      </el-tab-pane>

      <!-- 采购管理 -->
      <el-tab-pane label="采购管理" name="purchases">
        <el-row :gutter="12" class="toolbar">
          <el-col :span="6"><el-input v-model="purchaseFilters.supplier_name" placeholder="供应商名称" clearable @change="loadPurchases" /></el-col>
          <el-col :span="4"><el-button type="primary" @click="openPurchaseDialog()">+ 新增订单</el-button></el-col>
        </el-row>
        <el-table :data="purchaseList" v-loading="loading.purchases" stripe>
          <el-table-column prop="order_no" label="订单号" width="140" />
          <el-table-column prop="supplier_name" label="供应商" />
          <el-table-column prop="order_date" label="日期" width="120" />
          <el-table-column prop="total_quantity" label="数量" width="80" />
          <el-table-column prop="total_amount" label="金额" width="120" />
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.status===1?'success':row.status===2?'warning':'info'">
                {{ {1:'已确认',2:'已到货',3:'已完成'}[row.status]||row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" @click="openPurchaseDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deletePurchase(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="purchaseFilters.page" :page-size="purchaseFilters.page_size" :total="purchaseTotal" layout="prev,pager,next" @current-change="loadPurchases" />
      </el-tab-pane>
    </el-tabs>

    <!-- 品种表单弹窗 -->
    <el-dialog v-model="dialogs.breed" :title="breedForm.id?'编辑品种':'新增品种'" width="600px">
      <el-form :model="breedForm" label-width="100px">
        <el-form-item label="品种编码"><el-input v-model="breedForm.breed_code" /></el-form-item>
        <el-form-item label="品种名称"><el-input v-model="breedForm.breed_name" /></el-form-item>
        <el-form-item label="类型"><el-input v-model="breedForm.breed_type" /></el-form-item>
        <el-form-item label="产地"><el-input v-model="breedForm.origin" /></el-form-item>
        <el-form-item label="公均重(kg)"><el-input-number v-model="breedForm.avg_weight_male" :precision="2" /></el-form-item>
        <el-form-item label="母均重(kg)"><el-input-number v-model="breedForm.avg_weight_female" :precision="2" /></el-form-item>
        <el-form-item label="产蛋率(%)"><el-input-number v-model="breedForm.avg_egg_rate" :precision="2" /></el-form-item>
        <el-form-item label="料肉比"><el-input-number v-model="breedForm.feed_meat_ratio" :precision="3" /></el-form-item>
        <el-form-item label="成活率标准"><el-input-number v-model="breedForm.survival_rate_std" :precision="2" /></el-form-item>
        <el-form-item label="日增重标准"><el-input-number v-model="breedForm.daily_gain_std" :precision="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogs.breed=false">取消</el-button>
        <el-button type="primary" @click="saveBreed">保存</el-button>
      </template>
    </el-dialog>

    <!-- 鸡舍表单弹窗 -->
    <el-dialog v-model="dialogs.house" :title="houseForm.id?'编辑鸡舍':'新增鸡舍'" width="600px">
      <el-form :model="houseForm" label-width="100px">
        <el-form-item label="鸡舍编码"><el-input v-model="houseForm.house_code" /></el-form-item>
        <el-form-item label="鸡舍名称"><el-input v-model="houseForm.house_name" /></el-form-item>
        <el-form-item label="类型"><el-input v-model="houseForm.house_type" /></el-form-item>
        <el-form-item label="面积(m²)"><el-input-number v-model="houseForm.area_sqm" :precision="2" /></el-form-item>
        <el-form-item label="容量"><el-input-number v-model="houseForm.capacity" :precision="0" /></el-form-item>
        <el-form-item label="位置"><el-input v-model="houseForm.location" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="houseForm.status"><el-option label="启用" :value="1" /><el-option label="停用" :value="0" /></el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogs.house=false">取消</el-button>
        <el-button type="primary" @click="saveHouse">保存</el-button>
      </template>
    </el-dialog>

    <!-- 批次表单弹窗 -->
    <el-dialog v-model="dialogs.batch" :title="batchForm.id?'编辑批次':'新增批次'" width="600px">
      <el-form :model="batchForm" label-width="100px">
        <el-form-item label="批次号"><el-input v-model="batchForm.batch_no" /></el-form-item>
        <el-form-item label="批次名称"><el-input v-model="batchForm.batch_name" /></el-form-item>
        <el-form-item label="品种">
          <el-select v-model="batchForm.breed_id" filterable>
            <el-option v-for="b in allBreeds" :key="b.id" :label="b.breed_name" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="鸡舍">
          <el-select v-model="batchForm.house_id" filterable>
            <el-option v-for="h in allHouses" :key="h.id" :label="h.house_name" :value="h.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="入栏数量"><el-input-number v-model="batchForm.quantity_initial" :precision="0" /></el-form-item>
        <el-form-item label="入栏日期"><el-date-picker v-model="batchForm.date_in" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="入栏日龄"><el-input-number v-model="batchForm.age_day_in" :precision="0" /></el-form-item>
        <el-form-item label="负责人"><el-input v-model="batchForm.responsible_person" /></el-form-item>
        <el-form-item label="来源类型">
          <el-select v-model="batchForm.source_type">
            <el-option label="自繁" :value="1" /><el-option label="外购" :value="2" /><el-option label="回收" :value="3" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogs.batch=false">取消</el-button>
        <el-button type="primary" @click="saveBatch">保存</el-button>
      </template>
    </el-dialog>

    <!-- 个体表单弹窗 -->
    <el-dialog v-model="dialogs.individual" :title="individualForm.id?'编辑个体':'新增个体'" width="600px">
      <el-form :model="individualForm" label-width="100px">
        <el-form-item label="耳标号"><el-input v-model="individualForm.animal_no" /></el-form-item>
        <el-form-item label="批次">
          <el-select v-model="individualForm.batch_id" filterable>
            <el-option v-for="b in allBatches" :key="b.id" :label="b.batch_no" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="individualForm.gender"><el-option label="公" :value="1" /><el-option label="母" :value="2" /></el-select>
        </el-form-item>
        <el-form-item label="入栏日期"><el-date-picker v-model="individualForm.date_in" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="入栏体重"><el-input-number v-model="individualForm.weight_in" :precision="3" /></el-form-item>
        <el-form-item label="入栏日龄"><el-input-number v-model="individualForm.age_day_in" :precision="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogs.individual=false">取消</el-button>
        <el-button type="primary" @click="saveIndividual">保存</el-button>
      </template>
    </el-dialog>

    <!-- 操作记录弹窗 -->
    <el-dialog v-model="dialogs.operation" :title="operationForm.id?'编辑操作':'新增操作'" width="500px">
      <el-form :model="operationForm" label-width="100px">
        <el-form-item label="批次">
          <el-select v-model="operationForm.batch_id" filterable>
            <el-option v-for="b in allBatches" :key="b.id" :label="b.batch_no" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作类型"><el-input v-model="operationForm.op_type" /></el-form-item>
        <el-form-item label="操作日期"><el-date-picker v-model="operationForm.op_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="操作人"><el-input v-model="operationForm.operator" /></el-form-item>
        <el-form-item label="数量"><el-input-number v-model="operationForm.quantity" :precision="0" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="operationForm.remark" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogs.operation=false">取消</el-button>
        <el-button type="primary" @click="saveOperation">保存</el-button>
      </template>
    </el-dialog>

    <!-- 健康记录弹窗 -->
    <el-dialog v-model="dialogs.health" title="新增健康记录" width="500px">
      <el-form :model="healthForm" label-width="100px">
        <el-form-item label="类型">
          <el-select v-model="healthForm.record_type">
            <el-option label="免疫" :value="1" /><el-option label="治疗" :value="2" /><el-option label="死淘" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="记录日期"><el-date-picker v-model="healthForm.record_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="事件名称"><el-input v-model="healthForm.event_name" /></el-form-item>
        <el-form-item label="药品"><el-input v-model="healthForm.drug_name" /></el-form-item>
        <el-form-item label="剂量"><el-input v-model="healthForm.drug_dosage" /></el-form-item>
        <el-form-item label="症状"><el-input v-model="healthForm.symptom" type="textarea" /></el-form-item>
        <el-form-item label="诊断"><el-input v-model="healthForm.diagnosis" type="textarea" /></el-form-item>
        <el-form-item label="兽医"><el-input v-model="healthForm.veterinarian" /></el-form-item>
        <el-form-item label="死淘"><el-switch v-model="healthForm.mortality_flag" :active-value="1" :inactive-value="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogs.health=false">取消</el-button>
        <el-button type="primary" @click="saveHealth">保存</el-button>
      </template>
    </el-dialog>

    <!-- 销售订单弹窗 -->
    <el-dialog v-model="dialogs.sale" :title="saleForm.id?'编辑订单':'新增订单'" width="600px">
      <el-form :model="saleForm" label-width="100px">
        <el-form-item label="客户名称"><el-input v-model="saleForm.customer_name" /></el-form-item>
        <el-form-item label="客户电话"><el-input v-model="saleForm.customer_phone" /></el-form-item>
        <el-form-item label="订单日期"><el-date-picker v-model="saleForm.order_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="交货日期"><el-date-picker v-model="saleForm.delivery_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="总数量"><el-input-number v-model="saleForm.total_quantity" :precision="0" /></el-form-item>
        <el-form-item label="总金额"><el-input-number v-model="saleForm.total_amount" :precision="2" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="saleForm.remark" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogs.sale=false">取消</el-button>
        <el-button type="primary" @click="saveSale">保存</el-button>
      </template>
    </el-dialog>

    <!-- 采购订单弹窗 -->
    <el-dialog v-model="dialogs.purchase" :title="purchaseForm.id?'编辑订单':'新增订单'" width="600px">
      <el-form :model="purchaseForm" label-width="100px">
        <el-form-item label="供应商"><el-input v-model="purchaseForm.supplier_name" /></el-form-item>
        <el-form-item label="供应商电话"><el-input v-model="purchaseForm.supplier_phone" /></el-form-item>
        <el-form-item label="订单日期"><el-date-picker v-model="purchaseForm.order_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="交货日期"><el-date-picker v-model="purchaseForm.delivery_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="总数量"><el-input-number v-model="purchaseForm.total_quantity" :precision="0" /></el-form-item>
        <el-form-item label="总金额"><el-input-number v-model="purchaseForm.total_amount" :precision="2" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="purchaseForm.remark" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogs.purchase=false">取消</el-button>
        <el-button type="primary" @click="savePurchase">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const activeTab = ref('breeds')

const loading = reactive({
  breeds: false, houses: false, batches: false, individuals: false,
  operations: false, health: false, sales: false, purchases: false
})

const dialogs = reactive({
  breed: false, house: false, batch: false, individual: false,
  operation: false, health: false, sale: false, purchase: false
})

// 下拉选项缓存
const allBreeds = ref([])
const allHouses = ref([])
const allBatches = ref([])

// 品种
const breedList = ref([])
const breedTotal = ref(0)
const breedFilters = reactive({ keyword: '', page: 1, page_size: 20 })
const breedForm = reactive({})

async function loadBreeds() {
  loading.breeds = true
  try {
    const res = await api.getBreeds(breedFilters)
    breedList.value = res.data?.list || []
    breedTotal.value = res.data?.pagination?.total || 0
  } catch (e) { ElMessage.error('加载品种失败') }
  loading.breeds = false
}

function openBreedDialog(row = null) {
  if (row) Object.assign(breedForm, { ...row, id: row.id })
  else Object.keys(breedForm).forEach(k => delete breedForm[k])
  dialogs.breed = true
}

async function saveBreed() {
  try {
    if (breedForm.id) await api.updateBreed(breedForm.id, breedForm)
    else await api.createBreed(breedForm)
    ElMessage.success('保存成功')
    dialogs.breed = false
    loadBreeds()
  } catch (e) { ElMessage.error('保存失败') }
}

async function deleteBreed(row) {
  try {
    await ElMessageBox.confirm('确定删除该品种？', '提示', { type: 'warning' })
    await api.deleteBreed(row.id)
    ElMessage.success('删除成功')
    loadBreeds()
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

// 鸡舍
const houseList = ref([])
const houseTotal = ref(0)
const houseFilters = reactive({ keyword: '', page: 1, page_size: 20 })
const houseForm = reactive({})

async function loadHouses() {
  loading.houses = true
  try {
    const res = await api.getHouses(houseFilters)
    houseList.value = res.data?.list || []
    houseTotal.value = res.data?.pagination?.total || 0
  } catch (e) { ElMessage.error('加载鸡舍失败') }
  loading.houses = false
}

function openHouseDialog(row = null) {
  if (row) Object.assign(houseForm, { ...row, id: row.id })
  else Object.keys(houseForm).forEach(k => delete houseForm[k])
  dialogs.house = true
}

async function saveHouse() {
  try {
    if (houseForm.id) await api.updateHouse(houseForm.id, houseForm)
    else await api.createHouse(houseForm)
    ElMessage.success('保存成功')
    dialogs.house = false
    loadHouses()
  } catch (e) { ElMessage.error('保存失败') }
}

async function deleteHouse(row) {
  try {
    await ElMessageBox.confirm('确定删除该鸡舍？', '提示', { type: 'warning' })
    await api.deleteHouse(row.id)
    ElMessage.success('删除成功')
    loadHouses()
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

// 批次
const batchList = ref([])
const batchTotal = ref(0)
const batchFilters = reactive({ keyword: '', page: 1, page_size: 20 })
const batchForm = reactive({})

async function loadBatches() {
  loading.batches = true
  try {
    const res = await api.getBatches(batchFilters)
    batchList.value = res.data?.list || []
    batchTotal.value = res.data?.pagination?.total || 0
  } catch (e) { ElMessage.error('加载批次失败') }
  loading.batches = false
}

function openBatchDialog(row = null) {
  if (row) Object.assign(batchForm, { ...row, id: row.id })
  else Object.keys(batchForm).forEach(k => delete batchForm[k])
  dialogs.batch = true
}

async function saveBatch() {
  try {
    if (batchForm.id) await api.updateBatch(batchForm.id, batchForm)
    else await api.createBatch(batchForm)
    ElMessage.success('保存成功')
    dialogs.batch = false
    loadBatches()
  } catch (e) { ElMessage.error('保存失败') }
}

async function deleteBatch(row) {
  try {
    await ElMessageBox.confirm('确定删除该批次？', '提示', { type: 'warning' })
    await api.deleteBatch(row.id)
    ElMessage.success('删除成功')
    loadBatches()
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

// 个体
const individualList = ref([])
const individualTotal = ref(0)
const individualFilters = reactive({ keyword: '', page: 1, page_size: 20 })
const individualForm = reactive({})

async function loadIndividuals() {
  loading.individuals = true
  try {
    const res = await api.getIndividuals(individualFilters)
    individualList.value = res.data?.list || []
    individualTotal.value = res.data?.pagination?.total || 0
  } catch (e) { ElMessage.error('加载个体失败') }
  loading.individuals = false
}

function openIndividualDialog(row = null) {
  if (row) Object.assign(individualForm, { ...row, id: row.id })
  else Object.keys(individualForm).forEach(k => delete individualForm[k])
  dialogs.individual = true
}

async function saveIndividual() {
  try {
    if (individualForm.id) await api.updateIndividual(individualForm.id, individualForm)
    else await api.createIndividual(individualForm)
    ElMessage.success('保存成功')
    dialogs.individual = false
    loadIndividuals()
  } catch (e) { ElMessage.error('保存失败') }
}

async function deleteIndividual(row) {
  try {
    await ElMessageBox.confirm('确定删除该个体？', '提示', { type: 'warning' })
    await api.deleteIndividual(row.id)
    ElMessage.success('删除成功')
    loadIndividuals()
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

// 操作记录
const operationList = ref([])
const operationTotal = ref(0)
const operationFilters = reactive({ page: 1, page_size: 20 })
const operationForm = reactive({})

async function loadOperations() {
  loading.operations = true
  try {
    const res = await api.getOperations(operationFilters)
    operationList.value = res.data?.list || []
    operationTotal.value = res.data?.pagination?.total || 0
  } catch (e) { ElMessage.error('加载操作记录失败') }
  loading.operations = false
}

function openOperationDialog(row = null) {
  if (row) Object.assign(operationForm, { ...row, id: row.id })
  else Object.keys(operationForm).forEach(k => delete operationForm[k])
  dialogs.operation = true
}

async function saveOperation() {
  try {
    if (operationForm.id) await api.updateOperation(operationForm.id, operationForm)
    else await api.createOperation(operationForm)
    ElMessage.success('保存成功')
    dialogs.operation = false
    loadOperations()
  } catch (e) { ElMessage.error('保存失败') }
}

async function deleteOperation(row) {
  try {
    await ElMessageBox.confirm('确定删除该记录？', '提示', { type: 'warning' })
    await api.deleteOperation(row.id)
    ElMessage.success('删除成功')
    loadOperations()
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

// 健康记录
const healthList = ref([])
const healthTotal = ref(0)
const healthFilters = reactive({ page: 1, page_size: 20 })
const healthForm = reactive({})

async function loadHealth() {
  loading.health = true
  try {
    const res = await api.getHealthRecords(healthFilters)
    healthList.value = res.data?.list || []
    healthTotal.value = res.data?.pagination?.total || 0
  } catch (e) { ElMessage.error('加载健康记录失败') }
  loading.health = false
}

function openHealthDialog() {
  Object.keys(healthForm).forEach(k => delete healthForm[k])
  dialogs.health = true
}

async function saveHealth() {
  try {
    await api.createHealthRecord(healthForm)
    ElMessage.success('保存成功')
    dialogs.health = false
    loadHealth()
  } catch (e) { ElMessage.error('保存失败') }
}

async function deleteHealth(row) {
  try {
    await ElMessageBox.confirm('确定删除该记录？', '提示', { type: 'warning' })
    // 后端暂无健康记录删除接口，先提示
    ElMessage.info('删除功能待后端支持')
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

// 销售
const saleList = ref([])
const saleTotal = ref(0)
const saleFilters = reactive({ customer_name: '', page: 1, page_size: 20 })
const saleForm = reactive({})

async function loadSales() {
  loading.sales = true
  try {
    const res = await api.getSales(saleFilters)
    saleList.value = res.data?.list || []
    saleTotal.value = res.data?.pagination?.total || 0
  } catch (e) { ElMessage.error('加载销售订单失败') }
  loading.sales = false
}

function openSaleDialog(row = null) {
  if (row) Object.assign(saleForm, { ...row, id: row.id })
  else Object.keys(saleForm).forEach(k => delete saleForm[k])
  dialogs.sale = true
}

async function saveSale() {
  try {
    if (saleForm.id) await api.updateSale(saleForm.id, saleForm)
    else await api.createSale(saleForm)
    ElMessage.success('保存成功')
    dialogs.sale = false
    loadSales()
  } catch (e) { ElMessage.error('保存失败') }
}

async function deleteSale(row) {
  try {
    await ElMessageBox.confirm('确定删除该订单？', '提示', { type: 'warning' })
    await api.deleteSale(row.id)
    ElMessage.success('删除成功')
    loadSales()
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

// 采购
const purchaseList = ref([])
const purchaseTotal = ref(0)
const purchaseFilters = reactive({ supplier_name: '', page: 1, page_size: 20 })
const purchaseForm = reactive({})

async function loadPurchases() {
  loading.purchases = true
  try {
    const res = await api.getPurchases(purchaseFilters)
    purchaseList.value = res.data?.list || []
    purchaseTotal.value = res.data?.pagination?.total || 0
  } catch (e) { ElMessage.error('加载采购订单失败') }
  loading.purchases = false
}

function openPurchaseDialog(row = null) {
  if (row) Object.assign(purchaseForm, { ...row, id: row.id })
  else Object.keys(purchaseForm).forEach(k => delete purchaseForm[k])
  dialogs.purchase = true
}

async function savePurchase() {
  try {
    if (purchaseForm.id) await api.updatePurchase(purchaseForm.id, purchaseForm)
    else await api.createPurchase(purchaseForm)
    ElMessage.success('保存成功')
    dialogs.purchase = false
    loadPurchases()
  } catch (e) { ElMessage.error('保存失败') }
}

async function deletePurchase(row) {
  try {
    await ElMessageBox.confirm('确定删除该订单？', '提示', { type: 'warning' })
    await api.deletePurchase(row.id)
    ElMessage.success('删除成功')
    loadPurchases()
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

// 加载基础下拉数据
async function loadBaseData() {
  try {
    const [breeds, houses, batches] = await Promise.all([
      api.getBreeds({ page: 1, page_size: 100 }),
      api.getHouses({ page: 1, page_size: 100 }),
      api.getBatches({ page: 1, page_size: 100 })
    ])
    allBreeds.value = breeds.data?.list || []
    allHouses.value = houses.data?.list || []
    allBatches.value = batches.data?.list || []
  } catch (e) { console.error('加载基础数据失败', e) }
}

onMounted(() => {
  loadBreeds()
  loadHouses()
  loadBatches()
  loadIndividuals()
  loadOperations()
  loadHealth()
  loadSales()
  loadPurchases()
  loadBaseData()
})

watch(activeTab, (tab) => {
  if (tab === 'batches' || tab === 'individuals' || tab === 'operations') loadBaseData()
})
</script>

<style scoped>
.data-management {
  padding: 20px;
}
.toolbar {
  margin-bottom: 16px;
}
.mgmt-tabs {
  margin-top: 16px;
}
</style>
