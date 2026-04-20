import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1' })

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
