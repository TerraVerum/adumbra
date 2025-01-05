import axios from "axios";

const baseURL = "/api/model/";

export default {
  getModelWeights({modelName}) {
    return axios.get(baseURL + 'weights', {
      params: {
        model: modelName,
      },
    }).catch(function (error) {
        console.error("Error in getModelWeights", error.toJSON());
        return {
            default: "Default",
          };
      });
  },
};
