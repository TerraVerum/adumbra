import axios from "axios";

const baseURL = "/api/assistants/";

export default {
  getAssistants({ modelName }) {
    return axios
      .get(baseURL, {
        params: {
          assistant_type: modelName,
        },
      })
      .catch(function (error) {
        // We exppect this to never happen
        console.error("Error in getAssistants", error.toJSON());
      });
  },
};
