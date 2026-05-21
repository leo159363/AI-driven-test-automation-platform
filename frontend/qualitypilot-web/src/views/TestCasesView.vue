<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { getTestCases } from "../services/api";
import type { TestCaseCatalogResponse, TestCaseItem } from "../types";

const data = ref<TestCaseCatalogResponse | null>(null);
const filterType = ref("全部");
const error = ref("");

const filteredCases = computed<TestCaseItem[]>(() => {
  const items = data.value?.items ?? [];
  if (filterType.value === "全部") {
    return items;
  }
  return items.filter((item) => item.test_type === filterType.value);
});

onMounted(async () => {
  try {
    data.value = await getTestCases();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
});
</script>

<template>
  <section>
    <div class="page-title">
      <div>
        <h2>测试用例</h2>
        <p>展示接口测试和界面测试用例，并保留 pytest 目标，方便面试讲自动化落地。</p>
      </div>
      <div class="toolbar">
        <button class="ghost-button" @click="filterType = '全部'">全部</button>
        <button class="ghost-button" @click="filterType = '接口测试'">接口测试</button>
        <button class="ghost-button" @click="filterType = '界面测试'">界面测试</button>
      </div>
    </div>

    <div v-if="error" class="error-banner">用例加载失败：{{ error }}</div>

    <div class="metrics-grid">
      <div class="metric-card">
        <span>总用例</span>
        <strong>{{ data?.summary.total ?? "--" }}</strong>
      </div>
      <div class="metric-card">
        <span>接口测试</span>
        <strong>{{ data?.summary.api ?? "--" }}</strong>
      </div>
      <div class="metric-card">
        <span>界面测试</span>
        <strong>{{ data?.summary.ui ?? "--" }}</strong>
      </div>
      <div class="metric-card">
        <span>已自动化</span>
        <strong>{{ data?.summary.automated ?? "--" }}</strong>
      </div>
    </div>

    <div class="panel">
      <table class="data-table">
        <thead>
          <tr>
            <th>用例 ID</th>
            <th>标题</th>
            <th>类型</th>
            <th>模块</th>
            <th>优先级</th>
            <th>pytest 目标</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="testCase in filteredCases" :key="testCase.case_id">
            <td class="path-text">{{ testCase.case_id }}</td>
            <td>{{ testCase.title }}</td>
            <td>{{ testCase.test_type }}</td>
            <td>{{ testCase.module }}</td>
            <td><span class="tag">{{ testCase.priority }}</span></td>
            <td class="path-text">{{ testCase.pytest_target }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

