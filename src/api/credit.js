import request from './request'

export function getTenantCreditScore(tenantId) {
  return request.get(`/tenants/${tenantId}/credit-score`)
}

export function getTenantCreditRecords(tenantId, params) {
  return request.get(`/tenants/${tenantId}/credit-records`, { params })
}

export function adjustTenantCreditScore(tenantId, data) {
  return request.post(`/tenants/${tenantId}/credit-adjust`, data)
}
