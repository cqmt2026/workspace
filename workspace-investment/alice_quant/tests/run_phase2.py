import sys, os
# 确定项目根目录
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_script_dir, '..'))
sys.path.insert(0, _project_root)
import pandas as pd
from alice_quant.data.version import DataVersionManager
from alice_quant.data.snapshot import SnapshotManager
from alice_quant.data.sources import TencentSource, EfinanceSource, AkshareSource
from alice_quant.data.datahub import DataHub
from alice_quant.core.config import ConfigManager

# Test Version Manager
vm = DataVersionManager()
v = vm.create_version({'stock_count': 5000})
print(f'Version: {v}')
info = vm.get_version_info(v)
assert info['data']['stock_count'] == 5000
latest = vm.get_latest_version()
assert latest == v
versions = vm.list_versions(limit=5)
assert len(versions) >= 1
print('Version Manager OK')

# Test Snapshot
sm = SnapshotManager()
df = pd.DataFrame({'date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04'], 'close': [10, 11, 12, 13]})
f = sm.filter_by_date(df, '2024-01-03')
assert len(f) == 3
assert sm.validate_no_future_data(f, '2024-01-03')
assert not sm.validate_no_future_data(df, '2024-01-03')
print('Snapshot OK')

# Test Sources
ts = TencentSource()
print(f'Tencent connected: {ts.connect()}')
es = EfinanceSource()
print(f'Efinance connected: {es.connect()}')
aks = AkshareSource()
print(f'Akshare connected: {aks.connect()}')

# Test DataHub
config = ConfigManager()
config.load('config/default.yaml')
dh = DataHub(config)
ok = dh.initialize()
print(f'DataHub initialized: {ok}')
version = dh.get_latest_version()
print(f'DataHub latest version: {version}')

print('\nPhase 2 all OK')