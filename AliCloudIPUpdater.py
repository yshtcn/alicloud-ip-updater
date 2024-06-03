import os
import json
import requests
import time
import shutil
from requests.exceptions import RequestException
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkecs.request.v20140526 import DescribeSecurityGroupAttributeRequest, AuthorizeSecurityGroupRequest, RevokeSecurityGroupRequest

# 从配置文件加载配置信息
def load_config(config_file, sample_config_file):
    if not os.path.exists(config_file):
        print(f"配置文件 {config_file} 不存在。")
        print(f"将从样例配置文件 {sample_config_file} 复制一份。")
        shutil.copy(sample_config_file, config_file)
        print(f"请在 {config_file} 中配置您的设置。")
        raise FileNotFoundError(f"配置文件 {config_file} 不存在。")
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        print(f"配置文件 {config_file} 未找到。")
        raise
    except json.JSONDecodeError:
        print(f"配置文件 {config_file} 解析错误。")
        raise

# 获取IP地址
def get_ip_from_service(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        ip = response.text.strip()
        return ip
    except RequestException as e:
        print(f"无法从 {url} 获取IP地址: {e}")
        raise

# 获取当前安全组的规则
def get_security_group_rules(client, security_group_id):
    try:
        request = DescribeSecurityGroupAttributeRequest.DescribeSecurityGroupAttributeRequest()
        request.set_SecurityGroupId(security_group_id)
        request.set_accept_format('json')
        
        response = client.do_action_with_exception(request)
        rules = json.loads(response)
        return rules.get('Permissions', {}).get('Permission', [])
    except (ClientException, ServerException) as e:
        print(f"无法获取安全组规则: {e}")
        raise

# 删除带有标记的旧规则
def delete_old_rules(client, security_group_id, tag):
    try:
        rules = get_security_group_rules(client, security_group_id)
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
        print(f"无法删除旧的安全组规则: {e}")
        raise

# 更新安全组白名单
def update_security_group_white_list(client, security_group_id, ip, ports, tag, priority):
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
            print(str(response, encoding='utf-8'))
    except (ClientException, ServerException) as e:
        print(f"无法更新安全组白名单: {e}")
        raise

# 记录IP地址到本地文件
def record_ip(ip_record_file, ip_records):
    try:
        with open(ip_record_file, 'w') as file:
            json.dump(ip_records, file)
    except IOError as e:
        print(f"无法写入IP记录文件 {ip_record_file}: {e}")
        raise

# 读取本地记录的IP地址
def load_ip_records(ip_record_file):
    try:
        if os.path.exists(ip_record_file):
            with open(ip_record_file, 'r') as file:
                ip_records = json.load(file)
            return ip_records
        else:
            return {}
    except IOError as e:
        print(f"无法读取IP记录文件 {ip_record_file}: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"IP记录文件 {ip_record_file} 解析错误: {e}")
        raise

def main():
    try:
        # 加载配置文件
        config_path = os.environ.get('CONFIG_PATH', 'config.json')
        sample_config_path = os.environ.get('SAMPLE_CONFIG_PATH', 'config.sample.json')
        config = load_config(config_path, sample_config_path)
        
        ACCESS_KEY_ID = config['ACCESS_KEY_ID']
        ACCESS_KEY_SECRET = config['ACCESS_KEY_SECRET']
        REGION_ID = config['REGION_ID']
        SECURITY_GROUP_ID = config['SECURITY_GROUP_ID']
        TAG = config['TAG']
        GETIP_URLS = config['GETIP_URLS']
        PORTS = config['PORTS']
        PRIORITY = config.get('PRIORITY', 1)
        IP_RECORD_FILE = config.get('IP_RECORD_FILE', 'ip_records.json')
        INTERVAL_SECONDS = config.get('INTERVAL_SECONDS', 3600)
        
        client = AcsClient(ACCESS_KEY_ID, ACCESS_KEY_SECRET, REGION_ID)

        while True:
            # 读取本地记录的IP地址
            ip_records = load_ip_records(IP_RECORD_FILE)
            new_ip_records = {}

            # 获取并删除旧规则
            delete_old_rules(client, SECURITY_GROUP_ID, TAG)
            
            # 获取新的IP地址并更新安全组白名单
            for url in GETIP_URLS:
                ip = get_ip_from_service(url)
                print(f"IP from {url}: {ip}")
                new_ip_records[url] = ip

                if ip_records.get(url) != ip:
                    # 更新安全组白名单
                    update_security_group_white_list(client, SECURITY_GROUP_ID, ip, PORTS, TAG, PRIORITY)
                else:
                    print(f"IP from {url} has not changed, no update required.")

            # 记录新的IP地址到本地文件
            record_ip(IP_RECORD_FILE, new_ip_records)

            # 等待指定的时间间隔
            time.sleep(INTERVAL_SECONDS)

    except Exception as e:
        print(f"程序运行过程中出现错误: {e}")

if __name__ == "__main__":
    main()
