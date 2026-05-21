import { useEffect } from 'react'

import { appMessage } from '../../lib/antdApp'
import { requestJson } from '../../lib/api'
import type { MessageItem } from '../../types/chat'

type UseConversationMessagesParams = {
  authenticated: boolean
  loadedConversationIds: Set<string>
  selectedConversationId: string
  setLoadedConversationIds: React.Dispatch<React.SetStateAction<Set<string>>>
  setMessagesByConversation: React.Dispatch<React.SetStateAction<Record<string, MessageItem[]>>>
  setMessagesLoading: React.Dispatch<React.SetStateAction<boolean>>
}

export function useConversationMessages({
  authenticated,
  loadedConversationIds,
  selectedConversationId,
  setLoadedConversationIds,
  setMessagesByConversation,
  setMessagesLoading,
}: UseConversationMessagesParams) {
  useEffect(() => {
    if (!authenticated || !selectedConversationId) {
      setMessagesLoading(false)
      return
    }
    if (loadedConversationIds.has(selectedConversationId)) {
      setMessagesLoading(false)
      return
    }

    let active = true
    setMessagesLoading(true)

    async function loadMessages() {
      try {
        const response = await requestJson<{ ok: boolean; items: MessageItem[] }>(
          `/api/conversations/${selectedConversationId}/messages`,
        )
        if (!active) return
        setMessagesByConversation((current) => ({
          ...current,
          [selectedConversationId]: response.items,
        }))
        setLoadedConversationIds((current) => {
          const next = new Set(current)
          next.add(selectedConversationId)
          return next
        })
      } catch (error) {
        if (active) {
          appMessage.error(error instanceof Error ? error.message : '消息加载失败')
        }
      } finally {
        if (active) {
          setMessagesLoading(false)
        }
      }
    }

    void loadMessages()

    return () => {
      active = false
    }
  }, [
    authenticated,
    loadedConversationIds,
    selectedConversationId,
    setLoadedConversationIds,
    setMessagesByConversation,
    setMessagesLoading,
  ])
}
