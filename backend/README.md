# Backend Tree

```text
backend/
├── .env.example                              # 后端环境变量示例，说明数据库、管理员、邮件和前端静态资源等配置项
├── __init__.py                               # 后端包入口，供 Python 以包方式导入
├── app.py                                    # Flask 应用装配入口，初始化依赖、注册路由、挂载静态站点
├── main.py                                   # 本地启动入口，通常负责运行 Flask 应用
├── pyproject.toml                            # 后端项目元数据与 Python 依赖声明
├── README.md                                 # 当前文档，描述后端代码目录及职责
├── uv.lock                                   # `uv` 锁文件，固定后端依赖版本
├── core/                                     # 核心基础设施，放配置、认证上下文、依赖容器
│   ├── __init__.py                           # 导出 core 子模块公共接口
│   ├── auth.py                               # 会话鉴权、API Key 鉴权、TOTP 相关基础能力
│   ├── config.py                             # 读取环境变量并构造全局 Settings
│   └── dependencies.py                       # 定义 AppDependencies 等依赖注入数据结构
├── repositories/                             # 数据访问层，封装 SQLite 上的持久化读写
│   ├── __init__.py                           # 导出仓储层公共类型和构造入口
│   ├── conversations.py                      # 会话仓储门面，组合 conversation_store 各 mixin
│   ├── system_config.py                      # 系统配置仓储，管理开关、限制项和会话密钥
│   ├── users.py                              # 用户、密码、TOTP、API Key 等账户数据读写
│   └── conversation_store/                   # 会话仓储的细分实现，按职责拆开 CRUD 与统计
│       ├── __init__.py                       # 导出 conversation_store 子模块公共接口
│       ├── conversation_crud.py              # 会话创建、更新、删除、标题维护等会话级操作
│       ├── message_crud.py                   # 消息读写、历史匹配、tool_call 定位等消息级操作
│       ├── models.py                         # 会话/消息数据模型及 JSON、时间等辅助函数
│       └── statistics.py                     # 会话消息统计与 usage 估算逻辑
├── routes/                                   # HTTP/WebSocket 路由层，只负责协议转换和权限边界
│   ├── __init__.py                           # 汇总导出所有路由注册函数
│   ├── admin.py                              # 管理员接口，包含用户管理、邮件测试等能力
│   ├── auth.py                               # 认证路由装配入口，拼装 auth_handlers 各子路由
│   ├── conversations.py                      # 会话列表、消息查询、删除、批量裁剪等接口
│   ├── realtime.py                           # WebSocket 实时同步入口，负责订阅和快照下发
│   ├── responses.py                          # OpenAI/Anthropic/Responses 协议入口及系统配置接口
│   ├── statistics.py                         # 统计查询接口，对外暴露 usage/报表类数据
│   ├── uploads.py                            # 图片资源访问与占用统计接口
│   ├── user_api_keys.py                      # 用户 API Key 管理接口
│   ├── user_config.py                        # 用户级配置接口，例如自动化规则相关设置
│   └── auth_handlers/                        # 认证路由细分实现，按注册/登录/密码/TOTP 解耦
│       ├── __init__.py                       # 导出认证子路由注册函数和共享依赖
│       ├── common.py                         # 认证共享工具，如验证码存储、GeeTest 校验、公共依赖
│       ├── password_routes.py                # 找回密码与密码重置相关接口
│       ├── register_routes.py                # 注册配置、发码、注册提交相关接口
│       ├── session_routes.py                 # 登录、登出、会话查询相关接口
│       └── totp_routes.py                    # TOTP 开启、确认、重置相关接口
└── services/                                 # 业务服务层，承接协议编排、流式输出和辅助能力
    ├── __init__.py                           # 导出服务层公共接口
    ├── automation_rules.py                   # 自动化规则引擎，处理心跳和自动输出策略
    ├── email.py                              # 邮件发送抽象，适配多邮件 provider
    ├── image_assets.py                       # 图片落盘、内容重写、容量限制与孤儿清理
    ├── ntfy.py                               # 新消息通知能力
    ├── output_controller.py                  # 手动输出控制，补全/增量输出写回会话
    ├── payload_anthropic.py                  # Anthropic 协议响应体构造
    ├── payload_chat_completions.py           # Chat Completions 协议响应体构造
    ├── payload_openai.py                     # OpenAI 通用响应与错误体构造、usage 估算
    ├── pending.py                            # PendingTurn 与请求中的挂起状态管理
    ├── rate_limit.py                         # 消息频率限制器
    ├── realtime.py                           # 实时订阅 broker，负责连接管理和事件分发
    ├── response_payloads.py                  # 不同输出模式下的响应片段/结构拼装
    ├── response_stream.py                    # 非特定协议的流式响应编排与中断处理
    ├── stream_anthropic.py                   # Anthropic 协议流式输出实现
    ├── stream_chat_completions.py            # Chat Completions 协议流式输出实现
    ├── stream_common.py                      # 各流式协议共享的输出辅助逻辑
    ├── stream_responses.py                   # Responses API 协议流式输出实现
    ├── turn_coordinator.py                   # 单轮请求总编排器，负责建会话、入库、挂起和收尾
    ├── turn_protocols.py                     # 请求协议解析、历史抽取、会话归属推断等通用协议逻辑
    └── turn_request_tools.py                 # tool schema/name 与响应消息元数据提取等小型辅助函数
```
