<template>
  <div class="tools-page">
    <div class="tools-header">
      <el-input v-model="search" placeholder="搜索 17 个网络工具..." clearable size="large" style="max-width:420px">
        <template #prefix><span style="font-size:18px">🔍</span></template>
      </el-input>
      <el-radio-group v-model="filterLevel" size="small" style="margin-left:12px">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="p0">常用</el-radio-button>
        <el-radio-button value="p1">推荐</el-radio-button>
        <el-radio-button value="p2">辅助</el-radio-button>
      </el-radio-group>
    </div>
    <div class="tool-cards">
      <div v-for="tool in filteredTools" :key="tool.id" class="tool-card" @click="openTool(tool)">
        <div class="tool-icon">{{ tool.icon }}</div><div class="tool-name">{{ tool.name }}</div>
        <div class="tool-desc">{{ tool.desc }}</div>
        <el-tag size="small" :type="tool.level==='p0'? '' : tool.level==='p1'?'success':'info'">{{ tool.level==='p0'?'常用':tool.level==='p1'?'推荐':'辅助' }}</el-tag>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="activeTool?.name" width="900px" top="3vh" destroy-on-close>
      <!-- ═══ 子网计算器 ═══ -->
      <template v-if="activeId==='subnet'">
        <div class="param-bar"><el-input v-model="s.ip" placeholder="192.168.1.10" class="inp-m" /> <span class="sep">/</span> <el-input v-model="s.mask" placeholder="24" class="inp-s" /><el-button type="primary" @click="onSubnet" :loading="loadSub" style="margin-left:12px">计算</el-button></div>
        <div v-if="subnetR" class="result-box">
          <div class="cidr-bar"><div class="bar-seg network">网络号</div><div class="bar-seg hosts">{{ subnetR.usable_hosts }} 个可用IP（{{ subnetR.first_usable }} → {{ subnetR.last_usable }}）</div><div class="bar-seg broadcast">广播</div></div>
          <el-descriptions :column="3" border size="small" style="margin-top:16px">
            <el-descriptions-item label="IP 地址"><b>{{ s.ip }}</b></el-descriptions-item>
            <el-descriptions-item label="掩码">{{ subnetR.subnet_mask }}</el-descriptions-item>
            <el-descriptions-item label="CIDR">/{{ subnetR.prefix_length }}</el-descriptions-item>
            <el-descriptions-item label="网络地址"><el-tag type="primary" size="small">{{ subnetR.network_address }}</el-tag></el-descriptions-item>
            <el-descriptions-item label="广播地址"><el-tag type="warning" size="small">{{ subnetR.broadcast_address }}</el-tag></el-descriptions-item>
            <el-descriptions-item label="可用主机"><b style="color:#67c23a">{{ subnetR.usable_hosts }}</b></el-descriptions-item>
            <el-descriptions-item label="可用范围" :span="2"><code>{{ subnetR.first_usable }} ~ {{ subnetR.last_usable }}</code></el-descriptions-item>
            <el-descriptions-item label="IP 类型">{{ subnetR.ip_type }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </template>

      <!-- ═══ Ping ═══ -->
      <template v-if="activeId==='ping'">
        <div class="param-block">
          <div class="param-main">
            <span class="param-label">目标地址</span>
            <el-input v-model="p.target" placeholder="8.8.8.8 或 baidu.com" class="inp-l" />
            <div class="slider-wrap">
              <span class="param-label">发包次数</span>
              <el-slider v-model="p.count" :min="1" :max="50" show-input :show-input-controls="false" class="main-slider" />
            </div>
          </div>
          <el-collapse v-model="p.advanced">
            <el-collapse-item title="⚙ 高级参数" name="adv">
              <div class="adv-grid">
                <div class="adv-item"><span>超时</span><el-input-number v-model="p.timeout" :min="0.5" :max="10" :step="0.5" size="small" /> 秒</div>
              </div>
            </el-collapse-item>
          </el-collapse>
          <div class="param-summary">目标: <b>{{ p.target }}</b> · 发包 {{ p.count }} 次 · 超时 {{ p.timeout }}s</div>
          <el-button type="primary" @click="onPing" :loading="loadPing" size="large" style="width:100%">开始 Ping</el-button>
        </div>
        <div v-if="pingR" class="result-box">
          <div class="ping-stats"><StatBox label="发送" v="pingR.sent"/><StatBox label="接收" v="pingR.received" c="#67c23a"/><StatBox label="丢包" v="pingR.loss_percent+'%'" :c="pingR.loss_percent>0?'#f56c6c':'#67c23a'"/><StatBox label="最小" v="(pingR.min_rtt||'--')+'ms'" c="#409eff"/><StatBox label="最大" v="(pingR.max_rtt||'--')+'ms'" c="#e6a23c"/><StatBox label="平均" v="(pingR.avg_rtt||'--')+'ms'" c="#409eff"/></div>
          <div ref="pingChartRef" style="height:200px;margin-top:16px;border:1px solid #f0f0f0;border-radius:8px;padding:8px"></div>
          <div class="ping-table"><div v-for="r in pingR.results" :key="r.seq" class="ping-row" :class="{to:r.status==='timeout'}"><span class="pr-seq">#{{ r.seq }}</span><span class="pr-val" :style="{color:r.rtt===null?'#f56c6c':r.rtt<30?'#67c23a':r.rtt<100?'#e6a23c':'#f56c6c'}">{{ r.rtt!==null?r.rtt+'ms':'超时 ⚠' }}</span></div></div>
        </div>
      </template>

      <!-- ═══ 端口扫描 ═══ -->
      <template v-if="activeId==='portscan'">
        <div class="param-block">
          <div class="param-main"><span class="param-label">目标</span><el-input v-model="ps.target" placeholder="192.168.1.1" class="inp-l" /><span class="param-label" style="margin-left:12px">端口</span><el-input v-model="ps.ports" placeholder="22,80,443,3389" class="inp-l" /></div>
          <div class="param-summary">扫描: <b>{{ ps.target }}</b> 端口 {{ ps.ports }} · 离散模式</div>
          <el-button type="primary" @click="onScan" :loading="loadScan" size="large" style="width:100%">开始扫描</el-button>
        </div>
        <div v-if="scanR" class="result-box">
          <div class="ping-stats"><StatBox label="目标" v="scanR.target"/><StatBox label="已扫描" v="scanR.scanned||scanR.total" c="#409eff"/><StatBox label="开放" v="scanR.open_count" :c="scanR.open_count>0?'#67c23a':'#909399'"/></div>
          <div v-if="scanR.all_closed" style="text-align:center;padding:24px;color:#67c23a;font-size:15px">🎉 所有端口均已关闭或过滤，目标较安全</div>
          <el-table v-else-if="scanR.open_ports?.length" :data="scanR.open_ports" border size="small" style="margin-top:12px">
            <el-table-column type="index" label="#" width="44"/><el-table-column prop="port" label="端口" width="80" sortable><template #default="{row}"><b>{{ row.port }}</b></template></el-table-column><el-table-column prop="service" label="服务" width="130"/><el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip/>
            <el-table-column label="风险" width="80" align="center"><template #default="{row}"><el-tag :type="row.risk==='high'?'danger':row.risk==='medium'?'warning':'success'" size="small">{{ row.risk==='high'?'高危':row.risk==='medium'?'中危':'低' }}</el-tag></template></el-table-column>
          </el-table>
        </div>
      </template>

      <!-- ═══ 路由追踪 ═══ -->
      <template v-if="activeId==='traceroute'">
        <div class="param-block">
          <div class="param-main">
            <span class="param-label">目标地址</span>
            <el-input v-model="tr.target" placeholder="8.8.8.8 或 baidu.com" class="inp-l" />
            <div class="slider-wrap"><span class="param-label">最大跳数</span><el-slider v-model="tr.maxhops" :min="1" :max="30" show-input :show-input-controls="false" class="main-slider"/></div>
          </div>
          <el-collapse v-model="tr.advanced"><el-collapse-item title="⚙ 高级参数" name="adv"><div class="adv-grid"><div class="adv-item"><span>超时</span><el-input-number v-model="tr.timeout" :min="0.5" :max="5" :step="0.5" size="small"/> 秒</div></div></el-collapse-item></el-collapse>
          <div class="param-summary">目标: <b>{{ tr.target }}</b> · 最大 {{ tr.maxhops }} 跳 · 超时 {{ tr.timeout }}s</div>
          <el-button type="primary" @click="onTrace" :loading="loadTrace" size="large" style="width:100%">开始追踪</el-button>
        </div>
        <div v-if="traceR" class="result-box">
          <div class="ping-stats"><StatBox label="目标" v="tr.target"/><StatBox label="总跳数" v="traceR.total_hops" c="#409eff"/><StatBox label="到达?" v="traceR.hops[traceR.hops.length-1]?.ip==='超时'?'未到达':'已到达'" :c="traceR.hops[traceR.hops.length-1]?.ip==='超时'?'#f56c6c':'#67c23a'"/></div>
          <div class="trace-timeline" style="margin-top:16px">
            <div v-for="(h,i) in traceR.hops" :key="i" class="trace-hop">
              <div class="hop-num" :class="{timeout:h.ip==='超时'}">{{ h.hop }}</div>
              <div class="hop-body">
                <div class="hop-main"><span class="hop-ip" :style="{color:h.ip==='超时'?'#f56c6c':'#409eff'}">{{ h.ip }}</span><span v-if="h.avg_rtt" class="hop-avg">{{ h.avg_rtt }}ms</span><span v-else class="hop-avg" style="color:#f56c6c">超时</span></div>
                <div v-if="h.rtts?.length" class="hop-detail">单次: {{ h.rtts.join('ms, ') }}ms</div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- ═══ DNS ═══ -->
      <template v-if="activeId==='dns'">
        <div class="param-bar"><el-input v-model="d.domain" placeholder="baidu.com" class="inp-l"/><el-select v-model="d.type" style="width:100px;margin:0 8px"><el-option v-for="t in ['A','AAAA','MX','NS','TXT','CNAME']" :key="t" :label="t" :value="t"/></el-select><el-button type="primary" @click="onDns" :loading="loadDns">查询</el-button></div>
        <div v-if="dnsR" class="result-box"><div class="ping-stats" style="margin-bottom:12px"><StatBox label="域名" v="d.domain"/><StatBox label="记录" v="d.type" c="#409eff"/></div>
          <el-table :data="dnsR.results" border size="small"><el-table-column prop="resolver" label="DNS 服务器" width="130"/><el-table-column label="解析结果"><template #default="{row}"><template v-if="row.status==='ok'"><el-tag v-for="(a,i) in row.answers" :key="i" size="small" style="margin:2px">{{ a }}</el-tag></template><span v-else style="color:#f56c6c">{{ row.answers[0] }}</span></template></el-table-column><el-table-column label="状态" width="70"><template #default="{row}"><el-tag :type="row.status==='ok'?'success':'danger'" size="small">{{ row.status==='ok'?'✅':'❌' }}</el-tag></template></el-table-column></el-table>
        </div>
      </template>

      <!-- ═══ 快速工具（VLSM/CIDR/通配符/MAC/IP/DHCP等）═══ -->
      <template v-if="activeId==='split'"><div class="param-bar">网络 <el-input v-model="sp.network" placeholder="192.168.1.0" class="inp-m"/> /<el-input-number v-model="sp.prefix" :min="0" :max="32" size="small" class="nip"/> → /<el-input-number v-model="sp.newPrefix" :min="1" :max="32" size="small" class="nip"/><el-button type="primary" @click="onSplit" :loading="loadSplit" style="margin-left:12px">划分</el-button></div><el-table v-if="splitR?.subnets?.length" :data="splitR.subnets" border size="small"><el-table-column type="index" label="#" width="50"/><el-table-column prop="subnet" label="子网" width="180"/><el-table-column label="可用范围"><template #default="{row}">{{ row.first_host }} ~ {{ row.last_host }}</template></el-table-column><el-table-column prop="hosts" label="主机数" width="100"/></el-table></template>

      <template v-if="activeId==='cidr-merge'"><div class="param-bar"><el-input v-model="cm.input" placeholder="192.168.1.0/24, 192.168.2.0/24" type="textarea" :rows="3" class="inp-f"/><el-button type="primary" @click="onCidrMerge" style="margin-left:12px;vertical-align:top">汇总</el-button></div><div v-if="cm.result" class="result-box"><b>汇总结果：</b><el-tag v-for="r in cm.result" :key="r" size="default" style="margin:4px">{{ r }}</el-tag></div></template>

      <template v-if="activeId==='cidr-diff'"><div class="param-bar"><span>列表A</span><el-input v-model="cd.a" placeholder="10.0.0.0/8" class="inp-m"/><span style="margin-left:16px">列表B</span><el-input v-model="cd.b" placeholder="10.0.0.0/16" class="inp-m"/><el-button type="primary" @click="onCidrDiff" style="margin-left:12px">对比</el-button></div><div v-if="cd.result" class="result-box"><p>新增: <el-tag v-for="r in cd.result.added" :key="r" type="success" size="small" style="margin:2px">{{ r }}</el-tag></p><p>移除: <el-tag v-for="r in cd.result.removed" :key="r" type="danger" size="small" style="margin:2px">{{ r }}</el-tag></p><p>不变: <el-tag v-for="r in cd.result.same" :key="r" size="small" style="margin:2px">{{ r }}</el-tag></p></div></template>

      <template v-if="activeId==='wildcard'"><div class="result-box"><div class="param-bar">CIDR <span style="font-weight:700;font-size:18px;margin:0 8px">/</span><el-input-number v-model="wc.prefix" :min="0" :max="32" size="large" class="nip" style="width:100px"/></div><el-descriptions :column="2" border size="small"><el-descriptions-item label="子网掩码"><code style="font-size:15px;color:#409eff">{{ wcMask }}</code></el-descriptions-item><el-descriptions-item label="通配符掩码"><code style="font-size:15px;color:#e6a23c">{{ wcWildcard }}</code></el-descriptions-item></el-descriptions><div style="margin-top:16px;background:#1a1b2e;padding:12px;border-radius:6px"><code style="color:#86efac">rule 5 permit source 192.168.1.0 {{ wcWildcard }}</code></div></div></template>

      <template v-if="activeId==='mac'"><div class="param-bar"><el-input v-model="mac.addr" placeholder="E4-5F-01-02-03-04" class="inp-l" @keyup.enter="onMacLookup"/><el-button type="primary" @click="onMacLookup" style="margin-left:12px">查询</el-button></div><div v-if="mac.result" class="result-box"><el-descriptions border size="small"><el-descriptions-item label="MAC地址"><code>{{ mac.addr }}</code></el-descriptions-item><el-descriptions-item label="OUI前缀"><code>{{ macOui }}</code></el-descriptions-item><el-descriptions-item label="厂商"><b style="color:#409eff">{{ mac.result }}</b></el-descriptions-item></el-descriptions></div></template>

      <template v-if="activeId==='ip-fmt'"><div class="param-bar"><el-input v-model="ifm.ip" placeholder="192.168.1.1" class="inp-m" @keyup.enter="onIpFmt"/><el-button type="primary" @click="onIpFmt" style="margin-left:12px">转换</el-button></div><el-descriptions v-if="ifm.result" :column="1" border size="small" style="margin-top:12px"><el-descriptions-item label="十进制">{{ ifm.result.decimal }}</el-descriptions-item><el-descriptions-item label="二进制"><code>{{ ifm.result.binary }}</code></el-descriptions-item><el-descriptions-item label="十六进制"><code>{{ ifm.result.hex }}</code></el-descriptions-item><el-descriptions-item label="八进制"><code>{{ ifm.result.octal }}</code></el-descriptions-item></el-descriptions></template>

      <template v-if="activeId==='dhcp43'"><div class="param-bar"><el-select v-model="dhcp.vendor" style="width:110px"><el-option label="Cisco" value="cisco"/><el-option label="Aruba" value="aruba"/><el-option label="UniFi" value="unifi"/><el-option label="Ruckus" value="ruckus"/></el-select><el-input v-model="dhcp.acIp" placeholder="AC管理IP" class="inp-m" style="margin:0 8px"/><el-button type="primary" @click="onDhcp43">生成</el-button></div><div v-if="dhcp.result" class="result-box"><el-descriptions border size="small"><el-descriptions-item label="厂商">{{ dhcp.vendor.toUpperCase() }}</el-descriptions-item><el-descriptions-item label="AC地址">{{ dhcp.acIp }}</el-descriptions-item><el-descriptions-item label="Option 43值"><code style="color:#67c23a;word-break:break-all">{{ dhcp.result }}</code></el-descriptions-item></el-descriptions></div></template>

      <template v-if="activeId==='port-lookup'"><el-input v-model="pl.port" placeholder="端口号" class="inp-m" type="number" style="margin-bottom:12px"/><div v-if="pl.result" class="result-box" style="margin-bottom:12px"><b style="font-size:16px">{{ pl.port }}</b> — <el-tag size="large">{{ pl.result }}</el-tag></div><el-divider>常用端口速查</el-divider><div style="display:flex;flex-wrap:wrap;gap:4px"><el-tag v-for="pt in commonPorts" :key="pt.p" size="small" style="cursor:pointer" @click="pl.port=String(pt.p);onPortLookup()">{{ pt.p }}:{{ pt.n }}</el-tag></div></template>

      <template v-if="activeId==='randip'"><div class="param-bar"><el-select v-model="ri.mode" style="width:120px"><el-option label="完全随机" value="random"/><el-option label="10.x私网" value="private10"/><el-option label="192.168.x" value="private192"/><el-option label="CIDR内" value="cidr"/></el-select><el-input v-if="ri.mode==='cidr'" v-model="ri.cidr" placeholder="10.0.0.0/16" class="inp-m" style="margin-left:8px"/><span style="margin:0 8px">×</span><el-input-number v-model="ri.count" :min="1" :max="50" size="small" class="nip"/><el-button type="primary" @click="onRandIp" style="margin-left:12px">生成</el-button></div><div v-if="ri.ips?.length" style="display:flex;flex-wrap:wrap;gap:4px;margin-top:12px"><el-tag v-for="ip in ri.ips" :key="ip">{{ ip }}</el-tag></div></template>

      <template v-if="activeId==='timestamp'"><div class="param-bar"><el-input v-model="ts.input" placeholder="时间戳(秒) 或 2026-06-03" class="inp-l" @keyup.enter="onTsConvert"/><el-button type="primary" @click="onTsConvert" style="margin-left:12px">转换</el-button></div><el-descriptions v-if="ts.result" border size="small" style="margin-top:12px"><el-descriptions-item label="输入"><code>{{ ts.input }}</code></el-descriptions-item><el-descriptions-item label="结果">{{ ts.result }}</el-descriptions-item></el-descriptions></template>

      <template v-if="activeId==='base64'"><el-input v-model="b64.input" placeholder="输入文本" type="textarea" :rows="4"/><div style="display:flex;gap:8px;margin-top:12px"><el-button @click="onB64('encode')">编码 (Base64)</el-button><el-button @click="onB64('decode')">解码 (Base64)</el-button></div><div v-if="b64.output" style="background:#f5f7fa;padding:16px;border-radius:8px;margin-top:12px;font-family:monospace;font-size:13px;word-break:break-all;max-height:200px;overflow:auto">{{ b64.output }}</div></template>

      <template v-if="activeId==='json'"><el-input v-model="js.input" placeholder='{"name":"test"}' type="textarea" :rows="5"/><el-button type="primary" @click="onJson" style="margin-top:12px">格式化</el-button><pre v-if="js.output" style="background:#1a1b2e;color:#c9d1d9;padding:16px;border-radius:8px;margin-top:12px;max-height:400px;overflow:auto;font-size:13px;line-height:1.6">{{ js.output }}</pre></template>

      <template #footer><el-button @click="dialogVisible=false">关闭</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { calcSubnet, splitSubnet, doPing, doPortScan, doTrace, doDns } from '@/api'
import StatBox from '@/components/StatBox.vue'
import * as echarts from 'echarts'

const tools = [
  {id:'subnet',icon:'🔢',name:'子网计算器',desc:'IP+掩码→网络/广播/范围，CIDR可视化条',level:'p0',category:'子网'},
  {id:'ping',icon:'📡',name:'Ping 测试',desc:'连通检测+延迟波形图+丢包统计',level:'p0',category:'诊断'},
  {id:'portscan',icon:'🔍',name:'端口扫描',desc:'离散/范围+服务识别+风险评级',level:'p0',category:'诊断'},
  {id:'traceroute',icon:'🗺️',name:'路由追踪',desc:'逐跳时间线+详细延迟',level:'p0',category:'诊断'},
  {id:'dns',icon:'🌐',name:'DNS 查询',desc:'4解析器对比(阿里/Google/CF/Quad9)',level:'p1',category:'诊断'},
  {id:'split',icon:'✂️',name:'VLSM 子网划分',desc:'变长子网自动拆分表格',level:'p1',category:'子网'},
  {id:'cidr-merge',icon:'🧩',name:'CIDR 汇总',desc:'多网段→最小前缀集合',level:'p1',category:'子网'},
  {id:'wildcard',icon:'🎯',name:'通配符掩码',desc:'CIDR↔反掩码+ACL命令',level:'p1',category:'子网'},
  {id:'dhcp43',icon:'📡',name:'DHCP Option 43',desc:'Cisco/Aruba/UniFi AP发现AC',level:'p1',category:'配置'},
  {id:'mac',icon:'🖧',name:'MAC 厂商查询',desc:'OUI前缀→制造商(100+厂商)',level:'p1',category:'地址'},
  {id:'cidr-diff',icon:'⚖️',name:'CIDR 对比',desc:'两套列表差异(新增/移除/不变)',level:'p2',category:'子网'},
  {id:'ip-fmt',icon:'🔣',name:'IP 格式转换',desc:'十↔二↔十六↔八进制',level:'p2',category:'地址'},
  {id:'randip',icon:'🎲',name:'随机 IP 生成',desc:'CIDR内/私网/随机三模式',level:'p2',category:'地址'},
  {id:'port-lookup',icon:'📋',name:'端口服务速查',desc:'端口号↔服务名,23常用标签',level:'p2',category:'地址'},
  {id:'timestamp',icon:'⏰',name:'时间戳转换',desc:'Unix↔日期双向互转',level:'p2',category:'工具'},
  {id:'base64',icon:'🔐',name:'Base64 编解码',desc:'文本/证书Base64加解密',level:'p2',category:'工具'},
  {id:'json',icon:'📦',name:'JSON 格式化',desc:'压缩→美化,快速检查结构',level:'p2',category:'工具'},
]
const search=ref(''), filterLevel=ref('all')
const filteredTools=computed(()=>tools.filter(t=>(!search.value||t.name.includes(search.value)||t.desc.includes(search.value))&&(filterLevel.value==='all'||t.level===filterLevel.value)))
const activeId=ref(''), dialogVisible=ref(false)
const atool=computed(()=>tools.find(t=>t.id===activeId.value))
function openTool(t:typeof tools[0]){ activeId.value=t.id; dialogVisible.value=true }

// Subnet
const s=ref({ip:'192.168.1.10',mask:'24'}), subR=ref<any>(null), loadSub=ref(false)
async function onSubnet(){loadSub.value=true;try{subR.value=await calcSubnet(s.value.ip,s.value.mask)}catch(e:any){ElMessage.error(e.response?.data?.detail)}finally{loadSub.value=false}}

// Ping
const p=reactive({target:'8.8.8.8',count:10,timeout:3,advanced:[] as string[]})
const pingR=ref<any>(null), loadPing=ref(false)
const pingCRef=ref<HTMLElement|null>(null); let pingChart:any=null
async function onPing(){loadPing.value=true;try{pingR.value=await doPing(p.target,p.count,p.timeout);await nextTick();if(pingCRef.value){if(!pingChart)pingChart=echarts.init(pingCRef.value);pingChart.setOption({tooltip:{trigger:'axis'},grid:{top:20,right:20,bottom:30,left:45},xAxis:{type:'category',data:pingR.value.results.map((_:any,i:number)=>`#${i+1}`)},yAxis:{type:'value',name:'ms'},series:[{data:pingR.value.results.map((r:any)=>r.rtt??null),name:'延迟',type:'line',smooth:true,areaStyle:{opacity:0.2},markLine:{data:[{yAxis:pingR.value.avg_rtt,name:'平均'}],label:{formatter:'{c}ms'},lineStyle:{type:'dashed'}},itemStyle:{color:'#409eff'}}]},true)}}catch(e:any){ElMessage.error(e.response?.data?.detail)}finally{loadPing.value=false}}

// Port Scan
const ps=reactive({target:'192.168.1.1',ports:'22,80,443,3389'}), scanR=ref<any>(null), loadScan=ref(false)
async function onScan(){loadScan.value=true;try{scanR.value=await doPortScan(ps.target,ps.ports)}catch(e:any){ElMessage.error(e.response?.data?.detail)}finally{loadScan.value=false}}

// Traceroute
const tr=reactive({target:'8.8.8.8',maxhops:15,timeout:2,advanced:[] as string[]}), traceR=ref<any>(null), loadTrace=ref(false)
async function onTrace(){loadTrace.value=true;try{traceR.value=await doTrace(tr.target,tr.maxhops,tr.timeout)}catch(e:any){ElMessage.error(e.response?.data?.detail)}finally{loadTrace.value=false}}

// DNS
const d=reactive({domain:'baidu.com',type:'A'}), dnsR=ref<any>(null), loadDns=ref(false)
async function onDns(){loadDns.value=true;try{dnsR.value=await doDns(d.domain,d.type)}catch(e:any){ElMessage.error(e.response?.data?.detail)}finally{loadDns.value=false}}

// VLSM
const sp=reactive({network:'192.168.1.0',prefix:24,newPrefix:26}), splitR=ref<any>(null), loadSplit=ref(false)
async function onSplit(){loadSplit.value=true;try{splitR.value=await splitSubnet(sp.network,sp.prefix,sp.newPrefix)}catch(e:any){ElMessage.error(e.response?.data?.detail)}finally{loadSplit.value=false}}

// CIDR helpers
function ip2n(ip:string):number{const p=ip.split('.');return((+p[0]<<24)|(+p[1]<<16)|(+p[2]<<8)|(+p[3]))>>>0}
function n2ip(n:number):string{return[(n>>>24)&255,(n>>>16)&255,(n>>>8)&255,n&255].join('.')}
function r2cidr(s:number,e:number):string{let b=32;while(b>0){const m=(~0)>>>b;if((s&m)===s&&(e&~m)>>>0===e)break;b--}return`${n2ip(s)}/${b}`}
const cm=reactive({input:'',result:null as string[]|null})
function onCidrMerge(){try{const c=cm.input.split(/[\s,;]+/).filter(Boolean);if(c.length<2){ElMessage.warning('至少2个CIDR');return}const r=c.map(x=>{const[a,p]=x.split('/');const n=ip2n(a),pre=parseInt(p);return{start:n,end:n+((1<<(32-pre))-1)}});r.sort((a,b)=>a.start-b.start);const m:string[]=[];let cur=r[0];for(let i=1;i<r.length;i++){if(r[i].start<=cur.end+1)cur.end=Math.max(cur.end,r[i].end);else{m.push(r2cidr(cur.start,cur.end));cur=r[i]}}m.push(r2cidr(cur.start,cur.end));cm.result=m}catch{ElMessage.error('格式错误')}}

const cd=reactive({a:'10.0.0.0/8',b:'10.0.0.0/16',result:null as any})
function onCidrDiff(){const al=cd.a.split(/[\s,;]+/).filter(Boolean).sort(),bl=cd.b.split(/[\s,;]+/).filter(Boolean).sort();cd.result={added:bl.filter(x=>!al.includes(x)),removed:al.filter(x=>!bl.includes(x)),same:al.filter(x=>bl.includes(x))}}

const wc=reactive({prefix:24})
const wcMask=computed(()=>{const v=(~0)<<(32-wc.prefix);return`${(v>>>24)&255}.${(v>>>16)&255}.${(v>>>8)&255}.${v&255}`})
const wcWildcard=computed(()=>{const v=~((~0)<<(32-wc.prefix));return`${(v>>>24)&255}.${(v>>>16)&255}.${(v>>>8)&255}.${v&255}`})

const mac=reactive({addr:'',result:''}), macOui=computed(()=>mac.addr.replace(/[:-]/g,'').toUpperCase().slice(0,6))
const OUI:Record<string,string>={'00000C':'Cisco','001AA0':'Cisco','78F5FD':'Huawei','DC2B06':'H3C','386A28':'H3C','D8D0FC':'MikroTik','4C5E0C':'MikroTik','041E64':'Ubiquiti','788A20':'Ubiquiti','58639A':'TP-Link','000B86':'Aruba','001A1E':'Aruba','001C10':'Maipu','08C0DE':'Ruijie','409F87':'Google','000874':'Dell','00146C':'Netgear','000A95':'Apple','B827EB':'RaspberryPi','0006B4':'Fortinet','001C7E':'Juniper','0050BA':'D-Link','080023':'Panasonic','008067':'Intel'}
function onMacLookup(){const a=mac.addr.replace(/[:-]/g,'').toUpperCase().slice(0,12);if(a.length<6){ElMessage.warning('请输入完整MAC');return};mac.result=OUI[macOui.value]||'未找到'}

const ifm=reactive({ip:'192.168.1.1',result:null as any})
function onIpFmt(){try{const n=ip2n(ifm.ip);ifm.result={decimal:String(n),binary:(n>>>0).toString(2).padStart(32,'0').replace(/(.{8})/g,'$1 ').trim(),hex:'0x'+(n>>>0).toString(16).toUpperCase().padStart(8,'0'),octal:'0'+(n>>>0).toString(8)}}catch{ElMessage.error('IP错误')}}

const dhcp=reactive({vendor:'cisco',acIp:'192.168.1.100',result:''})
function onDhcp43(){try{const p=dhcp.acIp.split('.').map(Number);let h='';if(dhcp.vendor==='cisco')h='f104'+p.map(x=>x.toString(16).padStart(2,'0')).join('');else if(dhcp.vendor==='aruba'||dhcp.vendor==='unifi')h='0104'+p.map(x=>x.toString(16).padStart(2,'0')).join('');else h='030c3139322e3136382e312e313030';dhcp.result=h.toUpperCase()}catch{ElMessage.error('IP错误')}}

const pl=reactive({port:'80',result:''})
const cPorts=[{p:21,n:'FTP'},{p:22,n:'SSH'},{p:23,n:'Telnet'},{p:25,n:'SMTP'},{p:53,n:'DNS'},{p:80,n:'HTTP'},{p:110,n:'POP3'},{p:143,n:'IMAP'},{p:161,n:'SNMP'},{p:389,n:'LDAP'},{p:443,n:'HTTPS'},{p:993,n:'IMAPS'},{p:995,n:'POP3S'},{p:1433,n:'MSSQL'},{p:1521,n:'Oracle'},{p:3306,n:'MySQL'},{p:3389,n:'RDP'},{p:5432,n:'PostgreSQL'},{p:6379,n:'Redis'},{p:8080,n:'HTTP-Alt'},{p:8443,n:'HTTPS-Alt'},{p:9090,n:'Web-Admin'},{p:27017,n:'MongoDB'}]
function onPortLookup(){const f=cPorts.find(p=>p.p===Number(pl.port));pl.result=f?f.n:'未知服务'}

const ri=reactive({mode:'random',cidr:'10.0.0.0/16',count:5,ips:[] as string[]})
function onRandIp(){ri.ips=[];for(let i=0;i<ri.count;i++){if(ri.mode==='private10')ri.ips.push(`10.${~~(Math.random()*255)}.${~~(Math.random()*255)}.${~~(Math.random()*254)+1}`);else if(ri.mode==='private192')ri.ips.push(`192.168.${~~(Math.random()*255)}.${~~(Math.random()*254)+1}`);else if(ri.mode==='cidr'){const[a,p]=ri.cidr.split('/');const base=ip2n(a),mask=(~0)<<(32-parseInt(p));const r=base|(~~(Math.random()*((~mask)>>>0)-2)+1);ri.ips.push(n2ip(r))}else ri.ips.push(`${~~(Math.random()*223)+1}.${~~(Math.random()*255)}.${~~(Math.random()*255)}.${~~(Math.random()*254)+1}`)}}

const ts=reactive({input:'',result:''})
function onTsConvert(){const v=ts.input.trim();if(/^\d{10,13}$/.test(v)){const t=parseInt(v)*1000;ts.result=new Date(t).toLocaleString('zh-CN')}else{try{ts.result=String(Math.floor(new Date(v).getTime()/1000))}catch{ts.result='格式错误'}}}

const b64=reactive({input:'',output:''})
function onB64(m:'encode'|'decode'){try{b64.output=m==='encode'?btoa(b64.input):atob(b64.input)}catch{b64.output='(格式错误)'}}

const js=reactive({input:'',output:''})
function onJson(){try{js.output=JSON.stringify(JSON.parse(js.input),null,2)}catch{js.output='(JSON格式错误)'}}
</script>

<style scoped>
.tools-page{padding:24px;max-width:1200px;margin:0 auto}
.tools-header{margin-bottom:24px;display:flex;align-items:center}
.tool-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}
.tool-card{background:#fff;border:1px solid #e8ecf1;border-radius:12px;padding:18px;cursor:pointer;transition:all .2s;display:flex;flex-direction:column;gap:6px}
.tool-card:hover{border-color:#409eff;box-shadow:0 4px 12px rgba(64,158,255,.15);transform:translateY(-2px)}
.tool-icon{font-size:30px}.tool-name{font-size:14px;font-weight:600;color:#303133}.tool-desc{font-size:11px;color:#909399;line-height:1.5}
/* parameter blocks */
.param-bar{display:flex;align-items:center;flex-wrap:wrap;gap:6px;margin-bottom:16px}
.param-block{background:#fafbfc;border:1px solid #ebeef5;border-radius:10px;padding:16px;margin-bottom:16px}
.param-main{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.param-label{font-size:13px;font-weight:600;color:#606266;white-space:nowrap}
.slider-wrap{flex:1;min-width:180px;display:flex;align-items:center;gap:12px}
.main-slider{flex:1}
.adv-grid{display:flex;gap:24px;flex-wrap:wrap;padding:8px 0}.adv-item{display:flex;align-items:center;gap:8px;font-size:13px;color:#606266}
.param-summary{font-size:12px;color:#909399;margin-bottom:10px;padding:8px 12px;background:#f5f7fa;border-radius:6px}
/* inputs */
.inp-s{width:80px!important}.inp-m{width:160px!important}.inp-l{width:220px!important}.inp-f{width:420px!important}
.nip{width:80px}.sep{font-size:18px;font-weight:700;margin:0 2px}
/* results */
.result-box{margin-top:8px}
.cidr-bar{display:flex;height:36px;border-radius:8px;overflow:hidden;font-size:12px;line-height:36px;text-align:center;color:#fff;font-weight:600}
.bar-seg.network{background:linear-gradient(135deg,#409eff,#337ecc);flex:0 0 60px}.bar-seg.hosts{background:linear-gradient(135deg,#67c23a,#529b2e);flex-grow:1}.bar-seg.broadcast{background:linear-gradient(135deg,#e6a23c,#cf9236);flex:0 0 60px}
/* stats */
.stat-box{background:#f5f7fa;border:1px solid #ebeef5;border-radius:10px;padding:10px 16px;text-align:center;min-width:80px}
.stat-box .lbl{font-size:11px;color:#909399;margin-bottom:2px}.stat-box .val{font-size:20px;font-weight:700}
.ping-stats{display:flex;gap:10px;flex-wrap:wrap}
/* ping table */
.ping-table{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
.ping-row{background:#f0fdf4;border-radius:6px;padding:4px 12px;font-size:12px;font-family:monospace;display:flex;gap:8px;align-items:center}
.ping-row.to{background:#fef0f0}.pr-seq{color:#909399}.pr-val{font-weight:600}
/* traceroute */
.trace-timeline{position:relative}
.trace-hop{display:flex;align-items:flex-start;gap:14px;padding:10px 0}
.trace-hop+.trace-hop{border-top:1px dashed #e8ecf1}
.hop-num{width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#409eff,#337ecc);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;flex-shrink:0}
.hop-num.timeout{background:linear-gradient(135deg,#f56c6c,#d94545)}
.hop-body{flex:1;padding-top:6px}
.hop-main{display:flex;align-items:center;gap:12px}.hop-ip{font-weight:600;font-size:15px;font-family:monospace}.hop-avg{font-size:18px;font-weight:700;color:#67c23a}.hop-detail{font-size:11px;color:#909399;margin-top:4px;font-family:monospace}
</style>
