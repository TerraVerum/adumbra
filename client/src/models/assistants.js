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
  create({ assistant_name, assistant_type, asset_files }) {
    const form = new FormData();
    form.append("assistant_name", assistant_name);
    form.append("assistant_type", assistant_type);
    for (let i = 0; i < asset_files.length; i++) {
      form.append("assets", asset_files[i]);
    }
    return axios.post(baseURL, form, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
};
