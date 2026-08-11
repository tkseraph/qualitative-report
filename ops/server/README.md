# 价值涌现服务器恢复配置

本目录保存网站服务器的非敏感基础设施配置，用于服务器重建、配置审计和故障恢复。

不应加入本目录的内容：

- `/etc/letsencrypt/` 下的证书私钥和 ACME 账户凭据；
- SSH 私钥、`authorized_keys` 内容；
- 阿里云账号、AccessKey、Cookie 或控制台导出凭据；
- 任何报告生成流程使用的 API key。

## 配置对应关系

| 仓库文件 | 服务器路径 |
| --- | --- |
| `nginx-value-emergence.conf` | `/etc/nginx/sites-available/value-emergence` |
| `sshd-hardening.conf` | `/etc/ssh/sshd_config.d/99-value-emergence-hardening.conf` |
| `fail2ban-sshd.conf` | `/etc/fail2ban/jail.d/value-emergence-sshd.conf` |

Nginx 配置依赖 Certbot 在服务器上签发以下证书路径：

```text
/etc/letsencrypt/live/jiazhiyongxian.cn/fullchain.pem
/etc/letsencrypt/live/jiazhiyongxian.cn/privkey.pem
```

证书私钥不进入 Git；重建服务器时应使用 Certbot 重新签发。

## 防火墙基线

服务器仅开放以下入站端口：

- `22/tcp`：SSH，仅接受公钥认证；
- `80/tcp`：HTTP，域名访问跳转到 HTTPS；
- `443/tcp`：HTTPS。

SSH 不限制固定来源 IP，以兼容本地 VPN 和网络切换。安全性由公钥认证、关闭密码认证、Fail2ban 和较低的认证重试次数共同保证。

## 恢复后检查

恢复或替换配置后，应依次确认：

```bash
sshd -t
nginx -t
fail2ban-client -t
systemctl is-active ssh nginx fail2ban
ufw status verbose
certbot renew --dry-run
```

网站内容本身通过 `scripts/deploy_site.py` 的版本化发布目录恢复；不要直接修改 `/var/www/value-emergence/current` 中的文件。
