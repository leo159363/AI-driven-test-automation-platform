<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getPlatformSettings } from "../services/api";
import type { PlatformSetting } from "../types";

const settings = ref<PlatformSetting[]>([]);
const error = ref("");

onMounted(async () => {
  try {
    const data = await getPlatformSettings();
    settings.value = data.items;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
});
</script>

<template>
  <section>
    <div class="page-title">
      <div>
        <h2>系统设置</h2>
        <p>展示 LLM、RAG、MCP Server、pytest 和 Allure 等平台级配置，不做复杂权限系统。</p>
      </div>
      <button class="primary-button">保存配置</button>
    </div>

    <div v-if="error" class="error-banner">系统设置模块加载失败：{{ error }}</div>

    <div class="two-column">
      <article v-for="setting in settings" :key="setting.setting_id" class="panel">
        <div class="item-title">
          <h3>{{ setting.name }}</h3>
          <span class="tag">{{ setting.setting_id }}</span>
        </div>
        <pre class="mini-code">{{ setting.value }}</pre>
        <p class="muted">{{ setting.description }}</p>
      </article>
    </div>
  </section>
</template>
