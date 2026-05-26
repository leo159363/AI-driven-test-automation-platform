<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { message as antMessage, Modal } from "ant-design-vue";
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
} from "@ant-design/icons-vue";
import {
  createApiTestingEnvironment,
  deleteApiTestingEnvironment,
  getApiTestingEnvironments,
  updateApiTestingEnvironment,
} from "../services/api";
import type { ApiEnvironment } from "../types";

interface EnvironmentForm {
  environment_id: string;
  name: string;
  base_url: string;
  description: string;
  variables_json: string;
  headers_json: string;
  is_default: boolean;
}

const environments = ref<ApiEnvironment[]>([]);
const searchKeyword = ref("");
const modalOpen = ref(false);
const modalMode = ref<"create" | "edit">("create");
const loading = ref(false);
const saving = ref(false);
const error = ref("");

const form = reactive<EnvironmentForm>({
  environment_id: "",
  name: "",
  base_url: "",
  description: "",
  variables_json: '{\n  "bearer": "your_token_here",\n  "userId": "123",\n  "apiKey": "abc456"\n}',
  headers_json: '{\n  "Content-Type": "application/json"\n}',
  is_default: false,
});

const filteredEnvironments = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();
  if (!keyword) return environments.value;
  return environments.value.filter((item) =>
    `${item.name} ${item.base_url} ${item.description} ${item.environment_id}`
      .toLowerCase()
      .includes(keyword),
  );
});

const defaultEnvironment = computed(() => environments.value.find((item) => item.is_default));

function parseJsonObject(text: string, label: string): Record<string, string> {
  const parsed = JSON.parse(text || "{}") as unknown;
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error(`${label} 必须是 JSON 对象`);
  }
  return Object.fromEntries(Object.entries(parsed).map(([key, value]) => [key, String(value)]));
}

function resetForm(): void {
  form.environment_id = "";
  form.name = "";
  form.base_url = "";
  form.description = "";
  form.variables_json = '{\n  "bearer": "your_token_here",\n  "userId": "123",\n  "apiKey": "abc456"\n}';
  form.headers_json = '{\n  "Content-Type": "application/json"\n}';
  form.is_default = false;
}

function openCreateModal(): void {
  resetForm();
  modalMode.value = "create";
  modalOpen.value = true;
}

function openEditModal(environment: ApiEnvironment): void {
  form.environment_id = environment.environment_id;
  form.name = environment.name;
  form.base_url = environment.base_url;
  form.description = environment.description;
  form.variables_json = JSON.stringify(environment.variables, null, 2);
  form.headers_json = JSON.stringify(environment.headers, null, 2);
  form.is_default = Boolean(environment.is_default);
  modalMode.value = "edit";
  modalOpen.value = true;
}

async function loadEnvironments(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    const data = await getApiTestingEnvironments();
    environments.value = data.items;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

async function submitEnvironment(): Promise<void> {
  saving.value = true;
  error.value = "";
  try {
    const payload = {
      name: form.name.trim(),
      base_url: form.base_url.trim(),
      description: form.description.trim(),
      variables: parseJsonObject(form.variables_json, "环境变量"),
      headers: parseJsonObject(form.headers_json, "公共 Headers"),
      is_default: form.is_default,
    };
    if (!payload.name) {
      throw new Error("环境名称不能为空");
    }
    if (modalMode.value === "edit") {
      await updateApiTestingEnvironment(form.environment_id, payload);
      antMessage.success("环境已更新");
    } else {
      await createApiTestingEnvironment(payload);
      antMessage.success("环境已创建");
    }
    modalOpen.value = false;
    await loadEnvironments();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    saving.value = false;
  }
}

function confirmDelete(environment: ApiEnvironment): void {
  Modal.confirm({
    title: `删除环境：${environment.name}`,
    content: "删除后 API 工作台将不能再选择这个环境。内置环境不能删除。",
    okText: "删除",
    okType: "danger",
    cancelText: "取消",
    async onOk() {
      await deleteApiTestingEnvironment(environment.environment_id);
      antMessage.success("环境已删除");
      await loadEnvironments();
    },
  });
}

onMounted(loadEnvironments);
</script>

<template>
  <section class="qp-page env-page">
    <div class="qp-page-heading">
      <div>
        <p class="qp-eyebrow">API ENVIRONMENT</p>
        <h1>环境配置</h1>
        <p>管理接口测试的 Base URL、公共 Headers、环境变量和默认环境。新建后可在 API 测试工作台直接选择。</p>
      </div>
      <a-space>
        <a-input-search
          v-model:value="searchKeyword"
          class="env-search"
          placeholder="搜索环境..."
          allow-clear
        />
        <a-button @click="loadEnvironments">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
        <a-button type="primary" @click="openCreateModal">
          <template #icon><PlusOutlined /></template>
          新建环境
        </a-button>
      </a-space>
    </div>

    <a-alert
      v-if="error"
      class="section-gap"
      type="error"
      show-icon
      message="环境配置错误"
      :description="error"
    />

    <a-alert
      class="section-gap"
      type="info"
      show-icon
      message="这个页面是给 API 测试工作台选择运行环境用的"
      description="内置 Mock 环境不请求真实服务，适合演示；本机 API 环境会请求 http://127.0.0.1:9000，适合你本地启动了被测服务时使用；自定义环境可以保存测试/预发环境的 Base URL、公共 Headers 和 token 变量。"
    />

    <a-row :gutter="[16, 16]" class="section-gap">
      <a-col :xs="24" :md="6">
        <a-card class="stat-card">
          <span>环境总数</span>
          <strong>{{ environments.length }}</strong>
        </a-card>
      </a-col>
      <a-col :xs="24" :md="6">
        <a-card class="stat-card">
          <span>自定义环境</span>
          <strong>{{ environments.filter((item) => !item.is_builtin).length }}</strong>
        </a-card>
      </a-col>
      <a-col :xs="24" :md="6">
        <a-card class="stat-card">
          <span>默认环境</span>
          <strong>{{ defaultEnvironment?.name ?? "--" }}</strong>
        </a-card>
      </a-col>
      <a-col :xs="24" :md="6">
        <a-card class="stat-card">
          <span>Mock 可用</span>
          <strong>是</strong>
        </a-card>
      </a-col>
    </a-row>

    <a-card class="section-gap env-table-card" :bordered="false">
      <a-spin :spinning="loading">
        <table class="env-table">
          <thead>
            <tr>
              <th>环境名称</th>
              <th>Base URL</th>
              <th>变量数</th>
              <th>默认</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="environment in filteredEnvironments" :key="environment.environment_id">
              <td>
                <strong>{{ environment.name }}</strong>
                <div class="muted">{{ environment.description || environment.environment_id }}</div>
                <a-tag v-if="environment.is_builtin" color="blue">内置</a-tag>
                <a-tag v-else color="green">自定义</a-tag>
              </td>
              <td>
                <span class="path-text">{{ environment.base_url || "内置 Mock / 留空" }}</span>
              </td>
              <td>{{ Object.keys(environment.variables || {}).length }}</td>
              <td>
                <a-tag :color="environment.is_default ? 'green' : 'default'">
                  {{ environment.is_default ? "默认" : "否" }}
                </a-tag>
              </td>
              <td>{{ environment.updated_at ?? "-" }}</td>
              <td>
                <a-space>
                  <a-button size="small" @click="openEditModal(environment)">
                    <template #icon><EditOutlined /></template>
                    编辑
                  </a-button>
                  <a-button
                    size="small"
                    danger
                    :disabled="environment.is_builtin"
                    @click="confirmDelete(environment)"
                  >
                    <template #icon><DeleteOutlined /></template>
                    删除
                  </a-button>
                </a-space>
              </td>
            </tr>
          </tbody>
        </table>
        <a-empty v-if="!filteredEnvironments.length" description="暂无匹配环境" />
      </a-spin>
    </a-card>

    <a-modal
      v-model:open="modalOpen"
      :title="modalMode === 'create' ? '新建环境' : '编辑环境'"
      :confirm-loading="saving"
      width="640px"
      ok-text="确定"
      cancel-text="取消"
      @ok="submitEnvironment"
    >
      <a-form layout="vertical" class="env-form">
        <a-form-item label="环境名称" required>
          <a-input v-model:value="form.name" placeholder="请输入环境名称" />
        </a-form-item>
        <a-form-item label="Base URL" required>
          <a-input v-model:value="form.base_url" placeholder="https://api.example.com" />
          <div class="field-tip">
            如果是真实接口环境，填写接口服务根地址，例如 http://127.0.0.1:9000；如果只是演示，优先使用内置 Mock 环境。
          </div>
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="form.description" placeholder="请输入环境描述" :rows="3" />
        </a-form-item>
        <a-form-item label="环境变量 JSON">
          <a-textarea v-model:value="form.variables_json" class="code-editor" :rows="7" />
          <div class="field-tip">
            这里保存 token、userId 等变量，API 测试页可以用 <code>&#123;&#123;token&#125;&#125;</code> 引用，避免每个接口重复填写。
          </div>
        </a-form-item>
        <a-form-item label="公共 Headers JSON">
          <a-textarea v-model:value="form.headers_json" class="code-editor" :rows="4" />
        </a-form-item>
        <a-form-item label="设为默认">
          <a-switch v-model:checked="form.is_default" />
        </a-form-item>
      </a-form>
    </a-modal>
  </section>
</template>
