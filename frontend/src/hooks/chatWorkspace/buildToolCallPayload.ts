import { normalizeToolFieldValue } from '../../lib/chat-format'
import type { JsonSchema, ToolFieldValue } from '../../types/chat'

type BuildToolCallPayloadParams = {
  selectedToolSchema: { parameters: JsonSchema } | null
  toolFormValues: Record<string, ToolFieldValue>
  toolName: string
}

export function buildToolCallPayload({
  selectedToolSchema,
  toolFormValues,
  toolName,
}: BuildToolCallPayloadParams): string {
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
