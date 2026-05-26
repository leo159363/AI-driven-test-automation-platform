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
  createTestCase,
  deleteTestCase,
  getApiCollections,
  getTestCases,
  updateTestCase,
} from "../services/api";
import type { ApiCollection, TestCaseCatalogResponse, TestCaseItem } from "../types";

interface TestCaseForm {
  case_id: string;
  title: string;
  test_type: string;
  module: string;
  priority: string;
  method: string;
  path: string;
  collection_id: string;
  description: string;
  scenario_id: string;
  scenario_name: string;
  automation_status: string;
  pytest_target: string;
  assertion: string;
  related_report: string;
}

const data = ref<TestCaseCatalogResponse | null>(null);
const collections = ref<ApiCollection[]>([]);
const filterType = ref("全部");
const searchKeyword = ref("");
const loading = ref(false);
const saving = ref(false);
const modalOpen = ref(false);
const modalMode = ref<"create" | "edit">("create");
const error = ref("");

const form = reactive<TestCaseForm>({
  case_id: "",
  title: "",
  test_type: "接口测试",
  module: "登录鉴权",
  priority: "P1",
  method: "POST",
  path: "/api/login",
  collection_id: "auth",
  description: "",
  scenario_id: "api_login",
  scenario_name: "API: 登录接口",
  automation_status: "草稿",
  pytest_target: "",
  assertion: "",
  related_report: "",
});

const methodOptions = ["GET", "POST", "PUT", "PATCH", "DELETE"];
const priorityOptions = ["P0", "P1", "P2", "P3"];
const defaultCollectionOptions = [
  { label: "登录鉴权", value: "auth" },
  { label: "用户中心", value: "user" },
  { label: "文件上传", value: "upload" },
  { label: "订单流程", value: "order" },
  { label: "支付回调", value: "payment" },
  { label: "系统公共接口", value: "system" },
];

const filteredCases = computed<TestCaseItem[]>(() => {
  const items = (data.value?.items ?? []).filter((item) => item.test_type === "接口测试");
  const keyword = searchKeyword.value.trim().toLowerCase();
  return items.filter((item) => {
    const typeMatched = filterType.value === "全部" || item.module === filterType.value;
    const keywordMatched =
      !keyword ||
      `${item.case_id} ${item.title} ${item.module} ${item.path ?? ""} ${item.pytest_target}`
        .toLowerCase()
        .includes(keyword);
    return typeMatched && keywordMatched;
  });
});

const summary = computed(() => {
  const items = (data.value?.items ?? []).filter((item) => item.test_type === "接口测试");
  return {
    total: items.length,
    auth: items.filter((item) => item.module === "登录鉴权").length,
    upload: items.filter((item) => item.module === "文件上传").length,
    custom: items.filter((item) => !item.is_builtin).length,
  };
});

const collectionOptions = computed(() => {
  if (collections.value.length) {
    return collections.value.map((item) => ({
      label: item.name,
      value: item.collection_id,
    }));
  }
  return defaultCollectionOptions;
});

const moduleFilterOptions = computed(() => {
  if (collections.value.length) {
    return ["全部", ...collections.value.map((item) => item.name)];
  }
  return ["全部", ...defaultCollectionOptions.map((item) => item.label)];
});

function resetForm(): void {
  form.case_id = "";
  form.title = "";
  form.test_type = "接口测试";
  form.module = "登录鉴权";
  form.priority = "P1";
  form.method = "POST";
  form.path = "/api/login";
  form.collection_id = "auth";
  form.description = "";
  form.scenario_id = "api_login";
  form.scenario_name = "API: 登录接口";
  form.automation_status = "草稿";
  form.pytest_target = "";
  form.assertion = "";
  form.related_report = "";
}

function openCreateModal(): void {
  resetForm();
  modalMode.value = "create";
  modalOpen.value = true;
}

function openEditModal(testCase: TestCaseItem): void {
  form.case_id = testCase.case_id;
  form.title = testCase.title;
  form.test_type = testCase.test_type;
  form.module = testCase.module;
  form.priority = testCase.priority;
  form.method = testCase.method || "POST";
  form.path = testCase.path || "/api/login";
  form.collection_id = testCase.collection_id || "auth";
  form.description = testCase.description || "";
  form.scenario_id = testCase.scenario_id;
  form.scenario_name = testCase.scenario_name;
  form.automation_status = testCase.automation_status;
  form.pytest_target = testCase.pytest_target;
  form.assertion = testCase.assertion;
  form.related_report = testCase.related_report;
  modalMode.value = "edit";
  modalOpen.value = true;
}

function syncCollectionDefaults(collectionId: string): void {
  form.collection_id = collectionId;
  if (collectionId === "upload") {
    form.module = "文件上传";
    form.path = "/api/upload";
    form.scenario_id = "api_file_upload";
    form.scenario_name = "API: 文件上传接口";
    return;
  }
  if (collectionId === "user") {
    form.module = "用户中心";
    form.path = "/api/users";
    form.scenario_id = "api_user";
    form.scenario_name = "API: 用户中心接口";
    return;
  }
  if (collectionId === "order") {
    form.module = "订单流程";
    form.path = "/api/orders";
    form.scenario_id = "api_order";
    form.scenario_name = "API: 订单流程接口";
    return;
  }
  if (collectionId === "payment") {
    form.module = "支付回调";
    form.path = "/api/payments/callback";
    form.scenario_id = "api_payment";
    form.scenario_name = "API: 支付回调接口";
    return;
  }
  if (collectionId === "system") {
    form.module = "系统公共接口";
    form.path = "/api/health";
    form.scenario_id = "api_system";
    form.scenario_name = "API: 系统公共接口";
    return;
  }
  form.module = "登录鉴权";
  form.path = "/api/login";
  form.scenario_id = "api_login";
  form.scenario_name = "API: 登录接口";
}

function handleCollectionChange(value: string | number): void {
  syncCollectionDefaults(String(value));
}

function buildPayload() {
  return {
    title: form.title.trim(),
    test_type: "接口测试",
    module: form.module.trim(),
    priority: form.priority,
    method: form.method,
    path: form.path.trim(),
    collection_id: form.collection_id,
    description: form.description.trim(),
    scenario_id: form.scenario_id.trim(),
    scenario_name: form.scenario_name.trim(),
    automation_status: form.automation_status.trim(),
    pytest_target: form.pytest_target.trim(),
    assertion: form.assertion.trim(),
    related_report: form.related_report.trim(),
  };
}

async function loadData(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    const [caseData, collectionData] = await Promise.all([getTestCases(), getApiCollections()]);
    data.value = caseData;
    collections.value = collectionData.items;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

async function submitTestCase(): Promise<void> {
  saving.value = true;
  error.value = "";
  try {
    const payload = buildPayload();
    if (!payload.title) {
      throw new Error("用例名称不能为空");
    }
    if (!payload.path.startsWith("/")) {
      throw new Error("请求路径必须以 / 开头");
    }
    if (modalMode.value === "edit") {
      await updateTestCase(form.case_id, payload);
      antMessage.success("用例已更新");
    } else {
      await createTestCase(payload);
      antMessage.success("用例已创建");
    }
    modalOpen.value = false;
    await loadData();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    saving.value = false;
  }
}

function confirmDelete(testCase: TestCaseItem): void {
  Modal.confirm({
    title: `删除用例：${testCase.title}`,
    content: "删除后该用例草稿会从列表中移除。内置用例不能删除。",
    okText: "删除",
    okType: "danger",
    cancelText: "取消",
    async onOk() {
      await deleteTestCase(testCase.case_id);
      antMessage.success("用例已删除");
      await loadData();
    },
  });
}

onMounted(loadData);
</script>

<template>
  <section class="qp-page case-page">
    <div class="qp-page-heading">
      <div>
        <p class="qp-eyebrow">TEST CASE MANAGEMENT</p>
        <h1>用例管理</h1>
        <p>这里是接口测试下的用例管理，只创建 API 用例。Web、APP、性能测试用例应在各自模块中维护。</p>
      </div>
      <a-space>
        <a-input-search
          v-model:value="searchKeyword"
          class="env-search"
          placeholder="搜索用例..."
          allow-clear
        />
        <a-button @click="loadData">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
        <a-button type="primary" @click="openCreateModal">
          <template #icon><PlusOutlined /></template>
          新建用例
        </a-button>
      </a-space>
    </div>

    <a-alert
      v-if="error"
      class="section-gap"
      type="error"
      show-icon
      message="用例管理错误"
      :description="error"
    />

    <a-row :gutter="[16, 16]" class="section-gap">
      <a-col :xs="24" :md="6">
        <a-card class="stat-card">
          <span>总用例</span>
          <strong>{{ summary.total }}</strong>
        </a-card>
      </a-col>
      <a-col :xs="24" :md="6">
        <a-card class="stat-card">
          <span>登录鉴权</span>
          <strong>{{ summary.auth }}</strong>
        </a-card>
      </a-col>
      <a-col :xs="24" :md="6">
        <a-card class="stat-card">
          <span>文件上传</span>
          <strong>{{ summary.upload }}</strong>
        </a-card>
      </a-col>
      <a-col :xs="24" :md="6">
        <a-card class="stat-card">
          <span>自定义用例</span>
          <strong>{{ summary.custom }}</strong>
        </a-card>
      </a-col>
    </a-row>

    <a-card class="section-gap env-table-card" :bordered="false">
      <template #title>
        <a-space>
          <a-button
            v-for="type in moduleFilterOptions"
            :key="type"
            :type="filterType === type ? 'primary' : 'default'"
            @click="filterType = type"
          >
            {{ type }}
          </a-button>
        </a-space>
      </template>

      <a-spin :spinning="loading">
        <table class="env-table">
          <thead>
            <tr>
              <th>用例名称</th>
              <th>方法 / 路径</th>
              <th>所属集合</th>
              <th>优先级</th>
              <th>自动化</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="testCase in filteredCases" :key="testCase.case_id">
              <td>
                <strong>{{ testCase.title }}</strong>
                <div class="muted">{{ testCase.case_id }} · {{ testCase.module }}</div>
                <a-tag v-if="testCase.is_builtin" color="blue">内置</a-tag>
                <a-tag v-else color="green">自定义</a-tag>
              </td>
              <td>
                <a-tag v-if="testCase.method" color="blue">{{ testCase.method }}</a-tag>
                <span class="path-text">{{ testCase.path || "-" }}</span>
              </td>
              <td>{{ testCase.collection_id || testCase.module }}</td>
              <td><a-tag>{{ testCase.priority }}</a-tag></td>
              <td>
                <div>{{ testCase.automation_status }}</div>
                <div class="path-text">{{ testCase.pytest_target || "暂未绑定 pytest" }}</div>
              </td>
              <td>{{ testCase.updated_at ?? "-" }}</td>
              <td>
                <a-space>
                  <a-button
                    size="small"
                    :disabled="testCase.is_builtin"
                    @click="openEditModal(testCase)"
                  >
                    <template #icon><EditOutlined /></template>
                    编辑
                  </a-button>
                  <a-button
                    size="small"
                    danger
                    :disabled="testCase.is_builtin"
                    @click="confirmDelete(testCase)"
                  >
                    <template #icon><DeleteOutlined /></template>
                    删除
                  </a-button>
                </a-space>
              </td>
            </tr>
          </tbody>
        </table>
        <a-empty v-if="!filteredCases.length" description="暂无匹配用例" />
      </a-spin>
    </a-card>

    <a-modal
      v-model:open="modalOpen"
      :title="modalMode === 'create' ? '新建用例' : '编辑用例'"
      :confirm-loading="saving"
      width="640px"
      ok-text="确定"
      cancel-text="取消"
      @ok="submitTestCase"
    >
      <a-form layout="vertical" class="env-form">
        <a-form-item label="用例名称" required>
          <a-input v-model:value="form.title" placeholder="请输入用例名称" />
        </a-form-item>
        <a-form-item label="所属集合">
          <a-select
            v-model:value="form.collection_id"
            :options="collectionOptions"
            placeholder="请选择所属集合"
            @change="handleCollectionChange"
          />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="请求方法">
              <a-select v-model:value="form.method">
                <a-select-option v-for="method in methodOptions" :key="method" :value="method">
                  {{ method }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="优先级">
              <a-select v-model:value="form.priority">
                <a-select-option v-for="priority in priorityOptions" :key="priority" :value="priority">
                  {{ priority }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="请求路径">
          <a-input v-model:value="form.path" placeholder="请输入请求路径，例如 /api/login" />
        </a-form-item>
        <a-form-item label="测试类型">
          <a-input value="接口测试" disabled />
        </a-form-item>
        <a-form-item label="业务模块">
          <a-input v-model:value="form.module" disabled />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="form.description" placeholder="请输入用例描述" :rows="3" />
        </a-form-item>
        <a-form-item label="断言">
          <a-textarea v-model:value="form.assertion" placeholder="例如：状态码为 200，响应体包含 token" :rows="3" />
        </a-form-item>
        <a-form-item label="pytest 目标">
          <a-input
            v-model:value="form.pytest_target"
            placeholder="例如 tests/automation/test_api_login.py::test_api_login_success"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </section>
</template>
