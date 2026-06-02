<template>
  <el-form label-width="100px" size="default">
    <p style="font-size:12px;color:#909399;margin:0 0 12px">
      💡 访问控制：定义哪些设备/网段可以或不可以上网。每条规则从上到下匹配。
    </p>

    <div v-for="(r, i) in form.rules" :key="i" style="border:1px solid #ebeef5;border-radius:6px;padding:12px;margin-bottom:10px;background:#fafbfc">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
        <span :style="{fontWeight:600,fontSize:'13px',color:r.action==='deny'?'#f56c6c':'#67c23a'}">{{ r.action === 'deny' ? '🚫 禁止' : '✅ 允许' }}（规则 {{ i + 1 }}）</span>
        <el-button link type="danger" size="small" @click="form.rules.splice(i,1)" v-if="form.rules.length>1">删除</el-button>
      </div>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="动作" label-width="60px">
            <el-select v-model="r.action" size="default" style="width:100%">
              <el-option label="🚫 禁止" value="deny" />
              <el-option label="✅ 允许" value="permit" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="协议" label-width="60px">
            <el-select v-model="r.protocol" size="default" style="width:100%">
              <el-option label="所有" value="ip" />
              <el-option label="TCP" value="tcp" />
              <el-option label="UDP" value="udp" />
              <el-option label="ICMP(Ping)" value="icmp" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="端口" label-width="60px">
            <el-input v-model="r.dst_port" placeholder="80,443（留空=所有）" size="default" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="12">
        <el-col :span="12">
          <el-form-item label="源地址" label-width="80px">
            <el-input v-model="r.src_ip" placeholder="192.168.1.0/24" size="default" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="目的地址" label-width="80px">
            <el-input v-model="r.dst_ip" placeholder="留空=任意地址" size="default" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="描述" label-width="80px">
        <el-input v-model="r.desc" placeholder="例如：禁止财务部上网" size="default" />
      </el-form-item>
    </div>
    <el-button size="small" @click="form.rules.push({action:'deny',protocol:'ip',src_ip:'',dst_ip:'',dst_port:'',desc:''})">+ 添加规则</el-button>
    <div v-if="form.rules.length>0" style="font-size:12px;color:#909399;margin-top:8px">ℹ 规则从上到下匹配，默认最后一条隐含 deny all</div>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string,any> }>()
const emit = defineEmits<{ 'update:modelValue': [v: Record<string,any>] }>()

const form = reactive({
  rules: props.modelValue?.rules || [
    { action: 'permit', protocol: 'tcp', src_ip: '192.168.1.0/24', dst_ip: '', dst_port: '22,443', desc: '允许内网上网' },
  ],
})

watch(() => form, () => emit('update:modelValue', { ...form }), { deep: true })
</script>
