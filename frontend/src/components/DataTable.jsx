function pickColumns(rows) {
  if (!Array.isArray(rows) || rows.length === 0) return []
  const colSet = new Set()
  for (const r of rows) {
    if (r && typeof r === 'object') {
      Object.keys(r).forEach((k) => colSet.add(k))
    }
  }
  return Array.from(colSet)
}

export default function DataTable({ rows = [], title }) {
  const cols = pickColumns(rows)
  if (!rows || rows.length === 0) {
    return (
      <div className="card">
        {title ? <h2 style={{ marginTop: 0 }}>{title}</h2> : null}
        <div className="muted">Không có dữ liệu.</div>
      </div>
    )
  }

  return (
    <div className="card">
      {title ? <h2 style={{ marginTop: 0 }}>{title}</h2> : null}
      <div style={{ overflowX: 'auto' }}>
        <table className="table">
          <thead>
            <tr>
              {cols.map((c) => (
                <th key={c}>{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, idx) => (
              <tr key={idx}>
                {cols.map((c) => (
                  <td key={c}>{r?.[c] ?? ''}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

