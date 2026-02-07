# 📘 BelyvLMS Frontend Implementation Guide: User Management & Dynamic Roles

## 🚀 **Overview**
This document serves as the **Master Blueprint** for implementing the User Management module in the frontend. It connects the **Trinity Architecture** (Identity + RBAC + Profile) to the UI/UX.

---

## 🏗️ **1. Architecture & Service Layer**
The frontend must use the **Service Layer Pattern** to communicate with the backend.

### **Folder Structure**
```
/src/services/userManagement/
├── userService.js         # Handles User CRUD & Onboarding
└── roleConfigService.js   # Handles Dynamic Role & Field Configuration
```

---

## 🔌 **2. API Integration Strategy**

### **A. User Onboarding (The "Trinity" Flow)**
This is the most critical flow. It creates the User, Assigns Role, and Saves Profile Data in ONE request.

*   **Endpoint:** `POST /api/profiles/onboard/`
*   **Service Method:** `UserService.onboardUser(data)`
*   **Payload Structure:**
    ```json
    {
      "email": "john@example.com",     // Identity
      "name": "John Doe",              // Identity
      "password": "SecretPassword123", // Identity
      "role_code": "GUEST_LECTURER",   // Authorization (RBAC)
      "extra_data": {                  // Profile (Dynamic JSON)
        "University": "Anna Univ",
        "DailyRate": 5000
      }
    }
    ```

### **B. Fetching Users**
*   **Endpoint:** `GET /api/accounts/users/` (or `GET /api/profiles/`)
*   **Service Method:** `UserService.getAllUsers(params)`
*   **Params:** `{ role: 'STUDENT', status: 'active', search: 'John' }`

### **C. Dynamic Role Configuration (Admin Panel)**
*   **Fetch Roles:** `GET /api/rbac/roles/` → `RoleConfigService.getAllRoles()`
*   **Fetch Configs:** `GET /api/profiles/configs/` → `RoleConfigService.getConfigs()`
*   **Add Custom Field:** `POST /api/profiles/fields/` → `RoleConfigService.addCustomField()`

---

## 🎨 **3. UI/UX Design & Workflow**

### **Screen 1: User Management Dashboard**
*   **Purpose:** List all users with status and roles.
*   **Data Source:** `UserService.getAllUsers()`
*   **Key Components:**
    *   **Filter Bar:** Dropdown for Role (fetched via `RoleConfigService.getAllRoles()`).
    *   **Data Table:** Columns [Name, Email, Role (Badge), Status (Toggle)].
    *   **Action Button:** "Onboard New User" → Navigates to **Onboarding Wizard**.

### **Screen 2: Onboarding Wizard (The "Magic" Screen)**
This screen must be dynamic. It adapts based on the selected Role.

**Step 1: Identity**
*   Fields: Name, Email, Password.
*   Validation: Standard email/password rules.

**Step 2: Role Selection**
*   **Data Source:** `RoleConfigService.getAllRoles()`
*   **UI:** Grid of Cards (Student, Trainer, Guest Lecturer, etc.).
*   **Action:** When a user selects a role (e.g., "Guest Lecturer"), call `RoleConfigService.getConfigDetails(roleId)` to fetch the required fields.

**Step 3: Dynamic Profile Fields (Crucial)**
*   **Logic:**
    *   If Role is **Student/Trainer**: Show standard message "Profile managed via dedicated module."
    *   If Role is **Generic (e.g., Guest Lecturer)**: Render fields based on the API response.
*   **Rendering Logic (Pseudo-code):**
    ```javascript
    const fields = await RoleConfigService.getFieldsByConfig(selectedRoleConfigId);
    
    return fields.map(field => {
       if (field.type === 'TEXT') return <TextField label={field.label} />
       if (field.type === 'CHOICE') return <Select options={field.options} />
    });
    ```
*   **Submission:** Collect all dynamic inputs into an `extra_data` object and send to `onboardUser()`.

---

### **Screen 3: Role & Profile Settings (Admin Only)**
*   **Purpose:** Allow Admins to add new fields to roles without coding.
*   **Data Source:** `RoleConfigService.getConfigs()`
*   **Workflow:**
    1.  Admin selects "Guest Lecturer".
    2.  Admin clicks "+ Add Field".
    3.  Form asks: "Field Label" (e.g., "University"), "Type" (Text).
    4.  Frontend calls `RoleConfigService.addCustomField()`.
    5.  **Result:** The "Onboarding Wizard" (Step 3) automatically updates to show this new field.

---

## 🛠️ **4. Implementation Checklist for Developer**

1.  **Setup Services:** Ensure `userService.js` and `roleConfigService.js` are imported.
2.  **State Management:** Use React Query or useEffect to fetch `roles` and `configs` on load.
3.  **Dynamic Form Component:** Create a reusable `<DynamicField field={fieldDefinition} />` component.
4.  **Error Handling:** If `onboardUser` fails (e.g., "Email exists"), show a Toast notification.
5.  **Role Code Security:** Never hardcode role IDs. Always match by `role_code` (e.g., 'STUDENT', 'ADMIN').

---

## 📝 **5. Example API Response (For UI Testing)**
**GET /api/profiles/configs/1/ (Guest Lecturer)**
```json
{
  "role_name": "Guest Lecturer",
  "is_generic": true,
  "fields": [
    {
      "name": "university_name",
      "label": "University Name",
      "type": "TEXT",
      "required": true
    },
    {
      "name": "daily_rate",
      "label": "Daily Rate (INR)",
      "type": "NUMBER",
      "required": false
    }
  ]
}
```
*The Frontend should iterate over this `fields` array to generate the form.*
