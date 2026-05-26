<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { getWebTestScripts } from "../services/api";
import type { WebTestScript } from "../types";

const scripts = ref<WebTestScript[]>([]);
const selectedScriptId = ref("");
const loading = ref(false);
const error = ref("");

const selectedScript = computed(
  () => scripts.value.find((item) => item.script_id === selectedScriptId.value) ?? scripts.value[0],
);

const readyCount = computed(() => scripts.value.filter((item) => item.status === "ready").length);

onMounted(async () => {
  loading.value = true;
  try {
    const data = await getWebTestScripts();
    scripts.value = data.items;
    selectedScriptId.value = data.items[0]?.script_id ?? "";
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <section>
    <div class="page-title">
      <div>
        <h2>Web 自动化测试</h2>
        <p>参考 FullScopeTest 的 Web 测试模块，但这里强调 Playwright 脚本、pytest 映射和 AI 失败自愈。</p>
      </div>
      <button class="primary-button" :disabled="!selectedScript">生成脚本草稿</button>
    </div>

    <div v-if="error" class="error-banner">Web 测试模块加载失败：{{ error }}</div>

    <div class="metrics-grid">
      <div class="metric-card">
        <span>Web 脚本</span>
        <strong>{{ scripts.length }}</strong>
      </div>
      <div class="metric-card">
        <span>可执行</span>
        <strong>{{ readyCount }}</strong>
      </div>
      <div class="metric-card">
        <span>框架</span>
        <strong>Playwright</strong>
      </div>
      <div class="metric-card">
        <span>AI 能力</span>
        <strong>自愈</strong>
      </div>
    </div>

    <div class="split-layout">
      <aside class="panel">
        <h3>脚本目录</h3>
        <div v-if="loading" class="empty-state">加载中...</div>
        <div v-else class="stack">
          <button
            v-for="script in scripts"
            :key="script.script_id"
            class="template-button"
            :class="{ active: script.script_id === selectedScript?.script_id }"
            type="button"
            @click="selectedScriptId = script.script_id"
          >
            <strong>{{ script.name }}</strong>
            <span>{{ script.module }} / {{ script.priority }} / {{ script.status }}</span>
          </button>
        </div>
      </aside>

      <main class="panel">
        <template v-if="selectedScript">
          <div class="item-title">
            <div>
              <h3>{{ selectedScript.name }}</h3>
              <p class="path-text">{{ selectedScript.target_url }}</p>
            </div>
            <span class="status-pill ok">{{ selectedScript.framework }}</span>
          </div>

          <h3>测试步骤</h3>
          <ol class="number-list">
            <li v-for="step in selectedScript.steps" :key="step">{{ step }}</li>
          </ol>

          <h3>断言点</h3>
          <div>
            <span v-for="assertion in selectedScript.assertions" :key="assertion" class="tag">
              {{ assertion }}
            </span>
          </div>

          <h3>pytest 映射</h3>
          <pre class="code-block">{{ selectedScript.pytest_target }}</pre>
        </template>
      </main>

      <aside class="panel">
        <h3>AI + RAG 增强</h3>
        <template v-if="selectedScript">
          <p>{{ selectedScript.ai_capability }}</p>
          <h3>知识来源</h3>
          <span v-for="source in selectedScript.rag_sources" :key="source" class="tag">{{ source }}</span>
          <h3>面试说法</h3>
          <p class="muted">
            Web 自动化不是简单录制脚本，而是把脚本、用例、报告和失败原因串起来，失败后可以进入 AI 分析。
          </p>
        </template>
      </aside>
    </div>
  </section>
</template>
