# -*- coding: utf-8 -*-
"""
数据加载器
从缓存pickle文件加载K线数据
"""
import pickle, os, sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))


class DataLoader:
    """加载K线数据 + 财务数据"""

    FINANCIAL_PKL = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\quant_ml\data\financial_features.pkl')

    def __init__(self, config: dict):
        self.cfg = config
        self.data_dir = PROJECT_ROOT / config.get('data_dir', 'data')
        self.source_pickle = Path(config['data']['source_pickle'])
        self.min_history = config['data']['min_history_days']
        self._data = None
        self._fin_data = None

    def load(self) -> dict:
        """
        返回: dict {股票代码: pd.DataFrame}
        DataFrame列: date, open, high, low, close, volume
        """
        print(f"[DataLoader] 加载数据: {self.source_pickle}")
        t0 = os.popen('python -c "import time; print(time.time())"').__enter__()

        # 解析路径（支持相对/绝对）
        if not self.source_pickle.is_absolute():
            resolved = PROJECT_ROOT / self.source_pickle
        else:
            resolved = self.source_pickle

        # 如果没有，尝试workspace-investment/ml_output_v6/
        if not resolved.exists():
            alt = PROJECT_ROOT.parent / 'ml_output_v6' / 'all_kline.pkl'
            if alt.exists():
                resolved = alt
                print(f"[DataLoader] 备选路径: {resolved}")

        if not resolved.exists():
            raise FileNotFoundError(f"数据文件不存在: {resolved}")

        with open(resolved, 'rb') as f:
            kline = pickle.load(f)

        # float64 → float32 降精度，节省约 30% 内存（数值精度足够）
        for code, df in kline.items():
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns and df[col].dtype == 'float64':
                    df[col] = df[col].astype('float32')

        print(f"[DataLoader] 加载完成: {len(kline)} 只股票")
        self._data = kline
        self._load_financial()
        return kline

    def _load_financial(self):
        """加载财务特征数据"""
        fin_path = self.FINANCIAL_PKL
        if not fin_path.exists():
            print(f"[DataLoader] 财务数据不存在: {fin_path}，跳过")
            self._fin_data = {}
            return
        with open(fin_path, 'rb') as f:
            self._fin_data = pickle.load(f)
        print(f"[DataLoader] 财务数据加载完成: {len(self._fin_data)} 只")

    def get_financial(self, code: str) -> dict:
        """获取单只股票的财务特征（归一化后的code格式）"""
        if self._fin_data is None:
            return {}
        # 尝试原格式
        if code in self._fin_data:
            return self._fin_data[code]
        # 尝试归一化格式（去掉sh./sz.前缀）
        norm = code.replace('sh.', '').replace('sz.', '')
        if norm in self._fin_data:
            return self._fin_data[norm]
        # 尝试添加上前缀
        for prefix in ['sh.', 'sz.']:
            if prefix + code in self._fin_data:
                return self._fin_data[prefix + code]
        return {}

    def filter_min_history(self, data: dict) -> dict:
        """过滤历史不足的股票"""
        filtered = {
            code: df for code, df in data.items()
            if len(df) >= self.min_history
        }
        removed = len(data) - len(filtered)
        if removed > 0:
            print(f"[DataLoader] 过滤{removed}只（历史不足{self.min_history}日）")
        return filtered

    def get_date_range(self, data: dict) -> tuple:
        """返回数据日期范围"""
        dates = []
        for df in list(data.values())[:10]:
            dates.extend(df['date'].tolist())
        return min(dates), max(dates)

    @property
    def data(self):
        if self._data is None:
            self.load()
        return self._data
