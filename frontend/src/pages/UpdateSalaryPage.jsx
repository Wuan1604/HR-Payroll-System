import { useEffect, useMemo, useState } from 'react'
import ApiError from '../components/ApiError'
import Loading from '../components/Loading'
import { getSalaries } from '../api/payrollApi'
import { updateSalary } from '../api/payrollApi'

export default function UpdateSalaryPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [rows, setRows] = useState([])

  const [selectedSalaryID, setSelectedSalaryID] = useState('')
  const selectedRow = useMemo(
    () => rows.find((r) => String(r?.SalaryID) === String(selectedSalaryID)),
    [rows, selectedSalaryID],
  )

  const [form, setForm] = useState({
    BaseSalary: '',
    Bonus: '',
    Deductions: '',
  })

  const [saving, setSaving] = useState(false)
  const [result, setResult] = useState(null)

  async function load() {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await getSalaries()
      const arr = Array.isArray(res) ? res : []
      setRows(arr)
      if (arr.length > 0 && !selectedSalaryID) {
        setSelectedSalaryID(String(arr[0].SalaryID ?? ''))
      }
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!selectedRow) return
    setForm({
      BaseSalary: selectedRow.BaseSalary ?? '',
      Bonus: selectedRow.Bonus ?? '',
      Deductions: selectedRow.Deductions ?? '',
    })
  }, [selectedRow])

  function computeNet() {
    const base = Number(form.BaseSalary || 0)
    const bonus = Number(form.Bonus || 0)
    const deduct = Number(form.Deductions || 0)
    return base + bonus - deduct
  }

  async function onSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setResult(null)
    try {
      if (!selectedSalaryID) throw new Error('Bạn cần chọn `SalaryID`.')
      const payload = {
        SalaryID: Number(selectedSalaryID),
        BaseSalary: Number(form.BaseSalary || 0),
        Bonus: Number(form.Bonus || 0),
        Deductions: Number(form.Deductions || 0),
      }
      const res = await updateSalary(payload)
      setResult(res)
    } catch (e) {
      setError(e)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Cập nhật lương</h2>
        <div className="muted">
          Gọi POST <code>/api/payroll/update-salary</code>.
        </div>
      </div>

      {loading ? <Loading /> : null}
      {error ? <ApiError error={error} /> : null}

      {!loading && !error ? (
        <form className="card" onSubmit={onSubmit}>
          <div className="row">
            <label style={{ display: 'flex', flexDirection: 'column' }}>
              <span className="muted" style={{ marginBottom: 6 }}>
                Chọn bản ghi lương
              </span>
              <select
                className="input"
                value={selectedSalaryID}
                onChange={(e) => setSelectedSalaryID(e.target.value)}
              >
                {rows.map((r) => (
                  <option key={r.SalaryID} value={String(r.SalaryID)}>
                    {r.SalaryID} - {r?.FullName} ({r?.SalaryMonth})
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="row" style={{ marginTop: 14 }}>
            <label style={{ display: 'flex', flexDirection: 'column' }}>
              <span className="muted" style={{ marginBottom: 6 }}>
                BaseSalary
              </span>
              <input
                className="input"
                value={form.BaseSalary}
                onChange={(e) => setForm((p) => ({ ...p, BaseSalary: e.target.value }))}
              />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column' }}>
              <span className="muted" style={{ marginBottom: 6 }}>
                Bonus
              </span>
              <input
                className="input"
                value={form.Bonus}
                onChange={(e) => setForm((p) => ({ ...p, Bonus: e.target.value }))}
              />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column' }}>
              <span className="muted" style={{ marginBottom: 6 }}>
                Deductions
              </span>
              <input
                className="input"
                value={form.Deductions}
                onChange={(e) => setForm((p) => ({ ...p, Deductions: e.target.value }))}
              />
            </label>
          </div>

          <div className="row" style={{ marginTop: 14 }}>
            <div className="muted">
              NetSalary dự kiến: <b>{computeNet()}</b>
            </div>
            <button className="btn" type="submit" disabled={saving}>
              {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
            </button>
          </div>
          {result ? (
            <div className="card" style={{ marginTop: 14 }}>
              <h3 style={{ marginTop: 0 }}>Kết quả</h3>
              <div className="muted">
                {result?.message || 'OK'}
              </div>
              <pre style={{ textAlign: 'left', whiteSpace: 'pre-wrap', marginTop: 10 }}>
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          ) : null}
        </form>
      ) : null}
    </div>
  )
}

