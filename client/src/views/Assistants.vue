<template>
  <div>
    <div style="padding-top: 55px" />
    <div
      class="album py-5 bg-light"
      style="overflow: auto; height: calc(100vh - 55px)"
    >
      <div class="container">
        <h2 class="text-center">
          Assistants
          <i
            class="fa fa-question-circle help-icon"
            data-bs-toggle="modal"
            data-bs-target="#helpAssistants"
            aria-hidden="true"
          />
        </h2>

        <p class="text-center">
          Loaded <strong>{{ assistantCount }}</strong> assistants.
        </p>

        <div class="row justify-content-md-center">
          <div
            class="col-md-auto btn-group"
            role="group"
            style="padding-bottom: 20px"
          >
            <button
              type="button"
              class="btn btn-success"
              data-bs-toggle="modal"
              data-bs-target="#createAssistants"
            >
              Create
            </button>
            <button
              type="button"
              class="btn btn-secondary"
              @click="updatePage()"
            >
              Refresh
            </button>
          </div>
        </div>

        <hr />

        <p v-if="assistants.length < 1" class="text-center">
          You need to create a assistant!
        </p>
        <div v-else>
          <Pagination
            v-model:page="page"
            :pages="pages"
            @pagechange="updatePage"
          />

          <div class="row">
            <AssistantCard
              v-for="assistant in assistants"
              :key="assistant.id"
              :assistant="assistant"
              @update-page="updatePage"
            />
          </div>
        </div>
      </div>
    </div>

    <GenericDialog
      id="createAssistants"
      action="Create"
      :actionIsValid="isFormValid"
      @click-action="createAssistant"
      title="Creating an Assistant"
    >
      <form>
        <div class="row mb-3 align-items-center">
          <div class="col-4 text-end">
            <label for="assistantType" class="form-label"
              >Assistant Type:</label
            >
          </div>
          <div class="col-8">
            <select
              id="assistantType"
              class="form-select"
              v-model="newAssistantForm.type"
            >
              <option v-for="type in Object.values(AssistantType)" :key="type">
                {{ type }}
              </option>
            </select>
          </div>
        </div>

        <div class="row mb-3 align-items-center">
          <div class="col-4 text-end">
            <label for="assistantName" class="form-label">Name:</label>
          </div>
          <div class="col-8">
            <input
              id="assistantName"
              v-model="newAssistantForm.name"
              class="form-control"
              :class="{
                'is-invalid': newAssistantForm.name.trim().length === 0,
              }"
              required
              placeholder="Name"
            />
          </div>
        </div>

        <div class="row mb-3 align-items-center">
          <div class="col-4 text-end">
            <label for="modelAssets" class="form-label">Model Assets:</label>
          </div>
          <div class="col-8">
            <input
              id="modelAssets"
              type="file"
              class="form-control"
              multiple
              @change="handleAssetsUpload"
            />
          </div>
        </div>
      </form>
    </GenericDialog>

    <div id="helpAssistants" class="modal fade" tabindex="-1" role="dialog">
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header justify-content-between">
            <h5 class="modal-title">Assistants</h5>
            <button
              type="button"
              class="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            More information can be found in the
            <a
              href="https://github.com/jsbroks/coco-annotator/wiki/Usage#creating-assistants"
            >
              getting started section </a
            >.
            <hr />
            <h6>What is a assistant?</h6>

            <hr />
            <h6>How do I create one?</h6>
            Click on the "Create" button found on this webpage. You must
            provided a name for the assistant.
          </div>
          <div class="modal-footer">
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

<script setup lang="ts">
import AssistantCard from "@/components/cards/AssistantCard.vue";
import Pagination from "@/components/Pagination.vue";
import Assistant from "@/models/assistants";
import GenericDialog from "@/components/GenericDialog.vue";

import { onMounted, computed, reactive, ref } from "vue";

import useAxiosRequest from "@/composables/axiosRequest";
const { axiosReqestError, axiosReqestSuccess } = useAxiosRequest();

import { useProcStore } from "@/store/index";
const procStore = useProcStore();

const assistantCount = ref(0);
const pages = ref(1);
const page = ref(1);
const limit = ref(50);
enum AssistantType {
  SAM2 = "sam2",
  ZIM = "zim",
}
type AssistantProps = {
  name: string;
  type: AssistantType;
  assets: File[];
};
const _formDefaults = {
  name: "",
  type: AssistantType.SAM2,
  assets: [],
};
const newAssistantForm = reactive<AssistantProps>(
  structuredClone(_formDefaults)
);
const assistants = ref([]);

const isFormValid = computed(() => {
  return newAssistantForm.name.length !== 0;
});

const handleAssetsUpload = (event) => {
  newAssistantForm.assets = event.target.files;
};

const updatePage = () => {
  const process = "Loading assistants";
  procStore.addProcess(process);

  const p = page.value;
  page.value = p;
  Assistant.allData({
    page: p,
    page_size: limit.value,
  })
    .then((response) => {
      assistants.value = response.data.assistants;
      page.value = response.data.pagination.page;
      pages.value = response.data.pagination.total_pages;
      assistantCount.value = response.data.pagination.total_results;
    })
    .finally(() => {
      procStore.removeProcess(process);
    });
};

const createAssistant = () => {
  if (newAssistantForm.name.length < 1) return;

  Assistant.create({
    assistant_name: newAssistantForm.name,
    assistant_type: newAssistantForm.type,
    asset_files: newAssistantForm.assets,
  })
    .then(() => {
      Object.assign(newAssistantForm, structuredClone(_formDefaults));
      updatePage();
      axiosReqestSuccess(
        "Creating Assistant",
        "Assistant successfully created"
      );
    })
    .catch((error) => {
      axiosReqestError(
        "Creating Assistant",
        JSON.stringify(error.response.data.message)
      );
    });
};

onMounted(() => {
  updatePage();
});
</script>

<style scoped>
.card-img-overlay {
  padding: 0 10px 0 0;
}

.icon-more {
  width: 10%;
  margin: 3px 0;
  padding: 0;
  float: right;
  color: black;
}

.help-icon {
  color: darkblue;
  font-size: 20px;
  display: inline;
}
</style>
