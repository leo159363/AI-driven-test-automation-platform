<script setup lang="ts">
const navItems = [
  { label: "平台总览", path: "/", icon: "grid" },
  { label: "API 测试", path: "/api-testing", icon: "api" },
  { label: "测试用例", path: "/test-cases", icon: "case" },
  { label: "自动化执行", path: "/automation", icon: "run" },
  { label: "测试报告", path: "/reports", icon: "report" },
  { label: "AI 测试助手", path: "/assistant", icon: "ai" },
  { label: "知识库管理", path: "/knowledge", icon: "kb" },
];
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">QP</div>
        <div>
          <strong>QualityPilot</strong>
          <span>AI 测试平台</span>
        </div>
      </div>

      <nav class="nav-list">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        <span>FastAPI</span>
        <strong>127.0.0.1:8000</strong>
      </div>
    </aside>

    <main class="main-panel">
      <header class="topbar">
        <div>
          <p class="eyebrow">MCP + RAG + pytest + Allure</p>
          <h1>基于 AI 驱动的自动化测试平台</h1>
        </div>
        <div class="project-switcher">
          <span>当前项目</span>
          <strong>QualityPilot Demo</strong>
        </div>
      </header>

      <RouterView />
    </main>
  </div>
</template>

