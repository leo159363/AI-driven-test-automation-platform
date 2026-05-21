<script setup lang="ts">
const promptTemplates = [
  "智能用例生成",
  "接口测试设计",
  "失败原因分析",
  "Bug 报告生成",
  "可测性分析",
];
</script>

<template>
  <section>
    <div class="page-title">
      <div>
        <h2>AI 测试助手</h2>
        <p>参考 WHartTest 的 LLM 对话中心，但定位为测试开发专用助手。</p>
      </div>
      <button class="primary-button" disabled>新建对话</button>
    </div>

    <div class="split-layout">
      <aside class="panel">
        <h3>会话列表</h3>
        <div class="stack">
          <button class="ghost-button">登录接口测试设计</button>
          <button class="ghost-button">文件上传失败分析</button>
          <button class="ghost-button">回归测试计划</button>
        </div>
      </aside>

      <div class="panel">
        <h3>对话窗口</h3>
        <div class="empty-state">
          Stage 5 会接入 RAG 检索和 MCP tools。当前先保留页面结构，方便面试展示全栈规划。
        </div>
        <textarea
          rows="6"
          placeholder="请输入需求、接口描述或失败日志..."
          style="width: 100%; margin-top: 14px; padding: 12px; border: 1px solid #d8e1ef; border-radius: 8px;"
        />
      </div>

      <aside class="panel">
        <h3>提示词模板</h3>
        <div class="stack">
          <button v-for="template in promptTemplates" :key="template" class="ghost-button">
            {{ template }}
          </button>
        </div>
      </aside>
    </div>
  </section>
</template>

