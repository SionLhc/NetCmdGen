/**
 * 多厂商网络命令的语法定义
 * 用于 Monaco Editor 自定义语言
 */

import type * as Monaco from 'monaco-editor'

// 关键字（命令前缀/动作词）
export const NETWORK_KEYWORDS = [
  // 通用模式切换
  'system-view', 'sys', 'configure', 'terminal', 'enable', 'exit', 'quit', 'end', 'return',
  // 接口
  'interface', 'int', 'undo', 'no', 'shutdown', 'description',
  // VLAN
  'vlan', 'batch', 'port', 'link-type', 'access', 'trunk', 'hybrid', 'pvid',
  'allow-pass', 'allowed', 'tagged', 'untagged', 'native',
  // IP/路由
  'ip', 'address', 'gateway', 'route', 'static', 'rip', 'ospf', 'bgp', 'isis',
  'network', 'area', 'router-id', 'redistribute', 'next-hop',
  // ACL/QoS
  'acl', 'permit', 'deny', 'rule', 'source', 'destination', 'any',
  'traffic-policy', 'traffic-classifier', 'traffic-behavior',
  // STP
  'stp', 'spanning-tree', 'mstp', 'rstp', 'priority', 'cost', 'edged-port',
  // 安全
  'aaa', 'authentication', 'authorization', 'accounting', 'local-user',
  'password', 'cipher', 'simple', 'service-type', 'level',
  'dhcp', 'snooping', 'arp', 'inspection',
  // 链路聚合
  'link-aggregation', 'mode', 'manual', 'lacp', 'static', 'dynamic',
  'eth-trunk', 'port-channel',
  // 系统
  'sysname', 'hostname', 'clock', 'timezone', 'ntp-service',
  'save', 'commit', 'display', 'show', 'reset',
  // 厂商特有
  'super', 'config-mode', 'write', 'memory',
]

// 类型词（参数类型）
export const NETWORK_TYPES = [
  'GigabitEthernet', 'TenGigE', 'Ethernet', 'XGigabitEthernet', 'FastEthernet',
  'Vlanif', 'LoopBack', 'Tunnel', 'NULL', 'Eth-Trunk',
  'inbound', 'outbound', 'enable', 'disable', 'on', 'off',
]

/**
 * 命令片段（Snippets）：用户输入关键字 → 自动补全完整模板
 */
export const COMMAND_SNIPPETS: Array<{
  label: string
  insertText: string
  detail: string
  documentation: string
}> = [
  {
    label: 'vlan-create',
    insertText: 'vlan ${1:10}\n description ${2:VLAN_NAME}\n quit',
    detail: '创建 VLAN',
    documentation: '创建一个 VLAN 并设置描述',
  },
  {
    label: 'vlan-batch',
    insertText: 'vlan batch ${1:10 20 30}',
    detail: '批量创建 VLAN',
    documentation: '一次性创建多个 VLAN',
  },
  {
    label: 'interface-trunk',
    insertText: 'interface ${1:GigabitEthernet0/0/1}\n port link-type trunk\n port trunk allow-pass vlan ${2:all}\n quit',
    detail: 'Trunk 接口配置',
    documentation: '配置接口为 Trunk 模式',
  },
  {
    label: 'interface-access',
    insertText: 'interface ${1:GigabitEthernet0/0/1}\n port link-type access\n port default vlan ${2:10}\n quit',
    detail: 'Access 接口配置',
    documentation: '配置接口为 Access 模式',
  },
  {
    label: 'interface-vlanif',
    insertText: 'interface Vlanif${1:10}\n ip address ${2:192.168.1.1} ${3:255.255.255.0}\n quit',
    detail: 'VLAN 三层接口',
    documentation: '为 VLAN 配置三层 IP',
  },
  {
    label: 'ospf',
    insertText: 'ospf ${1:1} router-id ${2:1.1.1.1}\n area ${3:0}\n  network ${4:192.168.1.0} ${5:0.0.0.255}\n  quit\n quit',
    detail: 'OSPF 路由配置',
    documentation: 'OSPF 进程 + Area + Network 完整配置',
  },
  {
    label: 'static-route',
    insertText: 'ip route-static ${1:0.0.0.0} ${2:0.0.0.0} ${3:192.168.1.254}',
    detail: '静态路由',
    documentation: '配置静态/默认路由',
  },
  {
    label: 'acl-permit',
    insertText: 'acl ${1:2000}\n rule 5 permit source ${2:192.168.1.0} ${3:0.0.0.255}\n quit',
    detail: 'ACL 允许规则',
    documentation: '配置 ACL 允许特定网段',
  },
  {
    label: 'acl-deny',
    insertText: 'acl ${1:3000}\n rule 5 deny ip source ${2:192.168.1.0} ${3:0.0.0.255} destination ${4:10.0.0.0} ${5:0.255.255.255}\n quit',
    detail: 'ACL 拒绝规则',
    documentation: '配置 ACL 拒绝特定流量',
  },
  {
    label: 'eth-trunk',
    insertText: 'interface Eth-Trunk${1:1}\n mode lacp-static\n quit\ninterface ${2:GigabitEthernet0/0/1}\n eth-trunk ${1:1}\n quit',
    detail: '链路聚合',
    documentation: 'LACP 链路聚合配置',
  },
  {
    label: 'stp-priority',
    insertText: 'stp priority ${1:0}',
    detail: 'STP 优先级',
    documentation: '设置生成树优先级（0-61440，4096 倍数）',
  },
  {
    label: 'sysname',
    insertText: 'sysname ${1:Switch-Core-01}',
    detail: '设置主机名',
    documentation: '配置设备主机名',
  },
  {
    label: 'aaa-user',
    insertText: 'aaa\n local-user ${1:admin} password cipher ${2:Admin@123}\n local-user ${1:admin} service-type telnet ssh\n local-user ${1:admin} privilege level ${3:15}\n quit',
    detail: 'AAA 用户',
    documentation: '配置本地用户账号',
  },
  {
    label: 'dhcp-snooping',
    insertText: 'dhcp enable\ndhcp snooping enable\nvlan ${1:10}\n dhcp snooping enable\n quit',
    detail: 'DHCP Snooping',
    documentation: '启用 DHCP 监听防御',
  },
]

/**
 * 注册自定义网络命令语言到 Monaco
 */
export function registerNetworkLanguage(monaco: typeof Monaco) {
  const langId = 'network-cli'

  // 已注册过则跳过
  if (monaco.languages.getLanguages().some(l => l.id === langId)) {
    return langId
  }

  monaco.languages.register({ id: langId })

  // 语法高亮规则
  monaco.languages.setMonarchTokensProvider(langId, {
    keywords: NETWORK_KEYWORDS,
    typeKeywords: NETWORK_TYPES,
    operators: ['='],
    tokenizer: {
      root: [
        // 注释
        [/[#!].*$/, 'comment'],
        // IP 地址
        [/\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?\b/, 'number.ip'],
        // 数字
        [/\b\d+\b/, 'number'],
        // 接口标识 (G0/0/1, GE1/0/24 等)
        [/\b[GgXxFfEe][a-zA-Z]*\d+\/\d+\/\d+\b/, 'type'],
        // 字符串
        [/"([^"\\]|\\.)*$/, 'string.invalid'],
        [/"/, { token: 'string.quote', bracket: '@open', next: '@string' }],
        // 标识符（关键字 / 类型）
        [/[a-zA-Z_][\w-]*/, {
          cases: {
            '@keywords': 'keyword',
            '@typeKeywords': 'type',
            '@default': 'identifier',
          },
        }],
      ],
      string: [
        [/[^\\"]+/, 'string'],
        [/"/, { token: 'string.quote', bracket: '@close', next: '@pop' }],
      ],
    },
  } as any)

  // 自动补全（命令片段）
  monaco.languages.registerCompletionItemProvider(langId, {
    provideCompletionItems: (model, position) => {
      const word = model.getWordUntilPosition(position)
      const range: Monaco.IRange = {
        startLineNumber: position.lineNumber,
        endLineNumber: position.lineNumber,
        startColumn: word.startColumn,
        endColumn: word.endColumn,
      }
      // 关键字补全
      const keywordSuggestions = NETWORK_KEYWORDS.map(kw => ({
        label: kw,
        kind: monaco.languages.CompletionItemKind.Keyword,
        insertText: kw,
        range,
      }))
      // 片段补全
      const snippetSuggestions = COMMAND_SNIPPETS.map(snip => ({
        label: snip.label,
        kind: monaco.languages.CompletionItemKind.Snippet,
        insertText: snip.insertText,
        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
        documentation: snip.documentation,
        detail: snip.detail,
        range,
      }))
      return { suggestions: [...snippetSuggestions, ...keywordSuggestions] }
    },
  })

  // 主题（暗色友好）
  monaco.editor.defineTheme('network-cli-theme', {
    base: 'vs',
    inherit: true,
    rules: [
      { token: 'keyword', foreground: '0066cc', fontStyle: 'bold' },
      { token: 'type', foreground: '267f99' },
      { token: 'number', foreground: '098658' },
      { token: 'number.ip', foreground: 'd73a49', fontStyle: 'bold' },
      { token: 'comment', foreground: '6a737d', fontStyle: 'italic' },
      { token: 'string', foreground: 'a31515' },
    ],
    colors: {
      'editor.background': '#fafafa',
    },
  })

  return langId
}

/**
 * 简单命令校验
 * 检查每行命令是否以已知关键字开头
 */
export function validateCommands(text: string): Array<{ line: number; message: string }> {
  const errors: Array<{ line: number; message: string }> = []
  const lines = text.split('\n')
  const validStarts = new Set([...NETWORK_KEYWORDS, ...NETWORK_TYPES])

  lines.forEach((line, idx) => {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('!')) return

    const firstWord = trimmed.split(/\s+/)[0].toLowerCase()
    // 只对明显不像命令的报警（包含中文/特殊字符开头等）
    if (/^[\u4e00-\u9fa5]/.test(firstWord)) {
      errors.push({ line: idx + 1, message: '命令不应以中文开头' })
    } else if (firstWord.length > 30) {
      errors.push({ line: idx + 1, message: '命令关键字过长，可能拼写错误' })
    } else if (!validStarts.has(firstWord) && !firstWord.startsWith('undo') && !firstWord.startsWith('no')) {
      // 仅作为提示，不强制报错
      // 这里不 push，避免误报
    }
  })

  return errors
}
