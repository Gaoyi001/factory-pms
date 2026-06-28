<template>
  <div>
    <div class="table-toolbar">
      <div class="left">
        <el-button type="primary" @click="showForm()">
          <el-icon><Plus /></el-icon> 新建实验
        </el-button>
        <el-select v-model="filter.status" placeholder="实验状态" clearable style="width:130px" @change="onFilterChange">
          <el-option v-for="s in EXPERIMENT_STATUS_OPTS" :key="s.value" :label="s.label" :value="s.value" />
        </el-select>
        <el-select v-model="filter.exp_type" placeholder="实验类型" clearable style="width:130px" @change="onFilterChange">
          <el-option v-for="t in EXPERIMENT_TYPE_OPTS" :key="t.value" :label="t.label" :value="t.value" />
        </el-select>
        <el-select v-model="filter.project_id" placeholder="所属项目" clearable filterable style="width:160px" @change="onFilterChange">
          <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-date-picker v-model="filter.date_range" type="daterange" range-separator="至"
          start-placeholder="计划开始" end-placeholder="计划结束" style="width:240px"
          value-format="YYYY-MM-DD" @change="onFilterChange" />
      </div>
      <div class="right">
        <el-input v-model="filter.keyword" placeholder="搜索编号/名称" clearable style="width:200px" @keyup.enter="load">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button @click="load">查询</el-button>
      </div>
    </div>

    <el-table :data="tableData.items" v-loading="loading" stripe size="small" empty-text="暂无实验">
      <el-table-column prop="code" label="实验编号" width="160" />
      <el-table-column prop="name" label="实验名称" min-width="180" show-overflow-tooltip />
      <el-table-column prop="exp_type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ typeLabel(row.exp_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="设计师" width="100">
        <template #default="{ row }">{{ row.designer_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="执行人" width="100">
        <template #default="{ row }">{{ row.executor_name || '-' }}</template>
      </el-table-column>
      <el-table-column prop="plan_start" label="计划开始" width="110" />
      <el-table-column prop="plan_end" label="计划结束" width="110" />
      <el-table-column label="操作" width="360" fixed="right">
        <template #default="{ row }">
          <el-button link type="success" @click="showRecords(row)">记录</el-button>
          <el-dropdown link @command="(cmd: string) => handleStatusAction(row, cmd)" style="margin: 0 4px">
            <el-button link type="warning">状态<el-icon style="margin-left:2px"><ArrowDown /></el-icon></el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="start" :disabled="row.status !== 'draft'">开始</el-dropdown-item>
                <el-dropdown-item command="complete" :disabled="row.status === 'completed' || row.status === 'cancelled'">完成</el-dropdown-item>
                <el-dropdown-item command="cancel" :disabled="row.status === 'completed' || row.status === 'cancelled'">取消</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-tooltip :content="row.status !== 'in_progress' ? '请先将实验状态切换为进行中' : '温漂测试'" placement="top" :disabled="row.status === 'in_progress'">
            <span><el-button link type="primary" :disabled="row.status !== 'in_progress'" @click="goTcrTest(row)">温漂</el-button></span>
          </el-tooltip>
          <el-tooltip :content="row.status !== 'in_progress' ? '请先将实验状态切换为进行中' : '温升测试'" placement="top" :disabled="row.status === 'in_progress'">
            <span><el-button link type="primary" :disabled="row.status !== 'in_progress'" @click="goTempRiseTest(row)">温升</el-button></span>
          </el-tooltip>
          <el-button link type="primary" @click="showForm(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size"
      :total="tableData.total" layout="total, sizes, prev, pager, next"
      @current-change="load" @size-change="onPageSizeChange"
      style="margin-top:16px;justify-content:flex-end" />

    <!-- 新建/编辑实验对话框 -->
    <el-dialog v-model="formVisible" :title="formMode === 'create' ? '新建实验' : '编辑实验'" width="720px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="实验名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="所属项目">
          <el-select v-model="form.project_id" placeholder="请选择" style="width:100%">
            <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="实验类型">
          <el-select v-model="form.exp_type" style="width:100%">
            <el-option v-for="t in EXPERIMENT_TYPE_OPTS" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-tag :type="statusTag(form.status)" size="default">{{ statusLabel(form.status) }}</el-tag>
          <span style="color:#909399;font-size:12px;margin-left:8px">状态变更请通过列表"状态"下拉操作</span>
        </el-form-item>
        <el-form-item label="实验描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="计划周期">
          <el-date-picker v-model="form.plan_range" type="daterange" range-separator="至"
            start-placeholder="开始日期" end-placeholder="结束日期" style="width:100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="参数模板">
          <div style="width:100%">
            <el-button size="small" @click="addParam">
              <el-icon><Plus /></el-icon> 添加参数
            </el-button>
            <el-table :data="form.param_template" size="small" style="margin-top:8px" empty-text="暂无参数">
              <el-table-column label="参数名" width="160">
                <template #default="{ row }"><el-input v-model="row.name" size="small" /></template>
              </el-table-column>
              <el-table-column label="单位" width="100">
                <template #default="{ row }"><el-input v-model="row.unit" size="small" /></template>
              </el-table-column>
              <el-table-column label="默认值" width="120">
                <template #default="{ row }"><el-input v-model="row.default" size="small" /></template>
              </el-table-column>
              <el-table-column label="下限" width="100">
                <template #default="{ row }"><el-input-number v-model="row.min" size="small" controls-position="right" style="width:90px" /></template>
              </el-table-column>
              <el-table-column label="上限" width="100">
                <template #default="{ row }"><el-input-number v-model="row.max" size="small" controls-position="right" style="width:90px" /></template>
              </el-table-column>
              <el-table-column label="操作" width="80">
                <template #default="{ $index }">
                  <el-button link type="danger" size="small" @click="form.param_template.splice($index, 1)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 实验记录管理对话框 -->
    <el-dialog v-model="recordsVisible" :title="`实验记录 - ${currentExp?.name || ''}`" width="1000px" top="5vh">
      <!-- 记录筛选栏 -->
      <div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
        <el-input v-model="recordFilter.batch_no" placeholder="批次号" clearable size="small" style="width:130px" @keyup.enter="loadRecords" />
        <el-input v-model="recordFilter.sample_code" placeholder="样品编号" clearable size="small" style="width:130px" @keyup.enter="loadRecords" />
        <el-select v-model="recordFilter.conclusion" placeholder="结论" clearable size="small" style="width:120px" @change="loadRecords">
          <el-option v-for="c in CONCLUSION_OPTS" :key="c.value" :label="c.label" :value="c.value" />
        </el-select>
        <el-select v-model="recordFilter.is_abnormal" placeholder="异常" clearable size="small" style="width:100px" @change="loadRecords">
          <el-option label="仅异常" :value="true" />
          <el-option label="仅正常" :value="false" />
        </el-select>
        <el-date-picker v-model="recordFilter.date_range" type="daterange" range-separator="至"
          start-placeholder="开始" end-placeholder="结束" size="small" style="width:220px"
          value-format="YYYY-MM-DD" @change="loadRecords" />
        <el-button size="small" @click="loadRecords">查询</el-button>
        <el-button size="small" @click="resetRecordFilter">重置</el-button>
      </div>
      <!-- 操作栏 -->
      <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
        <div style="display:flex;align-items:center;gap:12px">
          <span style="color:#909399;font-size:13px">共 {{ recordsTotal }} 条记录</span>
          <el-tag v-if="records.length" size="small" :type="recordsSummaryTag">
            {{ recordsSummaryText }}
          </el-tag>
        </div>
        <div>
          <el-button type="danger" size="small" :disabled="!selectedRecordIds.length" @click="handleBatchDeleteRecords">
            批量删除{{ selectedRecordIds.length ? `(${selectedRecordIds.length})` : '' }}
          </el-button>
          <el-button size="small" :loading="exporting" @click="handleExportRecords">
            <el-icon><Download /></el-icon> 导出 Excel
          </el-button>
          <el-button type="primary" size="small" @click="showRecordForm()">
            <el-icon><Plus /></el-icon> 新增记录
          </el-button>
        </div>
      </div>
      <el-table :data="records" size="small" empty-text="暂无记录" border :row-class-name="recordRowClass"
        v-loading="recordsLoading" @selection-change="onRecordSelectionChange">
        <el-table-column type="selection" width="42" fixed="left" />
        <el-table-column label="#" type="index" width="45" fixed="left" />
        <el-table-column label="测试类型" width="90">
          <template #default="{ row }">
            <el-tag v-if="getTestType(row) === 'tcr'" type="warning" size="small" effect="plain">温漂</el-tag>
            <el-tag v-else-if="getTestType(row) === 'temp_rise'" type="danger" size="small" effect="plain">温升</el-tag>
            <el-tag v-else-if="getTestType(row) === 'aecq200'" type="primary" size="small" effect="dark">AEC-Q200</el-tag>
            <el-tag v-else-if="getTestType(row) === 'custom'" type="success" size="small" effect="dark">自定义</el-tag>
            <el-tag v-else type="info" size="small" effect="plain">常规</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="batch_no" label="批次号" width="120" show-overflow-tooltip>
          <template #default="{ row }">{{ row.batch_no || '-' }}</template>
        </el-table-column>
        <el-table-column prop="sample_code" label="样品编号" width="120" show-overflow-tooltip>
          <template #default="{ row }">{{ row.sample_code || '-' }}</template>
        </el-table-column>
        <el-table-column label="执行人" width="90">
          <template #default="{ row }">{{ row.executor_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="executed_at" label="执行日期" width="110" />
        <el-table-column label="结果摘要" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.result_summary">{{ row.result_summary }}</span>
            <span v-else style="color:#c0c4cc">{{ getResultPreview(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="结论" width="110" align="center">
          <template #default="{ row }">
            <div style="display:flex;flex-direction:column;gap:4px;align-items:center">
              <el-tag :type="conclusionTag(row.conclusion)" size="small" effect="dark">{{ conclusionLabel(row.conclusion) }}</el-tag>
              <el-tag v-if="row.is_abnormal" type="danger" size="small">异常</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="附件" width="60" align="center">
          <template #default="{ row }">
            <el-badge :value="row.attachment_count || 0" :hidden="!row.attachment_count" type="primary">
              <el-icon><Paperclip /></el-icon>
            </el-badge>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row: rec }">
            <el-button v-if="getTestType(rec) !== 'normal'" link type="success" size="small" @click="showPreview(rec)">预览</el-button>
            <el-button link size="small" @click="showRecordForm(rec)">编辑</el-button>
            <el-button link type="primary" size="small" @click="showAttachments(rec)">附件</el-button>
            <el-button link type="danger" size="small" @click="handleDeleteRecord(rec)">删除</el-button>
          </template>
        </el-table-column>
        <!--
          注：附件管理已整合到记录编辑表单中，「附件」按钮复用 showRecordForm 打开编辑模式。
          独立的 attachmentsVisible 对话框已废弃。
        -->
      </el-table>
      <el-pagination v-model:current-page="recordPagination.page" v-model:page-size="recordPagination.page_size"
      :total="recordsTotal" layout="total, sizes, prev, pager, next"
      @current-change="loadRecords" @size-change="onRecordPageSizeChange"
      style="margin-top:12px;justify-content:flex-end" />
    </el-dialog>

    <!-- 实验记录表单对话框 -->
    <el-dialog v-model="recordFormVisible" :title="recordFormMode === 'create' ? '新增实验记录' : '编辑实验记录'" width="900px" top="5vh">
      <el-form :model="recordForm" label-width="100px">
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="批次号">
              <el-input v-model="recordForm.batch_no" placeholder="例如 B20260627-01" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="样品编号">
              <el-input v-model="recordForm.sample_code" placeholder="例如 S-001" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="执行日期">
              <el-date-picker v-model="recordForm.executed_at" type="date" style="width:100%" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="执行人">
              <el-select v-model="recordForm.executor_id" placeholder="留空则默认为当前用户" clearable style="width:100%">
                <el-option v-for="u in userOptions" :key="u.id" :label="u.name" :value="u.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="结论">
              <el-select v-model="recordForm.conclusion" clearable style="width:100%">
                <el-option v-for="c in CONCLUSION_OPTS" :key="c.value" :label="c.label" :value="c.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="是否异常">
              <el-switch v-model="recordForm.is_abnormal" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 测试项目与参数 -->
        <el-divider content-position="left">测试项目与参数</el-divider>

        <el-form-item label="测试项目">
          <div style="width:100%">
            <!-- 温漂/温升记录：只读提示 -->
            <el-alert v-if="isStructuredTestRecord" type="warning" :closable="false" style="margin-bottom:8px">
              <template #title>
                该记录由{{ recordForm.test_type === 'tcr' ? '温漂' : '温升' }}测试页生成，含结构化采样数据，
                此处仅展示不可编辑。如需修改请通过专用测试页重新录入。
              </template>
            </el-alert>

            <!-- 选择测试项模式：通用 / AEC-Q200 / 自定义 -->
            <template v-if="!isStructuredTestRecord">
              <el-radio-group v-model="recordForm.test_type" style="margin-bottom:8px">
                <el-radio-button label="">通用记录</el-radio-button>
                <el-radio-button label="aecq200">AEC-Q200 可靠性测试</el-radio-button>
                <el-radio-button label="custom">自定义测试项</el-radio-button>
              </el-radio-group>

              <!-- AEC-Q200 测试项选择 -->
              <div v-if="isAecqRecord">
                <el-select v-model="recordForm.aecq_item_code" placeholder="选择测试项（温度循环/高温存储/振动...）"
                  filterable style="width:100%;margin-bottom:8px" @change="onAecqItemChange">
                  <el-option-group v-for="cat in ['temperature','mechanical','solder','electrical']" :key="cat" :label="AECQ_CATEGORY_LABEL[cat as keyof typeof AECQ_CATEGORY_LABEL]">
                    <el-option v-for="item in AECQ200_TEST_ITEMS.filter(t => t.category === cat)" :key="item.code"
                      :label="`${item.code} - ${item.name}`" :value="item.code" />
                  </el-option-group>
                </el-select>
                <!-- 测试项说明 -->
                <el-alert v-if="currentAecqItem" type="info" :closable="false" style="margin-bottom:8px">
                  <template #title>
                    <el-tag :type="AECQ_CATEGORY_TAG[currentAecqItem.category] as any" size="small" style="margin-right:6px">
                      {{ AECQ_CATEGORY_LABEL[currentAecqItem.category] }}
                    </el-tag>
                    <span style="font-weight:600">{{ currentAecqItem.code }} · {{ currentAecqItem.name }}</span>
                    <span style="margin-left:8px;color:#909399;font-size:12px">{{ currentAecqItem.description }}</span>
                  </template>
                </el-alert>
              </div>

              <!-- 自定义测试项选择 -->
              <div v-if="isCustomRecord">
                <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
                  <el-select v-model="recordForm.custom_item_id" placeholder="选择已保存的测试项（可复用）"
                    filterable clearable style="flex:1" @change="onCustomItemChange">
                    <el-option v-for="t in customTestItems" :key="t.id"
                      :label="`${t.name}${t.description ? ' - ' + t.description : ''}`" :value="t.id" />
                  </el-select>
                  <el-button @click="openCustomItemManager">
                    <el-icon><Setting /></el-icon> 管理测试项
                  </el-button>
                </div>
                <el-alert v-if="currentCustomItem" type="info" :closable="false" style="margin-bottom:8px">
                  <template #title>
                    <el-tag size="small" type="info" style="margin-right:6px">自定义</el-tag>
                    <span style="font-weight:600">{{ currentCustomItem.name }}</span>
                    <span v-if="currentCustomItem.description" style="margin-left:8px;color:#909399;font-size:12px">{{ currentCustomItem.description }}</span>
                    <div v-if="currentCustomItem.judge_rule" style="margin-top:4px;color:#909399;font-size:12px">
                      <b>判定规则：</b>{{ currentCustomItem.judge_rule }}
                    </div>
                  </template>
                </el-alert>
              </div>
            </template>
          </div>
        </el-form-item>

        <!-- 参数录入 -->
        <el-form-item v-if="!isStructuredTestRecord" label="测试参数">
          <div style="width:100%">
            <!-- AEC-Q200 参数表单（按测试项定义渲染） -->
            <template v-if="isAecqRecord && currentAecqItem">
              <el-row :gutter="12">
                <el-col v-for="p in currentAecqItem.params" :key="p.key" :span="8">
                  <el-form-item :label="p.name" label-width="100px">
                    <el-input-number v-if="p.input_type !== 'select' && p.input_type !== 'text'"
                      v-model="recordForm.aecq_params[p.key]" :precision="2" :step="1" :min="p.min ?? undefined" :max="p.max ?? undefined"
                      controls-position="right" size="default" style="width:100%" />
                    <el-select v-else-if="p.input_type === 'select'" v-model="recordForm.aecq_params[p.key]" style="width:100%">
                      <el-option v-for="opt in (p.options || [])" :key="opt" :label="opt" :value="opt" />
                    </el-select>
                    <el-input v-else v-model="recordForm.aecq_params[p.key]" placeholder="输入" />
                    <span v-if="p.unit" style="margin-left:6px;color:#909399;font-size:12px">{{ p.unit }}</span>
                    <div v-if="p.min != null || p.max != null" style="color:#909399;font-size:11px;margin-top:2px">
                      范围: {{ p.min ?? '-∞' }} ~ {{ p.max ?? '+∞' }}
                    </div>
                  </el-form-item>
                </el-col>
              </el-row>
            </template>

            <!-- 自定义测试项参数表单 -->
            <template v-else-if="isCustomRecord && currentCustomItem">
              <el-alert v-if="!currentCustomItem.params.length" type="info" :closable="false">
                <template #title>该测试项未定义参数，可直接录入结果数据</template>
              </el-alert>
              <el-row v-else :gutter="12">
                <el-col v-for="p in currentCustomItem.params" :key="p.key" :span="8">
                  <el-form-item :label="p.name" label-width="100px">
                    <el-input-number v-if="p.input_type !== 'select' && p.input_type !== 'text'"
                      v-model="recordForm.custom_params[p.key]" :precision="2" :step="1" :min="p.min ?? undefined" :max="p.max ?? undefined"
                      controls-position="right" size="default" style="width:100%" />
                    <el-select v-else-if="p.input_type === 'select'" v-model="recordForm.custom_params[p.key]" style="width:100%">
                      <el-option v-for="opt in (p.options || [])" :key="opt" :label="opt" :value="opt" />
                    </el-select>
                    <el-input v-else v-model="recordForm.custom_params[p.key]" placeholder="输入" />
                    <span v-if="p.unit" style="margin-left:6px;color:#909399;font-size:12px">{{ p.unit }}</span>
                    <div v-if="p.min != null || p.max != null" style="color:#909399;font-size:11px;margin-top:2px">
                      范围: {{ p.min ?? '-∞' }} ~ {{ p.max ?? '+∞' }}
                    </div>
                  </el-form-item>
                </el-col>
              </el-row>
            </template>

            <!-- 自定义测试项未选择时的引导 -->
            <template v-else-if="isCustomRecord && !currentCustomItem">
              <el-alert type="warning" :closable="false">
                <template #title>
                  请在上方下拉选择已保存的测试项，或点击「管理测试项」新建一个。新建后即可使用结构化参数与样品表格录入。
                </template>
              </el-alert>
            </template>

            <!-- 通用参数表格（无 AEC-Q200 / 自定义 测试项时） -->
            <template v-else-if="!isAecqRecord && !isCustomRecord">
              <div v-if="recordForm.param_rows.length" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                <el-tag size="small" type="info">基于实验参数模板，共 {{ recordForm.param_rows.length }} 项</el-tag>
                <el-button text size="small" @click="resetParamRows">恢复默认</el-button>
              </div>
              <el-table v-if="recordForm.param_rows.length" :data="recordForm.param_rows" size="small" border :row-class-name="paramRowClass">
                <el-table-column label="#" type="index" width="42" />
                <el-table-column label="参数名" width="160">
                  <template #default="{ row }">
                    <span style="font-weight:600">{{ row.name }}</span>
                    <el-tag v-if="row.unit" size="small" effect="plain" style="margin-left:4px">{{ row.unit }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="数值" min-width="160">
                  <template #default="{ row }">
                    <el-input v-model="row.value" size="small"
                      :placeholder="row.default != null ? `默认 ${row.default}` : '输入数值'"
                      :class="{ 'param-out': isParamOutOfRange(row) }" />
                  </template>
                </el-table-column>
                <el-table-column label="范围" width="160">
                  <template #default="{ row }">
                    <span v-if="row.min != null || row.max != null" style="color:#909399;font-size:12px">
                      <el-icon v-if="isParamOutOfRange(row)" style="color:#f56c6c;vertical-align:middle"><WarningFilled /></el-icon>
                      {{ row.min != null ? row.min : '-∞' }} ~ {{ row.max != null ? row.max : '+∞' }}
                    </span>
                    <span v-else style="color:#c0c4cc;font-size:12px">无限制</span>
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag v-if="row.value === '' || row.value == null" size="small" type="info" effect="plain">未填</el-tag>
                    <el-tag v-else-if="isParamOutOfRange(row)" size="small" type="danger" effect="dark">超限</el-tag>
                    <el-tag v-else size="small" type="success" effect="dark">合格</el-tag>
                  </template>
                </el-table-column>
              </el-table>
              <el-input v-else v-model="recordForm.param_values_text" type="textarea" :rows="3"
                placeholder='无参数模板，可输入 JSON，例如：{"温度": 185, "压力": 12.5}' />
            </template>
          </div>
        </el-form-item>

        <!-- 温漂/温升只读参数 -->
        <el-form-item v-if="isStructuredTestRecord" label="参数值">
          <el-input v-model="recordForm.param_values_text" type="textarea" :rows="6" readonly />
        </el-form-item>

        <!-- 结果数据 -->
        <el-divider content-position="left">结果数据</el-divider>

        <!-- AEC-Q200 批量样品表格 -->
        <el-form-item v-if="isAecqRecord && currentAecqItem" label="样品结果">
          <div style="width:100%">
            <!-- 操作栏 -->
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <div style="display:flex;align-items:center;gap:12px">
                <span style="color:#606266;font-size:13px">共 {{ aecqStats.total }} 个样品</span>
                <el-tag v-if="aecqStats.total" size="small" :type="aecqStats.failed ? 'danger' : 'success'">
                  合格 {{ aecqStats.passed }} / 失效 {{ aecqStats.failed }}
                  <span v-if="aecqStats.pending"> / 待判 {{ aecqStats.pending }}</span>
                </el-tag>
                <el-tag v-if="aecqStats.total && aecqStats.pending === 0" size="small" effect="dark"
                  :type="aecqStats.auto_conclusion === 'pass' ? 'success' : 'danger'">
                  合格率 {{ aecqStats.pass_rate }}%
                </el-tag>
              </div>
              <div>
                <el-button size="small" @click="addAecqSample"><el-icon><Plus /></el-icon> 追加样品</el-button>
                <el-button size="small" @click="batchAddAecqSamples">批量生成</el-button>
              </div>
            </div>
            <!-- 自动判定规则提示 -->
            <el-alert type="info" :closable="false" style="margin-bottom:8px">
              <template #title>
                <span style="font-size:12px">判定规则：{{ currentAecqItem.judge_rule }}</span>
              </template>
            </el-alert>
            <!-- 样品表格 -->
            <el-table :data="recordForm.aecq_samples" size="small" border max-height="360" empty-text="请追加或批量生成样品">
              <el-table-column label="#" type="index" width="42" fixed="left" />
              <el-table-column v-for="col in currentAecqItem.sample_columns" :key="col.key"
                :label="col.unit ? `${col.label} (${col.unit})` : col.label" :width="col.width">
                <template #default="{ row }">
                  <!-- 自动计算列：只读 -->
                  <span v-if="col.auto_calc" style="font-weight:600">
                    {{ row[col.key] != null && row[col.key] !== '' ? row[col.key] : '-' }}
                  </span>
                  <!-- 下拉选择列 -->
                  <el-select v-else-if="col.input_type === 'select'" v-model="row[col.key]" size="small"
                    :placeholder="`选择`" style="width:100%"
                    @change="onAecqSampleInput(row, col.key)">
                    <el-option v-for="opt in (col.options || [])" :key="opt" :label="opt" :value="opt" />
                  </el-select>
                  <!-- 数字输入列 -->
                  <el-input-number v-else-if="col.input_type === 'number'" v-model="row[col.key]" :precision="4" :step="0.01"
                    controls-position="right" size="small" style="width:100%"
                    @input="onAecqSampleInput(row, col.key)" />
                  <!-- 文本输入列（含样品编号） -->
                  <el-input v-else v-model="row[col.key]" size="small" :placeholder="col.key === 'code' ? 'S-001' : ''"
                    @input="onAecqSampleInput(row, col.key)" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="70" fixed="right">
                <template #default="{ $index }">
                  <el-button link type="danger" size="small" @click="recordForm.aecq_samples.splice($index, 1)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <!-- 自动判定按钮 -->
            <div style="margin-top:8px;display:flex;align-items:center;gap:12px">
              <el-button size="small" type="primary" plain :disabled="!aecqStats.total || aecqStats.pending > 0"
                @click="applyAutoConclusion">
                应用自动判定（{{ aecqStats.total && aecqStats.pending === 0 ? aecqStats.auto_conclusion === 'pass' ? '通过' : '失败' : '需全部判定' }}）
              </el-button>
              <span style="color:#909399;font-size:12px">系统建议：{{ conclusionLabel(aecqStats.auto_conclusion) }}</span>
            </div>
          </div>
        </el-form-item>

        <!-- 自定义测试项批量样品表格 -->
        <el-form-item v-if="isCustomRecord && currentCustomItem" label="样品结果">
          <div style="width:100%">
            <!-- 操作栏 -->
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <div style="display:flex;align-items:center;gap:12px">
                <span style="color:#606266;font-size:13px">共 {{ customStats.total }} 个样品</span>
                <el-tag v-if="customStats.total && hasCustomResultColumn" size="small" :type="customStats.failed ? 'danger' : 'success'">
                  合格 {{ customStats.passed }} / 失效 {{ customStats.failed }}
                  <span v-if="customStats.pending"> / 待判 {{ customStats.pending }}</span>
                </el-tag>
                <el-tag v-if="customStats.total && customStats.pending === 0 && hasCustomResultColumn" size="small" effect="dark"
                  :type="customStats.auto_conclusion === 'pass' ? 'success' : 'danger'">
                  合格率 {{ customStats.pass_rate }}%
                </el-tag>
              </div>
              <div>
                <el-button size="small" @click="addCustomSample"><el-icon><Plus /></el-icon> 追加样品</el-button>
                <el-button size="small" @click="batchAddCustomSamples">批量生成</el-button>
              </div>
            </div>
            <!-- 判定规则提示 -->
            <el-alert v-if="currentCustomItem.judge_rule" type="info" :closable="false" style="margin-bottom:8px">
              <template #title>
                <span style="font-size:12px">判定规则：{{ currentCustomItem.judge_rule }}</span>
              </template>
            </el-alert>
            <el-alert v-else-if="!currentCustomItem.sample_columns.length" type="warning" :closable="false" style="margin-bottom:8px">
              <template #title>
                <span style="font-size:12px">该测试项未定义结果列，请到「管理测试项」中添加列定义后再录入结果</span>
              </template>
            </el-alert>
            <!-- 样品表格 -->
            <el-table :data="recordForm.custom_samples" size="small" border max-height="360" empty-text="请追加或批量生成样品">
              <el-table-column label="#" type="index" width="42" fixed="left" />
              <el-table-column v-for="col in currentCustomItem.sample_columns" :key="col.key"
                :label="col.unit ? `${col.label} (${col.unit})` : col.label" :width="col.width">
                <template #default="{ row }">
                  <!-- 自动计算列：只读 -->
                  <span v-if="col.auto_calc" style="font-weight:600">
                    {{ row[col.key] != null && row[col.key] !== '' ? row[col.key] : '-' }}
                  </span>
                  <!-- 下拉选择列 -->
                  <el-select v-else-if="col.input_type === 'select'" v-model="row[col.key]" size="small"
                    placeholder="选择" style="width:100%"
                    @change="onCustomSampleInput(row, col.key)">
                    <el-option v-for="opt in (col.options || [])" :key="opt" :label="opt" :value="opt" />
                  </el-select>
                  <!-- 数字输入列 -->
                  <el-input-number v-else-if="col.input_type === 'number'" v-model="row[col.key]" :precision="4" :step="0.01"
                    controls-position="right" size="small" style="width:100%"
                    @input="onCustomSampleInput(row, col.key)" />
                  <!-- 文本输入列 -->
                  <el-input v-else v-model="row[col.key]" size="small" :placeholder="col.key === 'code' ? 'S-001' : ''"
                    @input="onCustomSampleInput(row, col.key)" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="70" fixed="right">
                <template #default="{ $index }">
                  <el-button link type="danger" size="small" @click="recordForm.custom_samples.splice($index, 1)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <!-- 自动判定按钮（仅当存在 result 列） -->
            <div v-if="hasCustomResultColumn" style="margin-top:8px;display:flex;align-items:center;gap:12px">
              <el-button size="small" type="primary" plain :disabled="!customStats.total || customStats.pending > 0"
                @click="applyCustomAutoConclusion">
                应用自动判定（{{ customStats.total && customStats.pending === 0 ? (customStats.auto_conclusion === 'pass' ? '通过' : '失败') : '需全部判定' }}）
              </el-button>
              <span style="color:#909399;font-size:12px">系统建议：{{ conclusionLabel(customStats.auto_conclusion) }}</span>
            </div>
          </div>
        </el-form-item>

        <!-- 通用结果数据：键值对录入（仅通用记录模式） -->
        <el-form-item v-if="!isAecqRecord && !isStructuredTestRecord && !isCustomRecord" label="结果数据">
          <div style="width:100%">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
              <el-tag size="small" type="info">键值对形式录入，提交时自动转为 JSON</el-tag>
              <div>
                <el-button text size="small" @click="addResultRow"><el-icon><Plus /></el-icon> 添加</el-button>
                <el-button text size="small" @click="toggleResultJsonMode">
                  {{ recordForm.result_use_json ? '切换为表格' : '切换为 JSON' }}
                </el-button>
              </div>
            </div>
            <el-table v-if="!recordForm.result_use_json && recordForm.result_rows.length" :data="recordForm.result_rows" size="small" border>
              <el-table-column label="键名" min-width="160">
                <template #default="{ row }">
                  <el-input v-model="row.key" size="small" placeholder="例如 拉力" />
                </template>
              </el-table-column>
              <el-table-column label="数值" min-width="140">
                <template #default="{ row }">
                  <el-input v-model="row.value" size="small" placeholder="例如 120" />
                </template>
              </el-table-column>
              <el-table-column label="单位" width="100">
                <template #default="{ row }">
                  <el-input v-model="row.unit" size="small" placeholder="可选" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center">
                <template #default="{ $index }">
                  <el-button link type="danger" size="small" @click="recordForm.result_rows.splice($index, 1)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-input v-else v-model="recordForm.result_data_text" type="textarea" :rows="3"
              placeholder='JSON 格式，例如：{"拉力": 120, "电阻": 0.025}' />
            <div v-if="!recordForm.result_use_json && !recordForm.result_rows.length" style="color:#c0c4cc;font-size:12px;text-align:center;padding:8px">
              暂无结果数据，点击右上角"添加"录入
            </div>
          </div>
        </el-form-item>

        <!-- 温漂/温升只读结果 -->
        <el-form-item v-if="isStructuredTestRecord" label="结果数据">
          <el-input v-model="recordForm.result_data_text" type="textarea" :rows="6" readonly />
        </el-form-item>

        <el-form-item label="结果摘要">
          <el-input v-model="recordForm.result_summary" type="textarea" :rows="2" placeholder="可选，留空将根据结果数据自动生成" />
        </el-form-item>

        <el-form-item v-if="recordForm.is_abnormal" label="异常描述">
          <el-input v-model="recordForm.abnormal_desc" type="textarea" :rows="2" placeholder="请描述异常现象" />
        </el-form-item>

        <!-- 附件上传：编辑模式可上传，新建模式提示先保存 -->
        <el-form-item label="附件">
          <div style="width:100%">
            <el-upload v-if="recordFormMode === 'edit'"
              drag action="#" :auto-upload="false" :show-file-list="false" :on-change="handleRecordAttachmentChange" style="margin-bottom:8px">
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
              <template #tip>
                <div class="el-upload__tip">单个文件最大 50MB，支持多文件</div>
              </template>
            </el-upload>
            <el-alert v-else type="warning" :closable="false" style="margin-bottom:8px">
              <template #title>请先保存记录后再上传附件</template>
            </el-alert>
            <el-table v-if="recordForm.attachments.length" :data="recordForm.attachments" size="small" empty-text="暂无附件" v-loading="recordAttachmentLoading">
              <el-table-column prop="file_name" label="文件名" min-width="200" show-overflow-tooltip />
              <el-table-column label="大小" width="100">
                <template #default="{ row }">{{ formatFileSize(row.file_size) }}</template>
              </el-table-column>
              <el-table-column prop="uploaded_at" label="上传时间" width="170">
                <template #default="{ row }">{{ formatDateTime(row.uploaded_at) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="180" align="center">
                <template #default="{ row }">
                  <el-button link size="small" @click="handleDownloadAttachment(row, true)">预览</el-button>
                  <el-button link type="primary" size="small" @click="handleDownloadAttachment(row, false)">下载</el-button>
                  <el-button link type="danger" size="small" @click="handleDeleteRecordAttachment(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="recordFormVisible = false">取消</el-button>
        <el-button type="primary" :loading="recordSubmitting" @click="handleRecordSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 温漂/温升记录预览对话框 -->
    <el-dialog v-model="previewVisible" :title="previewTitle" width="1100px" top="5vh" destroy-on-close>
      <div v-loading="previewLoading">
        <el-descriptions v-if="previewRecord" :column="4" border size="small" style="margin-bottom:12px">
          <el-descriptions-item label="批次号">{{ previewRecord.batch_no || '-' }}</el-descriptions-item>
          <el-descriptions-item label="样品编号">{{ previewRecord.sample_code || '-' }}</el-descriptions-item>
          <el-descriptions-item label="执行人">{{ previewRecord.executor_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="执行日期">{{ previewRecord.executed_at || '-' }}</el-descriptions-item>
          <el-descriptions-item label="结论">
            <el-tag :type="conclusionTag(previewRecord.conclusion)" size="small" effect="dark">{{ conclusionLabel(previewRecord.conclusion) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="是否异常">
            <el-tag v-if="previewRecord.is_abnormal" type="danger" size="small">异常</el-tag>
            <el-tag v-else type="success" size="small">正常</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="附件数">{{ previewRecord.attachment_count || previewRecord.attachments?.length || 0 }}</el-descriptions-item>
        </el-descriptions>

        <!-- 温漂预览：采样表 + 曲线 -->
        <template v-if="previewType === 'tcr'">
          <el-row :gutter="12">
            <el-col :span="10">
              <el-card shadow="never">
                <template #header><span style="font-weight:600">温度-阻值采样表</span></template>
                <el-table :data="tcrPreviewPoints" size="small" border max-height="380">
                  <el-table-column label="温度 (°C)" width="100" prop="temperature" />
                  <el-table-column label="阻值 (Ω)" width="120">
                    <template #default="{ row }">{{ row.resistance != null ? Number(row.resistance).toFixed(6) : '-' }}</template>
                  </el-table-column>
                  <el-table-column label="ΔT (°C)" width="90">
                    <template #default="{ row }">{{ (row.temperature - tcrPreviewRefTemp).toFixed(1) }}</template>
                  </el-table-column>
                  <el-table-column label="TCR (ppm/°C)">
                    <template #default="{ row }">
                      <span v-if="row.tcr != null" :style="{ color: tcrColorPreview(row.tcr), fontWeight: 600 }">
                        {{ Number(row.tcr).toFixed(2) }}
                      </span>
                      <span v-else>-</span>
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
            <el-col :span="14">
              <el-card shadow="never">
                <template #header><span style="font-weight:600">温度-阻值曲线</span></template>
                <div ref="previewChartRef" style="width:100%;height:380px"></div>
              </el-card>
            </el-col>
          </el-row>
        </template>

        <!-- 温升预览：参数表 + 汇总 -->
        <template v-else-if="previewType === 'temp_rise'">
          <el-row :gutter="12">
            <el-col :span="16">
              <el-card shadow="never">
                <template #header><span style="font-weight:600">功率-参数表</span></template>
                <el-table :data="tempRisePreviewPoints" size="small" border max-height="380">
                  <el-table-column label="#" type="index" width="42" />
                  <el-table-column label="功率 (W)" width="90" prop="power" />
                  <el-table-column label="电流 (A)" width="90" prop="current" />
                  <el-table-column label="电压 (mV)" width="100">
                    <template #default="{ row }">{{ row.voltage_mv ?? row.voltage ?? '-' }}</template>
                  </el-table-column>
                  <el-table-column label="阻值 (mΩ)" width="100">
                    <template #default="{ row }">{{ row.resistance_mohm ?? row.resistance ?? '-' }}</template>
                  </el-table-column>
                  <el-table-column label="本体温度" width="90">
                    <template #default="{ row }">{{ row.body_temp != null ? row.body_temp + '°C' : '-' }}</template>
                  </el-table-column>
                  <el-table-column label="温升 ΔT" width="90">
                    <template #default="{ row }">
                      <span v-if="row.temp_rise != null" :style="{ color: row.temp_rise > 80 ? '#f56c6c' : '#67c23a', fontWeight: 600 }">{{ row.temp_rise }}°C</span>
                      <span v-else>-</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="总热阻 (°C/W)" width="110">
                    <template #default="{ row }">{{ row.rth_core_to_ambient != null ? row.rth_core_to_ambient : '-' }}</template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="never">
                <template #header><span style="font-weight:600">汇总计算</span></template>
                <el-descriptions :column="1" border size="small">
                  <el-descriptions-item label="环境温度">{{ tempRisePreviewSummary.ambient_temp != null ? tempRisePreviewSummary.ambient_temp + ' °C' : '-' }}</el-descriptions-item>
                  <el-descriptions-item label="参考阻值">{{ tempRisePreviewSummary.ref_resistance != null ? tempRisePreviewSummary.ref_resistance + ' mΩ' : '-' }}</el-descriptions-item>
                  <el-descriptions-item label="测试点数">{{ tempRisePreviewPoints.length }}</el-descriptions-item>
                  <el-descriptions-item label="最大温升">
                    <span :style="{ color: (tempRisePreviewSummary.max_temp_rise ?? 0) > 80 ? '#f56c6c' : '#67c23a', fontWeight: 600 }">
                      {{ tempRisePreviewSummary.max_temp_rise != null ? tempRisePreviewSummary.max_temp_rise + ' °C' : '-' }}
                    </span>
                  </el-descriptions-item>
                  <el-descriptions-item label="最大热阻">{{ tempRisePreviewSummary.max_rth != null ? tempRisePreviewSummary.max_rth + ' °C/W' : '-' }}</el-descriptions-item>
                  <el-descriptions-item label="最大本体温度">{{ tempRisePreviewSummary.max_body_temp != null ? tempRisePreviewSummary.max_body_temp + ' °C' : '-' }}</el-descriptions-item>
                </el-descriptions>
              </el-card>
            </el-col>
          </el-row>
        </template>

        <!-- AEC-Q200 预览：测试项信息 + 样品结果表 -->
        <template v-else-if="previewType === 'aecq200'">
          <el-card shadow="never" style="margin-bottom:12px">
            <template #header>
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span style="font-weight:600">
                  {{ previewRecord?.param_values?.test_item_name || aecqPreviewItem?.name || 'AEC-Q200 测试项' }}
                </span>
                <el-tag v-if="aecqPreviewItem" size="small" :type="AECQ_CATEGORY_TAG[aecqPreviewItem.category]">
                  {{ AECQ_CATEGORY_LABEL[aecqPreviewItem.category] }}
                </el-tag>
              </div>
            </template>
            <el-descriptions :column="3" border size="small">
              <el-descriptions-item v-for="p in aecqPreviewItem?.params || []" :key="p.key" :label="p.name + (p.unit ? ` (${p.unit})` : '')">
                {{ previewRecord?.param_values?.params?.[p.key] ?? '-' }}
              </el-descriptions-item>
            </el-descriptions>
            <el-alert v-if="aecqPreviewItem?.judge_rule" type="info" :closable="false" style="margin-top:8px">
              <template #title>
                <span style="font-size:12px"><b>判定规则：</b>{{ aecqPreviewItem.judge_rule }}</span>
              </template>
            </el-alert>
          </el-card>

          <el-card shadow="never">
            <template #header>
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span style="font-weight:600">样品测试结果</span>
                <span style="color:#909399;font-size:12px">
                  总数 {{ previewRecord?.result_data?.total ?? aecqPreviewSamples.length }}
                  · 合格 {{ previewRecord?.result_data?.passed ?? 0 }}
                  · 失效 {{ previewRecord?.result_data?.failed ?? 0 }}
                  · 合格率 {{ previewRecord?.result_data?.pass_rate ?? 0 }}%
                </span>
              </div>
            </template>
            <el-table :data="aecqPreviewSamples" size="small" border max-height="420" empty-text="无样品数据">
              <el-table-column label="#" type="index" width="50" fixed="left" />
              <el-table-column
                v-for="col in aecqPreviewItem?.sample_columns || []"
                :key="col.key"
                :prop="col.key"
                :label="col.label + (col.unit ? ` (${col.unit})` : '')"
                :width="col.width || 120"
              >
                <template #default="{ row }">
                  <span v-if="col.key === 'result'">
                    <el-tag v-if="row.result === 'pass'" type="success" size="small">合格</el-tag>
                    <el-tag v-else-if="row.result === 'fail'" type="danger" size="small">失效</el-tag>
                    <el-tag v-else type="info" size="small">{{ row.result || '-' }}</el-tag>
                  </span>
                  <span v-else>{{ row[col.key] ?? '-' }}</span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </template>

        <!-- 自定义测试项预览：测试项信息 + 样品结果表 -->
        <template v-else-if="previewType === 'custom'">
          <el-card shadow="never" style="margin-bottom:12px">
            <template #header>
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span style="font-weight:600">
                  {{ previewRecord?.param_values?.custom_item_name || customPreviewItem?.name || '自定义测试项' }}
                </span>
                <el-tag size="small" type="success">自定义</el-tag>
              </div>
            </template>
            <el-descriptions :column="3" border size="small">
              <el-descriptions-item v-for="p in customPreviewSchema?.params || []" :key="p.key" :label="p.name + (p.unit ? ` (${p.unit})` : '')">
                {{ previewRecord?.param_values?.params?.[p.key] ?? '-' }}
              </el-descriptions-item>
            </el-descriptions>
            <el-alert v-if="customPreviewItem?.judge_rule || previewRecord?.param_values?.custom_judge_rule" type="info" :closable="false" style="margin-top:8px">
              <template #title>
                <span style="font-size:12px"><b>判定规则：</b>{{ customPreviewItem?.judge_rule || previewRecord?.param_values?.custom_judge_rule }}</span>
              </template>
            </el-alert>
          </el-card>

          <el-card shadow="never">
            <template #header>
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span style="font-weight:600">样品测试结果</span>
                <span style="color:#909399;font-size:12px">
                  总数 {{ previewRecord?.result_data?.total ?? customPreviewSamples.length }}
                  <template v-if="previewRecord?.result_data?.passed != null">
                    · 合格 {{ previewRecord?.result_data?.passed ?? 0 }}
                    · 失效 {{ previewRecord?.result_data?.failed ?? 0 }}
                    · 合格率 {{ previewRecord?.result_data?.pass_rate ?? 0 }}%
                  </template>
                </span>
              </div>
            </template>
            <el-table :data="customPreviewSamples" size="small" border max-height="420" empty-text="无样品数据">
              <el-table-column label="#" type="index" width="50" fixed="left" />
              <el-table-column
                v-for="col in customPreviewSchema?.sample_columns || []"
                :key="col.key"
                :prop="col.key"
                :label="col.label + (col.unit ? ` (${col.unit})` : '')"
                :width="col.width || 120"
              >
                <template #default="{ row }">
                  <span v-if="col.key === 'result'">
                    <el-tag v-if="row.result === 'pass'" type="success" size="small">合格</el-tag>
                    <el-tag v-else-if="row.result === 'fail'" type="danger" size="small">失效</el-tag>
                    <el-tag v-else type="info" size="small">{{ row.result || '-' }}</el-tag>
                  </span>
                  <span v-else>{{ row[col.key] ?? '-' }}</span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </template>

        <!-- 摘要 -->
        <el-card v-if="previewRecord?.result_summary" shadow="never" style="margin-top:12px">
          <template #header><span style="font-weight:600">结果摘要</span></template>
          <div style="white-space:pre-wrap">{{ previewRecord.result_summary }}</div>
        </el-card>
        <el-card v-if="previewRecord?.abnormal_desc" shadow="never" style="margin-top:12px">
          <template #header><span style="font-weight:600;color:#f56c6c">异常描述</span></template>
          <div style="white-space:pre-wrap;color:#f56c6c">{{ previewRecord.abnormal_desc }}</div>
        </el-card>
      </div>
    </el-dialog>

    <!-- 上传实验文档到知识库对话框（已移除：文档统一在记录里上传） -->

    <!-- 自定义测试项管理对话框 -->
    <el-dialog v-model="customMgrVisible" title="自定义测试项管理" width="900px" top="5vh">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <span style="color:#909399;font-size:13px">已保存 {{ customTestItems.length }} 个测试项，可在「通用记录 - 自定义测试项」中复用</span>
        <el-button type="primary" size="small" @click="openCustomItemEditor()">
          <el-icon><Plus /></el-icon> 新建测试项
        </el-button>
      </div>
      <el-table :data="customTestItems" size="small" border empty-text="暂无自定义测试项，点击右上角新建">
        <el-table-column label="名称" min-width="140">
          <template #default="{ row }">
            <span style="font-weight:600">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column label="描述" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.description || '-' }}</template>
        </el-table-column>
        <el-table-column label="参数数" width="80" align="center">
          <template #default="{ row }">{{ row.params?.length || 0 }}</template>
        </el-table-column>
        <el-table-column label="结果列数" width="90" align="center">
          <template #default="{ row }">{{ row.sample_columns?.length || 0 }}</template>
        </el-table-column>
        <el-table-column label="判定规则" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.judge_rule || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openCustomItemEditor(row)">编辑</el-button>
            <el-button link type="primary" size="small" @click="useCustomItem(row)">选用</el-button>
            <el-button link type="danger" size="small" @click="handleDeleteCustomItem(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="customMgrVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 自定义测试项编辑器对话框 -->
    <el-dialog v-model="customEditorVisible" :title="customEditorMode === 'create' ? '新建自定义测试项' : '编辑自定义测试项'" width="920px" top="5vh">
      <el-form :model="customEditorForm" label-width="100px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="测试项名称" required>
              <el-input v-model="customEditorForm.name" placeholder="例如 拉力测试 / 阻值老化" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="描述">
              <el-input v-model="customEditorForm.description" placeholder="可选，测试目的说明" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="判定规则">
          <el-input v-model="customEditorForm.judge_rule" type="textarea" :rows="2"
            placeholder="可选，例如：所有样品 result=pass 则通过；存在 fail 则失败" />
        </el-form-item>

        <el-divider content-position="left">参数定义（测试条件，如温度/压力/时长）</el-divider>
        <div style="margin-bottom:8px">
          <el-button size="small" @click="addEditorParam"><el-icon><Plus /></el-icon> 添加参数</el-button>
          <span style="margin-left:8px;color:#909399;font-size:12px">参数键建议用英文（如 temp_min），存入 param_values.params</span>
        </div>
        <el-table :data="customEditorForm.params" size="small" border empty-text="未定义参数">
          <el-table-column label="#" type="index" width="42" />
          <el-table-column label="参数键" width="120">
            <template #default="{ row }"><el-input v-model="row.key" size="small" placeholder="如 temp_min" /></template>
          </el-table-column>
          <el-table-column label="参数名" width="140">
            <template #default="{ row }"><el-input v-model="row.name" size="small" placeholder="如 温度下限" /></template>
          </el-table-column>
          <el-table-column label="单位" width="80">
            <template #default="{ row }"><el-input v-model="row.unit" size="small" placeholder="°C" /></template>
          </el-table-column>
          <el-table-column label="输入类型" width="110">
            <template #default="{ row }">
              <el-select v-model="row.input_type" size="small" style="width:100%">
                <el-option label="数字" value="number" />
                <el-option label="文本" value="text" />
                <el-option label="下拉" value="select" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="默认值" width="100">
            <template #default="{ row }"><el-input v-model="row.default" size="small" placeholder="可选" /></template>
          </el-table-column>
          <el-table-column label="下限" width="80">
            <template #default="{ row }"><el-input-number v-model="row.min" size="small" controls-position="right" style="width:70px" /></template>
          </el-table-column>
          <el-table-column label="上限" width="80">
            <template #default="{ row }"><el-input-number v-model="row.max" size="small" controls-position="right" style="width:70px" /></template>
          </el-table-column>
          <el-table-column label="选项(逗号分隔)" min-width="140">
            <template #default="{ row }">
              <el-input v-model="row.optionsText" size="small" :disabled="row.input_type !== 'select'" placeholder="如 A,B,C" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="70" fixed="right">
            <template #default="{ $index }">
              <el-button link type="danger" size="small" @click="customEditorForm.params.splice($index, 1)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-divider content-position="left">结果列定义（样品表格的列，如 阻值/拉力/判定结果）</el-divider>
        <div style="margin-bottom:8px;display:flex;justify-content:space-between;align-items:center">
          <el-button size="small" @click="addEditorColumn"><el-icon><Plus /></el-icon> 添加列</el-button>
          <span style="color:#909399;font-size:12px">
            提示：键名为 <code>result</code> 且选项含 pass/fail 时将启用自动判定；勾选「自动计算」可设为 after-before 差值列
          </span>
        </div>
        <el-table :data="customEditorForm.sample_columns" size="small" border empty-text="未定义结果列">
          <el-table-column label="#" type="index" width="42" />
          <el-table-column label="列键" width="120">
            <template #default="{ row }"><el-input v-model="row.key" size="small" placeholder="如 resistance" /></template>
          </el-table-column>
          <el-table-column label="列标题" width="140">
            <template #default="{ row }"><el-input v-model="row.label" size="small" placeholder="如 阻值" /></template>
          </el-table-column>
          <el-table-column label="单位" width="80">
            <template #default="{ row }"><el-input v-model="row.unit" size="small" placeholder="Ω" /></template>
          </el-table-column>
          <el-table-column label="输入类型" width="110">
            <template #default="{ row }">
              <el-select v-model="row.input_type" size="small" style="width:100%">
                <el-option label="文本" value="text" />
                <el-option label="数字" value="number" />
                <el-option label="下拉" value="select" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="选项(逗号分隔)" min-width="140">
            <template #default="{ row }">
              <el-input v-model="row.optionsText" size="small" :disabled="row.input_type !== 'select'" placeholder="如 pass,fail" />
            </template>
          </el-table-column>
          <el-table-column label="列宽" width="80">
            <template #default="{ row }"><el-input-number v-model="row.width" size="small" :min="60" :step="10" controls-position="right" style="width:70px" /></template>
          </el-table-column>
          <el-table-column label="自动计算" width="100" align="center">
            <template #default="{ row }">
              <el-checkbox v-model="row.auto_calc" />
            </template>
          </el-table-column>
          <el-table-column label="差值源(before)" width="140">
            <template #default="{ row }">
              <el-input v-model="row.before_key" size="small" :disabled="!row.auto_calc" placeholder="before列键" />
            </template>
          </el-table-column>
          <el-table-column label="差值源(after)" width="140">
            <template #default="{ row }">
              <el-input v-model="row.after_key" size="small" :disabled="!row.auto_calc" placeholder="after列键" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="70" fixed="right">
            <template #default="{ $index }">
              <el-button link type="danger" size="small" @click="customEditorForm.sample_columns.splice($index, 1)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-form>
      <template #footer>
        <el-button @click="customEditorVisible = false">取消</el-button>
        <el-button type="primary" :loading="customEditorSaving" @click="handleSaveCustomItem">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick, watch, onBeforeUnmount, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, UploadFilled, ArrowDown, Paperclip, WarningFilled, Download, Setting } from '@element-plus/icons-vue'
import { experimentApi, projectApi, userApi } from '@/api'
import {
  EXPERIMENT_STATUS_OPTS, EXPERIMENT_TYPE_OPTS, CONCLUSION_OPTS,
  statusLabel, statusTag, typeLabel, conclusionLabel, conclusionTag,
  type ExperimentOut, type ExperimentRecordOut, type ExperimentAttachmentOut, type ParamTemplateItem,
} from '@/types/experiment'
import {
  AECQ200_TEST_ITEMS, AECQ_CATEGORY_LABEL, AECQ_CATEGORY_TAG, findTestItem,
  type AecqTestItem,
} from '@/types/aecq200'
import {
  listCustomTestItems, getCustomTestItem, saveCustomTestItem, deleteCustomTestItem,
  genItemId, buildEmptyParams, buildEmptySample, recalcSampleRow, calcSampleStats,
  emptyParamDef, emptyColumnDef,
  type CustomTestItem, type CustomParamDef, type CustomColumnDef,
} from '@/utils/customTestItems'

const loading = ref(false)
const submitting = ref(false)
const formVisible = ref(false)
const recordsVisible = ref(false)
const formMode = ref<'create' | 'edit'>('create')
const router = useRouter()
const tableData = reactive<{ items: ExperimentOut[]; total: number }>({ items: [], total: 0 })
const projectOptions = ref<{ id: number; name: string }[]>([])
const userOptions = ref<{ id: number; name: string }[]>([])
const records = ref<ExperimentRecordOut[]>([])
const currentExp = ref<ExperimentOut | null>(null)
const pagination = reactive({ page: 1, page_size: 20 })
const filter = reactive({
  status: '', exp_type: '', keyword: '',
  project_id: null as number | null,
  date_range: null as [string, string] | null,
})

// 实验表单
const form = reactive({
  id: 0, name: '', description: '', project_id: null as number | null,
  exp_type: 'performance', status: 'draft',
  plan_range: null as [string, string] | null,
  param_template: [] as ParamTemplateItem[],
})

// 实验记录表单
const recordFormVisible = ref(false)
const recordSubmitting = ref(false)
const recordFormMode = ref<'create' | 'edit'>('create')
const recordForm = reactive({
  id: 0, experiment_id: 0,
  batch_no: '', sample_code: '', executor_id: null as number | null,
  // 通用参数录入（无 AEC-Q200 / 自定义 测试项时使用）
  param_rows: [] as Array<ParamTemplateItem & { value: any }>,
  param_values_text: '',
  // 记录类型标识：''=普通 | 'tcr'=温漂 | 'temp_rise'=温升 | 'aecq200'=AEC-Q200 | 'custom'=自定义测试项
  test_type: '' as '' | 'tcr' | 'temp_rise' | 'aecq200' | 'custom',
  // AEC-Q200 专用字段
  aecq_item_code: '',                              // 选中的测试项代码
  aecq_params: {} as Record<string, any>,          // 测试项参数值
  aecq_samples: [] as Array<Record<string, any>>,  // 批量样品结果
  // 自定义测试项专用字段
  custom_item_id: '',                              // 选中的自定义测试项 ID
  custom_params: {} as Record<string, any>,        // 测试项参数值
  custom_samples: [] as Array<Record<string, any>>, // 批量样品结果
  // 通用结果数据：键值对表格 or JSON 文本
  result_use_json: false,
  result_rows: [] as Array<{ key: string; value: string; unit: string }>,
  result_data_text: '',
  result_summary: '',
  conclusion: '' as string,
  is_abnormal: false,
  abnormal_desc: '',
  executed_at: '',
  // 记录附件（编辑模式可直接管理）
  attachments: [] as ExperimentAttachmentOut[],
})

// 是否为温漂/温升结构化测试记录（表单中切换只读，防破坏数据）
const isStructuredTestRecord = computed(() =>
  recordForm.test_type === 'tcr' || recordForm.test_type === 'temp_rise'
)

// 是否为自定义测试项记录
const isCustomRecord = computed(() => recordForm.test_type === 'custom')

// 是否为 AEC-Q200 可靠性测试记录
const isAecqRecord = computed(() => recordForm.test_type === 'aecq200')

// 当前选中的 AEC-Q200 测试项定义
const currentAecqItem = computed<AecqTestItem | undefined>(() =>
  recordForm.aecq_item_code ? findTestItem(recordForm.aecq_item_code) : undefined
)

// AEC-Q200 批量样品统计
const aecqStats = computed(() => {
  const samples = recordForm.aecq_samples
  const total = samples.length
  const failed = samples.filter(s => s.result === 'fail').length
  const passed = samples.filter(s => s.result === 'pass').length
  const pending = total - failed - passed
  const pass_rate = total > 0 ? Math.round((passed / total) * 1000) / 10 : 0
  // AEC-Q200 自动判定：0 失效 → pass；≥1 失效 → fail；否则需复测
  let auto_conclusion: string = 'need_retest'
  if (total > 0 && pending === 0) {
    auto_conclusion = failed === 0 ? 'pass' : 'fail'
  }
  return { total, passed, failed, pending, pass_rate, auto_conclusion }
})

// 切换/选择 AEC-Q200 测试项时：重置参数为默认值、清空样品表格
const onAecqItemChange = (code: string) => {
  const item = findTestItem(code)
  if (!item) {
    recordForm.aecq_params = {}
    recordForm.aecq_samples = []
    return
  }
  // 用默认值初始化参数
  const params: Record<string, any> = {}
  item.params.forEach(p => { params[p.key] = p.default ?? '' })
  recordForm.aecq_params = params
  recordForm.aecq_samples = []
  // 自动同步 is_abnormal：默认 false
  recordForm.is_abnormal = false
}

// AEC-Q200 批量样品：追加一行（按列定义初始化空行）
const addAecqSample = () => {
  const item = currentAecqItem.value
  if (!item) return
  const row: Record<string, any> = { code: '' }
  item.sample_columns.forEach(c => {
    if (c.key !== 'code' && !c.auto_calc) row[c.key] = ''
  })
  recordForm.aecq_samples.push(row)
}

// AEC-Q200 批量样品：根据数量批量生成空行（编号自动递增）
const batchAddAecqSamples = () => {
  ElMessageBox.prompt('请输入要生成的样品数量（1-200）', '批量生成样品', {
    confirmButtonText: '生成',
    cancelButtonText: '取消',
    inputPattern: /^[1-9]\d{0,2}$/,
    inputErrorMessage: '请输入 1-200 之间的数字',
  }).then(({ value }) => {
    const item = currentAecqItem.value
    if (!item) return
    const count = Math.min(200, parseInt(value))
    const startIdx = recordForm.aecq_samples.length
    for (let i = 0; i < count; i++) {
      const row: Record<string, any> = { code: `S-${String(startIdx + i + 1).padStart(3, '0')}` }
      item.sample_columns.forEach(c => {
        if (c.key !== 'code' && !c.auto_calc) row[c.key] = ''
      })
      recordForm.aecq_samples.push(row)
    }
  }).catch(() => {})
}

// AEC-Q200 样品变化率自动计算（before/after/delta 列存在时）
const onAecqSampleInput = (row: Record<string, any>, colKey: string) => {
  const item = currentAecqItem.value
  if (!item) return
  // 存在 delta 列且改了 before/after 时，自动算变化率
  const hasDelta = item.sample_columns.some(c => c.key === 'delta' && c.auto_calc)
  if (hasDelta && (colKey === 'before' || colKey === 'after')) {
    const before = parseFloat(row.before)
    const after = parseFloat(row.after)
    if (!isNaN(before) && !isNaN(after) && before !== 0) {
      row.delta = Math.round(((after - before) / before * 100) * 1000) / 1000
    } else {
      row.delta = ''
    }
  }
  // 同步 is_abnormal：有任何失效样品即为异常
  recordForm.is_abnormal = recordForm.aecq_samples.some(s => s.result === 'fail')
}

// 应用 AEC-Q200 自动判定到 conclusion
const applyAutoConclusion = () => {
  recordForm.conclusion = aecqStats.value.auto_conclusion
}

// ===== 自定义测试项 =====

// 已保存的自定义测试项列表（管理对话框使用）
const customTestItems = ref<CustomTestItem[]>([])
const reloadCustomTestItems = () => { customTestItems.value = listCustomTestItems() }

// 当前选中的自定义测试项定义
const currentCustomItem = computed<CustomTestItem | undefined>(() =>
  recordForm.custom_item_id ? getCustomTestItem(recordForm.custom_item_id) : undefined
)

// 是否存在 result 列（决定是否显示统计与自动判定）
const hasCustomResultColumn = computed(() =>
  !!currentCustomItem.value?.sample_columns.some(c => c.key === 'result')
)

// 自定义测试项样品统计
const customStats = computed(() => calcSampleStats(recordForm.custom_samples))

// 选择自定义测试项时：重置参数为默认、清空样品
const onCustomItemChange = (id: string) => {
  const item = id ? getCustomTestItem(id) : undefined
  if (!item) {
    recordForm.custom_params = {}
    recordForm.custom_samples = []
    return
  }
  recordForm.custom_params = buildEmptyParams(item.params)
  recordForm.custom_samples = []
  recordForm.is_abnormal = false
}

// 追加一个空白样品
const addCustomSample = () => {
  const item = currentCustomItem.value
  if (!item) return
  recordForm.custom_samples.push(buildEmptySample(item.sample_columns, ''))
}

// 批量生成 N 个样品（编号自动递增）
const batchAddCustomSamples = () => {
  ElMessageBox.prompt('请输入要生成的样品数量（1-200）', '批量生成样品', {
    confirmButtonText: '生成',
    cancelButtonText: '取消',
    inputPattern: /^[1-9]\d{0,2}$/,
    inputErrorMessage: '请输入 1-200 之间的数字',
  }).then(({ value }) => {
    const item = currentCustomItem.value
    if (!item) return
    const count = Math.min(200, parseInt(value))
    const startIdx = recordForm.custom_samples.length
    for (let i = 0; i < count; i++) {
      const code = `S-${String(startIdx + i + 1).padStart(3, '0')}`
      recordForm.custom_samples.push(buildEmptySample(item.sample_columns, code))
    }
  }).catch(() => {})
}

// 样品单元格输入变化：重算 auto_calc 列、同步 is_abnormal
const onCustomSampleInput = (row: Record<string, any>, _colKey: string) => {
  const item = currentCustomItem.value
  if (!item) return
  // 重算 auto_calc 列
  const newRow = recalcSampleRow(row, item.sample_columns)
  Object.keys(newRow).forEach(k => { row[k] = newRow[k] })
  // 同步 is_abnormal
  recordForm.is_abnormal = recordForm.custom_samples.some(s => s.result === 'fail')
}

// 应用自动判定
const applyCustomAutoConclusion = () => {
  recordForm.conclusion = customStats.value.auto_conclusion
}

// ===== 自定义测试项管理对话框 =====
const customMgrVisible = ref(false)
const customEditorVisible = ref(false)
const customEditorMode = ref<'create' | 'edit'>('create')
const customEditorSaving = ref(false)
// 编辑器表单（params/sample_columns 内部增加 optionsText 字段便于输入）
interface EditorParamRow extends CustomParamDef { optionsText: string }
interface EditorColumnRow extends CustomColumnDef { optionsText: string }
const customEditorForm = reactive({
  id: '',
  name: '',
  description: '',
  judge_rule: '',
  params: [] as EditorParamRow[],
  sample_columns: [] as EditorColumnRow[],
})

const openCustomItemManager = () => {
  reloadCustomTestItems()
  customMgrVisible.value = true
}

const parseOptionsText = (t: string): string[] =>
  t.split(',').map(s => s.trim()).filter(Boolean)

const openCustomItemEditor = (item?: CustomTestItem) => {
  reloadCustomTestItems()
  if (item) {
    customEditorMode.value = 'edit'
    customEditorForm.id = item.id
    customEditorForm.name = item.name
    customEditorForm.description = item.description || ''
    customEditorForm.judge_rule = item.judge_rule || ''
    customEditorForm.params = item.params.map(p => ({ ...p, optionsText: (p.options || []).join(',') }))
    customEditorForm.sample_columns = item.sample_columns.map(c => ({ ...c, optionsText: (c.options || []).join(',') }))
  } else {
    customEditorMode.value = 'create'
    customEditorForm.id = ''
    customEditorForm.name = ''
    customEditorForm.description = ''
    customEditorForm.judge_rule = ''
    customEditorForm.params = []
    customEditorForm.sample_columns = []
  }
  customEditorVisible.value = true
}

const addEditorParam = () => {
  customEditorForm.params.push({ ...emptyParamDef(), optionsText: '' })
}

const addEditorColumn = () => {
  customEditorForm.sample_columns.push({ ...emptyColumnDef(), optionsText: '' })
}

const handleSaveCustomItem = () => {
  if (!customEditorForm.name.trim()) {
    ElMessage.warning('请填写测试项名称')
    return
  }
  // 校验参数键与列键唯一且非空
  const paramKeys = customEditorForm.params.map(p => p.key).filter(Boolean)
  if (new Set(paramKeys).size !== paramKeys.length) {
    ElMessage.warning('参数键存在重复，请检查')
    return
  }
  const colKeys = customEditorForm.sample_columns.map(c => c.key).filter(Boolean)
  if (new Set(colKeys).size !== colKeys.length) {
    ElMessage.warning('结果列键存在重复，请检查')
    return
  }
  customEditorSaving.value = true
  try {
    const item: CustomTestItem = {
      id: customEditorForm.id || genItemId(),
      name: customEditorForm.name.trim(),
      description: customEditorForm.description.trim(),
      judge_rule: customEditorForm.judge_rule.trim(),
      params: customEditorForm.params
        .filter(p => p.key && p.name)
        .map(p => ({
          key: p.key, name: p.name, unit: p.unit || null,
          default: p.default ?? '', min: p.min ?? null, max: p.max ?? null,
          input_type: p.input_type || 'number',
          options: p.input_type === 'select' ? parseOptionsText(p.optionsText) : [],
        })),
      sample_columns: customEditorForm.sample_columns
        .filter(c => c.key && c.label)
        .map(c => ({
          key: c.key, label: c.label, unit: c.unit || null,
          input_type: c.input_type || 'text',
          options: c.input_type === 'select' ? parseOptionsText(c.optionsText) : [],
          width: c.width || 120, auto_calc: !!c.auto_calc,
          before_key: c.auto_calc ? (c.before_key || '') : '',
          after_key: c.auto_calc ? (c.after_key || '') : '',
        })),
      created_at: '', updated_at: '',
    }
    const saved = saveCustomTestItem(item)
    reloadCustomTestItems()
    ElMessage.success(customEditorMode.value === 'create' ? '已创建测试项' : '已更新测试项')
    customEditorVisible.value = false
    // 如果当前记录表单选中的就是这个测试项，刷新参数默认值
    if (recordForm.custom_item_id === saved.id) {
      onCustomItemChange(saved.id)
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '保存失败')
  } finally {
    customEditorSaving.value = false
  }
}

const handleDeleteCustomItem = (row: CustomTestItem) => {
  ElMessageBox.confirm(`确定删除测试项「${row.name}」？已使用该测试项的记录不受影响（数据已持久化）。`, '提示', {
    type: 'warning',
  }).then(() => {
    deleteCustomTestItem(row.id)
    reloadCustomTestItems()
    if (recordForm.custom_item_id === row.id) {
      recordForm.custom_item_id = ''
      onCustomItemChange('')
    }
    ElMessage.success('已删除')
  }).catch(() => {})
}

// 在管理对话框中点击「选用」：关闭管理对话框，将测试项填入记录表单
const useCustomItem = (row: CustomTestItem) => {
  recordForm.test_type = 'custom'
  recordForm.custom_item_id = row.id
  onCustomItemChange(row.id)
  customMgrVisible.value = false
  ElMessage.success(`已选用「${row.name}」`)
}

// 附件已整合到记录编辑表单（无独立对话框）
const recordAttachmentLoading = ref(false)

// 记录分页与筛选
const recordsLoading = ref(false)
const recordsTotal = ref(0)
const recordPagination = reactive({ page: 1, page_size: 20 })
const recordFilter = reactive({
  batch_no: '', sample_code: '', conclusion: '' as string,
  is_abnormal: null as boolean | null,
  date_range: null as [string, string] | null,
})
const selectedRecordIds = ref<number[]>([])
const exporting = ref(false)

// 预览对话框
const previewVisible = ref(false)
const previewLoading = ref(false)
const previewTitle = ref('')
const previewType = ref<'tcr' | 'temp_rise' | 'aecq200' | 'custom' | 'normal'>('normal')
const previewRecord = ref<ExperimentRecordOut | null>(null)
const previewChartRef = ref<HTMLDivElement | null>(null)
// ECharts 实例用 shallowRef 持有，懒加载 echarts 模块
const previewChart = shallowRef<any>(null)
let echartsModule: any = null

// 温漂预览数据
const tcrPreviewPoints = ref<any[]>([])
const tcrPreviewRefTemp = ref(25)
// 温升预览数据
const tempRisePreviewPoints = ref<any[]>([])
const tempRisePreviewSummary = reactive({
  ambient_temp: null as number | null,
  ref_resistance: null as number | null,
  max_temp_rise: null as number | null,
  max_rth: null as number | null,
  max_body_temp: null as number | null,
})
// AEC-Q200 预览数据
const aecqPreviewItem = ref<AecqTestItem | undefined>(undefined)
const aecqPreviewSamples = ref<Array<Record<string, any>>>([])
// 自定义测试项预览数据
const customPreviewItem = ref<CustomTestItem | undefined>(undefined)
const customPreviewSchema = ref<{ params: CustomParamDef[]; sample_columns: CustomColumnDef[] } | null>(null)
const customPreviewSamples = ref<Array<Record<string, any>>>([])

// 文件大小格式化
const formatFileSize = (size: number) => {
  if (!size) return '0 B'
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  return (size / 1024 / 1024).toFixed(2) + ' MB'
}
const formatDateTime = (s: string) => s ? new Date(s).toLocaleString('zh-CN') : '-'

const load = async () => {
  loading.value = true
  try {
    const res = await experimentApi.list({
      ...pagination,
      status: filter.status || undefined,
      exp_type: filter.exp_type || undefined,
      keyword: filter.keyword || undefined,
      project_id: filter.project_id || undefined,
      date_from: filter.date_range?.[0] || undefined,
      date_to: filter.date_range?.[1] || undefined,
    })
    tableData.items = res.items || []
    tableData.total = res.total || 0
  } finally { loading.value = false }
}

const onFilterChange = () => {
  pagination.page = 1
  load()
}

// page_size 变化时重置到第 1 页再加载（避免 @change 触发两次请求）
const onPageSizeChange = () => {
  pagination.page = 1
  load()
}

const loadProjects = async () => {
  try {
    const res = await projectApi.list({ page: 1, page_size: 100 })
    projectOptions.value = (res.items || []).map((p: any) => ({ id: p.id, name: p.name }))
  } catch {}
}

const loadUsers = async () => {
  try {
    const res = await userApi.simpleList()
    userOptions.value = (res || []).map((u: any) => ({ id: u.id, name: u.real_name || u.username }))
  } catch {}
}

const addParam = () => {
  form.param_template.push({ name: '', unit: '', default: null, min: null, max: null })
}

const showForm = async (row?: ExperimentOut) => {
  if (!projectOptions.value.length) await loadProjects()
  if (row) {
    formMode.value = 'edit'
    Object.assign(form, {
      id: row.id, name: row.name, description: row.description || '',
      project_id: row.project_id, exp_type: row.exp_type, status: row.status,
      plan_range: row.plan_start && row.plan_end ? [row.plan_start, row.plan_end] : null,
      param_template: Array.isArray(row.param_template)
        ? row.param_template.map((p: any) => ({ name: p.name || '', unit: p.unit || '', default: p.default ?? null, min: p.min ?? null, max: p.max ?? null }))
        : [],
    })
  } else {
    formMode.value = 'create'
    Object.assign(form, {
      id: 0, name: '', description: '', project_id: null,
      exp_type: 'performance', status: 'draft', plan_range: null, param_template: [],
    })
  }
  formVisible.value = true
}

const handleSubmit = async () => {
  if (!form.name.trim()) { ElMessage.warning('请输入实验名称'); return }
  if (!form.project_id) { ElMessage.warning('请选择所属项目'); return }
  submitting.value = true
  try {
    const payload: any = {
      name: form.name, description: form.description,
      project_id: form.project_id, exp_type: form.exp_type,
      // status 不通过 update 接口提交，必须走 /status 接口
      param_template: form.param_template.filter(p => p.name.trim()).map(p => ({
        name: p.name, unit: p.unit || null, default: p.default ?? null, min: p.min ?? null, max: p.max ?? null,
      })),
    }
    if (form.plan_range && form.plan_range.length === 2) {
      payload.plan_start = form.plan_range[0]
      payload.plan_end = form.plan_range[1]
    }
    if (formMode.value === 'create') {
      await experimentApi.create(payload)
      ElMessage.success('创建成功')
    } else {
      await experimentApi.update(form.id, payload)
      ElMessage.success('更新成功')
    }
    formVisible.value = false
    load()
  } finally { submitting.value = false }
}

const handleDelete = async (row: ExperimentOut) => {
  // 已完成/进行中的实验可能有记录和附件，给出额外警示
  const hint = (row.status === 'completed' || row.status === 'in_progress')
    ? '\n\n该实验可能含已录入的测试记录与附件，删除后无法恢复。'
    : ''
  await ElMessageBox.confirm(`确定删除实验「${row.name}」吗？删除后实验记录和附件将一并清除。${hint}`, '提示', { type: 'warning' })
  await experimentApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

// ===== 跳转专用测试页面 =====
const goTcrTest = (row: ExperimentOut) => router.push(`/experiments/${row.id}/tcr`)
const goTempRiseTest = (row: ExperimentOut) => router.push(`/experiments/${row.id}/temp-rise`)

// ===== 状态流转 =====
const handleStatusAction = async (row: ExperimentOut, action: string) => {
  const actionLabel: Record<string, string> = { start: '开始', complete: '完成', cancel: '取消' }
  await ElMessageBox.confirm(`确定要${actionLabel[action]}该实验吗？`, '提示', { type: 'warning' })
  try {
    await experimentApi.changeStatus(row.id, action as any)
    ElMessage.success('状态已更新')
    load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e?.response?.data?.detail || '操作失败')
  }
}

// ===== 实验记录 =====
const showRecords = async (row: ExperimentOut) => {
  currentExp.value = row
  recordsVisible.value = true
  // 重置筛选与分页
  recordPagination.page = 1
  recordPagination.page_size = 20
  Object.assign(recordFilter, {
    batch_no: '', sample_code: '', conclusion: '',
    is_abnormal: null, date_range: null,
  })
  records.value = []
  await loadRecords()
}

// 加载记录（带分页与筛选）
const loadRecords = async () => {
  if (!currentExp.value) return
  recordsLoading.value = true
  try {
    const data = await experimentApi.getRecords(currentExp.value.id, {
      ...recordPagination,
      batch_no: recordFilter.batch_no || undefined,
      sample_code: recordFilter.sample_code || undefined,
      conclusion: recordFilter.conclusion || undefined,
      is_abnormal: recordFilter.is_abnormal ?? undefined,
      date_from: recordFilter.date_range?.[0] || undefined,
      date_to: recordFilter.date_range?.[1] || undefined,
    })
    records.value = data.items || []
    recordsTotal.value = data.total || 0
  } catch {
    records.value = []
    recordsTotal.value = 0
  } finally { recordsLoading.value = false }
}

const resetRecordFilter = () => {
  Object.assign(recordFilter, {
    batch_no: '', sample_code: '', conclusion: '',
    is_abnormal: null, date_range: null,
  })
  recordPagination.page = 1
  loadRecords()
}

// page_size 变化时重置到第 1 页再加载
const onRecordPageSizeChange = () => {
  recordPagination.page = 1
  loadRecords()
}

const onRecordSelectionChange = (rows: ExperimentRecordOut[]) => {
  selectedRecordIds.value = rows.map(r => r.id)
}

const handleBatchDeleteRecords = async () => {
  if (!selectedRecordIds.value.length) return
  await ElMessageBox.confirm(`确定批量删除 ${selectedRecordIds.value.length} 条记录？`, '提示', { type: 'warning' })
  await experimentApi.batchDeleteRecords(selectedRecordIds.value)
  ElMessage.success('批量删除成功')
  selectedRecordIds.value = []
  await loadRecords()
}

const handleExportRecords = async () => {
  if (!currentExp.value) return
  exporting.value = true
  try {
    await experimentApi.exportRecords(currentExp.value.id)
    ElMessage.success('导出成功')
  } catch (e: any) {
    ElMessage.error(e?.message || '导出失败')
  } finally { exporting.value = false }
}

// 测试类型：根据参数 values.test_type 判定
const getTestType = (row: ExperimentRecordOut): 'tcr' | 'temp_rise' | 'aecq200' | 'custom' | 'normal' => {
  const pv = row?.param_values
  const t = pv?.test_type
  // 仅当声明为 tcr/temp_rise 且确实含结构化 sample_points 才识别为专用测试记录
  // 避免普通记录手动误填 test_type 字段导致预览时显示空表格
  if (t === 'tcr' && Array.isArray(pv?.sample_points)) return 'tcr'
  if (t === 'temp_rise' && Array.isArray(pv?.sample_points)) return 'temp_rise'
  // AEC-Q200 记录：含 test_item 字段且样品结果为数组
  if (t === 'aecq200' && pv?.test_item) return 'aecq200'
  // 自定义测试项记录：含 custom_item 字段且样品结果为数组
  if (t === 'custom' && pv?.custom_item && Array.isArray(row?.result_data?.samples)) return 'custom'
  return 'normal'
}

// 结果数据预览：从 result_data 生成简短摘要
const getResultPreview = (row: ExperimentRecordOut): string => {
  const data = row?.result_data
  if (!data) return '-'
  if (typeof data === 'string') return data
  if (typeof data === 'object') {
    // AEC-Q200 / 自定义 测试项：含 samples 数组与统计
    if (Array.isArray(data.samples) && typeof data.total === 'number') {
      const name = data.test_item_name || data.custom_item_name || data.test_item || data.custom_item || ''
      const parts = [
        name ? name : '样品测试',
        `样品${data.total}个`,
      ]
      // 仅当存在 result 列判定时才显示合格率
      if (data.passed != null || data.failed != null) {
        parts.push(`合格${data.passed ?? 0}/失效${data.failed ?? 0}`)
        if (data.pass_rate != null) parts.push(`合格率${data.pass_rate}%`)
      }
      return parts.join('，')
    }
    const entries = Object.entries(data).slice(0, 3)
    if (!entries.length) return '-'
    return entries.map(([k, v]) => `${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`).join('，')
  }
  return String(data)
}

// 记录汇总：异常条数 / 总数
const recordsSummaryText = computed(() => {
  const total = recordsTotal.value
  if (!total) return '暂无记录'
  const abnormal = records.value.filter(r => r.is_abnormal).length
  return abnormal ? `本页异常 ${abnormal} / 共 ${total} 条` : `本页正常 / 共 ${total} 条`
})
const recordsSummaryTag = computed<'danger' | 'success' | 'info'>(() => {
  if (!recordsTotal.value) return 'info'
  return records.value.some(r => r.is_abnormal) ? 'danger' : 'success'
})

// 异常行高亮
const recordRowClass = ({ row }: { row: ExperimentRecordOut }) =>
  row.is_abnormal ? 'abnormal-row' : ''

const buildParamRows = (template: any): Array<ParamTemplateItem & { value: any }> => {
  if (!Array.isArray(template)) return []
  return template.map((p: any) => ({
    name: p.name || '', unit: p.unit || '', default: p.default ?? null,
    min: p.min ?? null, max: p.max ?? null, value: p.default ?? '',
  }))
}

// 参数是否超出范围
const isParamOutOfRange = (row: ParamTemplateItem & { value: any }): boolean => {
  if (row.value === '' || row.value == null) return false
  const num = Number(row.value)
  if (Number.isNaN(num)) return false
  if (row.min != null && num < row.min) return true
  if (row.max != null && num > row.max) return true
  return false
}
const paramRowClass = ({ row }: { row: ParamTemplateItem & { value: any } }) =>
  isParamOutOfRange(row) ? 'param-out-row' : ''

const resetParamRows = () => {
  recordForm.param_rows.forEach(r => { r.value = r.default ?? '' })
}

// 结果数据：从对象转为可编辑行（还原 __unit 后缀字段）
const buildResultRows = (data: any): Array<{ key: string; value: string; unit: string }> => {
  if (!data || typeof data !== 'object' || Array.isArray(data)) return []
  return Object.entries(data)
    .filter(([k]) => !k.endsWith('__unit'))  // 跳过单位后缀字段
    .map(([k, v]) => ({
      key: k,
      value: typeof v === 'object' ? JSON.stringify(v) : String(v),
      unit: (data as any)[`${k}__unit`] || '',
    }))
}
const addResultRow = () => {
  recordForm.result_rows.push({ key: '', value: '', unit: '' })
}
const toggleResultJsonMode = () => {
  if (!recordForm.result_use_json) {
    // 切换为 JSON：把当前表格内容（含单位）序列化到文本框
    const obj: any = {}
    recordForm.result_rows.forEach(r => {
      if (r.key) {
        // 单独字段保存单位，便于切回表格时还原
        obj[r.key] = r.value
        if (r.unit) obj[`${r.key}__unit`] = r.unit
      }
    })
    recordForm.result_data_text = Object.keys(obj).length ? JSON.stringify(obj, null, 2) : ''
  } else {
    // 切换为表格：把 JSON 解析到行（还原单位）
    try {
      const parsed = recordForm.result_data_text ? JSON.parse(recordForm.result_data_text) : null
      recordForm.result_rows = buildResultRows(parsed)
    } catch {
      ElMessage.warning('JSON 格式错误，无法转换为表格')
      return
    }
  }
  recordForm.result_use_json = !recordForm.result_use_json
}

// 收集结果数据：表格模式 → 对象；JSON 模式 → 解析
const collectResultData = (): any => {
  if (recordForm.result_use_json) {
    return parseJsonSafe(recordForm.result_data_text)
  }
  const obj: any = {}
  let hasValue = false
  recordForm.result_rows.forEach(r => {
    if (r.key) {
      obj[r.key] = r.value
      if (r.unit) obj[`${r.key}__unit`] = r.unit
      hasValue = true
    }
  })
  return hasValue ? obj : null
}

// 自动生成结果摘要
const autoFillResultSummary = (): string => {
  if (recordForm.result_use_json) return ''
  const parts: string[] = []
  recordForm.result_rows.forEach(r => {
    if (r.key && r.value) parts.push(`${r.key}=${r.value}${r.unit || ''}`)
  })
  return parts.length ? `测试结果：${parts.join('，')}` : ''
}

const showRecordForm = async (rec?: ExperimentRecordOut) => {
  if (!userOptions.value.length) await loadUsers()
  if (!currentExp.value) return
  const template = currentExp.value.param_template
  // 刷新自定义测试项列表（供下拉使用）
  reloadCustomTestItems()

  if (rec) {
    recordFormMode.value = 'edit'
    // 识别温漂/温升/AEC-Q200/自定义 记录
    const testType = rec.param_values?.test_type
    const isStructured = testType === 'tcr' || testType === 'temp_rise'
    const isAecq = testType === 'aecq200' && rec.param_values?.test_item
    const isCustom = testType === 'custom' && rec.param_values?.custom_item
    const paramRows = (isStructured || isAecq || isCustom) ? [] : buildParamRows(template)
    if (!isStructured && !isAecq && !isCustom && paramRows.length && rec.param_values && typeof rec.param_values === 'object') {
      paramRows.forEach(r => { r.value = rec.param_values?.[r.name] ?? r.default ?? '' })
    }
    // 编辑模式下：尝试用表格展示 result_data，对象才能转，否则用 JSON 模式
    const useJson = rec.result_data && (typeof rec.result_data !== 'object' || Array.isArray(rec.result_data))
    Object.assign(recordForm, {
      id: rec.id, experiment_id: rec.experiment_id,
      batch_no: rec.batch_no || '', sample_code: rec.sample_code || '',
      executor_id: rec.executor_id || null,
      param_rows: paramRows,
      param_values_text: isStructured
        ? (rec.param_values ? JSON.stringify(rec.param_values, null, 2) : '')
        : (paramRows.length ? '' : (rec.param_values ? JSON.stringify(rec.param_values) : '')),
      test_type: isStructured ? testType : (isAecq ? 'aecq200' : (isCustom ? 'custom' : '')),
      aecq_item_code: isAecq ? (rec.param_values?.test_item || '') : '',
      aecq_params: isAecq ? { ...(rec.param_values?.params || {}) } : {},
      aecq_samples: isAecq ? (Array.isArray(rec.result_data?.samples) ? [...rec.result_data.samples] : []) : [],
      custom_item_id: isCustom ? (rec.param_values?.custom_item_id || '') : '',
      custom_params: isCustom ? { ...(rec.param_values?.params || {}) } : {},
      custom_samples: isCustom ? (Array.isArray(rec.result_data?.samples) ? rec.result_data.samples.map((s: any) => ({ ...s })) : []) : [],
      result_use_json: !!useJson,
      result_rows: buildResultRows(rec.result_data),
      result_data_text: isStructured
        ? (rec.result_data ? JSON.stringify(rec.result_data, null, 2) : '')
        : (useJson ? (rec.result_data ? JSON.stringify(rec.result_data) : '') : ''),
      result_summary: rec.result_summary || '',
      conclusion: rec.conclusion || '',
      is_abnormal: !!rec.is_abnormal, abnormal_desc: rec.abnormal_desc || '',
      executed_at: rec.executed_at || '',
      attachments: [],
    })
    // 加载附件列表
    try {
      const data = await experimentApi.listAttachments(rec.id)
      recordForm.attachments = data || []
    } catch { recordForm.attachments = [] }
  } else {
    recordFormMode.value = 'create'
    const paramRows = buildParamRows(template)
    Object.assign(recordForm, {
      id: 0, experiment_id: currentExp.value.id,
      batch_no: '', sample_code: '', executor_id: null,
      param_rows: paramRows,
      param_values_text: paramRows.length ? '' : '',
      test_type: '',
      aecq_item_code: '',
      aecq_params: {},
      aecq_samples: [],
      custom_item_id: '',
      custom_params: {},
      custom_samples: [],
      result_use_json: false,
      result_rows: [],
      result_data_text: '',
      result_summary: '', conclusion: '',
      is_abnormal: false, abnormal_desc: '', executed_at: '',
      attachments: [],
    })
  }
  recordFormVisible.value = true
}

const parseJsonSafe = (text: string): any => {
  if (!text || !text.trim()) return null
  try { return JSON.parse(text) } catch { throw new Error('JSON 格式错误，请检查参数值或结果数据') }
}

const handleRecordSubmit = async () => {
  if (!recordForm.experiment_id) { ElMessage.warning('缺少实验信息'); return }
  // AEC-Q200 校验：选了测试项必须有样品
  if (isAecqRecord.value) {
    if (!recordForm.aecq_item_code) { ElMessage.warning('请选择 AEC-Q200 测试项'); return }
    if (!recordForm.aecq_samples.length) { ElMessage.warning('请至少追加一个样品'); return }
  }
  // 自定义测试项校验
  if (isCustomRecord.value) {
    if (!recordForm.custom_item_id) { ElMessage.warning('请选择自定义测试项，或点击「管理测试项」新建'); return }
    if (!recordForm.custom_samples.length) { ElMessage.warning('请至少追加一个样品'); return }
  }
  recordSubmitting.value = true
  try {
    const payload: any = {
      batch_no: recordForm.batch_no || null,
      sample_code: recordForm.sample_code || null,
      executor_id: recordForm.executor_id || null,
      result_summary: recordForm.result_summary || null,
      conclusion: recordForm.conclusion || null,
      is_abnormal: recordForm.is_abnormal,
      abnormal_desc: recordForm.is_abnormal ? (recordForm.abnormal_desc || null) : null,
      executed_at: recordForm.executed_at || null,
    }

    if (isStructuredTestRecord.value) {
      // 温漂/温升记录：保留原始 param_values/result_data，不重新解析
    } else if (isAecqRecord.value) {
      // AEC-Q200 记录：构造结构化 param_values 和 result_data
      const item = currentAecqItem.value
      payload.param_values = {
        test_type: 'aecq200',
        test_item: recordForm.aecq_item_code,
        test_item_name: item?.name || '',
        category: item?.category || '',
        params: { ...recordForm.aecq_params },
      }
      const stats = aecqStats.value
      payload.result_data = {
        test_item: recordForm.aecq_item_code,
        test_item_name: item?.name || '',
        samples: recordForm.aecq_samples.map(s => ({ ...s })),
        total: stats.total,
        passed: stats.passed,
        failed: stats.failed,
        pending: stats.pending,
        pass_rate: stats.pass_rate,
        auto_conclusion: stats.auto_conclusion,
      }
      // 摘要为空时根据统计自动生成
      if (!payload.result_summary) {
        const parts = [
          `${item?.name || recordForm.aecq_item_code}`,
          `样品${stats.total}个`,
          `合格${stats.passed}/失效${stats.failed}`,
          `合格率${stats.pass_rate}%`,
        ]
        payload.result_summary = parts.join('，')
      }
    } else if (isCustomRecord.value) {
      // 自定义测试项记录：构造结构化 param_values 和 result_data
      const item = currentCustomItem.value
      const stats = customStats.value
      const hasResultCol = hasCustomResultColumn.value
      payload.param_values = {
        test_type: 'custom',
        custom_item: item?.name || '',
        custom_item_id: recordForm.custom_item_id,
        custom_item_name: item?.name || '',
        // 保存 schema 快照，便于历史记录在没有测试项定义时仍可还原列结构
        custom_schema: {
          params: item?.params || [],
          sample_columns: item?.sample_columns || [],
        },
        params: { ...recordForm.custom_params },
      }
      const resultData: any = {
        custom_item: item?.name || '',
        custom_item_name: item?.name || '',
        samples: recordForm.custom_samples.map(s => ({ ...s })),
        total: stats.total,
      }
      // 仅当存在 result 列时才记录判定统计
      if (hasResultCol) {
        resultData.passed = stats.passed
        resultData.failed = stats.failed
        resultData.pending = stats.pending
        resultData.pass_rate = stats.pass_rate
        resultData.auto_conclusion = stats.auto_conclusion
      }
      payload.result_data = resultData
      // 摘要为空时自动生成
      if (!payload.result_summary) {
        const parts = [item?.name || '自定义测试', `样品${stats.total}个`]
        if (hasResultCol) {
          parts.push(`合格${stats.passed}/失效${stats.failed}`)
          parts.push(`合格率${stats.pass_rate}%`)
        }
        payload.result_summary = parts.join('，')
      }
    } else {
      // 普通记录：正常收集
      let param_values: any = null
      if (recordForm.param_rows.length) {
        const obj: any = {}
        recordForm.param_rows.forEach(r => { if (r.name) obj[r.name] = r.value })
        param_values = obj
      } else {
        param_values = parseJsonSafe(recordForm.param_values_text)
      }
      payload.param_values = param_values
      payload.result_data = collectResultData()
      // 摘要为空时根据结果数据自动生成
      if (!payload.result_summary) payload.result_summary = autoFillResultSummary() || null
    }

    if (recordFormMode.value === 'create') {
      payload.experiment_id = recordForm.experiment_id
      await experimentApi.createRecord(payload)
      ElMessage.success('记录已创建')
    } else {
      await experimentApi.updateRecord(recordForm.id, payload)
      ElMessage.success('记录已更新')
    }
    recordFormVisible.value = false
    // 刷新记录列表
    await loadRecords()
  } catch (e: any) {
    ElMessage.error(e?.message || e?.response?.data?.message || '提交失败')
  } finally { recordSubmitting.value = false }
}

// 记录表单内的附件上传/删除
const handleRecordAttachmentChange = async (file: any) => {
  if (!recordForm.id) { ElMessage.warning('请先保存记录再上传附件'); return }
  const f = file.raw as File
  if (!f) return
  recordAttachmentLoading.value = true
  try {
    await experimentApi.uploadAttachment(recordForm.id, f)
    ElMessage.success('上传成功')
    const data = await experimentApi.listAttachments(recordForm.id)
    recordForm.attachments = data || []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '上传失败')
  } finally { recordAttachmentLoading.value = false }
}
const handleDeleteRecordAttachment = async (row: ExperimentAttachmentOut) => {
  await ElMessageBox.confirm(`确定要删除附件 "${row.file_name}" 吗？`, '提示', { type: 'warning' })
  await experimentApi.deleteAttachment(row.id)
  ElMessage.success('已删除')
  recordForm.attachments = recordForm.attachments.filter(a => a.id !== row.id)
}

const handleDeleteRecord = async (rec: ExperimentRecordOut) => {
  await ElMessageBox.confirm(`确定要删除实验记录 "${rec.batch_no || rec.sample_code || '#' + rec.id}" 吗？`, '提示', { type: 'warning' })
  await experimentApi.deleteRecord(rec.id)
  ElMessage.success('已删除')
  await loadRecords()
}

// ===== 附件 =====
// 附件管理已整合到记录编辑表单，「附件」按钮直接打开编辑模式，滚动到附件区
const showAttachments = async (rec: ExperimentRecordOut) => {
  await showRecordForm(rec)
}

const handleDownloadAttachment = async (row: ExperimentAttachmentOut, inline: boolean) => {
  try {
    await experimentApi.downloadAttachment(row.id, inline)
  } catch (e: any) {
    ElMessage.error('操作失败')
  }
}

// handleDeleteAttachment 已废弃：表单内使用 handleDeleteRecordAttachment

// ===== 温漂/温升记录预览 =====
const tcrColorPreview = (v: number | null) => {
  if (v == null) return ''
  const abs = Math.abs(v)
  if (abs <= 50) return '#67c23a'
  if (abs <= 100) return '#e6a23c'
  return '#f56c6c'
}

const showPreview = async (rec: ExperimentRecordOut) => {
  previewType.value = getTestType(rec)
  if (previewType.value === 'normal') {
    ElMessage.info('该记录为常规记录，无需预览')
    return
  }
  previewLoading.value = true
  previewVisible.value = true
  previewRecord.value = rec
  previewTitle.value =
    previewType.value === 'tcr' ? `温漂测试记录预览 - #${rec.id}`
    : previewType.value === 'temp_rise' ? `温升测试记录预览 - #${rec.id}`
    : previewType.value === 'aecq200' ? `AEC-Q200 测试记录预览 - #${rec.id}`
    : previewType.value === 'custom' ? `自定义测试项记录预览 - #${rec.id}`
    : `记录预览 - #${rec.id}`
  // 重置数据
  tcrPreviewPoints.value = []
  tempRisePreviewPoints.value = []
  aecqPreviewSamples.value = []
  aecqPreviewItem.value = undefined
  customPreviewSamples.value = []
  customPreviewItem.value = undefined
  customPreviewSchema.value = null
  Object.assign(tempRisePreviewSummary, {
    ambient_temp: null, ref_resistance: null,
    max_temp_rise: null, max_rth: null, max_body_temp: null,
  })
  try {
    // 拉取详情（含完整 param_values 和 result_data）
    const detail = await experimentApi.getRecord(rec.id)
    previewRecord.value = detail
    const pv = detail?.param_values || {}
    if (previewType.value === 'tcr') {
      tcrPreviewRefTemp.value = pv.temp_config?.ref ?? pv.ref_resistance_temp ?? 25
      tcrPreviewPoints.value = Array.isArray(pv.sample_points) ? pv.sample_points : []
      await nextTick()
      await renderTcrPreviewChart()
    } else if (previewType.value === 'temp_rise') {
      tempRisePreviewPoints.value = Array.isArray(pv.points) ? pv.points : (Array.isArray(pv.sample_points) ? pv.sample_points : [])
      tempRisePreviewSummary.ambient_temp = pv.power_config?.ambient_temp ?? null
      tempRisePreviewSummary.ref_resistance = pv.power_config?.ref_resistance ?? null
      // 计算汇总
      const validPoints = tempRisePreviewPoints.value.filter((p: any) => p.temp_rise != null)
      const rthValues = tempRisePreviewPoints.value.map((p: any) => p.rth_core_to_ambient).filter((v: any) => v != null)
      const bodyTemps = tempRisePreviewPoints.value.map((p: any) => p.body_temp).filter((v: any) => v != null)
      tempRisePreviewSummary.max_temp_rise = validPoints.length ? Math.max(...validPoints.map((p: any) => p.temp_rise)) : null
      tempRisePreviewSummary.max_rth = rthValues.length ? Math.max(...rthValues) : null
      tempRisePreviewSummary.max_body_temp = bodyTemps.length ? Math.max(...bodyTemps) : null
    } else if (previewType.value === 'aecq200') {
      const code = pv?.test_item || pv?.aecq_item_code
      aecqPreviewItem.value = code ? findTestItem(code) : undefined
      const rd = detail?.result_data || {}
      aecqPreviewSamples.value = Array.isArray(rd.samples) ? rd.samples : []
    } else if (previewType.value === 'custom') {
      // 优先用保存的 schema 快照（保证历史记录可还原列结构）
      const schema = pv?.custom_schema
      if (schema && Array.isArray(schema.params) && Array.isArray(schema.sample_columns)) {
        customPreviewSchema.value = schema
      } else {
        // 退化方案：尝试从 localStorage 加载最新定义（可能因模板改动而与历史记录不完全一致）
        const itemId = pv?.custom_item_id
        const item = itemId ? getCustomTestItem(itemId) : undefined
        customPreviewItem.value = item
        customPreviewSchema.value = item ? { params: item.params, sample_columns: item.sample_columns } : null
      }
      const rd = detail?.result_data || {}
      customPreviewSamples.value = Array.isArray(rd.samples) ? rd.samples : []
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '加载预览失败')
  } finally { previewLoading.value = false }
}

const renderTcrPreviewChart = async () => {
  if (!previewChartRef.value) return
  // 懒加载 echarts 模块
  if (!echartsModule) {
    echartsModule = await import('echarts')
  }
  if (previewChart.value) { previewChart.value.dispose(); previewChart.value = null }
  previewChart.value = echartsModule.init(previewChartRef.value)
  const valid = tcrPreviewPoints.value
    .filter((p: any) => p.resistance != null)
    .slice()
    .sort((a: any, b: any) => a.temperature - b.temperature)
  const option = {
    tooltip: { trigger: 'axis', formatter: (params: any) => {
      const p = params[0]
      return `温度: ${p.axisValue}°C<br/>阻值: ${p.data} Ω`
    }},
    grid: { left: 60, right: 20, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      name: '温度 (°C)',
      data: valid.map((p: any) => String(p.temperature)),
      axisLine: { lineStyle: { color: '#909399' } },
    },
    yAxis: {
      type: 'value',
      name: '阻值 (Ω)',
      axisLine: { lineStyle: { color: '#909399' } },
      axisLabel: { formatter: (v: number) => v.toFixed(4) },
    },
    series: [{
      name: '阻值',
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 7,
      data: valid.map((p: any) => p.resistance),
      lineStyle: { width: 2, color: '#409eff' },
      itemStyle: { color: '#409eff' },
      markPoint: {
        data: [
          { type: 'min', name: '最小值' },
          { type: 'max', name: '最大值' },
        ],
      },
      markLine: { data: [{ type: 'average', name: '平均值' }] },
    }],
  }
  previewChart.value.setOption(option, true)
}

// 预览对话框关闭时清理 echarts
watch(previewVisible, (v) => {
  if (!v) {
    if (previewChart.value) { previewChart.value.dispose(); previewChart.value = null }
  }
})

const handlePreviewResize = () => previewChart.value?.resize()
onBeforeUnmount(() => {
  window.removeEventListener('resize', handlePreviewResize)
  if (previewChart.value) { previewChart.value.dispose(); previewChart.value = null }
})

onMounted(() => {
  load()
  window.addEventListener('resize', handlePreviewResize)
})
</script>

<style scoped>
:deep(.el-table .abnormal-row) {
  background-color: #fef0f0;
}
:deep(.el-table .abnormal-row:hover > td) {
  background-color: #fde2e2;
}
:deep(.el-table .param-out-row) {
  background-color: #fdf6ec;
}
:deep(.el-table .param-out-row:hover > td) {
  background-color: #faecd8;
}
:deep(.param-out .el-input__wrapper) {
  box-shadow: 0 0 0 1px #f56c6c inset !important;
}
</style>
