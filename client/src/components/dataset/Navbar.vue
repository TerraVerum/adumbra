<template>
    <nav class="nav border-bottom shadow-sm" style="background-color: #4b5162">
      <a
        class="btn tab"
        :style="{ color: model == 'images' ? 'white' : 'darkgray' }"
        @click="model = 'images'"
      >
        <i class="fa fa-picture-o" aria-hidden="true" /> Images
      </a>
      <a
        class="btn tab"
        :style="{ color: model == 'exports' ? 'white' : 'darkgray' }"
        @click="model = 'exports'"
      >
        <i class="fa fa-share" aria-hidden="true" /> Exports
      </a>
      <a
        class="btn tab"
        :style="{ color: model == 'members' ? 'white' : 'darkgray' }"
        @click="model = 'members'"
      >
        <i class="fa fa-users" aria-hidden="true" /> Members
      </a>
      <a
        class="btn tab"
        :style="{ color: model == 'statistics' ? 'white' : 'darkgray' }"
        @click="model = 'statistics'"
      >
        <i class="fa fa-bar-chart" aria-hidden="true" /> Statistics
      </a>
      <a
        class="btn tab"
        :style="{ color: model == 'settings' ? 'white' : 'darkgray' }"
        @click="model = 'settings'"
      >
        <i class="fa fa-cog" aria-hidden="true" /> Settings
      </a>
    </nav>
</template>
  
<script setup lang="ts">
import { defineModel } from 'vue';

const model = defineModel<string>({ required: true, type: String });

</script>
  
  <style scoped>
.nav {
    display: flex;
    justify-content: space-around;
    padding: 10px;
}

.btn {
    cursor: pointer;
}
</style>