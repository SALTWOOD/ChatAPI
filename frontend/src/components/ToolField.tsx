import { Input, Select, Switch } from 'antd'

import { getSchemaType } from '../lib/chat-format'
import type { JsonSchema, ToolFieldValue } from '../types/chat'

const { TextArea } = Input

export function ToolField({
  disabled,
  fieldName,
  onChange,
  required,
  schema,
  value,
}: {
  disabled: boolean
  fieldName: string
  onChange: (fieldName: string, value: ToolFieldValue | string) => void
  required: boolean
  schema: JsonSchema
  value: ToolFieldValue | undefined
}) {
  const type = getSchemaType(schema)
  const label = schema.title || fieldName
  const description = schema.description || ''

  if (schema.enum?.length) {
    return (
      <div key={fieldName} className="tool-form-item">
        <div className="tool-form-label-row">
          <span className="tool-form-label">
            {label}
            {required && <span className="tool-form-required">*</span>}
          </span>
          <span className="tool-form-type">enum</span>
        </div>
        {description ? <div className="tool-form-description">{description}</div> : null}
        <Select
          value={value}
          allowClear={!required}
          placeholder={`选择 ${label}`}
          options={schema.enum.map((option) => ({
            label: String(option),
            value: option,
          }))}
          onChange={(nextValue) => onChange(fieldName, nextValue as ToolFieldValue)}
          disabled={disabled}
        />
      </div>
    )
  }

  if (type === 'boolean') {
    return (
      <div key={fieldName} className="tool-form-item">
        <div className="tool-form-label-row">
          <span className="tool-form-label">
            {label}
            {required && <span className="tool-form-required">*</span>}
          </span>
          <span className="tool-form-type">boolean</span>
        </div>
        {description ? <div className="tool-form-description">{description}</div> : null}
        <Switch
          checked={Boolean(value)}
          onChange={(checked) => onChange(fieldName, checked)}
          disabled={disabled}
        />
      </div>
    )
  }

  const isComplex = type === 'array' || type === 'object'
  const placeholder = isComplex ? `请输入 ${label} 的 JSON` : description || `请输入 ${label}`

  return (
    <div key={fieldName} className="tool-form-item">
      <div className="tool-form-label-row">
        <span className="tool-form-label">
          {label}
          {required && <span className="tool-form-required">*</span>}
        </span>
        <span className="tool-form-type">{type || 'string'}</span>
      </div>
      {description ? <div className="tool-form-description">{description}</div> : null}
      {isComplex ? (
        <TextArea
          value={typeof value === 'string' ? value : ''}
          onChange={(event) => onChange(fieldName, event.target.value)}
          placeholder={placeholder}
          autoSize={{ minRows: 3, maxRows: 8 }}
          disabled={disabled}
        />
      ) : (
        <Input
          value={value == null ? '' : String(value)}
          type={type === 'number' || type === 'integer' ? 'number' : 'text'}
          onChange={(event) => onChange(fieldName, event.target.value)}
          placeholder={placeholder}
          disabled={disabled}
        />
      )}
    </div>
  )
}
