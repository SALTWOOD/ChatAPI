import { Button, Descriptions, Modal, Popconfirm, Space, Table, Tag, Typography } from 'antd'
import { DeleteOutlined, SafetyOutlined } from '@ant-design/icons'

import type { AdminUserHistoryMessage, User } from '../../../types/chat'

type UserHistoryModalProps = {
  open: boolean
  user: User | null
  historyMessages: AdminUserHistoryMessage[]
  historyLoading: boolean
  deletingId: string
  onClose: () => void
  onDelete: (userId: string) => void
  onResetPassword: (user: User) => void
}

const historyColumns = [
  {
    title: '时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 190,
    render: (value: string) => (value ? new Date(value).toLocaleString() : '-'),
  },
  {
    title: '会话',
    dataIndex: 'conversation_title',
    key: 'conversation_title',
    width: 180,
    render: (value: string, record: AdminUserHistoryMessage) => (
      <Space direction="vertical" size={0}>
        <Typography.Text>{value || '未命名会话'}</Typography.Text>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          {record.conversation_id}
        </Typography.Text>
      </Space>
    ),
  },
  {
    title: '角色',
    dataIndex: 'role',
    key: 'role',
    width: 90,
    render: (role: string) => {
      const color = role === 'assistant' ? 'blue' : role === 'user' ? 'green' : 'default'
      return <Tag color={color}>{role || '-'}</Tag>
    },
  },
  {
    title: '内容',
    dataIndex: 'content',
    key: 'content',
    render: (value: string) => (
      <Typography.Paragraph style={{ marginBottom: 0 }} ellipsis={{ rows: 2, expandable: true, symbol: '展开' }}>
        {value || '-'}
      </Typography.Paragraph>
    ),
  },
]

export function UserHistoryModal({
  open,
  user,
  historyMessages,
  historyLoading,
  deletingId,
  onClose,
  onDelete,
  onResetPassword,
}: UserHistoryModalProps) {
  return (
    <Modal
      title={`查看历史消息 - ${user?.username ?? ''}`}
      open={open}
      onCancel={onClose}
      footer={null}
      width={1060}
      destroyOnHidden
    >
      <div className="user-history-modal">
        <Descriptions bordered column={2} size="small" className="user-history-descriptions">
          <Descriptions.Item label="用户名">{user?.username ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="角色">{user?.role === 'admin' ? '管理员' : '普通用户'}</Descriptions.Item>
          <Descriptions.Item label="API Keys">{user?.api_key_count ?? 0}</Descriptions.Item>
          <Descriptions.Item label="当前连接数">{user?.current_connection_count ?? 0}</Descriptions.Item>
          <Descriptions.Item label="创建时间" span={2}>
            {user?.created_at ? new Date(user.created_at).toLocaleString() : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="历史登录" span={2}>
            {user?.last_login_at ? new Date(user.last_login_at).toLocaleString() : '未登录'}
          </Descriptions.Item>
        </Descriptions>

        <div className="user-history-actions">
          <Button icon={<SafetyOutlined />} onClick={() => user && onResetPassword(user)}>
            重置密码
          </Button>
          <Popconfirm
            title={`删除用户：${user?.username ?? ''}`}
            description="删除后该用户的所有会话、消息和 API Key 都会被清理，且无法恢复。"
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
            onConfirm={() => user && onDelete(user.id)}
          >
            <Button danger icon={<DeleteOutlined />} loading={user ? deletingId === user.id : false}>
              删除用户
            </Button>
          </Popconfirm>
        </div>

        <Table
          className="user-history-table"
          columns={historyColumns}
          dataSource={historyMessages}
          rowKey="id"
          loading={historyLoading}
          pagination={false}
          size="small"
          locale={{
            emptyText: historyLoading ? '加载中...' : '暂无历史消息',
          }}
        />
      </div>
    </Modal>
  )
}
