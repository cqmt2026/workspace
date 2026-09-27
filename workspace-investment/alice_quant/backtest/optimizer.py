"""参数优化器 - 网格搜索 + Walk-Forward"""
import itertools
from typing import Dict, List, Any, Callable, Optional
from tqdm import tqdm


class ParameterOptimizer:
    """参数优化器

    用法:
        optimizer = ParameterOptimizer(evaluate_fn=my_evaluate)
        optimizer.add_param('ma_short', [5, 10, 20])
        optimizer.add_param('ma_long', [30, 60, 120])
        best = optimizer.grid_search(progress=True)
    """

    def __init__(self, evaluate_fn: Callable[[Dict[str, Any]], float]):
        self._params: Dict[str, List[Any]] = {}
        self._evaluate_fn = evaluate_fn
        self._results: List[tuple] = []

    def add_param(self, name: str, values: List[Any]):
        """添加待优化参数

        Args:
            name: 参数名
            values: 待搜索的值列表
        """
        self._params[name] = values

    def grid_search(self, progress: bool = True) -> Dict[str, Any]:
        """网格搜索最优参数

        Args:
            progress: 是否显示进度条

        Returns:
            最优参数字典
        """
        keys = list(self._params.keys())
        value_lists = [self._params[k] for k in keys]
        total = 1
        for vl in value_lists:
            total *= len(vl)

        iterator = itertools.product(*value_lists)
        if progress:
            iterator = tqdm(iterator, total=total, desc='参数搜索')

        best_score = float('-inf')
        best_params = {}

        for combo in iterator:
            params = dict(zip(keys, combo))
            try:
                score = self._evaluate_fn(params)
                self._results.append((score, params))
                if score > best_score:
                    best_score = score
                    best_params = params
            except Exception as e:
                continue

        if progress:
            tqdm.write(f'最优参数: {best_params}, 评分: {best_score:.4f}')

        return best_params

    def get_results(self) -> List[tuple]:
        """获取所有搜索结果 (score, params)"""
        return sorted(self._results, key=lambda x: -x[0])

    def top_n(self, n: int = 5) -> List[tuple]:
        """获取Top N结果"""
        return self.get_results()[:n]