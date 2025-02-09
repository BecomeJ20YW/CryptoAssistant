import json
import os
import sys

def load_api_config():
    config_file = 'api_config.json'
    
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"配置文件 {config_file} 不存在，请创建该文件并填入API密钥信息")
    
    # 读取配置文件
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # 验证配置是否完整
        if not config.get('api_key') or not config.get('api_secret'):
            raise ValueError("配置文件中缺少 api_key 或 api_secret")
        
        # 检查API密钥格式
        api_key = str(config['api_key']).strip()
        api_secret = str(config['api_secret']).strip()
        
        # 验证API密钥不是默认值
        if api_key in ['YOUR_API_KEY_HERE', '你的API密钥']:
            raise ValueError("请将配置文件中的 api_key 替换为你的实际API密钥")
        if api_secret in ['YOUR_SECRET_KEY_HERE', '你的API密钥密文']:
            raise ValueError("请将配置文件中的 api_secret 替换为你的实际API密钥密文")
            
        return api_key, api_secret
        
    except json.JSONDecodeError:
        raise ValueError(f"配置文件 {config_file} 格式不正确，请确保是有效的JSON格式")
    except UnicodeDecodeError:
        raise ValueError(f"配置文件 {config_file} 编码错误，请确保使用UTF-8编码保存文件")
    except Exception as e:
        raise ValueError(f"读取配置文件时发生错误: {str(e)}")

try:
    # 加载API配置
    API_KEY, API_SECRET = load_api_config()
except Exception as e:
    print(f"错误: {str(e)}")
    sys.exit(1)

if not API_KEY or not API_SECRET:
    raise ValueError("Please make sure you have set up your API keys in api_config.json") 