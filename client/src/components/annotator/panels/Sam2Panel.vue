<template>
  <div v-show="showme">
    <PanelInputNumber
      v-model:value="sam2.settings.threshold"
      name="Threshold"
      min="0"
      max="100"
      step="0.1"
      @update="sam2.settings.threshold = $event"
    />
    <PanelInputNumber
      v-model:value="sam2.settings.maxhole"
      name="Max Hole Area"
      min="0"
      max="100"
      step="0.1"
      @update="sam2.settings.maxhole = $event"
    />
    <PanelInputNumber
      v-model:value="sam2.settings.maxsprinkle"
      name="Max Sprinkle Area"
      min="0"
      max="100"
      step="0.1"
      @update="sam2.settings.maxsprinkle = $event"
    />
    <PanelInputDropdown
     v-model:value="sam2.settings.weightsFile"
      name="Model File"
      :values="weightsFiles"
      @update="sam2.settings.weightsFile = $event"
    />
  </div>
</template>

<script setup>
import PanelInputDropdown from "@/components/PanelInputDropdown.vue";
import PanelInputNumber from "@/components/PanelInputNumber.vue";
import modelWeightsRequests from "@/models/models"
import { ref, inject, watchEffect, onMounted } from 'vue';

const sam2 = defineModel('sam2', { type: Object, required: true });

const showme = ref('false');
const getActiveTool = inject('getActiveTool');

// If we don't set a default value, the dropdown will not create correctly
const weightsFiles = ref({default: "default"});

watchEffect(() => {
    showme.value = sam2.value.name === getActiveTool();
});

onMounted(async () => {
  const modelWeights = await modelWeightsRequests.getModelWeights({modelName: "sam2"})
  weightsFiles.value = modelWeights;
});

</script>
