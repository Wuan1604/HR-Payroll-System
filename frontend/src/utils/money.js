export function onlyDigits(value) {
  if (value === null || value === undefined) return ''
  return String(value).replace(/[^0-9]/g, '')
}

export function formatNumberWithCommas(value) {
  const raw = onlyDigits(value)
  if (!raw) return ''
  return raw.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

export function parseMoneyInput(value) {
  return onlyDigits(value)
}

export function formatMoney(value) {
  const raw = onlyDigits(value)
  if (!raw) return '0 VNĐ'
  return `${Number(raw).toLocaleString('en-US')} VNĐ`
}
