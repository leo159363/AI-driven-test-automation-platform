<script setup lang="ts">
const sourceTypes = [
  "requirement",
  "api_doc",
  "test_case",
  "bug",
  "test_report",
  "log",
  "standard",
];
</script>

<template>
  <section>
    <div class="page-title">
      <div>
        <h2>知识库管理</h2>
        <p>展示 RAG 知识来源类型，Stage 6 会接入文档上传、检索测试和召回片段展示。</p>
      </div>
      <button class="primary-button" disabled>上传文档</button>
    </div>

    <div class="two-column">
      <div class="panel">
        <h3>知识来源类型</h3>
        <div>
          <span v-for="type in sourceTypes" :key="type" class="tag">{{ type }}</span>
        </div>
      </div>

      <div class="panel">
        <h3>RAG 检索链路</h3>
        <div class="flow-list">
          <div class="flow-step">文档解析</div>
          <div class="flow-step">文本切分</div>
          <div class="flow-step">Embedding</div>
          <div class="flow-step">向量检索</div>
          <div class="flow-step">Prompt 拼接</div>
          <div class="flow-step">引用返回</div>
        </div>
      </div>
    </div>
  </section>
</template>

