<template>
  <div class="col-md-3">
    <div class="card mb-4 box-shadow">
      <img
        v-if="imageUrl"
        :src="imageUrl"
        class="card-img-top"
        style="width: 100%; display: block"
        @click="onCardClick"
        @error="onImageError"
      />

      <!-- Card Body -->
      <div class="card-body">
        <span
          class="d-inline-block text-truncate"
          style="max-width: 85%; float: left"
        >
          <strong class="card-title">{{ title }}</strong>
        </span>

        <i
          id="moreActions"
          class="card-text fa fa-ellipsis-v fa-x icon-more"
          data-bs-toggle="dropdown"
          aria-haspopup="true"
          aria-expanded="false"
          aria-hidden="true"
        />

        <br />

        <div v-for="(action, name) in nameActionMap" :key="name">
          class="dropdown-menu" :aria-labelledby="'dropdownDataset' +
          dataset.id" >
          <button class="dropdown-item" data-bs-toggle="modal" @click="action">
            {{ name }}
          </button>
        </div>
      </div>

      <div v-if="footerText" class="card-footer text-muted">
        {{ footerText }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  imageUrl?: string;
  title: string;
  nameActionMap: { [key: string]: () => void };
  footerText?: string;
  onCardClick: () => void;
  onImageError: () => void;
}>();
</script>

<style scoped>
.card-body {
  padding: 10px 10px 0 10px;
}

p {
  margin: 0;
  padding: 0 0 3px 0;
}

.list-group-item {
  height: 21px;
  font-size: 13px;
  padding: 2px;
  background-color: #4b5162;
}
.icon-more {
  width: 10%;
  margin: 3px 0;
  padding: 0;
  float: right;
  color: black;
}

.card-footer {
  padding: 2px;
  font-size: 11px;
}
</style>
