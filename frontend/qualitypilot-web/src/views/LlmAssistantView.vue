<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { getPromptTemplates, sendAssistantMessage } from "../services/api";
import type { AssistantResponse, PromptTemplate } from "../types";

const templates = ref<PromptTemplate[]>([]);
const selectedTemplateId = ref("test_case_generation");
const message = ref("登录接口支持账号密码登录，成功返回 token，错误密码返回 401，请生成接口测试用例。");
const project = ref("QualityPilot");
const moduleName = ref("登录鉴权");
const version = ref("demo");
const useKnowledge = ref(true);
const sourceTypes = ref<string[]>(["requirement", "api_doc", "test_case", "bug", "standard"]);
const topK = ref(4);
const loading = ref(false);
const error = ref("");
const response = ref<AssistantResponse | null>(null);

const sourceTypeOptions = [
  "requirement",
  "api_doc",
  "test_case",
  "bug",
  "test_report",
  "log",
  "standard",
];

const selectedTemplate = computed(
  () => templates.value.find((template) => template.template_id === selectedTemplateId.value),
);

function selectTemplate(template: PromptTemplate): void {
  selectedTemplateId.value = template.template_id;
  sourceTypes.value = [...template.default_source_types];
  message.value = template.placeholder;
}

async function submitAssistantRequest(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    response.value = await sendAssistantMessage({
      template_id: selectedTemplateId.value,
      message: message.value,
      project: project.value,
      module: moduleName.value,
      version: version.value,
      use_knowledge: useKnowledge.value,
      source_types: sourceTypes.value,
      top_k: topK.value,
    });
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  try {
    const data = await getPromptTemplates();
    templates.value = data.items;
    const first = data.items[0];
    if (first) {
      selectTemplate(first);
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
});
</script>

<template>
  <section>
    <div class="page-title">
      <div>
        <h2>AI 测试助手</h2>
        <p>面向测试开发的 LLM 对话中心：提示词模板、知识库开关、用例生成、失败分析和 Bug 草稿。</p>
      </div>
      <button class="primary-button" :disabled="loading" @click="submitAssistantRequest">
        {{ loading ? "生成中..." : "生成测试产物" }}
      </button>
    </div>

    <div v-if="error" class="error-banner">AI 助手请求失败：{{ error }}</div>

    <div class="assistant-layout">
      <aside class="panel">
        <h3>提示词模板</h3>
        <div class="stack">
          <button
            v-for="template in templates"
            :key="template.template_id"
            class="template-button"
            :class="{ active: template.template_id === selectedTemplateId }"
            @click="selectTemplate(template)"
          >
            <strong>{{ template.name }}</strong>
            <span>{{ template.description }}</span>
          </button>
        </div>
      </aside>

      <div class="panel">
        <h3>对话输入</h3>
        <div class="assistant-form-grid">
          <label>
            项目
            <input v-model="project" class="form-control" />
          </label>
          <label>
            模块
            <input v-model="moduleName" class="form-control" />
          </label>
          <label>
            版本
            <input v-model="version" class="form-control" />
          </label>
        </div>

        <textarea
          v-model="message"
          class="assistant-textarea"
          rows="8"
          :placeholder="selectedTemplate?.placeholder"
        />

        <div class="assistant-options">
          <label class="toggle-row">
            <input v-model="useKnowledge" type="checkbox" />
            启用知识库上下文
          </label>
          <label>
            召回数量
            <input v-model.number="topK" class="small-input" min="1" max="8" type="number" />
          </label>
        </div>

        <div class="source-type-grid">
          <label v-for="type in sourceTypeOptions" :key="type" class="checkbox-chip">
            <input v-model="sourceTypes" :value="type" type="checkbox" />
            {{ type }}
          </label>
        </div>

        <h3>推荐 MCP Tools</h3>
        <div>
          <span v-for="tool in selectedTemplate?.recommended_tools ?? []" :key="tool" class="tag">
            {{ tool }}
          </span>
        </div>
      </div>

      <aside class="panel">
        <h3>知识库上下文</h3>
        <div v-if="response?.contexts.length" class="stack">
          <article v-for="context in response.contexts" :key="context.chunk_id" class="context-card">
            <div class="item-title">
              <strong>{{ context.title }}</strong>
              <span class="tag">{{ context.source_type }}</span>
            </div>
            <p class="muted">{{ context.source_id }} · score {{ context.score }}</p>
            <p>{{ context.content }}</p>
          </article>
        </div>
        <div v-else class="empty-state">生成后这里展示 RAG 召回片段。</div>
      </aside>
    </div>

    <div class="two-column assistant-result-row">
      <div class="panel">
        <h3>生成结果</h3>
        <template v-if="response">
          <div class="toolbar">
            <span class="status-pill ok">{{ response.result_type }}</span>
            <span v-for="step in response.recommended_next_steps" :key="step" class="tag">{{ step }}</span>
          </div>
          <pre class="code-block">{{ JSON.stringify(response.result, null, 2) }}</pre>
        </template>
        <div v-else class="empty-state">选择模板并点击生成，结果会显示在这里。</div>
      </div>

      <div class="panel">
        <h3>Markdown 草稿</h3>
        <pre v-if="response?.markdown" class="code-block markdown-preview">{{ response.markdown }}</pre>
        <div v-else class="empty-state">这里会生成便于复制到文档或缺陷平台的 Markdown。</div>
      </div>
    </div>
  </section>
</template>
