# 缂栫爜閾佸緥锛?026-07-14 鏂板锛?
## 鏋舵瀯鍩哄噯閾佸緥锛?026-08-17 鏂板锛?
**鍏変紡/鑾峰瀛愮郴缁熸墍鏈変换鍔℃墽琛屼笌浼樺寲鍗囩骇锛屽繀椤讳弗鏍煎熀浜庛€婂琛屼笟鑾峰绯荤粺鏋舵瀯璁捐鏂囨。銆?*锛?
- **鍩哄噯鏂囨。**: `workspace-pv/docs/ARCHITECTURE.md`锛堝叚灞傛灦鏋?+ 琛屼笟鎻掍欢灞?+ 缁熶竴鎺ュ彛 + S1-S5寤鸿璺緞锛?- **鎵ц鍓嶅繀璇?*: 浠讳綍娑夊強鍏変紡鑾峰绯荤粺鐨勫紑鍙?浼樺寲/杩唬锛屽厛璇绘鏂囨。纭涓庢灦鏋勪竴鑷达紝绂佹鍑洿瑙夌洿鎺ュ啓浠ｇ爜
- **琛屼笟鎻掍欢鍘熷垯**: 閫氱敤寮曟搸 + 琛屼笟鎻掍欢锛坕ndustry_config/<琛屼笟>/锛夛紝鎹㈣涓氫笉鏀瑰紩鎿?- **褰撳墠闃舵**: S1瀹屾垚+鎻掍欢鍖栨敼閫狅紙2026-08-18锛夛細hot_topic_collector/policy_monitor/content_generator 鍧囧凡鎺ュ叆 industry_config/solar/ 鎻掍欢灞傦紱pv_analyzer bug宸蹭慨澶嶏紱pipeline姝ｅ父杩愯
- **褰掑睘**: 杩欐槸system绾ц鍒欙紝鎵€鏈夊瓙绯荤粺/瀛怉gent鎵ц鍏変紡鑾峰浠诲姟鏃跺悓鏍峰己鍒?
## 鏋舵瀯鏂囨。鍚屾閾佸緥锛?026-08-17 鏂板锛?
**浠讳綍缁忚繃楠岃瘉鐨勪紭鍖栧崌绾э紝閮藉繀椤诲悓姝ュ洖鏇存柊銆婂琛屼笟鑾峰绯荤粺鏋舵瀯璁捐鏂囨。銆?*锛?
- **楠岃瘉鎵嶆洿鏂?*: 鍙湁缁忚繃楠岃瘉鐨勪紭鍖栵紙宸茶窇閫?宸叉祴璇曢€氳繃锛夋墠鍐欏叆鏂囨。锛屼笉鐣?瑙勫垝涓絾鏈疄鐜?鐨勮繃鏃跺唴瀹?- **鍏堣縼绉诲悗鏇存柊**: 鏂扮殑/鏀硅繘鐨勬ā鍧椾唬鐮佽惤鍦板悗锛屽悓姝ユ洿鏂?ARCHITECTURE.md锛堟ā鍧楁竻鍗?鎺ュ彛/鏁版嵁琛?寤鸿璺緞锛?- **鐗堟湰閫掑**: 姣忔閲嶅ぇ鍙樻洿鍚庨€掑鏂囨。鐗堟湰鍙凤紙v0.1 鈫?v0.2...锛夛紝骞跺湪"鍏抽敭鍐崇瓥璁板綍"琛ㄨ拷鍔犺褰?- **妫€鏌ユ椂鏈?*: 姣忔鍏変紡鑾峰绯荤粺浠诲姟瀹屾垚鍚庯紝妫€鏌ユ槸鍚﹂渶瑕佸悓姝ユ洿鏂版灦鏋勬枃妗?- **钀藉湴浣嶇疆**: 涓庢灦鏋勬洿鏂板搴旂殑淇鏃ュ織锛屽瓨鑷?memory/鏃ュ織/淇鏃ュ織/ 骞舵爣娉?鏋舵瀯鍚屾"

---

# 缂栫爜閾佸緥锛?026-07-14 鏂板锛?
## 寮哄埗宸ヤ綔娴侊紙姣忔鍐欎唬鐮佸繀椤绘墽琛岋級

### 寮€濮嬪墠
1. `read` 鐩爣鏂囦欢 鈫?纭褰撳墠閫昏緫
2. `exec grep` 鎼滅储璋冪敤鐐?鈫?纭褰卞搷鑼冨洿
3. 纭 Python 鐗堟湰銆佽矾寰勭紪鐮併€佷緷璧栧彲鐢ㄦ€?
### 缂栧啓涓?1. 閬靛惊鍛藉悕绾﹀畾锛坰nake_case/PascalCase/UPPER_SNAKE_CASE锛?2. 杈圭晫鎯呭喌鍚屾澶勭悊锛堢┖杈撳叆/None/null/0/璐熸暟/鏋佸ぇ鍊硷級
3. 閬囧埌閲嶅浠ｇ爜 鈫?绔嬪嵆鎻愬彇鍑芥暟
4. 閿欒澶勭悊鐢ㄥ叿浣撳紓甯哥被鍨嬶紝涓嶈瑁?except

### 瀹屾垚鍚?1. 杩愯楠岃瘉娴嬭瘯锛坅ssert + print锛?2. grep 纭娌℃湁閬楁紡鐨勮皟鐢ㄧ偣
3. 閿欒淇℃伅瀹屾暣鍙

## 12 椤圭煭鏉垮鐓ц〃

| # | 鐭澘 | 瑙ｅ喅鏂瑰紡 | 浼樺厛绾?|
|---|------|---------|--------|
| 1 | 璇硶/鍩虹杈圭晫婕?| 姣忛」妫€鏌ョ┖/None/0/璐?瓒呭ぇ | P0 |
| 2 | 椤圭洰缁撴瀯缂哄叏灞€ | 鏀瑰墠鍏堣+grep 璋冪敤鐐?| P0 |
| 3 | 璋冭瘯鑳藉姏浣庢晥 | 鍏堢湅閿欒鏍堚啋浜屽垎娉曞畾浣嶁啋鏃ュ織楠岃瘉 | P0 |
| 4 | 閲嶆瀯鍡呰寮?| 鍑虹幇鍧忓懗閬撶珛鍗充慨锛堥噸澶嶄唬鐮?闀垮嚱鏁?娣卞祵濂楋級 | P1 |
| 5 | 娴嬭瘯鎰忚瘑缂哄け | 鏍稿績閫昏緫蹇呴』鏈?assert 楠岃瘉 | P0 |
| 6 | 鎬ц兘鎰忚瘑涓嶈冻 | O(n虏) 鎿嶄綔妫€鏌?+ 澶ф枃浠堕€愯璇?| P1 |
| 7 | 瀹夊叏鎰忚瘑绌虹櫧 | 鐢ㄦ埛杈撳叆涓嶅彲淇?+ 鍙傛暟鍖栨煡璇?| P1 |
| 8 | 閿欒澶勭悊绠€鍗?| 鍒嗗眰寮傚父 + fallback | P0 |
| 9 | 浠ｇ爜鍙鎬у樊 | 瑙佸悕鐭ユ剰 + 娉ㄩ噴瑙ｉ噴涓轰粈涔?| P1 |
| 10 | 鐗堟湰绠＄悊寮?| git diff 纭鍙樻洿 | P2 |
| 11 | 渚濊禆绠＄悊闅忔剰 | 鏍囧噯搴撲紭鍏?+ 閿佸畾鐗堟湰 | P1 |
| 12 | 鐜涓嶄竴鑷?| 鐗堟湰妫€鏌?+ 璺緞澶勭悊 + utf-8 | P0 |

瀹屾暣瑙勮寖: `coding-standards.md`

---

### 2026-07-30 鏂规硶璁洪搧寰嬩紭鍖?(v1.2)

- **AGENTS.md** 鏂规硶璁洪搧寰嬬増鏈寲锛歷1.2
- **鏂板绗洓姝ワ細浜嬪悗澶嶇洏锛?0绉掞級**锛氫换鍔″畬鎴愬悗鐨勫揩閫熷鐩橈紝纭繚瀛︿範闂幆
- **鏂板楠岃瘉閽╁瓙**锛氭墽琛屽墠鏌?shared-knowledge/绯荤粺鐭ヨ瘑鍥捐氨涓庡父瑙侀櫡闃辨墜鍐?md 鍖归厤闄烽槺
- **鏂板鎵ц涓‘璁?*锛氭瘡姝ュ畬鎴愬悗楠岃瘉缁撴灉锛岄槻姝㈤噸澶嶆搷浣?鍑劅瑙夊垽鏂?- **瑙﹀彂鏃舵満琛ュ厖**锛氭柊澧炲湴鍥剧儹鐐瑰瓙绯荤粺
- **鏂板鏂规硶璁哄仴搴锋鏌?cron**锛氭瘡鍛ㄤ竴10:05鎵弿鏍稿績瑙勫垯鏂囦欢瀹屾暣鎬?鐗堟湰/涓€鑷存€э紙scripts/methodology_health_check.py锛?- **R1 鏂囨。鑷姩鍚屾**锛歴ystem_maintenance.py 杩藉姞 sync_core_docs()锛屾瘡30鍒嗛挓妫€娴?涓牳蹇冩枃浠舵棩鏈熶竴鑷存€?- **R2 LLM 鐔旀柇**锛歳un_with_log.py 杩藉姞鐔旀柇鍣紝杩炵画3娆″け璐ュ憡璀︺€?娆＄啍鏂殏鍋?4h锛屾垚鍔熶竴娆″嵆閲嶇疆
- **R3 璁板繂灞傞檷绾?*锛歮emory_tools.py 宸查噸鏋勶紝DB 浠?F:\\supermemory 杩佺Щ鑷虫湰鍦?memory\\supermemory_db锛屾墍鏈夊煙缁熶竴浣跨敤 LIKE 鎼滅储锛堜笉渚濊禆澶栭儴鏈嶅姟锛夛紝365 鏉¤褰曚繚鐣欏彲璇?

- **闄烽槺鎵嬪唽鏇存柊**锛氭柊澧?4 鏉￠櫡闃辫褰曪紙auto_stagger stale寮曠敤銆乪dit鎹㈣绗ug銆丼upermemory璺緞杩佺Щ銆佺啍鏂櫒闄嶇骇瑙勫垯锛夛紝鏇存柊鑷?698 琛?
- **R4 淇鏃ュ織妯℃澘**\uff1a鏂板 TEMPLATE.md\uff08YAML frontmatter + 缁撴瀯鍖栧瓧娈礬uff09\uff0c浠ュ悗淇鏃ュ織鑷姩鏍囩鍖?
## 绯荤粺鍙樻洿璁板綍

### 2026-07-18 PPT妯℃澘鎵归噺鐢熶骇绯荤粺 (v2.3)

- **Skill鍒涘缓**: `ppt-template-producer` 鈥?閰嶇疆椹卞姩鈫抪ython-pptx鐢熸垚鈫掕嚜妫€鈫掍慨澶嶁啋鎵撳寘鍏ㄦ祦绋?- **鏍稿績鏂囦欢**: `scripts/gen_ppt_batch.py` + `scripts/ppt_templates_config.json`
- **浜у嚭**: 10濂楀彲鍞ā鏉匡紝23-25椤?濂楋紝27绉嶇増寮忥紝81%鏍囧噯绗﹀悎搴?- **璋冪敤鏂瑰紡**: 涓嬫璇?缁х画PPT妯℃澘"鎴?璋僷pt-template-producer"鍗虫帴缁?- **鍚屾**: TOOLS.md宸叉洿鏂帮紝skill鎻愭宸插垱寤?
### 2026-08-07 ForkProbe 瀹夎涓庨厤缃?
- **瀹夎**: `git clone` 鍒?`~/.agents/skills/forkprobe/`
- **渚濊禆**: jinja2 鉁?- **楠岃瘉**: 鎺ㄨ崘鍔熻兘姝ｅ父锛坮ecommend.py 璺戦€氾級锛?6涓猻moke娴嬭瘯涓牳蹇冩枃鏈姣旀ā鍧楅€氳繃
- **Windows 闄愬埗**: artifact 绠￠亾锛坵eb/video/鍥撅級渚濊禆 unix 鍛戒护锛學indows 涓嬮儴鍒嗗け璐ワ紱鏂囨湰瀵规瘮妯″紡鍙敤
- **璋冪敤鏂瑰紡**: 鑷劧璇█瑙﹀彂锛?姣旇緝鍑犱釜skill"锛夋垨 `/forkprobe`
- **鍚屾**: TOOLS.md 宸叉洿鏂?
### 2026-07-18 缂栫▼瀛怉gent鍒涘缓 (coding-agent)

- **Skill鍒涘缓**: `coding-agent` 鈥?涓撳绾х紪绋嬪瓙Agent锛屼富绯荤粺娲惧彂鈫掔紪鐮佲啋楠屾敹鈫掍氦浠?- **10鏉＄紪鐮侀搧寰?*: 鏀瑰墠鍏堣/褰卞搷闈㈡鏌?杈圭晫鍏ㄨ鐩?鏍囧噯搴撲紭鍏?閿欒澶勭悊鍒嗗眰/閲嶅浠ｇ爜鎻愬彇/鍛藉悕瑙勮寖/鏀瑰畬蹇呴獙/鎶ラ敊鍏堢湅鏍?鐜鎰熺煡
- **宸ヤ綔娴?*: 瀛愮郴缁熷彂鐜伴棶棰樷啋鎶ュ憡缁欎富绯荤粺鈫掍富绯荤粺娲惧彂鈫掔紪绋嬪瓙Agent鎵ц鈫掍富绯荤粺楠屾敹鈫掍氦浠樺瓙绯荤粺
- **閫傜敤**: 涓荤郴缁?灏忚/鑷獟浣?鎶曡祫/鏁板鍔ㄧ敾/寰俊灏忕▼搴?PPT妯℃澘锛屾墍鏈夌紪绋嬩换鍔?- **绂佹**: 涓嶅垹鏂囦欢/涓嶆敼绯荤粺閰嶇疆/涓嶈仈缃?涓嶈法鍩熷洖绛?- **璋冪敤鏂瑰紡**: 涓荤郴缁熼€氳繃 sessions_send 鎴?sessions_spawn 娲惧彂浠诲姟
- **鍚屾**: TOOLS.md宸叉洿鏂? skill鎻愭宸插垱寤? AGENTS.md宸叉洿鏂?
### 2026-07-18 宸℃鑴氭湰淇

- **daily_inspection.py** 淇3涓猙ug: 鏈堜唤纭紪鐮?06鈫掑姩鎬?銆丼upermemory鍦板潃(宸茶縼绉?銆丼erver閰辨畫鐣欐娴嬫帓闄?- **Server閰辨竻鐞?*: `holding_alert.py` 绉婚櫎搴熷純server閰辨帹閫佷唬鐮?- **纾佺洏娓呯悊**: Whisper缂撳瓨閲婃斁2.5GB (large-v3-turbo/medium/base/tiny鈫掑彧淇濈暀small)

### 2026-07-22 绯荤粺妫€鏌ヤ慨澶嶄笌鐦﹁韩

- **3涓狢ron timeout浼樺寲**: Hot-Topic-Finder(600s鈫?00s)銆丮ath-鑷姩瀛︿範(120s鈫?00s)銆丟itHub-Trending(180s鈫?00s)锛屽潎鍔?sense-6.7 fallback
- **绌虹洰褰曟竻鐞?*: 245涓┖鐩綍鍏ㄩ儴鍒犻櫎锛?19鈫?锛?- **纾佺洏鐦﹁韩鍚堣**: 閲婃斁 ~2.5GB锛圥ixelle-Video 545MB + MoneyPrinterTurbo 1.58GB + Temp/缂撳瓨 253MB + 搴熷純鑴氭湰娓呯悊锛?- **鏍稿績鑴氭湰绮剧畝**: scripts/ 浠?08涓啋73涓紙绮剧畝65%锛夛紝skills/ 浠?4涓啋39涓紙绮剧畝28%锛?- **瀹夊叏淇**: ai_retry.py 纭紪鐮丄PI Key 鈫?鏀逛负浠?openclaw.json 璇诲彇
- **澶囦唤鐩綍娓呯悊**: 淇濈暀 backup/sessions/ 鍜?backup/weekly/锛屾竻鐞嗗簾寮冩枃浠?- **PPT妯℃澘**: 浠?濂椻啋10濂楋紙v2.3, 81%绗﹀悎搴︼級

### 2026-07-22 绯荤粺缁存姢 Auto-Stagger 淇

- **闂**: system_maintenance.py 璋冪敤 auto_stagger.py 浣嗘枃浠朵笉瀛樺湪 鈫?閫€鍑虹爜1
- **鏍瑰洜**: stale reference 闄烽槺
- **淇**: 灏?run_auto_stagger() 璋冪敤鏀逛负 SKIP
- **楠岃瘉**: 鎵嬪姩鎵ц杩斿洖 3/3 OK锛岄€€鍑虹爜0

### 2026-07-24 鍦板浘鐑偣瀛愮郴缁?HyperFrames 闆嗘垚 (v13)

- **鏍稿績鏀归€?*: 寮曞叆HyperFrames (HTML+GSAP) 鏇夸唬鍘熸湁FFmpeg drawtext瑙嗛鍚堟垚鏂规
- **鏂版枃浠?*: `scripts/hyperframes_template.py` 鈥?JSON閰嶇疆鈫掕嚜鍔ㄧ敓鎴怘yperFrames HTML
- **鏂版枃浠?*: `scripts/config/city_shenzhen.json` 鈥?娣卞湷9鍖烘暟鎹厤缃枃浠?- **鏂伴厤缃?*: `config/map_style_config.json` 鏂板"鎶栭煶娣辫壊"鏍峰紡
- **淇敼鏂囦欢**: `scripts/pipeline.py` 鈥?鏂板 `--hyperframes` 鍙傛暟鍒囨崲娓叉煋寮曟搸
- **淇敼鏂囦欢**: `scripts/modules/map_drawer.py` 鈥?淇鍏ㄦ櫙鍥鹃噸澶嶇綏婀栧尯bug锛坔ighlight_name=None锛?- **淇bug**: 鍏ㄦ櫙鍥鹃珮浜涓€涓尯瀵艰嚧缃楁箹鍖洪噸澶嶆樉绀恒€佺鐢板尯琚烦杩?- **淇bug**: 闊抽鏃堕暱涓嶅尮閰嶏紙鑷姩妫€娴嬮煶棰戞椂闀匡紝鍔ㄦ€佸垎閰嶅悇鍖烘椂闂达級
- **淇bug**: 娣辫壊鑳屾櫙鏁堟灉宸紙鏀逛负钃濈伆鑳屾櫙+钃濊壊涓昏皟 #3b82f6锛?- **v13浜у嚭**: 9.9MB, 52.4s, 鍔ㄧ敾鍚斁澶ч暅+鏌辩姸鍥鹃棯鐑?鏁版嵁椤归€愰」寮瑰嚭
- **璋冪敤鏂瑰紡**: `python pipeline.py shenzhen --hyperframes`
- **妯℃澘鐢熸垚**: `python hyperframes_template.py shenzhen --render`
- **鍚屾**: TOOLS.md宸叉洿鏂? HEARTBEAT.md宸叉洿鏂?
### 2026-07-24 鏂规硶璁洪搧寰嬫墽琛屾鏌?
- **鏁欒**: 浠婂ぉ澶氭鍗″湪寰幆鎵ц澶辫触鍛戒护锛屾病鏈夊強鏃舵剰璇嗗埌鍗′綇
- **鏀硅繘**: 鎵ц浠诲姟鍓嶅厛璺戞柟娉曡妫€鏌ワ紝瓒呰繃30鍒嗛挓涓嶅嚭鎴愬搧绔嬪嵆鍒囨崲鏂规
- **楠岃瘉**: 宸插畬鎴?
- **AGENTS.md**锛氬伐浣滆鍒欐柊澧炪€岎煣?绗竴鎬у師鐞嗛搧寰嬨€嶏紝鍥涙鎷嗚В娉曪紙鐮哥琛ㄨ薄鈫掑€掔┖鐑傝嫻鏋溾啋閲嶆嫾涔愰珮鈫掓壘瑁傜紳锛? 5涓Е鍙戞椂鏈?- **SOUL.md**锛氭牳蹇冨師鍒欍€岀涓€鎬у師鐞嗐€嶄粠涓€鍙ヨ瘽灞曞紑涓哄彲鎵ц鐨勫洓姝ユ媶瑙ｆ硶 + 搴曠嚎鍘熷垯

## Promoted From Short-Term Memory (2026-07-17)

<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:10:13 -->
- 鏈€缁堜骇鍑? | 椤圭洰 | 鍊?| |------|-----| | 鏂囦欢 | L4-鍏变韩/videos/EP143_鍛ㄦ湡闂_final.mp4 | | 鎬绘椂闀?| 50.97s锛堝惈CTA缁撳熬4.7s锛?| [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:10-13]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:14:17 -->
- 鏈€缁堜骇鍑? | 鍑€鏃堕暱 | 46.27s锛堝亸宸?3.7s 鉁咃級 | | 鏂囦欢澶у皬 | 1.6MB | | atempo | 1.145x 鉁?| | TTS | 198瀛楋紝44.52s | [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:14-17]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:20:22 -->
- Method鍦烘櫙淇杩囩▼锛?杞紝鏁堢巼鏋佷綆锛? v1: self.wait(14.0)绌鸿浆14绉?鈫?閲嶅啓涓?姝idget灞曠ず; v2: 寰幆鍔ㄧ敾+wait杩囧锛?8s 鈫?绠€鍖栦负3姝idget涓嶅姞寰幆; v3-v5: wait缂╂斁闇囪崱锛?1s鈫?8s鈫?8s锛?[score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:20-22]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:25:27 -->
- 鏍稿績鏁欒: **ep_duration_checker --fix 涓嶅彲鐩蹭俊**锛氬畠鍙粺璁￠潤鎬佷唬鐮佷腑鐨剋ait锛屾棤娉曢娴婱anim娓叉煋鏃剁殑瀹為檯run_time; **澶嶆潅鍦烘櫙wait蹇呴』鎵嬪姩绠?*锛氶潪wait鍔ㄧ敾鏃堕暱鈮?2s锛岀洰鏍?0s锛岀洿鎺ュ姞8s wait銆備笉瑕佹瘡娆″彧璋?.5s璇? **鏀瑰畬鑴氭湰鍏堣窇棰勬鍐嶇湅宸窛**锛氬樊璺?3s灏变竴娆℃€ц皟澶燂紝涓嶈鍙嶅寰皟 [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:25-27]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:30:31 -->
- 鑷姩鍖栫郴缁焍ug: `auto_learn_trigger.py` Supermemory鍐欏叆澶辫触锛歚name 'error_counts' is not defined`; **宸蹭慨澶?*锛歚error_counts` 鈫?`error_counter`锛圠485锛?[score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:30-31]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:38:41 -->
- 鏂板3涓€氱敤widget缁勪欢: | 缁勪欢 | 鍔熻兘 | |------|------| | widget_pie_chart | 閫氱敤楗煎浘锛堝垎鏁?姒傜巼/鐧惧垎鏁板彲瑙嗗寲锛?| | widget_calendar_grid | 閫氱敤鏃ュ巻缃戞牸锛堟槦鏈熻绠楀彲瑙嗗寲锛?| [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:38-41]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:42:42 -->
- 鏂板3涓€氱敤widget缁勪欢: | widget_number_blocks | 閫氱敤鏁板瓧鏂瑰潡闃碉紙鏁板垪/鍛ㄦ湡/椤电爜鍙鍖栵級 | [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:42-42]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:45:48 -->
- 鏀归€?4涓浘褰㈠寲combo锛?8/18 = 100%锛? 楗煎浘缁勶細combo_fraction_ops, combo_probability, combo_percentage 鏉″舰鍥剧粍锛歝ombo_discount_calc, combo_ratio 鍒嗙粍鍥剧粍锛歝ombo_pigeonhole, combo_cow_grass 鏃ュ巻缁勶細combo_calendar_weekday [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:45-48]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:49:51 -->
- 鏀归€?4涓浘褰㈠寲combo锛?8/18 = 100%锛? 鏂瑰潡缁勶細combo_period_problem, combo_page_digit_count, combo_arithmetic_sequence 绾挎鍥剧粍锛歝ombo_speed_time_dist, combo_midterm_method 琛ㄦ牸缁勶細combo_logic_reasoning [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:49-51]
<!-- openclaw-memory-promotion:memory:memory/2026-07-12.md:6:7 -->
- 棰樼洰: 浠婂ぉ鏄槦鏈熶簩锛?00澶╁悗鏄槦鏈熷嚑锛?鏂规硶锛氫綑鏁版硶锛堝懆鏈?澶╋紝100梅7=14浣? 鈫?鍛ㄥ洓锛?[score=0.812 recalls=0 avg=0.620 source=memory/2026-07-12.md:6-7]

## Promoted From Short-Term Memory (2026-07-22)

<!-- openclaw-memory-promotion:memory:memory/2026-07-17.md:15:15 -->
- Pixelle-Video 閮ㄧ讲涓庢帓閿欙紙15:14~20:06锛? **鏁欒锛氭病鏈夊厛璺戞柟娉曡妫€鏌ワ紝鐩存帴鍐茶繘鎵ц妯″紡** [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-17.md:15-15]
<!-- openclaw-memory-promotion:memory:memory/2026-07-17.md:16:19 -->
- Pixelle-Video 閮ㄧ讲涓庢帓閿欙紙15:14~20:06锛? 灏濊瘯閮ㄧ讲 Pixelle-Video锛堝紑婧愯棰戠敓鎴愬伐鍏凤級; Streamlit Web UI 琚潃杞?SIGKILL 鈫?灏濊瘯淇甤onfig/婧愮爜/璺緞/env 鍏?娆℃墠鏀惧純; ComfyUI 闇€瑕佹湰鍦版樉鍗★紙940MX 2GB涓嶅锛? RunningHub 浜戠闇€瑕?API Key [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-17.md:16-19]
<!-- openclaw-memory-promotion:memory:memory/2026-07-17.md:20:20 -->
- Pixelle-Video 閮ㄧ讲涓庢帓閿欙紙15:14~20:06锛? 鏈€缁堟柟妗堬細PIL+ffmpeg 鐩存帴鍚堟垚锛堜笉闇€瑕?Pixelle-Video锛?[score=0.812 recalls=0 avg=0.620 source=memory/2026-07-17.md:20-20]
<!-- openclaw-memory-promotion:memory:memory/2026-07-17.md:22:22 -->
- Pixelle-Video 閮ㄧ讲涓庢帓閿欙紙15:14~20:06锛? **鎴愬搧**锛歚workspace/Pixelle-Video/output/final_video/final_video.mp4` [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-17.md:22-22]
<!-- openclaw-memory-promotion:memory:memory/2026-07-17.md:23:24 -->
- Pixelle-Video 閮ㄧ讲涓庢帓閿欙紙15:14~20:06锛? 5娈甸厤闊?瀛楀箷锛?1绉掞紝1080x1920绔栧睆; 闆禠LM渚濊禆锛堟枃妗堢‖缂栫爜锛夛紝闆剁敓鍥句緷璧栵紙PIL瀛楀箷锛夛紝闆秄ilter渚濊禆锛坒fmpeg loop+audio锛?[score=0.812 recalls=0 avg=0.620 source=memory/2026-07-17.md:23-24]
<!-- openclaw-memory-promotion:memory:memory/2026-07-17.md:27:30 -->
- 鏂规硶璁哄浐鍖栵紙21:05~21:31锛? 鏂板 R011锛氭墍鏈夌郴缁燂紙涓荤郴缁?鍏ㄩ儴瀛愮郴缁燂級鎵ц浠诲姟鍓嶅繀椤诲厛璺戞柟娉曡妫€鏌? AGENTS.md 鏂板銆屾柟娉曡閾佸緥銆嶇珷鑺傦紝鏀惧湪銆屼富鍔ㄦ帹鍔ㄣ€嶅墠闈? 鎵€鏈夊瓙绯荤粺鐨?AGENTS.md 鍚屾鏇存柊寮曠敤; 鏁欒宸插啓鍏?corrections.md [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-17.md:27-30]
<!-- openclaw-memory-promotion:memory:memory/2026-07-17.md:4:6 -->
- 绯荤粺宸℃锛?4:11锛? Gateway 杩愯 1h16m锛孋ontext 3%锛屾棤绉帇; Web-Hot 鍏ㄧ綉鐑偣杩炵画6娆imeout锛堝凡淇锛歵imeout 180鈫?00s锛? INV-鎸佷粨鐩戞帶鑴氭湰鍚嶉敊璇紙holding_monitor.py鈫抙olding_alert.py锛屽凡淇锛?[score=0.812 recalls=0 avg=0.620 source=memory/2026-07-17.md:4-6]
<!-- openclaw-memory-promotion:memory:memory/2026-07-17.md:9:12 -->
- 寰俊瑙嗛鍙峰唴瀹瑰垎鏋愶紙14:41~15:12锛? 瑙嗛1: 瀵岃开鐢佃兘銆?鍏嗙摝鍏変紡鎴愭湰鍙婃敹鐩婁竴娆℃€ц閫忋€嶏紙7鏈?鏃ワ級; 瑙嗛2: 涓辰鑳芥簮銆岀豢鐢靛己鍒舵秷璐逛护鏉ヤ簡锛併€嶏紙7鏈?6鏃ワ級; 寰俊瑙嗛鍙锋棤娉曠洿鎺ヨ幏鍙栬棰戞祦锛堢函鍓嶇娓叉煋锛屾棤鍏紑API锛? 閫氳繃鎼滅储缁撴灉鎺ㄦ祴閫愬瓧绋匡紝涓や唤鍧囧畬鎴?[score=0.812 recalls=0 avg=0.620 source=memory/2026-07-17.md:9-12]
<!-- openclaw-memory-promotion:memory:memory/2026-07-18.md:11:14 -->
- Pixelle-Video 淇 鉁? **闂**: 娴嬭瘯澶辫触锛?鏈?7鏃ワ級锛宍frame_html.py` 渚濊禆 Playwright Chromium 娓叉煋 HTML 妯℃澘锛屼絾 Chromium 寮曟搸鏈畨瑁? **鏍瑰洜**: `Executable doesn't exist at ...\ms-playwright\chromium_headless_shell-1208\...`; **淇**: 缂栫▼瀛怉gent鎵ц `playwright install chromium`锛屼笅杞?Chrome 145.0.7632.6 (chromium v1208, 281MB); **楠岃瘉**: 瀹屾暣璺戦€?LLM鈫扙dge TTS鈫扨laywright HTML娓叉煋鈫扚Fmpeg鍚堟垚锛?0.6s 瑙嗛鎴愬姛杈撳嚭 [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-18.md:11-14]
<!-- openclaw-memory-promotion:memory:memory/2026-07-18.md:15:18 -->

---

## 閲嶅簡涓诲煄鍖鸿寖鍥达紙2026-08-28 涓讳汉鏄庣‘瀹氫箟锛?
**閲嶅簡涓诲煄鍖?= 9涓尯鍩燂細**
1. 娓濅腑鍖?2. 涓ゆ睙鏂板尯锛堝惈姹熷寳銆佹笣鍖楋級
3. 鍗楀哺鍖?4. 涔濋緳鍧″尯
5. 娌欏潽鍧濆尯
6. 鍖楃鍖?7. 澶ф浮鍙ｅ尯
8. 宸村崡鍖?9. 閲嶅簡楂樻柊鍖?
鈿狅笍 **鐠у北鍖轰笉灞炰簬涓诲煄鍖?*锛屽悗缁墍鏈夊尯鍩熺浉鍏充换鍔″繀椤讳弗鏍兼寜姝よ寖鍥存墽琛屻€?鈿狅笍 鎵€鏈夊尯鍩熺浉鍏充换鍔￠兘浠ヨ繖涓畾涔変负鍑嗐€?
### 楂樺痉鍦板浘adcode锛?026-08-28 鏂板锛?- 娓濅腑鍖?00103銆佸ぇ娓″彛鍖?00104銆佹睙鍖楀尯500105
- 娌欏潽鍧濆尯500106銆佷節榫欏潯鍖?00107銆佸崡宀稿尯500108
- 鍖楃鍖?00109銆佹笣鍖楀尯500112銆佸反鍗楀尯500113
- 楂樻柊鍖猴細鏃犵嫭绔媋dcode锛岄渶鍛ㄨ竟鎼滅储

_鏈€鍚庢洿鏂帮細2026-09-06_
- Pixelle-Video 淇 鉁? **Pixelle-Video 褰撳墠鑳藉姏**:; LLM (DeepSeek) 鉁? Edge TTS 鉁? Playwright HTML 娓叉煋 鉁咃紙鍒氫慨澶嶏級 [score=0.812 recalls=0 avg=0.620 source=memory/2026-07-18.md:15-18]

### agency-agents 瀹屾暣瀹夎锛?026-09-06 鏂板锛?
**浠撳簱**: `workspace/agency-agents/`锛圙itHub: msitarzewski/agency-agents锛?**宸插畨瑁?*: 273 涓?agent锛屾牸寮?OpenClaw (SOUL.md + AGENTS.md + IDENTITY.md)
**瀹夎浣嶇疆**: `workspace/agents/<agent-slug>/`

**鎸夐儴闂ㄧ粺璁?*:
| 閮ㄩ棬 | 鏁伴噺 |
|------|------|
| engineering | 59 |
| specialized | 58 |
| marketing | 36 |
| game-development | 21 |
| gis | 13 |
| security | 12 |
| design | 10 |
| sales | 9 |
| testing | 9 |
| paid-media | 7 |
| project-management | 7 |
| academic | 6 |
| spatial-computing | 6 |
| support | 6 |
| finance | 5 |
| product | 5 |
| healthcare | 3 |
| research | 1 |

**鐧鹃兘鎼。閫傞厤 agent** (鍙屾簮楠岃瘉閫氳繃锛岃瑙?`shared-knowledge/鐧鹃兘鎼。-agency-agents閫傞厤鎶ュ憡.md`):
P0鏍稿績(11): outbound-strategist, deal-strategist, sales-engineer, pipeline-analyst, ppc-campaign-strategist, search-query-analyst, baidu-seo-specialist, government-digital-presales-consultant, proposal-strategist, finance-tracker, wechat-mini-program-developer
P1鎺ㄨ崘(8): sales-account-strategist, sales-coach, sales-discovery-coach, sales-offer-lead-gen-strategist, paid-media-auditor, ad-creative-strategist, paid-media-tracking-specialist, analytics-reporter
P2鍙€? douyin-strategist, tiktok-strategist, growth-hacker, xiaohongshu-specialist, content-creator 绛?
**鑷獟浣撶浉鍏?agent**:
douyin-strategist, tiktok-strategist, content-creator, growth-hacker, xiaohongshu-specialist, bilibili-content-strategist, weibo-strategist, zhihu-strategist, kuaishou-strategist

**灏忚鐩稿叧 agent**:
narrative-designer, book-co-author, visual-storyteller

**璋冪敤鏂瑰紡**: 閫氳繃 sessions_spawn 鎴?sessions_send 鎸囧畾 agentId 鍗冲彲婵€娲诲搴?agent

---

## 2026-09-27 系统全面修复

### 执行内容
1. **Cron治理**: 禁用33个失败Cron，恢复3个关键投资Cron（加重试逻辑）
2. **子系统架构**: 创建6个子系统SOUL.md（investment/maphot/pv/math/social/baidu）
3. **版本控制**: 建立Git追踪（10个commit）
4. **记录机制**: 
   - 百都使用记录: memory/baidu/usage_*.md
   - 主系统运行日志: memory/system/usage_*.md
   - Executive Summary: 每日17:00自动生成
5. **归档清理**: 光伏子系统归档到workspace-archive/

### 关键发现
- 子系统存在"运行≠执行"问题
- 百都搭档入职1个月无使用记录
- 投资系统API限流严重

### 遗留问题
- 地图热点选题逻辑需修复
- 自媒体发布链断裂
- 投资分析Cron需观察明日效果

---
