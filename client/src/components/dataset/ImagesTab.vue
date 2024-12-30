<template>
  <div class="container">
    <ol class="breadcrumb">
      <li class="breadcrumb-item" />
      <li class="breadcrumb-item active">
        <button class="btn btn-sm btn-link" @click="clearFolders">
          {{ dataset.name }}
        </button>
      </li>
      <li
        v-for="(folder, folderId) in folders"
        :key="folderId"
        class="breadcrumb-item"
      >
        <button
          class="btn btn-sm btn-link"
          :disabled="folders[folders.length - 1] === folder"
          @click="removeFolder(folder)"
        >
          {{ folder }}
        </button>
      </li>
    </ol>

    <p v-if="images.length < 1" class="text-center">
      No images found in directory.
    </p>
    <div v-else>
      <Pagination v-model:page="page" :pages="pages" @pagechange="updatePage" />
      <div class="row">
        <ImageCard
          v-for="image in images"
          :key="image.id"
          :image="image"
          @updatePage="updatePage"
        />
      </div>
      <Pagination :pages="pages" v-model:page="page" @pagechange="updatePage" />
    </div>
  </div>
</template>

<script setup lang="ts">
import ImageCard from "@/components/cards/ImageCard.vue";
import Pagination from "@/components/Pagination.vue";

const page = defineModel<number>("page", { required: true });

defineProps<{
  dataset: {
    id: number;
    name: string;
  };
  images: Array<{ id: number; name: string }>;
  folders: string[];
  pages: number;
  updatePage: (page: number) => void;
  removeFolder: (folder: string) => void;
  clearFolders: () => void;
}>();
</script>
