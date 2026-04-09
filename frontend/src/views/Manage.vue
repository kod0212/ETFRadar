<template>
  <div>
    <a-button type="primary" style="margin-bottom: 16px" @click="showAdd = true">添加ETF</a-button>
    <a-table :dataSource="funds" :columns="columns" rowKey="code" size="small">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'tags'">
          <a-space size="small" v-if="record.tags">
            <a-tag v-for="t in record.tags.split(',')" :key="t" color="blue">{{ t }}</a-tag>
          </a-space>
          <span v-else style="color: #ccc">-</span>
        </template>
        <template v-if="column.key === 'is_active'">
          <a-switch :checked="record.is_active" @change="(v: boolean) => onToggle(record.code, v)" />
        </template>
        <template v-if="column.key === 'action'">
          <a-space size="small">
            <a-button type="link" size="small" @click="openEditTags(record)">标签</a-button>
            <a-popconfirm title="确认删除?" @confirm="onDelete(record.code)">
              <a-button type="link" danger size="small">删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-modal v-model:open="showAdd" title="添加ETF" @ok="onAdd" :confirmLoading="adding"
             :okButtonProps="{ disabled: !lookupResult }">
      <a-form :labelCol="{ span: 6 }">
        <a-form-item label="基金代码">
          <a-input-search v-model:value="inputCode" placeholder="输入6位代码后回车"
                          :loading="looking" @search="onLookup" enter-button="查询" />
        </a-form-item>
        <template v-if="lookupResult">
          <a-form-item label="名称">
            <span>{{ lookupResult.name }}</span>
          </a-form-item>
          <a-form-item label="市场">
            <a-tag :color="lookupResult.market === 'sh' ? 'blue' : 'green'">
              {{ lookupResult.market === 'sh' ? '上海' : '深圳' }}
            </a-tag>
          </a-form-item>
          <a-form-item label="分组">
            <a-tag v-if="lookupResult.index_name" color="orange">{{ lookupResult.index_name }}</a-tag>
            <span v-else style="color: #999">未分类</span>
          </a-form-item>
          <a-form-item label="历史数据">
            <span v-if="lookupResult.has_history" style="color: #3f8600">
              ✓ 有 {{ lookupResult.history_count }} 天历史份额
            </span>
            <span v-else style="color: #999">暂无历史数据</span>
          </a-form-item>
          <a-form-item label="标签">
            <div style="margin-bottom: 8px; min-height: 24px">
              <a-tag v-for="(t, i) in tagsList" :key="i" color="blue" closable @close="tagsList.splice(i, 1)">{{ t }}</a-tag>
            </div>
            <a-input-search v-model:value="newAddTagInput" placeholder="输入标签名称" enter-button="添加"
                            @search="onAddNewTag" />
          </a-form-item>
        </template>
        <a-alert v-if="lookupError" :message="lookupError" type="error" show-icon style="margin-top: 8px" />
      </a-form>
    </a-modal>

    <a-modal v-model:open="showEditTags" title="编辑标签" @ok="onSaveTags">
      <p style="margin-bottom: 12px">{{ editingFund?.name }} ({{ editingFund?.code }})</p>
      <div style="margin-bottom: 12px; min-height: 32px">
        <a-tag v-for="(t, i) in editTagsList" :key="i" color="blue" closable @close="editTagsList.splice(i, 1)">
          {{ t }}
        </a-tag>
        <span v-if="!editTagsList.length" style="color: #ccc">暂无标签</span>
      </div>
      <a-input-search v-model:value="newTagInput" placeholder="输入标签名称" enter-button="添加"
                      @search="onAddTag" />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getFunds, lookupFund, createFund, updateFund, deleteFund } from '../api'

const funds = ref<any[]>([])
const showAdd = ref(false)
const adding = ref(false)
const inputCode = ref('')
const looking = ref(false)
const lookupResult = ref<any>(null)
const lookupError = ref('')
const tagsList = ref<string[]>([])
const newAddTagInput = ref('')

const onAddNewTag = () => {
  const tag = newAddTagInput.value.trim()
  if (tag && !tagsList.value.includes(tag)) {
    tagsList.value.push(tag)
  }
  newAddTagInput.value = ''
}
const showEditTags = ref(false)
const editingFund = ref<any>(null)
const editTagsList = ref<string[]>([])
const newTagInput = ref('')

const openEditTags = (record: any) => {
  editingFund.value = record
  editTagsList.value = record.tags ? record.tags.split(',').map((t: string) => t.trim()).filter(Boolean) : []
  newTagInput.value = ''
  showEditTags.value = true
}

const onAddTag = () => {
  const tag = newTagInput.value.trim()
  if (tag && !editTagsList.value.includes(tag)) {
    editTagsList.value.push(tag)
  }
  newTagInput.value = ''
}

const onSaveTags = async () => {
  if (!editingFund.value) return
  await updateFund(editingFund.value.code, { tags: editTagsList.value.join(',') || null })
  message.success('标签已更新')
  showEditTags.value = false
  await load()
}

const columns = [
  { title: '代码', dataIndex: 'code', key: 'code', width: 100 },
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '市场', dataIndex: 'market', key: 'market', width: 80 },
  { title: '分组', dataIndex: 'group_tag', key: 'group_tag', width: 100 },
  { title: '标签', dataIndex: 'tags', key: 'tags', width: 150 },
  { title: '启用', key: 'is_active', width: 80 },
  { title: '操作', key: 'action', width: 120 },
]

const load = async () => {
  const res = await getFunds()
  funds.value = res.data.data || []
}

const onLookup = async () => {
  const code = inputCode.value.trim()
  if (!code || code.length !== 6) {
    lookupError.value = '请输入6位基金代码'
    lookupResult.value = null
    return
  }
  looking.value = true
  lookupError.value = ''
  lookupResult.value = null
  try {
    const res = await lookupFund(code)
    if (res.data.code === 0) {
      lookupResult.value = res.data.data
    } else {
      lookupError.value = res.data.message
    }
  } catch (e: any) {
    lookupError.value = e.response?.data?.detail || '查询失败'
  } finally { looking.value = false }
}

const onAdd = async () => {
  if (!lookupResult.value) return
  adding.value = true
  try {
    await createFund({
      code: lookupResult.value.code,
      name: lookupResult.value.name,
      market: lookupResult.value.market,
      tags: tagsList.value.join(',') || null,
    })
    message.success(`已添加 ${lookupResult.value.name}`)
    showAdd.value = false
    inputCode.value = ''
    lookupResult.value = null
    tagsList.value = []
    newAddTagInput.value = ''
    await load()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '添加失败')
  } finally { adding.value = false }
}

const onToggle = async (code: string, active: boolean) => {
  await updateFund(code, { is_active: active })
  await load()
}

const onDelete = async (code: string) => {
  await deleteFund(code)
  message.success('已删除')
  await load()
}

onMounted(load)
</script>
