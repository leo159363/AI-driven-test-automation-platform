<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { getPromptTemplates, sendAssistantMessage } from "../services/api";
import type { AssistantResponse, PromptTemplate } from "../types";

interface SelectOption {
  value: string;
  label: string;
  description?: string;
}

interface TaskPreset {
  id: string;
  title: string;
  templateId: string;
  module: string;
  version: string;
  message: string;
  sourceTypes: string[];
  topK: number;
}

const templates = ref<PromptTemplate[]>([]);
const selectedTemplateId = ref("test_case_generation");
const selectedPresetId = ref("login-api-design");
const message = ref("");
const project = ref("QualityPilot");
const moduleName = ref("登录鉴权");
const version = ref("demo");
const useKnowledge = ref(true);
const sourceTypes = ref<string[]>(["requirement", "api_doc", "test_case", "bug", "standard"]);
const topK = ref(4);
const loading = ref(false);
const error = ref("");
const response = ref<AssistantResponse | null>(null);

const projectOptions: SelectOption[] = [
  {
    value: "QualityPilot",
    label: "QualityPilot Demo",
    description: "当前演示项目，包含登录鉴权、文件上传、知识库和自动化报告样例。",
  },
];

const moduleOptions: SelectOption[] = [
  { value: "登录鉴权", label: "登录鉴权", description: "登录成功、登录失败、Token 和权限校验。" },
  { value: "文件上传", label: "文件上传", description: "二进制上传、文件名、大小和参数校验。" },
  { value: "测试规范", label: "测试规范", description: "接口断言、错误码、安全和可观测性标准。" },
  { value: "失败分析", label: "失败分析", description: "pytest / JUnit / Allure 失败原因归类。" },
  { value: "缺陷管理", label: "缺陷管理", description: "把失败证据整理成 Bug 报告草稿。" },
];

const versionOptions: SelectOption[] = [
  { value: "demo", label: "demo 演示版" },
  { value: "v1.0", label: "v1.0 面试版" },
  { value: "local", label: "local 本地调试" },
];

const sourceTypeOptions: SelectOption[] = [
  { value: "requirement", label: "需求文档" },
  { value: "api_doc", label: "接口文档" },
  { value: "test_case", label: "历史用例" },
  { value: "bug", label: "历史 Bug" },
  { value: "test_report", label: "测试报告" },
  { value: "log", label: "失败日志" },
  { value: "standard", label: "测试规范" },
];

const taskPresets: TaskPreset[] = [
  {
    id: "login-api-design",
    title: "登录接口测试设计",
    templateId: "api_test_design",
    module: "登录鉴权",
    version: "demo",
    message:
      "POST /api/login 支持 username 和 password 登录。成功返回 200、token 和 user 信息；密码错误返回 401 和 invalid_credentials；缺少字段返回 400。请生成接口测试点、请求数据、断言和边界用例。",
    sourceTypes: ["requirement", "api_doc", "test_case", "bug", "standard"],
    topK: 4,
  },
  {
    id: "upload-boundary-cases",
    title: "文件上传边界用例",
    templateId: "api_test_design",
    module: "文件上传",
    version: "demo",
    message:
      "POST /api/upload 通过二进制 body 上传文件，必须携带 X-Filename header。成功返回 201、filename 和 size；缺少文件名返回 400 missing_filename。请设计正常、异常、边界和安全类接口用例。",
    sourceTypes: ["requirement", "api_doc", "standard"],
    topK: 4,
  },
  {
    id: "pytest-failure-analysis",
    title: "自动化失败原因分析",
    templateId: "failure_analysis",
    module: "失败分析",
    version: "demo",
    message:
      "pytest 用例 test_api_login_success 失败，断言信息为 expected token but missing。JUnit 报告显示状态码是 200，但是响应体没有 token 字段。请分析可能原因、证据和修复建议。",
    sourceTypes: ["test_report", "log", "bug", "api_doc", "standard"],
    topK: 4,
  },
  {
    id: "bug-report-draft",
    title: "Bug 报告草稿",
    templateId: "bug_report",
    module: "缺陷管理",
    version: "demo",
    message:
      "登录成功接口返回 200，但响应体缺少 token 字段，导致自动化用例 TC-API-LOGIN-001 失败。请生成可提交到缺陷平台的 Bug 报告，包含标题、复现步骤、期望结果、实际结果、影响范围和附件建议。",
    sourceTypes: ["test_report", "log", "bug", "requirement", "api_doc"],
    topK: 4,
  },
  {
    id: "requirement-testability",
    title: "需求可测性审查",
    templateId: "testability_review",
    module: "测试规范",
    version: "demo",
    message:
      "用户可以上传文件，系统需要进行安全检查。请从测试开发角度判断这个需求是否可测，指出缺失的验收标准、边界条件、安全要求和需要追问产品的问题。",
    sourceTypes: ["requirement", "api_doc", "standard"],
    topK: 3,
  },
];

const topKOptions = [3, 4, 6, 8];

const selectedTemplate = computed(() =>
  templates.value.find((template) => template.template_id === selectedTemplateId.value),
);

const selectedProject = computed(() =>
  projectOptions.find((item) => item.value === project.value),
);

const selectedModule = computed(() =>
  moduleOptions.find((item) => item.value === moduleName.value),
);

function selectTemplate(template: PromptTemplate): void {
  selectedTemplateId.value = template.template_id;
  sourceTypes.value = [...template.default_source_types];
  if (!message.value.trim()) {
    message.value = template.placeholder;
  }
}

function applyPreset(preset: TaskPreset): void {
  selectedPresetId.value = preset.id;
  selectedTemplateId.value = preset.templateId;
  moduleName.value = preset.module;
  version.value = preset.version;
  message.value = preset.message;
  sourceTypes.value = [...preset.sourceTypes];
  topK.value = preset.topK;
  response.value = null;
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
    const preset = taskPresets.find((item) => item.id === selectedPresetId.value);
    if (preset) {
      applyPreset(preset);
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
        <p>不用凭空输入项目和模块。先选择测试场景，再让 RAG + MCP 生成用例、失败分析或 Bug 草稿。</p>
      </div>
      <button class="primary-button" :disabled="loading || !message.trim()" @click="submitAssistantRequest">
        {{ loading ? "生成中..." : "生成测试产物" }}
      </button>
    </div>

    <div v-if="error" class="error-banner">AI 助手请求失败：{{ error }}</div>

    <div class="panel assistant-guide-panel">
      <div class="guide-step-card">
        <span class="step-index">1</span>
        <strong>选场景</strong>
        <p>登录接口、文件上传、失败分析、Bug 报告都已经预置好。</p>
      </div>
      <div class="guide-step-card">
        <span class="step-index">2</span>
        <strong>选模块和知识来源</strong>
        <p>项目、模块、版本、召回类型都用下拉或勾选，不需要记字段名。</p>
      </div>
      <div class="guide-step-card">
        <span class="step-index">3</span>
        <strong>生成产物</strong>
        <p>输出结构化 JSON 和 Markdown，可用于用例、分析报告和面试讲解。</p>
      </div>
    </div>

    <div class="assistant-layout refined-assistant-layout">
      <aside class="panel">
        <h3>测试场景</h3>
        <div class="stack">
          <button
            v-for="preset in taskPresets"
            :key="preset.id"
            class="template-button"
            :class="{ active: preset.id === selectedPresetId }"
            type="button"
            @click="applyPreset(preset)"
          >
            <strong>{{ preset.title }}</strong>
            <span>{{ preset.module }} / {{ preset.version }}</span>
          </button>
        </div>

        <h3 class="section-subtitle">提示词模板</h3>
        <div class="stack">
          <button
            v-for="template in templates"
            :key="template.template_id"
            class="template-button compact-template"
            :class="{ active: template.template_id === selectedTemplateId }"
            type="button"
            @click="selectTemplate(template)"
          >
            <strong>{{ template.name }}</strong>
            <span>{{ template.description }}</span>
          </button>
        </div>
      </aside>

      <div class="panel">
        <h3>对话配置</h3>
        <div class="assistant-form-grid">
          <label>
            项目
            <select v-model="project" class="form-control">
              <option v-for="item in projectOptions" :key="item.value" :value="item.value">
                {{ item.label }}
              </option>
            </select>
          </label>
          <label>
            模块
            <select v-model="moduleName" class="form-control">
              <option v-for="item in moduleOptions" :key="item.value" :value="item.value">
                {{ item.label }}
              </option>
            </select>
          </label>
          <label>
            版本
            <select v-model="version" class="form-control">
              <option v-for="item in versionOptions" :key="item.value" :value="item.value">
                {{ item.label }}
              </option>
            </select>
          </label>
        </div>

        <div class="selection-summary">
          <strong>{{ selectedProject?.label }}</strong>
          <span>{{ selectedModule?.description }}</span>
        </div>

        <label>
          当前任务描述
          <textarea
            v-model="message"
            class="assistant-textarea"
            rows="9"
            :placeholder="selectedTemplate?.placeholder"
          />
        </label>

        <div class="assistant-options">
          <label class="toggle-row">
            <input v-model="useKnowledge" type="checkbox" />
            启用知识库上下文
          </label>
          <label>
            召回数量
            <select v-model.number="topK" class="small-input">
              <option v-for="count in topKOptions" :key="count" :value="count">{{ count }}</option>
            </select>
          </label>
        </div>

        <h3 class="section-subtitle">知识来源</h3>
        <div class="source-type-grid">
          <label v-for="type in sourceTypeOptions" :key="type.value" class="checkbox-chip">
            <input v-model="sourceTypes" :value="type.value" type="checkbox" />
            {{ type.label }}
          </label>
        </div>

        <h3 class="section-subtitle">推荐 MCP Tools</h3>
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
            <p class="muted">{{ context.source_id }} / score {{ context.score }}</p>
            <p>{{ context.content }}</p>
          </article>
        </div>
        <div v-else class="empty-state">
          点击生成后，这里会展示 RAG 召回的文档片段，面试时可以说明 AI 不是凭空生成。
        </div>
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
        <div v-else class="empty-state">选择左侧场景并点击生成，结构化结果会显示在这里。</div>
      </div>

      <div class="panel">
        <h3>Markdown 草稿</h3>
        <pre v-if="response?.markdown" class="code-block markdown-preview">{{ response.markdown }}</pre>
        <div v-else class="empty-state">这里会生成便于复制到测试文档、缺陷平台或面试讲解稿的 Markdown。</div>
      </div>
    </div>
  </section>
</template>
