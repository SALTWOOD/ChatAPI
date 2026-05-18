import { Button, Card, Form, Input, Typography } from 'antd'

import { CosmicBackdrop } from './CosmicBackdrop'
import type { LoginFormValues } from '../types/chat'

type LoginScreenProps = {
  loading: boolean
  totpEnabled: boolean
  onSubmit: (values: LoginFormValues) => void | Promise<void>
}

export function LoginScreen({ loading, onSubmit, totpEnabled }: LoginScreenProps) {
  const [form] = Form.useForm<LoginFormValues>()

  return (
    <div className="login-screen">
      <CosmicBackdrop />
      <div className="login-glow login-glow-left" aria-hidden="true" />
      <div className="login-glow login-glow-right" aria-hidden="true" />
      <Card className="login-card">
        <div className="login-copy">
          <Typography.Title level={2} className="login-title">
            ChatAPI 登录
          </Typography.Title>
        </div>
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => void onSubmit(values)}
          autoComplete="off"
          className="login-form"
          initialValues={{ username: '', password: '', totp: '' }}
        >
          <Form.Item
            label="账号"
            name="username"
            rules={[{ required: true, message: '请输入账号' }]}
          >
            <Input placeholder="账号" size="large" />
          </Form.Item>
          <Form.Item
            label="密码"
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password placeholder="密码" size="large" />
          </Form.Item>
          {totpEnabled ? (
            <Form.Item
              label="验证码"
              name="totp"
              rules={[{ required: true, message: '请输入验证码' }]}
            >
              <Input
                placeholder="6 位 TOTP 验证码"
                size="large"
                inputMode="numeric"
                maxLength={6}
              />
            </Form.Item>
          ) : null}
          <Button type="primary" htmlType="submit" size="large" block loading={loading}>
            登录
          </Button>
        </Form>
      </Card>
    </div>
  )
}
