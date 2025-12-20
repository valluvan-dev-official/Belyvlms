import { api } from "./authentication";

// ============================================
// PERMISSION SERVICE CONFIGURATION
// ============================================

const PERMISSION_API_URL = "rbac/permissions/";
const ASSIGN_API_URL = "rbac/role-permissions/";

export const PermissionService = {
  /**
   * Get all Permissions
   * GET /api/rbac/permissions/
   */
  getPermissions: async () => {
    try {
      const response = await api.get(PERMISSION_API_URL);
      return response.data;
    } catch (error) {
      console.error("Failed to fetch permissions:", error);
      throw error;
    }
  },

  /**
   * Create a New Permission
   * POST /api/rbac/permissions/
   * @param {Object} permData - { code, name, module }
   */
  createPermission: async (permData) => {
    try {
      const response = await api.post(PERMISSION_API_URL, permData);
      return response.data;
    } catch (error) {
      console.error("Failed to create permission:", error);
      throw error;
    }
  },

  /**
   * Assign Permissions to a Role
   * POST /api/rbac/role-permissions/
   * @param {number} roleId
   * @param {Array<number>} permissionIds
   */
  assignPermissionsToRole: async (roleId, permissionIds) => {
    try {
      const response = await api.post(ASSIGN_API_URL, {
        role_id: roleId,
        permission_ids: permissionIds,
      });
      return response.data;
    } catch (error) {
      console.error("Failed to assign permissions:", error);
      throw error;
    }
  },

  /**
   * Get Permissions for a specific Role
   * GET /api/rbac/role-permissions/?role_id={id}
   */
  getRolePermissions: async (roleId) => {
    try {
      const response = await api.get(`${ASSIGN_API_URL}?role_id=${roleId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch permissions for role ${roleId}:`, error);
      throw error;
    }
  },
};
