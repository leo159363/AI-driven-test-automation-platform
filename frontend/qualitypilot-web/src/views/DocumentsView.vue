<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { message as antMessage, Modal } from "ant-design-vue";
import {
  DeleteOutlined,
  EditOutlined,
  FileAddOutlined,
  ReloadOutlined,
  SyncOutlined,
} from "@ant-design/icons-vue";
import {
  createTestingDocument,
  deleteTestingDocument,
  getTestingDocuments,
  syncTestingDocuments,
  updateTestingDocument,
} from "../services/api";
import type { TestingDocument } from "../types";

interface DocumentForm {
  doc_id: string;
  title: string;
  category: string;
  template: string;
  path: string;
  purpose: string;
  rag_ready: boolean;
}

const documents = ref<TestingDocument[]>([]);
const selectedDocumentId = ref("");
const searchKeyword = ref("");
const loading = ref(false);
const saving = ref(false);
const syncing = ref(false);
const modalOpen = ref(false);
const modalMode = ref<"create" | "edit">("create");
const error = ref("");

const categoryOptions = ["测试计划", "测试用例", "测试报告", "接口文档", "设计文档", "其他"];
const templateOptions = ["不使用模板", "测试计划模板", "测试用例模板", "接口文档模板"];

const form = reactive<DocumentForm>({
  doc_id: "",
  title: "",
  category: "测试用例",
  template: "不使用模板",
  path: "",
  purpose: "",
  rag_ready: true,
});

const selectedDocument = computed(
  () => documents.value.find((item) => item.doc_id === selectedDocumentId.value) ?? documents.value[0],
);

const filteredDocuments = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();
  if (!keyword) return documents.value;
  return documents.value.filter((document) =>
    `${document.title} ${document.category} ${document.path} ${document.purpose}`
      .toLowerCase()
      .includes(keyword),
  );
});

const summary = computed(() => ({
  total: documents.value.length,
  ragReady: documents.value.filter((item) => item.rag_ready).length,
  custom: documents.value.filter((item) => !item.is_builtin).length,
}));

function resetForm(): void {
  form.doc_id = "";
  form.title = "";
  form.category = "测试用例";
  form.template = "不使用模板";
  form.path = "";
  form.purpose = "";
  form.rag_ready = true;
}

function applyTemplate(template: string): void {
  form.template = template;
  if (template === "测试计划模板") {
    form.category = "测试计划";
    form.purpose = "记录测试范围、测试策略、风险点、准入准出标准和执行安排。";
    return;
  }
  if (template === "测试用例模板") {
    form.category = "测试用例";
    form.purpose = "记录前置条件、测试步骤、测试数据、预期结果和自动化映射。";
    return;
  }
  if (template === "接口文档模板") {
    form.category = "接口文档";
    form.purpose = "记录接口路径、请求参数、响应结构、错误码和断言规则。";
  }
}

function openCreateModal(): void {
  resetForm();
  modalMode.value = "create";
  modalOpen.value = true;
}

function openEditModal(document: TestingDocument): void {
  form.doc_id = document.doc_id;
  form.title = document.title;
  form.category = document.category;
  form.template = document.template || "不使用模板";
  form.path = document.path;
  form.purpose = document.purpose;
  form.rag_ready = document.rag_ready;
  modalMode.value = "edit";
  modalOpen.value = true;
}

function buildPayload() {
  return {
    title: form.title.trim(),
    category: form.category,
    template: form.template === "不使用模板" ? "" : form.template,
    path: form.path.trim(),
    purpose: form.purpose.trim(),
    rag_ready: form.rag_ready,
  };
}

async function loadDocuments(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    const data = await getTestingDocuments();
    documents.value = data.items;
    selectedDocumentId.value = data.items[0]?.doc_id ?? "";
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

async function submitDocument(): Promise<void> {
  saving.value = true;
  error.value = "";
  try {
    const payload = buildPayload();
    if (!payload.title) {
      throw new Error("文档名称不能为空");
    }
    if (modalMode.value === "edit") {
      await updateTestingDocument(form.doc_id, payload);
      antMessage.success("测试文档已更新");
    } else {
      const result = await createTestingDocument(payload);
      selectedDocumentId.value = result.document.doc_id;
      antMessage.success("测试文档已创建");
    }
    modalOpen.value = false;
    await loadDocuments();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    saving.value = false;
  }
}

async function submitSyncDocuments(): Promise<void> {
  syncing.value = true;
  error.value = "";
  try {
    const result = await syncTestingDocuments();
    antMessage.success(`已提交同步：${result.summary.synced} 个文档可入库`);
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    syncing.value = false;
  }
}

function confirmDelete(document: TestingDocument): void {
  Modal.confirm({
    title: `删除文档：${document.title}`,
    content: "删除后该文档记录会从测试文档列表移除。这里删除的是平台记录，不会删除你磁盘上的真实文件。",
    okText: "删除",
    okType: "danger",
    cancelText: "取消",
    async onOk() {
      await deleteTestingDocument(document.doc_id);
      antMessage.success("测试文档已删除");
      await loadDocuments();
    },
  });
}

onMounted(loadDocuments);
</script>

<template>
  <section class="qp-page document-page">
    <div class="qp-page-heading">
      <div>
        <p class="qp-eyebrow">TESTING DOCUMENTS</p>
        <h1>测试文档</h1>
        <p>管理测试计划、测试用例、测试报告、接口文档和设计文档，并作为 RAG 知识来源。</p>
      </div>
      <a-space>
        <a-button :loading="syncing" @click="submitSyncDocuments">
          <template #icon><SyncOutlined /></template>
          同步到知识库
        </a-button>
        <a-button type="primary" @click="openCreateModal">
          <template #icon><FileAddOutlined /></template>
          新建文档
        </a-button>
      </a-space>
    </div>

    <a-alert
      v-if="error"
      class="section-gap"
      type="error"
      show-icon
      message="测试文档模块错误"
      :description="error"
    />

    <a-row :gutter="[16, 16]" class="section-gap">
      <a-col :xs="24" :md="8">
        <a-card class="stat-card">
          <span>文档总数</span>
          <strong>{{ summary.total }}</strong>
        </a-card>
      </a-col>
      <a-col :xs="24" :md="8">
        <a-card class="stat-card">
          <span>可入库</span>
          <strong>{{ summary.ragReady }}</strong>
        </a-card>
      </a-col>
      <a-col :xs="24" :md="8">
        <a-card class="stat-card">
          <span>自定义文档</span>
          <strong>{{ summary.custom }}</strong>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="[16, 16]" class="section-gap">
      <a-col :xs="24" :lg="8">
        <a-card :bordered="false" class="env-table-card">
          <template #title>
            <a-space>
              <a-input-search
                v-model:value="searchKeyword"
                class="env-search"
                placeholder="搜索文档..."
                allow-clear
              />
              <a-button @click="loadDocuments">
                <template #icon><ReloadOutlined /></template>
              </a-button>
              <a-button @click="openCreateModal">
                <template #icon><FileAddOutlined /></template>
              </a-button>
            </a-space>
          </template>
          <a-spin :spinning="loading">
            <div class="doc-list">
              <button
                v-for="document in filteredDocuments"
                :key="document.doc_id"
                class="doc-list-item"
                :class="{ active: document.doc_id === selectedDocument?.doc_id }"
                type="button"
                @click="selectedDocumentId = document.doc_id"
              >
                <strong>{{ document.title }}</strong>
                <span>{{ document.category }} / {{ document.path }}</span>
              </button>
            </div>
            <a-empty v-if="!filteredDocuments.length" description="暂无匹配文档" />
          </a-spin>
        </a-card>
      </a-col>

      <a-col :xs="24" :lg="16">
        <a-card :bordered="false" class="env-table-card">
          <template v-if="selectedDocument">
            <div class="item-title">
              <h3>{{ selectedDocument.title }}</h3>
              <a-space>
                <a-tag :color="selectedDocument.rag_ready ? 'green' : 'orange'">
                  {{ selectedDocument.rag_ready ? "可入库" : "待处理" }}
                </a-tag>
                <a-tag v-if="selectedDocument.is_builtin" color="blue">内置</a-tag>
                <a-tag v-else color="green">自定义</a-tag>
              </a-space>
            </div>
            <a-descriptions bordered size="small" :column="1" class="section-gap-sm">
              <a-descriptions-item label="分类">{{ selectedDocument.category }}</a-descriptions-item>
              <a-descriptions-item label="模板">
                {{ selectedDocument.template || "未使用模板" }}
              </a-descriptions-item>
              <a-descriptions-item label="路径">
                <span class="path-text">{{ selectedDocument.path }}</span>
              </a-descriptions-item>
              <a-descriptions-item label="用途">{{ selectedDocument.purpose }}</a-descriptions-item>
              <a-descriptions-item label="更新时间">
                {{ selectedDocument.updated_at ?? "-" }}
              </a-descriptions-item>
            </a-descriptions>
            <a-space class="section-gap-sm">
              <a-button type="primary" @click="openEditModal(selectedDocument)">
                <template #icon><EditOutlined /></template>
                编辑文档
              </a-button>
              <a-button danger @click="confirmDelete(selectedDocument)">
                <template #icon><DeleteOutlined /></template>
                删除文档
              </a-button>
            </a-space>
          </template>
          <a-empty v-else description="请从左侧选择文档或创建新文档">
            <a-button type="primary" @click="openCreateModal">创建新文档</a-button>
          </a-empty>
        </a-card>
      </a-col>
    </a-row>

    <a-modal
      v-model:open="modalOpen"
      :title="modalMode === 'create' ? '新建文档' : '编辑文档'"
      :confirm-loading="saving"
      width="640px"
      ok-text="确定"
      cancel-text="取消"
      @ok="submitDocument"
    >
      <a-form layout="vertical" class="env-form">
        <a-form-item label="文档名称" required>
          <a-input v-model:value="form.title" placeholder="请输入文档名称" />
        </a-form-item>
        <a-form-item label="文档分类" required>
          <a-select v-model:value="form.category" placeholder="请选择文档分类">
            <a-select-option v-for="category in categoryOptions" :key="category" :value="category">
              {{ category }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="使用模板">
          <a-select
            v-model:value="form.template"
            placeholder="选择模板（可选）"
            @change="applyTemplate"
          >
            <a-select-option v-for="template in templateOptions" :key="template" :value="template">
              {{ template }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="文档路径">
          <a-input v-model:value="form.path" placeholder="例如 docs/api_login_cases.md" />
          <div class="field-tip">不填写时会按文档名称自动生成 docs/*.md 路径。</div>
        </a-form-item>
        <a-form-item label="用途说明">
          <a-textarea v-model:value="form.purpose" placeholder="请输入文档用途" :rows="3" />
        </a-form-item>
        <a-form-item label="可同步到知识库">
          <a-switch v-model:checked="form.rag_ready" />
        </a-form-item>
      </a-form>
    </a-modal>
  </section>
</template>
