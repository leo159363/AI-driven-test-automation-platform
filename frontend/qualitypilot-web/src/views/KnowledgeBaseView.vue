<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  getKnowledgeSources,
  getKnowledgeSourceTypes,
  searchKnowledge,
  uploadKnowledgeDocument,
} from "../services/api";
import type { KnowledgeContext, KnowledgeSource } from "../types";

const sourceTypes = ref<string[]>([]);
const selectedSourceTypes = ref<string[]>(["requirement", "api_doc", "bug", "standard"]);
const sources = ref<KnowledgeSource[]>([]);
const contexts = ref<KnowledgeContext[]>([]);

const project = ref("QualityPilot");
const moduleName = ref("");
const version = ref("demo");
const query = ref("登录接口 token 401 错误处理和用例设计");
const topK = ref(5);

const uploadFile = ref<File | null>(null);
const uploadTitle = ref("");
const uploadModule = ref("登录鉴权");
const uploadSourceType = ref("requirement");

const loadingSources = ref(false);
const searching = ref(false);
const uploading = ref(false);
const error = ref("");
const successMessage = ref("");

const builtinSources = computed(() => sources.value.filter((source) => source.origin === "builtin"));
const uploadedSources = computed(() => sources.value.filter((source) => source.origin === "uploaded"));

function setAllSourceTypes(): void {
  selectedSourceTypes.value = [...sourceTypes.value];
}

function clearSourceTypes(): void {
  selectedSourceTypes.value = [];
}

function handleFileChange(event: Event): void {
  const input = event.target as HTMLInputElement;
  uploadFile.value = input.files?.[0] ?? null;
  if (uploadFile.value && !uploadTitle.value) {
    uploadTitle.value = uploadFile.value.name.replace(/\.[^.]+$/, "");
  }
}

async function loadSourceTypes(): Promise<void> {
  const data = await getKnowledgeSourceTypes();
  sourceTypes.value = data.items;
  if (!selectedSourceTypes.value.length) {
    selectedSourceTypes.value = data.items;
  }
}

async function loadSources(): Promise<void> {
  loadingSources.value = true;
  error.value = "";
  try {
    const data = await getKnowledgeSources({
      project: project.value,
      module: moduleName.value,
      version: version.value,
      source_types: selectedSourceTypes.value,
    });
    sources.value = data.items;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loadingSources.value = false;
  }
}

async function submitSearch(): Promise<void> {
  searching.value = true;
  error.value = "";
  successMessage.value = "";
  try {
    const data = await searchKnowledge({
      query: query.value,
      project: project.value,
      module: moduleName.value,
      version: version.value,
      source_types: selectedSourceTypes.value,
      top_k: topK.value,
    });
    contexts.value = data.contexts;
    successMessage.value = `已召回 ${data.contexts.length} 个知识片段`;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    searching.value = false;
  }
}

async function submitUpload(): Promise<void> {
  if (!uploadFile.value) {
    error.value = "请先选择一个 txt 或 markdown 文档";
    return;
  }
  uploading.value = true;
  error.value = "";
  successMessage.value = "";
  try {
    const data = await uploadKnowledgeDocument({
      file: uploadFile.value,
      project: project.value,
      module: uploadModule.value,
      version: version.value,
      source_type: uploadSourceType.value,
      title: uploadTitle.value,
    });
    successMessage.value = `已入库：${data.source.title}，切分 ${data.source.chunk_count} 个片段`;
    await loadSources();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    uploading.value = false;
  }
}

onMounted(async () => {
  try {
    await loadSourceTypes();
    await loadSources();
    await submitSearch();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
});
</script>

<template>
  <section>
    <div class="page-title">
      <div>
        <h2>知识库管理</h2>
        <p>把需求、接口文档、历史 Bug、测试报告和规范沉淀为 RAG 上下文，给用例生成和失败分析提供依据。</p>
      </div>
      <button class="primary-button" :disabled="loadingSources" @click="loadSources">
        {{ loadingSources ? "刷新中..." : "刷新知识库" }}
      </button>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="successMessage" class="success-banner">{{ successMessage }}</div>

    <div class="knowledge-layout">
      <aside class="panel">
        <h3>知识库过滤</h3>
        <div class="stack">
          <label>
            项目
            <input v-model="project" class="form-control" />
          </label>
          <label>
            模块
            <input v-model="moduleName" class="form-control" placeholder="留空表示全部模块" />
          </label>
          <label>
            版本
            <input v-model="version" class="form-control" />
          </label>
        </div>

        <div class="toolbar filter-actions">
          <button class="ghost-button" @click="setAllSourceTypes">全选</button>
          <button class="ghost-button" @click="clearSourceTypes">清空</button>
        </div>

        <div class="source-type-grid">
          <label v-for="type in sourceTypes" :key="type" class="checkbox-chip">
            <input v-model="selectedSourceTypes" :value="type" type="checkbox" />
            {{ type }}
          </label>
        </div>

        <button class="primary-button full-width" @click="loadSources">应用过滤</button>
      </aside>

      <div class="panel">
        <h3>文档上传 / 入库</h3>
        <div class="upload-grid">
          <label>
            文档
            <input class="form-control file-input" type="file" accept=".txt,.md,.markdown" @change="handleFileChange" />
          </label>
          <label>
            标题
            <input v-model="uploadTitle" class="form-control" placeholder="默认使用文件名" />
          </label>
          <label>
            文档类型
            <select v-model="uploadSourceType" class="form-control">
              <option v-for="type in sourceTypes" :key="type" :value="type">{{ type }}</option>
            </select>
          </label>
          <label>
            业务模块
            <input v-model="uploadModule" class="form-control" />
          </label>
        </div>
        <button class="primary-button" :disabled="uploading" @click="submitUpload">
          {{ uploading ? "入库中..." : "上传并切分入库" }}
        </button>
        <p class="muted">
          当前先支持 txt / markdown 文本，上传后保存到本地 data/qualitypilot_knowledge，后续可以替换为真实向量库。
        </p>
      </div>

      <div class="panel">
        <h3>RAG 检索测试</h3>
        <textarea v-model="query" class="assistant-textarea compact-textarea" rows="5" />
        <div class="assistant-options">
          <label>
            召回数量
            <input v-model.number="topK" class="small-input" min="1" max="20" type="number" />
          </label>
          <button class="primary-button" :disabled="searching" @click="submitSearch">
            {{ searching ? "检索中..." : "检索知识片段" }}
          </button>
        </div>
      </div>
    </div>

    <div class="two-column knowledge-section">
      <div class="panel">
        <div class="item-title">
          <h3>知识来源</h3>
          <span class="tag">内置 {{ builtinSources.length }} / 上传 {{ uploadedSources.length }}</span>
        </div>
        <table class="data-table compact-table">
          <thead>
            <tr>
              <th>标题</th>
              <th>类型</th>
              <th>模块</th>
              <th>片段</th>
              <th>来源</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="source in sources" :key="source.source_id">
              <td>
                <strong>{{ source.title }}</strong>
                <div class="path-text">{{ source.source_id }}</div>
              </td>
              <td><span class="tag">{{ source.source_type }}</span></td>
              <td>{{ source.module }}</td>
              <td>{{ source.chunk_count }}</td>
              <td>{{ source.origin }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="!sources.length" class="empty-state">没有匹配当前过滤条件的知识来源。</div>
      </div>

      <div class="panel">
        <div class="item-title">
          <h3>召回片段</h3>
          <span class="tag">contexts {{ contexts.length }}</span>
        </div>
        <div v-if="contexts.length" class="stack">
          <article v-for="context in contexts" :key="context.chunk_id" class="context-card">
            <div class="item-title">
              <strong>{{ context.title }}</strong>
              <span class="tag">{{ context.source_type }} · score {{ context.score }}</span>
            </div>
            <p class="muted">
              {{ context.source_id }} · {{ context.metadata.module }} · {{ context.metadata.version }}
            </p>
            <p>{{ context.content }}</p>
            <pre class="mini-code">{{ JSON.stringify(context.metadata, null, 2) }}</pre>
          </article>
        </div>
        <div v-else class="empty-state">输入测试问题后，可以看到 RAG 召回的知识片段和引用来源。</div>
      </div>
    </div>

    <div class="panel knowledge-section">
      <h3>测试开发 RAG 数据流</h3>
      <div class="flow-list">
        <div class="flow-step">文档上传</div>
        <div class="flow-step">文本切分</div>
        <div class="flow-step">元数据标注</div>
        <div class="flow-step">知识检索</div>
        <div class="flow-step">用例生成</div>
        <div class="flow-step">失败分析</div>
      </div>
    </div>
  </section>
</template>
