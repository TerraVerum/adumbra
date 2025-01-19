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
      v-model:value="sam2.settings.max_hole"
      name="Max Hole Area"
      min="0"
      max="100"
      step="0.1"
      @update="sam2.settings.max_hole = $event"
    />
    <PanelInputNumber
      v-model:value="sam2.settings.max_sprinkle"
      name="Max Sprinkle Area"
      min="0"
      max="100"
      step="0.1"
      @update="sam2.settings.max_sprinkle = $event"
    />
    <PanelInputDropdown
      v-model:value="sam2.settings.assistantName"
      name="Assistant Name"
      :values="sam2Assistants"
      @update="sam2.settings.assistantName = $event"
    />
  </div>
</template>

<script setup>
import PanelInputDropdown from "@/components/PanelInputDropdown.vue";
import PanelInputNumber from "@/components/PanelInputNumber.vue";
import assistantsRequests from "@/models/models";
import { ref, inject, watchEffect, onMounted } from "vue";

const sam2 = defineModel("sam2", { type: Object, required: true });

const showme = ref("false");
const getActiveTool = inject("getActiveTool");

// If we don't set a default value, the dropdown will not create correctly
const sam2Assistants = ref({ sam2: "sam2" });

watchEffect(() => {
  showme.value = sam2.value.name === getActiveTool();
});

onMounted(async () => {
  const response = await assistantsRequests.getAssistants({
    modelName: "sam2",
  });
  sam2Assistants.value = response.data.assistants.reduce((acc, assistant) => {
    acc[assistant.name] = assistant.name;
    return acc;
  }, {});
});
</script>
