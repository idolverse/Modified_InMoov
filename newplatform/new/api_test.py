#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API测试工具 - 检查Flask路由是否正确注册
"""

import os
import sys
import requests
import time

def test_api_endpoint(url, method="GET", data=None):
    """测试API端点是否可访问"""
    print(f"测试 {method} {url}...")
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(url, json=data or {}, timeout=5)
        
        content_type = response.headers.get('Content-Type', '')
        
        print(f"状态码: {response.status_code}")
        print(f"Content-Type: {content_type}")
        
        if 'application/json' in content_type:
            print(f"响应内容: {response.json()}")
            return True
        else:
            print(f"警告: 响应不是JSON格式")
            print(f"响应内容前100个字符: {response.text[:100]}...")
            return False
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def main():
    """主函数"""
    print("API测试工具 - 检查Flask路由是否正确注册")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # 检查服务器是否在运行
    print("检查服务器是否在运行...")
    try:
        response = requests.get(f"{base_url}/", timeout=2)
        print(f"服务器已启动，状态码: {response.status_code}")
    except:
        print("❌ 服务器未启动或无法访问")
        print("请先运行 run_web.py 启动服务器")
        return
    
    # 测试各个API端点
    api_tests = [
        {"url": f"{base_url}/api/start", "method": "POST"},
        {"url": f"{base_url}/api/stop", "method": "POST"},
        {"url": f"{base_url}/api/status", "method": "GET"},
        {"url": f"{base_url}/api/chat", "method": "POST", "data": {"message": "测试消息"}}
    ]
    
    print("\n开始测试API端点...")
    for test in api_tests:
        success = test_api_endpoint(
            test["url"], 
            method=test["method"], 
            data=test.get("data")
        )
        print(f"测试结果: {'✅ 成功' if success else '❌ 失败'}")
        print("-" * 50)
    
    print("\n所有测试完成")
    print("如果发现任何失败的API端点，请检查相应的路由处理函数")

if __name__ == "__main__":
    main()
