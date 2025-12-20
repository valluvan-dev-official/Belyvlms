import { api } from "./authentication";

// ============================================
// ROLE SERVICE CONFIGURATION
// ============================================

// Base URL for Roles (Adjust this if your backend route is different)
const ROLE_API_URL = "rbac/roles/";

export const RoleService = {
  /**
   * Get all Roles
   * GET /api/rbac/roles/
   */
  getRoles: async () => {
    try {
      const response = await api.get(ROLE_API_URL);
      return response.data;
    } catch (error) {
      console.error("Failed to fetch roles:", error);
      throw error;
    }
  },

  /**
   * Create a New Role
   * POST /api/rbac/roles/
   * @param {Object} roleData - { code, name }
   */
  createRole: async (roleData) => {
    try {
      const response = await api.post(ROLE_API_URL, roleData);
      return response.data;
    } catch (error) {
      console.error("Failed to create role:", error);
      throw error;
    }
  },

  /**
   * Get Role by ID
   * GET /api/rbac/roles/{id}/
   */
  getRoleById: async (id) => {
    try {
      const response = await api.get(`${ROLE_API_URL}${id}/`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch role ${id}:`, error);
      throw error;
    }
  },

  /**
   * Update Role
   * PUT /api/rbac/roles/{id}/
   */
  updateRole: async (id, roleData) => {
    try {
      const response = await api.put(`${ROLE_API_URL}${id}/`, roleData);
      return response.data;
    } catch (error) {
      console.error(`Failed to update role ${id}:`, error);
      throw error;
    }
  },

  /**
   * Delete Role
   * DELETE /api/rbac/roles/{id}/
   */
  deleteRole: async (id) => {
    try {
      await api.delete(`${ROLE_API_URL}${id}/`);
    } catch (error) {
      console.error(`Failed to delete role ${id}:`, error);
      throw error;
    }
  },

  /**
   * Assign a Role to a User
   * POST /api/rbac/assign-role/
   * @param {number} userId
   * @param {number} roleId
   */
  assignRoleToUser: async (userId, roleId) => {
    try {
      const response = await api.post("rbac/assign-role/", {
        user: userId,
        role: roleId,
      });
      return response.data;
    } catch (error) {
      console.error("Failed to assign role to user:", error);
      throw error;
    }
  },
};
