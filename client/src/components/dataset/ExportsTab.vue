<template>
  <div class="container">
    <div class="card my-3 p-3 shadow-sm mr-2">
      <h6 class="border-bottom border-gray pb-2">
        <b>Exports</b>
      </h6>

      <div
        v-for="exp in datasetExports"
        :key="exp.id"
        class="media text-muted pt-3"
      >
        <div class="media-body lh-125 border-bottom border-gray">
          {{ exp.id }}. Exported
          {{ exp.ago.length > 0 ? exp.ago : 0 + " seconds" }} ago
          <div style="display: inline">
            <span
              v-for="(tag, index) in exp.tags"
              :key="index"
              class="badge badge-secondary"
              style="margin: 1px"
            >
              {{ tag }}
            </span>
          </div>
          <button
            class="btn btn-sm btn-success"
            style="float: right; margin: 2px; padding: 2px"
            @click="downloadExport(exp.id)"
          >
            Download
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  datasetExports: Array<{
    id: number;
    ago: string;
    tags: string[];
  }>;
  downloadExport: (id: number) => void;
}>();
</script>
