import json
with open(r'C:\Users\Administrator\.openclaw\openclaw.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Check all agents and their model configs
print("=== 所有Agent模型配置 ===")
for agent_id, agent_config in config.get('agents', {}).get('entries', {}).items():
    model_conf = agent_config.get('model', {})
    primary = model_conf.get('primary', '')
    fallbacks = model_conf.get('fallbacks', [])
    print(f"\n{agent_id}:")
    print(f"  primary: {primary}")
    if fallbacks:
        print(f"  fallbacks: {fallbacks[:5]}")

# Check default model config
print("\n=== 默认模型配置 ===")
defaults = config.get('agents', {}).get('defaults', {}).get('model', {})
print(f"primary: {defaults.get('primary', '')}")
print(f"fallbacks: {defaults.get('fallbacks', [])[:5]}")

# Check which providers have rate limits
print("\n=== Provider状态分析 ===")
providers = config.get('models', {}).get('providers', {})
for pname, pconf in providers.items():
    base_url = pconf.get('baseUrl', '')
    # Free providers that may have rate limits
    if 'agnes-ai.com' in base_url or 'sensenova.cn' in base_url:
        print(f"{pname}: 免费服务，可能有速率限制")
    elif 'nvidia.com' in base_url or 'modal.direct' in base_url:
        print(f"{pname}: NVIDIA/Modal API，通常不限流")
    elif 'agnes-ai.cn' in base_url:
        print(f"{pname}: 中国区API，可能不限流")
