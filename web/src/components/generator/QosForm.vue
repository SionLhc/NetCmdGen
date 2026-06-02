<template>
  <el-form label-width="90px" size="small" @change="emitUpdate">
    <!-- 流分类 -->
    <el-divider content-position="left">流分类</el-divider>
    <div v-for="(cls, idx) in classifiers" :key="'cls'+idx" class="sec-section">
      <div class="sec-header">
        <span>分类: {{ cls.name || '(未命名)' }}</span>
        <el-button text type="danger" size="small" @click="classifiers.splice(idx,1);emitUpdate()">删除</el-button>
      </div>
      <el-input v-model="cls.name" placeholder="分类名称" size="small" @change="emitUpdate" />
      <div v-for="(r, ri) in cls.rules" :key="'cr'+ri" class="rule-row">
        <el-row :gutter="4">
          <el-col :span="8">
            <el-select v-model="r.type" @change="emitUpdate">
              <el-option label="DSCP" value="dscp" />
              <el-option label="VLAN" value="vlan" />
              <el-option label="协议" value="protocol" />
              <el-option label="源IP" value="source_ip" />
              <el-option label="端口" value="destination_port" />
            </el-select>
          </el-col>
          <el-col :span="13"><el-input v-model="r.value" placeholder="值" @change="emitUpdate" /></el-col>
          <el-col :span="3"><el-button text type="danger" size="small" @click="cls.rules.splice(ri,1);emitUpdate()">✕</el-button></el-col>
        </el-row>
      </div>
      <el-button size="small" type="primary" plain @click="cls.rules.push({type:'dscp',value:'46'});emitUpdate()">+ 规则</el-button>
    </div>
    <el-button size="small" type="primary" plain @click="classifiers.push({name:'Class1',rules:[{type:'dscp',value:'46'}]});emitUpdate()" style="width:100%">+ 添加分类</el-button>

    <!-- 流行为 -->
    <el-divider content-position="left">流行为</el-divider>
    <div v-for="(b, idx) in behaviors" :key="'beh'+idx" class="sec-section">
      <div class="sec-header">
        <span>行为: {{ b.name || '(未命名)' }}</span>
        <el-button text type="danger" size="small" @click="behaviors.splice(idx,1);emitUpdate()">删除</el-button>
      </div>
      <el-input v-model="b.name" placeholder="行为名称" size="small" @change="emitUpdate" />
      <div v-for="(a, ai) in b.actions" :key="'ba'+ai" class="rule-row">
        <el-row :gutter="4">
          <el-col :span="8">
            <el-select v-model="a.type" @change="emitUpdate">
              <el-option label="重标 DSCP" value="remark_dscp" />
              <el-option label="CAR 限速" value="car" />
              <el-option label="放行" value="permit" />
              <el-option label="丢弃" value="deny" />
              <el-option label="重定向" value="redirect" />
              <el-option label="统计" value="statistic" />
            </el-select>
          </el-col>
          <el-col :span="13">
            <el-input v-if="a.type!=='permit'&&a.type!=='deny'&&a.type!=='statistic'" v-model="a.value" placeholder="值" @change="emitUpdate" />
          </el-col>
          <el-col :span="3"><el-button text type="danger" size="small" @click="b.actions.splice(ai,1);emitUpdate()">✕</el-button></el-col>
        </el-row>
      </div>
      <el-button size="small" type="primary" plain @click="b.actions.push({type:'remark_dscp',value:'46'});emitUpdate()">+ 动作</el-button>
    </div>
    <el-button size="small" type="primary" plain @click="behaviors.push({name:'Behav1',actions:[{type:'remark_dscp',value:'46'}]});emitUpdate()" style="width:100%">+ 添加行为</el-button>

    <!-- 流策略 -->
    <el-divider content-position="left">流策略</el-divider>
    <div v-for="(p, idx) in policies" :key="'pol'+idx" class="sec-section">
      <div class="sec-header">
        <span>策略: {{ p.name || '(未命名)' }}</span>
        <el-button text type="danger" size="small" @click="policies.splice(idx,1);emitUpdate()">删除</el-button>
      </div>
      <el-input v-model="p.name" placeholder="策略名称" size="small" @change="emitUpdate" />
      <div v-for="(pair, pi) in p.pairs" :key="'pp'+pi" class="rule-row">
        <el-row :gutter="4">
          <el-col :span="11"><el-input v-model="pair.classifier" placeholder="分类名" @change="emitUpdate" /></el-col>
          <el-col :span="11"><el-input v-model="pair.behavior" placeholder="行为名" @change="emitUpdate" /></el-col>
          <el-col :span="2"><el-button text type="danger" size="small" @click="p.pairs.splice(pi,1);emitUpdate()">✕</el-button></el-col>
        </el-row>
      </div>
      <el-button size="small" type="primary" plain @click="p.pairs.push({classifier:'',behavior:''});emitUpdate()">+ 绑定</el-button>
    </div>
    <el-button size="small" type="primary" plain @click="policies.push({name:'Policy1',pairs:[]});emitUpdate()" style="width:100%">+ 添加策略</el-button>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{ modelValue: Record<string, any> }>()
const emit = defineEmits<{ 'update:modelValue': [value: Record<string, any>] }>()

const classifiers = reactive<Array<any>>(props.modelValue.classifiers || [])
const behaviors = reactive<Array<any>>(props.modelValue.behaviors || [])
const policies = reactive<Array<any>>(props.modelValue.policies || [])

function emitUpdate() {
    const params: Record<string, any> = {}
    if (classifiers.length > 0) params.classifiers = [...classifiers]
    if (behaviors.length > 0) params.behaviors = [...behaviors]
    if (policies.length > 0) {
        params.policies = policies.map(p => ({
            name: p.name,
            classifier_behavior_pairs: p.pairs,
        }))
    }
    emit('update:modelValue', params)
}

watch([classifiers, behaviors, policies], emitUpdate, { deep: true })
</script>

<style scoped>
.sec-section { margin-bottom: 10px; padding: 8px; background: #fff; border-radius: 6px; border: 1px solid #ebeef5; }
.sec-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 12px; color: #606266; }
.rule-row { margin: 4px 0; }
</style>
