#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试上传功能的脚本
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import tempfile
import shutil
from pathlib import Path

# 测试配置
BASE_URL = 'http://127.0.0.1:8000'
LOGIN_URL = '/students/login/'
UPLOAD_URL = '/students/upload-proof/'
TEST_USERNAME = 'test_student'
TEST_PASSWORD = 'test_password'

def create_test_file():
    """创建临时测试文件"""
    temp_dir = tempfile.mkdtemp()
    try:
        file_path = os.path.join(temp_dir, 'test_file.txt')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('This is a test file for uploading.')
        return file_path
    except Exception as e:
        shutil.rmtree(temp_dir)
        raise e

def test_login_and_upload():
    """测试登录和上传功能"""
    session = requests.Session()
    
    # 1. 登录测试
    print(f"\n测试登录: {BASE_URL}{LOGIN_URL}")
    login_data = {
        'username': TEST_USERNAME,
        'password': TEST_PASSWORD,
        'user_type': 'student'
    }
    
    try:
        login_response = session.post(f"{BASE_URL}{LOGIN_URL}", data=login_data)
        print(f"登录状态码: {login_response.status_code}")
        print(f"登录响应URL: {login_response.url}")
        
        # 检查是否成功登录
        if login_response.status_code == 200 and '/login/' not in login_response.url:
            print("✓ 登录成功")
        else:
            print("✗ 登录失败或未正确重定向")
            print(f"响应内容片段: {login_response.text[:500]}...")
            return False
            
    except requests.RequestException as e:
        print(f"✗ 登录请求失败: {e}")
        return False
    
    # 2. 访问上传页面测试
    print(f"\n测试访问上传页面: {BASE_URL}{UPLOAD_URL}")
    try:
        upload_page_response = session.get(f"{BASE_URL}{UPLOAD_URL}")
        print(f"访问上传页面状态码: {upload_page_response.status_code}")
        
        if upload_page_response.status_code == 200:
            print("✓ 访问上传页面成功")
        else:
            print(f"✗ 访问上传页面失败: {upload_page_response.status_code}")
            print(f"响应内容片段: {upload_page_response.text[:500]}...")
            return False
            
    except requests.RequestException as e:
        print(f"✗ 访问上传页面请求失败: {e}")
        return False
    
    # 3. 上传测试
    print(f"\n测试文件上传: {BASE_URL}{UPLOAD_URL}")
    try:
        # 创建测试文件
        test_file_path = create_test_file()
        
        # 准备上传数据
        with open(test_file_path, 'rb') as f:
            upload_data = {
                'score_item': '1',  # 校级一等奖学金
                'additional_info': '这是一个测试上传'
            }
            upload_files = {
                'proof_file': ('test_upload.txt', f, 'text/plain')
            }
            
            upload_response = session.post(
                f"{BASE_URL}{UPLOAD_URL}", 
                data=upload_data, 
                files=upload_files,
                allow_redirects=True
            )
            
            print(f"上传状态码: {upload_response.status_code}")
            print(f"上传响应URL: {upload_response.url}")
            
            if upload_response.status_code == 200 or upload_response.status_code == 302:
                print("✓ 上传请求已成功处理")
                success = True
            else:
                print(f"✗ 上传请求失败: {upload_response.status_code}")
                print(f"响应内容片段: {upload_response.text[:500]}...")
                success = False
    
    except requests.RequestException as e:
        print(f"✗ 上传请求失败: {e}")
        success = False
    finally:
        # 清理临时文件
        if 'test_file_path' in locals():
            try:
                os.unlink(test_file_path)
                os.rmdir(os.path.dirname(test_file_path))
            except:
                pass
    
    return success

def main():
    """主函数"""
    print("开始测试学生上传功能...")
    print(f"基础URL: {BASE_URL}")
    print(f"测试账号: {TEST_USERNAME}/{TEST_PASSWORD}")
    
    success = test_login_and_upload()
    
    if success:
        print("\n🎉 测试完成，上传功能工作正常!")
    else:
        print("\n❌ 测试失败，请检查相关配置和代码")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())