$body = @{title='688池扫描 30只候选'; desp='昨日688股票池扫描
候选标的 30 只(TOP10):

立讯精密(002475) 价71.29 涨2.6% 量比1.1 分70 涨2.5% | 量比1.1 | 未涨停
中国卫星(600118) 价114.18 涨6.4% 量比1.4 分70 涨6.4% | 量比1.4 | 额7953万
东湖高新(600133) 价9.22 涨1.5% 量比1.2 分70 涨1.5% | 量比1.2 | 未涨停
金发科技(600143) 价18.07 涨1.9% 量比2.1 分70 涨1.9% | 量比2.1 | 未涨停
浪莎股份(600137) 价24.1 涨3.7% 量比1.1 分70 涨3.7% | 量比1.1 | 未涨停
中体产业(600158) 价13.49 涨1.7% 量比1.4 分70 涨1.7% | 量比1.4 | 未涨停
航天机电(600151) 价15.39 涨1.8% 量比1.2 分70 涨1.8% | 量比1.2 | 未涨停
安通控股(600179) 价4.39 涨1.6% 量比1.3 分70 涨1.6% | 量比1.3 | 未涨停
天坛生物(600161) 价14.35 涨1.5% 量比1.3 分70 涨1.5% | 量比1.3 | 未涨停
卧龙新能(600173) 价7.5 涨3.2% 量比1.6 分70 涨3.2% | 量比1.6 | 未涨停'}
$json = ConvertTo-Json -InputObject $body -Compress
$utf8 = [System.Text.Encoding]::UTF8.GetBytes($json)
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-RestMethod -Uri 'https://sctapi.ftqq.com/SCT345078TEFwhlSFcUKuEuPBQ2D21riKC.send' -Method Post -ContentType 'application/json' -Body $utf8 -TimeoutSec 15