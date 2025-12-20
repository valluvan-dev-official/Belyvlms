import { api } from "./authentication";

// ============================================
// TRAINER SERVICE CONFIGURATION
// ============================================

const TRAINER_API_URL = "trainersdb/trainers/";

export const TrainerService = {
  /**
   * Get All Trainers (Paginated & Filtered)
   * GET /api/trainersdb/trainers/
   * @param {Object} params - Query params (page, search, location, etc.)
   */
  getTrainers: async (params = {}) => {
    try {
      const response = await api.get(TRAINER_API_URL, { params });
      return response.data;
    } catch (error) {
      console.error("Failed to fetch trainers:", error);
      throw error;
    }
  },

  /**
   * Get Single Trainer by ID
   * GET /api/trainersdb/trainers/{id}/
   */
  getTrainerById: async (id) => {
    try {
      const response = await api.get(`${TRAINER_API_URL}${id}/`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch trainer ${id}:`, error);
      throw error;
    }
  },

  /**
   * Create New Trainer
   * POST /api/trainersdb/trainers/
   * @param {FormData} trainerData - Use FormData for file uploads (profile pic)
   */
  createTrainer: async (trainerData) => {
    try {
      const response = await api.post(TRAINER_API_URL, trainerData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      return response.data;
    } catch (error) {
      console.error("Failed to create trainer:", error);
      throw error;
    }
  },

  /**
   * Update Trainer
   * PUT /api/trainersdb/trainers/{id}/
   * @param {number} id
   * @param {FormData} trainerData
   */
  updateTrainer: async (id, trainerData) => {
    try {
      const response = await api.put(`${TRAINER_API_URL}${id}/`, trainerData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      return response.data;
    } catch (error) {
      console.error(`Failed to update trainer ${id}:`, error);
      throw error;
    }
  },

  /**
   * Delete Trainer
   * DELETE /api/trainersdb/trainers/{id}/
   */
  deleteTrainer: async (id) => {
    try {
      await api.delete(`${TRAINER_API_URL}${id}/`);
    } catch (error) {
      console.error(`Failed to delete trainer ${id}:`, error);
      throw error;
    }
  },
};
