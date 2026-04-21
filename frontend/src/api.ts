import axios from 'axios'
import { message } from 'ant-design-vue'

const api = axios.create({ baseURL: '/api/v1' })

// 统一错误处理
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response) {
      const msg = err.response.data?.detail || err.response.data?.message || `请求失败 (${err.response.status})`
      message.error(msg)
    } else if (err.code === 'ECONNABORTED') {
      message.error('请求超时，请检查网络')
    } else {
      message.error('网络连接失败，请检查后端是否运行')
    }
    return Promise.reject(err)
  }
)

// ETF管理
export const getFunds = () => api.get('/funds')

export const lookupFund = (code: string) => api.get('/funds/lookup', { params: { code } })
export const createFund = (data: any) => api.post('/funds', data)
export const updateFund = (code: string, data: any) => api.put(`/funds/${code}`, data)
export const deleteFund = (code: string) => api.delete(`/funds/${code}`)

// 份额数据
export const getLatestShares = () => api.get('/shares/latest')
export const getShares = (params: any) => api.get('/shares', { params })
export const getSharesSummary = (params: any) => api.get('/shares/summary', { params })
export const getSharesTrend = (params: any) => api.get('/shares/trend', { params })

// 采集
export const triggerCollect = (force = false) => api.post(`/collect/trigger?force=${force}`)
export const getCollectStatus = () => api.get('/collect/status')

// 版本更新
export const checkUpdate = () => api.get('/collect/check_update')
export const doUpdate = () => api.post('/collect/do_update')
export const getUpdateProgress = () => api.get('/collect/update_progress')
