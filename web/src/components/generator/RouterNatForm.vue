<template>
  <el-form label-width="120px" size="default">
    <el-form-item label="启用NAT">
      <el-switch v-model="form.enable_nat" active-text="开启" inactive-text="关闭" />
      <span style="font-size:12px;color:#909399;margin-left:8px">让内网设备能访问互联网</span>
    </el-form-item>

    <template v-if="form.enable_nat">
      <el-divider content-position="left">端口映射（把内网服务暴露到公网）</el-divider>

      <div v-for="(m, i) in form.mappings" :key="i" style="border:1px solid #ebeef5;border-radius:6px;padding:12px;margin-bottom:10px;background:#fafbfc">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
          <span style="font-weight:600;font-size:13px">映射 #{{ i + 1 }}</span>
          <el-button link type="danger" size="small" @click="removeMapping(i)" v-if="form.mappings.length>1">删除此映射</el-button>
        </div>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="描述" label-width="60px">
              <el-input v-model="m.desc" placeholder="例如：公司网站" size="default" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="协议" label-width="60px">
              <el-select v-model="m.protocol" size="default" style="width:100%">
                <el-option label="TCP（网页/SSH等）" value="tcp" />
                <el-option label="UDP（DNS/VPN等）" value="udp" />
                <el-option label="TCP+UDP" value="both" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="公网端口" label-width="80px">
              <el-input-number v-model="m.external_port" :min="1" :max="65535" size="default" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="内网IP" label-width="80px">
              <el-input v-model="m.internal_ip" placeholder="192.168.1.100" size="default" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="内网端口" label-width="80px">
              <el-input-number v-model="m.internal_port" :min="1" :max="65535" size="default" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8" />
        </el-row>
      </div>
      <el-button size="small" @click="addMapping" style="margin-top:4px">+ 添加端口映射</el-button>
    </template>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string,any> }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string,any>] }>()

const form = reactive({
  enable_nat: props.modelValue?.enable_nat ?? true,
  mappings: props.modelValue?.mappings || [
    { desc: '', protocol: 'tcp', external_port: 80, internal_ip: '192.168.1.100', internal_port: 80 },
  ],
})

function addMapping() {
  form.mappings.push({ desc: '', protocol: 'tcp', external_port: 443, internal_ip: '', internal_port: 443 })
}

function removeMapping(i: number) { form.mappings.splice(i, 1) }

watch(() => form, () => emit('update:modelValue', { ...form }), { deep: true })
</script>
