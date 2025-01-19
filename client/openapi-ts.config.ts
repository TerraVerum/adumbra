import { defineConfig } from "@hey-api/openapi-ts";
import { defaultPlugins } from "@hey-api/openapi-ts";

export default defineConfig({
  client: "@hey-api/client-axios",
  // Make sure ia server is running to provide the openapi.json spec
  input: "http://localhost:6001/openapi.json",
  output: "src/assistants-api",
  plugins: [
    ...defaultPlugins,
    {
      enums: "javascript",
      name: "@hey-api/typescript",
    },
    "@hey-api/transformers",
  ],
});
