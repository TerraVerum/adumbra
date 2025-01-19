<template>
  <div v-show="showme">
    <PanelInputNumber
      v-model:value="zim.settings.padding"
      name="Padding"
      min="0"
      max="1000"
      step="2"
      @update="zim.settings.padding = $event"
    />
    <PanelInputNumber
      v-model:value="zim.settings.threshold"
      name="Threshold"
      min="0"
      max="100"
      step="5"
      @update="zim.settings.threshold = $event"
    />
    <PanelInputDropdown
      v-model:value="zim.settings.assistantName"
      name="Assistant Name"
      :values="zimAssistants"
      @update="zim.settings.assistantName = $event"
    />
  </div>
</template>

<script setup>
import PanelInputNumber from "@/components/PanelInputNumber.vue";
import PanelInputDropdown from "@/components/PanelInputDropdown.vue";
import { assistant_type, getAssistants } from "@/assistants-api/";
import { ref, inject, watchEffect, onMounted } from "vue";

const zim = defineModel("zim", { type: Object, required: true });

const showme = ref("false");
const getActiveTool = inject("getActiveTool");

// If we don't set a default value, the dropdown will not create correctly
const zimAssistants = ref({ zim: "zim" });

watchEffect(() => {
  showme.value = zim.value.name === getActiveTool();
});

onMounted(async () => {
  const response = await getAssistants({
    query: { assistant_type: assistant_type.ZIM },
  });
  if (response.error) {
    console.error(response.error);
    return;
  }

  zimAssistants.value = response.data.assistants.reduce((acc, assistant) => {
    acc[assistant.name] = assistant.name;
    return acc;
  }, {});
});
</script>
