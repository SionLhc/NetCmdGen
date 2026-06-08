<template>
  <div class="tools-page">
    <div class="tools-header">
      <el-input v-model="search" placeholder="搜索 38 个网络工具..." clearable size="large" style="max-width:420px">
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

    <el-dialog v-model="dialogVisible" :title="atool?.name" width="900px" top="3vh" @closed="onDialogClosed">
      <!-- ═══ 子网计算器 ═══ -->
      <template v-if="activeId==='subnet'">
        <div class="param-bar"><el-input v-model="s.ip" placeholder="192.168.1.10" class="inp-m" /> <span class="sep">/</span> <el-input v-model="s.mask" placeholder="24" class="inp-s" /><el-button type="primary" @click="onSubnet" :loading="loadSub" style="margin-left:12px">计算</el-button></div>
        <transition name="result-fade">
        <div v-if="subR" class="result-box">
          <div class="cidr-bar"><div class="bar-seg network">网络号</div><div class="bar-seg hosts">{{ subR.usable_hosts }} 个可用IP（{{ subR.first_usable }} → {{ subR.last_usable }}）</div><div class="bar-seg broadcast">广播</div></div>
          <el-descriptions :column="3" border size="small" style="margin-top:16px">
            <el-descriptions-item label="IP 地址"><b>{{ s.ip }}</b></el-descriptions-item>
            <el-descriptions-item label="掩码">{{ subR.subnet_mask }}</el-descriptions-item>
            <el-descriptions-item label="CIDR">/{{ subR.prefix_length }}</el-descriptions-item>
            <el-descriptions-item label="网络地址"><el-tag type="primary" size="small">{{ subR.network_address }}</el-tag></el-descriptions-item>
            <el-descriptions-item label="广播地址"><el-tag type="warning" size="small">{{ subR.broadcast_address }}</el-tag></el-descriptions-item>
            <el-descriptions-item label="可用主机"><b style="color:#67c23a">{{ subR.usable_hosts }}</b></el-descriptions-item>
            <el-descriptions-item label="可用范围" :span="2"><code>{{ subR.first_usable }} ~ {{ subR.last_usable }}</code></el-descriptions-item>
            <el-descriptions-item label="IP 类型">{{ subR.ip_type }}</el-descriptions-item>
          </el-descriptions>
        </div>
        </transition>
      </template>

      <!-- ═══ 端口扫描 ═══ -->
      <template v-if="activeId==='portscan'">
        <div class="param-block">
          <div class="param-main"><span class="param-label">目标</span><el-input v-model="ps.target" placeholder="192.168.1.1" class="inp-l" /><span class="param-label" style="margin-left:12px">端口</span><el-input v-model="ps.ports" placeholder="22,80,443,3389" class="inp-l" /></div>
          <div class="param-summary">扫描: <b>{{ ps.target }}</b> 端口 {{ ps.ports }} · 离散模式</div>
          <el-button v-if="!scanProgress" type="primary" @click="onScan" :loading="loadScan" size="large" style="width:100%">开始扫描</el-button>
          <el-button v-else type="warning" size="large" style="width:100%" disabled>
            <el-icon class="is-loading"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;animation:spin 1s linear infinite"><circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="32"/></svg></el-icon>
            扫描中... {{ scanDone }}/{{ scanTotal }}
          </el-button>
          <!-- 扫描进度条 -->
          <div v-if="scanProgress" style="margin-top:8px">
            <el-progress :percentage="scanTotal > 0 ? Math.round(scanDone / scanTotal * 100) : 0" :stroke-width="8" :color="'#409eff'" />
          </div>
        </div>
        <transition name="result-fade">
        <div v-if="scanR" class="result-box">
          <div class="ping-stats"><StatBox label="目标" :v="scanR.target"/><StatBox label="已扫描" :v="scanR.scanned||scanR.total" c="#409eff"/><StatBox label="开放" :v="scanR.open_count" :c="scanR.open_count>0?'#67c23a':'#909399'"/></div>
          <div v-if="scanR.all_closed" style="text-align:center;padding:24px;color:#67c23a;font-size:15px">🎉 所有端口均已关闭或过滤，目标较安全</div>
          <el-table v-else-if="scanR.open_ports?.length" :data="scanR.open_ports" border size="small" style="margin-top:12px">
            <el-table-column type="index" label="#" width="44"/><el-table-column prop="port" label="端口" width="80" sortable><template #default="{row}"><b>{{ row.port }}</b></template></el-table-column><el-table-column prop="service" label="服务" width="130"/><el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip/>
            <el-table-column label="风险" width="80" align="center"><template #default="{row}"><el-tag :type="row.risk==='high'?'danger':row.risk==='medium'?'warning':'success'" size="small">{{ row.risk==='high'?'高危':row.risk==='medium'?'中危':'低' }}</el-tag></template></el-table-column>
          </el-table>
        </div>
        </transition>
      </template>

      <!-- ═══ DNS ═══ -->
      <template v-if="activeId==='dns'">
        <div class="param-bar"><el-input v-model="d.domain" placeholder="baidu.com" class="inp-l"/><el-select v-model="d.type" style="width:100px;margin:0 8px"><el-option v-for="t in ['A','AAAA','MX','NS','TXT','CNAME']" :key="t" :label="t" :value="t"/></el-select><el-button type="primary" @click="onDns" :loading="loadDns">查询</el-button></div>
        <transition name="result-fade"><div v-if="dnsR" class="result-box"><div class="ping-stats" style="margin-bottom:12px"><StatBox label="域名" :v="d.domain"/><StatBox label="记录" :v="d.type" c="#409eff"/></div>
          <el-table :data="dnsR.results" border size="small"><el-table-column prop="resolver" label="DNS 服务器" width="130"/><el-table-column label="解析结果"><template #default="{row}"><template v-if="row.status==='ok'"><el-tag v-for="(a,i) in row.answers" :key="i" size="small" style="margin:2px">{{ a }}</el-tag></template><span v-else style="color:#f56c6c">{{ row.answers[0] }}</span></template></el-table-column><el-table-column label="状态" width="70"><template #default="{row}"><el-tag :type="row.status==='ok'?'success':'danger'" size="small">{{ row.status==='ok'?'✅':'❌' }}</el-tag></template></el-table-column></el-table>
        </div></transition>
      </template>

      <!-- ═══ 快速工具（VLSM/CIDR/通配符/MAC/IP/DHCP等）═══ -->
      <template v-if="activeId==='split'"><div class="param-bar">网络 <el-input v-model="sp.network" placeholder="192.168.1.0" class="inp-m"/> /<el-input-number v-model="sp.prefix" :min="0" :max="32" size="small" class="nip"/> → /<el-input-number v-model="sp.newPrefix" :min="1" :max="32" size="small" class="nip"/><el-button type="primary" @click="onSplit" :loading="loadSplit" style="margin-left:12px">划分</el-button></div><transition name="result-fade"><el-table v-if="splitR?.subnets?.length" :data="splitR.subnets" border size="small"><el-table-column type="index" label="#" width="50"/><el-table-column prop="subnet" label="子网" width="180"/><el-table-column label="可用范围"><template #default="{row}">{{ row.first_host }} ~ {{ row.last_host }}</template></el-table-column><el-table-column prop="hosts" label="主机数" width="100"/></el-table></transition></template>

      <template v-if="activeId==='cidr-merge'"><div class="param-bar"><el-input v-model="cm.input" placeholder="192.168.1.0/24, 192.168.2.0/24" type="textarea" :rows="3" class="inp-f"/><el-button type="primary" @click="onCidrMerge" :loading="loadMerge" style="margin-left:12px;vertical-align:top">汇总</el-button></div><transition name="result-fade"><div v-if="cm.result" class="result-box"><b>汇总结果：</b><el-tag v-for="r in cm.result" :key="r" size="default" style="margin:4px">{{ r }}</el-tag></div></transition></template>

      <template v-if="activeId==='cidr-diff'"><div class="param-bar"><span>列表A</span><el-input v-model="cd.a" placeholder="10.0.0.0/8" class="inp-m"/><span style="margin-left:16px">列表B</span><el-input v-model="cd.b" placeholder="10.0.0.0/16" class="inp-m"/><el-button type="primary" @click="onCidrDiff" style="margin-left:12px">对比</el-button></div><transition name="result-fade"><div v-if="cd.result" class="result-box"><p>新增: <el-tag v-for="r in cd.result.added" :key="r" type="success" size="small" style="margin:2px">{{ r }}</el-tag></p><p>移除: <el-tag v-for="r in cd.result.removed" :key="r" type="danger" size="small" style="margin:2px">{{ r }}</el-tag></p><p>不变: <el-tag v-for="r in cd.result.same" :key="r" size="small" style="margin:2px">{{ r }}</el-tag></p></div></transition></template>

      <template v-if="activeId==='wildcard'"><div class="result-box"><div class="param-bar">CIDR <span style="font-weight:700;font-size:18px;margin:0 8px">/</span><el-input-number v-model="wc.prefix" :min="0" :max="32" size="large" class="nip" style="width:100px"/></div><el-descriptions :column="2" border size="small"><el-descriptions-item label="子网掩码"><code style="font-size:15px;color:#409eff">{{ wcMask }}</code></el-descriptions-item><el-descriptions-item label="通配符掩码"><code style="font-size:15px;color:#e6a23c">{{ wcWildcard }}</code></el-descriptions-item></el-descriptions><div style="margin-top:16px;background:#1a1b2e;padding:12px;border-radius:6px"><code style="color:#86efac">rule 5 permit source 192.168.1.0 {{ wcWildcard }}</code></div></div></template>

      <template v-if="activeId==='mac'"><div class="param-bar"><el-input v-model="mac.addr" placeholder="E4-5F-01-02-03-04" class="inp-l" @keyup.enter="onMacLookup"/><el-button type="primary" @click="onMacLookup" style="margin-left:12px">查询</el-button></div><div v-if="mac.result" class="result-box"><el-descriptions border size="small"><el-descriptions-item label="MAC地址"><code>{{ mac.addr }}</code></el-descriptions-item><el-descriptions-item label="OUI前缀"><code>{{ macOui }}</code></el-descriptions-item><el-descriptions-item label="厂商"><b style="color:#409eff">{{ mac.result }}</b></el-descriptions-item></el-descriptions></div></template>

      <template v-if="activeId==='ip-fmt'"><div class="param-bar"><el-input v-model="ifm.ip" placeholder="192.168.1.1" class="inp-m" @keyup.enter="onIpFmt"/><el-button type="primary" @click="onIpFmt" style="margin-left:12px">转换</el-button></div><el-descriptions v-if="ifm.result" :column="1" border size="small" style="margin-top:12px"><el-descriptions-item label="十进制">{{ ifm.result.decimal }}</el-descriptions-item><el-descriptions-item label="二进制"><code>{{ ifm.result.binary }}</code></el-descriptions-item><el-descriptions-item label="十六进制"><code>{{ ifm.result.hex }}</code></el-descriptions-item><el-descriptions-item label="八进制"><code>{{ ifm.result.octal }}</code></el-descriptions-item></el-descriptions></template>

      <template v-if="activeId==='dhcp43'"><div class="param-bar"><el-select v-model="dhcp.vendor" style="width:110px"><el-option label="Cisco" value="cisco"/><el-option label="Aruba" value="aruba"/><el-option label="UniFi" value="unifi"/><el-option label="Ruckus" value="ruckus"/></el-select><el-input v-model="dhcp.acIp" placeholder="AC管理IP" class="inp-m" style="margin:0 8px"/><el-button type="primary" @click="onDhcp43">生成</el-button></div><div v-if="dhcp.result" class="result-box"><el-descriptions border size="small"><el-descriptions-item label="厂商">{{ dhcp.vendor.toUpperCase() }}</el-descriptions-item><el-descriptions-item label="AC地址">{{ dhcp.acIp }}</el-descriptions-item><el-descriptions-item label="Option 43值"><code style="color:#67c23a;word-break:break-all">{{ dhcp.result }}</code></el-descriptions-item></el-descriptions></div></template>

      <template v-if="activeId==='port-lookup'"><el-input v-model="pl.port" placeholder="端口号" class="inp-m" type="number" style="margin-bottom:12px"/><div v-if="pl.result" class="result-box" style="margin-bottom:12px"><b style="font-size:16px">{{ pl.port }}</b> — <el-tag size="large">{{ pl.result }}</el-tag></div><el-divider>常用端口速查</el-divider><div style="display:flex;flex-wrap:wrap;gap:4px"><el-tag v-for="pt in cPorts" :key="pt.p" size="small" style="cursor:pointer" @click="pl.port=String(pt.p);onPortLookup()">{{ pt.p }}:{{ pt.n }}</el-tag></div></template>

      <template v-if="activeId==='randip'"><div class="param-bar"><el-select v-model="ri.mode" style="width:120px"><el-option label="完全随机" value="random"/><el-option label="10.x私网" value="private10"/><el-option label="192.168.x" value="private192"/><el-option label="CIDR内" value="cidr"/></el-select><el-input v-if="ri.mode==='cidr'" v-model="ri.cidr" placeholder="10.0.0.0/16" class="inp-m" style="margin-left:8px"/><span style="margin:0 8px">×</span><el-input-number v-model="ri.count" :min="1" :max="50" size="small" class="nip"/><el-button type="primary" @click="onRandIp" style="margin-left:12px">生成</el-button></div><div v-if="ri.ips?.length" style="display:flex;flex-wrap:wrap;gap:4px;margin-top:12px"><el-tag v-for="ip in ri.ips" :key="ip">{{ ip }}</el-tag></div></template>

      <template v-if="activeId==='timestamp'"><div class="param-bar"><el-input v-model="ts.input" placeholder="时间戳(秒) 或 2026-06-03" class="inp-l" @keyup.enter="onTsConvert"/><el-button type="primary" @click="onTsConvert" style="margin-left:12px">转换</el-button></div><el-descriptions v-if="ts.result" border size="small" style="margin-top:12px"><el-descriptions-item label="输入"><code>{{ ts.input }}</code></el-descriptions-item><el-descriptions-item label="结果">{{ ts.result }}</el-descriptions-item></el-descriptions></template>

      <template v-if="activeId==='base64'"><el-input v-model="b64.input" placeholder="输入文本" type="textarea" :rows="4"/><div style="display:flex;gap:8px;margin-top:12px"><el-button @click="onB64('encode')">编码 (Base64)</el-button><el-button @click="onB64('decode')">解码 (Base64)</el-button></div><div v-if="b64.output" style="background:#f5f7fa;padding:16px;border-radius:8px;margin-top:12px;font-family:monospace;font-size:13px;word-break:break-all;max-height:200px;overflow:auto">{{ b64.output }}</div></template>

      <template v-if="activeId==='json'"><el-input v-model="js.input" placeholder='{"name":"test"}' type="textarea" :rows="5"/><el-button type="primary" @click="onJson" style="margin-top:12px">格式化</el-button><pre v-if="js.output" style="background:#1a1b2e;color:#c9d1d9;padding:16px;border-radius:8px;margin-top:12px;max-height:400px;overflow:auto;font-size:13px;line-height:1.6">{{ js.output }}</pre></template>

      <template v-if="activeId==='poe-budget'">
        <div class="param-block"><h4 style="margin-bottom:10px">交换机 PoE 参数</h4>
          <el-row :gutter="12"><el-col :span="8"><span class="param-label">PoE 总功率 (W)</span><el-input-number v-model="poe.totalPower" :min="10" :max="3000" size="default" style="width:100%"/></el-col>
          <el-col :span="8"><span class="param-label">端口数</span><el-input-number v-model="poe.portCount" :min="1" :max="96" size="default" style="width:100%"/></el-col>
          <el-col :span="8"><span class="param-label">系统预留 (W)</span><el-input-number v-model="poe.reserve" :min="0" :max="500" size="default" style="width:100%"/></el-col></el-row>
          <h4 style="margin:16px 0 10px">设备参数</h4>
          <el-row :gutter="12"><el-col :span="8"><span class="param-label">单设备功率 (W)</span><el-input-number v-model="poe.devPower" :min="1" :max="100" :step="0.5" size="default" style="width:100%"/></el-col>
          <el-col :span="8"><span class="param-label">安全系数</span><el-slider v-model="poe.safety" :min="0.7" :max="1.0" :step="0.05" :format-tooltip="(v:number)=>(v*100).toFixed(0)+'%'" style="width:100%"/></el-col>
          <el-col :span="8"><el-button type="primary" @click="poeCalc=true" size="default" style="width:100%;margin-top:18px">计算</el-button></el-col></el-row>
        </div>
        <transition name="result-fade">
        <div v-if="poeCalc" class="result-box">
          <div class="ping-stats">
            <div class="stat-box"><div class="lbl">可用功率</div><div class="val" style="color:#6366f1">{{ poeAvailable }}W</div></div>
            <div class="stat-box"><div class="lbl">最大带机</div><div class="val" style="color:#10b981">{{ poeMaxDevices }} 台</div></div>
            <div class="stat-box"><div class="lbl">端口利用率</div><div class="val" :style="{color:poeUtilization>80?'#f56c6c':'#6366f1'}">{{ poeUtilization }}%</div></div>
          </div>
          <div style="margin-top:12px;padding:12px;background:#f8fafc;border-radius:8px;font-size:13px;color:#64748b">
            <p>计算公式：可用 = {{ poe.totalPower }}W - {{ poe.reserve }}W(预留) = {{ poeAvailable }}W</p>
            <p>单设备实际功耗 = {{ poe.devPower }}W × {{ (poe.safety*100).toFixed(0) }}%(安全系数) = {{ (poe.devPower*poe.safety).toFixed(1) }}W</p>
            <p>最大带机量 = ⌊{{ poeAvailable }}W ÷ {{ (poe.devPower*poe.safety).toFixed(1) }}W⌋ = <b style="color:#10b981">{{ poeMaxDevices }} 台</b></p>
          </div>
          <el-tag v-if="poeMaxDevices > poe.portCount" type="warning" style="margin-top:8px">⚠ 最大带机超出端口数 {{ poe.portCount }}，实际最多接 {{ poe.portCount }} 台</el-tag>
        </div></transition></template>

      <template v-if="activeId==='wifi-channel'">
        <div class="param-block"><h4 style="margin-bottom:10px">WiFi 信道规划参数</h4>
          <el-row :gutter="12"><el-col :span="8"><span class="param-label">频段</span><el-select v-model="wifiBand" size="default" style="width:100%"><el-option label="2.4 GHz" value="2.4"/><el-option label="5 GHz" value="5"/></el-select></el-col>
          <el-col :span="8"><span class="param-label">AP 数量</span><el-input-number v-model="wifiApCount" :min="1" :max="16" size="default" style="width:100%"/></el-col>
          <el-col :span="8"><span class="param-label">信道宽度</span><el-select v-model="wifiWidth" size="default" style="width:100%"><el-option label="20 MHz" value="20"/><el-option v-if="wifiBand==='5'" label="40 MHz" value="40"/><el-option v-if="wifiBand==='5'" label="80 MHz" value="80"/></el-select></el-col></el-row></div>
        <transition name="result-fade"><div class="result-box">
          <div class="ping-stats" style="margin-bottom:10px"><div class="stat-box"><div class="lbl">频段</div><div class="val" style="color:#6366f1">{{ wifiBand }}GHz</div></div><div class="stat-box"><div class="lbl">AP 数量</div><div class="val" style="color:#10b981">{{ wifiApCount }}</div></div></div>
          <el-table :data="wifiChannels" border size="small"><el-table-column type="index" label="AP #" width="55"/>
          <el-table-column prop="channel" label="信道" width="80"><template #default="{row}"><el-tag :type="row.overlap?'warning':'success'" size="small">{{ row.channel }}</el-tag></template></el-table-column>
          <el-table-column prop="freq" label="频率" width="100"/>
          <el-table-column prop="note" label="说明" min-width="140"/>
          </el-table>
          <div v-if="wifiBand==='2.4'" style="margin-top:10px;padding:10px;background:#fef3c7;border-radius:6px;font-size:12px;color:#d97706">
            💡 2.4GHz 仅 1/6/11 三个互不干扰信道。{{ wifiApCount > 3 ? '超过 3 个 AP 会产生同频干扰，建议换 5GHz。' : '' }}
          </div>
        </div></transition></template>

      <!-- EUI-64 计算器 -->
      <template v-if="activeId==='eui64'"><div class="param-block"><h4>MAC → IPv6 EUI-64</h4><div style="display:flex;gap:12px;align-items:center">
        <el-input v-model="euiMac" placeholder="AA:BB:CC:DD:EE:FF" class="inp-l" @keyup.enter="onEui64"/><el-button type="primary" @click="onEui64">计算</el-button></div></div>
        <transition name="result-fade"><div v-if="eui64Result" class="result-box"><el-descriptions border size="small"><el-descriptions-item label="MAC">{{ euiMac }}</el-descriptions-item><el-descriptions-item label="EUI-64 标识"><code style="color:#6366f1;font-size:14px">{{ eui64Result }}</code></el-descriptions-item></el-descriptions></div></transition></template>

      <!-- IPv6 压缩/展开 -->
      <template v-if="activeId==='ipv6-compress'"><div class="param-block"><h4>IPv6 地址处理</h4><el-input v-model="ipv6Addr" placeholder="2001:0db8:0000:0000:0000:ff00:0042:8329" class="inp-f" style="margin-bottom:10px"/><el-row :gutter="8"><el-col :span="8"><el-button @click="onIpv6Compress" style="width:100%">压缩 (::)</el-button></el-col><el-col :span="8"><el-button @click="onIpv6Expand" style="width:100%">展开（完整）</el-button></el-col><el-col :span="8"><el-button @click="onIpv6Check" style="width:100%">类型检测</el-button></el-col></el-row></div>
        <transition name="result-fade"><div v-if="ipv6Result" class="result-box"><el-tag v-for="(r,i) in ipv6Result" :key="i" size="default" style="margin:3px" :type="i===0?'':'info'">{{ r }}</el-tag></div></transition></template>

      <!-- 带宽需求计算 -->
      <template v-if="activeId==='bandwidth'"><div class="param-block"><h4 style="margin-bottom:8px">应用分布</h4>
        <el-row :gutter="10"><el-col :span="6"><span class="param-label">总用户</span><el-input-number v-model="bwUsers" :min="1" :max="100000" size="small" style="width:100%"/></el-col>
        <el-col :span="6"><span class="param-label">并发率</span><el-slider v-model="bwConcur" :min="10" :max="100" :format-tooltip="(v:number)=>v+'%'" style="width:100%"/></el-col>
        <el-col :span="6"><span class="param-label">冗余系数</span><el-slider v-model="bwRedundancy" :min="1.1" :max="2" :step="0.1" :format-tooltip="(v:number)=>v.toFixed(1)+'x'" style="width:100%"/></el-col></el-row>
        <div style="margin-top:10px"><el-checkbox v-model="bwApps.web">网页/邮件 2Mbps</el-checkbox><el-checkbox v-model="bwApps.video">视频 8Mbps</el-checkbox><el-checkbox v-model="bwApps.voip">VoIP 0.5Mbps</el-checkbox><el-checkbox v-model="bwApps.conference">视频会议 4Mbps</el-checkbox></div></div>
        <transition name="result-fade"><div v-if="bwResult" class="result-box"><div class="ping-stats">
          <div class="stat-box"><div class="lbl">并发用户</div><div class="val" style="color:#6366f1">{{ Math.round(bwUsers*bwConcur/100) }}</div></div>
          <div class="stat-box"><div class="lbl">基础带宽</div><div class="val" style="color:#10b981">{{ bwResult.base }}M</div></div>
          <div class="stat-box"><div class="lbl">建议带宽</div><div class="val" style="color:#f59e0b">{{ bwResult.recommended }}M</div></div></div></div></transition></template>

      <!-- 光纤功率预算 -->
      <template v-if="activeId==='fiber-budget'"><div class="param-block"><h4 style="margin-bottom:8px">光纤参数</h4>
        <el-row :gutter="10"><el-col :span="6"><span class="param-label">发射功率(dBm)</span><el-input-number v-model="fib.txPower" :min="-20" :max="10" :step="0.5" size="small" style="width:100%"/></el-col>
        <el-col :span="6"><span class="param-label">接收灵敏度(dBm)</span><el-input-number v-model="fib.rxSens" :min="-40" :max="0" :step="0.5" size="small" style="width:100%"/></el-col>
        <el-col :span="6"><span class="param-label">衰减(dB/km)</span><el-input-number v-model="fib.attenuation" :min="0.1" :max="5" :step="0.1" size="small" style="width:100%"/></el-col>
        <el-col :span="6"><span class="param-label">接头损耗(dB)</span><el-input-number v-model="fib.connector" :min="0" :max="10" :step="0.1" size="small" style="width:100%"/></el-col></el-row></div>
        <transition name="result-fade"><div v-if="fibCalc" class="result-box"><div class="ping-stats"><div class="stat-box"><div class="lbl">功率预算</div><div class="val" style="color:#6366f1">{{ fibBudget }}dB</div></div><div class="stat-box"><div class="lbl">最大距离</div><div class="val" style="color:#10b981">{{ fibMaxDist.toFixed(1) }}km</div></div></div></div></transition></template>

      <!-- 正则测试器 -->
      <template v-if="activeId==='regex'"><el-input v-model="regexPat" placeholder="正则表达式，如 (\d+\.\d+\.\d+\.\d+)" class="inp-f" style="margin-bottom:8px"/><el-input v-model="regexText" placeholder="测试文本" type="textarea" :rows="4" class="inp-f" style="margin-bottom:8px"/><el-row :gutter="8"><el-col :span="6"><el-select v-model="regexFlag" size="small"><el-option label="全局 (g)" value="g"/><el-option label="忽略大小写 (gi)" value="gi"/><el-option label="多行 (gm)" value="gm"/></el-select></el-col><el-col :span="6"><el-tag v-if="regexMatchCount>0" type="success">匹配 {{ regexMatchCount }} 处</el-tag><el-tag v-else-if="regexText" type="danger">无匹配</el-tag></el-col></el-row><div v-if="regexMatches.length" style="margin-top:8px;max-height:200px;overflow:auto"><el-tag v-for="(m,i) in regexMatches" :key="i" size="small" style="margin:2px" type="success">{{ m }}</el-tag></div></template>

      <!-- VLAN 端口配置批量生成 -->
      <template v-if="activeId==='vlan-range'"><div class="param-block"><h4 style="margin-bottom:8px">VLAN 批量配置</h4>
        <el-row :gutter="10"><el-col :span="5"><span class="param-label">起始VLAN</span><el-input-number v-model="vrStart" :min="1" :max="4094" size="small" style="width:100%"/></el-col>
        <el-col :span="5"><span class="param-label">结束VLAN</span><el-input-number v-model="vrEnd" :min="1" :max="4094" size="small" style="width:100%"/></el-col>
        <el-col :span="5"><span class="param-label">起始端口</span><el-input v-model="vrPort" placeholder="G0/0/1" size="small"/></el-col>
        <el-col :span="5"><span class="param-label">端口类型</span><el-select v-model="vrType" size="small"><el-option label="Access" value="access"/><el-option label="Trunk" value="trunk"/></el-select></el-col></el-row></div>
        <div class="result-box"><pre style="background:#1a1b2e;color:#86efac;padding:12px;border-radius:8px;font-size:12px;line-height:1.5;max-height:300px;overflow:auto">{{ vrOutput }}</pre></div></template>

      <!-- 哈希计算 -->
      <template v-if="activeId==='hash'"><el-input v-model="hashText" placeholder="输入要哈希的文本" type="textarea" :rows="3" style="margin-bottom:8px"/><el-row :gutter="8"><el-col :span="4" v-for="a in hashAlgos" :key="a"><el-button @click="onHash(a)" size="small" style="width:100%">{{ a }}</el-button></el-col></el-row><el-input v-if="hashResult" :model-value="hashResult" readonly style="margin-top:8px;font-family:monospace"/></template>

      <!-- 交换机选型参考 -->
      <template v-if="activeId==='switch-ref'"><el-table :data="switchRefs" border size="small"><el-table-column prop="model" label="型号" width="180"/><el-table-column prop="ports" label="端口" width="70"/><el-table-column prop="speed" label="速率" width="80"/><el-table-column prop="poe" label="PoE" width="80"/><el-table-column prop="forward" label="包转发率" width="100"/><el-table-column prop="layer" label="层级" width="70"/><el-table-column prop="descr" label="适用场景" min-width="160"/></el-table></template>

      <!-- 子网掩码速查表 -->
      <template v-if="activeId==='mask-table'"><el-table :data="maskTable" border size="small" max-height="360"><el-table-column prop="prefix" label="CIDR" width="65"/><el-table-column prop="mask" label="子网掩码" width="165"/><el-table-column prop="wildcard" label="通配符" width="165"/><el-table-column prop="hosts" label="可用主机" width="100"/><el-table-column prop="class" label="类别" width="70"/></el-table></template>

      <!-- DNS 记录生成 -->
      <template v-if="activeId==='dns-gen'"><el-select v-model="dnsType" style="width:120px;margin-right:8px"><el-option v-for="t in ['A','AAAA','CNAME','MX','TXT']" :key="t" :label="t" :value="t"/></el-select><el-input v-model="dnsName" placeholder="example.com" class="inp-m" style="margin-right:8px"/><el-input v-model="dnsValue" placeholder="93.184.216.34 / mail.example.com" class="inp-m"/><div style="margin-top:8px"><el-input :model-value="dnsRecord" readonly style="font-family:monospace;color:#6366f1"/></div></template>

      <!-- 默认密码速查 -->
      <template v-if="activeId==='default-pwd'"><el-table :data="defaultPwds" border size="small" max-height="360"><el-table-column prop="vendor" label="厂商/设备" width="150"/><el-table-column prop="user" label="用户名" width="110"/><el-table-column prop="pwd" label="密码" width="130"/><el-table-column prop="method" label="方式" width="80"/><el-table-column prop="note" label="备注" min-width="120"/></el-table></template>

      <!-- 网络术语速查 -->
      <template v-if="activeId==='net-terms'"><el-input v-model="termSearch" placeholder="搜索术语..." size="small" style="margin-bottom:8px"/><el-table :data="filteredTerms" border size="small" max-height="380"><el-table-column prop="abbr" label="缩写" width="100"/><el-table-column prop="full" label="全称" min-width="200"/><el-table-column prop="cn" label="中文" width="200"/></el-table></template>

      <!-- 配置检查清单 -->
      <template v-if="activeId==='config-check'"><div v-for="(item,i) in checkItems" :key="i" style="padding:6px 0;border-bottom:1px solid #f5f5f5;display:flex;align-items:center;gap:8px"><el-checkbox v-model="item.done"/><span :style="{textDecoration:item.done?'line-through':'none',color:item.done?'#94a3b8':'#334155',fontSize:'14px'}"><span :style="{color:item.severity==='high'?'#ef4444':item.severity==='med'?'#f59e0b':'#3b82f6',fontWeight:600,marginRight:'6px'}">{{item.severity==='high'?'🔴':item.severity==='med'?'🟡':'🔵'}}</span>{{item.label}}</span></div></template>

      <!-- SNMP MIB速查 -->
      <template v-if="activeId==='snmp-mib'"><el-table :data="snmpMibs" border size="small" max-height="360"><el-table-column prop="oid" label="OID" width="180"/><el-table-column prop="name" label="名称" width="160"/><el-table-column prop="desc" label="说明" min-width="140"/></el-table></template>

      <!-- 数据包结构 -->
      <template v-if="activeId==='packet-struct'"><el-select v-model="packetProto" size="small" style="width:140px;margin-bottom:8px"><el-option v-for="p in ['IP','TCP','UDP','ICMP']" :key="p" :label="p" :value="p"/></el-select><el-table :data="packetFields" border size="small" max-height="360"><el-table-column prop="offset" label="偏移" width="70"/><el-table-column prop="field" label="字段" width="160"/><el-table-column prop="bits" label="位宽" width="70"/><el-table-column prop="desc" label="说明" min-width="180"/></el-table></template>

      <!-- iPerf3 指引 -->
      <template v-if="activeId==='iperf-guide'"><el-table :data="iperfCmds" border size="small"><el-table-column prop="scenario" label="场景" width="140"/><el-table-column prop="cmd" label="命令" min-width="300"/><el-table-column prop="note" label="说明" width="160"/></el-table></template>

      <!-- 接口速率对照表 -->
      <template v-if="activeId==='speed-table'"><el-table :data="speedRefs" border size="small"><el-table-column prop="name" label="接口标准" width="130"/><el-table-column prop="speed" label="速率" width="90"/><el-table-column prop="encoding" label="编码" width="70"/><el-table-column prop="cable" label="线缆" width="120"/><el-table-column prop="distance" label="最大距离" width="90"/><el-table-column prop="year" label="发布年" width="70"/></el-table></template>

      <!-- Wake-on-LAN -->
      <template v-if="activeId==='wol'"><el-input v-model="wolMac" placeholder="AA:BB:CC:DD:EE:FF" class="inp-l" style="margin-bottom:8px"/><el-button type="primary" @click="onWol" size="default">发送 Magic Packet</el-button><div v-if="wolSent" style="margin-top:8px;color:#10b981;font-size:13px">✅ Magic Packet 已构造(WoL需UDP广播到255.255.255.255:9)</div></template>

      <!-- 网线线序 -->
      <template v-if="activeId==='cable-pinout'"><el-table :data="pinoutData" border size="small"><el-table-column prop="pin" label="针脚" width="60"/><el-table-column prop="a" label="568A" width="120"/><el-table-column prop="b" label="568B" width="120"/><el-table-column prop="use" label="用途" min-width="140"/></el-table></template>

      <!-- RIP参考 -->
      <template v-if="activeId==='rip-ref'"><el-table :data="ripRefs" border size="small"><el-table-column prop="vendor" label="厂商" width="80"/><el-table-column prop="cmd" label="命令" min-width="320"/><el-table-column prop="note" label="说明" width="140"/></el-table></template>

      <!-- Syslog解码 -->
      <template v-if="activeId==='syslog-decode'"><el-table :data="syslogLevels" border size="small"><el-table-column prop="level" label="级别" width="60"/><el-table-column prop="name" label="名称" width="120"/><el-table-column prop="desc" label="说明" min-width="140"/></el-table></template>

      <!-- WiFi 实时状态 -->
      <template v-if="activeId==='wifi-status'">
        <div style="text-align:center;margin-bottom:14px"><el-button type="primary" @click="getWifiStatus" :loading="wifiLoading">📡 获取实时状态</el-button></div>
        <el-descriptions v-if="wifiStatus" :column="2" border size="small">
          <el-descriptions-item label="状态"><el-tag :type="wifiStatus.connected?'success':'danger'">{{ wifiStatus.connected?'已连接':'未连接' }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="SSID">{{ wifiStatus.ssid||'--' }}</el-descriptions-item>
          <el-descriptions-item label="BSSID">{{ wifiStatus.bssid||'--' }}</el-descriptions-item>
          <el-descriptions-item label="信号强度"><el-progress :percentage="wifiStatus.signal||0" :color="(wifiStatus.signal||0)>60?'#67c23a':(wifiStatus.signal||0)>30?'#e6a23c':'#f56c6c'"/></el-descriptions-item>
          <el-descriptions-item label="信道">{{ wifiStatus.channel||'--' }}</el-descriptions-item>
          <el-descriptions-item label="无线类型">{{ wifiStatus.radio||'--' }}</el-descriptions-item>
          <el-descriptions-item label="接收速率">{{ wifiStatus.rx_rate||0 }} Mbps</el-descriptions-item>
          <el-descriptions-item label="发送速率">{{ wifiStatus.tx_rate||0 }} Mbps</el-descriptions-item>
          <el-descriptions-item label="认证方式">{{ wifiStatus.auth||'--' }}</el-descriptions-item>
          <el-descriptions-item label="加密">{{ wifiStatus.cipher||'--' }}</el-descriptions-item>
          <el-descriptions-item label="网卡">{{ wifiStatus.adapter?.name||'--' }}</el-descriptions-item>
          <el-descriptions-item label="制造商">{{ wifiStatus.adapter?.manufacturer||'--' }}</el-descriptions-item>
        </el-descriptions>
        <div v-else-if="!wifiLoading" style="text-align:center;color:#94a3b8;padding:30px">仅支持 Windows，点击按钮获取</div>
      </template>

      <!-- WiFi 信道扫描 -->
      <template v-if="activeId==='wifi-scan'">
        <div style="text-align:center;margin-bottom:14px"><el-button type="primary" @click="getWifiScan" :loading="wifiLoading">🔍 扫描周围 AP</el-button></div>
        <el-table v-if="wifiNetworks.length" :data="wifiNetworks" size="small" border max-height="400">
          <el-table-column prop="ssid" label="SSID" width="160"/>
          <el-table-column prop="bssid" label="BSSID" width="150"/>
          <el-table-column label="信号" width="120" align="center">
            <template #default="{row}"><el-progress :percentage="row.signal" :color="row.signal>60?'#67c23a':row.signal>30?'#e6a23c':'#f56c6c'" :stroke-width="14"/></template>
          </el-table-column>
          <el-table-column prop="channel" label="信道" width="60" align="center">
            <template #default="{row}"><el-tag :type="row.channel>14?'success':''" size="small">{{ row.channel }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="radio" label="类型" width="100"/>
          <el-table-column prop="rate" label="速率" width="90"/>
        </el-table>
        <div v-else-if="!wifiLoading" style="text-align:center;color:#94a3b8;padding:30px">仅支持 Windows，点击扫描</div>
      </template>

      <!-- WiFi 事件日志 -->
      <template v-if="activeId==='wifi-events'">
        <div style="display:flex;gap:8px;margin-bottom:14px;align-items:center">
          <span style="font-size:12px;color:#64748b">时间范围:</span>
          <el-input-number v-model="wifiMinutes" :min="1" :max="1440" size="small" style="width:100px"/>
          <span style="font-size:12px;color:#64748b">分钟</span>
          <el-button type="primary" size="small" @click="getWifiEvents" :loading="wifiLoading">查询</el-button>
        </div>
        <el-table v-if="wifiEventsList.length" :data="wifiEventsList" size="small" border max-height="400">
          <el-table-column prop="time" label="时间" width="160"/>
          <el-table-column prop="event_id" label="EventID" width="80" align="center">
            <template #default="{row}">
              <el-tag :type="row.event_id===10000?'success':row.event_id===10001||row.event_id===10003?'danger':'warning'" size="small">{{ row.event_id }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="级别" width="60" align="center">
            <template #default="{row}"><span :style="{color:row.level?.includes('Error')?'#f56c6c':row.level?.includes('Warning')?'#e6a23c':'#67c23a'}">{{ row.level||'--' }}</span></template>
          </el-table-column>
          <el-table-column prop="desc" label="描述" min-width="200"/>
        </el-table>
        <div v-else-if="!wifiLoading" style="text-align:center;color:#94a3b8;padding:30px">仅支持 Windows，选择时间范围查询</div>
      </template>

      <template #footer><el-button @click="dialogVisible=false">关闭</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { calcSubnet, splitSubnet, doPortScan, doDns } from '@/api'
import StatBox from '@/components/StatBox.vue'

const tools = [
  {id:'subnet',icon:'🔢',name:'子网计算器',desc:'IP+掩码→网络/广播/范围，CIDR可视化条',level:'p0',category:'子网'},
  {id:'portscan',icon:'🔍',name:'端口扫描',desc:'离散/范围+服务识别+风险评级',level:'p0',category:'诊断'},
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
  {id:'poe-budget',icon:'🔌',name:'PoE 功率预算',desc:'交换机总PoE÷设备功率=最大带机量',level:'p1',category:'规划'},
  {id:'wifi-channel',icon:'📶',name:'WiFi 信道规划',desc:'2.4G/5G 信道自动分配+干扰分析',level:'p1',category:'规划'},
  {id:'eui64',icon:'🌐',name:'EUI-64 计算器',desc:'MAC地址→IPv6接口标识（RFC4291）',level:'p1',category:'IPv6'},
  {id:'ipv6-compress',icon:'🔢',name:'IPv6 压缩/展开',desc:'::省略规则双向转换',level:'p1',category:'IPv6'},
  {id:'bandwidth',icon:'📊',name:'带宽需求计算',desc:'用户数×应用类型×并发率=建议带宽',level:'p1',category:'规划'},
  {id:'fiber-budget',icon:'🔦',name:'光纤功率预算',desc:'发射功率-衰减-接收灵敏度=最大距离',level:'p2',category:'规划'},
  {id:'regex',icon:'🔎',name:'正则测试器',desc:'实时高亮+捕获组(日志提取/配置解析)',level:'p2',category:'开发'},
  {id:'vlan-range',icon:'🏷',name:'VLAN 端口配置',desc:'输入VLAN范围→批量生成access/trunk端口配置',level:'p1',category:'配置'},
  {id:'hash',icon:'🔐',name:'哈希计算',desc:'MD5/SHA-1/SHA-256 文本校验',level:'p2',category:'工具'},
  {id:'switch-ref',icon:'📋',name:'交换机选型参考',desc:'主流型号端口/速率/PoE/包转发率对照',level:'p2',category:'参考'},
  {id:'mask-table',icon:'📐',name:'子网掩码速查表',desc:'/0~/32 掩码/通配符/主机数对照',level:'p2',category:'参考'},
  {id:'dns-gen',icon:'📝',name:'DNS 记录生成',desc:'A/AAAA/MX/CNAME/TXT 标准格式',level:'p2',category:'DNS'},
  {id:'default-pwd',icon:'🔑',name:'默认密码速查',desc:'常见网络设备出厂默认账号密码',level:'p2',category:'参考'},
  {id:'net-terms',icon:'📖',name:'网络术语速查',desc:'VLAN/OSPF/BGP/STP等50+术语中英对照',level:'p1',category:'参考'},
  {id:'config-check',icon:'✅',name:'配置检查清单',desc:'上线前安全自检:SSH/ACL/SNMP/NTP/密码强度',level:'p1',category:'运维'},
  {id:'snmp-mib',icon:'📊',name:'SNMP MIB 速查',desc:'常用OID:CPU/内存/端口流量/系统信息',level:'p2',category:'运维'},
  {id:'packet-struct',icon:'📦',name:'数据包结构',desc:'IP/TCP/UDP/ICMP头部交互式解析',level:'p2',category:'学习'},
  {id:'iperf-guide',icon:'📡',name:'iPerf3 测速指引',desc:'带宽/抖动/丢包测试命令+参数说明',level:'p2',category:'诊断'},
  {id:'speed-table',icon:'⚡',name:'接口速率对照表',desc:'FastEthernet/Gigabit/10GE/40GE/100GE速率+编码',level:'p2',category:'参考'},
  {id:'wol',icon:'💻',name:'Wake-on-LAN',desc:'局域网唤醒Magic Packet发送器',level:'p2',category:'工具'},
  {id:'cable-pinout',icon:'🔌',name:'网线线序参考',desc:'568A/568B/交叉线/反转线线序+用途',level:'p2',category:'参考'},
  {id:'rip-ref',icon:'🔄',name:'RIP 配置参考',desc:'RIPv1/v2 基础配置+认证+汇总(华为/Cisco)',level:'p2',category:'参考'},
  {id:'syslog-decode',icon:'📜',name:'Syslog 消息解码',desc:'日志级别/设施码→中文说明',level:'p2',category:'运维'},
  {id:'wifi-status',icon:'📡',name:'WiFi 实时状态',desc:'当前信号/信道/速率/网卡驱动',level:'p0',category:'无线'},
  {id:'wifi-scan',icon:'🔍',name:'WiFi 信道扫描',desc:'周围AP列表/信号强度/信道分布/干扰检测',level:'p1',category:'无线'},
  {id:'wifi-events',icon:'📋',name:'WiFi 事件日志',desc:'WLAN事件日志查询+断线原因解析',level:'p1',category:'无线'},
]
const search=ref(''), filterLevel=ref('all')
const filteredTools=computed(()=>tools.filter(t=>(!search.value||t.name.includes(search.value)||t.desc.includes(search.value))&&(filterLevel.value==='all'||t.level===filterLevel.value)))
const activeId=ref(''), dialogVisible=ref(false)
const atool=computed(()=>tools.find(t=>t.id===activeId.value))
function openTool(t:typeof tools[0]){ activeId.value=t.id; dialogVisible.value=true }
/** dialog 关闭时清理当前工具的状态，确保下次打开是干净的 */
function onDialogClosed() {
  loadSub.value = false; loadScan.value = false
  loadDns.value = false; loadSplit.value = false
  loadMerge.value = false
  scanProgress.value = false
  wifiLoading.value = false
}

// WiFi 工具
const wifiLoading = ref(false)
const wifiStatus = ref<any>(null)
const wifiNetworks = ref<any[]>([])
const wifiEventsList = ref<any[]>([])
const wifiMinutes = ref(30)

async function getWifiStatus() {
  wifiLoading.value = true; wifiStatus.value = null
  try { const r = await fetch('/api/tools/wifi/status'); wifiStatus.value = await r.json() } catch { }
  finally { wifiLoading.value = false }
}
async function getWifiScan() {
  wifiLoading.value = true; wifiNetworks.value = []
  try { const r = await fetch('/api/tools/wifi/networks'); wifiNetworks.value = await r.json() } catch { }
  finally { wifiLoading.value = false }
}
async function getWifiEvents() {
  wifiLoading.value = true; wifiEventsList.value = []
  try { const r = await fetch(`/api/tools/wifi/events?minutes=${wifiMinutes.value}`); wifiEventsList.value = await r.json() } catch { }
  finally { wifiLoading.value = false }
}

// Subnet
const s=ref({ip:'192.168.1.10',mask:'24'}), subR=ref<any>(null), loadSub=ref(false)
async function onSubnet(){loadSub.value=true;try{subR.value=await calcSubnet(s.value.ip,s.value.mask)}catch(e:any){ElMessage.error(e.response?.data?.detail)}finally{loadSub.value=false}}

// Port Scan
const ps=reactive({target:'192.168.1.1',ports:'22,80,443,3389'}), scanR=ref<any>(null), loadScan=ref(false)
const scanProgress=ref(false), scanDone=ref(0), scanTotal=ref(0)
async function onScan(){
  loadScan.value=true; scanR.value=null; scanProgress.value=true; scanDone.value=0
  // 解析端口列表获取总数
  const allPorts = ps.ports.split(',').filter(Boolean).map(p => {
    const r = p.trim().split('-');
    return r.length === 2 ? (parseInt(r[1]) - parseInt(r[0]) + 1) : 1;
  });
  scanTotal.value = allPorts.reduce((a: number, b: number) => a + b, 0)
  // 用定时器模拟进度（后端一次性返回，前端逐段推进）
  const progressTimer = setInterval(() => {
    if (scanDone.value < scanTotal.value) scanDone.value++
  }, scanTotal.value > 50 ? 20 : 40)
  try {
    scanR.value = await doPortScan(ps.target, ps.ports)
    scanDone.value = scanTotal.value // 完成
  } catch(e: any) {
    ElMessage.error(e.response?.data?.detail)
  } finally {
    clearInterval(progressTimer)
    scanDone.value = scanTotal.value
    setTimeout(() => { scanProgress.value = false }, 300)
    loadScan.value = false
  }
}

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
const cm=reactive({input:'',result:null as string[]|null}), loadMerge=ref(false)
function onCidrMerge(){
  loadMerge.value=true; cm.result=null
  // 用 nextTick 让 loading 效果先渲染
  setTimeout(() => {
    try {
      const c=cm.input.split(/[\s,;]+/).filter(Boolean)
      if(c.length<2){ElMessage.warning('至少2个CIDR');loadMerge.value=false;return}
      const r=c.map(x=>{const[a,p]=x.split('/');const n=ip2n(a),pre=parseInt(p);return{start:n,end:n+((1<<(32-pre))-1)}})
      r.sort((a,b)=>a.start-b.start)
      const m:string[]=[];let cur=r[0]
      for(let i=1;i<r.length;i++){if(r[i].start<=cur.end+1)cur.end=Math.max(cur.end,r[i].end);else{m.push(r2cidr(cur.start,cur.end));cur=r[i]}}
      m.push(r2cidr(cur.start,cur.end)); cm.result=m
      ElMessage.success(`汇总完成：${c.length} → ${m.length} 条`)
    } catch {
      ElMessage.error('格式错误，请输入有效的 CIDR（如 192.168.1.0/24）')
    } finally {
      loadMerge.value=false
    }
  }, 50)
}

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

// PoE 功率预算
const poe=reactive({totalPower:370,portCount:24,reserve:30,devPower:15.4,safety:0.8}), poeCalc=ref(false)
const poeAvailable=computed(()=>Math.max(0,poe.totalPower-poe.reserve))
const poeMaxDevices=computed(()=>Math.floor(poeAvailable.value/(poe.devPower*poe.safety)))
const poeUtilization=computed(()=>Math.min(100,Math.round(poeMaxDevices.value/poe.portCount*100)))

// WiFi 信道规划
const wifiBand=ref('2.4'), wifiApCount=ref(3), wifiWidth=ref('20')
const wifiChannels=computed(()=>{
  const ch24=[{channel:1,freq:'2412 MHz',overlap:false,note:'主信道'},
             {channel:6,freq:'2437 MHz',overlap:false,note:'无干扰'},
             {channel:11,freq:'2462 MHz',overlap:false,note:'无干扰'}]
  const ch5=[{channel:36,freq:'5180 MHz',overlap:false,note:'低频段'}]
  const ch5ext=[{channel:149,freq:'5745 MHz',overlap:false,note:'高频段'}]
  const extra5=[{channel:52,freq:'5260 MHz',overlap:wifiApCount.value>2,note:wifiApCount.value>2?'可能同频':'备选'}]
  if(wifiBand.value==='2.4') return ch24.slice(0,Math.min(wifiApCount.value,3))
  const result=ch5.slice()
  if(wifiApCount.value>1) result.push(...ch5ext)
  if(wifiApCount.value>2) result.push(...extra5)
  return result.slice(0,wifiApCount.value)
})

// EUI-64
const euiMac=ref('AA:BB:CC:DD:EE:FF'), eui64Result=ref('')
function onEui64(){
  const m=euiMac.value.replace(/[:-]/g,'').toLowerCase()
  if(m.length!==12){ElMessage.warning('请输入完整MAC地址');return}
  const b1=parseInt(m.slice(0,2),16); const flipped=(b1^0x02).toString(16).padStart(2,'0')
  eui64Result.value=`${flipped}${m.slice(2,6)}:${m.slice(6,8)}ff:fe${m.slice(8,12)}`
}

// IPv6工具
const ipv6Addr=ref(''), ipv6Result=ref<string[]>([])
function onIpv6Compress(){
  try{const g=ipv6Addr.value.trim().match(/[0-9a-fA-F:]+/)
  if(!g){ipv6Result.value=['无效IPv6地址'];return}
  // 展开后压缩
  const parts=g[0].replace(/::/g,':0'.repeat(9-g[0].split(':').length)).split(':')
  while(parts.length<8) parts.push('0')
  let compressed=parts.map(p=>parseInt(p||'0',16).toString(16)).join(':')
  // 找最长0段
  compressed=compressed.replace(/(:0){2,}/,':')
  compressed=compressed.replace(/:0:0:/g,'::').replace(/^0:/,'::').replace(/:0$/,'::')
  ipv6Result.value=[compressed||g[0]]
  }catch{ipv6Result.value=['格式错误']}
}
function onIpv6Expand(){
  const v=ipv6Addr.value.trim()
  try{
    let expanded=v
    if(v.includes('::')){
      const[p,s]=v.split('::'); const pc=(p?p.split(':'):[]).length; const sc=(s?s.split(':'):[]).length
      expanded=p+':'+'0:'.repeat(8-pc-sc)+(s?':'+s:'')
    }
    expanded=expanded.split(':').map(x=>x.padStart(4,'0')).join(':')
    ipv6Result.value=[expanded]
  }catch{ipv6Result.value=['格式错误']}
}
function onIpv6Check(){
  const v=ipv6Addr.value.trim()
  if(v.startsWith('fe80')) ipv6Result.value=['链路本地 (Link-Local)','fe80::/10']
  else if(v.startsWith('fc')||v.startsWith('fd')) ipv6Result.value=['唯一本地 (ULA)','fc00::/7']
  else if(v.startsWith('200')) ipv6Result.value=['全球单播 (Global Unicast)','2000::/3']
  else if(v.startsWith('ff')) ipv6Result.value=['多播 (Multicast)','ff00::/8']
  else if(v==='::1') ipv6Result.value=['回环 (Loopback)','::1/128']
  else if(v==='::') ipv6Result.value=['未指定 (Unspecified)','::']
  else ipv6Result.value=['其他类型','无法自动识别']
}

// 带宽需求
const bwUsers=ref(100), bwConcur=ref(60), bwRedundancy=ref(1.3)
const bwApps=reactive({web:true,video:true,voip:false,conference:false})
const bwResult=computed(()=>{
  const c=Math.round(bwUsers.value*bwConcur.value/100)
  let base=(bwApps.web?2:0)+(bwApps.video?8:0)+(bwApps.voip?0.5:0)+(bwApps.conference?4:0)
  return {base:Math.round(base*c),recommended:Math.round(base*c*bwRedundancy.value)}
})

// 光纤功率预算
const fib=reactive({txPower:0,rxSens:-24,attenuation:0.4,connector:1}), fibCalc=ref(true)
const fibBudget=computed(()=>fib.txPower-fib.rxSens)
const fibMaxDist=computed(()=>Math.max(0,(fibBudget.value-fib.connector)/fib.attenuation))

// 正则测试器
const regexPat=ref(''), regexText=ref(''), regexFlag=ref('g'), regexMatches=ref<string[]>([])
const regexMatchCount=computed(()=>{try{return regexMatches.value.length}catch{return 0}})
watch([regexPat,regexText,regexFlag],()=>{
  if(!regexPat.value||!regexText.value){regexMatches.value=[];return}
  try{const re=new RegExp(regexPat.value,regexFlag.value);const m=regexText.value.match(re);regexMatches.value=m?[...m]:[]}catch{regexMatches.value=[]}
})

// VLAN范围生成
const vrStart=ref(10), vrEnd=ref(20), vrPort=ref('GigabitEthernet0/0/'), vrType=ref('access')
const vrOutput=computed(()=>{
  const lines:string[]=[]; const start=Math.min(vrStart.value,vrEnd.value), end=Math.max(vrStart.value,vrEnd.value)
  for(let v=start, p=1;v<=end;v++,p++){
    lines.push(`vlan ${v}`); lines.push(` name VLAN${v}`)
    lines.push(`interface ${vrPort.value}${p}`)
    if(vrType.value==='trunk') lines.push(` port link-type trunk`); lines.push(` port ${vrType.value==='trunk'?'trunk allow-pass vlan':'default vlan'} ${v}`)
  }
  return lines.join('\n')
})

// 哈希计算
const hashText=ref(''), hashResult=ref('')
const hashAlgos=['MD5','SHA-1','SHA-256']
async function onHash(a:string){
  const e=new TextEncoder().encode(hashText.value)
  if(a==='MD5'){try{const h=Array.from(new Uint8Array(await crypto.subtle.digest('MD5',e)));hashResult.value=h.map(b=>b.toString(16).padStart(2,'0')).join('')}catch{hashResult.value='MD5不支持，请用SHA-256'};return}
  const algo=a==='SHA-1'?'SHA-1':'SHA-256'; const h=Array.from(new Uint8Array(await crypto.subtle.digest(algo,e))); hashResult.value=h.map(b=>b.toString(16).padStart(2,'0')).join('')
}

// 交换机选型参考
const switchRefs=[
  {model:'华为 S5735-L24P4X-A',ports:'28',speed:'千兆+万兆',poe:'370W',forward:'96Mpps',layer:'三层',descr:'中小企业接入/汇聚'},
  {model:'华为 S6730-H24X6C',ports:'30',speed:'万兆',poe:'无',forward:'720Mpps',layer:'三层',descr:'数据中心/核心'},
  {model:'H3C S5560X-30C-EI',ports:'28',speed:'千兆+万兆',poe:'选配',forward:'216Mpps',layer:'三层',descr:'园区汇聚'},
  {model:'H3C S5130S-28P-EI',ports:'28',speed:'千兆',poe:'选配',forward:'96Mpps',layer:'二层',descr:'接入层'},
  {model:'Cisco C9300-24P',ports:'24',speed:'千兆',poe:'715W',forward:'154Mpps',layer:'三层',descr:'企业接入/汇聚'},
  {model:'Cisco C9200L-24P-4G',ports:'28',speed:'千兆',poe:'370W',forward:'64Mpps',layer:'二层',descr:'中小企业接入'},
  {model:'TP-LINK TL-SG3428',ports:'28',speed:'千兆',poe:'250W',forward:'41Mpps',layer:'二层',descr:'小企业/SOHO'},
  {model:'Juniper EX3400-24P',ports:'24',speed:'千兆',poe:'720W',forward:'95Mpps',layer:'三层',descr:'企业接入/汇聚'},
]

// 子网掩码速查表
const maskTable=computed(()=>{
  const result=[]
  for(let p=0;p<=32;p++){
    const mask=((0xFFFFFFFF<<(32-p))>>>0); const a=(mask>>>24)&255, b=(mask>>>16)&255, c=(mask>>>8)&255, d=mask&255
    const wild=~mask>>>0; result.push({prefix:'/'+p, mask:`${a}.${b}.${c}.${d}`, wildcard:`${(wild>>>24)&255}.${(wild>>>16)&255}.${(wild>>>8)&255}.${wild&255}`, hosts:p===32?1:p===31?0:Math.pow(2,32-p)-2, class:p<=8?'A':p<=16?'B':p<=24?'C':'VLSM'})
  }
  return result
})

// DNS记录生成
const dnsType=ref('A'), dnsName=ref('example.com'), dnsValue=ref('93.184.216.34')
const dnsRecord=computed(()=>{
  if(dnsType.value==='MX') return `${dnsName.value}. IN MX 10 ${dnsValue.value}.`
  if(dnsType.value==='CNAME') return `${dnsName.value}. IN CNAME ${dnsValue.value}.`
  return `${dnsName.value}. IN ${dnsType.value} ${dnsValue.value}`
})

// 默认密码速查
const defaultPwds=[
  {vendor:'华为交换机/路由器',user:'admin',pwd:'admin@123 / Admin@123',method:'SSH/Web',note:'新版本需首次设置密码'},
  {vendor:'H3C 交换机',user:'admin',pwd:'admin / h3capadmin',method:'SSH/Web',note:'V5默认admin,V7无默认'},
  {vendor:'Cisco IOS',user:'cisco',pwd:'cisco',method:'Console',note:'新版首次启动需设置'},
  {vendor:'Juniper Junos',user:'root',pwd:'(空)',method:'Console',note:'首次无密码，需commit前设置'},
  {vendor:'RouterOS',user:'admin',pwd:'(空)',method:'WinBox/SSH',note:'首次无密码'},
  {vendor:'锐捷',user:'admin',pwd:'admin / ruijie',method:'SSH/Web',note:'不同版本差异'},
  {vendor:'TP-LINK 交换机',user:'admin',pwd:'admin',method:'Web',note:'部分型号Web管理页'},
  {vendor:'Ubiquiti UniFi',user:'ubnt',pwd:'ubnt',method:'SSH',note:'AP/交换机默认'},
  {vendor:'Aruba 交换机',user:'admin',pwd:'admin / (空)',method:'SSH/Web',note:'出厂默认'},
  {vendor:'Fortinet 防火墙',user:'admin',pwd:'(空)',method:'Web/SSH',note:'首次无密码'},
]

// 网络术语速查
const termSearch=ref('')
const allTerms=[
  {abbr:'VLAN',full:'Virtual Local Area Network',cn:'虚拟局域网'},
  {abbr:'OSPF',full:'Open Shortest Path First',cn:'开放最短路径优先'},
  {abbr:'BGP',full:'Border Gateway Protocol',cn:'边界网关协议'},
  {abbr:'STP',full:'Spanning Tree Protocol',cn:'生成树协议'},
  {abbr:'VRRP',full:'Virtual Router Redundancy Protocol',cn:'虚拟路由冗余协议'},
  {abbr:'ACL',full:'Access Control List',cn:'访问控制列表'},
  {abbr:'NAT',full:'Network Address Translation',cn:'网络地址转换'},
  {abbr:'DHCP',full:'Dynamic Host Configuration Protocol',cn:'动态主机配置协议'},
  {abbr:'SNMP',full:'Simple Network Management Protocol',cn:'简单网络管理协议'},
  {abbr:'LLDP',full:'Link Layer Discovery Protocol',cn:'链路层发现协议'},
  {abbr:'LACP',full:'Link Aggregation Control Protocol',cn:'链路聚合控制协议'},
  {abbr:'PoE',full:'Power over Ethernet',cn:'以太网供电'},
  {abbr:'MPLS',full:'Multi-Protocol Label Switching',cn:'多协议标签交换'},
  {abbr:'VPN',full:'Virtual Private Network',cn:'虚拟专用网络'},
  {abbr:'IPSec',full:'Internet Protocol Security',cn:'IP安全协议'},
  {abbr:'DNS',full:'Domain Name System',cn:'域名系统'},
  {abbr:'NTP',full:'Network Time Protocol',cn:'网络时间协议'},
  {abbr:'SSH',full:'Secure Shell',cn:'安全外壳协议'},
  {abbr:'AAA',full:'Authentication Authorization Accounting',cn:'认证授权审计'},
  {abbr:'BFD',full:'Bidirectional Forwarding Detection',cn:'双向转发检测'},
  {abbr:'EIGRP',full:'Enhanced Interior Gateway Routing Protocol',cn:'增强内部网关路由协议'},
  {abbr:'RIP',full:'Routing Information Protocol',cn:'路由信息协议'},
  {abbr:'VXLAN',full:'Virtual Extensible LAN',cn:'虚拟扩展局域网'},
  {abbr:'MTU',full:'Maximum Transmission Unit',cn:'最大传输单元'},
  {abbr:'TTL',full:'Time To Live',cn:'生存时间'},
]
const filteredTerms=computed(()=>allTerms.filter(t=>!termSearch.value||t.abbr.toLowerCase().includes(termSearch.value.toLowerCase())||t.cn.includes(termSearch.value)||t.full.toLowerCase().includes(termSearch.value.toLowerCase())))

// 配置检查清单
const checkItems=reactive([
  {label:'禁用 Telnet，仅使用 SSH v2 远程管理',severity:'high',done:false},
  {label:'修改默认密码（长度≥12，含大小写+数字+特殊字符）',severity:'high',done:false},
  {label:'SNMP Community 不使用 public/private 默认值',severity:'high',done:false},
  {label:'配置 ACL 限制管理访问来源 IP',severity:'high',done:false},
  {label:'配置 NTP 时间同步（至少2个源）',severity:'med',done:false},
  {label:'端口安全：Access口限制MAC数+违规shutdown',severity:'med',done:false},
  {label:'STP BPDU Guard/PortFast 边缘端口',severity:'med',done:false},
  {label:'配置 Syslog 日志服务器',severity:'med',done:false},
  {label:'DHCP Snooping 防伪造DHCP服务器',severity:'med',done:false},
  {label:'Trunk 口限定允许 VLAN 列表',severity:'med',done:false},
  {label:'接口配置 description 描述信息',severity:'low',done:false},
  {label:'配置 Banner/MOTD 登录警告',severity:'low',done:false},
  {label:'保存配置并备份到外部存储',severity:'med',done:false},
  {label:'验证关闭未使用的端口',severity:'low',done:false},
])

// SNMP MIB 速查
const snmpMibs=[
  {oid:'1.3.6.1.2.1.1.1.0',name:'sysDescr',desc:'系统描述'},
  {oid:'1.3.6.1.2.1.1.3.0',name:'sysUpTime',desc:'运行时间'},
  {oid:'1.3.6.1.2.1.1.5.0',name:'sysName',desc:'主机名'},
  {oid:'1.3.6.1.2.1.25.3.3.1.2',name:'hrProcessorLoad',desc:'CPU 负载（%）'},
  {oid:'1.3.6.1.4.1.2021.4.5.0',name:'memTotalReal',desc:'总内存 (KB)'},
  {oid:'1.3.6.1.4.1.2021.4.6.0',name:'memAvailReal',desc:'可用内存 (KB)'},
  {oid:'1.3.6.1.2.1.2.2.1.2',name:'ifDescr',desc:'接口名称'},
  {oid:'1.3.6.1.2.1.2.2.1.5',name:'ifSpeed',desc:'接口速率 (bps)'},
  {oid:'1.3.6.1.2.1.2.2.1.10',name:'ifInOctets',desc:'入字节数'},
  {oid:'1.3.6.1.2.1.2.2.1.16',name:'ifOutOctets',desc:'出字节数'},
  {oid:'1.3.6.1.2.1.2.2.1.8',name:'ifOperStatus',desc:'接口状态 (1=up,2=down)'},
  {oid:'1.3.6.1.2.1.4.20.1.2',name:'ipAdEntIfIndex',desc:'IP接口索引'},
  {oid:'1.3.6.1.2.1.4.20.1.1',name:'ipAdEntAddr',desc:'接口 IP 地址'},
]

// 数据包结构
const packetProto=ref('IP')
const ipFields=[{offset:'0','field':'Version(4)+IHL(4)','bits':'8','desc':'版本(IPv4=4) + 头部长度(5=20B)'},{offset:'1','field':'DSCP(6)+ECN(2)','bits':'8','desc':'服务类型/优先级'},{offset:'2','field':'Total Length','bits':'16','desc':'IP包总长度(含头部+数据)'},{offset:'4','field':'Identification','bits':'16','desc':'分片标识'},{offset:'6','field':'Flags(3)+Fragment Offset(13)','bits':'16','desc':'DF不分片/MF更多分片标志'},{offset:'8','field':'TTL','bits':'8','desc':'生存时间(每跳-1)'},{offset:'9','field':'Protocol','bits':'8','desc':'上层协议(6=TCP,17=UDP,1=ICMP)'},{offset:'10','field':'Checksum','bits':'16','desc':'头部校验和'},{offset:'12','field':'Source IP','bits':'32','desc':'源IP地址'},{offset:'16','field':'Destination IP','bits':'32','desc':'目标IP地址'}]
const tcpFields=[{offset:'0','field':'Source Port','bits':'16','desc':'源端口号'},{offset:'2','field':'Destination Port','bits':'16','desc':'目标端口号'},{offset:'4','field':'Sequence Number','bits':'32','desc':'序列号(三次握手)'},{offset:'8','field':'ACK Number','bits':'32','desc':'确认号'},{offset:'12','field':'Data Offset(4)+Flags(12)','bits':'16','desc':'头部长度+SYN/ACK/FIN/RST等'},{offset:'14','field':'Window Size','bits':'16','desc':'接收窗口大小'},{offset:'16','field':'Checksum','bits':'16','desc':'校验和'},{offset:'18','field':'Urgent Pointer','bits':'16','desc':'紧急指针'}]
const udpFields=[{offset:'0','field':'Source Port','bits':'16','desc':'源端口'},{offset:'2','field':'Dest Port','bits':'16','desc':'目标端口'},{offset:'4','field':'Length','bits':'16','desc':'UDP长度'},{offset:'6','field':'Checksum','bits':'16','desc':'校验和(可选)'}]
const icmpFields=[{offset:'0','field':'Type','bits':'8','desc':'类型(8=Request,0=Reply)'},{offset:'1','field':'Code','bits':'8','desc':'子类型码'},{offset:'2','field':'Checksum','bits':'16','desc':'校验和'},{offset:'4','field':'ID+Sequence','bits':'32','desc':'标识符+序列号'}]
const packetFields=computed(()=>{const m:Record<string,any[]>={IP:ipFields,TCP:tcpFields,UDP:udpFields,ICMP:icmpFields};return m[packetProto.value]||[]})

// iPerf3
const iperfCmds=[{scenario:'TCP带宽测试(服务端)',cmd:'iperf3 -s',note:'监听5201端口'},{scenario:'TCP带宽测试(客户端)',cmd:'iperf3 -c 192.168.1.1 -t 30 -P 4',note:'30秒/4并行流'},{scenario:'UDP带宽测试(服务端)',cmd:'iperf3 -s',note:'同TCP服务端'},{scenario:'UDP带宽测试(客户端)',cmd:'iperf3 -c 192.168.1.1 -u -b 100M -t 10',note:'限100M UDP'},{scenario:'反向测试(下载)',cmd:'iperf3 -c 192.168.1.1 -R',note:'测试下行带宽'},{scenario:'双向同时测试',cmd:'iperf3 -c 192.168.1.1 --bidir',note:'上下行同时测'},{scenario:'指定端口',cmd:'iperf3 -s -p 8080\niperf3 -c 192.168.1.1 -p 8080',note:'自定义端口'}]
const speedRefs=[{name:'FastEthernet',speed:'100Mbps',encoding:'4B/5B',cable:'Cat5 UTP',distance:'100m',year:'1995'},{name:'Gigabit',speed:'1Gbps',encoding:'8B/10B',cable:'Cat5e/Cat6',distance:'100m',year:'1999'},{name:'10 Gigabit',speed:'10Gbps',encoding:'64B/66B',cable:'Cat6a/光纤',distance:'100m/10km',year:'2002'},{name:'40 Gigabit',speed:'40Gbps',encoding:'64B/66B',cable:'QSFP+光纤',distance:'10km',year:'2010'},{name:'100 Gigabit',speed:'100Gbps',encoding:'64B/66B',cable:'QSFP28光纤',distance:'40km',year:'2010'}]
const wolMac=ref(''), wolSent=ref(false)
function onWol(){const m=wolMac.value.replace(/[:-]/g,'');if(m.length!==12){ElMessage.warning('MAC格式错误');return};wolSent.value=true;ElMessage.success('Magic Packet已构造(WoL需UDP广播到255.255.255.255:9)')}
const pinoutData=[{pin:'1',a:'白绿',b:'白橙',use:'TX+/RX+'},{pin:'2',a:'绿',b:'橙',use:'TX-/RX-'},{pin:'3',a:'白橙',b:'白绿',use:'RX+/TX+'},{pin:'4',a:'蓝',b:'蓝',use:'电话/POE'},{pin:'5',a:'白蓝',b:'白蓝',use:'电话/POE'},{pin:'6',a:'橙',b:'绿',use:'RX-/TX-'},{pin:'7',a:'白棕',b:'白棕',use:'POE'},{pin:'8',a:'棕',b:'棕',use:'POE'}]
const ripRefs=[{vendor:'华为',cmd:'rip 1\n version 2\n network 10.0.0.0',note:'RIPv2基础'},{vendor:'华为',cmd:'rip 1\n version 2\n undo summary\n network 10.0.0.0',note:'不自动汇总'},{vendor:'华为',cmd:'rip 1\n authentication-mode md5 cipher xxx',note:'MD5认证'},{vendor:'Cisco',cmd:'router rip\n version 2\n network 10.0.0.0\n no auto-summary',note:'RIPv2不汇总'}]
const syslogLevels=[{level:'0',name:'Emergency',desc:'系统不可用(紧急)'},{level:'1',name:'Alert',desc:'必须立即处理'},{level:'2',name:'Critical',desc:'严重错误'},{level:'3',name:'Error',desc:'一般错误'},{level:'4',name:'Warning',desc:'警告'},{level:'5',name:'Notice',desc:'正常但重要'},{level:'6',name:'Informational',desc:'一般信息'},{level:'7',name:'Debug',desc:'调试信息'}]
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
.ping-fade-enter-active{transition:all .3s ease}.ping-fade-enter-from{opacity:0;transform:translateY(8px)}
/* traceroute */
.trace-timeline{position:relative}
.trace-hop{display:flex;align-items:flex-start;gap:14px;padding:10px 0;transition:all .3s ease}
.trace-hop+.trace-hop{border-top:1px dashed #e8ecf1}
.trace-hop.hop-reached{background:rgba(16,185,129,0.04);border-radius:8px;padding:10px 8px;margin:0 -8px}
.trace-hop.hop-latest{border-left:3px solid #6366f1;padding-left:11px;background:rgba(99,102,241,0.03);border-radius:0 8px 8px 0}
.hop-num{width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#409eff,#337ecc);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;flex-shrink:0;transition:all .3s}
.hop-num.timeout{background:linear-gradient(135deg,#f56c6c,#d94545)}
.hop-num.reached{background:linear-gradient(135deg,#10b981,#059669);box-shadow:0 0 8px rgba(16,185,129,.3)}
.hop-body{flex:1;padding-top:6px}
.hop-main{display:flex;align-items:center;gap:12px}.hop-ip{font-weight:600;font-size:15px;font-family:monospace}.hop-avg{font-size:18px;font-weight:700;color:#67c23a}.hop-detail{font-size:11px;color:#909399;margin-top:4px;font-family:monospace}
/* ═══ 通用过渡动画 ═══ */
.result-fade-enter-active{transition:all .35s ease-out}
.result-fade-enter-from{opacity:0;transform:translateY(12px)}
.result-fade-leave-active{transition:all .2s ease-in}
.result-fade-leave-to{opacity:0;transform:translateY(-8px)}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
