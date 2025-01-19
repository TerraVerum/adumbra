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

        <!-- <div>
          <p v-if="assistant.numberAnnotations > 0">
            {{ assistant.numberAnnotations }} objects have been made with this
            assistant.
          </p>
          <p v-else>No annotations use this assistant</p>
        </div> -->

        <div
          class="dropdown-menu"
          :aria-labelledby="'dropdownAssistant' + assistant.id"
        >
          <a class="dropdown-item" @click="onDeleteClick">Delete</a>
          <!-- <button
            class="dropdown-item"
            data-bs-toggle="modal"
            :data-bs-target="'#assistantEdit' + assistant.id"
          >
            Edit
          </button> -->
        </div>
      </div>

      <!-- <div v-show="authStore.loginEnabled()" class="card-footer text-muted">
        Created by {{ assistant.creator }}
      </div> -->
    </div>

    <GenericDialog
      :id="'assistantEdit' + assistant.id"
      :title="'Edit Assistant: ' + assistant.name"
      action="Update"
      :actionIsValid="isFormValid"
      @click-action="onUpdateClick"
    >
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

        <div class="form-group row">
          <label class="col-sm-2 col-form-label">Color</label>
          <div class="col-sm-9">
            <input v-model="color" type="color" class="form-control" />
          </div>
        </div>
      </form>
    </GenericDialog>
  </div>
</template>

<script setup>
import GenericDialog from "@/components/GenericDialog.vue";
import useAxiosRequest from "@/composables/axiosRequest";
import axios from "axios";
import { computed, onMounted, reactive, ref, toRefs } from "vue";

import { useAuthStore } from "@/store/user";
const authStore = useAuthStore();

const { axiosReqestError, axiosReqestSuccess } = useAxiosRequest();

const emit = defineEmits(["updatePage"]);

const props = defineProps({
  assistant: {
    type: Object,
    required: true,
  },
});

const assistant = ref(props.assistant);

const state = reactive({
  group: null,
  color: props.assistant.color,
  metadata: [],
  name: assistant.value.name,
  isMounted: false,
});

const { group, color, metadata, name } = toRefs(state);
defineExpose({ group, color, metadata, name });

onMounted(() => {
  state.isMounted = true;
  resetAssistantSettings();
});

const isFormValid = computed(() => {
  return state.isMounted && name.value.length !== 0;
});

const resetAssistantSettings = () => {
  name.value = props.assistant.name;
  color.value = props.assistant.color;
};
const onCardClick = () => {};
const onDownloadClick = () => {};
const onDeleteClick = async () => {
  await axios.delete("/api/assistants/" + props.assistant.id);
  emit("updatePage");
  axiosReqestSuccess("Deleting Assistant", "Assistant successfully deleted");
};

const onUpdateClick = () => {
  try {
    axios.put("/api/assistants/" + assistant.value.id, {
      name: name.value,
      color: color.value,
      metadata: metadata.value,
    });

    assistant.value.name = name.value;
    assistant.value.color = color.value;
    assistant.value.metadata = { ...metadata.value };
    axiosReqestSuccess("Updating Assistant", "Assistant successfully updated");
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
