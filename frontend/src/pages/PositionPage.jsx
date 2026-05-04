import { useEffect, useState } from 'react';
import { RefreshCw, Plus, Save, X, Pencil, Trash2 } from '../components/LineIcons'
import { showPositions, addPosition, updatePosition, deletePosition } from '../api/humanApi';
import Loading from '../components/Loading';
import ApiError from '../components/ApiError';
import '../styles/PositionPage.css';

export default function PositionPage() {
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [newName, setNewName] = useState('');

  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError(null);

    try {
      const data = await showPositions();
      setPositions(data);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleAdd(e) {
    e.preventDefault();

    if (!newName.trim()) return;

    try {
      await addPosition(newName);
      setNewName('');
      loadData();
    } catch (e) {
      alert('Lỗi khi thêm chức vụ');
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('Bạn có chắc chắn muốn xóa chức vụ này?')) return;

    try {
      await deletePosition(id);
      loadData();
    } catch (e) {
      alert(e.message || 'Không thể xóa chức vụ này');
    }
  }

  async function handleUpdate(id) {
    if (!editName.trim()) return;

    try {
      await updatePosition({ PositionID: id, PositionName: editName });
      setEditingId(null);
      setEditName('');
      loadData();
    } catch (e) {
      alert('Lỗi khi cập nhật');
    }
  }

  function handleCancelEdit() {
    setEditingId(null);
    setEditName('');
  }

  return (
    <div className="position-page">
      <div className="position-header card">
        <div>
          <h2>Quản lý Chức vụ</h2>
          <p>Dữ liệu được quản lý tại SQL Server và đồng bộ sang MySQL.</p>
        </div>

        <button className="btn-refresh-position" onClick={loadData} disabled={loading}>
          <RefreshCw size={16} strokeWidth={1.8} aria-hidden="true" /> Làm mới
        </button>
      </div>

      {error && <ApiError error={error} />}

      <form className="position-add-form card" onSubmit={handleAdd}>
        <input
          className="position-input"
          placeholder="Nhập tên chức vụ mới..."
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
        />

        <button className="btn-add-position" type="submit" disabled={loading}>
          <Plus size={16} strokeWidth={1.8} aria-hidden="true" /> Thêm chức vụ
        </button>
      </form>

      <div className="position-table-wrapper">
        {loading && positions.length === 0 ? (
          <Loading />
        ) : (
          <table className="position-table">
            <thead>
              <tr>
                <th>Mã</th>
                <th>Tên chức vụ</th>
                <th>Thao tác</th>
              </tr>
            </thead>

            <tbody>
              {positions.map((pos) => (
                <tr key={pos.PositionID}>
                  <td>{pos.PositionID}</td>

                  <td>
                    {editingId === pos.PositionID ? (
                      <input
                        className="position-input edit-position-input"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        autoFocus
                      />
                    ) : (
                      <span className="position-name">{pos.PositionName}</span>
                    )}
                  </td>

                  <td>
                    <div className="position-actions">
                      {editingId === pos.PositionID ? (
                        <>
                          <button
                            className="btn-save-position"
                            type="button"
                            onClick={() => handleUpdate(pos.PositionID)}
                          >
                            <Save size={15} strokeWidth={1.8} aria-hidden="true" /> Lưu
                          </button>

                          <button
                            className="btn-cancel-position"
                            type="button"
                            onClick={handleCancelEdit}
                          >
                            <X size={15} strokeWidth={1.8} aria-hidden="true" /> Hủy
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            className="btn-edit-position"
                            type="button"
                            onClick={() => {
                              setEditingId(pos.PositionID);
                              setEditName(pos.PositionName);
                            }}
                          >
                            <Pencil size={15} strokeWidth={1.8} aria-hidden="true" /> Sửa
                          </button>

                          <button
                            className="btn-delete-position"
                            type="button"
                            onClick={() => handleDelete(pos.PositionID)}
                          >
                            <Trash2 size={15} strokeWidth={1.8} aria-hidden="true" /> Xóa
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}

              {positions.length === 0 && !loading && (
                <tr>
                  <td colSpan="3" className="position-empty">
                    Chưa có dữ liệu chức vụ.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
