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

<script setup>
import Assistant from "@/models/assistants";
import AssistantCard from "@/components/cards/AssistantCard.vue";
import Pagination from "@/components/Pagination.vue";
import KeypointsDefinition from "@/components/KeypointsDefinition.vue";

import { ref, computed, watch, inject, onMounted, provide } from "vue";

import useAxiosRequest from "@/composables/axiosRequest";
const { axiosReqestError, axiosReqestSuccess } = useAxiosRequest();

import { useProcStore } from "@/store/index";
const procStore = useProcStore();

const assistantCount = ref(0);
const pages = ref(1);
const page = ref(1);
const limit = ref(50);
const range = ref(11);
const newAssistantName = ref("");
const newAssistantSuperassistant = ref("");
const newAssistantColor = ref(null);
const newAssistantKeypoint = ref({
  labels: [],
  edges: [],
  colors: [],
});
const assistants = ref([]);
const status = ref({
  data: { state: true, message: "Loading assistants" },
});
const keypoints = ref(null);

const updatePage = (p) => {
  const process = "Loading assistants";
  procStore.addProcess(process);

  p = p || page.value;
  page.value = p;
  Assistant.allData({
    page: p,
    limit: limit.value,
  })
    .then((response) => {
      assistants.value = response.data.assistants;
      page.value = response.data.pagination.page;
      pages.value = response.data.pagination.pages;
      assistantCount.value = response.data.pagination.total;
    })
    .finally(() => {
      procStore.removeProcess(process);
    });
};

const createAssistant = () => {
  if (newAssistantName.value.length < 1) return;

  Assistant.create({
    name: newAssistantName.value,
    superassistant: newAssistantSuperassistant.value,
    color: newAssistantColor.value,
    keypoint_labels: newAssistantKeypoint.value.labels,
    keypoint_edges: newAssistantKeypoint.value.edges,
    keypoint_colors: newAssistantKeypoint.value.colors,
  })
    .then(() => {
      newAssistantName.value = "";
      newAssistantSuperassistant.value = "";
      newAssistantColor.value = null;
      newAssistantKeypoint.value = {};
      updatePage();
    })
    .catch((error) => {
      axiosReqestError("Creating Assistant", error.response.data.message);
    });
};

const previousPage = () => {
  page.value -= 1;
  if (page.value < 1) {
    page.value = 1;
  }
  updatePage();
};

const nextPage = () => {
  page.value += 1;
  if (page.value > pages.value) {
    page.value = pages.value;
  }
  updatePage();
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
