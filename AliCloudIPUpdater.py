import os
import json
import requests
import time
import shutil
import logging
from requests.exceptions import RequestException
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkecs.request.v20140526 import DescribeSecurityGroupAttributeRequest, AuthorizeSecurityGroupRequest, RevokeSecurityGroupRequest

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger()

# 从配置文件加载配置信息
def load_config(config_file, sample_config_file):
    if not os.path.exists(config_file):
        logger.error(f"配置文件 {config_file} 不存在。")
        logger.info(f"将从样例配置文件 {sample_config_file} 复制一份。")
        shutil.copy(sample_config_file, config_file)
        logger.info(f"请在 {config_file} 中配置您的设置。")
        raise FileNotFoundError(f"配置文件 {config_file} 不存在。")
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        logger.error(f"配置文件 {config_file} 未找到。")
        raise
    except json.JSONDecodeError:
        logger.error(f"配置文件 {config_file} 解析错误。")
        raise

# 获取IP地址
def get_ip_from_service(url, server_chan_key):
    try:
        response = requests.get(url)
        response.raise_for_status()
        ip = response.text.strip()
        return ip
    except RequestException as e:
        logger.error(f"无法从 {url} 获取IP地址: {e}")
        if server_chan_key and server_chan_key != "your_server_chan_key":
            send_critical_notification(server_chan_key, f"无法从 {url} 获取IP地址: {e}")
        raise

# 获取当前安全组的规则
def get_security_group_rules(client, security_group_id, server_chan_key):
    try:
        request = DescribeSecurityGroupAttributeRequest.DescribeSecurityGroupAttributeRequest()
        request.set_SecurityGroupId(security_group_id)
        request.set_accept_format('json')
        
        response = client.do_action_with_exception(request)
        rules = json.loads(response)
        return rules.get('Permissions', {}).get('Permission', [])
    except (ClientException, ServerException) as e:
        logger.error(f"无法获取安全组规则: {e}")
        if server_chan_key and server_chan_key != "your_server_chan_key":
            send_critical_notification(server_chan_key, f"无法获取安全组规则: {e}")
        raise

# 删除带有标记的旧规则
def delete_old_rules(client, security_group_id, tag, server_chan_key):
    try:
        rules = get_security_group_rules(client, security_group_id, server_chan_key)
        for rule in rules:
            if rule.get('Description') == tag:
                request = RevokeSecurityGroupRequest.RevokeSecurityGroupRequest()
                request.set_SecurityGroupId(security_group_id)
                request.set_IpProtocol(rule['IpProtocol'])
                request.set_PortRange(rule['PortRange'])
                request.set_SourceCidrIp(rule['SourceCidrIp'])
                request.set_Policy(rule['Policy'])
                request.set_NicType(rule['NicType'])
                client.do_action_with_exception(request)
    except (ClientException, ServerException) as e:
        logger.error(f"无法删除旧的安全组规则: {e}")
        if server_chan_key and server_chan_key != "your_server_chan_key":
            send_critical_notification(server_chan_key, f"无法删除旧的安全组规则: {e}")
        raise

# 更新安全组白名单
def update_security_group_white_list(client, security_group_id, ip, ports, tag, priority, server_chan_key, server_chan_title, server_chan_message):
    try:
        for port_info in ports:
            port = port_info["port"]
            protocol = port_info["protocol"]
            # 将单个端口转换为端口范围格式
            if '-' not in port:
                port = f"{port}/{port}"
            request = AuthorizeSecurityGroupRequest.AuthorizeSecurityGroupRequest()
            request.set_accept_format('json')
            request.set_SecurityGroupId(security_group_id)
            request.set_IpProtocol(protocol)
            request.set_PortRange(port)
            request.set_SourceCidrIp(ip + "/32")
            request.set_Policy('accept')
            request.set_NicType('internet')
            request.set_Description(tag)
            request.set_Priority(priority)

            response = client.do_action_with_exception(request)
            logger.info(str(response, encoding='utf-8'))

        # 发送通知
        if server_chan_key and server_chan_key != "your_server_chan_key":
            send_server_chan_notification(server_chan_key, server_chan_title, server_chan_message, ip, ports)

    except (ClientException, ServerException) as e:
        logger.error(f"无法更新安全组白名单: {e}")
        if server_chan_key and server_chan_key != "your_server_chan_key":
            send_critical_notification(server_chan_key, f"无法更新安全组白名单: {e}")
        raise

# 发送Server酱通知
def send_server_chan_notification(server_chan_key, title, message, ip, ports):
    try:
        title = title.replace("{IP}", ip).replace("{ports}", str(ports))
        message = message.replace("{IP}", ip).replace("{ports}", str(ports))
        url = f"https://sctapi.ftqq.com/{server_chan_key}.send"
        data = {
            "title": title,
            "desp": message
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            logger.info("Server酱通知发送成功")
        else:
            logger.error(f"Server酱通知发送失败，状态码: {response.status_code}")
    except RequestException as e:
        logger.error(f"无法发送Server酱通知: {e}")
        raise

# 发送重大错误通知
def send_critical_notification(server_chan_key, message):
    try:
        url = f"https://sctapi.ftqq.com/{server_chan_key}.send"
        data = {
            "title": "重大错误通知",
            "desp": message
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            logger.info("重大错误通知发送成功")
        else:
            logger.error(f"重大错误通知发送失败，状态码: {response.status_code}")
    except RequestException as e:
        logger.error(f"无法发送重大错误通知: {e}")
        raise

# 记录IP地址到本地文件
def record_ip(ip_record_file, ip_records, server_chan_key):
    try:
        with open(ip_record_file, 'w') as file:
            json.dump(ip_records, file)
    except IOError as e:
        logger.error(f"无法写入IP记录文件 {ip_record_file}: {e}")
        if server_chan_key and server_chan_key != "your_server_chan_key":
            send_critical_notification(server_chan_key, f"无法写入IP记录文件 {ip_record_file}: {e}")
        raise

# 读取本地记录的IP地址
def load_ip_records(ip_record_file, server_chan_key):
    try:
        if os.path.exists(ip_record_file):
            with open(ip_record_file, 'r') as file:
                ip_records = json.load(file)
            return ip_records
        else:
            return {}
    except IOError as e:
        logger.error(f"无法读取IP记录文件 {ip_record_file}: {e}")
        if server_chan_key and server_chan_key != "your_server_chan_key":
            send_critical_notification(server_chan_key, f"无法读取IP记录文件 {ip_record_file}: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"IP记录文件 {ip_record_file} 解析错误: {e}")
        if server_chan_key and server_chan_key != "your_server_chan_key":
            send_critical_notification(server_chan_key, f"IP记录文件 {ip_record_file} 解析错误: {e}")
        raise

def main():
    try:
        # 加载配置文件
        config_path = os.environ.get('CONFIG_PATH', '/app/config/config.json')
        sample_config_path = os.environ.get('SAMPLE_CONFIG_PATH', '/app/config.sample.json')
        config = load_config(config_path, sample_config_path)
        
        ACCESS_KEY_ID = config['ACCESS_KEY_ID']
        ACCESS_KEY_SECRET = config['ACCESS_KEY_SECRET']
        REGION_ID = config['REGION_ID']
        SECURITY_GROUP_ID = config['SECURITY_GROUP_ID']
        TAG = config['TAG']
        GETIP_URLS = config['GETIP_URLS']
        PORTS = config['PORTS']
        PRIORITY = config.get('PRIORITY', 1)
        IP_RECORD_FILE = config.get('IP_RECORD_FILE', '/app/config/' + config.get('IP_RECORD_FILE', 'ip_records.json'))
        INTERVAL_SECONDS = config.get('INTERVAL_SECONDS', 3600)
        SERVER_CHAN_KEY = config.get('SERVER_CHAN_KEY', 'your_server_chan_key')
        SERVER_CHAN_TITLE = config.get('SERVER_CHAN_TITLE', '阿里云安全组白名单更新通知')
        SERVER_CHAN_MESSAGE = config.get('SERVER_CHAN_MESSAGE', '已新增白名单，IP:{IP}，端口: {ports}\n\n注意:在本次更新前，已将系统内有相同tag的规则全部删除。需要手动修改的记录请避免使用同样的tag。')

        client = AcsClient(ACCESS_KEY_ID, ACCESS_KEY_SECRET, REGION_ID)

        # 忽略现有的 IP 记录文件，强制更新一次规则
        new_ip_records = {}

        # 获取并删除旧规则
        delete_old_rules(client, SECURITY_GROUP_ID, TAG, SERVER_CHAN_KEY)
        
        # 获取新的IP地址并更新安全组白名单
        for url in GETIP_URLS:
            ip = get_ip_from_service(url, SERVER_CHAN_KEY)
            logger.info(f"IP from {url}: {ip}")
            new_ip_records[url] = ip

            # 更新安全组白名单
            update_security_group_white_list(client, SECURITY_GROUP_ID, ip, PORTS, TAG, PRIORITY, SERVER_CHAN_KEY, SERVER_CHAN_TITLE, SERVER_CHAN_MESSAGE)

        # 记录新的IP地址到本地文件
        record_ip(IP_RECORD_FILE, new_ip_records, SERVER_CHAN_KEY)

        while True:
            # 读取本地记录的IP地址
            ip_records = load_ip_records(IP_RECORD_FILE, SERVER_CHAN_KEY)
            new_ip_records = {}

            # 获取新的IP地址并更新安全组白名单
            for url in GETIP_URLS:
                ip = get_ip_from_service(url, SERVER_CHAN_KEY)
                logger.info(f"IP from {url}: {ip}")
                new_ip_records[url] = ip

                if ip_records.get(url) != ip:
                    # 更新安全组白名单
                    update_security_group_white_list(client, SECURITY_GROUP_ID, ip, PORTS, TAG, PRIORITY, SERVER_CHAN_KEY, SERVER_CHAN_TITLE, SERVER_CHAN_MESSAGE)
                else:
                    logger.info(f"IP from {url} has not changed, no update required.IP没有发生变化,本次没有更新")

            # 记录新的IP地址到本地文件
            record_ip(IP_RECORD_FILE, new_ip_records, SERVER_CHAN_KEY)

            # 等待指定的时间间隔
            time.sleep(INTERVAL_SECONDS)

    except Exception as e:
        logger.error(f"程序运行过程中出现错误: {e}")
        if SERVER_CHAN_KEY and SERVER_CHAN_KEY != "your_server_chan_key":
            send_critical_notification(SERVER_CHAN_KEY, f"程序运行过程中出现错误: {e}")

if __name__ == "__main__":
    main()
