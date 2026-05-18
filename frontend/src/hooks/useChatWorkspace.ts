import { useEffect, useRef, useState } from 'react'
import { message } from 'antd'

import { requestJson } from '../lib/api'
import {
  buildInitialToolFormValues,
  getLastToolSchemas,
  normalizeToolFieldValue,
} from '../lib/chat-format'
import type {
  AutomationRuleCondition,
  AutomationRule,
  AuthSession,
  AuthUser,
  ComposerMode,
  Conversation,
  MessageItem,
  ResponsesPayload,
  ToolFieldValue,
  VisibleMessage,
} from '../types/chat'

const STORAGE_KEY = 'chatapi.conversationId'

export function useChatWorkspace(isMobile: boolean) {
  const [booting, setBooting] = useState(true)
  const [auth, setAuth] = useState<AuthSession>({
    authenticated: false,
    user: null,
  })
  const [loginLoading, setLoginLoading] = useState(false)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConversationId, setSelectedConversationId] = useState('')
  const [messages, setMessages] = useState<MessageItem[]>([])
  const [composer, setComposer] = useState('')
  const [composerMode, setComposerMode] = useState<ComposerMode>('assistant_message')
  const [toolName, setToolName] = useState('')
  const [toolCallId, setToolCallId] = useState('')
  const [toolFormValues, setToolFormValues] = useState<Record<string, ToolFieldValue>>({})
  const [draftBuffers, setDraftBuffers] = useState<Record<string, string>>({})
  const [sending, setSending] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [keyboardOffset, setKeyboardOffset] = useState(0)
  const [deletingConversationId, setDeletingConversationId] = useState('')
  const [pruneModalOpen, setPruneModalOpen] = useState(false)
  const [pruneKeepCount, setPruneKeepCount] = useState<number>(20)
  const [pruningConversations, setPruningConversations] = useState(false)
  const [abortingConversationId, setAbortingConversationId] = useState('')
  const [abortPopoverConversationId, setAbortPopoverConversationId] = useState('')
  const [abortReason, setAbortReason] = useState('')
  const [automationRulesModalOpen, setAutomationRulesModalOpen] = useState(false)
  const [automationRuleEditorOpen, setAutomationRuleEditorOpen] = useState(false)
  const [automationRules, setAutomationRules] = useState<AutomationRule[]>([])
  const [editingAutomationRule, setEditingAutomationRule] = useState<AutomationRule | null>(null)
  const [savingAutomationRules, setSavingAutomationRules] = useState(false)
  const chatScrollRef = useRef<HTMLDivElement | null>(null)
  const bottomRef = useRef<HTMLDivElement | null>(null)
  const shouldStickToBottomRef = useRef(true)
  const previousConversationIdRef = useRef('')

  const selectedConversation = conversations.find(
    (item) => item.id === selectedConversationId,
  )
  const hasLocalDraftBuffer =
    !!selectedConversationId &&
    Object.prototype.hasOwnProperty.call(draftBuffers, selectedConversationId)
  const draftBuffer = hasLocalDraftBuffer
    ? draftBuffers[selectedConversationId] ?? ''
    : selectedConversation?.metadata?.realtime_draft_text ?? ''
  const isWaitingForUser =
    selectedConversation?.metadata?.realtime_status === 'waiting'
  const availableToolSchemas = getLastToolSchemas(messages)
  const selectedToolSchema =
    availableToolSchemas.find((item) => item.name === toolName) ?? null
  const visibleMessages: VisibleMessage[] = [
    ...messages,
    ...(draftBuffer
      ? [
          {
            id: 'draft-buffer',
            role: 'draft',
            content: draftBuffer,
            created_at: new Date().toISOString(),
            draft: true,
          },
        ]
      : []),
  ]

  function setDraftBufferForConversation(conversationId: string, value: string) {
    if (!conversationId) return
    setDraftBuffers((prev) => {
      return {
        ...prev,
        [conversationId]: value,
      }
    })
  }

  useEffect(() => {
    let active = true

    async function bootstrapPage() {
      setBooting(true)
      try {
        const session = await requestJson<AuthSession>('/api/auth/session')
        if (!active) return
        setAuth(session)
        if (session.authenticated) {
          await loadAutomationRules()
          await loadConversations()
        }
      } catch (error) {
        if (active) {
          message.error(error instanceof Error ? error.message : '初始化失败')
        }
      } finally {
        if (active) {
          setBooting(false)
        }
      }
    }

    void bootstrapPage()

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    setDraftBuffers((prev) => {
      let changed = false
      const next = { ...prev }
      for (const conversation of conversations) {
        const draftText = conversation.metadata?.realtime_draft_text
        if (typeof draftText !== 'string') continue
        if (draftText) {
          if (next[conversation.id] !== draftText) {
            next[conversation.id] = draftText
            changed = true
          }
        } else if (next[conversation.id]) {
          delete next[conversation.id]
          changed = true
        }
      }
      return changed ? next : prev
    })
  }, [conversations])

  useEffect(() => {
    const conversationChanged =
      previousConversationIdRef.current !== selectedConversationId

    if (conversationChanged) {
      previousConversationIdRef.current = selectedConversationId
      shouldStickToBottomRef.current = true
    }

    if (!shouldStickToBottomRef.current) return

    const frame = window.requestAnimationFrame(() => {
      bottomRef.current?.scrollIntoView({
        behavior: conversationChanged ? 'auto' : 'smooth',
        block: 'end',
      })
    })

    return () => window.cancelAnimationFrame(frame)
  }, [selectedConversationId, messages, draftBuffer, sending])

  useEffect(() => {
    if (!auth.authenticated || !selectedConversationId) return
    void loadMessages(selectedConversationId)
  }, [auth.authenticated, selectedConversationId])

  useEffect(() => {
    if (composerMode !== 'tool_call') return
    if (toolName && selectedToolSchema) return
    if (availableToolSchemas[0]?.name) {
      setToolName(availableToolSchemas[0].name)
    }
  }, [availableToolSchemas, composerMode, selectedToolSchema, toolName])

  useEffect(() => {
    setToolFormValues(buildInitialToolFormValues(selectedToolSchema?.parameters))
  }, [selectedToolSchema?.name])

  useEffect(() => {
    if (!auth.authenticated) return
    const timer = window.setInterval(() => {
      void loadConversations()
      if (selectedConversationId) {
        void loadMessages(selectedConversationId)
      }
    }, 1500)
    return () => window.clearInterval(timer)
  }, [auth.authenticated, selectedConversationId])

  useEffect(() => {
    if (typeof window === 'undefined' || !window.visualViewport) {
      setKeyboardOffset(0)
      return
    }

    const viewport = window.visualViewport
    const updateKeyboardOffset = () => {
      const rawOffset = Math.max(
        0,
        window.innerHeight - viewport.height - viewport.offsetTop,
      )
      setKeyboardOffset(rawOffset > 80 ? Math.round(rawOffset) : 0)
    }

    updateKeyboardOffset()
    viewport.addEventListener('resize', updateKeyboardOffset)
    viewport.addEventListener('scroll', updateKeyboardOffset)

    return () => {
      viewport.removeEventListener('resize', updateKeyboardOffset)
      viewport.removeEventListener('scroll', updateKeyboardOffset)
    }
  }, [])

  async function loadConversations(nextSelectedId?: string) {
    const data = await requestJson<{ items: Conversation[] }>('/api/conversations')
    setConversations(data.items)
    const requested =
      nextSelectedId ??
      selectedConversationId ??
      localStorage.getItem(STORAGE_KEY) ??
      ''
    const preferred = data.items.some((item) => item.id === requested)
      ? requested
      : data.items[0]?.id ?? ''

    if (!preferred) {
      if (selectedConversationId) {
        setSelectedConversationId('')
      }
      setMessages([])
      localStorage.removeItem(STORAGE_KEY)
      return
    }

    if (preferred !== selectedConversationId) {
      setSelectedConversationId(preferred)
      localStorage.setItem(STORAGE_KEY, preferred)
    }
  }

  async function loadMessages(conversationId: string) {
    try {
      const data = await requestJson<{ items: MessageItem[] }>(
        `/api/conversations/${conversationId}/messages`,
      )
      setMessages(data.items)
    } catch (error) {
      if (error instanceof Error && error.message.includes('not found')) {
        setMessages([])
        return
      }
      message.error(error instanceof Error ? error.message : '加载消息失败')
    }
  }

  async function handleLogin(values: { username: string; password: string }) {
    setLoginLoading(true)
    try {
      await requestJson<{ ok: boolean; user: AuthUser }>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(values),
      })
      const session = await requestJson<AuthSession>('/api/auth/session')
      setAuth(session)
      await loadAutomationRules()
      await loadConversations()
      message.success('登录成功')
    } catch (error) {
      message.error(error instanceof Error ? error.message : '登录失败')
    } finally {
      setLoginLoading(false)
    }
  }

  async function handleLogout() {
    try {
      await requestJson('/api/auth/logout', { method: 'POST' })
    } finally {
      setAuth({ authenticated: false, user: null })
      setConversations([])
      setSelectedConversationId('')
      setMessages([])
      setComposer('')
      setComposerMode('assistant_message')
      setToolName('')
      setToolCallId('')
      setToolFormValues({})
      setDraftBuffers({})
      setAutomationRulesModalOpen(false)
      setAutomationRuleEditorOpen(false)
      setAutomationRules([])
      setEditingAutomationRule(null)
      localStorage.removeItem(STORAGE_KEY)
      message.info('已退出登录')
    }
  }

  async function loadAutomationRules() {
    const data = await requestJson<{ ok?: boolean; rules?: AutomationRule[] }>(
      '/api/config/automation-rules',
    )
    setAutomationRules(Array.isArray(data.rules) ? data.rules : [])
  }

  function buildEmptyAutomationRule(): AutomationRule {
    return {
      id: `rule_${Math.random().toString(36).slice(2, 10)}`,
      enabled: true,
      conditions: {
        contains: [],
        excludes: [],
      },
      timing: {
        delay_seconds: 0,
        repeat_interval_seconds: 0,
      },
      action: {
        type: 'output_text',
        text: '',
        error_message: '',
      },
    }
  }

  async function persistAutomationRules(nextRules: AutomationRule[], successText = '规则已保存') {
    setSavingAutomationRules(true)
    try {
      const response = await requestJson<{ ok: boolean; rules: AutomationRule[] }>(
        '/api/config/automation-rules',
        {
          method: 'POST',
          body: JSON.stringify({
            rules: nextRules,
          }),
        },
      )
      setAutomationRules(response.rules)
      message.success(successText)
    } catch (error) {
      message.error(error instanceof Error ? error.message : '规则保存失败')
      throw error
    } finally {
      setSavingAutomationRules(false)
    }
  }

  async function handleSaveAutomationRule(rule: AutomationRule) {
    const normalized: AutomationRule = {
      ...rule,
      conditions: {
        contains: normalizeRuleConditions(rule.conditions.contains),
        excludes: normalizeRuleConditions(rule.conditions.excludes),
      },
      timing: {
        delay_seconds: Number(rule.timing.delay_seconds) || 0,
        repeat_interval_seconds: Number(rule.timing.repeat_interval_seconds) || 0,
      },
      action: {
        ...rule.action,
        text: rule.action.text ?? '',
        error_message: rule.action.error_message ?? '',
      },
    }

    if (normalized.timing.delay_seconds < 0 || normalized.timing.repeat_interval_seconds < 0) {
      message.warning('时间配置必须大于等于 0')
      return
    }
    if (normalized.action.type === 'output_text' && !normalized.action.text.trim()) {
      message.warning('输出指定文本时必须填写文本')
      return
    }
    if (normalized.action.type === 'error' && !normalized.action.error_message.trim()) {
      message.warning('返回 error 时必须填写错误信息')
      return
    }

    const nextRules = automationRules.some((item) => item.id === normalized.id)
      ? automationRules.map((item) => (item.id === normalized.id ? normalized : item))
      : [...automationRules, normalized]
    await persistAutomationRules(nextRules)
    setAutomationRuleEditorOpen(false)
    setEditingAutomationRule(null)
  }

  function normalizeRuleConditions(items: AutomationRuleCondition[]): AutomationRuleCondition[] {
    return items
      .map((item) => ({
        match_type:
          item.match_type === 'regex'
            ? ('regex' as const)
            : ('substring' as const),
        pattern: item.pattern.trim(),
      }))
      .filter((item) => item.pattern)
  }

  async function handleDeleteAutomationRule(ruleId: string) {
    const nextRules = automationRules.filter((item) => item.id !== ruleId)
    await persistAutomationRules(nextRules, '规则已删除')
  }

  async function handleToggleAutomationRule(ruleId: string, enabled: boolean) {
    const nextRules = automationRules.map((item) =>
      item.id === ruleId ? { ...item, enabled } : item,
    )
    await persistAutomationRules(nextRules, enabled ? '规则已启用' : '规则已停用')
  }

  function handleCreateAutomationRule() {
    setEditingAutomationRule(buildEmptyAutomationRule())
    setAutomationRuleEditorOpen(true)
  }

  function handleEditAutomationRule(ruleId: string) {
    const rule = automationRules.find((item) => item.id === ruleId)
    if (!rule) return
    setEditingAutomationRule({
      ...rule,
      conditions: {
        contains: [...rule.conditions.contains],
        excludes: [...rule.conditions.excludes],
      },
      timing: { ...rule.timing },
      action: { ...rule.action },
    })
    setAutomationRuleEditorOpen(true)
  }

  async function handleSelectConversation(conversationId: string) {
    setSelectedConversationId(conversationId)
    localStorage.setItem(STORAGE_KEY, conversationId)
    await loadMessages(conversationId)
    if (isMobile) setDrawerOpen(false)
    setComposerMode('assistant_message')
    setToolName('')
    setToolCallId('')
    setToolFormValues({})
  }

  async function handleDeleteConversation(conversationId: string) {
    const targetConversation = conversations.find((item) => item.id === conversationId)
    if (targetConversation?.metadata?.realtime_status === 'waiting') {
      message.warning('等待中的会话不允许删除')
      return
    }

    setDeletingConversationId(conversationId)
    try {
      await requestJson(`/api/conversations/${conversationId}`, {
        method: 'DELETE',
      })

      const remaining = conversations.filter((item) => item.id !== conversationId)
      const nextConversationId =
        conversationId === selectedConversationId ? remaining[0]?.id ?? '' : selectedConversationId

      if (!nextConversationId) {
        setSelectedConversationId('')
        setMessages([])
        localStorage.removeItem(STORAGE_KEY)
      } else if (nextConversationId !== selectedConversationId) {
        setSelectedConversationId(nextConversationId)
        localStorage.setItem(STORAGE_KEY, nextConversationId)
        await loadMessages(nextConversationId)
      }

      await loadConversations(nextConversationId)
      message.success('会话已删除')
    } catch (error) {
      message.error(error instanceof Error ? error.message : '删除会话失败')
    } finally {
      setDeletingConversationId('')
    }
  }

  async function handlePruneConversations() {
    if (!Number.isInteger(pruneKeepCount) || pruneKeepCount < 0) {
      message.warning('请输入大于等于 0 的整数')
      return
    }

    setPruningConversations(true)
    try {
      const response = await requestJson<{
        deleted_count: number
        skipped_count: number
        keep_count: number
      }>('/api/conversations/prune', {
        method: 'POST',
        body: JSON.stringify({
          keep_count: pruneKeepCount,
        }),
      })

      setPruneModalOpen(false)
      await loadConversations(selectedConversationId)

      if (response.skipped_count > 0) {
        message.success(
          `已删除 ${response.deleted_count} 个会话，跳过 ${response.skipped_count} 个等待中的旧会话`,
        )
        return
      }
      message.success(`已删除 ${response.deleted_count} 个会话`)
    } catch (error) {
      message.error(error instanceof Error ? error.message : '批量删除会话失败')
    } finally {
      setPruningConversations(false)
    }
  }

  async function handleAbortConversation(conversationId: string) {
    const reason = abortReason.trim()
    if (!reason) {
      message.warning('请输入 abort 错误信息')
      return
    }

    setAbortingConversationId(conversationId)
    try {
      await requestJson(`/api/conversations/${conversationId}/abort`, {
        method: 'POST',
        body: JSON.stringify({ error: reason }),
      })
      setAbortPopoverConversationId('')
      setAbortReason('')
      await loadConversations(selectedConversationId)
      if (conversationId === selectedConversationId) {
        await loadMessages(conversationId)
      }
      message.success('已 abort 该请求')
    } catch (error) {
      message.error(error instanceof Error ? error.message : 'Abort 失败')
    } finally {
      setAbortingConversationId('')
    }
  }

  async function handleDraft() {
    if (!isWaitingForUser) return
    if (composerMode === 'tool_call') {
      await handleSend({ resetMode: true, successMessage: '已输出 Tool Call' })
      return
    }
    const chunk = composer.trim()
    if (!chunk) return
    try {
      const response = await requestJson<{
        draft_text?: string
        draft_length: number
      }>('/api/chat/output/delta', {
        method: 'POST',
        body: JSON.stringify({
          text: chunk,
          conversation_id: selectedConversationId || undefined,
        }),
      })
      setDraftBufferForConversation(
        selectedConversationId,
        typeof response.draft_text === 'string' ? response.draft_text : `${draftBuffer}${chunk}`,
      )
      setComposer('')
      message.success('已输出片段')
    } catch (error) {
      message.error(error instanceof Error ? error.message : '输出片段失败')
    }
  }

  function buildToolCallPayload(): string {
    if (!toolName.trim()) {
      throw new Error('请先选择一个 tool')
    }
    const properties = selectedToolSchema?.parameters?.properties ?? {}
    const required = new Set(selectedToolSchema?.parameters?.required ?? [])
    const payloadEntries = Object.entries(properties).flatMap(([key, schema]) => {
      const rawValue = toolFormValues[key]
      if (rawValue == null || rawValue === '') {
        if (required.has(key)) {
          throw new Error(`请填写必填参数: ${key}`)
        }
        return []
      }
      return [[key, normalizeToolFieldValue(rawValue, schema)] as const]
    })
    return JSON.stringify(Object.fromEntries(payloadEntries))
  }

  async function handleSend(options?: {
    resetMode?: boolean
    successMessage?: string
  }) {
    if (!isWaitingForUser) return
    let finalText = ''

    if (composerMode === 'assistant_message') {
      finalText = `${draftBuffer}${composer}`.trim()
    } else {
      try {
        finalText = buildToolCallPayload()
      } catch (error) {
        message.error(error instanceof Error ? error.message : '工具参数格式错误')
        return
      }
    }

    if (!finalText) return

    setSending(true)
    try {
      setDraftBufferForConversation(selectedConversationId, '')
      const payload = {
        text: finalText,
        mode: composerMode,
        tool_name: composerMode === 'tool_call' ? toolName.trim() || undefined : undefined,
        tool_call_id:
          composerMode === 'tool_call' ? toolCallId.trim() || undefined : undefined,
        conversation_id: selectedConversationId || undefined,
      }
      const response = await requestJson<ResponsesPayload>('/api/chat/output/complete', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      const nextConversationId = response.conversation?.id ?? selectedConversationId
      if (nextConversationId) {
        setSelectedConversationId(nextConversationId)
        localStorage.setItem(STORAGE_KEY, nextConversationId)
      }
      setComposer('')
      if (options?.resetMode !== false) {
        setComposerMode('assistant_message')
      }
      setToolName('')
      setToolCallId('')
      setToolFormValues({})
      await loadConversations(nextConversationId)
      if (nextConversationId) {
        await loadMessages(nextConversationId)
      }
      message.success(options?.successMessage || '已结束输出')
    } catch (error) {
      message.error(error instanceof Error ? error.message : '发送失败')
    } finally {
      setSending(false)
    }
  }

  function handleComposerKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== 'Enter' || event.shiftKey) return
    event.preventDefault()
    if (
      sending ||
      !isWaitingForUser ||
      composerMode !== 'assistant_message' ||
      !composer.trim()
    ) {
      return
    }
    void handleDraft()
  }

  function handleChatScroll(event: React.UIEvent<HTMLDivElement>) {
    const container = event.currentTarget
    const distanceToBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight
    shouldStickToBottomRef.current = distanceToBottom <= 80
  }

  return {
    abortPopoverConversationId,
    abortReason,
    abortingConversationId,
    auth,
    availableToolSchemas,
    booting,
    bottomRef,
    chatScrollRef,
    composer,
    composerMode,
    conversations,
    deletingConversationId,
    draftBuffer,
    drawerOpen,
    handleAbortConversation,
    handleChatScroll,
    handleComposerKeyDown,
    handleDeleteConversation,
    handleDraft,
    handleLogin,
    handleLogout,
    handlePruneConversations,
    handleSelectConversation,
    handleSend,
    isWaitingForUser,
    keyboardOffset,
    loginLoading,
    messages,
    pruneKeepCount,
    pruneModalOpen,
    pruningConversations,
    automationRuleEditorOpen,
    automationRules,
    automationRulesModalOpen,
    selectedConversation,
    selectedConversationId,
    selectedToolSchema,
    sending,
    setAbortPopoverConversationId,
    setAbortReason,
    setComposer,
    setComposerMode,
    setDrawerOpen,
    setEditingAutomationRule,
    setPruneKeepCount,
    setPruneModalOpen,
    setAutomationRuleEditorOpen,
    setAutomationRulesModalOpen,
    setToolCallId,
    setToolFormValues,
    setToolName,
    editingAutomationRule,
    savingAutomationRules,
    toolCallId,
    toolFormValues,
    toolName,
    visibleMessages,
    handleCreateAutomationRule,
    handleDeleteAutomationRule,
    handleEditAutomationRule,
    handleSaveAutomationRule,
    handleToggleAutomationRule,
  }
}
