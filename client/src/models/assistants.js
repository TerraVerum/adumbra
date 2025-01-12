import axios from "axios";

const baseURL = "/api/assistants/";

export default {
  allData(params) {
    return axios.get(baseURL, {
      params: {
        ...params,
      },
    });
  },
  create(create) {
    return axios.post(baseURL, { ...create });
  },
};
