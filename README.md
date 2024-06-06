
# AliCloud IP Updater

## 项目简介

[AliCloudIPUpdater](https://github.com/yshtcn/alicloud-ip-updater)  是一个用于定期更新阿里云安全组白名单的工具。它可以从指定的URL获取当前IP地址，并将其添加到阿里云安全组中。程序还集成了Server酱API，用于在更新白名单和发生重大错误时发送通知。

## 功能

- 定期从指定URL获取当前IP地址。
- 更新阿里云安全组的白名单。
- 删除旧的白名单规则。
- 通过Server酱发送更新和错误通知。
- 支持自定义通知标题和内容。

## 环境要求

- Python 3.12
- 阿里云账号及其访问密钥（Access Key ID 和 Access Key Secret）
- Docker（可选）

## 配置文件

程序需要一个配置文件 `config.json`，您可以基于 `config.sample.json` 创建。以下是配置文件的示例：

```json
{
    "ACCESS_KEY_ID": "your_access_key_id",
    "ACCESS_KEY_SECRET": "your_access_key_secret",
    "REGION_ID": "your_region_id",
    "SECURITY_GROUP_ID": "your_security_group_id",
    "TAG": "your_tag",
    "GETIP_URLS": [
        "https://getip.ysht.me"
    ],
    "PORTS": [
        {"port": "53", "protocol": "udp"},
        {"port": "6053", "protocol": "tcp"},
        {"port": "1-65535", "protocol": "tcp"}
    ],
    "PRIORITY": 1,
    "IP_RECORD_FILE": "ip_records.json",
    "INTERVAL_SECONDS": 3600,
    "SERVER_CHAN_KEY": "your_server_chan_key",
    "SERVER_CHAN_TITLE": "阿里云安全组白名单更新通知",
    "SERVER_CHAN_MESSAGE": "monitor已更新白名单，IP:{IP}，端口: {ports}"
}
```

## 使用方法

### 在本地运行

1. 克隆项目：

    ```bash
    git clone https://github.com/yshtcn/alicloud-ip-updater.git
    cd alicloud-ip-updater
    ```

2. 安装依赖：

    ```bash
    pip install -r requirements.txt
    ```

3. 创建配置文件：

    基于 `config.sample.json` 创建 `config.json` 并填写您的配置信息。

4. 运行程序：

    ```bash
    python AliCloudIPUpdater.py
    ```

### 使用Docker

1. 构建Docker镜像：

    ```bash
    docker build -t yshtcn/alicloud_ip_updater .
    ```

2. 运行Docker容器：

    ```bash
    docker run -v /path/to/config:/app/config yshtcn/alicloud_ip_updater
    ```

    注意：请将 `/path/to/config` 替换为您本地存放 `config.json` 的路径。

### Docker Hub

本项目发布在 [Docker Hub](https://hub.docker.com/r/yshtcn/alicloud_ip_updater),您也可以直接从Docker Hub拉取本项目镜像：

```bash
docker pull yshtcn/alicloud_ip_updater
```

然后运行Docker容器：

```bash
docker run -v /path/to/config:/app/config yshtcn/alicloud_ip_updater
```

## 常见问题

### 配置文件不存在

如果程序提示配置文件不存在，请确保您已正确映射配置文件目录，并且配置文件名为 `config.json`。

### 通知发送失败

请检查您的Server酱Key是否正确配置，并且网络连接正常。

## 特别说明

本项目代码及其文档使用AI辅助编写实现创意，请您谨防相关风险。

## 许可证

本项目使用MIT许可证。详细信息请参见LICENSE文件。




