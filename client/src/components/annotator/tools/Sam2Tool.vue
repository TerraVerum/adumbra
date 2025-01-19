<template>
  <div>
    <i
      v-tooltip.right="tooltip"
      class="fa fa-x"
      :class="icon"
      :style="{ color: iconColor }"
      @click="click"
    />
    <br />
  </div>
</template>
<script setup>
import paper from "paper";
import { ref, watch, inject, onMounted } from "vue";

import { sam2Segmentation } from "@/assistants-api/sdk.gen";
import { useTools } from "@/composables/toolBar/tools";

const getCurrentAnnotation = inject("getCurrentAnnotation");
const getImageRaster = inject("getImageRaster");

const { click, state, iconColor, tooltip, name, cursor } = useTools();

const scale = defineModel("scale", { type: Number, default: 1 });

name.value = "SAM2";
cursor.value = "crosshair";
const icon = ref("fa-crosshairs");

const settings = ref({
  threshold: 0,
  max_hole: 0,
  max_sprinkle: 0,
  assistantName: "sam2",
});

let paperPoint = null;
const points = ref([]);

const localCurrentAnnotation = ref(null);
const localImageRaster = ref(null);

watch(
  () => getImageRaster(),
  (value) => {
    localImageRaster.value = value;
  },
);

watch(
  () => getCurrentAnnotation(),
  (value) => {
    localCurrentAnnotation.value = value;
  },
);

function createPoint(point) {
  paperPoint = new paper.Path.Circle(point, 5);
  paperPoint.fillColor = localCurrentAnnotation.value.color;
  paperPoint.data.point = point;
  points.value.push(paperPoint);
}

function onMouseDown(event) {
  if (state.isActive) {
    createPoint(event.point);
    checkPoints(points.value);
  }
}

function createPath(segments, width, height) {
  const center = new paper.Point(width, height);
  const compoundPath = new paper.CompoundPath();
  segments.forEach((polygon) => {
    const path = new paper.Path();
    for (let j = 0; j < polygon.length; j += 2) {
      const point = new paper.Point(polygon[j], polygon[j + 1]);
      path.add(point.subtract(center));
    }
    path.closePath();
    compoundPath.addChild(path);
  });
  return compoundPath;
}

// original code was watching for new points, but it seem's to be a bug between Vue3 and paper.js.
// so we call function directly
function checkPoints(newPoints) {
  if (newPoints.length == 1) {
    let currentAnnotation = localCurrentAnnotation.value;
    let pointsList = [];
    let width = localImageRaster.value.width / 2;
    let height = localImageRaster.value.height / 2;
    newPoints.forEach((point) => {
      let pt = point.position;
      pointsList.push([Math.round(width + pt.x), Math.round(height + pt.y)]);
    });

    let canvas = getImageRaster().canvas;
    canvas.toBlob((blob) => {
      if (!blob) return;
      sam2Segmentation({
        body: {
          assistant_name: settings.value.assistantName,
          // https://github.com/hey-api/openapi-ts/issues/1585 means list[list[number]]
          // doesn't convert correctly in form data, so use an explicitly stringified
          // version in the meantime
          foreground_xy: JSON.stringify(pointsList),
          parameters: {},
          image: blob,
        },
      })
        .then((response) => {
          if (response.error) {
            console.error(response.error);
            return;
          }
          let compoundPath = createPath(
            response.data.segmentation,
            width,
            height,
          );
          currentAnnotation.unite(compoundPath);
        })
        .finally(() => {
          points.value = [];
          paperPoint.removeSegments();
        });
    });
  }
}

onMounted(() => {
  state.tool.onMouseDown = onMouseDown;
  // state.tool.onMouseDrag = onMouseDrag;
  // state.tool.onMouseMove = onMouseMove;
  // state.tool.onMouseUp = onMouseUp;
});

defineExpose({ points, settings, name });
</script>
