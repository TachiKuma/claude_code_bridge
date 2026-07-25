---
doc_type: audit-finding
audit: 2026-07-25-windows-rmux-native-backend
finding_id: "security-02"
nature: security
severity: P1
confidence: medium
suggested_action: cs-issue
status: open
---

# Finding 02：ccbd 客户端响应读取缺少最大字节上限

## 速答

`recv_response_line()` 会一直累积响应直到读到换行或连接关闭，没有最大字节限制；Windows TCP loopback 控制面同样复用该客户端路径，若 endpoint 被污染或本地服务异常发送无换行大响应，CLI 进程可能被内存耗尽。

## 关键证据

- `lib/ccbd/socket_client.py:29` — `CcbdClient.request()` 连接当前项目的控制面 socket/endpoint。
- `lib/ccbd/socket_client.py:34` — 客户端直接调用 `recv_response_line(sock)` 读取响应。
- `lib/ccbd/socket_client_runtime/transport.py:26` — `recv_response_line(sock)` 没有 size 参数或上限常量。
- `lib/ccbd/socket_client_runtime/transport.py:28` — 循环条件只检查 `b'\n' not in raw`。
- `lib/ccbd/socket_client_runtime/transport.py:32` — 每轮 `raw += chunk` 无界增长。
- `lib/ccbd/socket_server_runtime/protocol.py:9` — 服务端请求读取有 `_MAX_REQUEST_BYTES = 1024 * 1024`，说明该协议已有大小上限口径。
- `lib/ccbd/control_plane_transport/windows_tcp.py:40`、`lib/ccbd/control_plane_transport/windows_tcp.py:523` — Windows bootstrap 自检响应也有 `_MAX_RESPONSE_BYTES` 保护，但通用客户端读取没有复用这个上限。

## 影响

这是本地 IPC/loopback 的可用性安全问题。正常 ccbd 会返回单行 JSON，但一旦 endpoint descriptor 指向异常本地服务、旧进程损坏或测试/插件错误实现连接，调用 `doctor`、`ping`、`ask` 等命令的客户端可被无界响应拖垮。

## 修复方向

给 `recv_response_line()` 增加与 bootstrap 一致的最大响应字节限制，超过阈值立即抛出 `CcbdClientError` 或协议错误，并覆盖 Windows TCP 客户端测试。

## 建议动作

`cs-issue`，因为这是协议健壮性缺口，修复点小但影响所有 ccbd 客户端调用。
