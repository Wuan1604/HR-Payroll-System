import { useEffect, useState } from 'react';
import { showPositions, addPosition, updatePosition, deletePosition } from '../api/humanApi';
import Loading from '../components/Loading';
import ApiError from '../components/ApiError';

export default function PositionPage() {
    const [positions, setPositions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    // State cho thêm mới
    const [newName, setNewName] = useState('');
    
    // State cho chỉnh sửa
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
            alert("Lỗi khi thêm chức vụ");
        }
    }

    async function handleDelete(id) {
        if (window.confirm("Bạn có chắc chắn muốn xóa chức vụ này? (Lưu ý: Không thể xóa nếu có nhân viên đang giữ chức vụ này)")) {
            try {
                await deletePosition(id);
                loadData();
            } catch (e) {
                alert(e.message || "Không thể xóa chức vụ này");
            }
        }
    }

    async function handleUpdate(id) {
        if (!editName.trim()) return;
        try {
            await updatePosition({ PositionID: id, PositionName: editName });
            setEditingId(null);
            loadData();
        } catch (e) {
            alert("Lỗi khi cập nhật");
        }
    }

    return (
        <div>
            <div className="card">
                <h2 style={{ marginTop: 0 }}>Quản lý Chức vụ</h2>
                <div className="muted">
                    Dữ liệu được quản lý tại SSMS (SQL Server) và đồng bộ sang MySQL.
                </div>
            </div>

            {error && <ApiError error={error} />}

            {/* Form thêm mới */}
            <form className="card" onSubmit={handleAdd} style={{ display: 'flex', gap: 10 }}>
                <input 
                    className="input" 
                    placeholder="Nhập tên chức vụ mới..." 
                    value={newName}
                    onChange={e => setNewName(e.target.value)}
                    style={{ flex: 1 }}
                />
                <button className="btn" type="submit" disabled={loading}>
                    Thêm chức vụ
                </button>
            </form>

            <div className="card">
                {loading && positions.length === 0 ? (
                    <Loading />
                ) : (
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr style={{ textAlign: 'left', borderBottom: '2px solid #eee' }}>
                                <th style={{ padding: '12px 8px' }}>Mã</th>
                                <th style={{ padding: '12px 8px' }}>Tên chức vụ</th>
                                <th style={{ padding: '12px 8px', textAlign: 'right' }}>Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            {positions.map((pos) => (
                                <tr key={pos.PositionID} style={{ borderBottom: '1px solid #eee' }}>
                                    <td style={{ padding: '12px 8px' }}>{pos.PositionID}</td>
                                    <td style={{ padding: '12px 8px' }}>
                                        {editingId === pos.PositionID ? (
                                            <input 
                                                className="input"
                                                value={editName}
                                                onChange={e => setEditName(e.target.value)}
                                                autoFocus
                                            />
                                        ) : (
                                            pos.PositionName
                                        )}
                                    </td>
                                    <td style={{ padding: '12px 8px', textAlign: 'right' }}>
                                        {editingId === pos.PositionID ? (
                                            <>
                                                <button className="btn" onClick={() => handleUpdate(pos.PositionID)} style={{ marginRight: 5 }}>Lưu</button>
                                                <button className="btn" onClick={() => setEditingId(null)}>Hủy</button>
                                            </>
                                        ) : (
                                            <>
                                                <button 
                                                    className="btn" 
                                                    onClick={() => {
                                                        setEditingId(pos.PositionID);
                                                        setEditName(pos.PositionName);
                                                    }}
                                                    style={{ marginRight: 5 }}
                                                >
                                                    Sửa
                                                </button>
                                                <button 
                                                    className="btn" 
                                                    style={{ backgroundColor: '#dc3545', color: 'white' }}
                                                    onClick={() => handleDelete(pos.PositionID)}
                                                >
                                                    Xóa
                                                </button>
                                            </>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {positions.length === 0 && !loading && (
                                <tr>
                                    <td colSpan="3" style={{ textAlign: 'center', padding: 20 }} className="muted">
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