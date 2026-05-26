<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getTestingDocuments } from "../services/api";
import type { TestingDocument } from "../types";

const documents = ref<TestingDocument[]>([]);
const error = ref("");

onMounted(async () => {
  try {
    const data = await getTestingDocuments();
    documents.value = data.items;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
});
</script>

<template>
  <section>
    <div class="page-title">
      <div>
        <h2>测试文档</h2>
        <p>把 README、面试讲解稿、MCP Tools 文档和测试规范作为 RAG 知识来源管理。</p>
      </div>
      <button class="primary-button">同步到知识库</button>
    </div>

    <div v-if="error" class="error-banner">测试文档模块加载失败：{{ error }}</div>

    <div class="panel">
      <table class="data-table">
        <thead>
          <tr>
            <th>文档</th>
            <th>分类</th>
            <th>路径</th>
            <th>用途</th>
            <th>RAG</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="document in documents" :key="document.doc_id">
            <td><strong>{{ document.title }}</strong></td>
            <td>{{ document.category }}</td>
            <td class="path-text">{{ document.path }}</td>
            <td>{{ document.purpose }}</td>
            <td>
              <span class="status-pill" :class="document.rag_ready ? 'ok' : 'warn'">
                {{ document.rag_ready ? "可入库" : "待处理" }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
