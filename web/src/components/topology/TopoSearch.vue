<template>
  <div class="topo-search">
    <el-input v-model="keyword" placeholder="搜索设备..." size="small" clearable style="width:180px" @input="onSearch">
      <template #prefix><span>🔍</span></template>
    </el-input>
    <el-select v-model="layer" size="small" style="width:100px" @change="onFilter">
      <el-option label="全部" value="all"/>
      <el-option label="核心层" value="core"/>
      <el-option label="汇聚层" value="dist"/>
      <el-option label="接入层" value="access"/>
    </el-select>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
const emit = defineEmits<{search:[kw:string];filter:[layer:string]}>()
const keyword=ref(''); const layer=ref('all')
function onSearch(){emit('search',keyword.value)}
function onFilter(){emit('filter',layer.value)}
</script>
<style scoped>
.topo-search{display:flex;align-items:center;gap:6px;margin-left:auto}
</style>
