import axios from "axios";

const baseURL = "/api/image/";

export default {
  allData(params) {
    return axios.get(baseURL, {
      params: {
        ...params,
      },
    });
  },
  /**
   * Creates a new image entry in the dataset.
   *
   * @param {File} image - The image file to be uploaded.
   * @param {Number} datasetId - The ID of the dataset to which the image belongs.
   * @returns {Promise} - A promise that resolves to the response of the POST request.
   */
  create(image, datasetId) {
    const formData = new FormData();
    formData.append("image", image);
    formData.append("dataset_id", datasetId);
    return axios.post(baseURL, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
};
