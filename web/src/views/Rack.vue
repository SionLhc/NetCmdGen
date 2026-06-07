<template>
  <div class="page"><h2>🗄️ 机柜管理</h2>
    <div style="display:flex;gap:12px;margin-bottom:14px;flex-wrap:wrap"><el-button size="small" type="primary" @click="showAdd=true">+ 新增机柜</el-button>
      <el-select v-model="activeRack" placeholder="选择机柜" size="small" style="width:200px" @change="load"><el-option v-for="r in racks" :key="r.id" :label="r.name" :value="r.id"/></el-select>
    </div>
    <el-dialog v-model="showAdd" title="新增机柜" width="360px"><el-form label-width="80px" size="default">
      <el-form-item label="名称"><el-input v-model="f.name" placeholder="A01"/></el-form-item>
      <el-form-item label="位置"><el-input v-model="f.loc" placeholder="机房A排"/></el-form-item>
      <el-form-item label="U数"><el-input-number v-model="f.rows" :min="12" :max="48"/></el-form-item>
    </el-form><template #footer><el-button @click="showAdd=false">取消</el-button><el-button type="primary" @click="addRack">创建</el-button></template></el-dialog>
    <el-dialog v-model="showDev" title="添加设备" width="380px"><el-form label-width="80px" size="default">
      <el-form-item label="名称"><el-input v-model="df.name" placeholder="交换机-01"/></el-form-item>
      <el-form-item label="品牌"><el-input v-model="df.vendor"/></el-form-item>
      <el-form-item label="U位起"><el-input-number v-model="df.ustart" :min="1" :max="48"/></el-form-item>
      <el-form-item label="U高度"><el-input-number v-model="df.uheight" :min="1" :max="10"/></el-form-item>
      <el-form-item label="IP"><el-input v-model="df.ip"/></el-form-item>
    </el-form><template #footer><el-button @click="showDev=false">取消</el-button><el-button type="primary" @click="addDev">添加</el-button></template></el-dialog>
    <div v-if="rack" class="rack-visual">
      <div class="ru" v-for="u in rack.rows" :key="u" :class="{occupied:deviceAtU(u)}" @click="selectU(u)">
        <span class="ru-num">{{ rack.rows-u+1 }}</span>
        <div v-if="deviceAtU(u)" class="ru-dev" :title="deviceAtU(u).name">
          <span class="ru-name">{{ deviceAtU(u).name }}</span>
          <span class="ru-det">{{ deviceAtU(u).vendor }} · U{{ deviceAtU(u).u_start }}-{{ deviceAtU(u).u_start+deviceAtU(u).u_height-1 }}</span>
        </div>
      </div>
    </div>
    <div v-if="rack" style="margin-top:10px"><el-button size="small" @click="showDev=true">+ 添加设备到 {{ rack.name }}</el-button></div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
const racks=ref<any[]>([]);const activeRack=ref('');const rack=ref<any>(null);const showAdd=ref(false);const showDev=ref(false)
const f=ref({name:'',loc:'',rows:42});const df=ref({name:'',vendor:'',ustart:1,uheight:1,ip:''})
function deviceAtU(u:number){if(!rack.value)return null;const rev=rack.value.rows-u+1;for(const d of rack.value.devices||[]){if(rev>=d.u_start&&rev<d.u_start+d.u_height)return d}return null}
function selectU(u:number){const d=deviceAtU(u);if(d){df.value.ustart=u;df.value.uheight=1}}
async function load(){const r=await fetch('/api/rack/racks');racks.value=await r.json();if(activeRack.value)rack.value=racks.value.find((x:any)=>x.id==activeRack.value)}
async function addRack(){await fetch(`/api/rack/racks?name=${encodeURIComponent(f.value.name)}&location=${f.value.loc}&rows=${f.value.rows}`,{method:'POST'});showAdd.value=false;load()}
async function addDev(){await fetch(`/api/rack/devices?rack_id=${rack.value.id}&name=${encodeURIComponent(df.value.name)}&vendor=${df.value.vendor}&u_start=${df.value.ustart}&u_height=${df.value.uheight}&ip=${df.value.ip}`,{method:'POST'});showDev.value=false;load()}
onMounted(load)
</script>
<style scoped>
.page{padding:24px;max-width:900px;margin:0 auto}h2{margin:0 0 14px;font-size:20px}
.rack-visual{background:#1e293b;border-radius:10px;padding:8px;max-width:320px}
.ru{height:30px;display:flex;align-items:center;border-bottom:1px solid #334155;padding:0 8px;cursor:pointer;transition:.2s}.ru:hover{background:rgba(255,255,255,.05)}
.ru.occupied{background:rgba(59,130,246,.15)}.ru-num{color:#64748b;font-size:11px;width:24px}.ru-dev{font-size:11px;color:#e2e8f0;flex:1;display:flex;justify-content:space-between}.ru-det{color:#64748b}
</style>
