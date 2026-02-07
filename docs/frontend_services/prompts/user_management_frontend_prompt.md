# 🚀 Enterprise User Management Implementation Prompt (Advanced)

**Role:** Senior React Developer & Enterprise Frontend Architect
**Context:** You are building the **User Management Module** for "BeLyv LMS". The system must be intelligent enough to show different onboarding flows based on the **User Role**.

---

## 🎯 Goal
Implement a **Role-Aware Onboarding Wizard** that dynamically adjusts its fields.
- **Dedicated Models (Student/Trainer):** Skip dynamic fields (handled by dedicated modules).
- **Generic Roles (Guest Lecturer, Consultant, etc.):** Show **Mandatory Default Fields** + **Dynamic Fields**.

---

## 🛠️ Service Layer Integration (Use These Exactly)
- `UserService.onboardUser(userData)`: The "Trinity" endpoint for creation.
- `RoleConfigService.getAllRoles()`: Fetch role list.
- `RoleConfigService.getConfigDetails(configId)`: Fetch dynamic fields configuration.

---

## 🏗️ The Intelligent Workflow (Step-by-Step)

### **Step 1: Identity & Authorization**
- **Fields:** Name, Email, Password, Confirm Password.
- **Role Selection:** A prominent Dropdown or Card Grid to select the User Role.

### **Step 2: Intelligent Profile Routing (CRITICAL LOGIC)**

When a role is selected, apply this logic immediately:

#### **CASE A: The Role is "STUDENT" or "TRAINER"**
*   **Logic:** These are "Heavy" roles with their own dedicated modules (`studentsdb`, `trainersdb`). We do **NOT** ask for profile details here to avoid duplication.
*   **UI Action:**
    - Show a friendly message: *"Student/Trainer profiles are managed in their respective modules. Click 'Create' to generate the user account now."*
    - **Skip Step 3** (Profile Fields).
    - **Go directly to Step 4** (Review & Submit).

#### **CASE B: The Role is "GENERIC" (e.g., Guest Lecturer, Consultant, Admin, Staff)**
*   **Logic:** These roles rely on the `GenericProfile` system. We must collect their KYC and specific details right here.
*   **UI Action:** Proceed to **Step 3 (Profile Fields)**.

---

### **Step 3: Profile Fields (Only for Case B)**

This form has two sections: **Mandatory Defaults** and **Dynamic Extras**.

#### **Section 3.1: Mandatory KYC Fields (Hardcoded in Frontend)**
For *any* Generic Role (except Student/Trainer), you **MUST** render these fields by default. They are required for Indian Enterprise Compliance.

1.  **Aadhar Number** (12 digits, validation required)
2.  **PAN Card Number** (Alphanumeric, validation required)
3.  **Current Address** (Multiline Text Area)
4.  **Permanent Address** (Multiline Text Area + "Same as Current" Checkbox)

#### **Section 3.2: Dynamic Fields (Fetched from Backend)**
After the KYC fields, render the role-specific fields fetched from `RoleConfigService.getConfigDetails()`.

*   *Example for Guest Lecturer:*
    - **University Name** (Text)
    - **Daily Rate** (Number)

*   *Example for Placement Officer:*
    - **Company Contacts** (Text)

---

### **Step 4: Review & Submit**
- **Action:** Consolidate all data into the JSON payload.
- **Payload Structure (Case B - Generic Role):**
  ```json
  {
    "email": "consultant@example.com",
    "name": "Rajesh Kumar",
    "password": "...",
    "role_code": "CONSULTANT",
    "extra_data": {
      "aadhar_number": "123456789012",       // From Section 3.1
      "pan_number": "ABCDE1234F",            // From Section 3.1
      "current_address": "123, MG Road...",  // From Section 3.1
      "permanent_address": "Same...",        // From Section 3.1
      "specialization": "Taxation",          // From Section 3.2 (Dynamic)
      "consulting_fee": 5000                 // From Section 3.2 (Dynamic)
    }
  }
  ```
- **Payload Structure (Case A - Student/Trainer):**
  ```json
  {
    "email": "student@example.com",
    "name": "Student Name",
    "password": "...",
    "role_code": "STUDENT",
    "extra_data": {} // Empty, as profile is handled later
  }
  ```

---

## 🎨 UI/UX Specifications
1.  **Split Form Layout (Step 3):**
    - Use a divider or a subsection header: **"KYC & Personal Details"** (for the default fields).
    - Followed by **"Role Specific Details"** (for the dynamic fields).
2.  **Address Toggle:**
    - Include a "Same as Current Address" checkbox. When checked, disable the Permanent Address field and auto-copy the value.
3.  **Validation:**
    - **Aadhar:** Must be exactly 12 digits.
    - **PAN:** Regex `[A-Z]{5}[0-9]{4}[A-Z]{1}`.
4.  **Empty State:** If a Generic Role has *no* dynamic fields configured in the backend, still show the Mandatory KYC fields (Section 3.1).

---

## 📝 Developer Checklist
- [ ] Import `UserService` and `RoleConfigService`.
- [ ] Implement the `if (role === 'STUDENT' || role === 'TRAINER')` check in Step 2.
- [ ] Create a reusable `<AddressForm />` component for Step 3.1.
- [ ] Merge `kycData` and `dynamicData` into `extra_data` before submitting.
