<template>
  <div class="col-md-3">
    <div class="card mb-4 box-shadow" @click="onCardClick">
      <div class="card-body">
        <span
          class="d-inline-block text-truncate"
          style="max-width: 75%; float: left"
        >
          <i
            class="fa fa-circle color-icon"
            aria-hidden="true"
            :style="{ color: assistant.color }"
          />
          <strong class="card-title">{{ assistant.name }}</strong>
        </span>

        <i
          :id="'dropdownAssistant' + assistant.id"
          class="card-text fa fa-ellipsis-v fa-x icon-more"
          data-bs-toggle="dropdown"
          aria-haspopup="true"
          aria-expanded="false"
          aria-hidden="true"
        />

        <br />

        <div>
          <p v-if="assistant.numberAnnotations > 0">
            {{ assistant.numberAnnotations }} objects have been made with this
            assistant.
          </p>
          <p v-else>No annotations use this assistant</p>
        </div>

        <div
          class="dropdown-menu"
          :aria-labelledby="'dropdownAssistant' + assistant.id"
        >
          <a class="dropdown-item" @click="onDeleteClick">Delete</a>
          <!--<a class="dropdown-item" @click="onDownloadClick"
            >Download COCO & Images</a
          >-->
          <button
            class="dropdown-item"
            data-bs-toggle="modal"
            :data-bs-target="'#assistantEdit' + assistant.id"
          >
            Edit
          </button>
        </div>
      </div>

      <div v-show="authStore.loginEnabled()" class="card-footer text-muted">
        Created by {{ assistant.creator }}
      </div>
    </div>

    <div
      :id="'assistantEdit' + assistant.id"
      ref="assistant_settings"
      class="modal fade"
      role="dialog"
      @hidden="resetAssistantSettings"
    >
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header justify-content-between">
            <h5 class="modal-title">Assistant: {{ assistant.name }}</h5>
            <button
              type="button"
              class="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <form>
              <div class="form-group">
                <label>Name</label>
                <input
                  type="text"
                  :value="name"
                  required="true"
                  class="form-control"
                  :class="{ 'is-invalid': name.length === 0 }"
                  @input="name = $event.target.value"
                />
              </div>

              <div class="form-group">
                <label>Superassistant</label>
                <input
                  type="text"
                  class="form-control"
                  :value="assistant.superassistant"
                  @input="superassistant = $event.target.value"
                />
              </div>

              <div class="form-group row">
                <label class="col-sm-2 col-form-label">Color</label>
                <div class="col-sm-9">
                  <input v-model="color" type="color" class="form-control" />
                </div>
              </div>

              <div class="form-group">
                <KeypointsDefinition
                  ref="keypoints"
                  v-model:keypoints-def="keypoint"
                  element-id="keypoints"
                  placeholder="Add a keypoint"
                />
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-success"
              :disabled="!isFormValid"
              :class="{ disabled: !isFormValid }"
              data-bs-dismiss="modal"
              @click="onUpdateClick"
            >
              Update
            </button>
            <button
              type="button"
              class="btn btn-secondary"
              data-bs-dismiss="modal"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, toRefs, reactive, onMounted, computed } from "vue";

import axios from "axios";
import KeypointsDefinition from "@/components/KeypointsDefinition.vue";
import useAxiosRequest from "@/composables/axiosRequest";

import { useAuthStore } from "@/store/user";
const authStore = useAuthStore();

const { axiosReqestError, axiosReqestSuccess } = useAxiosRequest();

const emit = defineEmits(["updatePage"]);
const keypoints = ref([]);

const props = defineProps({
  assistant: {
    type: Object,
    required: true,
  },
});

const assistant = ref(props.assistant);

const state = reactive({
  group: null,
  superassistant: assistant.value.superassistant,
  color: props.assistant.color,
  metadata: [],
  keypoint: {
    labels: [...assistant.value.keypoint_labels],
    edges: [...assistant.value.keypoint_edges],
    colors: [...assistant.value.keypoint_colors],
  },
  name: assistant.value.name,
  isMounted: false,
});

const { group, superassistant, color, metadata, keypoint, name } =
  toRefs(state);
defineExpose({ group, superassistant, color, metadata, keypoint, name });

onMounted(() => {
  state.isMounted = true;
  resetAssistantSettings();
});

const isFormValid = computed(() => {
  return (
    state.isMounted &&
    name.value.length !== 0 &&
    keypoints.value &&
    keypoints.value.valid
  );
});

const resetAssistantSettings = () => {
  name.value = props.assistant.name;
  superassistant.value = props.assistant.superassistant;
  color.value = props.assistant.color;
  keypoint.value = {
    labels: [...props.assistant.keypoint_labels],
    edges: [...props.assistant.keypoint_edges],
    colors: [...props.assistant.keypoint_colors],
  };
};
const onCardClick = () => {};
const onDownloadClick = () => {};
const onDeleteClick = async () => {
  await axios.delete("/api/assistant/" + props.assistant.id);
  emit("updatePage");
};

const onUpdateClick = () => {
  try {
    axios.put("/api/assistant/" + assistant.value.id, {
      name: name.value,
      color: color.value,
      superassistant: superassistant.value,
      metadata: metadata.value,
      keypoint_edges: keypoint.value.edges,
      keypoint_labels: keypoint.value.labels,
      keypoint_colors: keypoint.value.colors,
    });
    axiosReqestSuccess("Updating Assistant", "Assistant successfully updated");

    assistant.value.name = name.value;
    assistant.value.superassistant = superassistant.value;
    assistant.value.color = color.value;
    assistant.value.metadata = { ...metadata.value };
    assistant.value.keypoint_edges = [...keypoint.value.edges];
    assistant.value.keypoint_labels = [...keypoint.value.labels];
    assistant.value.keypoint_colors = [...keypoint.value.colors];
    emit("updatePage");
  } catch (error) {
    console.error("Error updating assistant:", error.message);
    axiosReqestError("Updating Assistant", error.message);
    emit("updatePage");
  }
};
</script>

<style scoped>
.icon-more {
  width: 10%;
  margin: 3px 0;
  padding: 0;
  float: right;
  color: black;
}

.card-body {
  padding: 10px 10px 0 10px;
}

.color-icon {
  display: inline;
  margin: 0;
  padding-right: 10px;
}

.card-footer {
  padding: 2px;
  font-size: 11px;
}
</style>
