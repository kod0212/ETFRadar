import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1' })

// ETF管理
export const getFunds = (group?: string) =>
  api.get('/funds', { params: group ? { group_tag: group } : {} })

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
export const triggerCollect = () => api.post('/collect/trigger')
export const getCollectStatus = () => api.get('/collect/status')
