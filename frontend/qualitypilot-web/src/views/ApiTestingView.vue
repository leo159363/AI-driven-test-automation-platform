<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { getApiEndpoints } from "../services/api";
import type { ApiEndpointItem } from "../types";

const endpoints = ref<ApiEndpointItem[]>([]);
const selectedPath = ref("");
const error = ref("");

const selectedEndpoint = computed(
  () => endpoints.value.find((item) => item.path === selectedPath.value) ?? endpoints.value[0],
);

const folders = computed(() => {
  const groups = new Map<string, ApiEndpointItem[]>();
  for (const endpoint of endpoints.value) {
    const moduleName = endpoint.path.includes("login") ? "auth" : "file";
    groups.set(moduleName, [...(groups.get(moduleName) ?? []), endpoint]);
  }
  return Array.from(groups.entries());
});

onMounted(async () => {
  try {
    const data = await getApiEndpoints();
    endpoints.value = data.items;
    selectedPath.value = data.items[0]?.path ?? "";
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
});
</script>

<template>
  <section>
    <div class="page-title">
      <div>
        <h2>API 测试中心</h2>
        <p>参考 Postman / Apifox / WHartTest 的接口测试视图，先展示接口目录和 pytest 关联。</p>
      </div>
      <button class="primary-button" disabled>运行接口测试</button>
    </div>

    <div v-if="error" class="error-banner">接口数据加载失败：{{ error }}</div>

    <div class="split-layout">
      <aside class="panel">
        <h3>接口目录</h3>
        <div v-for="[folder, items] in folders" :key="folder" class="stack">
          <strong>{{ folder }}</strong>
          <button
            v-for="endpoint in items"
            :key="`${endpoint.name}-${endpoint.related_case_id}`"
            class="ghost-button"
            type="button"
            @click="selectedPath = endpoint.path"
          >
            {{ endpoint.path }}
          </button>
        </div>
      </aside>

      <div class="panel">
        <h3>全部接口</h3>
        <div class="stack">
          <article
            v-for="endpoint in endpoints"
            :key="`${endpoint.name}-${endpoint.related_case_id}`"
            class="endpoint-card"
            :class="{ selected: endpoint === selectedEndpoint }"
            @click="selectedPath = endpoint.path"
          >
            <div class="item-title">
              <strong>{{ endpoint.name }}</strong>
              <span class="method-pill">{{ endpoint.method }}</span>
            </div>
            <p class="path-text">{{ endpoint.path }}</p>
            <p class="muted">关联用例：{{ endpoint.related_case_id }}</p>
          </article>
        </div>
      </div>

      <div class="panel">
        <h3>接口详情</h3>
        <template v-if="selectedEndpoint">
          <div class="item-title">
            <strong>{{ selectedEndpoint.name }}</strong>
            <span class="method-pill">{{ selectedEndpoint.method }}</span>
          </div>
          <p class="path-text">{{ selectedEndpoint.path }}</p>

          <h3>Request</h3>
          <pre class="code-block">{{ selectedEndpoint.request_example }}</pre>

          <h3>Assertions</h3>
          <pre class="code-block">{{ selectedEndpoint.expected_result }}</pre>

          <h3>关联测试用例</h3>
          <span class="tag">{{ selectedEndpoint.related_case_id }}</span>
        </template>
        <div v-else class="empty-state">暂无接口数据</div>
      </div>
    </div>
  </section>
</template>

