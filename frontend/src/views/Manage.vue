<template>
  <div>
    <a-button type="primary" style="margin-bottom: 16px" @click="showAdd = true">添加ETF</a-button>
    <a-table :dataSource="funds" :columns="columns" rowKey="code" size="small">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'is_active'">
          <a-switch :checked="record.is_active" @change="(v: boolean) => onToggle(record.code, v)" />
        </template>
        <template v-if="column.key === 'action'">
          <a-popconfirm title="确认删除?" @confirm="onDelete(record.code)">
            <a-button type="link" danger size="small">删除</a-button>
          </a-popconfirm>
        </template>
      </template>
    </a-table>

    <a-modal v-model:open="showAdd" title="添加ETF" @ok="onAdd" :confirmLoading="adding">
      <a-form :labelCol="{ span: 6 }">
        <a-form-item label="基金代码"><a-input v-model:value="form.code" placeholder="如 510300" /></a-form-item>
        <a-form-item label="名称"><a-input v-model:value="form.name" /></a-form-item>
        <a-form-item label="市场">
          <a-select v-model:value="form.market">
            <a-select-option value="sh">上海</a-select-option>
            <a-select-option value="sz">深圳</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="跟踪指数"><a-input v-model:value="form.index_name" /></a-form-item>
        <a-form-item label="分组"><a-input v-model:value="form.group_tag" /></a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { message } from 'ant-design-vue'
import { getFunds, createFund, updateFund, deleteFund } from '../api'

const funds = ref<any[]>([])
const showAdd = ref(false)
const adding = ref(false)
const form = reactive({ code: '', name: '', market: 'sh', index_name: '', group_tag: '' })

const columns = [
  { title: '代码', dataIndex: 'code', key: 'code', width: 100 },
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '市场', dataIndex: 'market', key: 'market', width: 80 },
  { title: '跟踪指数', dataIndex: 'index_name', key: 'index_name', width: 120 },
  { title: '分组', dataIndex: 'group_tag', key: 'group_tag', width: 100 },
  { title: '启用', key: 'is_active', width: 80 },
  { title: '操作', key: 'action', width: 80 },
]

const load = async () => {
  const res = await getFunds()
  funds.value = res.data.data || []
}

const onAdd = async () => {
  adding.value = true
  try {
    await createFund(form)
    message.success('添加成功')
    showAdd.value = false
    Object.assign(form, { code: '', name: '', market: 'sh', index_name: '', group_tag: '' })
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
