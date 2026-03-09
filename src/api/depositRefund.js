import request from './request'

export function getDepositRefunds(params) {
  return request.get('/deposit-refunds', { params })
}

export function getDepositRefund(id) {
  return request.get(`/deposit-refunds/${id}`)
}

export function processRefund(id, data) {
  return request.post(`/deposit-refunds/${id}/process`, data)
}

export function completeRefund(id, data) {
  return request.post(`/deposit-refunds/${id}/complete`, data)
}

export function cancelRefund(id, data) {
  return request.post(`/deposit-refunds/${id}/cancel`, data)
}
