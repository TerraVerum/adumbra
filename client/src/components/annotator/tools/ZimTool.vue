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
<script setup lang="ts">
import paper from "paper";
import { inject, onMounted, ref, watch } from "vue";

import { zimSegmentation } from "@/assistants-api/sdk.gen";
import Annotation from "@/components/annotator/Annotation.vue";
import { useTools } from "@/composables/toolBar/tools";

const getCurrentAnnotation = inject(
  "getCurrentAnnotation",
) as () => typeof Annotation;
const getImageRaster = inject("getImageRaster") as () => paper.Raster;

const { click, state, iconColor, tooltip, name, cursor } = useTools();

const scale = defineModel("scale", { type: Number, default: 1 });

name.value = "ZIM";
cursor.value = "crosshair";
const icon = ref("fa-crosshairs");

const settings = ref({
  padding: 50,
  threshold: 80,
  assistantName: "zim",
});

let paperPoint: paper.Path.Circle | null = null;
const points = ref<paper.Path.Circle[]>([]);

const localCurrentAnnotation = ref<typeof Annotation | null>(null);
const localImageRaster = ref<paper.Raster | null>(null);

watch(
  () => getImageRaster(),
  (value: paper.Raster) => {
    localImageRaster.value = value;
  },
);

watch(
  () => getCurrentAnnotation(),
  (value: any) => {
    localCurrentAnnotation.value = value;
  },
);

function createPoint(point: paper.Point): void {
  paperPoint = new paper.Path.Circle(point, 5);
  paperPoint.fillColor = localCurrentAnnotation.value!.color!;
  paperPoint.data.point = point;
  points.value.push(paperPoint);
}

function onMouseDown(event: paper.ToolEvent): void {
  if (state.isActive) {
    createPoint(event.point);
    checkPoints(points.value);
  }
}

function createPath(
  segments: number[][],
  width: number,
  height: number,
): paper.CompoundPath {
  const center = new paper.Point(width, height);
  const compoundPath = new paper.CompoundPath({});
  segments.forEach((polygon: number[]) => {
    const path = new paper.Path();
    for (let j = 0; j < polygon.length; j += 2) {
      const point = new paper.Point(polygon[j]!, polygon[j + 1]!);
      path.add(point.subtract(center));
    }
    path.closePath();
    compoundPath.addChild(path);
  });
  return compoundPath;
}

// original code was watching for new points, but it seem's to be a bug between Vue3 and paper.js.
// so we call function directly
function checkPoints(newPoints: paper.Path.Circle[]): void {
  if (newPoints.length != 1 || paperPoint === null) {
    return;
  }
  let currentAnnotation = localCurrentAnnotation.value!;
  let width = localImageRaster.value?.width! / 2;
  let height = localImageRaster.value?.height! / 2;
  let pointsList = newPoints.map((point) => {
    let pt = point.position;
    return [Math.round(width + pt.x), Math.round(height + pt.y)];
  });

  let canvas = getImageRaster().canvas;
  canvas.toBlob((blob: Blob | null) => {
    if (!blob) return;
    zimSegmentation({
      body: {
        assistant_name: settings.value.assistantName,
        // https://github.com/hey-api/openapi-ts/issues/1585 means list[list[number]]
        // doesn't convert correctly in form data, so use an explicitly stringified
        // version in the meantime
        foreground_xy: JSON.stringify(pointsList) as unknown as number[][],
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
        paperPoint!.removeSegments();
      });
  });
}

onMounted(() => {
  const tool = state.tool as paper.Tool | null;
  tool!.onMouseDown = onMouseDown;
  // state.tool.onMouseDrag = onMouseDrag;
  // state.tool.onMouseMove = onMouseMove;
  // state.tool.onMouseUp = onMouseUp;
});

defineExpose({ points, settings, name });
</script>
