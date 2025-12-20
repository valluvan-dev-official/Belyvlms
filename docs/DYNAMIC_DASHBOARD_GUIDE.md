# Dynamic Dashboard & RBAC Frontend Implementation Guide

This guide explains how to build a **Single Dynamic Dashboard** that adapts to the user's permissions, rather than having separate pages for each role.

## 1. The Concept
Instead of redirecting users to `/admin-dashboard` or `/student-dashboard`, every user goes to `/dashboard`.
Inside `/dashboard`, the widgets, menu items, and buttons are **conditionally rendered** based on the list of permissions returned by the backend.

## 2. Backend APIs
You have two key endpoints to support this:

### A. Login (`POST /api/rbac/auth/login/`)
Returns the token and the initial permission set.
**Response:**
```json
{
    "access": "eyJ...",
    "refresh": "eyJ...",
    "role": { "code": "ADMIN", "name": "Administrator" },
    "permissions": ["USER_CREATE", "COURSE_VIEW", "REPORTS_VIEW"],
    "user": { "id": 1, "is_superuser": false }
}
```

### B. Get Current User Profile (`GET /api/rbac/auth/me/`)
**NEW Endpoint**: Use this to reload permissions if the user refreshes the page (so you don't rely only on stale localStorage).
**Response:** Same structure as Login (excluding tokens).

---

## 3. Frontend Architecture (React Example)

### Step 1: Auth Context (Global State)
Create a context to hold the `user`, `role`, and `permissions`.

```javascript
// src/context/AuthContext.js
import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [permissions, setPermissions] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchMe = async () => {
        try {
            const res = await axios.get('/api/rbac/auth/me/');
            setUser(res.data.user);
            setPermissions(res.data.permissions);
        } catch (err) {
            console.error("Failed to fetch user profile");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (localStorage.getItem('token')) {
            fetchMe();
        } else {
            setLoading(false);
        }
    }, []);

    // Helper: Check if user has specific permission
    const can = (permissionCode) => {
        if (user?.is_superuser) return true; // Superuser can do everything
        return permissions.includes(permissionCode);
    };

    return (
        <AuthContext.Provider value={{ user, permissions, can, loading }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
```

### Step 2: The `<PermissionGate>` Component
A reusable component to hide/show UI elements.

```javascript
// src/components/PermissionGate.jsx
import { useAuth } from '../context/AuthContext';

const PermissionGate = ({ permission, children, fallback = null }) => {
    const { can } = useAuth();

    if (can(permission)) {
        return children;
    }
    
    return fallback;
};

export default PermissionGate;
```

### Step 3: Dynamic Sidebar
Configure your menu items with a `requiredPermission` field.

```javascript
// src/config/menu.js
export const MENU_ITEMS = [
    { label: "Dashboard", path: "/dashboard", icon: "Home" }, // Public to all logged in
    { label: "Manage Users", path: "/users", icon: "Users", permission: "USER_VIEW" },
    { label: "Courses", path: "/courses", icon: "Book", permission: "COURSE_VIEW" },
    { label: "Financial Reports", path: "/reports", icon: "Dollar", permission: "FINANCE_VIEW" },
];

// Sidebar.jsx
import { MENU_ITEMS } from '../config/menu';
import PermissionGate from './PermissionGate';

const Sidebar = () => {
    return (
        <div className="sidebar">
            {MENU_ITEMS.map((item) => (
                // If item has no permission, show it. If it has permission, check it.
                (!item.permission) ? (
                    <Link to={item.path}>{item.label}</Link>
                ) : (
                    <PermissionGate permission={item.permission} key={item.path}>
                         <Link to={item.path}>{item.label}</Link>
                    </PermissionGate>
                )
            ))}
        </div>
    );
};
```

### Step 4: The Dynamic Dashboard Page
Compose the dashboard using PermissionGates.

```javascript
// src/pages/Dashboard.jsx
import PermissionGate from '../components/PermissionGate';

const Dashboard = () => {
    return (
        <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Everyone sees this */}
            <div className="card">
                <h2>Welcome Back!</h2>
                <p>Here is your daily summary.</p>
            </div>

            {/* Only Admins/Trainers with USER_CREATE can see this */}
            <PermissionGate permission="USER_CREATE">
                <div className="card bg-blue-100">
                    <h3>Quick Actions</h3>
                    <button>Add New Student</button>
                </div>
            </PermissionGate>

            {/* Only Finance Team sees this */}
            <PermissionGate permission="FINANCE_VIEW">
                <div className="card bg-green-100">
                    <h3>Revenue Stats</h3>
                    <Chart data={revenueData} />
                </div>
            </PermissionGate>

             {/* Only Trainers see this */}
             <PermissionGate permission="COURSE_MANAGE">
                <div className="card bg-purple-100">
                    <h3>My Batches</h3>
                    <List batches={myBatches} />
                </div>
            </PermissionGate>

        </div>
    );
};

export default Dashboard;
```

## 4. Summary
1.  **Login** -> Get `permissions` array.
2.  **AuthContext** -> Store permissions in memory.
3.  **PermissionGate** -> Wrap sensitive UI elements.
4.  **One Dashboard** -> The dashboard looks different for everyone because the components inside it conditionally render.

This is the standard "Enterprise" way to handle RBAC on the frontend.
