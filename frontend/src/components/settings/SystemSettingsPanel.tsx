import { useEffect, useState } from 'react'
import { Button, Card, Switch, Typography, message } from 'antd'

import { requestJson } from '../../lib/api'
import type { SystemConfig } from '../../types/chat'

type SystemSettingsPanelProps = {
  open: boolean
}

export function SystemSettingsPanel({ open }: SystemSettingsPanelProps) {
  const [config, setConfig] = useState<SystemConfig>({ public_statistics: false })
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return

    let active = true

    async function loadSystemConfig() {
      setLoading(true)
      try {
        const data = await requestJson<{ ok: boolean } & SystemConfig>('/api/config/system')
        if (!active) return
        setConfig({
          public_statistics: Boolean(data.public_statistics),
        })
      } catch (error) {
        if (!active) return
        message.error(error instanceof Error ? error.message : '系统设置加载失败')
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    void loadSystemConfig()

    return () => {
      active = false
    }
  }, [open])

  async function handleSave() {
    setSaving(true)
    try {
      const data = await requestJson<{ ok: boolean } & SystemConfig>('/api/config/system', {
        method: 'POST',
        body: JSON.stringify(config),
      })
      setConfig({
        public_statistics: Boolean(data.public_statistics),
      })
      message.success('系统设置已保存')
    } catch (error) {
      message.error(error instanceof Error ? error.message : '系统设置保存失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="system-settings-panel">
      <Card className="system-settings-card" loading={loading}>
        <div className="system-settings-row">
          <div className="system-settings-copy">
            <Typography.Title level={5} className="system-settings-title">
              公开统计
            </Typography.Title>
            <Typography.Paragraph className="system-settings-desc">
              开启后，未登录用户也可以访问独立统计页和统计接口。
            </Typography.Paragraph>
          </div>
          <Switch
            checked={config.public_statistics}
            checkedChildren="公开"
            unCheckedChildren="关闭"
            onChange={(checked) => setConfig((current) => ({ ...current, public_statistics: checked }))}
          />
        </div>
        <div className="system-settings-actions">
          <Button type="primary" loading={saving} onClick={() => void handleSave()}>
            保存设置
          </Button>
        </div>
      </Card>
    </div>
  )
}
