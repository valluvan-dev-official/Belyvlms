import { api } from "../../authentication";

// ============================================
// ROLE CONFIGURATION SERVICE (GENERIC PROFILES)
// ============================================

const ROLE_CONFIGS_URL = "profiles/configs/";
const PROFILE_FIELDS_URL = "profiles/fields/";
const ROLES_URL = "rbac/roles/"; // To fetch list of available roles

export const RoleConfigService = {
  /**
   * Get All Role Configurations
   * Returns list of roles and whether they use Generic Profile or Dedicated Model.
   * GET /api/profiles/configs/
   */
  getConfigs: async () => {
    try {
      const response = await api.get(ROLE_CONFIGS_URL);
      return response.data;
    } catch (error) {
      console.error("Failed to fetch role configs:", error);
      throw error;
    }
  },

  /**
   * Get Specific Role Config with Field Definitions
   * GET /api/profiles/configs/{id}/
   * @param {number} configId 
   */
  getConfigDetails: async (configId) => {
    try {
      const response = await api.get(`${ROLE_CONFIGS_URL}${configId}/`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch config ${configId}:`, error);
      throw error;
    }
  },

  /**
   * Create a New Role Configuration
   * POST /api/profiles/configs/
   * @param {Object} configData - { role: roleId, has_dedicated_profile: false, ... }
   */
  createConfig: async (configData) => {
    try {
      const response = await api.post(ROLE_CONFIGS_URL, configData);
      return response.data;
    } catch (error) {
      console.error("Failed to create config:", error);
      throw error;
    }
  },

  /**
   * Update a Role Configuration
   * PUT/PATCH /api/profiles/configs/{id}/
   * @param {number} configId
   * @param {Object} configData
   */
  updateConfig: async (configId, configData) => {
    try {
      const response = await api.patch(`${ROLE_CONFIGS_URL}${configId}/`, configData);
      return response.data;
    } catch (error) {
      console.error(`Failed to update config ${configId}:`, error);
      throw error;
    }
  },

  /**
   * Create a Custom Field for a Role (Generic Profile)
   * POST /api/profiles/fields/
   * Payload must include 'config' ID.
   */
  addCustomField: async (configId, fieldData) => {
    // fieldData = { name: 'university', label: 'University Name', field_type: 'TEXT', ... }
    const payload = { config: configId, ...fieldData };
    try {
      const response = await api.post(PROFILE_FIELDS_URL, payload);
      return response.data;
    } catch (error) {
      console.error("Failed to add custom field:", error);
      throw error;
    }
  },

  /**
   * Update a Custom Field
   * PATCH /api/profiles/fields/{fieldId}/
   */
  updateCustomField: async (fieldId, fieldData) => {
    try {
      const response = await api.patch(`${PROFILE_FIELDS_URL}${fieldId}/`, fieldData);
      return response.data;
    } catch (error) {
      console.error(`Failed to update field ${fieldId}:`, error);
      throw error;
    }
  },

  /**
   * Delete a Custom Field
   * DELETE /api/profiles/fields/{fieldId}/
   */
  deleteCustomField: async (fieldId) => {
    try {
      await api.delete(`${PROFILE_FIELDS_URL}${fieldId}/`);
    } catch (error) {
      console.error(`Failed to delete field ${fieldId}:`, error);
      throw error;
    }
  },

  /**
   * Fetch All Roles (RBAC)
   * Helper to populate the "Role" dropdown in the UI.
   */
  getAllRoles: async () => {
    try {
      const response = await api.get(ROLES_URL);
      return response.data;
    } catch (error) {
      console.error("Failed to fetch roles:", error);
      throw error;
    }
  }
};
