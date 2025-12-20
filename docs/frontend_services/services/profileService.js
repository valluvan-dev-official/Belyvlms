import { api } from "./authentication";

// ============================================
// PROFILE & ONBOARDING SERVICE CONFIGURATION
// ============================================

const PROFILE_API_URL = "profiles/";

export const ProfileService = {
  /**
   * Get Role Profile Configurations
   * GET /api/profiles/configs/
   */
  getProfileConfigs: async () => {
    try {
      const response = await api.get(`${PROFILE_API_URL}configs/`);
      return response.data;
    } catch (error) {
      console.error("Failed to fetch profile configs:", error);
      throw error;
    }
  },

  /**
   * Onboard a New User
   * POST /api/profiles/onboard/
   * @param {Object} userData - User and Profile data
   */
  onboardUser: async (userData) => {
    try {
      const response = await api.post(`${PROFILE_API_URL}onboard/`, userData);
      return response.data;
    } catch (error) {
      console.error("Failed to onboard user:", error);
      throw error;
    }
  },
};
