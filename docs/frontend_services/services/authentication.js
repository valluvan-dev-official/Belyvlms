import axios from "axios";

// ============================================
// 1. BASE CONFIGURATION
// ============================================

const BASE_URL = "https://dissimilar-madyson-uncriticisably.ngrok-free.dev/api/";

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
    "ngrok-skip-browser-warning": "true",
  },
});

const log = (msg, data = null) => {
  const time = new Date().toLocaleTimeString();
  console.log(`[${time}] ${msg}`);
  if (data) console.log(data);
};

// ============================================
// 2. TOKEN & USER MANAGEMENT
// ============================================

/**
 * Get current user data from localStorage
 * Returns full user object with token, role, permissions
 */
export const getCurrentUser = () => {
  try {
    const userData = localStorage.getItem("belyv_user");
    return userData ? JSON.parse(userData) : null;
  } catch (err) {
    log("⚠️ Error parsing user data from localStorage", err);
    return null;
  }
};

/**
 * Get access token only
 */
export const getAccessToken = () => {
  const user = getCurrentUser();
  return user?.access || localStorage.getItem("access");
};

/**
 * Check if user has a specific permission
 * @param {string} permissionCode - Permission code to check (e.g., "STUDENT_CREATE")
 * @returns {boolean}
 */
export const hasPermission = (permissionCode) => {
  const user = getCurrentUser();
  if (!user || !user.permissions) return false;
  return user.permissions.includes(permissionCode);
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = () => {
  return !!getAccessToken();
};

/**
 * Get user role
 */
export const getUserRole = () => {
  const user = getCurrentUser();
  return user?.role || null;
};

// ============================================
// 3. AUTHENTICATION FUNCTIONS
// ============================================

/**
 * Login user with RBAC API
 * @param {object} credentials - { email, password }
 * @returns {Promise} - Returns full RBAC response
 */
export const loginUser = async (credentials) => {
  log(`🌐 Calling: ${BASE_URL}rbac/auth/login/`);
  log(`📧 Email: ${credentials.email}`);
  
  try {
    const res = await api.post("rbac/auth/login/", credentials);

    log("✅ Logged in successfully!");
    log("📦 Response data:", res.data);

    // Extract data from RBAC response (only use access token)
    const { access, role, permissions, user } = res.data;

    // Create user object to store (no refresh token)
    const userData = {
      access,
      role: {
        code: role?.code || "ADMIN",
        name: role?.name || "Admin"
      },
      permissions: permissions || [],
      user: {
        id: user?.id || 1,
        email: user?.email || credentials.email,
        name: user?.name || user?.email?.split("@")[0] || "User"
      }
    };

    // Store only access token (60 days validity)
    localStorage.setItem("belyv_user", JSON.stringify(userData));
    localStorage.setItem("access", access);
    localStorage.setItem("isAuthenticated", JSON.stringify(true));
    
    // Return userData so the login form can access it
    return userData;
  } catch (err) {
    log(`❌ Login failed: ${err.message}`);
    log(`📍 Full URL attempted: ${BASE_URL}rbac/auth/login/`);
    
    if (err.response) {
      log(`📊 Status: ${err.response.status}`);
      log(`📄 Response:`, err.response.data);
      log(`📋 Detail: ${err.response.data?.detail || 'No detail provided'}`);
    }
    if (err.request) {
      log(`📨 Request was sent but no response received`);
    }
    
    throw err;
  }
};

/**
 * Logout user - clears local storage and redirects immediately
 * Synchronous function for instant logout (no delay)
 */
export const logoutUser = () => {
  log("🚪 Logout initiated...");
  
  try {
    // Clear all auth data immediately
    localStorage.removeItem("belyv_user");
    localStorage.removeItem("access");
    localStorage.setItem("isAuthenticated", JSON.stringify(false));
    
    log("🧹 Local storage cleared");
    log("🚪 Redirecting to login page NOW");
    
    // Set a flag for showing logout transition
    sessionStorage.setItem("showLogoutTransition", "true");
    
    // Immediate redirect - use href for instant navigation
    window.location.href = "/";
  } catch (error) {
    // Handle SecurityError or any other error during logout
    console.error("⚠️ SecurityError during logout:", error);
    
    // Even if there's an error, try to clear what we can
    try {
      localStorage.clear();
      sessionStorage.clear();
    } catch (e) {
      console.error("Could not clear storage:", e);
    }
    
    // Set security error flag
    try {
      sessionStorage.setItem("securityError", "true");
      sessionStorage.setItem("securityErrorMessage", error.message || "Unknown error");
    } catch (e) {
      // If even sessionStorage fails, just redirect
      console.error("SessionStorage blocked:", e);
    }
    
    // Force redirect even if storage is blocked
    window.location.href = "/";
  }
};

// ============================================
// 4. AXIOS INTERCEPTOR
// ============================================

/**
 * Request interceptor - Auto-attach JWT token
 */
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      // Remove "Bearer " prefix if it exists, then add it fresh
      const cleanToken = token.startsWith("Bearer ") ? token.substring(7) : token;
      config.headers.Authorization = `Bearer ${cleanToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor - Handle 401 unauthorized errors
 * If token is invalid/expired (401), set unauthorized flag
 */
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Handle 401 errors (unauthorized - token invalid or expired)
    if (error.response?.status === 401) {
      log("❌ 401 Unauthorized - Token invalid or expired");
      
      // Clear all auth data
      localStorage.removeItem("belyv_user");
      localStorage.removeItem("access");
      localStorage.setItem("isAuthenticated", JSON.stringify(false));
      
      // Set unauthorized flag to trigger unauthorized page
      localStorage.setItem("unauthorized", JSON.stringify(true));
      
      // Trigger a custom event that App.tsx can listen to
      window.dispatchEvent(new Event('unauthorized'));
    }

    return Promise.reject(error);
  }
);

// ============================================
// 5. EXPORTS
// ============================================

// Export the configured api instance for making authenticated requests
export default api;