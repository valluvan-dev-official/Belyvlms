import { api } from "../../authentication";

// ============================================
// USER MANAGEMENT SERVICE
// ============================================

const ONBOARDING_URL = "profiles/onboard/";
const USERS_LIST_URL = "profiles/users/"; // Updated to point to the new UserViewSet

export const UserService = {
  /**
   * Onboard a New User (Trinity Architecture)
   * Handles Identity + RBAC + Profile Creation in one step.
   * 
   * POST /api/profiles/onboard/
   * 
   * @param {Object} userData
   * @param {string} userData.email - User Identity
   * @param {string} userData.name - User Identity
   * @param {string} userData.password - User Identity
   * @param {string} userData.role_code - Authorization (e.g., 'STUDENT', 'GUEST_LECTURER')
   * @param {Object} userData.profile_data - Static Profile Data (e.g., { phone: '123' })
   * @param {Object} userData.extra_data - Dynamic Profile Data (e.g., { 'University': 'Anna Univ' })
   */
  onboardUser: async (userData) => {
    try {
      const response = await api.post(ONBOARDING_URL, userData);
      return response.data;
    } catch (error) {
      console.error("Failed to onboard user:", error);
      throw error;
    }
  },

  /**
   * Get List of All Users (with Filtering)
   * GET /api/profiles/users/
   * 
   * @param {Object} params - { role: 'STUDENT', is_active: true, email: '...' }
   */
  getAllUsers: async (params = {}) => {
    try {
      const response = await api.get(USERS_LIST_URL, { params });
      return response.data;
    } catch (error) {
      console.error("Failed to fetch users:", error);
      throw error;
    }
  },

  /**
   * Get User Details by ID
   * GET /api/profiles/users/{id}/
   * @param {number} userId 
   */
  getUserById: async (userId) => {
    try {
      const response = await api.get(`${USERS_LIST_URL}${userId}/`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch user ${userId}:`, error);
      throw error;
    }
  },

  /**
   * Update User Status (Activate/Deactivate)
   * NOTE: Currently ReadOnlyViewSet in backend. 
   * To implement update, backend needs 'update' mixin in UserViewSet.
   * For now, this might fail unless backend allows it.
   */
  updateUserStatus: async (userId, isActive) => {
    // This is a placeholder. If you need this, we must add 'UpdateModelMixin' to UserViewSet
    console.warn("Update User Status not fully implemented in backend yet (ReadOnly).");
    // try {
    //   const response = await api.patch(`${USERS_LIST_URL}${userId}/`, { is_active: isActive });
    //   return response.data;
    // } catch (error) {
    //   throw error;
    // }
  }
};
