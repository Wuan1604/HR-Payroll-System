import { useEffect, useState } from 'react';
import { showDepartments, addDepartment, updateDepartment, deleteDepartment } from '../api/humanApi';
import Loading from '../components/Loading';

export default function DepartmentPage() {
    const [departments, setDepartments] = useState([]);
    const [loading, setLoading] = useState(false);
    const [newDeptName, setNewDeptName] = useState('');
    const [editingId, setEditingId] = useState(null);
    const [editName, setEditName] = useState('');

    useEffect(() => { loadData(); }, []);

    async function loadData() {
        setLoading(true);
        try {
            const data = await showDepartments();
            setDepartments(data);
        } catch (e) { alert("Lỗi load dữ liệu"); }
        setLoading(false);
    }

    async function handleAdd() {
        if (!newDeptName) return;
        await addDepartment(newDeptName);
        setNewDeptName('');
        loadData();
    }

    async function handleDelete(id) {
        if (window.confirm("Bạn có chắc chắn muốn xóa phòng ban này?")) {
            try {
                await deleteDepartment(id);
                loadData();
            } catch (e) { alert(e.message); }
        }
    }

    async function handleUpdate(id) {
        await updateDepartment({ DepartmentID: id, DepartmentName: editName });
        setEditingId(null);
        loadData();
    }

    return (
        <div className="card">
            <h2>Quản lý Phòng ban</h2>
            
            {/* Form thêm mới */}
            <div style={{ marginBottom: 20, display: 'flex', gap: 10 }}>
                <input 
                    className="input" 
                    placeholder="Tên phòng ban mới..." 
                    value={newDeptName}
                    onChange={e => setNewDeptName(e.target.value)}
                />
                <button className="btn" onClick={handleAdd}>Thêm mới</button>
            </div>

            {loading ? <Loading /> : (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ background: '#f4f4f4', textAlign: 'left' }}>
                            <th style={{ padding: 10 }}>ID</th>
                            <th style={{ padding: 10 }}>Tên phòng ban</th>
                            <th style={{ padding: 10 }}>Thao tác</th>
                        </tr>
                    </thead>
                    <tbody>
                        {departments.map(dept => (
                            <tr key={dept.DepartmentID} style={{ borderBottom: '1px solid #ddd' }}>
                                <td style={{ padding: 10 }}>{dept.DepartmentID}</td>
                                <td style={{ padding: 10 }}>
                                    {editingId === dept.DepartmentID ? (
                                        <input 
                                            className="input"
                                            value={editName}
                                            onChange={e => setEditName(e.target.value)}
                                        />
                                    ) : dept.DepartmentName}
                                </td>
                                <td style={{ padding: 10 }}>
                                    {editingId === dept.DepartmentID ? (
                                        <button className="btn" onClick={() => handleUpdate(dept.DepartmentID)}>Lưu</button>
                                    ) : (
                                        <button className="btn" onClick={() => {
                                            setEditingId(dept.DepartmentID);
                                            setEditName(dept.DepartmentName);
                                        }}>Sửa</button>
                                    )}
                                    <button 
                                        className="btn" 
                                        style={{ marginLeft: 5, background: '#ff4d4d' }}
                                        onClick={() => handleDelete(dept.DepartmentID)}
                                    >Xóa</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
}