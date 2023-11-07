/**
 * @descripttion: btwaf防火墙
 * @author: wenrijian
 * @Date: 2021-03-25
 */
var bt_waf = {
	plugin_name: 'btwaf', //插件名称
	overall_config: {}, //全局配置参数
	site_config: {}, //站点配置参数
	waf_table_list: [], //渲染表格专用列表
	site_list: [], //站点列表
	batch_config_sitename: [],
	overall_config: {}, //全局配置参数
	attack_rank: [],
	waf_table_list: [], //渲染表格专用列表
	ip_config_list: [],
	drop_abroad_list: [],
	ua_config_list: [],
	url_config_list: [],
	ban_word_list: [], //违禁词列表
	spider_data_list: [], //某个蜘蛛池列表
	waf_button: false,
	fullscreen: false,
	stringreg: /\\|\*|\"|\“|\”|\'|\‘|\’|\<|\>|\{|\}|\[|\]|\【|\】|\：|\:|\^|\$|\!|\~|\`|\|/g,
	searchData: {},
	time_cycle: [
		{ title: '今日', day: '1' },
		{ title: '昨日', day: '2' },
		{ title: '近7天', day: '7' },
		{ title: '近30天', day: '30' },
	], //周期范围
	ajaxList: {
		get_webshell_info: '获取木马文件列表',
		get_total_all_overview: '获取攻击数据',
		get_all_tu: '获取攻击数据',
		get_total_all: '获取攻击信息',
		get_rule: '获取规则列表',
		get_config: '获取防火墙全局配置',
		get_total_all: '获取防火墙数据',
		get_url_find: '获取URL关键词列表',
		get_ua_white: '获取UA白名单',
		get_ua_black: '获取UA黑名单',
		get_url_white_chekc: '获取API防御数据',
		get_zhizu_list2233: '从云端更新蜘蛛池',
		get_site_rule: '获取网站规则',
		get_site_cdn_header: '设置网站CDN-Header',
		get_site_config_byname: '获取网站配置',
		get_site_disable_rule: '获取网站规则',
		get_log: '获取webshell日志',
		get_logs_list: '获取站点日志列表',
		get_webshell: '获取webshell动态查杀列表',
		get_golbls_cc: '获取URL白名单',
		get_gl_logs: '获取防火墙封锁日志',
		get_safe_logs: '获取防火墙封锁IP列表',
		get_site_config: '获取防火墙站点配置列表',
		get_stop_ip: '获取四层防御状态',
		get_log_send: '获取拦截日志列表',
		get_url_request_mode: '获取URL请求类型拦截',
		get_reg_tions: '获取地区限制列表',
		shell_get_rule: '获取webshell查杀规则列表',
		set_open: '获取防火墙状态',
		start_cc_status: '开启自动模式',
		stop_cc_status: '关闭自动模式',
		set_site_disable_rule: '设置网站规则状态',
		set_site_obj_open: '设置站点状态',
		set_retry: '设置攻击次数拦截',
		set_site_retry: '设置攻击次数拦截',
		set_rule_state: '设置规则状态',
		set_cc_conf: '设置CC配置',
		set_obj_status: '设置响应代码',
		set_site_cc_conf: '设置站点CC配置',
		set_obj_open: '设置全局配置开关',
		set_cc_automatic: '设置自动模式配置',
		set_stop_ip_stop: '停止四层防御',
		set_dingding: '设置钉钉推送',
		set_mail_to: '设置邮箱推送',
		set_stop_ip: '开启四层防御',
		send_baota: '使用宝塔规则库检测文件',
		add_url_white: '添加URL白名单',
		golbls_cc_zeng: '添加URL白名单',
		add_url_black: '添加URL黑名单',
		add_site_rule: '添加网站规则',
		add_ip_black: '添加IP黑名单',
		add_ip_white: '添加IP白名单',
		set_ipv6_back: '添加IP黑名单',
		add_ua_white: '添加UA白名单',
		add_ua_black: '添加UA黑名单',
		add_url_white_chekc: '添加API防御',
		add_url_find: '添加URL关键词',
		add_body_rule: '添加敏感文字替换',
		add_body_intercept: '添加违禁词',
		add_body_site_rule: '添加敏感文字替换',
		add_site_cdn_header: '添加网站CDN-Header',
		add_cnip: '添加禁用IP',
		add_rule: '添加规则',
		add_method_type: '添加请求类型',
		add_header_len: '添加header过滤',
		add_spider: '添加蜘蛛IP',
		add_reg_tions: '添加地区限制',
		add_url_request_mode: '添加URL请求类型拦截',
		save_scan_rule: '保存扫描器规则',
		modify_rule: '保存规则',
		return_site: '扫描站点',
		san_dir: '扫描webshell',
		shell_add_rule: '添加webshell规则',
		clean_waf_drop_ip: '解封全部IP',
		import_data: '导入数据',
		import_body_intercept: '导入违禁词',
		export_body_intercept: '导出违禁词',
		lock_not_webshell: '设置文件误报',
		upload_file_url: '使用第三方规则库检测文件',
		wubao_url_white: '添加URL白名单',
		sync_cnlist: '从云端更新国内IP库',
		shell_del_rule: '删除webshell规则',
		edit_header_len: '修改header过滤',
		remove_waf_drop_ip: '解封IP',
		remove_site_rule: '删除网站规则',
		remove_site_cdn_header: '删除网站CDN-Header',
		remove_url_white: '删除URL白名单',
		remove_url_black: '删除URL黑名单',
		remove_ip_black: '删除IP黑名单',
		remove_ip_white: '删除IP白名单',
		remove_cnip: '删除禁用IP',
		remove_rule: '删除规则',
		remove_log: '清理日志',
		del_ua_black: '删除UA黑名单',
		del_ua_white: '删除UA白名单',
		del_golbls_cc: '删除URL白名单',
		del_ipv6_back: '删除IP黑名单',
		del_url_white_chekc: '删除API防御数据',
		del_body_rule: '删除敏感文字列表',
		del_body_site_rule: '删除敏感文字列表',
		del_url_find: 'URL关键词列表',
		del_webshell_list: '删除动态查杀列表',
		del_method_type: '删除请求类型',
		del_header_len: '删除header过滤',
		del_body_intercept: '删除违禁词',
		del_reg_tions: '删除地区限制',
		del_url_request_mode: '删除URL请求类型拦截',
		empty_body_intercept: '清空违禁词',
		import_ip_data: '导出封锁中IP列表',
		import_ip_black: '导入IP黑名单',
		import_spider: '导入蜘蛛池数据',
		test_waf: '测试防火墙',
		import_sesings: '导入防火墙配置',
		return_is_site: '获取被攻击网站',
		get_report: '获取攻击报告',
		get_id_log: '获取攻击ip信息',
		get_server_name: '获取被攻击站点',
		get_search: '获取搜索信息',
		check_renji: '检测人机验证环境',
		del_yangben: '删除文件',
		add_static_code_config: '添加单URL CC防御',
		edit_cc_uri_frequency: '修改单URL CC防御',
		del_cc_uri_frequency: '删除单URL CC防御',
		del_spider: '删除蜘蛛池IP',
		set_scan_conf: '设置目录扫描防御',
		bckup_sesings: '导出配置',
		get_search_logs: '搜索封锁记录',
	},
	overall_show_config: [
		{ name: 'CC防御', type: 'cc', ps: '防御CC攻击，具体防御参数请到站点配置中调整<a href="https://www.bt.cn/bbs/thread-57581-1-1.html" target="_blank" class="btlink"> &gt;教程</a>' },
		{
			name: '攻击次数拦截',
			type: 'cc_tolerate',
			ps: '封锁连续的恶意攻击请求，请到站点配置中调整阈值<a href="https://www.bt.cn/bbs/thread-57581-1-1.html" target="_blank" class="btlink"> &gt;教程</a>',
			status: '',
			open: '',
		},
		{
			name: 'IP白名单',
			sortId: 1,
			type: 'ip_white',
			ps: '所有规则对IP白名单无效<a href="https://www.bt.cn/bbs/thread-57589-1-1.html" target="_blank" class="btlink"> &gt;教程</a>',
			status: '',
			open: '',
		},
		{ name: 'IP黑名单', sortId: 2, type: 'ip_black', ps: '禁止访问的IP<a href="https://www.bt.cn/bbs/thread-57589-1-1.html" target="_blank" class="btlink"> &gt;教程</a>', status: '', open: '' },
		{ name: '单URL CC防御', type: 'cc_uri_frequency', ps: '单URL的防御CC规则，优先级高于URL白名单', status: '', open: '' },
		{
			name: 'URL白名单',
			sortId: 5,
			type: 'url_white',
			ps: '放行URL地址,在当前URL白名单列表中防火墙将不会进行任何拦截【优先级更高的除外】。<a href="https://www.bt.cn/bbs/thread-57589-1-1.html" target="_blank" class="btlink"> &gt;教程</a>',
			status: '',
			open: '',
		},
		{
			name: 'URL黑名单',
			sortId: 6,
			type: 'url_black',
			ps: '禁止访问的URL地址<a href="https://www.bt.cn/bbs/thread-57589-1-1.html" target="_blank" class="btlink"> &gt;教程</a>',
			status: '',
			open: '',
		},
		{ name: 'UA白名单', sortId: 3, type: 'ua_white', ps: '初始化阶段User-Agent白名单<a href="https://www.bt.cn/bbs/thread-57589-1-1.html" target="_blank" class="btlink"> &gt;教程</a>' },
		{ name: 'UA黑名单', sortId: 4, type: 'ua_black', ps: '初始化阶段User-Agent黑名单<a href="https://www.bt.cn/bbs/thread-57589-1-1.html" target="_blank" class="btlink"> &gt;教程</a>' },
		{
			name: '蜘蛛池',
			type: 'spider',
			ps: '默认放行各大搜索引擎蜘蛛爬取，现有蜘蛛分类：百度、谷歌、360、搜狗、雅虎、必应、头条。<a href="https://www.bt.cn/bbs/thread-57590-1-1.html" target="_blank" class="btlink"> &gt;教程</a>',
			status: '',
			open: '',
		},
		{
			name: '木马查杀',
			type: 'webshell_opens',
			ps: '通过实时访问的文件进行查杀木马,结果在木马隔离箱页面，建议不要关闭此功能。<br><span>注意：如您的正常文件被拉入到隔离箱中，请在隔离箱中加白。</span>',
			status: '',
			open: '',
			note: '注意：如您的正常文件被拉入到隔离箱中，请在隔离箱中加白。',
		},
		{
			name: '非浏览器拦截',
			type: 'is_browser',
			ps: '可以防御爬虫攻击、非浏览器访问、当前将应用于所有网站，如果网站开启CDN 建议不要开启（存在缓存误报）<a href="https://www.bt.cn/bbs/thread-57585-1-1.html" target="_blank" class="btlink"> &gt;教程</a>',
			status: '',
			open: '',
		},
		{
			name: 'HTTP请求过滤',
			type: 'method_type',
			ps: 'HTTP请求类型过滤/请求头过滤/语义分析开关<a href="https://www.bt.cn/bbs/thread-57585-1-1.html" target="_blank" class="btlink"> &gt;教程</a>',
			status: '',
			open: '',
		},
		// 		{name:'状态码过滤',type:'static_code_config',ps:'识别和限制HTTP响应码<a href="https://www.bt.cn/bbs/thread-57585-1-1.html" target="_blank" class="btlink"> &gt;教程</a>',status:'',open:''},
		{
			name: 'SQL注入防御',
			type: 'sql_injection',
			ps: '检测恶意SQL语句、防止数据库因SQL注入导致的恶意篡改、删库、数据泄露<a href="https://www.bt.cn/bbs/thread-57587-1-1.html" target="_blank" class="btlink"> &gt;教程</a><br><span>注意：若您的网站发布的内容本身会包含SQL语句（如：数据库相关教程类文章），开启此防御可能会导致相关内容的发布被拦截</span>',
			note: '注意：若您的网站发布的内容本身会包含SQL语句（如：数据库相关教程类文章），开启此防御可能会导致相关内容的发布被拦截',
		},
		{
			name: '恶意下载防御',
			type: 'get',
			ps: '检测恶意下载，防止备份文件、源代码、其他关键数据被下载<a href="https://www.bt.cn/bbs/thread-57587-1-1.html" target="_blank" class="btlink"> &gt;教程</a><br><span>注意：若您需要通过网站下载备份文件时、若压缩包带有网站名称，开启此防御可能会导致下载文件被拦截，可以通过面板下载</span>',
			note: '注意：若您需要通过网站下载备份文件时、若压缩包带有网站名称，开启此防御可能会导致下载文件被拦截，可以通过面板下载',
		},
		{
			name: '恶意爬虫防御',
			type: 'user-agent',
			ps: '检测恶意爬虫，防止恶意爬虫、访问网站<a href="https://www.bt.cn/bbs/thread-57587-1-1.html" target="_blank" class="btlink"> &gt;教程</a><br><span>注意：若您的网站需要被搜索引擎收录，一定不要把搜索引擎的特征加入当中</span>',
			note: '注意：若您的网站需要被搜索引擎收录，一定不要把搜索引擎的特征加入当中',
		},
		{
			name: 'XSS防御',
			type: 'xss_injection',
			ps: '检测XSS语法，防止网页被恶意篡改、用户信息泄露、权限窃取<a href="https://www.bt.cn/bbs/thread-57587-1-1.html" target="_blank" class="btlink"> &gt;教程</a><br><span>注意：若您的网站发布的内容本身会包含javascipt恶意利用教程,开启此防御可能会导致相关内容的发布被拦截</span>',
			note: '注意：若您的网站发布的内容本身会包含javascipt恶意利用教程,开启此防御可能会导致相关内容的发布被拦截',
		},
		{
			name: '恶意Cookie防御',
			type: 'cookie',
			ps: '检测Cookie中是否包含恶意代码、SQL注入、XSS攻击<a href="https://www.bt.cn/bbs/thread-57587-1-1.html" target="_blank" class="btlink"> &gt;教程</a>',
			note: '注意：如您的Cookie中包含特殊的代码，可能会导致访问被拦截。如出现误报时、点击误报即可',
		},
		{
			name: '恶意扫描器防御',
			type: 'scan',
			ps: '检测恶意扫描器，防止各类扫描器、木马连接工具、访问网站<a href="https://www.bt.cn/bbs/thread-57587-1-1.html" target="_blank" class="btlink"> &gt;教程</a><br><span>注意：若您的网站做安全测试时、可能会被拦截</span>',
			note: '注意：若您的网站做安全测试时、可能会被拦截',
		},
		{
			name: '目录扫描防御',
			type: 'set_scan_conf',
			ps: '防止目录/文件被扫描、通过访问的404状态码进行统计拦截。<br><span>注意：如您的网页很多404图片时、可能会导致访问被拦截</span>',
			note: '注意：如您的网页很多404图片时、可能会导致访问被拦截',
		},
		{ name: '禁止海外访问', type: 'drop_abroad', ps: '禁止中国大陆以外的地区访问站点<a href="https://www.bt.cn/bbs/thread-57588-1-1.html" target="_blank" class="btlink"> &gt;教程</a>' },
		{ name: '禁止境内访问', type: 'drop_china', ps: '禁止大陆地区访问<a href="https://www.bt.cn/bbs/thread-57588-1-1.html" target="_blank" class="btlink"> &gt;教程</a>' },
		// 		{name:'Webshell查杀',type:'webshell_open',ps:'Webshell动态查杀开关<a href="https://www.bt.cn/bbs/thread-57590-1-1.html" target="_blank" class="btlink"> &gt;教程</a>',status:'',open:''},
		{
			name: '恶意文件上传防御',
			type: 'file_upload',
			ps: '检测恶意文件上传，防止被上传木马、防止服务器权限丢失<a href="https://www.bt.cn/bbs/thread-57590-1-1.html" target="_blank" class="btlink"> &gt;教程</a><br><span>注意：若您在文件上传时、文件名带有php 关键词、开启此防御可能会导致IP被封锁</span>',
			status: '',
			open: '',
			note: '注意：若您在文件上传时、文件名带有php 关键词、开启此防御可能会导致IP被封锁',
		},
		{
			name: '日志记录',
			type: 'http_open',
			ps: '默认防火墙只记录1M以内的HTTP拦截数据包、如您需要记录更大的数据包则打开此功能。<a href="https://www.bt.cn/bbs/thread-57590-1-1.html" target="_blank" class="btlink"> &gt;教程</a>',
			status: '',
			open: '',
		},
		{
			name: '敏感文字替换',
			type: 'sensitive_text',
			ps: '替换设置的敏感文字，如果安装了堡塔网站加速则此功能会无效。<a href="https://www.bt.cn/bbs/thread-57590-1-1.html" target="_blank" class="btlink"> &gt;教程</a>',
			status: '',
			open: '',
		},
		{ name: 'URL关键词拦截', type: 'key_words', ps: '从URL中拦截关键词<a href="https://www.bt.cn/bbs/thread-57590-1-1.html" target="_blank" class="btlink"> &gt;教程</a>', status: '', open: '' },
		{
			name: '违禁词拦截',
			type: 'body_intercept',
			ps: '拦截文本中违禁的文字或词组<a href="https://www.bt.cn/bbs/thread-57590-1-1.html" target="_blank" class="btlink"> &gt;教程</a>',
			status: '',
			open: '',
		},
		{
			name: 'API接口防御',
			type: 'api_defense',
			ps: '此功能是当某些接口存在白名单中的情况下，需要对其中一个接口进行CC防御下使用<a href="https://www.bt.cn/bbs/thread-57590-1-1.html" target="_blank" class="btlink"> &gt;教程</a>',
			status: '',
			open: '',
		},
		{ name: 'URL请求类型拦截', type: 'url_request_type_refuse', ps: '单独设置URL拦截请求类型', status: '', open: '' },
		{ name: '人机验证白名单', type: 'golbls_cc', ps: '开启人机验证时候需要不验证某些页面时使用', status: '', open: '' },
		{
			name: '自定义规则拦截',
			type: 'other_rule',
			ps: '检测php代码执行、检测目录探测、检测ssrf探测、及自定义检测<a href="https://www.bt.cn/bbs/thread-57589-1-1.html" target="_blank" class="btlink"> &gt;教程</a><br><span>注意：当前规则可以编辑，默认为GET/POST请求方式都会生效。</span>',
		},
	],
	new_config_arr: {
		//防CC攻击
		anti_cc: ['cc', 'cc_tolerate', 'cc_uri_frequency', 'golbls_cc'],
		//黑白名单
		black_white_list: ['url_white', 'url_black', 'ua_white', 'ua_black', 'ip_white', 'ip_black'],
		//访问过滤
		access_filter: ['is_browser', 'method_type', 'drop_abroad', 'drop_china', 'url_request_type_refuse', 'api_defense', 'spider'],
		//网站漏洞防御
		website_vulne_defense: ['sql_injection', 'xss_injection', 'file_upload', 'get', 'other_rule', 'user-agent', 'cookie', 'scan', 'set_scan_conf', 'webshell_opens', 'http_open'],
		//敏感词
		sensitive_words: ['sensitive_text', 'key_words', 'body_intercept'],
	},
	new_config_arr_name: {
		//防CC攻击
		anti_cc: '防CC攻击',
		//黑白名单
		black_white_list: '黑白名单',
		//访问过滤
		access_filter: '访问过滤',
		//网站漏洞防御
		website_vulne_defense: '网站漏洞防御',
		//敏感词
		sensitive_words: '敏感词',
	},
	site_show_config: [
		{ name: 'CC防御', type: 'cc', ps: '防御CC攻击，具体防御参数请到站点配置中调整' },
		{ name: '攻击次数拦截', type: 'cc_tolerate', ps: '封锁连续的恶意攻击请求，请到站点配置中调整阈值' },
		{ name: 'SQL注入防御', type: 'xss_injection', ps: '检测恶意SQL语句、防止数据库因SQL注入导致的恶意篡改、删库、数据泄露' },
		{ name: 'XSS防御', type: 'post', ps: '检测XSS语法，防止网页被恶意篡改、用户信息泄露、权限窃取' },
		{ name: '恶意文件上传防御', type: 'file_upload', ps: '检测恶意文件上传，防止被上传木马、防止服务器权限丢失', status: '', open: '' },
		{ name: '恶意下载防御', type: 'get', ps: '检测恶意下载，防止备份文件、源代码、其他关键数据被下载' },
		{ name: '恶意爬虫防御', type: 'user-agent', ps: '检测恶意爬虫，防止恶意爬虫、访问网站' },
		{ name: 'Cookie过滤', type: 'cookie' },
		{ name: '禁止海外访问', type: 'drop_abroad' },
		{ name: '禁止境内访问', type: 'drop_china' },
		{ name: '常见扫描器', type: 'scan' },
		{ name: '蜘蛛池', type: 'spider_status', ps: '默认允许的蜘蛛进行爬取' },
		{ name: '使用CDN', type: 'cdn', ps: '该站点使用CDN，启动后方可正确获取客户IP' },
		{ name: '兼容百度CDN', type: 'cdn_baidu', ps: '使用百度CDN时开启或使用其他CDN无法获取真实IP时开启' },
		{ name: '禁止执行PHP的URL', type: 'disable_php_path', ps: '禁止在指定URL运行PHP脚本' },
		{ name: '禁止访问的URL', type: 'disable_path', ps: '禁止访问指定的URL' },
		{ name: '禁止扩展名', type: 'disable_ext', ps: '禁止访问指定扩展名' },
		{ name: '禁止上传的文件类型', type: 'disable_upload_ext', ps: '禁止上传指定的文件类型' },
		{ name: '受保护的URL', type: 'url_tell', ps: '通过自定义参数加密URL地址,参数错误将被拦截' },
		{name:'URL专用过滤',type:'url_rule',ps:"为特定URL地址设置过滤规则"},
		// {name:'敏感文字替换',type:'sensitive_text',ps:'替换设置的敏感文字',status:'',open:''},
		// {name:'防盗链',type:'preventing_hotlinking',ps:'防盗链',status:'',open:''},
	],
	waf_cc_config_list: {
		1: {
			title: '小白模式',
			data: {
				cc_cycle: '60',
				cc_limit: '180',
				cc_endtime: '300',
				increase_wu_heng: '0',
				cc_four_defense: '0',
				cc_auto_mode: '0',
				cc_time: '0',
				cc_retry_cycle: '0',
				cc_enhance_mode: '0',
				cc_increase_type: 'js',
			},
		},
		2: {
			title: '一般模式',
			data: {
				cc_cycle: '60',
				cc_limit: '240',
				cc_endtime: '300',
				increase_wu_heng: '0',
				cc_four_defense: '0',
				cc_auto_mode: '0',
				cc_time: '0',
				cc_retry_cycle: '0',
				cc_enhance_mode: '0',
				cc_increase_type: 'js',
			},
		},
		3: {
			title: '自动模式',
			data: {
				cc_cycle: '60',
				cc_limit: '240',
				cc_endtime: '300',
				increase_wu_heng: '0',
				cc_four_defense: '0',
				cc_auto_mode: '1',
				cc_time: '60',
				cc_retry_cycle: '600',
				cc_enhance_mode: '0',
				cc_increase_type: 'js',
			},
		},
		4: {
			title: '增强模式',
			data: {
				cc_cycle: '60',
				cc_limit: '240',
				cc_endtime: '300',
				increase_wu_heng: '0',
				cc_four_defense: '0',
				cc_auto_mode: '0',
				cc_time: '0',
				cc_retry_cycle: '0',
				cc_enhance_mode: '1',
				cc_increase_type: 'js',
			},
		},
	},
	/**
	 * @descripttion: 主方法
	 */
	init: function () {
		var that = this;
		//获取数据
		var type = bt.get_cookie('btwaf_type');
		if (type) {
			$('.tab-list span[data-type=' + type + ']').addClass('active');
			that.refresh_data_total(type);
		} else {
			$(".tab-list span[data-type='home']").addClass('active');
			that.refresh_data_total('home');
		}
		// 【日志清理】
		$('.ng-waf-box').on('click', '.clear_log', function () {
			var _type = $(this).parents('.ng-item-box').attr('data-type');
			that.clean_site_or_history_log(_type);
		});
		// 【日志清理】
		$('.ng-waf-box').on('click', '.set_default_settings', function () {
			bt.show_confirm('是否恢复站点默认配置', '<span style="color:red">将会清除所有配置,恢复到默认配置,包括URL黑白名单,IP黑白名单...</br></span>', function () {
				$.post('/btwaf/set_default_settings.json', function (res) {
					layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					that.create_site_table();
				});
			});
		});
		//添加地区限制
		$('.ng-waf-box').on('click', '.add_reg_tions', function () {
			that.set_add_reg_tions_view();
		});
		// 单选框点击事件
		$('.ng-waf-box').on('click', '.waf_unselect', function () {
			var _checked = $(this).find('input').prop('checked');
			if (_checked) {
				$(this).find('.waf-icon').removeClass('waf-checked');
				$(this).find('input').prop('checked', false);
			} else {
				$(this).find('.waf-icon').addClass('waf-checked');
				$(this).find('input').prop('checked', true);
			}
		});
		// 扫描木马按钮
		$('.ng-waf-box').on('click', '#san_webshell_event', function () {
			var type = $('[name="dir_path"]').val(),
				path = '';
			if (type == '0') {
				path = $('[name="static_site_list"]').val();
			} else {
				path = $('#san_path').val();
				if (path == '') return layer.msg('扫描地址不能为空!', { icon: 2 });
			}
			that.ajaxTask('san_dir', { path: path }, function (res) {
				that.render_san_webshell({ data: res, path: path });
			});
		});
		// 【木马查杀】选择目录类型
		$('.ng-waf-box').on('change', '[name="dir_path"]', function () {
			if ($(this).val() == '0') {
				$('.input_list_one').css('display', 'inline-block');
				$('.input_list_two').hide();
			} else {
				$('.input_list_two').css('display', 'inline-block');
				$('.input_list_one').hide();
			}
		});
		// 【木马查杀】文件图标按钮
		$('.ng-waf-box').on('click', 'span[data-id="path"]', function () {
			bt.select_path('san_path');
		});
		// webshell菜单
		$('.ng-waf-box').on('click', '.waf_nav_group span', function () {
			var _index = $(this).index(),
				_type = $('.waf_nav_content .waf_nav_item:eq(' + _index + ')').attr('data-type');
			$(this).addClass('active').siblings().removeClass('active');
			$('.waf_nav_content .waf_nav_item:eq(' + _index + ')')
				.addClass('active')
				.siblings()
				.removeClass('active');
			that.refresh_data_webshell(_type);
		});
		// 导出防火墙配置
		$('.ng-waf-box').on('click', '.import_waf_config', function () {
			that.ajaxTask('bckup_sesings', function (res) {
				if (res.status) that.import_or_export_waf_config(true, res.msg);
			});
		});
		// 导入防火墙配置
		$('.ng-waf-box').on('click', '.export_waf_config', function () {
			that.import_or_export_waf_config();
		});
		// 【封锁历史】解封所有按钮
		$('.ng-waf-box').on('click', '.uncover_all', function () {
			layer.confirm('是否要从防火墙解封所有IP', { title: '解封IP地址', closeBtn: 2, icon: 0 }, function () {
				that.ajaxTask('clean_waf_drop_ip', function (res) {
					if (res.status) that.render_history_data();
					layer.msg(res.msg, { icon: res.status ? 1 : 2 });
				});
			});
		});
		// 【封锁历史】一键拉黑
		$('.ng-waf-box').on('click', '.a_key_block', function () {
			layer.confirm('是否要拉黑当前状态为【<span style="color:red">封锁中</span>】的所有IP', { title: '一键拉黑', closeBtn: 2, icon: 0 }, function () {
				that.ajaxTask('import_ip_black', function (res) {
					layer.msg(res.msg, { icon: res.status ? 1 : 2 });
				});
			});
		});
		//【封锁历史】高级搜索
		$('.ng-waf-box').on('click', '.ipCompleteSearch', function (e) {
			var box = $(this).find('.complete_search_view');
			if ($(e.target).hasClass('modeFilter')) {
				if (box.hasClass('hide')) {
					$('.modeFilter').css('color', '#23527c');
					box.removeClass('hide');
					$('#search_start_stop_time').removeAttr('lay-key');
					laydate.render({
						elem: '#search_start_stop_time',
						range: true,
						value: '',
						done: function (value, startdate, endDate) {
							var timeA = value.split(' - ');
							$('#search_start_stop_time').val(value);
						},
					});
				} else {
					box.addClass('hide');
					$('.modeFilter').removeAttr('style');
				}
			}
			$(document).one('click', function () {
				box.addClass('hide');
				$('.modeFilter').removeAttr('style');
			});
			e.stopPropagation();
		});
		//【封锁历史】搜索
		$('.ng-waf-box').on('click', '.ipSearch', function (e) {
			var param = {
				ip: $('.search_ip').val(),
				serach_url: $('.search_url').val(),
				domain: $('.search_domain').val(),
				user_agent: $('.search_user_agent').val(),
			};
			if ($('#search_start_stop_time').val() != '') {
				var time_arr = $('#search_start_stop_time').val().split(' - ');
				param['start_time'] = new Date(time_arr[0] + ' 00:00:00').getTime() / 1000;
				param['end_time'] = new Date(time_arr[1] + ' 23:59:59').getTime() / 1000;
				param['time_reverse'] = 1;
			}
			that.render_history_data({ url: '/plugin?action=a&s=get_search_logs&name=btwaf', param: param });
		});
		// 【封锁历史】导出记录
		$('.ng-waf-box').on('click', '.export_block_list', function () {
			window.location.href = '/btwaf/index?export=export';
		});
		// 【封锁历史】导出ip
		$('.ng-waf-box').on('click', '.export_block_list_ip', function () {
			that.export_block_view();
		});

		//排行榜拉黑操作
		$('.ng-waf-box').on('click', '.add_ip_black', function () {
			var ip = $(this).attr('data-ip');
			var ipv4Range = '';
			if (bt.check_ip(ip)) {
				ipv4Range =
					'<div class="mt10"><input type="checkbox" id="ipRangeInsulate"/><label for="ipRangeInsulate" style="font-weight: 400;margin: 0 0 0 5px;cursor: pointer;">是否拉黑整个IP段？</label></div>';
			}
			layer.confirm('是否将 <span style="color:red">' + ip + '</span> 添加到IP黑名单？' + ipv4Range, { title: '加入IP黑名单', closeBtn: 2 }, function () {
				if (bt.check_ip(ip)) {
					var isCheck = $('#ipRangeInsulate').is(':checked');
					if (!isCheck) {
						that.ajaxTask('add_ip_black', { start_ip: ip, end_ip: ip }, function (res) {
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
						});
					} else {
						var ipRange = ip.replace(/\d{1,3}$/, '0/24');
						bt_waf.http({
							method: 'import_data',
							data: { s_Name: 'ip_black', pdata: ipRange },
							success: function (res) {
								layer.msg(res.status ? '操作成功' : '添加失败', { icon: res.status ? 1 : 2 });
							},
						});
					}
				} else {
					that.ajaxTask('set_ipv6_back', { addr: ip }, function (res) {
						layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					});
				}
			});
		});
		$('.ng-waf-box').on('click', '.add_url_black', function () {
			var url = $(this).data('ip');
			layer.confirm('是否将 <span style="color:red">' + url + '</span> 添加到URL黑名单？', { title: '加入URL黑名单', closeBtn: 2 }, function () {
				that.ajaxTask('add_url_black', { url_rule: url }, function (res) {
					layer.msg(res.msg, { icon: res.status ? 1 : 2 });
				});
			});
		});
		//首页解封ip
		$('.ng-waf-box').on('click', '.remove_waf_drop_ip', function () {
			var _ip = $(this).data().ip;
			layer.confirm('是否要从防火墙解封IP【' + _ip + '】', { title: '解封IP地址', closeBtn: 2, icon: 0 }, function () {
				that.ajaxTask('remove_waf_drop_ip', { ip: _ip }, function (res) {
					layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					$.post('/btwaf/get_total_all_overview.json', function (res) {
						that.create_block_table(res);
					});
				});
			});
		});
		//首页解封ip
		$('.ng-waf-box').on('click', '.attack_log', function () {
			var ip = $(this).parents('tr').data().data[0],
				start_time = $(this).parents('tr').data().start_time.split(' ')[0],
				end_time = $(this).parents('tr').data().end_time.split(' ')[0];
			that.ajaxTask('get_search', { server_name: ip, type: 4, start_time: start_time, end_time: end_time }, function (res) {
				layer.open({
					type: 1,
					title: '恶意IP -【' + ip + '】拦截记录',
					area: ['930px', '510px'],
					closeBtn: 2,
					shadeClose: false,
					content:
						'<div class="ip_logs_table">\
        			            <div class="divtable ng-fixed" style="width:100%;padding:15px">\
        						    <table class="table table-hover">\
        								<thead>\
        									<tr>\
        										<th width="150px">攻击时间</th>\
        										<th width="100px">攻击IP</th>\
        										<th width="100px">被保护网站</th>\
        										<th width="200px">URI</th>\
        										<th width="100px">保护类型</th>\
        										<th width="100px" style="text-align:right" width="10%">操作</th>\
        									</tr>\
        								</thead>\
        							</table>\
        						</div>\
        						<div id="report_logs_table" class="divtable" style="width:100%;height:460px;overflow:auto;padding:15px;scrollbar-width:thin;">\
        						    <table class="table table-hover">\
        								<thead>\
        									<tr>\
        										<th width="150px">攻击时间</th>\
        										<th width="100px">攻击IP</th>\
        										<th width="100px">被保护网站</th>\
        										<th width="200px">URI</th>\
        										<th width="100px">保护类型</th>\
        										<th width="100px" style="text-align:right" width="10%">操作</th>\
        									</tr>\
        								</thead>\
        								<tbody id="reportLogBody"></tbody>\
        							</table>\
        							<div class="page" id="reportLogTablePage"></div>\
        						</div>\
        					</div>',
					success: function (layero, index) {
						$('#reportLogBody').empty();
						that.render_report_table(res.msg.data, 'uri');
						$('#reportLogTablePage').html(res.msg.page);
						$('.ip_logs_table').on('click', '#reportLogTablePage a', function (e) {
							e.stopPropagation();
							e.preventDefault();
							var _p = $(this)
								.attr('href')
								.match(/p=([0-9]*)/)[1];
							that.ajaxTask('get_search', { server_name: ip, type: 4, start_time: start_time, end_time: end_time, p: _p }, function (res) {
								$('#reportLogBody').empty();
								that.render_report_table(res.msg.data, 'uri');
								$('#reportLogTablePage').html(res.msg.page);
							});
						});
					},
				});
			});
		});
		$('.ng-waf-box').on('click', '.dynamic_log', function (e) {
			var data = $(this).parents('tr').data().data;
			that.ajaxTask('get_id_log', { id: data.id }, function (res) {
				var row = res.msg[0];
				that.create_details(row);
			});
		});
		// 首页详情
		$('.ng-waf-box').on('click', '.ng-maximize, .ng-minsize', function () {
			var _type = $(this).data('type');
			// if (_type) {
			// 	$('.ng-waf-box .tab-list span[data-type="' + _type + '"]').click();
			// } else {
			// 	$('.ng-waf-box .tab-list span').eq(0).click();
			// }
			if (_type === 'attack_map') {
				if ($(this).hasClass('ng-maximize')) {
					that.refresh_data_total(_type);
				} else {
					that.refresh_data_total('home');
				}
			}
		});
		//菜单切换
		$('.tab-list .tabs-item').click(function () {
			var _type = $(this).data('type');
			$(this).addClass('active').siblings('.active').removeClass('active');
			bt.set_cookie('btwaf_type', _type);
			that.refresh_data_total(_type);
			layer.closeAll('tips');
		});

		//设置经纬度
		$('.ng-waf-box').on('click', '.set_longitude_and_latitude', function () {
			that.set_longitude_and_latitude();
		});
		//全屏
		$('.ng-waf-box').on('click', '.ng-window', function () {
			var fullarea = document.getElementById('map');
			if (that.fullscreen) {
				// 退出全屏
				if (document.exitFullscreen) {
					document.exitFullscreen();
				} else if (document.webkitCancelFullScreen) {
					document.webkitCancelFullScreen();
				} else if (document.mozCancelFullScreen) {
					document.mozCancelFullScreen();
				} else if (document.msExitFullscreen) {
					document.msExitFullscreen();
				}
			} else {
				// 进入全屏
				if (fullarea.requestFullscreen) {
					fullarea.requestFullscreen();
				} else if (fullarea.webkitRequestFullScreen) {
					fullarea.webkitRequestFullScreen();
				} else if (fullarea.mozRequestFullScreen) {
					fullarea.mozRequestFullScreen();
				} else if (fullarea.msRequestFullscreen) {
					// IE11
					fullarea.msRequestFullscreen();
				}
			}
			that.fullscreen = !that.fullscreen;
		});
		//报告详情
		$('.ng-waf-box').on('click', '.getIdLog ,.getUriLog', function (e) {
			var data = $(this).parents('tr').data().ip_list,
				item = $(this).parents('tr').data().data[0];
			$(this).hasClass('getIdLog') ? that.create_report_site(item, data) : that.create_report_URI(item, data);
		});
		//报告搜索类型选择
		$('.ng-waf-box').on('click', '.protect_input ul li a', function (e) {
			$(this).parents('ul').siblings().children('b').attr('value', $(this).attr('value')).html($(this).html());
			if ($(this).parents('ul').attr('aria-labelledby') == 'server_type') {
				if ($(this).attr('value') == 'time') {
					$('.search_time').show();
					$('.search_data').hide();
				} else {
					$('.search_time').hide();
					$('.search_data').show();
				}
			}
		});
		//查询报告
		$('.ng-waf-box').on('click', '.report_search', function (e) {
			var ip = $('#server_name b').attr('value'),
				type = $('#server_type b').attr('value'),
				data = type == 'time' ? $('#search_time').val() : $('#search_data').val(),
				name = type == 'time' ? '#search_time' : '#search_data',
				server = ip == 'all' ? 'isall' : 'server_name';
			if (data == '') return layer.tips('请输入搜索条件', name, { tips: [1, '#e62214'] });
			var obj = {
				is_all: ip == 'all' ? 1 : undefined,
				server_name: ip == 'all' ? undefined : ip,
				type: type == 'time' ? 4 : type,
				start_time: type == 'time' ? data.split(' - ')[0] : undefined,
				end_time: type == 'time' ? data.split(' - ')[1] : undefined,
				serach: type == 'time' ? undefined : data,
			};
			that.searchData = obj;
			that.create_search_table(obj, 1);
		});
		//报告分页切换
		$('.ng-waf-box').on('click', '#searchTablePage a', function (e) {
			e.stopPropagation();
			e.preventDefault();
			var _p = $(this)
				.attr('href')
				.match(/p=([0-9]*)/)[1];
			that.create_search_table(that.searchData, _p);
		});
		//搜索列表详情和http
		$('.ng-waf-box').on('click', '#ng_search_table .report_details', function (e) {
			var data = $(this).parents('tr').data().data;
			that.ajaxTask('get_id_log', { id: data.id }, function (res) {
				var row = res.msg[0];
				that.create_details(row);
			});
		});
		$('.ng-waf-box').on('click', '#ng_search_table .report_HTTP', function (e) {
			var data = $(this).parents('tr').data().data;
			that.ajaxTask('get_id_log', { id: data.id }, function (res) {
				var row = res.msg[0];
				that.create_HTTP(row);
			});
		});
		//报告切换
		$('.ng-waf-box').on('click', '.ng-second-head span', function (e) {
			var index = $(this).index();
			$(this).addClass('active').siblings().removeClass('active');

			if (index == 2) {
				$('.ng_protect_search').show();
				$('.ng_protect_table').hide();
				$('.server_name ul').empty().append('<li class="active"><a role="menuitem" tabindex="-1" href="javascript:;" value="all">所有站点</a></li>');
				that.ajaxTask('get_server_name', function (res) {
					$.each(res, function (index, item) {
						$('.server_name ul').append('<li><a role="menuitem" tabindex="-1" href="javascript:;" value="' + item + '">' + item + '</a></li>');
					});
					$('#search_time').removeAttr('lay-key');
					laydate.render({
						elem: '#search_time',
						range: true,
						value: '',
						done: function (value, startdate, endDate) {
							var timeA = value.split(' - ');
							$('#search_time').val(value);
						},
					});
				});
			} else {
				$('.ng_protect_search').hide();
				$('.ng_protect_table').show();
				that.get_report();
			}
		});
		// 模拟攻击
		$('.ng-waf-box').on('click', '.waf_all_text', function () {
			layer.open({
				type: 1,
				title: '模拟攻击',
				area: '600px',
				closeBtn: 2,
				content:
					'<div id="bt_waf_test_table" class="pd20 bt_table" style="padding-bottom:30px;">\
                    			<div class="divtable mtb10" style="max-height:300px">\
                    				<table class="table table-hover">\
                    					<thead>\
                    						<tr>\
                    							<th width="300px"><span data-index="1"><span>模拟攻击网站列表</span></span></th>\
                    							<th width="80px"><span data-index="2"><span>防护情况</span></span></th>\
                    							<th width="80px" style="text-align:right"><span data-index="3"><span>操作</span></span></th>\
                    						</tr>\
                    					</thead>\
                    					<tbody id="waf_test_table_body"></tbody>\
                    				</table>\
                    			</div>\
                    		</div>\
                    		 <ul class="mtl0 c7" style="font-size: 13px;position:relative;bottom:20px;padding-right: 40px;">\
                    		    <li style="list-style:inside disc;margin-top:5px" style="">此模拟攻击为:黑客进行SQL注入获取数据库权限.不会影响业务的正常运行\
                    		    </li>\
                    		    <li style="list-style:inside disc;margin-top:5px">如果你的IP在IP白名单中测试则无效果\
                    		    </li>\
                    		    <li style="list-style:inside disc;margin-top:5px">如需测试其他的网站可使用【http://网站域名/?id=/etc/passwd】进行攻击\
                    		    </li>\
                    		    <li style="list-style:inside disc;margin-top:5px">返回拦截信息则表示拦截成功,如发现未拦截,建议更新至最新版\
                    		    </li>\
                    		    <li style="list-style:inside disc;margin-top:5px">如有疑问请联系宝塔运维\
                    		    </li>\
        	                </ul>',
				success: function (index, layers) {
					that.ajaxTask('return_is_site', function (res) {
						$.each(res, function (index, item) {
							$('#waf_test_table_body').append(
								$(
									'<tr>\
					                <td><a href="' +
										item +
										'" target="_blank" class="btlink local_attack">' +
										(item.length >= 45 ? item.slice(0, 45) + '...' : item) +
										'</a></td>\
					                <td><span class="waf_unselect"><i class="waf-icon waf-icon-ok waf-checked"><span class="glyphicon glyphicon-ok" aria-hidden="true" title=""></span></i><input type="checkbox" checked="">&nbsp;&nbsp;防护中</span></td>\
                                    <td style="text-align: right;">\
                                        <a href="' +
										item +
										'" target="_blank" class="btlink" >查看防护效果</a>\
                                    </td>\
                                </tr>'
								).data({ data: item, index: index })
							);
						});
					});
				},
				cancel: function (index, layero) {
					// that.refresh_data_total('overall');
				},
			});
		});
		// 选择框
		$('.ng-waf-box').on('click', '.dropdown .btn', function (e) {
			var $menu = $(this).next();
			$('.dropdown-menu').not($menu).slideUp(300);
			$menu.slideToggle(300);
			$(document).one('click', function () {
				$menu.slideUp(300);
			});
			e.stopPropagation();
		});
		$('.ng-waf-box').on('click', '.dropdown .dropdown-menu li', function () {
			$(this).addClass('active').siblings('.active').removeClass('active');
			$(this).parent().slideUp(300);
		});

		//监控报表 查看报告
		$('.ng-waf-box').on('click', '.view_report', function () {
			var currtime = Date.parse(new Date()); //当前时间戳
			var timeVal = $('#waf_time_choose').val(),
				stime = '',
				etime = '';
			if (timeVal && !$('#waf_time_choose').parent().find('span').hasClass('on')) {
				stime = timeVal.split(' - ')[0];
				etime = timeVal.split(' - ')[1];
			}
			if ($('#waf_time_choose').parent().find('span').eq(0).hasClass('on')) {
				stime = that.getNextDate(currtime, -1);
				etime = that.getNextDate(currtime, -1);
			}
			window.open('/btwaf/content_report.html' + (stime && etime ? '?stime=' + stime + '&etime=' + etime : ''));
		});
	},
	/**
	 * @descripttion: 获取站点配置
	 */
	get_site_config: function (callback) {
		var that = this;
		that.ajaxTask('get_site_config', function (res) {
			if (callback) callback(res);
		});
	},
	/**
	 * @descripttion: 创建网页视图
	 */
	refresh_data_total: function (index) {
		var that = this,
			_view = $('.ng-item-box').attr('data-type');
		if (index === 'overall') {
			//固定顶部tab
			$('.ng-item')
				.prev()
				.css({
					position: 'fixed',
					'z-index': 1,
					background: 'rgb(241 241 241)',
					width: $('.ng-item').width(),
					padding: '15px 0',
					height: 'auto',
					'border-radius': '0',
					'margin-bottom': '15px',
				})
				.addClass('none_shadow')
				.removeClass('mtb15')
				.find('.tab-list')
				.css({
					'border-radius': '4px',
				})
				.addClass('show_shadow');
			$('.ng-item').css({
				'padding-top': '60px',
			});
			$('.ng-item').parent().css({
				display: 'flex',
				'flex-direction': 'column',
				'margin-bottom': '15px',
			});
		} else {
			$('.ng-item').prev().removeAttr('style').removeClass('none_shadow').addClass('mtb15').find('.tab-list').removeAttr('style').removeClass('show_shadow');
			$('.ng-item').removeAttr('style');
			$('.ng-item').parent().removeAttr('style');
		}
		$.get('/btwaf/static/js/echarts.min.js', function () {
			switch (index) {
				case 'home':
					var loadA = bt.load('正在获取防火墙数据');
					$.get('/btwaf/static/js/world_fix.js', function () {
						if (_view !== index) $('.ng-item').html($('#home').html());
						$('.ng-waf-box .ng-maximize').attr('data-type', $('.ng-waf-title').eq(1).attr('data-type'));
						$.post('/btwaf/get_all_tu.json', function (res) {
							that.attack_rank = res.gongji;
							that.create_attack_rank(res);
							that.create_attack_tendency(res);
							that.create_dynamic_table(res);
						});
						$.post('/btwaf/get_total_all_overview.json', function (res) {
							loadA.close();
							that.create_block_table(res);
							that.create_attack_list(res);
							that.create_attack_map(res);
							$('.day_intercept').html(res.map['24_day_count']);
							if (res.map['24_day_count'] >= 100) {
							    layer.tips('<span>注意：当天拦截的攻击超过100次！</span>', '.day_intercept', {
                                  tips: [2, '#FCB958'],
                                  time: 0,
                                  closeBtn:1,
                                  success: function () {
                                       $(".layui-layer-tips .layui-layer-setwin").css({'top':'11px','right':'10px'}); //按钮位置 
                                    //   $(".layui-layer-tips .layui-layer-setwin a").removeClass('layui-layer-close1').addClass('layui-layer-close2'); //按钮样式 
                                  }
                                }); 
								// layer.tips('<span>注意：当天拦截的攻击超过100次！</span>', '.day_intercept', { tips: [2, '#FCB958'], time: 0 }); // 原弹窗
								$('.day_intercept').css('color', '#FCB958');
								// $('.logo_mask,.ng-logo').css('background','url(static/img/ng-waf/ng-logo1.png) no-repeat center center')
								// $('.ng-logo').prop('title','当天拦截的攻击超过100次！')
							}
						});
						that.ajaxTask('get_total_all', function (res) {
							that.waf_button = res.open;
							$('.protect_day')
								.html(res.webshell)
								.addClass(res.webshell ? 'color-red' : 'color-green');
							if (res.webshell) {
								$('.protect_day').click(function () {
									$('.tab-list .tabs-item').eq(4).click();
								});
							} else {
								$('.protect_day').unbind('click');
							}
							$('.all_intercept').html(res.total.total);
							$.each(res.total.rules, function (index, item) {
								if (item.key == 'cc') $('.cc_defense').html(item.value);
							});
						});
					});
					break;
				case 'overall':
					if (_view != index) $('.ng-item').html($('#overall').html());
					// that.render_overall_data();
					that.new_render_overall_data();
					// that.ajaxTask('get_total_all',function(res){
					// 		$('#waf_swicth_all').prop('checked',res.open).parent().parent().parent().addClass(res.open ? 'bg-green' : 'bg-red')
					// });
					break;
				case 'site':
					if (_view != index) $('.ng-item').html($('#site').html());
					that.create_site_table();
					break;
				case 'webshell':
					if (_view != index) $('.ng-item').html($('#webshell').html());
					// that.render_san_webshell({data:[]})
					that.render_webshell_list();
					//获取可查杀的站点
					that.ajaxTask('return_site', function (res) {
						var _option = '',
							rdata = res.msg;
						for (var i in rdata) {
							_option += '<option value="' + rdata[i] + '">' + i + '</option>';
						}
						$('[name="static_site_list"]').html(_option);
					});
					// 规则列表>>>添加webshell规则
					$('.add_webshell_rule').click(function () {
						layer.open({
							type: 1,
							title: '添加规则',
							area: ['345px', '220px'],
							closeBtn: 2,
							shadeClose: false,
							btn: ['确认', '取消'],
							content:
								'<div class="waf-form">\
									<div class="waf-line"  style="margin-bottom: 0;">\
										<span class="name-l" style="width:30px !important;">规则</span>\
										<div class="info-r">\
											<textarea name="webshell_rule" style="border:1px solid #ccc;border-radius:2px;width:220px;line-height: 15px;height: 75px;"></textarea>\
										</div>\
									</div>\
								</div>',
							success: function (layero, index) {
								layero.find('.layui-layer-content').css('overflow', 'visible');
							},
							yes: function (index, layers) {
								var _rule = $('[name="webshell_rule"]').val();
								if (_rule == '') return layer.msg('规则不能为空!', { icon: 2 });
								that.ajaxTask('shell_add_rule', { rule: _rule }, function (res) {
									if (res.status) {
										layer.close(index);
										that.refresh_data_webshell('rule_list');
									}
									layer.msg(res.msg, { icon: res.status ? 1 : 2 });
								});
							},
						});
					});
					break;
				case 'reg_tions':
					if (_view != index) $('.ng-item').html($('#reg_tions').html());
					that.render_regional_restrictions();
					break;
				case 'history':
					if (_view != index) $('.ng-item').html($('#history').html());
					that.render_history_data();
					break;
				case 'alarm':
					if (_view != index) $('.ng-item').html($('#alarm').html());
					that.render_alarm_data();
					break;
				case 'logs':
					if (_view != index) $('.ng-item').html($('#logs').html());
					that.get_gl_table_page();
					break;
				case 'ng_waf_map':
					$('body svg').remove();
					if (_view != index) $('.ng-item').html($('#ng_waf_map').html());
					$.get('/btwaf/static/js/attack-map.min.js', function (res) {
						$.get('../static/js/public.js', function (res) {
							that.create_map_details();
							that.intercept_trend_chart();
						});
					});
					break;
				case 'ng_waf_data_report':
					if (_view != index) $('.ng-item').html($('#ng_waf_data_report').html());
					$('#waf_time_choose').removeAttr('lay-key');
					laydate.render({
						elem: '#waf_time_choose',
						range: true,
						value: '',
						done: function (value, startdate, endDate) {
							if (!value) {
								that.get_report();
								return false;
							}
							$('#waf_time_choose').val(value);
							that.get_report();
						},
					});
					that.get_report();
					break;
				case 'attack_map':
					$.get('/btwaf/static/js/world_fix.js', function () {
						$('body svg').remove();
						if (_view != index)
							$('.ng-item').html('<div class="col-xs-12 col-sm-12 col-md-6 ng-waf-content max_content" style="width: 100%;height: auto;margin-top: 0;">' + $('#attack_map').html() + '</div>');
						$('.max_content .ng-border').css('margin-left', '0');
						$('.max_content .ng-waf-info').css('height', '605px');
						$('.max_content #ng-world').css('height', '600px').empty().removeAttr('_echarts_instance_');
						$('.max_content .ng-ip-list').css('height', '600px');
						$('.max_content .ng-maximize').addClass('ng-minsize').removeClass('ng-maximize').css('right', '25px');
						$.post('/btwaf/get_total_all_overview.json', function (res) {
							that.create_attack_list(res);
							that.create_attack_map(res);
						});
					});
					break;
			}
		});
	},
	/**
	 * @descripttion: 创建封锁列表
	 * @params obj 配置数据
	 */
	create_block_table: function (obj) {
		var that = this;
		$('#blockTableBody').empty();
		bt_tools.table({
			el: '#blockTableBody',
			height: '183px',
			default: '当前数据为空',
			data: obj.day24_lan.info,
			column: [
				{
					title: '开始时间',
					width: '100px',
					template: function (item) {
						return '<span>' + item.time_localtime.substring(5, item.time_localtime.length) + '</span>';
					},
				},
				{
					title: 'IP',
					width: '100px',
					template: function (item) {
						return '<a class="btlink add_ip_black" data-ip="' + item.ip + '">' + that.escapeHTML(item.ip) + '</a>';
					},
				},
				{
					fid: 'ip_country',
					title: 'IP归属地',
					width: '100px',
					template: function (item) {
						return '<span>' + that.render_ip_country(item) + '</span>';
					}
				},
				{
					fid: 'server_name',
					title: '站点',
					width: '106px',
				},
				{
					title: '状态',
					width: '70px',
					template: function (item) {
						return '<span class="' + (item.is_status ? 'red' : '') + '">' + (item.is_status ? '封锁中' : '已解封') + '</span>';
					},
				},
				{
					fid: 'blocking_time',
					title: '封锁时间',
					width: '80px',
				},
				{
					title: '操作',
					align: 'right',
					width: '90px',
					template: function (item) {
						return (
							'<span><span data-ip="' +
							item.ip +
							'" class="' +
							(item.is_status ? 'remove_waf_drop_ip green' : '') +
							'">' +
							(item.is_status ? '解封' : '--') +
							'</span>&nbsp;&nbsp;|&nbsp;&nbsp;\
						<a class="btlink add_ip_black" data-ip="' +
							item.ip +
							'" >拉黑</a></span>'
						);
					},
				},
			],
		});
		$('.day-block-ip').html('<span>24小时ip封锁数</span><span>' + obj.day24_lan.day_count + '</span>');
		$('.blocking-ip').html('<span>正在封锁的IP</span><span>' + obj.day24_lan.is_count_ip + '</span>');
	},
	/**
	 * @descripttion: 创建攻击地图
	 * @params obj 配置数据
	 */
	create_attack_map: function (obj) {
		var that = this,
			_map = [];
		$.each(obj.map.info, function (index, item) {
			var _list = { name: item[0], value: item[1] };
			_map.push(_list);
		});
		//生成地图
		var ng_world = echarts.init(document.getElementById('ng-world'));
		var option = {
			title: {
				left: 'center',
				top: 'top',
			},
			tooltip: {
				trigger: 'item',
				formatter: function (params) {
					var a;
					var value = (params.value + '').split('.');
					value[0] == 'NaN'
						? (a = '国家：' + params.name)
						: (a = '国家:' + params.name + ' </br> ' + '时间:' + that.attack_rank[6][0].substring(0, 10) + '&nbsp;-&nbsp;' + that.attack_rank[0][0].substring(0, 10) + ' </br> ' + '攻击次数:' + value);
					return a;
				},
			},
			grid: {
				top: 70,
				bottom: 40,
				left: 0,
				right: 0,
			},
			visualMap: {
				min: 0,
				max: 100,
				left: -200,
				range: null,
				inRange: {
					color: ['#EBF3FC', '#92BDEE', '#3887E0'],
				},
			},
			series: [
				{
					name: 'World Population (2010)',
					type: 'map',
					mapType: 'world',
					zoom: 1.2,
					itemStyle: {
						emphasis: {
							borderColor: '#ffffff',
							areaColor: ' #20a53a',
						},
						normal: {
							borderColor: '#ffffff',
							areaColor: '#E6E6E6',
						},
					},
					data: _map,
				},
			],
		};
		ng_world.setOption(option);
		window.addEventListener('resize', function () {
			ng_world.resize();
		});
	},

	/**
	 * @description 返回服务器当前经纬度
	 * @return callback
	 */
	getServerLongitude: function (callback) {
		$.post('/btwaf/get_server_longitude.json', function (res) {
			if (res.status) callback(res);
		});
	},
	getAttackMap: function (callback) {
		$.post('/btwaf/gongji_map.json', function (res) {
			if (res.status) callback(res);
		});
	},

	/**
	 * @descripttion 创建地图框架
	 */
	create_map_frame: function (center) {
		var map = L.map('map', { attributionControl: false, zoomControl: false }).setView(center, 3);
		// 设置地图瓦块
		L.control
			.zoom({
				position: 'topright',
				zoomInTitle: '放大',
				zoomOutTitle: '缩小',
				maxZoom: 7, // 设置地图最大缩放级别
				minZoom: 3, // 设置地图最小缩放级别
			})
			.addTo(map);
		L.tileLayer('https://mts.bt.cn/{z}/{y}/{x}?x={x}&y={y}&z={z}', {
			maxZoom: 7, // 设置地图最大缩放级别
			minZoom: 3, // 设置地图最小缩放级别
		}).addTo(map);
		return map;
	},

	mapInfo: null,
	/**
	 * @descripttion 渲染攻击地图
	 */
	create_map_details: function () {
		var that = this;
		$('#map').empty();
		that.getServerLongitude(function (res) {
			if (res.status) {
				var data = res.msg;
				var longitude = data.longitude,
					latitude = data.latitude,
					ipAddress = data.ip_address;
				that.mapInfo = that.create_map_frame([latitude, longitude]); // 创建地图框架
				$('.ng-mycenter').html('当前经度:' + longitude + '&nbsp当前纬度:' + latitude);
				that.getAttackMap(function (rdata) {
					that.render_map_details([longitude, latitude, ipAddress], rdata.msg);
				});
			} else {
				layer.msg('无法获取出口Ip失败，请检查网络是否连接!', { icon: res.status ? 1 : 2 });
				// that.render_map_details(undefined,[])
				$('.ng-mycenter').css('color', 'red').html('无法获取经纬度,请点击设置。');
			}
		});
	},
	// ip_country_str: function (str) {
	// 	str = str == '台湾' || str == '香港' || str == '澳门' ? '中国' + str : str;
	// 	return str;
	// },
	// 渲染IP归属地
	render_ip_country: function (item) {
		return  (item.ip_country === '中国' && item['ip_subdivisions'] ? ' ' + item.ip_subdivisions + (item['ip_city'] && item.ip_subdivisions !== item.ip_city ? ' ' + item.ip_city : '')  : item.ip_country);
	},
	intercept_trend_chart: function () {
		var that = this;
		$('#map').append('<div id="intercept">\
			<div class="day-intercept">\
				<span class="icon-intercept icon-day-intercept"></span>\
				<div>\
					<div class="intercept-title">今日拦截</div>\
					<div class="intercept-num"></div>\
				</div>\
			</div>\
			<div class="all-intercept">\
				<span class="icon-intercept icon-all-intercept"></span>\
				<div>\
					<div class="intercept-title">总拦截</div>\
					<div class="intercept-num"></div>\
				</div>\
			</div>\
		</div>\
		<div class="intercept-trend-chart">\
			<div class="img-intercept-trend-chart"></div>\
			<div id="intercept-trend-chart"></div>\
		</div>\
		<div class="attack-source-box">\
			<div class="img-attack-source"></div>\
			<div id="attack-source-cont"></div>\
		</div>\
		<div class="site-block-box">\
			<div class="img-site-block"></div>\
			<div id="site-block-cont"></div>\
		</div>\
		<div class="defense-dynamics-box">\
			<div class="img-defense-dynamics"></div>\
			<div id="defense-dynamics-cont"></div>\
		</div>');
		$.get('/btwaf/static/js/world_fix.js', function () {
			$.post('/btwaf/get_all_tu.json', function (res) {
				var top5 = '',
					_dynamic_html = '';
				$.each(res.server_name_top5, function (index, item) {
					top5 +=
						'<div class="item">\
						    <span>' +item[0] +'</span>\
							<span>' +item[1] +'次</span>\
						</div>';
				});
				$('#site-block-cont').html('<div class="cont">' + top5 + '</div>');
				that.create_attack_tendency1(res);
				var _dynamic = res.dongtai;
				$.each(_dynamic, function (index, item) {
					_dynamic_html +=
						'<div class="item">\
						    <span>' + item.time_localtime +'</span>\
							<span>' +item.filter_rule +'</span>\
							<span>' + that.render_ip_country(item) + '</span>\
							<span>' +(that.escapeHTML(item.ip) + '攻击了网站' + item.server_name +'，已被拦截，触发规则是：' + that.escapeHTML(item.filter_rule)) +
						    '</span>\
						</div>';
				});
				$('#defense-dynamics-cont').html('<div class="cont"><div class="item"><span>时间</span><span>过滤器</span><span>IP归属地</span><span>内容</span></div>' + _dynamic_html + '</div>');
			});
		});
		that.ajaxTask('get_total_all', function (res) {
			$('.all-intercept .intercept-num').html(res.total.total);
		});
		$.post('/btwaf/get_total_all_overview.json', function (res) {
			var html = '';
			$.each(res.map.top10_ip, function (index, item) {
				html +=
					'<div class="item">\
						<span> '+that.escapeHTML(item[0]) +'</span>\
						<span>' + that.render_ip_country({ip_country: item[2],ip_subdivisions: item[3],ip_city: item[4]}) +'</span>\
						<span>' +item[1] +'次</span>\
					</div>';
			});
			$('.day-intercept .intercept-num').html(res.map['24_day_count']);
			$('#attack-source-cont').html('<div class="cont">' + html + '</div>');
		});
	},
	/**
	 * @descripttion: 设置经纬度
	 * params center  中心点数据
	 * params data  攻击点数据
	 */
	set_longitude_and_latitude: function () {
		var that = this;
		layer.open({
			type: 1,
			title: '设置经纬度',
			area: ['420px', '320px'],
			closeBtn: 2,
			shadeClose: false,
			btn: ['确认', '取消'],
			content:
				'<div class="ng-map-china" style="padding: 20px 20px 10px 20px">\
					<div class="waf-line long_lat_select">\
							<span class="name-l" style="width:30px">省:</span>\
							<div class="info-r">\
								<select class="bt-input-text mr5" style="width:140px" name="ng_map_province" id="ng_map_province">\
														</select>\
							</div>\
					</div>\
					<div class="waf-line long_lat_select">\
							<span class="name-l" style="width:30px">市:</span>\
							<div class="info-r">\
								<select class="bt-input-text mr5" style="width:140px" name="ng_map_city" id="ng_map_city">\
										<option value="北京">北京</option>\
														</select>\
							</div>\
					</div>\
					<div class="waf-line long_lat_input"  style="display:none">\
							<span class="name-l" style="width:30px">经度:</span>\
							<div class="info-r">\
														<input type="number" style="border: 1px solid #ccc;height: 30px;" id="ng_map_log_input" placeholder="请输入纬度" class="waf-input">\
							</div>\
					</div>\
						<div class="waf-line long_lat_input"  style="display:none">\
							<span class="name-l" style="width:30px">纬度:</span>\
							<div class="info-r">\
														<input type="number" style="border: 1px solid #ccc;height: 30px;" id="ng_map_lat_input" placeholder="请输入纬度" class="waf-input">\
							</div>\
					</div>\
					<div class="waf-line" style="display:inline-block;margin-bottom:0px">\
							<span class="name-l">经度/纬度:</span>\
							<div class="info-r">\
									<span style="width:110px" class="city_log_lat">116.395645/39.929986</span>\
									<a target="_blank" class="btlink log_lat_write"> &gt;点击输入</a>\
							</div>\
					</div>\
					<ul class="waf_tips_list mtl0 c7 ptb10">\
												<li >位置仅供参考,并非为准确位置！</li>\
												<li >当前提供的位置为国内位置,如需获取国外位置，请查询<a href="http://api.map.baidu.com/lbsapi/getpoint/" target="_blank" class="btlink"> &gt;点击查询</a></li>\
					</ul>\
				</div>',
			success: function (index, layers) {
				$('.ng-map-china').on('click', '.log_lat_write', function (e) {
					$(this).addClass('log_lat_change').removeClass('log_lat_write').html('&gt;点击选择');
					$('.long_lat_input').show();
					$('.long_lat_select').hide();
				});
				$('.ng-map-china').on('click', '.log_lat_change', function (e) {
					$(this).addClass('log_lat_write').removeClass('log_lat_change').html('&gt;点击输入');
					$('.long_lat_input').hide();
					$('.long_lat_select').show();
				});
				var province = '',
					city = '';
				$.each(geoCoordMap.municipalities, function (index, item) {
					province += '<option value="' + item.n + '" data-id="' + item.g.substring(0, 17) + '">' + item.n + '</option>';
				});
				$.each(geoCoordMap.provinces, function (index, item) {
					province += '<option value="' + item.n + '" data-id="' + item.g.substring(0, 17) + '">' + item.n + '</option>';
				});
				$.each(geoCoordMap.other, function (index, item) {
					province += '<option value="' + item.n + '" data-id="' + item.g.substring(0, 17) + '">' + item.n + '</option>';
				});
				$('#ng_map_province').html(province);
				$('#ng_map_province').change(function (e) {
					var china_province = $(this).val(),
						id = $('#ng_map_province option:selected').attr('data-id');
					if (['北京', '上海', '重庆', '', '天津', '台湾', '香港', '澳门'].includes(china_province)) {
						$('#ng_map_city').html('<option value="' + china_province + '" data-id="' + id + '">' + china_province + '</option>');
					} else {
						$.each(geoCoordMap.provinces, function (index, item) {
							if (china_province == item.n) {
								city = '';
								$.each(item.cities, function (indexs, items) {
									city += '<option value="' + items.n + '" data-id="' + items.g.substring(0, 17) + '">' + items.n + '</option>';
								});
								$('#ng_map_city').html(city);
							}
						});
					}
					$('.city_log_lat').html(id.replace(',', '/'));
				});
				$('#ng_map_city').change(function (e) {
					var id = $('#ng_map_city option:selected').attr('data-id');
					$('.city_log_lat').html(id.replace(',', '/'));
				});
				$('.long_lat_input input').bind('input propertychange', function () {
					var log = $('#ng_map_log_input').val(),
						lat = $('#ng_map_lat_input').val();
					$('.city_log_lat').html(log + '/' + lat);
				});
			},
			yes: function (index, layers) {
				var list = $('.city_log_lat').html().split('/'),
					latitude = list[1],
					longitude = list[0];
				$.post('/btwaf/set_server_longitude.json', { latitude: latitude, longitude: longitude }, function (res) {
					layer.close(index);
					layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					var loadA = bt.load('正在重新获取攻击数据！');
					setTimeout(function () {
						window.location.reload();
					}, 200);
				});
			},
		});
	},
	/**
	 * @descripttion: 渲染攻击地图详情
	 * params center  中心点数据
	 * params data  攻击点数据
	 */
	render_map_details: function (center, data) {
		$('.arc-loading').hide(); // 关闭过渡状态

		var that = this;
		var overlay = new L.echartsLayer3(that.mapInfo, echarts);
		var chartsContainer = overlay.getEchartsContainer();
		var myChart = overlay.initECharts(chartsContainer);

		window.onresize = myChart.onresize;

		var lineColor = ['#a6c84c', '#ffa022', '#46bee9'];

		var list = [];
		var pointList = [];
		for (var j = 0; j < data.length; j++) {
			var item = data[j];
			var num = Math.floor(Math.random() * 3);
			if (!list[num]) {
				list[num] = [];
				pointList[num] = [];
			}
			list[num].push([{ coord: [item.ip_longitude, item.ip_latitude, item.ip] }, { coord: center }]);
			pointList[num].push({ name: '攻击IP：' + item.ip, value: [item.ip_longitude, item.ip_latitude, 1, item] });
		}
		var series = [];

		for (var i = 0; i < lineColor.length; i++) {
			var item = lineColor[i];
			if (!Array.isArray(list[i])) continue;
			for (var z = 0; z < list[i].length; z++) {
				var num = Math.floor((Math.random() * z) / 2);
				series.push({
					// 			name: '攻击点_ip',
					type: 'lines',
					zlevel: 1,
					effect: {
						show: true,
						period: 10 + num,
						trailLength: 0.5,
						color: item,
						symbolSize: 3,
					},
					lineStyle: {
						normal: {
							color: item,
							width: 0,
							curveness: 0.2,
						},
					},
					data: [list[i][z]],
				});
			}
			series.push({
				name: '攻击IP',
				type: 'scatter',
				coordinateSystem: 'geo',
				data: pointList[i],
				symbolSize: 4,
				label: {
					normal: {
						position: 'right',
						right: '10',
						show: false,
					},
					emphasis: {
						show: true,
					},
				},
				itemStyle: {
					normal: {
						color: 'red',
					},
				},
			});
		}
		series.push(
			{
				name: '本地IP地址',
				type: 'scatter',
				coordinateSystem: 'geo',
				data: [{ name: '本地IP：' + center[2], value: center }],
				symbolSize: 10,
				label: {
					emphasis: {
						show: true,
					},
				},
				itemStyle: {
					normal: {
						color: '#fc3f00',
					},
				},
			},
			{
				name: '本机IP地址',
				type: 'effectScatter',
				coordinateSystem: 'geo',
				data: [{ name: '本机IP地址：' + center[2], value: center }],
				symbolSize: 10,
				showEffectOn: 'render',
				rippleEffect: {
					brushType: 'stroke',
				},
				hoverAnimation: true,
				label: {
					normal: {
						formatter: '{b}',
						position: 'right',
						show: true,
					},
				},
				itemStyle: {
					normal: {
						color: '#fc3f00',
						shadowBlur: 10,
						shadowColor: '#333',
					},
				},
				zlevel: 1,
			}
		);

		option = {
			tooltip: {
				trigger: 'item',
				formatter: function (data) {
					var param = data.value ? data.value[3] : {};
					var html = '';
					html += '<span>攻击IP：' + (param ? param.ip : '') + '</span></br>';
					// html += '<span>地理位置：' + param.ip_continent + ' ' +  param.ip_country+ '</span>\r';
					return html;
				},
			},
			legend: {
				orient: 'vertical',
				y: 'bottom',
				x: 'right',
				data: [],
				textStyle: {
					color: '#fff',
				},
			},
			geo: {
				map: '',
				label: {
					emphasis: {
						show: false,
					},
				},
				roam: true,
				itemStyle: {
					normal: {
						areaColor: '#323c48',
						borderColor: '#404a59',
					},
					emphasis: {
						areaColor: '#2a333d',
					},
				},
			},
			series: series,
		};
		// 使用刚指定的配置项和数据显示图表。
		overlay.setOption(option);
	},

	/**
	 * @descripttion: 创建攻击排行榜
	 */
	create_attack_list: function (obj) {
		var that = this;
		$('.ng-attack-list').empty();
		if (obj.map.top10_ip.length == 0) {
			$('.ng-ip-list').hide();
			$('.ng-waf-map').addClass('col-sm-12').removeClass('col-sm-9');
		}
		$('.ng-attack-list').append(
			'<div class="divtable ng-table" style="height:200px;background-color:#ffffff;border:0;padding:0">\
			<table class="table table-hover">\
				<tbody id="ip_list_body">\
				</tbody>\
			</table>\
		</div>'
		);
		$.each(obj.map.top10_ip, function (index, item) {
			$('#ip_list_body').append(
				'<tr>\
			        <td><a class="btlink add_ip_black"  data-ip="' +
					item[0] +
					'" href="javascript:;">' +
					that.escapeHTML(item[0]) +
					'</a>&nbsp;&nbsp;(' +
					item[1] +
					')次&nbsp;&nbsp;' +
					that.render_ip_country({ip_country: item[2],ip_subdivisions: item[3],ip_city: item[4]}) +
					'</td>\
			        </tr>'
			);
		});
	},
	/**
	 * @descripttion: 创建攻击趋势图
	 * params obj 配置数据
	 */
	create_attack_tendency: function (obj) {
		var that = this,
			xData = [],
			yData = [];
		$.each(obj.gongji, function (index, item) {
			var _item;
			_item = item[0].substring(5, 10);
			xData.push(_item);
			yData.push(item[1]);
		});
		xData = xData.reverse();
		yData = yData.reverse();
		var attack_tendency = echarts.init(document.getElementById('ng-tendency'));
		var option = {
			title: {
				left: 'center',
				textStyle: {
					color: '#666666',
					fontSize: 16,
					fontWeight: 700,
				},
			},
			tooltip: {
				trigger: 'axis',
				axisPointer: {
					type: 'cross',
				},
				formatter: function (params) {
					var value = '攻击时间:' + params[0].name + '</br>' + '攻击次数:' + params[0].value;
					return value;
				},
			},
			grid: {
				left: 45,
				right: 15,
				top: 30,
				bottom: 20,
				backgroundColor: '#888',
			},
			xAxis: {
				type: 'category',
				boundaryGap: false,
				data: xData,
				axisLabel: {
					fontSize: 10,
					color: '#666',
					interval: 'auto',
				},
			},
			yAxis: {
				type: 'value',
				splitNumber: 5,
				name: '单位/次',
				min: 0,
				axisLine: {
					show: false,
				},
				axisTick: {
					show: false,
				},
				axisLabel: {
					fontSize: 10,
					color: '#666',
				},
			},
			series: [
				{
					data: yData,
					type: 'line',
					smooth: 0.6,
					areaStyle: {
						normal: {
							color: new echarts.graphic.LinearGradient(
								0,
								0,
								0,
								1,
								[
									{
										offset: 0,
										color: '#FF9E9E',
									},
									{
										offset: 1,
										color: '#FFF6F6',
									},
								],
								false
							),
						},
					},
					itemStyle: {
						normal: {
							color: '#FF8585', //改变折线点的颜色
							lineStyle: {
								color: '#FF8585', //改变折线颜色
								type: 'solid',
							},
						},
					},
				},
			],
		};
		option && attack_tendency.setOption(option);
		window.addEventListener('resize', function () {
			attack_tendency.resize();
		});
	},
	/**
	 * @descripttion: 创建攻击趋势图
	 * params obj 配置数据
	 */
	create_attack_tendency1: function (obj) {
		var that = this,
			xData = [],
			yData = [];
		$.each(obj.gongji, function (index, item) {
			var _item;
			_item = item[0].substring(5, 10);
			xData.push(_item);
			yData.push(item[1]);
		});
		xData = xData.reverse();
		yData = yData.reverse();
		var attack_tendency = echarts.init(document.getElementById('intercept-trend-chart'));
		var option = {
			title: {
				left: 'center',
				textStyle: {
					color: '#fff',
					fontSize: 16,
					fontWeight: 700,
				},
			},
			tooltip: {
				trigger: 'axis',
				axisPointer: {
					type: 'line',
					lineStyle: {
						color: '#fff',
					},
				},
				backgroundColor: 'rgba(255,255,255,0.3)',
				padding: [8, 10], //内边距
				formatter: function (params) {
					var value = '攻击时间：' + (params.length ? params[0].name : '--') + '</br>' + '攻击次数：' + (params.length ? (params[0].value ? params[0].value : 0) : '--');
					return value;
				},
			},
			grid: {
				left: 45,
				right: 15,
				top: 30,
				bottom: 20,
				backgroundColor: '#fff',
			},
			xAxis: {
				type: 'category',
				boundaryGap: false,
				data: xData,
				axisLabel: {
					// 坐标轴刻度标签的相关设置
					fontSize: 10,
					textStyle: {
						color: '#fff',
					},
				},
				splitLine: {
					show: false,
				},
				axisLine: {
					show: true,
					lineStyle: {
						color: '#2EB8C2',
						width: 1,
					},
				},
				axisTick: {
					// 刻度点数轴
					show: true,
					lineStyle: {
						color: '#2EB8C2',
					},
				},
			},
			yAxis: {
				type: 'value',
				splitNumber: 5,
				min: 0,
				minInterval: 1,
				name: '单位/次',
				nameTextStyle: {
					color: '#fff',
				},
				axisLine: {
					show: false,
					lineStyle: {
						color: '#fff',
					},
				},
				axisTick: {
					show: false,
				},
				axisLabel: {
					fontSize: 10,
					textStyle: {
						color: '#fff',
					},
				},
				splitLine: {
					show: false,
				},
			},
			series: [
				{
					data: yData,
					type: 'line',
					smooth: 0.6,
					areaStyle: {
						normal: {
							color: new echarts.graphic.LinearGradient(
								0,
								0,
								0,
								1,
								[
									{
										offset: 0,
										color: 'rgba(190, 240, 244, 0.5)',
									},
									{
										offset: 1,
										color: 'rgba(196, 196, 196, 0)',
									},
								],
								false
							),
						},
					},
					itemStyle: {
						normal: {
							color: '#49E6F1', //改变折线点的颜色
							lineStyle: {
								color: '#49E6F1', //改变折线颜色
								type: 'solid',
							},
						},
					},
				},
			],
		};
		option && attack_tendency.setOption(option);
		window.addEventListener('resize', function () {
			attack_tendency.resize();
		});
	},
	/**
	 * @description 获取指定日期上一天\下一天
	 * @param {String} date 指定日期时间戳 当前时间戳Date.parse(new Date())
	 * @param {Number} day -1:上一天 1:下一天
	 */
	getNextDate: function (date, day) {
		var dd = new Date(date);
		dd.setDate(dd.getDate() + day);
		var y = dd.getFullYear(),
			m = dd.getMonth() + 1 < 10 ? '0' + (dd.getMonth() + 1) : dd.getMonth() + 1,
			d = dd.getDate() < 10 ? '0' + dd.getDate() : dd.getDate();
		return y + '-' + m + '-' + d;
	},
	/**
	 * @description 获取报表
	 */
	get_report: function (num) {
		var that = this,
			param = {};
		var currtime = Date.parse(new Date()); //当前时间戳
		var timeVal = $('#waf_time_choose').val();
		var index = $('.ng-second-head span.active').index();
		if (num != undefined) {
			$('#waf_time_choose').val('');
			$('#waf_time_choose')
				.parent()
				.find('span')
				.eq(num ? 0 : 1)
				.addClass('on')
				.siblings()
				.removeClass('on');
		} else {
			if (timeVal) {
				param.start_time = timeVal.split(' - ')[0];
				param.end_time = timeVal.split(' - ')[1];
				$('#waf_time_choose').addClass('on').siblings().removeClass('on');
			}
		}
		if ($('#waf_time_choose').parent().find('span').eq(0).hasClass('on')) {
			param.start_time = that.getNextDate(currtime, -1);
			param.end_time = that.getNextDate(currtime, -1);
		}
		// 日期选择
		that.ajaxTask('get_report', param, function (res) {
			if (res.status) {
				var total = 0;
				if (res.msg == []) {
					$('#protectTableBody').html('<tr><td colspan="5" align="center">当前数据为空</td></tr>');
				} else {
					switch (index) {
						case 0:
							// if(typeof res.msg.type) return false
							$.each(res.msg.type, function (index, item) {
								total += item[1];
							});
							$('#ng_protect_table .ip_address').remove();
							$('#ng_protect_table table thead tr th:eq(0)').after('<th class="ip_address" width="100px">IP归属地</th>');
							$('#ng_protect_table table thead tr th').eq(0).html('攻击IP');
							$('#protectTableBody').empty();
							that.create_report_table(res.msg.ip, total, res, index);
							if (res.msg.ip) {
								that.create_table_thead({
									el: '.ng-fixed',
									list: [
										['攻击IP', 'width="250px"'],
										['IP归属地', 'width="100px"'],
										['攻击次数', 'width="100px"'],
										['攻击占比', 'width="250px"'],
										['操作', 'style="text-align:right" width="100px"'],
									],
								});
							}
							break;
						case 1:
							$.each(res.msg.uri, function (index, item) {
								total += item[1];
							});
							$('#ng_protect_table .ip_address').remove();
							$('#ng_protect_table table thead tr th').eq(0).html('URI');
							$('#protectTableBody').empty();
							that.create_report_table(res.msg.uri, total, res, index);
							if (res.msg.uri) {
								that.create_table_thead({
									el: '.ng-fixed',
									list: [
										['URI', 'width="250px"'],
										['攻击次数', 'width="100px"'],
										['攻击占比', 'width="250px"'],
										['操作', 'style="text-align:right" width="100px"'],
									],
								});
							}
							break;
					}
					var reportType = echarts.init(document.getElementById('ng_protect_type'));
					that.create_report_pie(res.msg.type, reportType);
					that.create_report_top(res);
				}
			}
		});
	},
	/**
	 * @descripttion: 创建防御饼图
	 * params location  绘制位置
	 * params config  数据
	 */
	create_report_pie: function (config, location, text) {
		var that = this,
			colorList = ['#6ec71e', '#4885FF', '#fc8b40', '#818af8', '#31c9d7', '#f35e7a', '#ab7aee', '#14d68b', '#cde5ff'],
			types = [],
			total = 0;
		$.each(config, function (index, item) {
			var list = { name: item[0], value: item[1] };
			(total += item[1]), types.push(list);
		});
		if (!text) text = '总防护类型';
		var option = {
			backgroundColor: '#fff',
			title: {
				text: text,
				textStyle: {
					color: '#484848',
					fontSize: 17,
				},
				subtext: total,
				subtextStyle: {
					color: '#717171',
					fontSize: 15,
				},
				itemGap: 20,
				left: 'center',
				top: '42%',
			},
			tooltip: {
				trigger: 'item',
				formatter: function (param) {
					var range = 0;
					if (!isNaN(total) && !isNaN(param.data.value) && total > 0) {
						range = (param.data.value / total).toFixed(2) * 100;
					}
					return (
						'<div style="display: inline-block; width: 10px; height: 10px; margin-right: 5px; border-radius: 50%; background-color: ' +
						param.color +
						'"></div>' +
						param.data.name +
						': ' +
						param.data.value +
						' (' +
						parseFloat(range.toFixed(2)) +
						'%)'
					);
				},
			},
			series: [
				{
					type: 'pie',
					radius: ['45%', '55%'],
					center: ['50%', '50%'],
					clockwise: true,
					avoidLabelOverlap: true,
					hoverOffset: 15,
					itemStyle: {
						normal: {
							label: {
								show: true,
								position: 'outside',
								color: '#ddd',
								formatter: function (params) {
									var percent = 0;
									var total = 0;
									for (var i = 0; i < types.length; i++) {
										total += types[i].value;
									}
									if (params.name !== '') {
										var range = 0;
										if (!isNaN(total) && !isNaN(params.value) && total > 0) {
											range = (params.value / total).toFixed(2) * 100;
										}
										return params.name + '\n' + '\n' + params.value + '/次，' + parseFloat(range.toFixed(2)) + '%';
									} else {
										return '';
									}
								},
							},
							labelLine: {
								normal: {
									length: 30,
									length2: 30,
									lineStyle: {
										width: 1,
										color: '#CDCDCD',
									},
								},
							},
							color: function (params) {
								return colorList[params.dataIndex];
							},
						},
					},
					data: types,
				},
				{
					itemStyle: {
						normal: {
							color: '#F5F6FA',
						},
					},
					type: 'pie',
					hoverAnimation: false,
					radius: ['42%', '58%'],
					center: ['50%', '50%'],
					label: {
						normal: {
							show: false,
						},
					},
					data: [],
					z: -1,
				},
			],
		};
		location.setOption(option);
		window.addEventListener('resize', function () {
			location.resize();
		});
	},
	/**
	 * @descripttion: 绘制报表柱形图
	 * params obj  配置数据
	 */
	create_report_column: function (location, config) {
		var that = this;
		var serData = [];
		var lenend = [];
		for (var i = 0; i < config.length; i++) {
			if (i >= 5) break;
			lenend.push(config[i]['name'].substring(0, 25));
			serData.push({
				name: config[i]['name'],
				type: 'bar',
				label: {
					normal: {
						show: true,
						position: 'top',
					},
				},
				barMaxWidth: 60,
				data: [config[i]['value']],
			});
		}
		var option2 = {
			backgroundColor: '#fff',
			tooltip: {
				trigger: 'item',
				axisPointer: {
					type: 'shadow',
					textStyle: {
						color: '#fff',
						fontSize: '26',
					},
				},
				formatter: function (params) {
					var text = params.marker + that.escapeHTML(params.seriesName) + '<br>当前uri总攻击次数:' + params.data;
					return text;
				},
			},
			legend: {
				top: '0%',
				data: lenend,
				textStyle: {
					fontSize: 12,
					color: '#808080',
				},
				icon: 'rect',
			},
			grid: {
				top: 60,
				left: 60,
				right: 0,
				bottom: 50,
			},
			xAxis: [
				{
					type: 'category',
					axisLabel: {
						color: '#4D4D4D',
						fontSize: 14,
						fontWeight: 'bold',
					},
					data: ['今日URI(TOP5)'],
				},
			],
			color: ['#4fa8f9', '#6ec71e', '#f56e6a', '#fc8b40', '#818af8', '#31c9d7', '#f35e7a', '#ab7aee', '#14d68b', '#cde5ff'],
			yAxis: [
				{
					type: 'value',
					axisLine: {
						show: false,
					},
					axisTick: {
						show: false,
					},
					splitNumber: 4, //y轴分割线数量
					axisLabel: {
						color: '#8C8C8C',
					},
					splitLine: {
						lineStyle: {
							type: 'dashed',
						},
					},
				},
			],
			series: serData,
		};
		location.setOption(option2);
	},
	/**
	 * @descripttion: 绘制攻击排行榜
	 * params obj  配置数据
	 */
	create_report_top: function (config) {
		var that = this;
		$('#ip_list_body').empty();
		$.each(config.msg.ip, function (index, item) {
			//  <td><a class="btlink add_ip_black"  data-ip="'+item[0]+'" href="javascript:;">'+ item[0] +'</a>&nbsp;&nbsp;('+item[1] +')次</td>\
			$('#ip_list_body').append(
				'<tr><td><a class="btlink add_ip_black"  data-ip="' +
					that.escapeHTML(item[0]) +
					'" href="javascript:;">' +
					that.escapeHTML(item[0]) +
					'</a>&nbsp;&nbsp;' +
					that.render_ip_country({ip_country: item[2],ip_subdivisions: item[3],ip_city: item[4]}) +
					'&nbsp;&nbsp;(' +
					item[1] +
					')次</td></tr>'
			);
		});
	},
	/**
	 * @descripttion: 绘制攻击报表
	 * params obj  配置数据
	 * params total  总条数
	 */
	create_report_table: function (data, total, config, num) {
		var that = this;
		if (data) {
			$.each(data, function (index, item) {
				$('#protectTableBody').append(
					$(
						'<tr>\
    				<td><a class="btlink ' +
							(num == 0 ? 'getIdLog' : 'getUriLog') +
							'">' +
							that.escapeHTML(item[0]) +
							'</a></td>\
    				' +
							(num == 0 ? '<td>' + that.render_ip_country({ip_country: item[2],ip_subdivisions: item[3],ip_city: item[4]}) + '</td>' : '') +
							'\
    				<td>' +
							item[1] +
							'</td>\
    				<td><div class="ip-list-box" style="width: ' +
							((item[1] / total) * 85).toFixed(3) +
							'%;"></div><span class="ng-ratio">' +
							((item[1] / total) * 100).toFixed(3) +
							'%</span></td>\
    				<td style="text-align:right"><a class="btlink ' +
							(num == 0 ? 'add_ip_black' : 'add_url_black') +
							'" data-ip="' +
							that.escapeHTML(item[0]) +
							'">拉黑</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a class="btlink ' +
							(num == 0 ? 'getIdLog' : 'getUriLog') +
							'">详情</a></td>\
    			</tr>'
					).data({ data: item, index: index, ip_list: num == 0 ? config.msg.ip_list[item[0]] : config.msg.uri_list[item[0]].ip_list })
				);
			});
		} else {
			$('#protectTableBody').html('<tr><td colspan="5" align="center">当前数据为空</td></tr>');
		}
	},
	/**
	 * @descripttion: 创建报表信息
	 * params ip  当前ip
	 * params config  当前ip配置信息
	 */
	create_report_site: function (ip, config) {
		var that = this;
		layer.open({
			type: 1,
			title: '恶意IP -【' + that.escapeHTML(ip) + '】攻击详情',
			area: ['930px', '720px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="site_logs_table">\
						<div id="type_total_echart" style="height: 280px; width: 350px;-webkit-tap-highlight-color: transparent;user-select: none;position: relative;display:inline-block"></div>\
						<div id="uri_total_echart" style="height: 280px; width: 500px;-webkit-tap-highlight-color: transparent;user-select: none;position: relative;display:inline-block"></div>\
						<div class="divtable ng-fixed" style="width:100%;padding:0px 28px 0px 20px"></div>\
						<div id="report_logs_table" class="divtable" style="width:100%;height:337px;overflow:auto;scrollbar-width: thin;">\
						    <table class="table table-hover">\
								<thead>\
									<tr>\
										<th width="150px">攻击时间</th>\
										<th width="100px">被保护网站</th>\
										<th width="100px">IP归属地</th>\
										<th width="200px">URI</th>\
										<th width="100px">保护类型</th>\
										<th width="100px" style="text-align:right" width="10%">操作</th>\
									</tr>\
								</thead>\
								<tbody id="reportLogBody"></tbody>\
							</table>\
						</div>\
					</div>',
			success: function (layero, index) {
				//饼图
				var type = config.type,
					arr1 = [],
					arr2 = [],
					list = [];
				for (var key in type) {
					arr1.push(key);
					arr2.push(type[key]);
				}
				$.each(arr1, function (index, item) {
					var arr3 = [];
					arr3.push(item);
					arr3.push(arr2[index]);
					list.push(arr3);
				});
				var typeTotalEchart = echarts.init(document.getElementById('type_total_echart'));
				that.create_report_pie(list, typeTotalEchart, '当前IP总拦截数');
				//柱状图
				var uri = config.uri,
					arr4 = [],
					arr5 = [],
					uri_list = [];
				for (var key in uri) {
					if (!uri[key][0]) continue;
					arr4.push(uri[key][0]);
					arr5.push(uri[key][1]);
				}
				$.each(arr4, function (index, item) {
					var data = {};
					data['name'] = item;
					data['value'] = arr5[index];
					uri_list.push(data);
				});
				// that.render_site_logs({siteName:row.siteName,start_time:dateList[0]});
				var uriTotalEchart = echarts.init(document.getElementById('uri_total_echart'));
				that.create_report_column(uriTotalEchart, uri_list);
				that.render_report_table(config.list);
				if (config.list.length > 9) {
					that.create_table_thead({
						el: '.site_logs_table .ng-fixed',
						list: [
							['攻击时间', 'width="150px"'],
							['被保护网站', 'width="100px"'],
							['IP归属地', 'width="100px"'],
							['URI', 'width="200px"'],
							['保护类型', 'width="100px"'],
							['操作', 'style="text-align:right" width="100px"'],
						],
					});
				}
			},
		});
	},
	/**
	 * @descripttion: 创建报表信息
	 * params uri  当前URI
	 * params config  当前ip配置信息
	 */
	create_report_URI: function (uri, config) {
		var that = this;
		layer.open({
			type: 1,
			title: '被攻击的URI -【' + that.escapeHTML(uri) + '】防护记录',
			area: ['930px', '680px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="uri_logs_table">\
			            <div class="divtable ng-fixed" style="width:100%;padding:0px 23px 0px 15px"></div>\
						<div id="report_logs_table" class="divtable" style="width:100%;height:600px;overflow:auto;padding:0px 15px 15px 15px;margin-top:15px">\
						    <table class="table table-hover">\
								<thead>\
									<tr>\
										<th width="150px">攻击时间</th>\
										<th width="100px">攻击IP</th>\
										<th width="100px">被保护网站</th>\
										<th width="100px">IP归属地</th>\
										<th width="200px">URI</th>\
										<th width="100px">保护类型</th>\
										<th width="100px" style="text-align:right" width="10%">操作</th>\
									</tr>\
								</thead>\
								<tbody id="reportLogBody"></tbody>\
							</table>\
						</div>\
					</div>',
			success: function (layero, index) {
				$('#reportLogBody').empty();
				that.render_report_table(config, 'uri');
				if (config.length > 17) {
					that.create_table_thead({
						el: '.uri_logs_table .ng-fixed',
						list: [
							['攻击时间', 'width="150px"'],
							['攻击IP', 'width="100px"'],
							['被保护网站', 'width="100px"'],
							['IP归属地', 'width="100px"'],
							['URI', 'width="200px"'],
							['保护类型', 'width="100px"'],
							['操作', 'style="text-align:right" width="100px"'],
						],
					});
				}
			},
		});
	},
	/**
	 * @descripttion: 创建查询列表
	 * params obj  查询数据
	 * params p  分页信息
	 */
	create_search_table: function (obj, p) {
		var that = this;
		if (p == undefined) p = 1;
		obj.p = p;
		that.ajaxTask('get_search', obj, function (res) {
			if (res.status) {
				$('#ng_search_table').show();
				$('#searchTableBody').empty();
				if (res.msg.data.length == 0) {
					$('#searchTableBody').append('<tr><td colspan="6" align="center">当前数据为空</td></tr>');
				} else {
					$.each(res.msg.data, function (index, item) {
						$('#searchTableBody').append(
							$(
								'<tr>\
            				<td>' +
									item.time_localtime +
									'</td>\
            				<td>' +
									item.ip +
									'</td>\
            				<td>' +
									item.server_name +
									'</td>\
            				<td>' +
									that.escapeHTML(item.uri.substring(0, 30)) +
									'</td>\
            				<td>' +
									item.filter_rule +
									'</td>\
            			<td style="text-align:right"><a class="btlink report_details">详情</a>&nbsp&nbsp|&nbsp&nbsp<a class="btlink report_HTTP">HTTP</a></td>\
            			</tr>'
							).data({ data: item, index: index })
						);
					});
					$('#searchTablePage').html(res.msg.page);
				}
			}
		});
	},
	/**
	 * @descripttion: 创建排行列表
	 * params obj  配置数据
	 */
	render_report_table: function (config, type) {
		var that = this;
		$('#reportLogBody').empty();
		$.each(config, function (index, item) {
			$('#reportLogBody').append(
				$(
					'<tr>\
				<td>' +
						item.time_localtime +
						'</td>' +
						(type == 'uri' ? '<td>' + item.ip + '</td>' : '') +
						'\
				<td>' +
						item.server_name +
						'</td>\
				<td>' + that.render_ip_country(item)
						 +
						'</td>\
				<td>' +
						that.escapeHTML(item.uri).substring(0, 30) +
						'</td>\
				<td>' +
						item.filter_rule +
						'</td>\
			<td style="text-align:right"><a class="btlink report_details">详情</a>&nbsp&nbsp|&nbsp&nbsp<a class="btlink report_HTTP">HTTP</a></td>\
			</tr>'
				).data({ data: item, index: index })
			);
		});
		$('#report_logs_table').on('click', '.report_details', function (e) {
			var data = $(this).parents('tr').data().data;
			that.ajaxTask('get_id_log', { id: data.id }, function (res) {
				var row = res.msg[0];
				that.create_details(row);
			});
		});
		$('#report_logs_table').on('click', '.report_HTTP', function (e) {
			var data = $(this).parents('tr').data().data;
			that.ajaxTask('get_id_log', { id: data.id }, function (res) {
				var row = res.msg[0];
				that.create_HTTP(row);
			});
		});
	},
	/**
	 * @descripttion: 创建详情
	 * params row  配置数据
	 */
	create_details: function (row) {
		var that = this;
		var _type = row.type;
		var filter_rule = '',
			rule_arry = row.incoming_value.indexOf('b"') > -1 ? row.incoming_value.substring(2, row.incoming_value.length - 1).split(' >> ') : row.incoming_value.split(' >> '),
			incoming_value = '',
			risk_value = '';
		if (rule_arry.length == 0) filter_rule = rule_arry[0];
		incoming_value = rule_arry[1] == undefined ? '空' : rule_arry[1];
		risk_value = rule_arry[2] ? rule_arry[2] : '空';
		layer.open({
			type: 1,
			title: '【' + row.time_localtime + '】详情',
			area: '600px',
			closeBtn: 2,
			shadeClose: false,
			content:
				'\
				<div class="pd15 lib-box">\
					<table class="table" style="border:#ddd 1px solid;">\
						<tbody>\
							<tr>\
								<th>时间</th>\
								<td>' +
				that.escapeHTML(row.time_localtime) +
				'</td>\
								<th>攻击IP</th>\
								<td>\
									<a class="btlink add_log_ip_black"  title="加入黑名单">' +
				that.escapeHTML(row.ip) +
				'</a>\
								</td>\
							</tr>\
							<tr>\
								<th>类型</th>\
								<td>' +
				that.escapeHTML(_type) +
				'</td>\
								<th>过滤器</th>\
								<td style="max-width: 330px;word-break: break-all;">' +
				that.escapeHTML(row.filter_rule) +
				'</td>\
							</tr>\
						</tbody>\
					</table>\
					<div style="margin-top:20px">\
						<b style="margin-left:10px">URI地址</b>\
						<a class="btlink btn-error pull-right">URL加白</a>\
					</div>\
					<div class="lib-con mt10">\
						<div class="divpre">' +
				that.escapeHTML(row.uri) +
				'</div>\
					</div>\
					<div style="margin-top:20px">\
						<b style="margin-left:10px">User-Agent</b>\
					</div>\
					<div class="lib-con mt10">\
						<div class="divpre">' +
				that.escapeHTML(row.user_agent) +
				'</div>\
					</div>\
					<div class="clearfix" style="margin-top:20px">\
						<b style="margin-left:10px">过滤规则 <a class="btlink" href="https://www.bt.cn/bbs/thread-65364-1-1.html" target="_blank">《点我提交误拦截》</a></b>\
					</div>\
					<div class="lib-con mt10">\
						<div class="divpre">' +
				that.escapeHTML(rule_arry[0]) +
				'</div>\
					</div>\
					<div style="margin-top:20px">\
						<b style="margin-left:10px">传入值</b>\
					</div>\
					<div class="lib-con mt10">\
						<div class="divpre">' +
				that.escapeHTML(incoming_value) +
				'</div>\
					</div>\
					<div style="margin-top:20px">\
						<b style="margin-left:10px">风险值</b>\
					</div>\
					<div class="lib-con mt10">\
						<div class="divpre">' +
				that.escapeHTML(risk_value) +
				'</div>\
					</div>\
				</div>',
			success: function ($layer) {
				$('.add_log_ip_black').click(function () {
					var ipv4Range = '';
					if (bt.check_ip(row.ip)) {
						ipv4Range =
							'<div class="mt10"><input type="checkbox" id="ipRangeInsulate"/><label for="ipRangeInsulate" style="font-weight: 400;margin: 0 0 0 5px;cursor: pointer;">是否拉黑整个IP段？</label></div>';
					}
					layer.confirm('是否将 <span style="color:red">' + row.ip + '</span> 添加到IP黑名单？' + ipv4Range, { title: '加入IP黑名单', closeBtn: 2 }, function () {
						if (bt.check_ip(row.ip)) {
							var isCheck = $('#ipRangeInsulate').is(':checked');
							if (!isCheck) {
								that.ajaxTask('add_ip_black', { start_ip: row.ip, end_ip: row.ip }, function (res) {
									layer.msg(res.msg, { icon: res.status ? 1 : 2 });
								});
							} else {
								var ipRange = row.ip.replace(/\d{1,3}$/, '0/24');
								bt_waf.http({
									method: 'import_data',
									data: { s_Name: 'ip_black', pdata: ipRange },
									success: function (res) {
										layer.msg(res.status ? '操作成功' : '添加失败', { icon: res.status ? 1 : 2 });
									},
								});
							}
						} else {
							that.ajaxTask('set_ipv6_back', { addr: row.ip }, function (res) {
								layer.msg(res.msg, { icon: res.status ? 1 : 2 });
							});
						}
					});
				});
				$layer.find('.btn-error').click(function () {
					if (row.uri == '/') return layer.msg('当前ip的uri为根目录,无法执行误报操作！');
					layer.confirm('加入URL白名单后此URL将不再进行防御，是否继续操作？', { title: '加入URL白名单', icon: 3, closeBtn: 2 }, function () {
						if (row.http_log_path === 1) {
							$.post('/btwaf/get_logs', { path: row.http_log }, function (res) {
								that.ajaxTask('wubao_url_white', { url_rule: row.uri, error_log: row.ip + ' >> ' + row.incoming_value, http_log: res }, function (res) {
									layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									if (rule_arry[1] != undefined) {
										$.get('https://www.bt.cn/Api/add_waf_logs?data=' + rule_arry[1], function (rdata) {}, 'jsonp');
									}
								});
							});
						} else {
							that.ajaxTask('wubao_url_white', { url_rule: row.uri, error_log: row.ip + ' >> ' + row.incoming_value, http_log: row.http_log }, function (res) {
								layer.msg(res.msg, { icon: res.status ? 1 : 2 });
								if (rule_arry[1] != undefined) {
									$.get('https://www.bt.cn/Api/add_waf_logs?data=' + rule_arry[1], function (rdata) {}, 'jsonp');
								}
							});
						}
					});
				});
			},
		});
	},
	create_HTTP: function (row) {
		var that = this;
		var _http_info = row.http_log.indexOf('b"') > -1 ? row.http_log.substring(2, row.http_log.length - 1).replace(/\\n/g, ' \n') : row.http_log.replace(/\\n/g, ' \n');
		if (_http_info) {
			layer.open({
				type: 1,
				title: '【' + row.time_localtime + '】HTTP详情',
				area: ['800px', '500px'],
				closeBtn: 1,
				shadeClose: false,
				maxmin: true,
				content:
					'<div class="pd15 lib-box" style="height:100%">\
    					<pre id="http_info_data" style="height:100%"></pre></div>',
				success: function (layers) {
					if (row.http_log_path == 1) {
						$.post('/btwaf/get_logs', { path: _http_info }, function (res) {
							$('#http_info_data').text(res);
						});
					} else {
						$('#http_info_data').text(_http_info);
					}
					$(layers).css('top', ($(window).height() - $(layers).height()) / 2);
				},
			});
		} else {
			layer.msg('暂无HTTP详情信息', { icon: 6 });
		}
	},
	/**
	 * @descripttion: 创建排行列表
	 * params obj  配置数据
	 */
	create_attack_rank: function (obj) {
		var that = this;
		$('#rankTableBody').empty();
		if (JSON.stringify(obj.server_name_top5) == '{}') {
			$('#rankTableBody').append('<tr><td colspan="2" align="center">当前数据为空</td></tr>');
		}
		$.each(obj.server_name_top5, function (index, item) {
			$('#rankTableBody').append(
				$(
					'<tr>\
				<td>' +
						item[0] +
						'</td>\
				<td>' +
						item[1] +
						'</td>\
			</tr>'
				).data({ data: item, index: index, start_time: obj.gongji[1][0], end_time: obj.gongji[0][0] })
			);
			// 			$('#rankTableBody').append($('<tr>\
			// 				<td>'+ item[0]+'</td>\
			// 				<td>'+ item[1]+'</td>\
			// 				<td style="text-align:right"><a class="btlink attack_log" >详情<a></td>\
			// 			</tr>').data({data:item,index:index,start_time:obj.gongji[1][0],end_time:obj.gongji[0][0]}))
		});
	},
	/**
	 * @descripttion: 创建动态列表
	 * params obj 配置数据
	 */
	create_dynamic_table: function (obj) {
		var that = this;
		$('#dynamicTableBody').empty();
		var _dynamic = obj.dongtai;
		if (JSON.stringify(_dynamic) == '{}') {
			$('#dynamicTableBody').append('<tr><td colspan="3" align="center">当前数据为空</td></tr>');
		}
		$.each(_dynamic, function (index, item) {
			$('#dynamicTableBody').append(
				$(
					'<tr>\
			<td>' +
						item.time_localtime.substring(5, item.time_localtime.length) +
						'</td>\
			<td>' +
						(that.escapeHTML(item.ip) + '攻击了网站' + item.server_name + '，已被拦截，触发规则是：' + that.escapeHTML(item.filter_rule)) +
						'</td>\
			<td>' +
			that.render_ip_country(item) +
						'</td>\
			<td style="text-align:right"><a class="btlink dynamic_log" >详情<a></td>\
			</tr>'
				).data({ data: item, index: index })
			);
		});
	},
	/**
	 * @description 渲染日志分页
	 * @param {Number} pages 每页个数
	 * @param {Number} p 当前页数
	 * @param {Number} num 总数
	 * @return 返回组合的HTML页码文本
	 */
	render_logs_pages: function (pages, p, num) {
		return (
			'<a class="nextPage" data-page="1">首页</a>' +
			(p != 1 ? '<a class="nextPage" data-page="' + (p - 1) + '">上一页</a>' : '') +
			(pages <= num ? '<a class="nextPage" data-page="' + (p + 1) + '">下一页</a>' : '') +
			'<span class="Pcount">第 ' +
			p +
			' 页</span>'
		);
	},
	/**
	 * @description 日志跳转页面
	 * @param {String} p 页数
	 */
	get_gl_table_page: function (p) {
		if (p == undefined) p = 1;
		this.render_logs_data({ p: p, tojs: 'bt_waf.get_gl_table_page' });
	},
	/**
	 * @description 渲染告警设置
	 * */
	render_alarm_data: function () {
		var that = this;
		$('[data-type=alarm] .tab-nav-border span')
			.unbind('click')
			.click(function () {
				var index = $(this).index();
				$(this).addClass('on').siblings().removeClass('on');
				$(this).parent().next().find('.tab-block').eq(index).addClass('on').siblings().removeClass('on');
				that.cutAlarmTab(index);
			});
		$('[data-type=alarm] .tab-nav-border span').eq(0).trigger('click');
	},
	/**
	 * @description 告警设置tab切换
	 * @param {number} index
	 * */
	cutAlarmTab: function (index) {
		var that = this;
		switch (index) {
			case 0:
				that.render_alarm_set();
				break;
			case 1:
				that.render_alarm_logs();
				break;
		}
	},
	/**
	 * @description 渲染告警设置
	 * */
	render_alarm_set: function () {
		var that = this;
		var titleArr = {
			cc: { name: 'CC告警', ps: '' },
			file: { name: '封锁IP总数告警', ps: '' },
			version: { name: '版本更新通知', ps: '* 当检测到新的版本时发送一次通知，一天检测一次' },
			webshell: { name: 'webshell 查杀', ps: '* 当检测到有木马时发送一次通知，每十分钟检测一次' },
			vul: { name: '安全漏洞预警', ps: '* 当检测到有新的安全漏洞时发送一次通知，一天检测一次' },
			send: { name: '告警方式' },
		};
		var sendList = ['dingding', 'feishu', 'weixin'];
		var el = $('#alarm-set-form');
		bt_tools.send(
			{
				url: '/config?action=get_msg_configs',
			},
			function (alarms) {
				bt_tools.send(
					{ url: '/plugin?action=a&name=btwaf&s=Get_Alarm' },
					function (alarm_data) {
						el.empty();
						$.each(alarm_data, function (index, item) {
							var send_html = '';
							if (index === 'send') {
								$.each(alarms, function (index1, item1) {
									if (sendList.indexOf(index1) !== -1) {
										var is_disabled = !item1.setup || $.isEmptyObject(item1.data) ? true : false;
										var is_checked = item.send_type === index1;
										send_html +=
											'<div class="form-radio">\
									            <input type="radio" id="radio_' +index1 +'" name="push_method" value="' +index1 +'" ' +
    											(is_disabled ? 'disabled' : '') +
    											(is_checked && !is_disabled ? 'checked' : '') +'>\
    									        <label class="cursor mr5" for="radio_' +index1 +'" title="' +item1.ps +'">' +item1.title +'</label>' +
											    (!item1.setup || $.isEmptyObject(item1.data) ? '[<a target="_blank" class="bterror installNotice" data-type="' + item1.name + '">点击安装</a>]' : '') +
											'</div>';
									}
								});
							}
							var html ='<div class="line" title="' +titleArr[index].name +'">\
						            <div class="line-title">' +titleArr[index].name +'</div>\
						            <div class="line-form">' +(index === 'send'? '<div class="form-content">' + send_html + '</div>': '<div class="ssh-item">\
								    <input class="btswitch btswitch-ios" id="' +index +'_switch" type="checkbox" name="' +index +'_switch" ' +(item.status ? 'checked' : '') +'>\
								    <label class="btswitch-btn"\
								    for="' +index +'_switch"\
								    style="margin-bottom: 0">\
								    </label></div>') 
								    +(item.hasOwnProperty('cycle')? '<span class="mr20 inlineBlock ml30">访问时间</span>\
								    <div class="inlineBlock group">\
								        <input type="number" name="' +index +'_time" min="60" class="bt-input-text mr10  group" style="width:70px;" value="' +item.cycle +'">\
								        <span class="unit">秒</span>\
							        </div>\
        							<span class="mr20 inlineBlock ml30">访问次数</span>\
        							<div class="inlineBlock group">\
        								<input type="number" name="' +index +'_count" min="' +(index === 'cc' ? '30' : '60') +'" class="bt-input-text mr10  group" style="width:70px;" value="' +item.limit +'">\
        								<span class="unit">次</span>\
        							</div>': '') +
								    (item.hasOwnProperty('cycle')? '<div class="line-row-tips">* 当<span class="' +index +'_time">' +item.cycle +'</span>秒内有<span class="' +index +'_count">' +item.limit +
									  '</span>个IP触发' +(index === 'cc' ? 'CC拦截' : '封锁') +'时发送一次通知，十分钟内不会发送第二次</div>': titleArr[index].hasOwnProperty('ps')? '<div class="line-row-tips">' + titleArr[index].ps + '</div>': '') +
								    '</div>';
							    el.append(html);
						    });
						el.append('<div class="line">\
					        <div class="line-title"></div>\
					        <div class="line-form">\
						        <button type="button" title="设置" class="btn btn-success btn-sm mr5 set_alarm_btn"><span>设置</span></button>\
					       </div>\
				        </div>');
					   },'获取告警信息');
				el.on('click', '.installNotice', function (ev) {
					var el = $(ev.currentTarget),
						type = $(el).data('type');
					openAlertModuleInstallView(type);
				});
				el.on('input', '[name=cc_time],[name=file_time]', function (ev) {
					var val = $(this).val();
					if (parseInt(val) < 60) {
						layer.tips('不能少于60秒！', $(this), {
							tips: [1, 'red'],
							time: 0,
						});
					} else {
						layer.closeAll('tips');
					}
				});
				el.on('input', '[name=cc_count],[name=file_count]', function (ev) {
					var val = $(this).val();
					var num = $(this).prop('name').indexOf('cc') !== -1 ? 30 : 60;
					if (parseInt(val) < num) {
						layer.tips('不能小于' + num + '次！', $(this), {
							tips: [1, 'red'],
							time: 0,
						});
					} else {
						layer.closeAll('tips');
					}
				});
				el.on('click', '.form-radio', function (ev) {
					$(this).find('[name=push_method]').prop('checked', !$(this).find('[name=push_method]').prop('checked'));
					ev.stopPropagation();
					ev.preventDefault();
				});
				el.on('click', '.set_alarm_btn', function (ev) {
					var cc_time = $('[name=cc_time]').val(),
						cc_count = $('[name=cc_count]').val(),
						file_time = $('[name=file_time]').val(),
						file_count = $('[name=file_count]').val(),
						send_type = $('input[name="push_method"]:checked').val();
					if (cc_time < 60 || file_time < 60) {
						return layer.msg('访问时间不能少于60秒');
					}
					if (cc_count < 30) {
						return layer.msg('CC告警访问次数不能小于30次');
					}
					if (file_count < 60) {
						return layer.msg('封锁IP总数告警访问次数不能小于60次');
					}
					var param = {
						cc: JSON.stringify({
							cycle: cc_time,
							limit: cc_count,
							status: $('#cc_switch').prop('checked'),
						}),
						file: JSON.stringify({
							cycle: file_time,
							limit: file_count,
							status: $('#file_switch').prop('checked'),
						}),
						version: JSON.stringify({
							status: $('#version_switch').prop('checked'),
						}),
						webshell: JSON.stringify({
							status: $('#webshell_switch').prop('checked'),
						}),
						vul: JSON.stringify({
							status: $('#vul_switch').prop('checked'),
						}),
						send: JSON.stringify({
							status: true,
							send_type: send_type ? send_type : '',
						}),
					};
					bt_tools.send(
						{ url: '/plugin?action=a&name=btwaf&s=Set_Alarm', data: param },
						function (res) {
							bt_tools.msg(res);
						},
						'设置告警信息'
					);
				});
			}
		);
	},
	/**
	 * @description 渲染告警日志
	 * */
	render_alarm_logs: function () {
		bt_tools.table({
			el: '#alarm-logs-table',
			url: '/plugin?action=a&name=btwaf&s=get_log_send',
			load: true,
			column: [
				{
					fid: 'log',
					title: '标题',
				},
				{
					fid: 'addtime',
					width: '150px',
					title: '时间',
				},
			],
			tootls: [
				{
					type: 'page',
					numberStatus: true, //　是否支持分页数量选择,默认禁用
					jump: true, //是否支持跳转分页,默认禁用
				},
			],
		});
	},
	/**
	 * @description 渲染操作日志列表
	 * @param {Object} obj 页数,点击页码时调用的函数
	 */
	render_logs_data: function (obj, callback) {
		var that = this;
		if (obj == undefined) obj = { p: 1 };
		var search = obj.search || '';
		this.ajaxTask('get_gl_logs', { p: obj.p, search: search }, function (res) {
			that.refresh_table_view({
				el: '#logs_table',
				form_id: 'logs_table', //用于重置
				config: [
					{ fid: 'log', width: '70%', title: '详情' },
					{ fid: 'addtime', title: '操作时间', width: '180px', style: 'text-align: right;' },
				],
				data: res.data,
				page: res.page,
				done: function (res, obj) {
					$('.search-input').val(search);
					$('.search-input')
						.unbind('keyup')
						.on('keyup', function (e) {
							if (e.keyCode == 13) {
								if ($(this).val() !== '') that.render_logs_data({ p: 1, tojs: obj.tojs, search: $(this).val() });
							}
						});
					$('.glyphicon-search')
						.unbind('click')
						.on('click', function () {
							if ($(this).prev().val() !== '') that.render_logs_data({ p: 1, tojs: obj.tojs, search: $(this).prev().val() });
						});
					$('.waf_page a').on('click', function () {
						var _p = $(this).prop('href').split('=')[1];
						that.render_logs_data({ p: _p, tojs: obj.tojs, search: search });
						return false;
					});
				},
			});
		});
	},
	/**
	 * @description 最新渲染全局配置页面
	 */
	new_render_overall_data: function () {
		var that = this;
		$('[data-type=overall] .global-set-cont .global-search-box').nextAll().remove();
		var _cont = $('.global-set-cont');
		this.ajaxTask('get_config', function (res) {
			that.overall_config = res;
			_cont.append(
				'<div class="global-set-item global">\
				<div class="global-set-item-title">全局</div>\
				<div class="global-set-item-body ' +
					(res.open ? 'bg-green' : 'bg-red') +
					'">\
					<div class="body-cont">\
						<div class="item-left">防火墙开关</div>\
						<div class="item-right">\
							<input class="btswitch btswitch-ios" id="waf_swicth_all" type="checkbox" ' +
					(res.open ? 'checked' : '') +
					'>\
							<label class="btswitch-btn" for="waf_swicth_all" onclick="bt_waf.waf_switch()" style="font-size:12px"></label>\
						</div>\
					</div>\
					<div class="body-cont">\
						<div>此开关关闭后所有防护将失效</div>\
						<div>\
							<button class="btn btn-default btn-sm waf_all_text ml20">模拟攻击</button>\
							<button class="btn btn-default btn-sm import_waf_config ml20">导出配置</button>\
							<button class="btn btn-default btn-sm export_waf_config ml20">导入配置</button>\
							<button class="btn btn-default btn-sm set_default_settings ml20">恢复默认配置</button>\
						</div>\
					</div>\
				</div>\
			</div>'
			);
			for (var i = 0; i < that.overall_show_config.length; i++) {
				var _type = that.overall_config[that.overall_show_config[i]['type']];
				if (that.overall_show_config[i]['ps'] === undefined) that.overall_show_config[i]['ps'] = _type !== undefined ? _type['ps'] : '';
				that.overall_show_config[i]['status'] = _type != undefined ? _type['status'] : '';
				that.overall_show_config[i]['open'] = _type != undefined ? _type['open'] : '';
			}
			that.overall_show_config[1].status = that.overall_config.cc.status; //攻击次数拦截
			that.overall_show_config[10].open = that.overall_config.webshell_opens; //Webshell查杀
			that.overall_show_config[11].open = that.overall_config.is_browser; //非浏览器拦截
			that.overall_show_config[12].status = ''; //HTTP请求类型过滤
			that.overall_show_config[12].open = '';
			// 		that.overall_show_config[11].status = '';            //状态码过滤
			// 		that.overall_show_config[11].open = '';
			that.overall_show_config[7].status = ''; //UA白名单
			that.overall_show_config[7].open = '';
			that.overall_show_config[8].status = ''; //UA黑名单
			that.overall_show_config[8].open = '';
			that.overall_show_config[3].status = that.overall_config.cc.status; //IP黑名单
			that.overall_show_config[6].status = that.overall_config.get.status; //URL黑名单
			// 		that.overall_show_config[20].status = that.overall_config.get.status;   //Webshell查杀
			// 		that.overall_show_config[20].open = that.overall_config.webshell_open;
			that.overall_show_config[19].status = that.overall_config.scan.status; //目录扫描防御
			that.overall_show_config[19].open = that.overall_config.scan_conf.open; //目录扫描防御
			that.overall_show_config[22].status = ''; //恶意文件上传防御                           //From-data协议
			that.overall_show_config[22].open = that.overall_config.file_upload.open;
			that.overall_show_config[22].status = that.overall_config.file_upload.status;
			that.overall_show_config[23].open = that.overall_config.http_open; //HTTP包
			that.overall_show_config[24].status = ''; //URL关键词拦截
			that.overall_show_config[24].open = '';
			that.overall_show_config[4].status = ''; //单URL CC防御
			that.overall_show_config[4].open = '';
			that.overall_show_config[29].status = ''; //人机验证白名单
			that.overall_show_config[29].open = '';
			that.overall_show_config[30].status = that.overall_config.other_rule.status; //人机验证白名单
			that.overall_show_config[30].open = that.overall_config.other_rule.open;

			//渲染页面内容
			$.each(that.new_config_arr, function (index, item) {
				var _html = '',
					list = [],
					i = -1;
				item.forEach(function (_item, _index) {
					var arr = that.overall_show_config.filter(function (_item2) {
						return _item2.type == _item;
					});
					if (arr.length > 1) {
						i += 1;
						list.push(arr[i]);
					} else {
						list.push(arr[0]);
					}
				});
				if (index == 'black_white_list') {
					//升序
					list.sort(function (a, b) {
						return a.sortId - b.sortId;
					});
				}
				list.forEach(function (_list, idx) {
					var _title = [],
						_arry = '',
						_type = _list.type,
						_status_html = '';
					switch (_type) {
						case 'cc':
						case 'cc_tolerate':
							_title = ['设置规则'];
							break;
						case 'get':
						case 'post':
						case 'user-agent':
						case 'cookie':
						case 'other_rule':
							_title = ['响应内容', '设置规则'];
							break;
						case 'sql_injection':
						case 'xss_injection':
							_title = ['响应内容'];
							break;
						case 'file_upload':
							_title = ['响应内容', '设置'];
							break;
						case 'spider':
						case 'drop_abroad':
							_title = ['同步', '设置'];
							break;
						case 'url_black':
						case 'drop_china':
						case 'static_code_config':
						case 'method_type':
						case 'ua_black':
						case 'ua_white':
						case 'ip_black':
						case 'ip_white':
						case 'url_white':
						case 'scan':
						case 'set_scan_conf':
						case 'sensitive_text':
						case 'body_intercept':
						case 'api_defense':
						case 'key_words':
						case 'url_request_type_refuse':
						case 'cc_uri_frequency':
						case 'golbls_cc':
							_title = ['设置'];
							break;
					}
					if (_list['status']) {
						var _li = '',
							_title_div = '';
						var statusList = [
							{ title: '200 正常访问', value: 200 },
							{ title: '404 文件不存在', value: 404 },
							{ title: '403 拒绝访问', value: 403 },
							{ title: '444 关闭连接', value: 444 },
							{ title: '500 应用程序错误', value: 500 },
							{ title: '502 连接超时', value: 502 },
							{ title: '503 服务器不可用', value: 503 },
						];
						for (var i = 0; i < statusList.length; i++) {
							var val = statusList[i].value,
								title = statusList[i].title;
							var selected = _list.status === val ? 'selected' : '';
							if (selected) _title_div = '<button class="btn btn-default btn-sm code_title"><span title="' + title + '">响应状态 [' + val + ']</span><span class="icon-xiala"></span></button>';
							_li += '<li class="' + selected + '" data-value="' + val + '" title="' + title + '">' + title + '</li>';
						}
						var obj = _type == 'cc_tolerate' || _type == 'ip_black' ? 'cc' : _type == 'url_black' || _type == 'webshell_open' ? 'get' : _type;
						_status_html = '<div class="statusCode code_' + obj + '" data-obj="' + obj + '">' + _title_div + '<ul class="hide">' + _li + '</ul></div>';
					}
					//按钮
					_title.forEach(function (_title2, _index2) {
						_arry +=
							'<button class="btn btn-default btn-sm ml20 overall_table_tools ' +
							(_title2.indexOf('设置') !== -1 ? 'b_green' : '') +
							'" data-index="' +
							_index2 +
							'" data-name="' +
							_list.name +
							'">' +
							_title2 +
							'</button>';
					});
					//(_list.note ? '<a class="bt-ico-ask" title="'+ _list.note +'">?</a>':'')
					_html +=
						'<div class="global-set-item-body"><div class="body-cont">\
							<div class="item-left">' +_list.name +'</div>' +
						    (_list.open !== '' && _list.open !== undefined? '<div class="item_right">\
						    <input class="btswitch btswitch-ios" id="close_open_' +_type +idx +'" type="checkbox" ' +
							  (_list.open ? 'checked' : '') +'>\
							<label class="btswitch-btn overall_table_open" data-type="' +_list.type +'" data-name="' +_list.name +'" for="close_open_' +
							  _type +idx +'"></label></div>': '') +
						    '</div>\
							<div class="body-cont"><div>' +_list.ps +
						        (_list.type === 'drop_abroad' ? '<br><a class="btlink" onclick="$(\'.ng-waf-box .tab-list .tabs-item:eq(4)\').click()">' + res.drop_abroad_count + '个网站已开启此功能</a>' : '') +
						    '</div>\
							<div>' +_status_html +_arry +'</div></div></div>';});
							
				    _cont.append(
					    '<div class="global-set-item ' +index +'"><div class="global-set-item-title">' +
						    that.new_config_arr_name[index] +
						'</div>' 
						+_html +'</div>'
				    );
				//点击事件
				//滚动切换tab
				$(window).scroll(function () {
					var top = $(this).scrollTop();
					var _el = $('.global-set-box .global-set-cont .global-set-item'),
						_li = $('.global-set-box .global-set-tab li');
					var height = 0;
					if (top !== 0) {
					}
					for (var i = 0; i < _el.length; i++) {
						height += _el.eq(i).height();
						if (top <= height) {
							if ($(this)[0].scrollTop + $(this).height() >= $(this)[0].scrollHeight) {
								_li
									.eq(_li.length - 1)
									.addClass('on')
									.siblings()
									.removeClass('on');
							} else if (top === 0) {
								_li.eq(0).addClass('on').siblings().removeClass('on');
							} else {
								_li.eq(i).addClass('on').siblings().removeClass('on');
							}
							return;
						}
					}
				});
				//tab切换 滚动到对应的位置
				$('.global-set-box .global-set-tab li')
					.unbind('click')
					.click(function () {
						var $this = $(this),
							index = $this.index(),
							_el = $('.global-set-box .global-set-cont .global-set-item'),
							_top = 0;
						for (var i = 0; i < _el.length; i++) {
							if (index != 0 && i < index) {
								_top += _el.eq(i).height() + 16;
							}
						}
						$(window).scrollTop(_top);
						$this.addClass('on').siblings().removeClass('on');
					});

				//全局搜索事件
				that.global_search($('.global-set-box .bt-search .search-input').val());
				$('.global-set-box .bt-search .search-input').on('input', function (e) {
					$(this).next().click();
				});
				$('.global-set-box .bt-search .glyphicon-search')
					.unbind('click')
					.click(function () {
						var val = $(this).prev().val();
						if (val) {
							$('.global-set-box .global-set-tab li').removeClass('on');
						}
						that.global_search(val);
						that.global_event();
						$('.ng-item')
							.prev()
							.css({
								width: $('.ng-item').width(),
							});
					});

				that.global_event();

				$('.ng-waf-box').css('min-height', 'auto');
				// //高度限制
				// _cont.css('height',$(window).height() - 280)
				// //窗口大小改变
				$(window).resize(function () {
					// _cont.css('height',$(window).height() - 280)
					$('.ng-item')
						.prev()
						.css({
							width: $('.ng-item').width(),
						});
				});
			});
		});
	},
	//全局点击事件
	global_event: function () {
		var that = this;
		//开关点击事件
		$('.overall_table_open')
			.unbind('click')
			.click(function () {
				var $this = $(this);
				var open = $this.prev().prop('checked'),
					name = $this.data('name'),
					type = $this.data('type');
				if (open) {
					layer.confirm(
						(open ? '关闭后，此功能在所有网站中会停止防护' : '开启' + name) + '，是否继续操作？',
						{
							title: (open ? '关闭' : '开启') + name,
							closeBtn: 2,
							icon: 13,
							cancel: function () {
								$this.prev().prop('checked', open);
							},
						},
						function () {
							that.ajaxTask('set_obj_open', { obj: type }, function (res) {
								// if(res.status) that.refresh_data_total('overall');
								layer.msg(res.msg, { icon: res.status ? 1 : 2 });
							});
						},
						function () {
							$this.prev().prop('checked', open);
						}
					);
				} else {
					that.ajaxTask('set_obj_open', { obj: type }, function (res) {
						// if(res.status) that.refresh_data_total('overall');
						layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					});
				}
			});
		//按钮点击事件
		$('.global-set-box .overall_table_tools')
			.unbind('click')
			.click(function () {
				var name = $(this).data('name'),
					index = $(this).data('index');
				var row = that.overall_show_config.filter(function (item) {
					return item.name == name;
				})[0];
				switch (row.type) {
					case 'cc': //cc防御
						that.set_cc_rule_view({
							cc_cycle: that.overall_config.cc.cycle,
							cc_limit: that.overall_config.cc.limit,
							cc_endtime: that.overall_config.cc.endtime,
							increase_wu_heng: that.overall_config.increase_wu_heng,
							increase: that.overall_config.cc.increase,
							cc_increase_type: that.overall_config.cc.cc_increase_type,
							mode: that.overall_config.cc_mode,
							cc_type_status: that.overall_config.cc_type_status,
							cc: that.overall_config.cc,
							retry: that.overall_config.retry,
						});

						break;
					case 'static_code_config':
						layer.msg('功能暂时下架,优化后开放！');
						// 			that.set_static_code_config();
						break;
					case 'method_type':
						that.set_http_rule_view();
						break;
					case 'get': //GET-URI过滤 或 SQL注入防御
					case 'post': //XSS防御
					case 'user-agent': //恶意文件上传防御
					case 'cookie': //cookie
					case 'other_rule':
						if (index) {
							that.set_other_rule_view(row);
						} else {
							if (row.type === 'other_rule') bt.pub.on_edit_file(0, '/www/server/btwaf/html/' + that.overall_config[row.type].reqfile);
							else bt.pub.on_edit_file(0, '/www/server/btwaf/html/' + (row.type != 'user-agent' ? row.type : 'user_agent') + '.html');
						}
						break;
					case 'sql_injection':
					case 'xss_injection':
					case 'file_upload':
						if (index) {
							that.set_file_upload_view();
						} else {
							bt.pub.on_edit_file(0, '/www/server/btwaf/html/' + that.overall_config[row.type].reqfile);
						}
						break;
					case 'drop_abroad': //禁止海外访问
						if (index) {
							that.set_ip_region_view(row.type);
						} else {
							that.ajaxTask('sync_cnlist', function (res) {
								layer.msg(res.msg, { icon: res.status ? 1 : 2 });
							});
						}
						break;
					case 'drop_china':
						that.set_ip_region_view(row.type);
						break;
					case 'cc_tolerate': //攻击次数拦截
						that.set_cc_tolerate_view({
							cycle: that.overall_config.retry_cycle,
							retry: that.overall_config.retry,
							time: that.overall_config.retry_time,
						});
						break;
					case 'spider': //蜘蛛池
						if (index) {
							that.get_spider_view();
						} else {
							that.ajaxTask('get_zhizu_list2233', function (res) {
								layer.msg(res.msg, { icon: res.status ? 1 : 2 });
							});
						}
						break;
					case 'ua_white': //ua白名单
					case 'ua_black': //ua黑名单
						that.set_ua_white_view(row.type);
						break;
					case 'ip_white': //IP白名单
					case 'ip_black': //IP黑名单
						that.set_ip_region_view(row.type);
						break;
					case 'url_white': //URL白名单
					case 'url_black': //URL黑名单
					case 'api_defense': //API接口防御
					case 'key_words': //URL关键词拦截
					case 'golbls_cc': //人机验证白名单
						that.set_other_rule_one_view({ type: row.type });
						break;
					case 'scan': //常见扫描器
						that.set_scan_rule_view();
						break;
					case 'set_scan_conf': //目录扫描防御
						that.set_scan_conf_view();
						break;
					case 'sensitive_text': //敏感字替换
						// layer.msg('功能暂时下架,优化后开放！')
						that.set_sensitive_text_view(false);
						break;
					case 'body_intercept': //违禁词拦截
						that.set_body_intercept_view(row.type);
						break;
					case 'url_request_type_refuse': //URL请求类型拦截
						that.set_url_request_type_refuse_view();
						break;
					case 'cc_uri_frequency': //单URL CC防御
						that.set_cc_uri_frequency_view();
						break;
				}
			});
		//状态码点击事件
		$('.global-set-box .statusCode .code_title')
			.unbind('click')
			.click(function (e) {
				var $this = $(this),
					parent = $(this).parent(),
					title = $this.find('span:eq(0)').prop('title');
				var rect = $this.offset();
				$this.next().css({
					top: rect.top + 30 - $(window).scrollTop() + 'px',
					left: rect.left + 'px',
					right: 'auto',
					bottom: 'auto',
				});
				$this
					.next()
					.find('li[title="' + title + '"]')
					.addClass('selected')
					.siblings()
					.removeClass('selected');
				$('.statusCode ul').addClass('hide');
				parent.find('ul').toggleClass('hide');
				$(document).one('click', function () {
					$('.statusCode ul').addClass('hide');
				});
				e.stopPropagation();
			});
		//状态码选择事件
		$('.global-set-box .statusCode ul li')
			.unbind('click')
			.click(function (e) {
				var parent = $(this).parent().parent(),
					obj = parent.data('obj'),
					value = $(this).data('value'),
					title = $(this).html();
				parent
					.find('.code_title span:eq(0)')
					.text('响应状态 [' + value + ']')
					.prop('title', title);
				that.ajaxTask(obj === 'set_scan_conf' ? obj : 'set_obj_status', { obj: obj, statusCode: value }, function (res) {
					if (res.status) {
						// that.refresh_data_total('overall');
						$('.global-set-cont .statusCode.code_' + obj + ' .code_title')
							.find('span:eq(0)')
							.text('响应状态 [' + value + ']')
							.prop('title', title);
					}
					layer.msg(res.msg, { icon: res.status ? 1 : 2 });
				});
			});
	},
	//全局搜索
	global_search: function (search) {
		var _this = this;
		var lines = [],
			lines1 = [];
		var items = $('.global-set-box .global-set-cont .global-set-item-body'),
			items1 = $('.global-set-box .global-set-cont .global-set-item-title');
		lines.push.apply(lines, items.filter(':contains('.concat(search, ')')));
		lines1.push.apply(lines1, items1.filter(':contains('.concat(search, ')')));
		if (search) {
			items.hide();
			$('.global-set-box .global-set-item').hide();
			$.each(lines, function (index, item) {
				$(lines[index]).show().parent().show();
				var html = $(item).html();
				var reg1 = new RegExp('<i>', 'g');
				var reg2 = new RegExp('</i>', 'g');
				var newHtml = html.replace(reg1, '').replace(reg2, '');
				$(item).html(newHtml);
			});
			$.each(lines1, function (index, item) {
				$(lines1[index]).show().parent().show();
				var html = $(item).html();
				var reg1 = new RegExp('<i>', 'g');
				var reg2 = new RegExp('</i>', 'g');
				var newHtml = html.replace(reg1, '').replace(reg2, '');
				$(item).html(newHtml);
			});
			$.each(lines, function (index, item) {
				var html = $(item).html();
				if (html && html.indexOf('<i>') === -1) {
					var nHtml = _this.searchHTML(search, html);
					$(item).html(nHtml);
				}
			});
			$.each(lines1, function (index, item) {
				var html = $(item).html();
				if (html && html.indexOf('<i>') === -1) {
					var nHtml = _this.searchHTML(search, html);
					$(item).html(nHtml);
				}
			});
			$.each(lines, function (index, item) {
				$(item).parent().parent().show();
			});
			$.each(lines1, function (index, item) {
				$(item).parent().show();
				$(item).nextAll().show();
			});
			if (lines.length === 0 && lines1.length === 0) {
				$('.global-search-box').removeClass('hide');
				$('.global-search-box-text')
					.show()
					.text('很抱歉，没有找到有关"' + search + '"的信息');
			} else {
				$('.global-set-tab').children().eq(0).addClass('on').siblings().removeClass('on');
				$('.global-search-box').addClass('hide');
			}
		} else {
			items.show();
			$('.global-search-box').addClass('hide');
			$('.global-set-box .global-set-item').show();
			$('.global-set-box .global-set-tab li').eq(0).addClass('on').siblings().removeClass('on');
			$.each(items, function (index, item) {
				var html = $(item).html();
				var reg1 = new RegExp('<i>', 'g');
				var reg2 = new RegExp('</i>', 'g');
				var newHtml = html.replace(reg1, '').replace(reg2, '');
				$(item).html(newHtml);
			});
			$.each(items1, function (index, item) {
				var html = $(item).html();
				var reg1 = new RegExp('<i>', 'g');
				var reg2 = new RegExp('</i>', 'g');
				var newHtml = html.replace(reg1, '').replace(reg2, '');
				$(item).html(newHtml);
			});
		}
	},
	//全局搜索高亮
	searchHTML: function (search, html) {
		var expr = new RegExp(search, 'gi');
		var container = $('<div>').html(html);
		var elements = container.find('*').andSelf();
		var textNodes = elements.contents().not(elements);
		textNodes.each(function () {
			var matches = this.nodeValue.match(expr);
			if (matches) {
				var parts = this.nodeValue.split(expr);
				for (var n = 0; n < parts.length; n++) {
					if (n) {
						$('<i>')
							.text(matches[n - 1])
							.insertBefore(this);
					}
					if (parts[n]) {
						$(document.createTextNode(parts[n])).insertBefore(this);
					}
				}
				$(this).remove();
			}
		});
		return container.html();
	},
	/**全局配置页面方法开始 */
	/**
	 * @description 渲染全局页面
	 * @param {String} obj 配置项
	 */
	render_overall_data: function () {
		var that = this;
		this.ajaxTask('get_config', function (res) {
			that.overall_config = res;
			for (var i = 0; i < that.overall_show_config.length; i++) {
				var _type = that.overall_config[that.overall_show_config[i]['type']];
				if (that.overall_show_config[i]['ps'] === undefined) that.overall_show_config[i]['ps'] = _type !== undefined ? _type['ps'] : '';
				that.overall_show_config[i]['status'] = _type != undefined ? _type['status'] : '';
				that.overall_show_config[i]['open'] = _type != undefined ? _type['open'] : '';
			}
			that.overall_show_config[1].status = that.overall_config.cc.status; //攻击次数拦截
			that.overall_show_config[10].open = that.overall_config.webshell_opens; //Webshell查杀
			that.overall_show_config[11].open = that.overall_config.is_browser; //非浏览器拦截
			that.overall_show_config[12].status = ''; //HTTP请求类型过滤
			that.overall_show_config[12].open = '';
			// 		that.overall_show_config[11].status = '';            //状态码过滤
			// 		that.overall_show_config[11].open = '';
			that.overall_show_config[7].status = ''; //UA白名单
			that.overall_show_config[7].open = '';
			that.overall_show_config[8].status = ''; //UA黑名单
			that.overall_show_config[8].open = '';
			that.overall_show_config[3].status = that.overall_config.cc.status; //IP黑名单
			that.overall_show_config[6].status = that.overall_config.get.status; //URL黑名单
			// 		that.overall_show_config[20].status = that.overall_config.get.status;   //Webshell查杀
			// 		that.overall_show_config[20].open = that.overall_config.webshell_open;
			that.overall_show_config[19].status = that.overall_config.scan.status; //目录扫描防御
			that.overall_show_config[19].open = that.overall_config.scan_conf.open; //目录扫描防御
			that.overall_show_config[22].status = ''; //From-data协议
			that.overall_show_config[22].open = that.overall_config.from_data;
			that.overall_show_config[23].open = that.overall_config.http_open; //HTTP包
			that.overall_show_config[24].status = ''; //URL关键词拦截
			that.overall_show_config[24].open = '';
			that.overall_show_config[4].status = ''; //单URL CC防御
			that.overall_show_config[4].open = '';

			that.refresh_table_view({
				el: '#overall_table',
				form_id: 'overall_table', //用于重置
				height: 690,
				config: [
					{ fid: 'name', title: '名称', width: '120px' },
					{ fid: 'ps', title: '描述', width: '35%' },
					{
						fid: 'status',
						type: 'link',
						title: '响应',
						width: '50px',
						templet: function (row) {
							var _type = row.type,
								_html = '',
								_title = '',
								_li = '';
							statusList = [
								{ title: '200 正常访问', value: 200 },
								{ title: '404 文件不存在', value: 404 },
								{ title: '403 拒绝访问', value: 403 },
								{ title: '444 关闭连接', value: 444 },
								{ title: '500 应用程序错误', value: 500 },
								{ title: '502 连接超时', value: 502 },
								{ title: '503 服务器不可用', value: 503 },
							];
							if (_type == 'cc_tolerate') _type = 'cc';
							if (_type == 'ip_black') _type = 'cc';
							if (_type == 'url_black') _type = 'get';
							if (_type == 'webshell_open') _type = 'get';
							if (row['status']) {
								for (var i = 0; i < statusList.length; i++) {
									var val = statusList[i].value,
										title = statusList[i].title;
									var selected = row.status === val ? 'selected' : '';
									if (selected) _title = '<div class="code_title"><span title="' + title + '">' + val + '</span><i class="icon-xiala"></i></div>';
									_li += '<li class="' + selected + '" data-value="' + val + '" title="' + title + '">' + title + '</li>';
								}
							}
							_html = '<div class="statusCode" data-obj="' + _type + '">' + _title + '<ul class="hide">' + _li + '</ul></div>';
							return row['status'] ? _html : '<span>--</span>';
						},
					},
					{
						fid: 'open',
						type: 'btswitch',
						title: '状态',
						width: '60px',
						event: function (row, index, event) {
							layer.confirm(
								'请确定是否' + (row.open ? '关闭' : '开启') + row.name + '开关？',
								{
									title: '状态设置',
									closeBtn: 2,
									icon: 13,
									cancel: function () {
										$('#close_open_overall_table_' + index).prop('checked', row.open);
									},
								},
								function () {
									that.ajaxTask('set_obj_open', { obj: row.type }, function (res) {
										if (res.status) that.refresh_data_total('overall');
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								},
								function () {
									$('#close_open_overall_table_' + index).prop('checked', row.open);
								}
							);
						},
					},
					{
						fid: 'tools',
						title: '操作',
						style: 'text-align: right;',
						width: '120px',
						group: function (row, index) {
							var _title = [],
								_arry = [];
							switch (row.type) {
								case 'cc':
									_title = ['初始规则'];
									break;
								case 'cc_tolerate':
									_title = ['初始规则'];
									break;
								case 'url_black':
									_title = ['设置'];
									break;
								case 'get':
								case 'post':
								case 'user-agent':
								case 'cookie':
									_title = ['规则', '响应内容'];
									break;
								case 'spider':
								case 'drop_abroad':
									_title = ['设置', '同步'];
									break;
								case 'drop_china':
									_title = ['设置'];
									break;
								case 'static_code_config':
								case 'method_type':
								case 'ua_black':
								case 'ua_white':
								case 'ip_black':
								case 'ip_white':
								case 'url_white':
								case 'scan':
								case 'set_scan_conf':
								case 'sensitive_text':
								case 'body_intercept':
								case 'api_defense':
								case 'key_words':
								case 'url_request_type_refuse':
								case 'cc_uri_frequency':
									_title = ['设置'];
									break;
							}
							for (var j = 0; j < _title.length; j++) {
								_arry.push({
									title: _title[j],
									event: function (row, index, ev, _that) {
										var j = _that.index();
										switch (row.type) {
											case 'cc': //cc防御
												that.set_cc_rule_view({
													cc_cycle: that.overall_config.cc.cycle,
													cc_limit: that.overall_config.cc.limit,
													cc_endtime: that.overall_config.cc.endtime,
													increase_wu_heng: that.overall_config.increase_wu_heng,
													increase: that.overall_config.cc.increase,
													cc_increase_type: that.overall_config.cc.cc_increase_type,
													mode: that.overall_config.cc_mode,
													cc_type_status: that.overall_config.cc_type_status,
													cc: that.overall_config.cc,
													retry: that.overall_config.retry,
												});

												break;
											case 'static_code_config':
												layer.msg('功能暂时下架,优化后开放！');
												// 			that.set_static_code_config();
												break;
											case 'method_type':
												that.set_http_rule_view();
												break;
											case 'get': //GET-URI过滤 或 SQL注入防御
											case 'post': //XSS防御
											case 'user-agent': //恶意文件上传防御
											case 'cookie': //cookie
												if (j == 0) {
													that.set_other_rule_view(row);
												} else {
													bt.pub.on_edit_file(0, '/www/server/btwaf/html/' + (row.type != 'user-agent' ? row.type : 'user_agent') + '.html');
												}
												break;
											case 'drop_abroad': //禁止海外访问
												if (j == 0) {
													that.set_ip_region_view(row.type);
												} else {
													that.ajaxTask('sync_cnlist', function (res) {
														layer.msg(res.msg, { icon: res.status ? 1 : 2 });
													});
												}
												break;
											case 'drop_china':
												that.set_ip_region_view(row.type);
												break;
											case 'cc_tolerate': //攻击次数拦截
												that.set_cc_tolerate_view({
													cycle: that.overall_config.retry_cycle,
													retry: that.overall_config.retry,
													time: that.overall_config.retry_time,
												});
												break;
											case 'spider': //蜘蛛池
												if (j == 0) {
													that.get_spider_view();
												} else {
													that.ajaxTask('get_zhizu_list2233', function (res) {
														layer.msg(res.msg, { icon: res.status ? 1 : 2 });
													});
												}
												break;
											case 'ua_white': //ua白名单
											case 'ua_black': //ua黑名单
												if (j == 0) {
													that.set_ua_white_view(row.type);
												} else {
													bt.pub.on_edit_file(0, '/www/server/btwaf/html/' + (row.type != 'ua_black' ? row.type : 'ua_black') + '.html');
												}
												break;
											case 'ip_white': //IP白名单
											case 'ip_black': //IP黑名单
												that.set_ip_region_view(row.type);
												break;
											case 'url_white': //URL白名单
											case 'url_black': //URL黑名单
											case 'api_defense': //API接口防御
											case 'key_words': //URL关键词拦截
												that.set_other_rule_one_view({ type: row.type });
												break;
											case 'scan': //常见扫描器
												that.set_scan_rule_view();
												break;
											case 'set_scan_conf': //目录扫描防御
												that.set_scan_conf_view();
												break;
											case 'sensitive_text': //敏感字替换
												// layer.msg('功能暂时下架,优化后开放！')
												that.set_sensitive_text_view(false);
												break;
											case 'body_intercept': //违禁词拦截
												that.set_body_intercept_view(row.type);
												break;
											case 'url_request_type_refuse': //URL请求类型拦截
												that.set_url_request_type_refuse_view();
												break;
											case 'cc_uri_frequency': //单URL CC防御
												that.set_cc_uri_frequency_view();
												break;
										}
									},
								});
							}
							return _arry;
						},
					},
				],
				data: that.overall_show_config,
				done: function () {
					// 表格滚动隐藏解决方案内容
					$('#overall_table').scroll(function (e) {
						$('.statusCode ul').addClass('hide');
					});
					$(window).scroll(function (e) {
						$('.statusCode ul').addClass('hide');
					});
					$('#overall_table .statusCode .code_title').click(function (e) {
						var $this = $(this),
							parent = $(this).parent();
						var rect = $this.offset();
						$this.next().css({
							top: rect.top + 30 - $(window).scrollTop() + 'px',
							left: rect.left + 'px',
							right: 'auto',
							bottom: 'auto',
						});
						$('.statusCode ul').addClass('hide');
						parent.find('ul').toggleClass('hide');
						$(document).one('click', function () {
							$('.statusCode ul').addClass('hide');
						});
						e.stopPropagation();
					});
					$('#overall_table .statusCode ul li').click(function (e) {
						var parent = $(this).parent().parent(),
							obj = parent.data('obj'),
							value = $(this).data('value'),
							title = $(this).html();
						parent.find('.code_title span').text(value).prop('title', title);
						that.ajaxTask(obj === 'set_scan_conf' ? obj : 'set_obj_status', { obj: obj, statusCode: value }, function (res) {
							if (res.status) {
								that.refresh_data_total('overall');
							}
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
						});
					});
				},
			});
		});
	},
	/**
	 * 渲染单URL CC防御
	 */
	render_cc_uri_frequency_body: function () {
		var that = this;
		this.ajaxTask('get_config', function (res) {
			var _array = [];
			$.each(res.cc_uri_frequency, function (index, item) {
				_array.push({ url: index, frequency: item.frequency, cycle: item.cycle });
			});
			that.refresh_table_view({
				el: '#cc_uri_frequencye_table',
				form_id: 'cc_uri_frequencye_table',
				height: 305,
				config: [
					{
						title: 'URL',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 230px;" title="' + row.url + '">' + row.url + '</span>';
						},
					},
					{
						title: '访问次数',
						width: '86px',
						templet: function (row) {
							return '<span class="overflow_hide" style="width: 70px;" title="' + row.frequency + '">' + row.frequency + '</span>';
						},
					},
					{
						title: '时间范围',
						width: '96px',
						templet: function (row) {
							return '<span class="overflow_hide" style="width: 80px;" title="' + row.cycle + ' 秒">' + row.cycle + ' 秒</span>';
						},
					},
					{
						title: '操作',
						style: 'text-align: right;',
						group: [
							{
								title: '修改',
								event: function (row, index) {
									that.edit_cc_uri_frequency(false, row);
								},
							},
							{
								title: '删除',
								event: function (row, index) {
									that.ajaxTask('del_cc_uri_frequency', { url: row.url }, function (res) {
										if (res.status) that.render_cc_uri_frequency_body();
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								},
							},
						],
					},
				],
				data: _array,
				done: function (rdata) {},
			});
		});
	},
	/**
	 * @description 设置状态码配置
	 */
	set_static_code_config: function () {
		var that = this;
		layer.open({
			type: 1,
			title: '状态码列表',
			area: ['550px', '500px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="code_table" style="padding:25px 15px">\
					<div class="waf-form-input">\
						<button class="btn btn-success btn-sm va0 add_code">添加</button>\
					</div>\
					<div id="code_table"></div>\
					<ul class="help-info-text c7 ptb10">\
						<li style="color:red;">注意:如果你拦截的状态码是403那么添加后拦截页面是不会显示的</li>\
						<li>建议加500报错进行拦截,有效防御信息泄露</li>\
					</ul>\
				</div>',
			success: function () {
				that.render_static_code_list();
				$('.add_code').click(function () {
					that.open_code_view_dialog(true);
				});
			},
		});
	},
	/**
	 * @description HTTP请求过滤视图
	 */
	set_http_rule_view: function () {
		var that = this;
		layer.open({
			type: 1,
			title: 'HTTP请求过滤',
			area: ['550px', '560px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="http_rule_table" style="padding:0">\
					<div class="tab_list">\
						<div class="tab_block active">请求类型过滤</div>\
						<div class="tab_block">请求头过滤</div>\
					</div>\
					<div class="pd15 http_filtering tabs_box">\
						<div id="http_filtering_table"></div>\
					</div>\
					<div class="pd15 header_filtering tabs_box" style="display:none">\
						<div class="waf-form-input">\
							<input type="text" class="waf-input" name="rule_header_filtering" style="width: 350px;" placeholder="请输入header名称" />\
							<input type="number" class="waf-input" name="rule_header_length" placeholder="长度" style="width: 95px;"/>\
							<button class="btn btn-success btn-sm va0 pull-right add_header_filtering">添加</button>\
						</div>\
						<div id="header_filtering_table"></div>\
					</div>\
					<div class="pd15 statement_analyze tabs_box" style="display:none">\
						<div id="statement_analyze_table"></div>\
					</div>\
					<ul class="waf_tips_list mtl0 c7 plr20">\
						<li>默认对所有请求类型都放行，如需要关闭某个请求类型则关闭此类型的按钮</li>\
						<li>例如：只允许GET和POST进行访问，则关闭除GET和POST之外的所有类型</li>\
						<li style="display: none;">当前请求过滤为长度过滤限制</li>\
						<li style="display: none;">例如：host的值为小于500 则通过 大于500 则拦截</li>\
						<li style="display: none;">语义分析模块是内置的一个安全模块，就是所有的参数和值都会经过语义分析进行检测。如果检测为攻击则会进行拦截</li>\
					</ul>\
				</div>',
			success: function () {
				//  选项卡切换
				$('.tab_list .tab_block').click(function () {
					$(this).addClass('active').siblings().removeClass('active');
					$('.http_rule_table .waf_tips_list li').hide();
					if ($(this).index() == 0) {
						$('.http_filtering').show().siblings('.tabs_box').hide();
						that.render_http_rule_view(0);
						$('.http_rule_table .waf_tips_list li:eq(0),.http_rule_table .waf_tips_list li:eq(1)').show();
					} else if ($(this).index() == 1) {
						$('.header_filtering').show().siblings('.tabs_box').hide();
						that.render_http_rule_view(1);
						$('.http_rule_table .waf_tips_list li:eq(2),.http_rule_table .waf_tips_list li:eq(3)').show();
					} else {
						$('.statement_analyze').show().siblings('.tabs_box').hide();
						that.render_http_rule_view(2);
						$('.http_rule_table .waf_tips_list li:eq(4)').show();
					}
				});
				that.render_http_rule_view(0);

				//请求头添加
				$('.add_header_filtering').click(function () {
					var header_ = $('[name=rule_header_filtering]'),
						len_ = $('[name=rule_header_length]');
					if (header_.val() == '') return layer.msg('请求类型不能为空', { icon: 2 });
					if (len_.val() == '') return layer.msg('长度不能为空', { icon: 2 });
					that.ajaxTask('add_header_len', { header_type: header_.val(), header_type_len: len_.val() }, function (res) {
						if (res.status) {
							header_.val('');
							len_.val('');
							that.refresh_data_total('overall');
							setTimeout(function () {
								that.render_http_rule_view(1);
							}, 200);
						}
						layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					});
				});
			},
		});
	},
	/**
	 * @description 渲染http过滤视图
	 * @param {Number} type  [0]为请求过滤   [1]为请求头过滤
	 */
	render_http_rule_view: function (type) {
		var that = this,
			data_request = this.overall_config['method_type'],
			data_header = this.overall_config['header_len'],
			analyze_ = [
				['POST传参XSS防御', this.overall_config['post_is_xss'], 'post_is_xss'],
				['POST传参SQL注入防御', this.overall_config['post_is_sql'], 'post_is_sql'],
				['GET传参XSS防御', this.overall_config['get_is_xss'], 'get_is_xss'],
				['GET传参SQL注入防御', this.overall_config['get_is_sql'], 'get_is_sql'],
			];
		if (type == 0) {
			that.refresh_table_view({
				el: '#http_filtering_table',
				form_id: 'http_filtering_table', //用于重置
				height: 380,
				config: [
					{
						title: '请求类型',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 410px;" title="' + row[0] + '">' + row[0] + '</span>';
						},
					},
					{
						fid: '1',
						title: '状态',
						type: 'btswitch',
						width: '50px',
						style: 'text-align: center;',
						event: function (row, index, event) {
							that.ajaxTask('add_method_type', { method_type: row[0], check: row[1] ? 0 : 1 }, function (res) {
								if (res.status) {
									that.refresh_data_total('overall');
									setTimeout(function () {
										that.render_http_rule_view(0);
									}, 200);
								}
								layer.msg(res.msg, { icon: res.status ? 1 : 2 });
							});
						},
					},
				],
				data: data_request,
				done: function () {},
			});
		} else if (type == 1) {
			that.refresh_table_view({
				el: '#header_filtering_table',
				form_id: 'header_filtering_table', //用于重置
				height: 337,
				config: [
					{
						title: 'Header',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 260px;" title="' + row[0] + '">' + row[0] + '</span>';
						},
					},
					{
						title: '长度',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 45px;" title="' + row[1] + '">' + row[1] + '</span>';
						},
					},
					{
						title: '操作',
						width: '100px',
						style: 'text-align: right;',
						group: [
							{
								title: '编辑',
								event: function (row, index, event, el) {
									var _tr = $(el).parent().parent().parent();
									$(_tr)
										.find('td:eq(' + 1 + ')')
										.html('<input type="text" class="waf-input waf-rule-len" value="' + row[1] + '" style="width:60px"/>');
									$(_tr)
										.find('td:eq(' + 2 + ')')
										.html('<span><a class="btlink save_header_data" href="javascript:;">保存</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a class="btlink clear_header_data" href="javascript:;">取消</a></span>');
									$('.save_header_data').click(function (e) {
										that.ajaxTask('edit_header_len', { header_type: row[0].toLowerCase(), header_type_len: $('.waf-rule-len').val() }, function (res) {
											if (res.status) {
												that.refresh_data_total('overall');
												setTimeout(function () {
													that.render_http_rule_view(1);
												}, 200);
											}
											layer.msg(res.msg, { icon: res.status ? 1 : 2 });
										});
									});
									$('.clear_header_data').click(function (e) {
										that.waf_table_list.header_filtering_table.reset();
									});
								},
							},
							{
								title: '删除',
								event: function (row, index) {
									that.ajaxTask('del_header_len', { header_type: row[0], header_type_len: row[1] }, function (res) {
										if (res.status) {
											that.refresh_data_total('overall');
											setTimeout(function () {
												that.render_http_rule_view(1);
											}, 200);
										}
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								},
							},
						],
					},
				],
				data: data_header,
				done: function () {},
			});
		} else {
			that.refresh_table_view({
				el: '#statement_analyze_table',
				form_id: 'statement_analyze_table', //用于重置
				height: 380,
				config: [
					{
						title: '防御类型',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 410px;" title="' + row[0] + '">' + row[0] + '</span>';
						},
					},
					{
						fid: '1',
						title: '状态',
						type: 'btswitch',
						width: '50px',
						style: 'text-align: center;',
						event: function (row, index, event) {
							that.ajaxTask('set_obj_open', { obj: row[2] }, function (res) {
								if (res.status) {
									that.refresh_data_total('overall');
									setTimeout(function () {
										that.render_http_rule_view(0);
									}, 200);
								}
								layer.msg(res.msg, { icon: res.status ? 1 : 2 });
							});
						},
					},
				],
				data: analyze_,
				done: function () {},
			});
		}
	},
	/**
	 * @description 设置规则配置视图
	 * @param {Object} row 数据对象
	 */
	set_other_rule_view: function (row) {
		var _type = '',
			that = this;
		if (row.name == '自定义规则拦截') {
			_type = 'args';
		} else if (row.name == '恶意下载防御') {
			_type = 'url';
		} else if (row.type == 'user-agent') {
			_type = 'user_agent';
		} else {
			_type = row.type;
		}
		layer.open({
			type: 1,
			title: '编辑规则【' + row.name + '】',
			area: ['800px', '590px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="other_table">\
						<div class="waf-form-input">\
							<input type="text" class="waf-input" name="ruleValue" placeholder="规则内容,请使用正则表达式" />\
							<input type="text" class="waf-input" name="rulePs" placeholder="说明" />\
							<button class="btn btn-success btn-sm va0 pull-right add_overall_rule">添加</button></div>\
						<div id="other_conf_table"></div>\
						<ul class="help-info-text c7 ptb10">\
							<li style="color:red;">注意:如果您不了解正则表达式,请不要随意修改规则内容</li>\
							<li>您可以添加或修改规则内容,但请使用正则表达式</li>\
							<li>内置规则允许修改,但不可以直接删除,您可以设置规则状态来定义防火墙是否使用此规则</li>\
						</ul>\
					</div>',
			success: function (index, layero) {
				that.render_other_conf({ ruleName: _type });
				$('.add_overall_rule').click(function () {
					var _ruleValue = $('[name=ruleValue]'),
						_rulePs = $('[name=rulePs]');
					that.ajaxTask(
						'add_rule',
						{
							ruleValue: _ruleValue.val(),
							ps: _rulePs.val(),
							ruleName: _type,
						},
						function (res) {
							if (res.status) {
								that.render_other_conf({ ruleName: _type });
								_ruleValue.val('');
								_rulePs.val('');
							}
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
						}
					);
				});
			},
		});
	},
	/**
	 * @description 设置IP段视图（IP黑、白名单、禁止海外、禁止境内）
	 * @param {String} type 数据类型
	 * @param {Boolean} isShow 数据类型
	 */
	set_ip_region_view: function (type, isShow) {
		var that = this;
		var prompt_msg =
			'<li>添加某个IP例子：192.168.10.6   起始IP为192.168.10.6  结束IP为192.168.10.6</li>\
						<li>添加多个IP例子：192.168.100.6-100   起始IP为192.168.100.6  结束IP为192.168.100.100</li>\
						<li>添加IP段例子：192.168.1.0/24   起始IP为192.168.1.1  结束IP为192.168.1.254</li>\
						<li>添加IP段例子：172.16.10.1/16   起始IP为172.16.1.1  结束IP为172.16.255.255</li>\
						<li>如其他地址段计算请参考 <a href="https://ipjisuanqi.com/" target="_blank" class="btlink">ip地址在线计算</a></li>';
		layer.open({
			type: 1,
			title: type == 'drop_abroad' || type == 'drop_china' ? '管理境内IP段' : type == 'ip_white' ? '管理IP白名单' : '管理IP黑名单',
			area: ['550px', '635px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="ip_region_table" style="padding:' +
				(type == 'ip_black' ? '0' : '20px 15px') +
				'">\
                    <div style="display:' +
				(type == 'ip_black' ? 'block' : 'none') +
				'">\
                        <div class="tab_list">\
                            <div class="tab_block active">IPv4黑名单</div>\
                            <div class="tab_block">IPv6黑名单</div></div>\
                        <div class="pd15 ipv4_block">\
                            <div class="waf-form-input">\
                                <button class="btn btn-success btn-sm va0 add_ipv4_region">添加</button>\
                            </div>\
                            <div id="ipv4_region_table"></div>\
                            <div class="waf-btn-group">\
                                <button class="btn btn-success va0 mr5 mt10 import_ip">导入</button>\
                                <button class="btn btn-success va0 mr5 mt10 export_ip">导出</button>\
                                <button class="btn btn-success va0 mr5 mt10 empty_ip">清空</button>\
                            </div>\
                        </div>\
                        <div class="pd15 ipv6_block" style="display:none;">\
                            <div class="waf-form-input">\
                                <input type="text" class="waf-input" name="ipv6_address" placeholder="IPv6地址" style="width: 440px;" />\
                                <button class="btn btn-success btn-sm va0 pull-right add_ipv6_region">添加</button>\
                            </div>\
                            <div id="ipv6_region_table"></div>\
                        </div>\
                        <ul class="pd15 waf_tips_list mtl0 c7 ptb10" style="padding-top: 0;position: absolute;bottom: 0;">\
                            <li class="black_tips">黑名单中的IP段将被禁止访问,IP白名单中已存在的除外</li>' +
				prompt_msg +
				'</ul>\
                    </div>\
                    <div style="display:' +
				(type != 'ip_black' ? 'block' : 'none') +
				'">\
                        <div class="waf-form-input">' +
				(type == 'ip_white'
					? '<button class="btn btn-success btn-sm va0 add_ip_region">添加</button>'
					: '<input type="text" class="waf-input" name="start_ip" placeholder="起始IP地址" />\
													<input type="text" class="waf-input" name="end_ip" placeholder="结束IP地址" />\
													<button class="btn btn-success btn-sm va0 pull-right add_ip_region">添加</button>') +
				'</div>\
                        <div id="ip_region_table"></div>\
                        <div class="waf-btn-group" style="display:' +
				(isShow == undefined ? 'block' : 'none') +
				'">\
                            <button class="btn btn-success va0 mr5 mt10 import_ip">导入</button>\
                            <button class="btn btn-success va0 mr5 mt10 export_ip">导出</button>\
                            ' +
				(type == 'ip_white' ? '<button class="btn btn-success va0 mr5 mt10 empty_ip">清空</button>' : '') +
				'\
                        </div>\
						<ul class="waf_tips_list mtl0 c7 ptb10" style="padding-top: 0;position: absolute;bottom: 0;">\
							<li style="' +
				(type == 'drop_abroad' ? ';' : 'display:none;') +
				'">如果有遗漏的境内IP段，请在此添加</li>\
							<li style="' +
				(type == 'ip_white' ? '' : 'display:none;') +
				'">所有规则对白名单中的IP段无效，包括IP黑名单和URL黑名单，IP白名单具备最高优先权</li>' +
				prompt_msg +
				'</ul>\
                    </div>\
				</div>',
			success: function (layero, index) {
				switch (type) {
					case 'drop_abroad':
					case 'drop_china':
						that.render_drop_abroad();
						break;
					case 'ip_white':
						that.render_ip_white();
						break;
					case 'ip_black':
						that.render_ip_black(0);
						break;
				}
				$('.add_ip_region').click(function () {
					if (type == 'ip_white' || type == 'ip_black') {
						that.add_ip_whiteOrBlack(type);
					} else {
						var start_ip = $('[name=start_ip]'),
							end_ip = $('[name=end_ip]');
						if (start_ip.val() == '' || end_ip.val() == '') return layer.msg('请输入起始IP地址或结束IP地址', { icon: 2 });
						if (!bt.check_ip(start_ip.val()) || !bt.check_ip(end_ip.val())) return layer.msg('请输入正确的IP格式', { icon: 2 });
						that.ajaxTask('add_' + (type == 'ip_white' ? 'ip_white' : type == 'ip_black' ? 'ip_black' : 'cnip'), { start_ip: start_ip.val(), end_ip: end_ip.val() }, function (res) {
							if (res.status) {
								start_ip.val('');
								end_ip.val('');
								that['render_' + (type == 'ip_white' ? 'ip_white' : 'drop_abroad')](0);
							}
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
						});
					}
				});
				$('.add_ipv4_region').click(function () {
					that.add_ip_whiteOrBlack(type);
					// var start_ip = $('[name=ipv4_start_ip]'),end_ip = $('[name=ipv4_end_ip]');
					// if(start_ip.val() == '' || end_ip.val() == '')return layer.msg('请输入起始IP地址或结束IP地址',{icon:2})
					// if(!bt.check_ip(start_ip.val()) || !bt.check_ip(end_ip.val()))return layer.msg('请输入正确的IP格式',{icon:2})
					// that.ajaxTask('add_'+(type =='ip_white'?'ip_white':'ip_black'),{start_ip:start_ip.val(),end_ip:end_ip.val()},function(res){
					// 	if(res.status) {
					// 		start_ip.val('');
					// 		end_ip.val('');
					// 		that['render_'+ type](0);
					// 	}
					// 	layer.msg(res.msg,{icon:res.status?1:2});
					// });
				});
				$('.add_ipv6_region').click(function () {
					var addr = $('[name=ipv6_address]').val();
					if (['', undefined].includes(addr)) return layer.msg('请输入ipv6地址', { icon: 2 });
					that.ajaxTask('set_ipv6_back', { addr: addr }, function (res) {
						if (res.status) {
							$('[name="ipv6_address"]').val('');
							$('.tab_list .tab_block:eq(1)').click();
						}
						layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					});
				});
				//ip黑名单tab选项
				$('.tab_list .tab_block').click(function () {
					$(this).addClass('active').siblings().removeClass('active');
					if ($(this).index() == 0) {
						$('.ipv4_block').show().next().hide();
						$('.black_tips').nextAll().show();
						that.render_ip_black(0);
					} else {
						$('.ipv4_block').hide().next().show();
						$('.black_tips').nextAll().hide();
						that.render_ip_black(1);
					}
				});
				// 导入
				$('.import_ip').click(function () {
					that.import_or_export_view(type, true);
				});
				// 导出
				$('.export_ip').click(function () {
					that.import_or_export_view(type, false, type == 'drop_abroad' || type == 'drop_china' ? that.drop_abroad_list : that.ip_config_list);
				});
				//清空
				$('.empty_ip').click(function () {
					that.empty_data_list(type);
				});
			},
		});
	},
	//添加IP白名单或IP黑名单
	add_ip_whiteOrBlack: function (type) {
		var that = this;
		bt_tools.open({
			type: 1,
			title: '添加' + (type == 'ip_white' ? 'IP白名单' : 'IP黑名单'),
			area: '540px',
			btn: ['添加', '取消'],
			content: {
				class: 'pd20',
				form: [
					{
						label: '起始IP',
						group: {
							type: 'text',
							name: 'start_ip',
							placeholder: '请输入起始IP地址',
							width: '336px',
						},
					},
					{
						label: '结束IP',
						group: {
							type: 'text',
							name: 'end_ip',
							placeholder: '请输入结束IP地址',
							width: '336px',
						},
					},
					{
						label: '备注',
						group: {
							type: 'text',
							name: 'ps',
							placeholder: '请输入备注信息',
							width: '336px',
						},
					},
					{
						group: {
							type: 'help',
							list: [
								'添加某个IP例子：192.168.10.6 起始IP为192.168.10.6 结束IP为192.168.10.6',
								'添加多个IP例子：192.168.100.6-100 起始IP为192.168.100.6 结束IP为192.168.100.100',
								'添加IP段例子：192.168.1.0/24 起始IP为192.168.1.1 结束IP为192.168.1.254',
								'添加IP段例子：172.16.10.1/16 起始IP为172.16.1.1 结束IP为172.16.255.255',
								'如其他地址段计算请参考<a href="https://ipjisuanqi.com/" target="_blank" class="btlink">ip地址在线计算</a>',
							],
						},
					},
				],
			},
			yes: function (form, indexs) {
				if (form.start_ip == '' || form.end_ip == '') return layer.msg('请输入起始IP地址或结束IP地址', { icon: 2 });
				if (!bt.check_ip(form.start_ip) || !bt.check_ip(form.end_ip)) return layer.msg('请输入正确的IP格式', { icon: 2 });
				that.ajaxTask('add_' + (type == 'ip_white' ? 'ip_white' : 'ip_black'), { start_ip: form.start_ip, end_ip: form.end_ip, ps: form.ps }, function (res) {
					if (res.status) {
						that['render_' + (type == 'ip_white' ? 'ip_white' : 'ip_black')](0);
						layer.close(indexs);
					}
					layer.msg(res.msg, { icon: res.status ? 1 : 2 });
				});
			},
		});
	},
	/**
	 * @description 设置攻击次数拦截视图
	 * @param {Object} obj 数据参数
	 */
	set_cc_tolerate_view: function (obj) {
		var _btn = ['应用'],
			that = this;
		if (!obj.siteName) _btn = ['全局应用'];
		layer.open({
			type: 1,
			title: '设置攻击次数拦截' + (obj.siteName ? '【' + obj.siteName + '】' : ''),
			area: '420px',
			closeBtn: 2,
			shadeClose: false,
			btn: _btn,
			content:
				'<div class="waf-form cc_rule_form pd20">\
				<div class="waf-line">\
					<span class="name-l">访问时间</span>\
					<div class="info-r">\
						<input type="number" name="cc_tolerate_cycle" value="' +
				obj.cycle +
				'" class="waf-input" />\
						<span class="waf_input_tips">秒</span>\
					</div>\
				</div>\
				<div class="waf-line">\
					<span class="name-l">攻击次数</span>\
					<div class="info-r">\
						<input type="number" name="cc_tolerate_retry" value="' +
				obj.retry +
				'" class="waf-input" />\
						<span class="waf_input_tips">次</span>\
					</div>\
				</div>\
				<div class="waf-line">\
					<span class="name-l">封锁时间</span>\
					<div class="info-r">\
						<input type="number" name="cc_tolerate_time" value="' +
				obj.time +
				'" class="waf-input" />\
						<span class="waf_input_tips">秒</span>\
					</div>\
				</div>\
				<div class="waf-line-tips">\
					<ul class="waf_tips_list mtl0 c7 ptb10">\
						<li><span class="key">' +
				obj.cycle +
				'</span> 秒内累计攻击超过 <span class="key">' +
				obj.retry +
				'</span> 次，封锁 <span class="key">' +
				obj.time +
				'</span> 秒</li>\
					</ul>\
				</div>\
			</div>',
			yes: function (index, layero) {
				var time = $('[name=cc_tolerate_time]').val(),
					cycle = $('[name="cc_tolerate_cycle"]').val(),
					retry = $('[name="cc_tolerate_retry"]').val();
				var region = $('.cc_city .btn .filter-option')
					.text()
					.replace('中国大陆以外的地区(包括[中国特别行政区:港,澳,台])', '海外')
					.replace('中国大陆(不包括[中国特别行政区:港,澳,台])', '中国')
					.replace('中国香港', '香港')
					.replace('中国澳门', '澳门')
					.replace('中国台湾', '台湾');
				if (region.indexOf('请选择') > -1) region = '';
				if (retry == 0 || cycle == 0 || time == 0) return layer.msg('规则参数不能为0，请重新输入！', { icon: 2 });
				if (!obj.siteName) {
					bt.confirm({ title: '全局应用', msg: '全局设置当前攻击次数拦截，且覆盖当前全部站点的攻击次数拦截，是否继续操作？', icon: 3 }, function () {
						set_retry();
					});
				} else {
					set_retry();
				}
				function set_retry() {
					that.ajaxTask(
						obj.siteName ? 'set_site_retry' : 'set_retry',
						{
							retry: retry,
							retry_time: time,
							retry_cycle: cycle,
							is_open_global: obj.siteName == undefined ? 1 : 0,
							siteName: obj.siteName,
						},
						function (rdata) {
							if (rdata.status) {
								setTimeout(function () {
									layer.close(index);
									obj.siteName ? that.render_site_config({ siteName: obj.siteName }) : that.refresh_data_total('overall');
								}, 1000);
							}
							layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
						}
					);
				}
			},
		});
	},
	/**
	 * @description 设置站点规则视图
	 * @param {Object} obj 站点名称,规则名称
	 */
	set_site_rule_view: function (obj, callback) {
		var that = this;
		layer.open({
			type: 1,
			title: '编辑站点规则【' + obj.siteName + '】 - 【 ' + obj.name + ' 】',
			area: ['800px', '590px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="other_table">\
						<div id="site_rule_table"></div>\
						<ul class="help-info-text c7 ptb10">\
							<li>此处继承全局设置中已启用的规则</li>\
							<li>此处的设置仅对当前站点有效</li>\
						</ul>\
					</div>',
			success: function (layer, index) {
				that.render_site_rule({ siteName: obj.siteName, ruleName: obj.ruleName });
			},
		});
	},
	/**
	 * @description 设置CC规则配置视图
	 * @param {String} obj 对象，显示的数据
	 */
	set_cc_rule_view: function (obj) {
		var that = this,
			_btn = ['应用'],
			enhance_mode = '',
			mode = 1,
			renji_flag = false,
			renji_count = 0;
		var site_html = '';
		if (!obj.siteName) {
			_btn = ['全局应用'];
		} else {
			var option = '';
			$.each(that.batch_config_sitename, function (index, item) {
				option += '<option value="' + item.siteName + '">' + item.siteName + '</option>';
			});
			site_html =
				'<div class="waf-line">\
				<span class="name-l">站点</span>\
				<div class="info-r">\
					<select class="bt-input-text mr5" style="width:140px" name="site_name" id="site_name">' +
				option +
				'\
					</select>\
				</div>\
			</div>';
		}
		// 增强模式
		if (obj.increase) {
			enhance_mode = 1;
		} else {
			enhance_mode = 0;
		}
		//模式
		if (obj.mode == undefined) {
			mode = 1;
		} else {
			mode = obj.mode <= '1' ? 1 : 2;
		}
		layer.open({
			type: 1,
			title: '设置CC规则' + (obj.siteName ? '【' + obj.siteName + '】' : ''),
			area: '560px',
			closeBtn: 2,
			shadeClose: false,
			btn: _btn,
			skin: 'cc-waf-form',
			content:
				'<div class="waf-form cc_rule_form pd20">' +
				site_html +
				'\
                <div class="waf-line">\
					<span class="name-l">模式</span>\
					<div class="info-r">\
						<select class="bt-input-text mr5" style="width:140px" name="cc_key_mode" id="cc_key_mode">\
                            <option value="1">标准模式</option>\
                            <option value="2">增强模式</option>\
                        </select>\
						<div class="c9 mt5 cc_four" style="display:none;line-height: 20px;width:390px;">开启后，访问网站会出现人机校验机制，需要用户手动验证才能继续访问，推荐用户受CC攻击时开启。</div>\
					</div>\
				</div>\
				 <div class="waf-line">\
					<span class="name-l">请求类型</span>\
					<div class="info-r">\
						<select class="bt-input-text mr5" style="width:140px" name="cc_type_status" id="cc_type_status">\
                            <option value="1">URL带参数</option>\
                            <option value="2">URL不带参数</option>\
                            <option value="3">IP</option>\
                            <option value="4">IP+UA</option>\
                        </select>\
                        <a href="https://www.bt.cn/bbs/thread-72613-1-1.html" target="_blank" class="btlink"> &nbsp;教程</a>\
					</div>\
				</div>\
				<div class="waf-line">\
					<span class="name-l">访问时间</span>\
					<div class="info-r">\
						<input type="number" name="cc_cycle" value="" class="waf-input" />\
						<span class="waf_input_tips">秒</span>\
					</div>\
				</div>\
				<div class="waf-line">\
					<span class="name-l">访问次数</span>\
					<div class="info-r">\
						<input type="number" name="cc_limit" value="" class="waf-input" />\
						<span class="waf_input_tips">次</span>\
					</div>\
				</div>\
				<div class="waf-line">\
					<span class="name-l">封锁时间</span>\
					<div class="info-r">\
						<input type="number" name="cc_endtime" value="" class="waf-input" />\
						<span class="waf_input_tips">秒</span>\
					</div>\
				</div>\
                <div class="waf-line enhance_view" style="display:none;">\
					<span class="name-l">人机校验</span>\
					<div class="info-r">\
						<select class="bt-input-text mr5" style="width:80px" name="cc_enhance_mode">\
                            <option value="0">自动开启</option>\
                            <option value="1">一直开启</option>\
                        </select>\
                        <div class="bt_cc_view" style="display:inline-block;">\
                            <div class="info-r" style="display: inline-block;margin-left:10px;margin-bottom:0;">设置触发条件，时间<input class="bt-input-text" name="cc_time" type="text" value="" style="width:50px;margin:0 5px;"/>秒</div>\
                            <div class="info-r" style="display: inline-block;margin-left:10px;margin-bottom:0;">阈值<input class="bt-input-text" name="cc_retry_cycle" type="text" value="" style="width:50px;margin:0 5px;"/>次</div>\
                        </div>\
					</div>\
                </div>\
                <div class="waf-line cc_increase">\
					<span class="name-l">验证方式</span>\
					<div class="info-r">\
                        <select class="bt-input-text mr5" style="width:90px" name="cc_increase_type" disabled="disabled">\
							<option value="browser">浏览器验证</option>\
                            <option value="js">跳转验证</option>\
                            <option value="code">验证码验证</option>\
                            <option value="renji">人机验证</option>\
                            <option value="huadong">滑动验证</option>\
                        </select>\
                        <span class="increase_span code_span hide red">验证码验证:如果站点有开启CDN 建议不要使用。</span>\
                        <span class="increase_span renji_span hide"><a href="https://www.bt.cn/bbs/thread-73326-1-1.html" target="_blank" class="btlink"> &nbsp;教程</a></span>\
					</div>\
				</div>\
				<div class="waf-line-tips">\
					<ul class="waf_tips_list mtl0 c7 ptb10">\
						<li style="display:' +
				(obj.siteName ? 'none' : 'list-item') +
				'">此处设置的是初始值，新添加站点时将继承。</li>\
						<li class="key" style="display:' +
				(!obj.siteName ? 'none' : 'list-item') +
				'">此处设置仅对当前站点有效。</li>\
                        <li class="key cc_borwser" style="display:none">浏览器验证:验证是否为正常浏览器请求，若打开后网站访问异常，请关闭它</li>\
                        <li class="cc_auto" style="display:none">设置为自动模式为开启状态时，当网站 <span class="waf_cc_limit cc_time key"></span> 秒 时间内,被访问 <span class="waf_cc_limit cc_retry_cycle key"></span> 次自动开启增强模式，没有触发该规则，自动关闭增强模式。</li>\
						<li>单IP<span class="waf_cc_cycle key">' +
				obj.cc_cycle +
				'</span> 秒内累计请求同一URL超过 <span class="waf_cc_limit key">' +
				obj.cc_limit +
				'</span> 次,触发CC防御,封锁此IP <span class="waf_cc_endtime key">' +
				obj.cc_endtime +
				'</span> 秒</li>\
						<li class="key" style="display:' +
				(!obj.siteName ? 'none' : 'list-item') +
				'">请不要设置过于严格的CC规则,以免影响正常用户体验</li>\
						<li>地区人机验证：选中的地区自动开启增强模式，验证模式：<span class="key">JS</span>，访问时间：<span class="waf_cc_cycle key">' +
				obj.cc_cycle +
				'</span> 秒，如验证失败：<span class="key">' +
				obj.retry +
				'</span> 次，封锁时间：<span class="waf_cc_endtime key">' +
				obj.cc_endtime +
				'</span> 秒</li>\
					</ul>\
				</div>\
			</div>',
			success: function (index, layero) {
				//<li class="key cc_four" style="display:none">增强模式:CC防御加强版，开启后可能会影响用户体验，建议在用户受到CC攻击时开启。</li>\
				var robj = $('.cc_rule_form .enhance_view'),
					city_html = '';
				if (obj.siteName) $('#site_name').val(obj.siteName);
				$.post('/plugin?action=a&name=btwaf&s=city', function (res) {
					for (var i = 0; i < res.length; i++) {
						city_html += '<li><a><span class="text">' + res[i] + '</span><span class="glyphicon check-mark"></span></a></li>';
					}
					robj.before(
						'<div class="waf-line cc_region" style="height: 32px;"><span class="name-l">地区人机验证</span><div class="info-r ml0">' + that.multi_select_view('cc_city', city_html) + '</div></div>'
					);
					if (mode === 2) {
						$('.cc_region').hide();
					} else {
						$('.cc_region').show();
					}
					that.nulti_event('cc_city', res, '地区');
					var country = [];
					var arr = Object.keys(obj.cc.countrys);
					if (arr.length > 0) {
						for (var i = 0; i < arr.length; i++) {
							var str = arr[i].toString().trim();
							if (str === '海外') country.push(str.replace('海外', '中国大陆以外的地区(包括[中国特别行政区:港,澳,台])'));
							else if (str === '中国') country.push(str.replace('中国', '中国大陆(不包括[中国特别行政区:港,澳,台])'));
							else if (str === '香港') country.push(str.replace('香港', '中国香港'));
							else if (str === '澳门') country.push(str.replace('澳门', '中国澳门'));
							else if (str === '台湾') country.push(str.replace('台湾', '中国台湾'));
							else country.push(str);
						}
					}
					if (country.length > 0) {
						for (var j = 0; j < country.length; j++) {
							for (var i = 0; i < res.length; i++) {
								if (country[j].trim() === res[i]) {
									$('.cc_city .dropdown-menu li').eq(i).click();
								}
							}
						}
					}
				});
				// 同步提示
				var arry = ['cc_cycle', 'cc_limit', 'cc_endtime'];
				for (var i = 0; i < arry.length; i++) {
					(function (i) {
						$('[name="' + arry[i] + '"]').on('keyup click', function () {
							$('.waf_' + arry[i]).html($(this).val());
						});
					})(i);
				}
				// 设置选项
				var _sel = that.waf_cc_config_list;
				// 选项触发
				$('[name=cc_key_mode]').change(function () {
					//数据填入
					var _data = _sel[$(this).val() == '1' ? 1 : obj.mode == '3' ? 3 : 4].data;
					for (var item in _data) {
						$('[name=' + item + ']').val(_data[item]);
					}
					$('[name=cc_cycle]').val(obj.cc_cycle);
					$('[name=cc_limit]').val(obj.cc_limit);
					$('[name=cc_endtime]').val(obj.cc_endtime);
					$('[name=cc_type_status]').val(obj.cc_type_status);
					//触发不同的显示
					if ($(this).val() == 1) {
						$('.cc_region').show();
						$('.bt_cc_view,.enhance_view,.cc_borwser,.cc_four,.cc_auto,.cc_increase').hide();
						$('.cc_rule_form .waf_tips_list li:eq(4)').show();
					} else {
						$('.cc_region').hide();
						$('.bt_cc_view,.cc_borwser,.cc_auto,.enhance_view,.cc_four,.cc_increase').show();
						$('.cc_rule_form .waf_tips_list li:eq(4)').hide();

						// 设置自动模式触发时间、阀口
						if (obj.siteName) {
							$('[name=cc_time]').val(obj.cc_time).attr('data-default', obj.cc_time);
							$('.cc_time').html(obj.cc_time);
							$('[name="cc_retry_cycle"]').val(obj.cc_retry_cycle).attr('data-default', obj.cc_retry_cycle);
							$('.cc_retry_cycle').html(obj.cc_retry_cycle);
						} else {
							$('[name=cc_time]').val(that.overall_config.cc_time).attr('data-default', that.overall_config.cc_time);
							$('.cc_time').html(that.overall_config.cc_time);
							$('[name="cc_retry_cycle"]').val(that.overall_config.cc_retry_cycle).attr('data-default', that.overall_config.cc_retry_cycle);
							$('.cc_retry_cycle').html(that.overall_config.cc_retry_cycle);
						}
					}
					//人机校验判断
					var _val = _data.cc_enhance_mode;
					_val == 0 ? $('[name=cc_enhance_mode]').siblings().show() : $('[name=cc_enhance_mode]').siblings().hide();
					_val == 0 ? $('[name=cc_increase_type]').val('js').prop('disabled', 'disabled') : $('[name=cc_increase_type]').prop('disabled', false);
					$('.increase_span').addClass('hide');
				});
				$('[name=cc_enhance_mode]').change(function () {
					var _val = $(this).val();
					_val == 0 ? $(this).siblings().show() : $(this).siblings().hide();
					_val == 0 ? $('[name=cc_increase_type]').val('js').prop('disabled', 'disabled') : $('[name=cc_increase_type]').prop('disabled', false);
				});
				$('[name=cc_increase_type]').change(function () {
					var _val = $(this).val(),
						_select = $(this);
					switch (_val) {
						case 'browser':
							$('.code_span').addClass('hide');
							$('.renji_span').addClass('hide');
							break;
						case 'code':
							$('.code_span').removeClass('hide');
							$('.renji_span').addClass('hide');
							break;
						case 'renji':
						case 'huadong':
							$('.code_span').addClass('hide');
							$('.renji_span').removeClass('hide');
							if (!renji_flag && renji_count == 0) {
								that.ajaxTask('check_renji', function (res) {
									renji_count = 1;
									if (!res) {
										layer.msg('当前面板' + (res ? '可以' : '无法') + '开启人机和滑动验证,详细请查看教程。', { icon: res ? 1 : 2 });
										renji_flag = true;
										$('[name=cc_increase_type] option[value=renji], [name=cc_increase_type] option[value=huadong]').prop('disabled', true);
									}
								});
							}
							break;
					}
				});
				// 触发默认select
				$('[name=cc_key_mode]').val(mode);
				$('[name=cc_key_mode]').change();
				//设置获取的数据重新填入
				$('[name=cc_cycle]').val(obj.cc_cycle);
				$('[name=cc_limit]').val(obj.cc_limit);
				$('[name=cc_endtime]').val(obj.cc_endtime);
				$('[name=cc_type_status]').val(obj.cc_type_status);
				// 设置四层防御状态/增强模式验证方式
				$('[name=cc_increase_type]').val(obj.cc_increase_type == undefined ? 'js' : obj.cc_increase_type);
				$('.' + obj.cc_increase_type + '_span').removeClass('hide');
			},
			yes: function (index, layero) {
				var num = $('[name=cc_key_mode]').val(),
					cc_cycle = $('[name="cc_cycle"]').val(),
					cc_limit = $('[name="cc_limit"]').val(),
					cc_endtime = $('[name="cc_endtime"]').val(),
					increase_wu_heng = $('[name="increase_wu_heng"]').val(),
					cc_four_defense = $('[name="cc_four_defense"]').val(),
					cc_time = $('[name="cc_time"]'),
					cc_retry_cycle = $('[name="cc_retry_cycle"]'),
					cc_enhance_mode = $('[name="cc_enhance_mode"]').val(),
					cc_increase_type = $('[name="cc_increase_type"]').val();
				cc_type_status = $('[name="cc_type_status"]').val();

				var region = $('.cc_city .btn .filter-option')
					.text()
					.replace('中国大陆以外的地区(包括[中国特别行政区:港,澳,台])', '海外')
					.replace('中国大陆(不包括[中国特别行政区:港,澳,台])', '中国')
					.replace('中国香港', '香港')
					.replace('中国澳门', '澳门')
					.replace('中国台湾', '台湾');
				if (region.indexOf('请选择') > -1) region = '';

				if (renji_flag) {
					layer.msg('当前面板无法开启人机和滑动验证', { icon: 2 });
					return false;
				}
				if (cc_cycle == 0 || cc_limit == 0 || cc_endtime == 0) return layer.msg('规则参数不能为0，请重新输入！', { icon: 2 });
				if (num == '2') {
					// layer.confirm('当前验证模式，适合长期开启（比较适合官网博客开启，不适合前后端分离项目开启），但遇到大量CC时请选择其他验证模式', { title: '提示',closeBtn:2,icon:7}, function () {
					// 	postFun()
					// })
					layer.confirm('效果：大幅度提升拦截效果<br>影响：体验下降会误拦截一些正常访问<br>建议：在普通模式无法防御时临时开启攻击结束后关闭', { title: '提示', closeBtn: 2, icon: 7 }, function () {
						postFun();
					});
					return false;
				}
				postFun();
				function postFun() {
					num == '1' ? (num = 1) : cc_enhance_mode == '0' ? (num = 3) : (num = 4);
					// 提交基础信息
					var pdata = {
						siteName: !obj.siteName ? $('#site_name').val() : obj.siteName,
						cc_mode: num,
						cycle: cc_cycle,
						limit: cc_limit,
						endtime: cc_endtime,
						is_open_global: obj.siteName == undefined ? 1 : 0,
						increase: cc_enhance_mode == '0' ? 0 : 1,
						increase_wu_heng: increase_wu_heng == '0' ? 0 : 1,
						cc_increase_type: cc_increase_type,
						cc_type_status: cc_type_status,
					};
					if (num === 1) pdata['country'] = region;
					// 检测是否需要开启/关闭【自动，四层防御】，规则配置提交
					// 一、是否为自动模式
					if (num == 3) {
						if (cc_time.val() == '' || cc_retry_cycle.val() == '') return layer.msg('请设置正确的触发条件', { icon: 2 });
						if (!obj.siteName) {
							that.http({ load: 3, check: true, method: 'start_cc_status', success: function (res) {} });
							if (cc_time.val() != cc_time.attr('data-default') || cc_retry_cycle.val() != cc_retry_cycle.attr('data-default')) {
								//提交自动模式数据
								that.http({
									load: 3,
									method: 'set_cc_automatic',
									data: {
										cc_time: cc_time.val(),
										cc_retry_cycle: cc_retry_cycle.val(),
										increase_wu_heng: increase_wu_heng,
									},
									success: function (res) {},
								});
							}
						} else {
							pdata['cc_time'] = cc_time.val();
							pdata['cc_retry_cycle'] = cc_retry_cycle.val();
						}
					} else {
						that.http({ load: 3, check: true, method: 'stop_cc_status', success: function (res) {} });
					}
					// //                 // 三、CC防御配置提交
					that.ajaxTask(!obj.siteName ? 'set_cc_conf' : 'set_site_cc_conf', pdata, function (res) {
						if (res.status) {
							if (obj.siteName) {
								that.render_site_config({ siteName: obj.siteName });
							} else {
								that.refresh_data_total('overall');
							}
							layer.close(index);
						}
						layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					});
				}
			},
		});
	},
	/**
	 * @descripttion 添加单URL CC防御
	 * @param {Booleans} is_creat   是否为添加
	 * @param {Object} data   修改时原本的数据
	 * @return: 无返回值
	 */
	edit_cc_uri_frequency: function (is_creat, data) {
		var that = this;
		var addUrlCCFrequency = null;
		if (is_creat) {
			data = {
				url: '',
				frequency: 30,
				cycle: 60,
			};
		}
		layer.open({
			type: 1,
			title: (is_creat ? '添加' : '修改') + '单URL CC防御',
			area: '530px',
			closeBtn: 2,
			btn: [is_creat ? '添加' : '修改', '取消'],
			content: '<div class="waf-form pd20"></div>',
			success: function (layers, indexs) {
				addUrlCCFrequency = bt_tools.form({
					el: '.waf-form',
					form: [
						{
							label: 'URL',
							group: [
								{
									name: 'url',
									width: '236px',
									type: 'text',
									placeholder: '/index.php',
									unit: '* 不能带参数的URL',
								},
							],
						},
						{
							label: '访问次数',
							group: [
								{
									name: 'frequency',
									width: '236px',
									type: 'number',
									unit: '次',
								},
							],
						},
						{
							label: '时间范围',
							group: [
								{
									name: 'cycle',
									width: '236px',
									type: 'number',
									unit: '秒',
								},
							],
						},
						{
							group: {
								type: 'help',
								style: { 'margin-left': '30px' },
								list: ['当前CC防御为单个URl设置CC防御，建议最低范围为60秒和30次'],
							},
						},
					],
					data: data,
				});
			},
			yes: function (indexs) {
				var formData = addUrlCCFrequency.$get_form_value(),
					params = [];
				if (formData.url == '') return layer.msg('URL内容不能为空!', { icon: 2 });
				if (formData.frequency == '') return layer.msg('访问次数内容不能为空!', { icon: 2 });
				if (formData.cycle == '') return layer.msg('时间范围不能为空!', { icon: 2 });
				if (formData.frequency <= 0 || formData.cycle <= 0) return layer.msg('访问次数或时间范围不能小于等于0!', { icon: 2 });
				that.ajaxTask(is_creat ? 'add_cc_uri_frequency' : 'edit_cc_uri_frequency', formData, function (res) {
					if (res.status) {
						layer.close(indexs);
						that.render_cc_uri_frequency_body();
					}
					layer.msg(res.msg, { icon: res.status ? 1 : 2 });
				});
			},
		});
	},
	/**
	 * @descripttion  添加/修改状态码
	 * @param {Booleans} is_creat   是否为添加
	 * @param {Object} data   修改时原本的数据
	 * @return: 无返回值
	 */
	open_code_view_dialog: function (is_creat, data) {
		var that = this;
		layer.open({
			type: 1,
			title: (is_creat ? '添加' : '修改') + '状态码',
			area: '350px',
			closeBtn: 2,
			btn: [is_creat ? '添加' : '修改', '取消'],
			content:
				'<div class="waf-form pd20">\
						<div class="waf-line waf_one">\
							<span class="name-l">状态码</span>\
							<div class="info-r">\
								<select id="staticStatusCode" class="bt-input-text mr5" style="width: 80px;" ' +
				(is_creat ? '' : 'disabled="disabled"') +
				'></select>\
							</div>\
						</div>\
						<div class="waf-line waf_one">\
							<span class="name-l">拦截状态</span>\
							<div class="info-r">\
								<select id="interceptCode" class="bt-input-text mr5" style="width: 80px;"></select>\
							</div>\
						</div>\
					</div>',
			success: function () {
				var code_from = ['403', '404', '500', '501', '502'],
					code_to = ['444', '500', '501', '502', '503', '400', '401', '404'],
					cf_html = '',
					ct_html = '';
				$.each(code_from, function (index, item) {
					cf_html += '<option value="' + item + '">' + item + '</option>';
				});
				$.each(code_to, function (index, item) {
					ct_html += '<option value="' + item + '">' + (item == '444' ? '拦截' : item) + '</option>';
				});

				$('#staticStatusCode').html(cf_html);
				$('#interceptCode').html(ct_html);
				if (!is_creat) {
					$('#staticStatusCode').val(data['code']);
					$('#interceptCode').val(data['status']);
				}
			},
			yes: function (index, layero) {
				that.ajaxTask(is_creat ? 'add_static_code_config' : 'edit_static_code_config', { code_from: $('#staticStatusCode').val(), code_to: $('#interceptCode').val() }, function (res) {
					if (res.status) {
						layer.close(index);
						that.render_static_code_list();
					}
					layer.msg(res.msg, { icon: res.status ? 1 : 2 });
				});
			},
		});
	},
	/**
	 * @descripttion 获取蜘蛛视图
	 * @return: 无返回值
	 */
	get_spider_view: function () {
		var that = this;
		layer.open({
			type: 1,
			title: '蜘蛛池列表',
			area: ['550px', '554px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="spider_list_table" style="padding:0">\
					<ul class="tab_list">\
						<li class="tab_block active">百度</li>\
						<li class="tab_block">谷歌</li>\
						<li class="tab_block">360</li>\
						<li class="tab_block">搜狗</li>\
						<li class="tab_block">雅虎</li>\
						<li class="tab_block">必应</li>\
						<li class="tab_block">头条</li>\
					</ul>\
					<div class="pd15">\
						<div class="waf-form-input">\
							<input type="text" class="waf-input" name="add_spider" style="width: 450px;" placeholder="请输入IP">\
							<button class="btn btn-success btn-sm va0 pull-right submit_spider">添加</button>\
						</div>\
						<div id="spider_list_info"></div>\
						<div class="waf-btn-group">\
							<button class="btn btn-success va0 mr5 mt10 import_ip">导入</button>\
							<button class="btn btn-success va0 mr5 mt10 export_ip">导出</button>\
						</div>\
						<ul class="help-info-text c7">\
							<li style="color:red;font-size: 12px;">导入错误会导致蜘蛛爬取失败,非专业人员请勿操作。</li>\
							<li style="font-size: 12px;">蜘蛛池内的IP访问时不会触发拦截规则</li>\
						</ul>\
					</div>\
				</div>',
			success: function () {
				var _that = 0,
					plist = ['baidu', 'google', '360', 'sogou', 'yahoo', 'bingbot', 'bytespider'];
				that.render_spider_list(0); //默认百度
				//选项卡切换
				$('.spider_list_table .tab_block').click(function () {
					var _index = $(this).index();
					_that = _index;
					$(this).addClass('active').siblings().removeClass('active');
					that.render_spider_list(_index);
				});
				//添加蜘蛛IP
				$('.submit_spider').click(function () {
					var val = $('input[name=add_spider]');
					if (!bt.check_ip(val.val()) || val.val() == '') return layer.msg('请输入正确的IP格式', { icon: 0 });
					that.ajaxTask('add_spider', { spider: plist[_that], ip: val.val() }, function (res) {
						if (res.status) {
							val.val('');
							that.render_spider_list(_that);
						}
						layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					});
				});
				//导入
				$('.import_ip').click(function () {
					that.import_or_export_spider_view(plist[_that], true);
				});
				//导出
				$('.export_ip').click(function () {
					that.import_or_export_spider_view(plist[_that], false, that.spider_data_list);
				});
			},
		});
	},
	/**
	 * @description 设置ua黑/白名单
	 * @param {String} type 数据类型
	 */
	set_ua_white_view: function (type) {
		var that = this;
		layer.open({
			type: 1,
			title: type == 'ua_white' ? 'UA白名单' : 'UA黑名单',
			area: ['550px', '560px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="ua_name_table">\
                <div class="waf-form-input">\
                    <input type="text" class="waf-input" name="ua_region" placeholder="例如:Mozilla">\
                    <button class="btn btn-success btn-sm va0 pull-right add_ua_region">添加</button>\
                </div>\
                <div id="ua_name_table"></div>\
                <div class="waf-btn-group">\
                    <button class="btn btn-success va0 mr5 mt10 ua_import_url">导入</button>\
                    <button class="btn btn-success va0 mr5 mt10 ua_export_url">导出</button>\
                    <button class="btn btn-success va0 mr5 mt10 ua_empty">清空</button>\
                </div>\
                <ul class="waf_tips_list mtl0 c7 ptb10">\
                    <li class="key">初始化阶段在客户端UA中查找关键词。谨慎使用。</li>\
                    <li>可以在API接口使用作为一个秘钥的方式使用</li>\
                    <li>查询到关键词直接跳过任何拦截</li>\
                </ul>\
            </div>',
			success: function (layero, index) {
				switch (type) {
					case 'ua_white':
						that.render_ua_white();
						break;
					case 'ua_black':
						that.render_ua_black();
						break;
				}
				$('.add_ua_region').click(function () {
					var ua_region = $('input[name=ua_region]').val(),
						pdata = {};
					if (ua_region == '') return layer.msg('请输入关键词', { icon: 2 });
					that.ajaxTask('add_' + type, type == 'ua_white' ? { ua_white: ua_region } : { ua_black: ua_region }, function (res) {
						if (res.status) {
							$('input[name=ua_region]').val('');
							that['render_' + type]();
						}
						layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					});
				});
				// 导入
				$('.ua_import_url').click(function () {
					that.import_or_export_pure_array_view(type, true);
				});
				// 导出
				$('.ua_export_url').click(function () {
					that.import_or_export_pure_array_view(type, false, that.ua_config_list);
				});
				//清空
				$('.ua_empty').click(function () {
					that.empty_data_list(type);
				});
			},
		});
	},
	/**
	 * @description 规则显示页面
	 * @param {Object} obj 数据类型
	 */
	set_other_rule_one_view: function (obj) {
		var _title = '',
			_pl = '',
			that = this;
		switch (obj.type) {
			case 'url_white':
				(_title = '管理URL白名单'), (_pl = 'URL地址，例如：/admin/update');
				break;
			case 'url_black':
				(_title = '管理URL黑名单'), (_pl = 'URL地址，例如：/admin/update');
				break;
			case 'cdn':
				(_title = '管理网站CDN-Headers【' + obj.siteName + '】'), (_pl = 'header名称');
				break;
			case 'disable_upload_ext':
				(_title = '禁止上传文件类型【' + obj.siteName + '】'), (_pl = '扩展名，不包含点(.)，示例：sql');
				break;
			case 'disable_php_path':
				(_title = '禁止运行PHP的URL地址【' + obj.siteName + '】'), (_pl = 'URL地址，例如：/admin/update');
				break;
			case 'disable_path':
				(_title = '禁止访问的URL地址【' + obj.siteName + '】'), (_pl = 'URL地址，例如：/admin/update');
				break;
			case 'disable_ext':
				(_title = '禁止访问的扩展名【' + obj.siteName + '】'), (_pl = '扩展名，不包含点(.)，示例：sql');
				break;
			case 'api_defense':
				(_title = 'API防御'), (_pl = '例如 : ^/api/getinfo$');
				break;
			case 'key_words':
				(_title = 'URL关键词拦截'), (_pl = '例如 : find.zip');
				break;
			case 'golbls_cc':
				(_title = '人机验证白名单'), (_pl = 'URL地址，例如：/admin/update');
				break;
		}
		layer.open({
			type: 1,
			title: _title,
			area: ['550px', '530px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="other_rule_table" style="padding:' +
				(obj.type == 'url_white' ? '0' : '20px 15px') +
				'">\
                    <div style="display:' +
				(obj.type == 'url_white' ? 'block' : 'none') +
				'">\
                        <div class="tab_list">\
                            <div class="tab_block active">标准模式-URL白名单</div>\
                            <div class="tab_block">标准模式-URL白名单带参数</div></div>\
                        <div class="pd15 url_white">\
                            <div class="waf-form-input">\
                                <input type="text" class="waf-input" name="rule_url_white" placeholder="' +
				_pl +
				'" />\
                                <button class="btn btn-success btn-sm va0 pull-right add_white_rule">添加</button>\
                            </div>\
                            <div id="white_rule_table"></div>\
                            <div class="waf-btn-group">\
                                <button class="btn btn-success va0 mr5 mt10 white_import_url">导入</button>\
                                <button class="btn btn-success va0 mr5 mt10 white_export_url">导出</button>\
                                <button class="btn btn-success va0 mr5 mt10 empty_url_or_key">清空</button>\
                            </div>\
                        </div>\
						<div class="pd15 url_white" style="display:none">\
							<div class="waf-form-input">\
								<button class="btn btn-success btn-sm va0 add_white_rule_params">添加</button>\
							</div>\
							<div id="white_rule_param_table"></div>\
						</div>\
                        <ul class="waf_tips_list mtl0 c7" style="padding-left:15px;position:absolute;bottom: 15px;">\
                            <li>所有规则对白名单中的URL无效，不包括IP黑名单。</li>\
							<li class="not_sup_msg">当前URL白名单不支持带参数。</li>\
							<li class="not_sup_msg">例子1 : /admin/admin.php?system=abc 添加地址: /admin/admin.php</li>\
							<li class="not_sup_msg">例子2: /admin/1   1 为可变 1-99    添加地址为: /admin/[1-99]</li>\
                        </ul>\
                    </div>\
                    <div style="display:' +
				(obj.type != 'url_white' ? 'block' : 'none') +
				'">\
                        <div class="waf-form-input">\
                            <input type="text" class="waf-input" name="' +
				(obj.type == 'golbls_cc' ? 'rule_url_white_strong' : 'rule_url') +
				'" placeholder="' +
				_pl +
				'" />\
                            <button class="btn btn-success btn-sm va0 pull-right add_other_rule">添加</button>\
                        </div>\
                        <div id="' +
				(obj.type == 'golbls_cc' ? 'white_rule_strong_table' : 'other_rule_table') +
				'"></div>\
                        <div class="waf-btn-group" style="display:' +
				(obj.type == 'url_black' || obj.type == 'key_words' ? 'block' : 'none') +
				'">\
                            <button class="btn btn-success va0 mr5 mt10 ' +
				(obj.type == 'url_black' ? 'black_import_url' : 'key_import') +
				'">导入</button>\
                            <button class="btn btn-success va0 mr5 mt10 ' +
				(obj.type == 'url_black' ? 'black_export_url' : 'key_export') +
				'">导出</button>\
                            <button class="btn btn-success va0 mr5 mt10 empty_url_or_key">清空</button>\
                        </div>\
												<ul class="waf_tips_list mtl0 c7 ptb10" style="display:' +
				(obj.type == 'golbls_cc' ? 'block' : 'none') +
				'">\
                            <li>开启人机验证时候需要不验证某些页面时使用</li>\
													<li>例子1 : /admin/admin.php?system=abc 添加地址: /admin/admin.php</li>\
													<li>例子2: /admin/1 1 为可变 1-99 添加地址为: /admin/[1-99]</li>\
                        </ul>\
                        <ul class="waf_tips_list mtl0 c7 ptb10" style="display:' +
				(obj.type == 'url_black' ? 'block' : 'none') +
				'">\
                            <li>禁止访问URL黑名单，URL白名单和IP白名单中存在时除外。</li>\
													<li>例子1 : /admin/admin.php?system=abc 添加地址: /admin/admin.php</li>\
													<li>例子2: /admin/1   1 为可变 1-99    添加地址为: /admin/[1-99]</li>\
                        </ul>\
                        <ul class="waf_tips_list mtl0 c7 ptb10" style="display:' +
				(obj.type == 'cdn' ? 'block' : 'none') +
				'">\
                            <li>防火墙将尝试在以上header中获取客户IP</li>\
                        </ul>\
                        <ul class="waf_tips_list mtl0 c7 ptb10" style="display:' +
				(obj.type == 'disable_upload_ext' ? 'block' : 'none') +
				'">\
                            <li>除正则表达式语句外规则值对大小写不敏感，建议统一使用小写</li>\
                            <li>直接填要被禁止访问的扩展名，如我希望禁止上传*.php文件：php</li>\
                        </ul>\
                        <ul class="waf_tips_list mtl0 c7 ptb10" style="display:' +
				(obj.type == 'disable_php_path' || obj.type == 'disable_path' ? 'block' : 'none') +
				'">\
                            <li>除正则表达式语句外规则值对大小写不敏感,建议统一使用小写</li>\
                            <li>此处请不要包含URI参数,一般针对目录URL,示例：/admin</li>\
						</ul>\
						<ul class="waf_tips_list mtl0 c7 ptb10" style="display:' +
				(obj.type == 'disable_ext' ? 'block' : 'none') +
				'">\
                            <li>除正则表达式语句外规则值对大小写不敏感，建议统一使用小写</li>\
                            <li>直接填要被禁止访问的扩展名，如我希望禁止访问*.sql文件：sql</li>\
                        </ul>\
                        <ul class="waf_tips_list mtl0 c7 ptb10" style="display:' +
				(obj.type == 'api_defense' ? 'block' : 'none') +
				'">\
                            <li>API防御指的是部分API在白名单的情况下有需要对某些接口进行CC防御</li>\
                            <li>API写的时候例子如下：^/api/getuserinfo$</li>\
                            <li>写法注意了。一定得用^开头和$结尾</li>\
                        </ul>\
                        <ul class="waf_tips_list mtl0 c7 ptb10" style="display:' +
				(obj.type == 'key_words' ? 'block' : 'none') +
				'">\
                            <li>初始化阶段URL拦截</li>\
							<li>URL关键词拦截添加，例：/aa/bb/?a=hello需拦截a=hello，可添加a=hello、=hello、hello</li>\
                        </ul>\
                    </div>\
				</div>',
			success: function (layero, index) {
				var other_rule_msg = { disable_upload_ext: '请输入扩展名', disable_php_path: '请输入URL地址', disable_path: '请输入URL地址', disable_ext: '请输入扩展名' };
				switch (obj.type) {
					case 'golbls_cc':
						that.render_url_white(2);
						break;
					case 'url_white':
						that.render_url_white(0);
						break;
					case 'url_black':
						that.render_url_black();
						break;
					case 'cdn':
						that.render_cdn_table({ siteName: obj.siteName });
						break;
					case 'disable_upload_ext':
					case 'disable_php_path':
					case 'disable_path':
					case 'disable_ext':
						that.render_disable_other({ siteName: obj.siteName, ruleName: obj.type });
						break;
					case 'api_defense':
					case 'key_words':
						that.render_apiDefense_or_wordsKey({ type: obj.type });
						break;
				}
				$('.add_other_rule').click(function () {
					var rule_url = $('[name=rule_url]');
					switch (obj.type) {
						case 'golbls_cc':
							var rule_url_white = $('[name=rule_url_white_strong]');
							if (rule_url_white.val() == '') return layer.msg('请输入URL地址', { icon: 2 });
							that.ajaxTask('golbls_cc_zeng', { text: rule_url_white.val() }, function (res) {
								if (res.status) {
									rule_url_white.val('');
									that.render_url_white(2);
								}
								layer.msg(res.msg, { icon: res.status ? 1 : 2 });
							});
							break;
						case 'url_black':
							if (rule_url.val() == '') return layer.msg('请输入URL地址', { icon: 2 });
							that.ajaxTask('add_url_black', { url_rule: rule_url.val() }, function (res) {
								if (res.status) {
									rule_url.val('');
									that.render_url_black();
								}
								layer.msg(res.msg, { icon: res.status ? 1 : 2 });
							});
							break;
						case 'cdn':
							if (rule_url.val() == '') return layer.msg('请输入Header', { icon: 2 });
							that.ajaxTask('add_site_cdn_header', { siteName: obj.siteName, cdn_header: rule_url.val() }, function (res) {
								if (res.status) {
									that.render_cdn_table({ siteName: obj.siteName });
									rule_url.val('');
								}
								layer.msg(res.msg, { icon: res.status ? 1 : 2 });
							});
							break;
						case 'api_defense':
						case 'key_words':
							if (rule_url.val() == '') return layer.msg('关键词不能为空', { icon: 2 });
							that.ajaxTask(obj.type == 'api_defense' ? 'add_url_white_chekc' : 'add_url_find', { url_find: rule_url.val() }, function (res) {
								if (res.status) {
									rule_url.val('');
									that.render_apiDefense_or_wordsKey({ type: obj.type });
								}
								layer.msg(res.msg, { icon: res.status ? 1 : 2 });
							});
							break;
						case 'disable_upload_ext':
						case 'disable_php_path':
						case 'disable_path':
						case 'disable_ext':
							if (rule_url.val() == '') return layer.msg(other_rule_msg[obj.type], { icon: 2 });
							that.ajaxTask('add_site_rule', { siteName: obj.siteName, ruleName: obj.type, ruleValue: rule_url.val() }, function (res) {
								if (res.status) {
									rule_url.val('');
									that.render_disable_other({ siteName: obj.siteName, ruleName: obj.type });
								}
								layer.msg(res.msg, { icon: res.status ? 1 : 2 });
							});
							break;
					}
				});
				$('.add_white_rule').click(function () {
					var rule_url_white = $('[name=rule_url_white]');
					if (rule_url_white.val() == '') return layer.msg('请输入URL地址', { icon: 2 });
					that.ajaxTask('add_url_white', { url_rule: rule_url_white.val() }, function (res) {
						if (res.status) {
							rule_url_white.val('');
							that.render_url_white(0);
						}
						layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					});
				});
				$('.add_white_rule_params').click(function () {
					that.add_url_white_params();
				});
				//url白名单tab选项
				$('.tab_list .tab_block').click(function () {
					$(this).addClass('active').siblings().removeClass('active');
					var index = $(this).index();
					$('.url_white').hide().eq(index).show();
					that.render_url_white(index);
					if (index == 0) {
						$('.not_sup_msg').show();
					} else {
						$('.not_sup_msg').hide();
					}
				});
				// 导入
				$('.white_import_url,.black_import_url').click(function () {
					that.import_or_export_view(obj.type, true);
				});
				// 导出
				$('.white_export_url,.black_export_url').click(function () {
					that.import_or_export_view(obj.type, false, that.url_config_list);
				});
				// 关键词拦截
				$('.key_import').click(function () {
					that.import_or_export_pure_array_view(obj.type, true);
				});
				$('.key_export').click(function () {
					that.import_or_export_pure_array_view(obj.type, false, that.ua_config_list);
				});
				// 清空
				$('.empty_url_or_key').click(function () {
					that.empty_data_list(obj.type);
				});
			},
		});
	},
	// 添加URL白名单带参数
	add_url_white_params: function () {
		var that = this;
		layer.open({
			type: 1,
			title: '添加URL白名单规则',
			area: ['550px', '390px'],
			closeBtn: 2,
			btn: ['添加', '取消'],
			content:
				'<div class="waf-form pd20">\
				<div class="waf-line">\
					<span class="name-l">URL</span>\
					<div class="info-r">\
						<input type="text" class="waf-input" name="url_cc_text" placeholder="例如:/upload/upload.php" style="width: 265px; padding: 0 10px;">\
					</div>\
				</div>\
				<div class="waf-line" style="height:138px;margin-bottom:0">\
					<span class="name-l">参数值</span>\
					<div class="info-r">\
						<textarea name="url_cc_textarea" rows="4" cols="46" style="width: 362px; padding:5px 10px;border-radius:2px;border:1px solid #ccc;height:200px;line-height:24px;" placeholder="默认为空参数,如需要填写多个参数一行一个,\n例子如下:URL为: /index.php?id=1&pp=xx\n注意的是一行一个参数不能放在一行内这样会使白名单失效\n第一种例子:\nid=1 \n第二种:\nid \npp\n第三种:\npp=xx \nid"></textarea>\
					</div>\
				</div>\
			</div>',
			yes: function (index) {
				var _type = $('#url_cc_select').val(),
					_url = $('[name=url_cc_text]').val(),
					_param = $('textarea[name=url_cc_textarea]').val().replace(/\n/g, ',');
				if (_url.trim() == '') return layer.msg('URL内容不能为空!', { icon: 2 });
				if (_param != '') {
					var _val = _param.split(',');
					_param = JSON.stringify(_val);
				} else {
					_param = JSON.stringify([]);
				}
				that.ajaxTask(
					'add_url_white_senior',
					{
						url: _url,
						param: _param,
					},
					function (res) {
						if (res.status) {
							layer.close(index);
							that.render_url_white(1);
						}
						layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					}
				);
			},
		});
	},
	/**
	 * @description 设置扫描器视图
	 */
	set_scan_rule_view: function () {
		var that = this;
		layer.open({
			type: 1,
			title: '常用扫描器过滤规则',
			area: ['600px', '515px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="waf-form scan_rule_form pd20">\
				<div class="waf-lines">\
					<span class="name-l">Header</span>\
					<div class="info-r">\
						<textarea name="scan_args" class="waf-input"></textarea>\
					</div>\
				</div>\
				<div class="waf-lines">\
					<span class="name-l">Cookie</span>\
					<div class="info-r">\
						<textarea name="scan_cookie" class="waf-input"></textarea>\
					</div>\
				</div>\
				<div class="waf-lines">\
					<span class="name-l">Args</span>\
					<div class="info-r">\
						<textarea name="scan_header" class="waf-input"></textarea>\
					</div>\
				</div>\
				<div class="waf-line-tips">\
					<ul class="waf_tips_list mtl0 c7 ptb10">\
						<li class="key">会同时过滤key和value,请谨慎设置。</li>\
						<li>请使用正则表达式,提交前应先备份原有表达式。</li>\
					</ul>\
				</div>\
			</div>',
			btn: ['应用', '关闭'],
			success: function (index, layero) {
				that.ajaxTask('get_rule', { ruleName: 'scan_black' }, function (res) {
					$('[name=scan_args]').text(res.args);
					$('[name=scan_cookie]').text(res.cookie);
					$('[name=scan_header]').text(res.header);
				});
			},
			yes: function (layero, index) {
				var scan_args = $('[name=scan_args]').val(),
					scan_cookie = $('[name=scan_cookie]').val(),
					scan_header = $('[name=scan_header]').val();
				that.ajaxTask('save_scan_rule', { header: scan_header, cookie: scan_cookie, args: scan_args }, function (res) {
					if (res.status) {
						layer.close(layero);
						that.refresh_data_total('overall');
					}
					layer.msg(res.msg, { icon: res.status ? 1 : 2 });
				});
			},
		});
	},
	/**
	 * @description 目录扫描防御
	 */
	set_scan_conf_view: function () {
		var that = this;
		layer.open({
			type: 1,
			title: '目录扫描防御',
			area: ['420px', '375px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="waf-form pd20">\
				<div class="waf-line">\
					<span class="name-l">开关</span>\
					<div class="info-r">\
						<input class="btswitch btswitch-ios" id="scan_open" name="scan_open" type="checkbox">\
						<label class="btswitch-btn" for="scan_open"></label>\
					</div>\
				</div>\
				<div class="waf-line">\
					<span class="name-l">访问时间</span>\
					<div class="info-r">\
						<input type="number" name="cc_cycle" value="" class="waf-input" min="60" />\
						<span class="waf_input_tips">秒</span>\
					</div>\
				</div>\
				<div class="waf-line">\
					<span class="name-l">攻击次数</span>\
					<div class="info-r">\
						<input type="number" name="cc_limit" value="" class="waf-input" min="120" />\
						<span class="waf_input_tips">次</span>\
					</div>\
				</div>\
				<div class="waf-line-tips">\
					<ul class="waf_tips_list mtl0 c7 ptb10">\
						<li>当前扫描器开关只是对于当前防御扫描目录/文件的设置有效。</li>\
						<li>此拦截是通过访问url 产生的404链接进行防御</li>\
						<li>最低不能低于20秒20次。</li>\
					</ul>\
				</div>\
			</div>',
			btn: ['应用', '关闭'],
			success: function (index, layero) {
				$('[name=cc_cycle]').attr('value', that.overall_config.scan_conf.cycle);
				$('[name=cc_limit]').attr('value', that.overall_config.scan_conf.limit);
				$('[name=scan_open]').prop('checked', that.overall_config.scan_conf.open);
			},
			yes: function (layero, index) {
				var cc_cycle = $('[name=cc_cycle]').val();
				cc_limit = $('[name=cc_limit]').val();
				scan_open = $('[name=scan_open]').is(':checked');
				scan_open = scan_open ? 1 : 0;
				if (!cc_cycle || !cc_limit) return layer.msg((!cc_cycle ? '访问时间' : '访问次数') + '不能为空!', { icon: 2 });
				if (cc_cycle < 20 || cc_limit < 20) return layer.msg(cc_cycle < 20 ? '访问时间不能低于20秒' : '访问次数不能低于20次', { icon: 2 });
				that.ajaxTask('set_scan_conf', { open: scan_open, limit: cc_limit, cycle: cc_cycle }, function (res) {
					if (res.status) {
						layer.close(layero);
						that.refresh_data_total('overall');
					}
					layer.msg(res.msg, { icon: res.status ? 1 : 2 });
				});
			},
		});
	},
	/**
	 * @description 设置蜘蛛
	 * @param {*} config 配置
	 * @param {*} tableData 数据
	 */
	set_spider_view: function (config, tableData) {
		var that = this;
		var data = [];
		$.each(tableData, function (index, item) {
			if (typeof item === 'object') data.push(item);
		});
		layer.open({
			type: 1,
			title: config.name + '【' + config.siteName + '】',
			area: ['800px', '500px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'\
				<div class="other_table">\
					<div id="site_spider_table"></div>\
					<ul class="help-info-text c7 ptb10">\
						<li>默认允许的蜘蛛进行爬取开启代表允许爬取</li>\
						<li>禁止后状态码表示禁止该蜘蛛后返回的状态码</li>\
					</ul>\
				</div>\
			',
			success: function () {
				that.refresh_table_view({
					el: '#site_spider_table',
					height: '320px',
					data: data,
					config: [
						{ fid: 'name', width: 400, title: '名称' },
						{ fid: 'return', width: 200, title: '禁止后状态码' },
						{
							fid: 'status',
							title: '是否允许爬取',
							type: 'btswitch',
							style: 'text-align: right;',
							event: function (row, index, event) {
								that.ajaxTask(
									'set_spider',
									{
										siteName: config.siteName,
										id: row.id,
									},
									function (res) {
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
										if (res.status) row.status = !row.status;
									}
								);
							},
						},
					],
				});
			},
		});
	},
	/**
	 * @description 设置敏感文字替换视图
	 * @param {Booleans} isBoolean 是否为站点
	 * @param {String} site 站点名称
	 */
	set_sensitive_text_view: function (isBoolean, site) {
		var that = this;
		layer.open({
			type: 1,
			title: '敏感文字替换',
			area: ['550px', isBoolean ? '400px' : '442px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="sensitive_text_table pd20">\
                <div class="waf-form-input">\
                    <input type="text" class="waf-input" name="sensitive_text" placeholder="敏感文字" style="width: 215px;">\
                    <input type="text" class="waf-input" name="replace_text" placeholder="替换文字" style="width: 215px;">\
                    <button class="btn btn-success btn-sm va0 pull-right add_replace">添加</button>\
                </div>\
                <div id="sensitive_text_table"></div>\
				<ul class="waf_tips_list mtl0 c7 ptb10">\
					<li>敏感文字替换添加，例如：敏感文字您好 替换成你好</li>\
					<li>请不要乱随意填写，可能会导致整个站点空白</li>\
					<li class="' +
				(isBoolean ? 'hide' : '') +
				'">在此处添加后会应用到所有网站</li>\
					<li class="' +
				(isBoolean ? 'hide' : '') +
				'">如果设置和网站单独设置的冲突，将会优先使用网站设置内的</li>\
				</ul>\
            </div>',
			success: function (layers, index) {
				// 渲染表格
				that.render_sansitive_table({ isBoolean: isBoolean, site: site });
				// 添加
				$('.add_replace').click(function () {
					var _sen = $('[name=sensitive_text]'),
						_rep = $('[name=replace_text]');
					if (_sen.val() == '' || _rep.val() == '') return layer.msg('请输入敏感文字或替换文字', { icon: 2 });
					that.ajaxTask(isBoolean ? 'add_body_site_rule' : 'add_body_rule', { text: _sen.val(), text2: _rep.val(), siteName: site }, function (res) {
						if (res.status) {
							_sen.val('');
							_rep.val('');
							if (site) {
								$.post('/plugin?action=a&name=btwaf&s=get_site_config_byname', { siteName: site }, function (rdata) {
									that.site_config = rdata;
								});
							} else {
								$.post('/plugin?action=a&name=btwaf&s=get_config', function (rdata) {
									that.overall_config = rdata;
								});
							}
							setTimeout(function () {
								that.render_sansitive_table({ site: site });
							}, 500);
						}
						layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					});
				});
			},
		});
	},
	/**
	 * @description 设置URL请求类型拦截
	 *
	 */
	set_url_request_type_refuse_view: function () {
		var that = this;
		layer.open({
			type: 1,
			title: 'URL请求类型拦截',
			area: ['600px', '500px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="pd20">\
				<div class="waf-form-input"><button class="btn btn-success btn-sm url_request_type_refuse">添加</button></div>\
				<div id="url_request_type_refuse_table"></div>\
				<ul class="waf_tips_list mtl0 c7 ptb10">\
					<li>拦截:指定当前URL不允许某些请求类型</li>\
					<li>只放行：指定当前URL只允许某些请求类型</li>\
				</ul>\
			</div>',
			success: function () {
				that.render_url_request_type_refuse_body();
				$('.url_request_type_refuse').click(function () {
					that.add_url_request_type_refuse();
				});
			},
		});
	},
	/**
	 * @description 单URL CC防御
	 *
	 */
	set_cc_uri_frequency_view: function () {
		var that = this;
		layer.open({
			type: 1,
			title: '单URL CC防御',
			area: ['600px', '500px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="pd20">\
				<div class="waf-form-input"><button class="btn btn-success btn-sm cc_uri_frequency">添加</button></div>\
				<div id="cc_uri_frequencye_table"></div>\
			</div>',
			success: function () {
				that.render_cc_uri_frequency_body();
				$('.cc_uri_frequency').click(function () {
					that.edit_cc_uri_frequency(true);
				});
			},
		});
	},
	/**
	 * @description 恶意文件上传防御
	 */
	set_file_upload_view: function () {
		var that = this;
		layer.open({
			type: 1,
			title: '恶意文件上传防御',
			area: ['600px', '500px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="pd20">\
				<div id="file_upload_table"></div>\
			</div>',
			success: function () {
				var data = [];
				data.push({
					title: 'From-data协议',
					status: that.overall_config.from_data,
					ps: 'from-data是文件上传的默认格式，防火墙只信任默认格式。如果您网站修改上传格式则需要关闭该功能，关闭后只会对上传包格式不检查。',
				});
				bt_tools.table({
					el: '#file_upload_table',
					data: data,
					column: [
						{ fid: 'title', title: '名称', width: 120 },
						{ fid: 'ps', title: '描述' },
						{
							fid: 'status',
							title: '状态',
							type: 'switch',
							event: function (row, index) {
								layer.confirm(
									'请确定是否' + (row.status ? '关闭' : '开启') + 'From-data协议开关？',
									{
										title: '状态设置',
										closeBtn: 2,
										icon: 13,
										cancel: function () {
											$('#file_upload_table input[type="checkbox"]').prop('checked', row.status);
										},
									},
									function () {
										that.ajaxTask('set_obj_open', { obj: 'from_data' }, function (res) {
											layer.msg(res.msg, { icon: res.status ? 1 : 2 });
											that.overall_config.from_data = !that.overall_config.from_data;
										});
									},
									function () {
										$('#file_upload_table input[type="checkbox"]').prop('checked', row.status);
									}
								);
							},
						},
					],
				});
			},
		});
	},
	/**
	 * 渲染URL请求类型拦截
	 */
	render_url_request_type_refuse_body: function () {
		var that = this;
		this.ajaxTask('get_url_request_mode', function (res) {
			that.refresh_table_view({
				el: '#url_request_type_refuse_table',
				form_id: 'url_request_type_refuse_table',
				height: 305,
				config: [
					{
						title: 'URL',
						width: '206px',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 190px;" title="' + row.url + '">' + row.url + '</span>';
						},
					},
					{
						title: '类型',
						width: '70px',
						templet: function (row) {
							return row.type === 'refuse' ? '拦截' : '只放行';
						},
					},
					{
						title: '请求类型',
						width: '216px',
						templet: function (row) {
							var str = [];
							$.each(row.mode, function (index, item) {
								str.push(row.mode[item]);
							});
							return '<span class="overflow_hide" style="width: 200px;" title="' + str + '">' + str + '</span>';
						},
					},
					{
						title: '操作',
						width: '50px',
						style: 'text-align: right;',
						group: [
							{
								title: '删除',
								event: function (row, index) {
									var str = [];
									$.each(row.mode, function (index, item) {
										str.push(row.mode[item]);
									});
									that.ajaxTask('del_url_request_mode', { url: row.url, type: row.type, param: str.toString() }, function (res) {
										if (res.status) that.render_url_request_type_refuse_body();
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								},
							},
						],
					},
				],
				data: res,
				done: function (rdata) {},
			});
		});
	},
	/**
	 * @descripttion 添加URL请求类型拦截
	 * @return {*}
	 */
	add_url_request_type_refuse: function () {
		var that = this;
		var addUrlRequest = null,
			requestList = ['POST', 'GET', 'PUT', 'OPTIONS', 'HEAD', 'DELETE', 'TRACE', 'PATCH', 'MOVE', 'COPY', 'LINK', 'UNLINK', 'WRAPPED', 'PROPFIND', 'PROPPATCH', 'MKCOL', 'CONNECT', 'SRARCH'];
		layer.open({
			type: 1,
			title: '添加URL请求类型拦截',
			area: '545px',
			closeBtn: 2,
			btn: ['添加', '取消'],
			content: '<div class="waf-form pd20 url-request"></div>',
			success: function (layers, indexs) {
				addUrlRequest = bt_tools.form({
					el: '.waf-form',
					form: [
						{
							label: '类型',
							group: [
								{
									name: 'type',
									width: '95px',
									type: 'select',
									list: [
										{ title: '拦截', value: 'refuse' },
										{ title: '只放行', value: 'accept' },
									],
								},
								{
									name: 'url',
									width: '236px',
									class: 'verticalAlignTop',
									type: 'text',
									placeholder: '/uptime',
								},
							],
						},
					],
				});
				var robj = $('.bt-form'),
					btnHtml = '<button type="button" class="btn_cycle">全选</button>';
				for (var i = 0; i < requestList.length; i++) {
					btnHtml += '<button type="button" class="btn_cycle">' + requestList[i] + '</button>';
				}
				robj.append('<div class="line requestType"><span class="tname">请求类型</span><div class="info-r"><div class="inlineBlock">' + btnHtml + '</div></div></div>');
				var btn = $('.requestType button');
				btn.click(function () {
					var index = $(this).index();
					if (index === 0) {
						if ($(this).hasClass('active')) {
							btn.removeClass('active');
						} else {
							btn.addClass('active');
						}
					} else {
						if ($(this).hasClass('active')) {
							btn.eq(0).removeClass('active');
							$(this).removeClass('active');
						} else {
							$(this).addClass('active');
							var n = 0;
							for (var i = 0; i < btn.length; i++) {
								if (btn.eq(i).hasClass('active')) {
									n++;
								}
							}
							if (n === 18) {
								btn.eq(0).addClass('active');
							}
						}
					}
				});
			},
			yes: function (indexs) {
				var formData = addUrlRequest.$get_form_value(),
					btn = $('.requestType button'),
					params = [];
				if (formData.url == '') return layer.msg('URL内容不能为空!', { icon: 2 });
				for (var i = 1; i < btn.length; i++) {
					if (btn.eq(i).hasClass('active')) {
						params.push(btn.eq(i).text());
					}
				}
				if (!params.length) return layer.msg('请求类型最少选一个!', { icon: 2 });
				that.ajaxTask(
					'add_url_request_mode',
					{
						url: formData.url,
						type: formData.type,
						param: params.toString(),
					},
					function (res) {
						if (res.status) {
							layer.close(indexs);
							that.render_url_request_type_refuse_body();
						}
						layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					}
				);
			},
		});
	},
	/**
	 * @description 设置违禁词拦截视图
	 * @param {object} obj 站点名称
	 */
	set_body_intercept_view: function (obj) {
		var that = this;
		layer.open({
			type: 1,
			title: '违禁词拦截',
			area: ['550px', '445px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="sensitive_text_table pd20">\
	            <div class="waf-form-input">\
	                <input type="text" class="waf-input" name="body_intercept" placeholder="违禁词" style="width: 430px;">\
                    <button class="btn btn-success btn-sm va0 pull-right add_body_intercept">添加</button>\
	            </div>\
	            <div id="body_intercept_table"></div>\
	            <div class="waf-btn-group">\
                     <button class="btn btn-success va0 mr5 mt10 import_body_intercept">导入</button>\
                     <button class="btn btn-success va0 mr5 mt10 export_body_intercept">导出</button>\
                     <button class="btn btn-success va0 mr5 mt10 empty_body_intercept">清空</button>\
                </div>\
	            <ul class="waf_tips_list mtl0 c7 ptb10">\
                    <li>请不要乱随意填写,违禁词建议全部为中文</li>\
					<li>当前拦截为请求时拦截，检测客户端发送中是否包含违禁词，如果包含则拦截</li>\
	            </ul>\
	        </div>',
			success: function (layers, index) {
				that.render_body_intercept_table(); // 渲染表格
				// 添加
				$('.add_body_intercept').click(function () {
					var _ban = $('[name=body_intercept]');
					if (_ban.val() == '') return layer.msg('请输入违禁词', { icon: 2 });
					that.ajaxTask('add_body_intercept', { text: _ban.val() }, function (res) {
						if (res.status) {
							_ban.val('');
							that.render_body_intercept_table(); // 渲染表格
						}
						layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					});
				});
				// 导入
				$('.import_body_intercept').click(function () {
					that.import_or_export_body_intercept_view(obj.type, true);
				});
				// 导出
				$('.export_body_intercept').click(function () {
					that.import_or_export_body_intercept_view(obj.type, false, that.ban_word_list);
				});
				// 清空
				$('.empty_body_intercept').click(function () {
					var _ban_data = that.ban_word_list;
					if (_ban_data == []) layer.msg('当前违禁词为空', { icon: 2 });
					layer.confirm('是否清空列表数据', { title: '清空列表', closeBtn: 2, icon: 0 }, function () {
						that.ajaxTask('empty_body_intercept', { text: _ban_data }, function (res) {
							if (res.status) {
								_ban_data = [];
								that.render_body_intercept_table(); // 渲染表格
							}
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
						});
					});
				});
			},
		});
	},
	/**
	 * @description 设置URL专用过滤
	 * @param {Object} obj 站点名称,规则名称
	 */
	set_url_special_filter_view: function (obj) {
		var that = this;
		layer.open({
			type: 1,
			title: 'URL专用过滤【' + obj.siteName + '】',
			area: ['550px', '550px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="url_special_filter_table" style="padding:25px 15px">\
                    <div><div class="waf-form-input">\
                            <input type="text" class="waf-input" name="url_filter_address" placeholder="URL地址，例如：/admin/update" style="margin-right:10px;width:215px"/>\
                            <input type="text" class="waf-input" name="url_filter_rule" placeholder="过滤值，例如：date" style="width:215px"/>\
                            <button class="btn btn-success btn-sm va0 pull-right add_filter_rule">添加</button>\
                        </div>\
                        <div id="url_special_filter_table"></div>\
                        <ul class="waf_tips_list mtl0 c7 ptb10">\
                            <li>可用于加强登陆入口、回帖评论等接口的保护,快速修补第三方程序安全漏洞</li>\
                            <li>参数名与参数值对大小写敏感</li>\
                            <li>本过滤器同时作用于GET和POST参数</li>\
							<li>例子：/admin/update.php?update=_date&date=666 update参数中包含_date 存在漏洞利用的风险。那么可以设置为：</li>\
							<li>URL地址/admin/update.php，过滤规则为_date，过滤规则是过滤的参数内容。</li>\
                        </ul>\
                    </div>\
				</div>',
			success: function (layero, index) {
				// 初次触发
				that.render_url_filter_table({ siteName: obj.siteName, ruleName: 'url_rule' });
				// 添加事件
				$('.add_filter_rule').click(function () {
					var _address = $('[name=url_filter_address]'),
						_rule = $('[name=url_filter_rule]');
					if (_address.val() == '' || _rule.val() == '') return layer.msg('请输入地址或过滤规则');
					that.ajaxTask(
						'add_site_rule',
						{
							siteName: obj.siteName,
							ruleName: 'url_rule',
							ruleValue: _rule.val(),
							ruleUri: _address.val(),
						},
						function (res) {
							if (res.status) {
								that.render_url_filter_table({ siteName: obj.siteName, ruleName: 'url_rule' });
								_address.val('');
								_rule.val('');
							}
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
						}
					);
				});
			},
		});
	},
	/**
	 * @description 站点防盗链视图
	 * @param {Object} obj 站点名称,站点id
	 */
	set_hotlinking_view: function (web) {
		layer.open({
			type: 1,
			title: '防盗链设置',
			area: '600px',
			closeBtn: 2,
			shadeClose: false,
			content: '<div class="bt-form pd20"></div>',
			success: function ($layer) {
				this.getConfig($layer, function () {
					var height = $(window).height();
					var layerHeight = $layer.height();
					var top = (height - layerHeight) / 2;
					$layer.css('top', top + 'px');
				});
			},
			getConfig: function ($layer, callback) {
				var that = this;
				bt.site.get_site_security(web.id, web.siteName, function (rdata) {
					if (typeof rdata == 'object' && rdata.status === false && rdata.msg) {
						bt.msg(rdata);

						return;
					}
					$layer.find('.layui-layer-content .bt-form').html('');

					var robj = $layer.find('.layui-layer-content .bt-form');
					var datas = [
						{ title: 'URL后缀', name: 'sec_fix', value: rdata.fix, disabled: rdata.status, width: '300px' },
						{ title: '许可域名', type: 'textarea', name: 'sec_domains', value: rdata.domains.replace(/,/g, '\n'), disabled: rdata.status, width: '300px', height: '210px' },
						{ title: '响应资源', name: 'return_rule', value: rdata.return_rule, disabled: rdata.status, width: '300px' },
						{
							title: ' ',
							class: 'label-input-group',
							items: [
								{
									text: '启用防盗链',
									name: 'door_status',
									value: rdata.status,
									type: 'checkbox',
									callback: function (sdata) {
										if (sdata.sec_domains === '') {
											$('#door_status').prop('checked', false);
											bt.msg({
												status: false,
												msg: '许可域名不能为空！',
											});
											return false;
										}
										var domain = '';
										if (sdata.sec_domains) {
											domain = sdata.sec_domains.split('\n').join(',');
										}
										bt.site.set_site_security(web.id, web.siteName, sdata.sec_fix, domain, sdata.door_status, sdata.return_rule, function (ret) {
											if (ret.status) that.getConfig($layer);
											bt.msg(ret);
										});
									},
								},
								{
									text: '允许空HTTP_REFERER请求',
									name: 'none',
									value: rdata.none,
									type: 'checkbox',
									callback: function (sdata) {
										var domain = '';
										if (sdata.sec_domains) {
											domain = sdata.sec_domains.split('\n').join(',');
										}
										bt.site.set_site_security(web.id, web.siteName, sdata.sec_fix, domain, '1', sdata.return_rule, function (ret) {
											if (ret.status) that.getConfig($layer);
											bt.msg(ret);
										});
									},
								},
							],
						},
					];
					for (var i = 0; i < datas.length; i++) {
						var _form_data = bt.render_form_line(datas[i]);
						robj.append(_form_data.html);
						bt.render_clicks(_form_data.clicks);
					}
					var helps = [
						'【URL后缀】一般填写文件后缀，每行一个后缀,如: png',
						'【许可域名】允许作为来路的域名，每行一个域名,如: www.bt.cn',
						'【响应资源】可设置404/403等状态码，也可以设置一个有效资源，如：/security.png',
						'【允许空HTTP_REFERER请求】是否允许浏览器直接访问，若您的网站访问异常，可尝试开启此功能',
					];
					robj.append(bt.render_help(helps));

					callback && callback();
				});
			},
		});
		// var that = this;
		// layer.open({
		// 	type: 1,
		// 	title: "防盗链设置",
		// 	area: '600px',
		// 	closeBtn: 2,
		// 	shadeClose: false,
		// 	content:'<div class="bt-form pd20">\
		// 		<div class="line">\
		// 			<span class="tname">URL后缀</span>\
		// 			<div class="info-r"><input name="sec_fix" class="bt-input-text mr5 sec_fix" type="text" style="width:360px"></div>\
		// 		</div>\
		// 		<div class="line">\
		// 			<span class="tname">许可域名</span>\
		// 			<div class="info-r"><input name="sec_domains" class="bt-input-text mr5 sec_domains" type="text" style="width:360px"></div>\
		// 		</div>\
		// 		<div class="line label-input-group">\
		// 			<span class="tname"> </span>\
		// 			<div class="info-r ">\
		// 				<input type="checkbox" class="hotlinking_status" id="hotlinking_status" name="hotlinking_status">\
		// 				<label class="mr20" for="hotlinking_status" style="font-weight:normal">启用防盗链</label>\
		// 				<input type="checkbox" class="hotlinking_none" id="hotlinking_none" name="hotlinking_none">\
		// 				<label class="mr20" for="hotlinking_none" style="font-weight:normal">允许空HTTP_REFERER请求</label>\
		// 			</div>\
		// 		</div>\
		// 		<ul class="help-info-text c7"><li>默认允许资源被直接访问,即不限制HTTP_REFERER为空的请求</li><li>多个URL后缀与域名请使用逗号(,)隔开,如: png,jpeg,zip,js</li><li>当触发防盗链时,将直接返回404状态</li></ul>\
		// 		</div>',
		// 	success:function(){
		// 		that.get_hotlinking_data(obj);
		// 		$('#hotlinking_status').click(function(){
		// 			var loadTa = layer.msg('正在开启防盗链设置...', { time: 0, icon: 16, shade: [0.3, '#000'] });
		// 			$.post('/site?action=SetSecurity',{
		// 				id: obj.id,
		// 				name: obj.siteName,
		// 				fix: $('input[name=sec_fix]').val(),
		// 				domains: obj.siteName,
		// 				status: $(this).prop('checked')},function(res){
		// 					layer.close(loadTa);
		// 					if(res.status) that.get_hotlinking_data(obj);
		// 					layer.msg(res.msg,{icon:res.status?1:2})
		// 			})
		// 		})
		// 		$('#hotlinking_none').click(function(){
		// 			var loadTs = layer.msg('正在提交防盗链配置...', { time: 0, icon: 16, shade: [0.3, '#000'] });
		// 			$.post('/site?action=SetSecurity',{
		// 				id: obj.id,
		// 				name: obj.siteName,
		// 				fix: $('input[name=sec_fix]').val(),
		// 				domains: obj.siteName,
		// 				status: '1'},function(res){
		// 					layer.close(loadTs);
		// 					if(res.status) that.get_hotlinking_data(obj);
		// 					layer.msg(res.msg,{icon:res.status?1:2})
		// 			})
		// 		})
		// 	}
		// })
	},
	/**
	 * @description 渲染站点规则
	 * @param {Object} obj 站点名称,规则名称
	 */
	render_site_rule: function (obj, callback) {
		var that = this;
		that.ajaxTask('get_site_disable_rule', { siteName: obj.siteName, ruleName: obj.ruleName }, function (res) {
			that.refresh_table_view({
				el: '#site_rule_table',
				form_id: 'site_rule_table', //用于重置
				height: 425,
				config: [
					{
						fid: '1',
						title: '规则',
						templet: function (row, index) {
							return '<div class="" style="width:450px;word-break:break-all;line-height: 20px;">' + row[1] + '</div>';
						},
					},
					{ fid: '2', title: '说明', width: '150px' },
					{
						fid: '0',
						title: '状态',
						type: 'btswitch',
						width: '50px',
						style: 'text-align: center;',
						event: function (row, index, event) {
							that.ajaxTask('set_site_disable_rule', { index: index, ruleName: obj.ruleName, siteName: obj.siteName }, function (res) {
								layer.msg(res.msg, { icon: res.status ? 1 : 2 });
							});
						},
					},
				],
				data: res,
				done: function (res) {
					if (callback) callback(res);
				},
			});
		});
	},
	/**
	 * @description 渲染受保护url地址
	 * @param {Object} obj 站点名称,规则名称
	 */
	render_defend_url_table: function (obj, callback) {
		var that = this;
		that.ajaxTask('get_site_rule', { siteName: obj.siteName, ruleName: 'url_tell' }, function (res) {
			that.refresh_table_view({
				el: '#defend_url_table',
				form_id: 'defend_url_table', //用于重置
				height: 283,
				config: [
					{
						title: 'URL地址',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 210px;" title="' + row[0] + '">' + row[0] + '</span>';
						},
					},
					{
						title: '参数名',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 100px;" title="' + row[1] + '">' + row[1] + '</span>';
						},
					},
					{
						title: '参数值',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 100px;" title="' + row[2] + '">' + row[2] + '</span>';
						},
					},
					{
						title: '操作',
						width: '50px',
						style: 'text-align: right;',
						group: [
							{
								title: '删除',
								event: function (row, index) {
									that.ajaxTask('remove_site_rule', { siteName: obj.siteName, index: index, ruleName: obj.ruleName }, function (res) {
										if (res.status) that.render_defend_url_table(obj);
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								},
							},
						],
					},
				],
				data: res,
				done: function (res) {
					if (callback) callback(res);
				},
			});
		});
	},
	/**
	 * @description 渲染url专用过滤表格
	 * @param {Object} obj 站点名称,规则名称
	 */
	render_url_filter_table: function (obj, callback) {
		var that = this;
		that.ajaxTask('get_site_rule', { siteName: obj.siteName, ruleName: 'url_rule' }, function (res) {
			that.refresh_table_view({
				el: '#url_special_filter_table',
				form_id: 'url_special_filter_table', //用于重置
				height: 260,
				config: [
					{
						title: 'URL地址',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 210px;" title="' + row[0] + '">' + row[0] + '</span>';
						},
					},
					{
						title: '过滤规则',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 210px;" title="' + row[1] + '">' + row[1] + '</span>';
						},
					},
					{
						title: '操作',
						width: '50px',
						style: 'text-align: right;',
						group: [
							{
								title: '删除',
								event: function (row, index) {
									that.ajaxTask('remove_site_rule', { siteName: obj.siteName, index: index, ruleName: obj.ruleName }, function (res) {
										if (res.status) that.render_url_filter_table(obj);
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								},
							},
						],
					},
				],
				data: res,
				done: function (res) {
					if (callback) callback(res);
				},
			});
		});
	},
	/**
	 * 渲染状态码列表
	 */
	render_static_code_list: function (callback) {
		var that = this;
		this.ajaxTask('get_config', function (res) {
			var rdata = res.static_code_config;
			var _arry = [];
			for (var i in rdata) {
				var o = { code: i, status: rdata[i] };
				_arry.push(o);
			}
			that.refresh_table_view({
				el: '#code_table',
				form_id: 'code_table', //用于重置
				height: 270,
				config: [
					{
						title: '状态码',
						templet: function (row, index) {
							return row['code'];
						},
					},
					{
						title: '拦截状态',
						templet: function (row, index) {
							if (row['status'] == '444') return '拦截';
							return row['status'];
						},
					},
					{
						title: '操作',
						width: '120px',
						style: 'text-align: right;',
						group: [
							{
								title: '修改',
								event: function (row, index) {
									that.open_code_view_dialog(false, row);
								},
							},
							{
								title: '删除',
								event: function (row, index) {
									that.ajaxTask('del_static_code_config', { code_from: row['code'], code_to: row['status'] }, function (res) {
										if (res.status) that.render_static_code_list();
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								},
							},
						],
					},
				],
				data: _arry,
				done: function (res) {
					if (callback) callback(res);
				},
			});
		});
	},
	/**
	 * @description 渲染站点配置
	 * @param {Object} obj 站点名称
	 */
	render_site_config: function (obj, callback) {
		var that = this;
		this.ajaxTask('get_site_config_byname', { siteName: obj.siteName }, function (res) {
			that.site_config = res;
			for (var i = 0; i < that.site_show_config.length; i++) {
				var _type = res[that.site_show_config[i]['type']];
				if (that.site_show_config[i]['ps'] === undefined)
					that.site_show_config[i]['ps'] = res['top'][that.site_show_config[i]['type']]['ps'] !== undefined ? res['top'][that.site_show_config[i]['type']]['ps'] : '';
				that.site_show_config[i]['open'] = typeof _type == 'boolean' ? _type : _type != undefined ? _type['open'] : '';
			}
			that.site_show_config[0].ps =
				'<font style="color:red;">' +
				res.cc.cycle +
				'</font> 秒内,请求同一URI累计超过 <font style="color:red;">' +
				res.cc.limit +
				'</font> 次,封锁IP <font style="color:red;">' +
				res.cc.endtime +
				'</font> 秒';
			that.site_show_config[1].open = ''; //攻击次数拦截
			that.site_show_config[12].open = that.site_config.cdn; //使用CDN
			that.site_show_config[13].open = that.site_config.cdn_baidu; //兼容百度CDN
			that.site_show_config[14].open = ''; //禁止执行PHP的URL
			that.site_show_config[17].open = ''; //禁止上传的文件类型
			that.site_show_config[4].open = that.site_config.file_upload.open; //恶意文件上传防御
			that.site_show_config[4].status = that.site_config.file_upload.status;
			that.site_show_config[16].open = ''; //禁止扩展名
			// that.site_show_config[17].open = ''
			that.refresh_table_view({
				el: '#site_config_table',
				form_id: 'site_config_table', //用于重置
				height: 440,
				config: [
					{ fid: 'name', title: '名称' },
					{ fid: 'ps', title: '描述' },
					{
						fid: 'open',
						type: 'btswitch',
						title: '状态',
						style: 'text-align: center;',
						event: function (row, index, event) {
							var submit = function () {
								that.ajaxTask('set_site_obj_open', { siteName: obj.siteName, obj: row.type }, function (res) {
									if (res.status) {
										that.refresh_data_total('site');
										that.render_site_config({ siteName: obj.siteName });
									}
									layer.msg(res.msg, { icon: res.status ? 1 : 2 });
								});
							};
							if (row.type == 'spider_status' && row.open) {
								that.warning_confirm(
									{ title: '提示', msg: '如果关闭蜘蛛爬取，该网站则不会蜘蛛爬取!', tips: '注意事项:如果关闭会影响录入' },
									function () {
										submit();
									},
									function () {
										$(event.target).prev().prop('checked', row.open);
									}
								);
							} else {
								submit();
							}
						},
					},
					{
						fid: 'tools',
						title: '操作',
						style: 'text-align: right;',
						width: '90px',
						group: function (row, index) {
							return [
								{
									title: row.type == 'get' || row.type == 'post' || row.type == 'user-agent' ? '规则' : row.type == 'cdn_baidu' || row.type == 'file_upload' ? ' ' : '设置',
									event: function (row, index) {
										switch (row.type) {
											case 'cc': //CC防御
												that.set_cc_rule_view({
													cc_cycle: res.cc.cycle,
													cc_endtime: res.cc.endtime,
													cc_limit: res.cc.limit,
													siteName: obj.siteName,
													increase_wu_heng: res.increase_wu_heng,
													increase: res.cc.increase,
													cc_increase_type: res.cc.cc_increase_type,
													cc_retry_cycle: res.cc_retry_cycle,
													cc_time: res.cc_time,
													mode: res.cc_mode,
													cc_type_status: res.cc_type_status,
													cc: res.cc,
													retry: res.retry,
												});
												break;
											case 'cc_tolerate': //攻击次数拦截
												that.set_cc_tolerate_view({ cycle: res.retry_cycle, retry: res.retry, time: res.retry_time, siteName: obj.siteName });
												break;
											case 'get': //恶意下载防御
											case 'post': //XSS防御
											case 'user-agent': //恶意文件上传防御
											case 'cookie': //Cookie过滤
												var _rule = row.type;
												if (row.name === '恶意下载防御') _rule = 'url';
												if (row.name === 'SQL注入防御') _rule = 'args';
												if (row.type === 'user-agent') _rule = 'user_agent';
												if (row.type === 'cookie') _rule = 'cookie';
												that.set_site_rule_view({ siteName: obj.siteName, name: row.name, ruleName: _rule });
												break;
											case 'drop_abroad': //禁止海外访问
											case 'drop_china':
												that.set_ip_region_view(row.type, false);
												break;
											case 'scan': //常见扫描器
												that.set_scan_rule_view();
												break;
											case 'spider_status':
												that.set_spider_view({ siteName: obj.siteName, name: row.name }, that.site_config.spider);
												break;
											case 'cdn': //使用CDN
											case 'disable_php_path': //禁止执行PHP的URL
											case 'disable_path': //禁止访问的URL
											case 'disable_ext': //禁止扩展名
											case 'disable_upload_ext': //禁止上传的文件类型
												that.set_other_rule_one_view({ type: row.type, siteName: obj.siteName });
												break;
											case 'url_tell': //受保护的URL
												that.set_defend_url_view({ siteName: obj.siteName });
												break;
											case 'url_rule': //URL专用过滤
												that.set_url_special_filter_view({ siteName: obj.siteName });
												break;
											case 'sensitive_text': //敏感文字替换
												that.set_sensitive_text_view(true, obj.siteName);
												break;
											case 'body_intercept': //违禁词拦截
												that.set_body_intercept_view({ siteName: obj.siteName });
												break;
											case 'preventing_hotlinking':
												that.set_hotlinking_view({ siteName: obj.siteName, id: res.site_id });
												break;
										}
									},
								},
							];
						},
					},
				],
				data: that.site_show_config,
				done: function () {
					if (callback) callback(res);
				},
			});
		});
	},
	/**
	 * @description 渲染海外禁用IP地址列表
	 * @renturn 回调数据
	 */
	render_drop_abroad: function (callback) {
		var that = this;
		this.ajaxTask('get_rule', { ruleName: 'cn' }, function (res) {
			that.drop_abroad_list = res;
			that.refresh_table_view({
				el: '#ip_region_table',
				form_id: 'ip_region_table', //用于重置
				height: 305,
				config: [
					{
						fid: '0',
						title: '起始IP',
						templet: function (row, index) {
							return row[0];
						},
					},
					{
						fid: '1',
						title: '结束IP',
						templet: function (row, index) {
							return row[1];
						},
					},
					{
						title: '操作',
						width: '50px',
						style: 'text-align: right;',
						group: [
							{
								title: '删除',
								event: function (row, index) {
									that.ajaxTask('remove_cnip', { index: index }, function (res) {
										if (res.status) that.render_drop_abroad();
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								},
							},
						],
					},
				],
				data: res,
				done: function (res) {},
			});
		});
	},
	/**
	 * 警告弹框
	 * @param {*} data 配置
	 * @param {*} callback 成功回调
	 * @param {*} cancel 取消回调
	 */
	warning_confirm: function (data, callback, cancel) {
		var random = bt.get_random_code();
		var num1 = random['num1'];
		var num2 = random['num2'];
		var title = data.title;
		var msg = data.msg;
		var tips = data.tips;
		var show = data.show || true;
		layer.open({
			type: 1,
			title: title,
			icon: 0,
			skin: 'delete_site_layer',
			area: '530px',
			closeBtn: 2,
			shadeClose: true,
			btn: [lan.public.ok, lan.public.cancel],
			content:
				'\
				<div class="bt-form webDelete pd30" id="site_delete_form">\
					<i class="layui-layer-ico layui-layer-ico0"></i>\
					<div class="f13 check_title" style="margin-bottom: 20px;">' +
				msg +
				'</div>\
					<div style="color:red;margin:18px 0 18px 18px;font-size:14px;font-weight: bold;">' +
				tips +
				'</div>\
					<div class="vcode">' +
				lan.bt.cal_msg +
				'<span class="text">' +
				num1 +
				' + ' +
				num2 +
				'</span>=<input type="number" id="vcodeResult"></div>\
				</div>\
			',
			yes: function (indexs) {
				var vcodeResult = $('#vcodeResult');
				if (vcodeResult.val() === '') {
					layer.tips('计算结果不能为空', vcodeResult, {
						tips: [1, 'red'],
						time: 3000,
					});
					vcodeResult.focus();
					return false;
				} else if (parseInt(vcodeResult.val()) !== num1 + num2) {
					layer.tips('计算结果不正确', vcodeResult, {
						tips: [1, 'red'],
						time: 3000,
					});
					vcodeResult.focus();
					return false;
				}
				show && layer.close(indexs);
				callback(indexs);
			},
			btn2: function (indexs) {
				cancel && cancel(indexs);
			},
			cancel: function (indexs) {
				cancel && cancel(indexs);
			},
		});
	},
	/**
	 * @description 渲染规则列表
	 * @param {Object} obj 数据类型
	 * @renturn 回调数据
	 */
	render_other_conf: function (obj, callback) {
		var that = this;
		this.ajaxTask('get_rule', { ruleName: obj.ruleName }, function (res) {
			that.refresh_table_view({
				el: '#other_conf_table',
				form_id: 'other_conf_table', //用于重置
				height: 340,
				config: [
					{
						fid: '1',
						title: '规则',
						templet: function (row, index) {
							return '<div class="" style="width:450px;word-break:break-all;line-height: 20px;">' + row[1] + '</div>';
						},
					},
					{ fid: '2', title: '说明', width: '150px' },
					{
						fid: '0',
						title: '状态',
						type: 'btswitch',
						width: '50px',
						style: 'text-align: center;',
						event: function (row, index, event) {
							that.ajaxTask('set_rule_state', { index: index, ruleName: obj.ruleName }, function (res) {
								layer.msg(res.msg, { icon: res.status ? 1 : 2 });
							});
						},
					},
					{
						fid: 'tools',
						title: '操作',
						width: '100px',
						style: 'text-align: right;',
						group: function (row, index) {
							var _arry = [
								{
									title: '编辑',
									event: function (row, index, event, el) {
										var _tr = $(el).parent().parent().parent();
										$(_tr)
											.find('td:eq(' + 0 + ')')
											.html('<textarea class="waf-input waf-table-textarea waf-rule-val" style="width:440px;">' + row[1] + '</textarea>');
										$(_tr)
											.find('td:eq(' + 1 + ')')
											.html('<input type="text" class="waf-input waf-rule-ps" value="' + row[2] + '" style="width:110px"/>');
										$(_tr)
											.find('td:eq(' + 2 + ')')
											.html('');
										$(_tr)
											.find('td:eq(' + 3 + ')')
											.html('<span><a class="btlink save_table_data" href="javascript:;">保存</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a class="btlink clear_table_data" href="javascript:;">取消</a></span>');
										$('.save_table_data').click(function (e) {
											that.ajaxTask(
												'modify_rule',
												{
													index: index,
													ruleBody: $('.waf-rule-val').val(),
													rulePs: $('.waf-rule-ps').val(),
													ruleName: obj.ruleName,
												},
												function (res) {
													if (res.status) that.render_other_conf({ ruleName: obj.ruleName });
													layer.msg(res.msg, { icon: res.status ? 1 : 2 });
												}
											);
										});
										$('.clear_table_data').click(function (e) {
											that.waf_table_list.other_conf_table.reset();
										});
									},
								},
							];
							if (row[3]) {
								_arry.push({
									title: '删除',
									event: function (row, index) {
										bt.confirm({ title: '删除规则', msg: '您真的要删除这条过滤规则吗？', icon: 3, closeBtn: 2 }, function () {
											that.ajaxTask('remove_rule', { ruleName: obj.ruleName, index: index }, function (res) {
												if (res.status) that.render_other_conf({ ruleName: obj.ruleName });
												layer.msg(res.msg, { icon: res.status ? 1 : 2 });
											});
										});
									},
								});
							}
							return _arry;
						},
					},
				],
				data: res,
				done: function (res) {},
			});
		});
	},
	/**
	 * @description 渲染ip白名单
	 * @renturn 回调数据
	 */
	render_ip_white: function (callback) {
		var that = this;
		bt_tools.table({
			el: '#ip_region_table',
			url: '/plugin?action=a&name=btwaf&s=get_rule',
			param: { ruleName: 'ip_white' },
			default: '当前数据为空',
			height: '305px',
			dataFilter: function (res) {
				for (var i = 0; i < res.length; i++) {
					if (res[i].length == 2) {
						res[i].push('');
					}
				}
				that.ip_config_list = res;
				return { data: res };
			},
			column: [
				{ fid: '0', title: '起始IP' },
				{ fid: '1', title: '结束IP' },
				{
					fid: '2',
					title: '备注',
					type: 'input',
					width: 120,
					blur: function (row, index, ev, key, _that) {
						if (row[2] == ev.target.value) return false;
						bt_tools.send(
							{ url: '/plugin?action=a&name=btwaf&s=edit_ip_white_ps', data: { id: index, ps: ev.target.value } },
							function (res) {
								bt_tools.msg(res, { is_dynamic: true });
							},
							'修改备注'
						);
					},
					keyup: function (row, index, ev) {
						if (ev.keyCode === 13) {
							$(this).blur();
						}
					},
				},
				{
					title: '操作',
					type: 'group',
					align: 'right',
					width: 55,
					group: [
						{
							title: '删除',
							event: function (row, index, ev, key, _that) {
								that.ajaxTask('remove_ip_white', { index: index }, function (res) {
									if (res.status) that.render_ip_white();
									layer.msg(res.msg, { icon: res.status ? 1 : 2 });
								});
							},
						},
					],
				},
			],
		});
	},
	/**
	 * @description 渲染ip黑名单
	 * @param {Number} obj [0]ipv4，[1]ipv6
	 * @renturn 回调数据
	 */
	render_ip_black: function (obj, callback) {
		var that = this;
		if (obj === 0) {
			bt_tools.table({
				el: '#ipv4_region_table',
				url: '/plugin?action=a&name=btwaf&s=get_rule',
				param: { ruleName: 'ip_black' },
				default: '当前数据为空',
				height: '285px',
				dataFilter: function (res) {
					for (var i = 0; i < res.length; i++) {
						if (res[i].length == 2) {
							res[i].push('');
						}
					}
					that.ip_config_list = res;
					return { data: res };
				},
				column: [
					{ fid: '0', title: '起始IP' },
					{ fid: '1', title: '结束IP' },
					{
						fid: '2',
						title: '备注',
						type: 'input',
						width: 120,
						blur: function (row, index, ev, key, _that) {
							if (row[2] == ev.target.value) return false;
							bt_tools.send(
								{ url: '/plugin?action=a&name=btwaf&s=edit_ip_black_ps', data: { id: index, ps: ev.target.value } },
								function (res) {
									bt_tools.msg(res, { is_dynamic: true });
								},
								'修改备注'
							);
						},
						keyup: function (row, index, ev) {
							if (ev.keyCode === 13) {
								$(this).blur();
							}
						},
					},
					{
						title: '操作',
						type: 'group',
						align: 'right',
						width: 55,
						group: [
							{
								title: '删除',
								event: function (row, index, ev, key, _that) {
									that.ajaxTask('remove_ip_black', { index: index }, function (res) {
										if (res.status) that.render_ip_black(0);
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								},
							},
						],
					},
				],
			});
		} else {
			var loadT = layer.msg('正在获取IPV6列表中，请稍候。。。', { icon: 16, time: 0, shade: [0.3, '#000'] });
			$.post('/plugin?action=a&name=btwaf&s=get_ipv6_address', function (res) {
				layer.close(loadT);
				var rdata = res.msg;
				that.refresh_table_view({
					el: '#ipv6_region_table',
					form_id: 'ipv6_region_table', //用于重置
					height: 420,
					config: [
						{
							title: 'IPv6地址',
							templet: function (row, index) {
								return '<span class="overflow_hide" style="width: 410px;" title="' + row + '">' + row + '</span>';
							},
						},
						{
							title: '操作',
							width: '50px',
							style: 'text-align: right;',
							group: [
								{
									title: '删除',
									event: function (row, index) {
										that.ajaxTask('del_ipv6_back', { addr: row }, function (res) {
											if (res.status) that.render_ip_black(1);
											layer.msg(res.msg, { icon: res.status ? 1 : 2 });
										});
									},
								},
							],
						},
					],
					data: rdata,
					done: function (rdata) {
						if (callback) callback(rdata);
					},
				});
			});
		}
	},
	/**
	 * @description 渲染ua白名单
	 * @renturn 回调数据
	 */
	render_ua_white: function (callback) {
		var that = this;
		this.ajaxTask('get_ua_white', function (res) {
			that.ua_config_list = res.msg;
			that.refresh_table_view({
				el: '#ua_name_table',
				form_id: 'ua_name_table',
				height: 275,
				config: [
					{
						title: 'UA',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 410px;" title="' + row + '">' + row + '</span>';
						},
					},
					{
						title: '操作',
						style: 'text-align: right;',
						group: [
							{
								title: '删除',
								event: function (row, index) {
									that.ajaxTask('del_ua_white', { ua_white: row }, function (res) {
										if (res.status) that.render_ua_white();
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								},
							},
						],
					},
				],
				data: res.msg,
				done: function (rdata) {
					if (callback) callback(rdata);
				},
			});
		});
	},
	/**
	 * @description 渲染ua黑名单
	 * @renturn 回调数据
	 */
	render_ua_black: function (callback) {
		var that = this;
		this.ajaxTask('get_ua_black', function (res) {
			that.ua_config_list = res.msg;
			that.refresh_table_view({
				el: '#ua_name_table',
				form_id: 'ua_name_table',
				height: 275,
				config: [
					{
						title: 'UA',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 410px;" title="' + row + '">' + row + '</span>';
						},
					},
					{
						title: '操作',
						width: '50px',
						style: 'text-align: right;',
						group: [
							{
								title: '删除',
								event: function (row, index) {
									that.ajaxTask('del_ua_black', { ua_black: row }, function (res) {
										if (res.status) that.render_ua_black();
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								},
							},
						],
					},
				],
				data: res.msg,
				done: function (rdata) {
					if (callback) callback(rdata);
				},
			});
		});
	},
	/**
	 * @description 渲染禁止上传、执行PHP的URL表格、访问的URL表格、扩展名表格
	 * @param {Object} obj 网站名称，数据类型
	 * @renturn 回调数据
	 */
	render_disable_other: function (obj, callback) {
		var that = this;
		this.ajaxTask('get_site_rule', { siteName: obj.siteName, ruleName: obj.ruleName }, function (res) {
			that.refresh_table_view({
				el: '#other_rule_table',
				form_id: 'other_rule_table',
				height: 335,
				config: [
					{
						title: '规则',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 410px;" title="' + row + '">' + row + '</span>';
						},
					},
					{
						title: '操作',
						width: '50px',
						style: 'text-align: right;',
						group: [
							{
								title: '删除',
								event: function (row, index) {
									that.ajaxTask('remove_site_rule', { siteName: obj.siteName, index: index, ruleName: obj.ruleName }, function (res) {
										if (res.status) that.render_disable_other(obj);
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								},
							},
						],
					},
				],
				data: res,
				done: function (res) {
					if (callback) callback(res);
				},
			});
		});
	},
	/**
	 * @description 渲染Api接口防御、关键词拦截列表
	 * @param {String} obj Api接口防御、关键词拦截
	 */
	render_apiDefense_or_wordsKey: function (obj) {
		var that = this;
		this.ajaxTask(obj.type == 'api_defense' ? 'get_url_white_chekc' : 'get_url_find', function (res) {
			that.ua_config_list = res.msg;
			that.refresh_table_view({
				el: '#other_rule_table',
				form_id: 'other_rule_table', //用于重置
				height: 285,
				config: [
					{
						title: 'URL',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 410px;" title="' + row + '">' + row + '</span>';
						},
					},
					{
						title: '操作',
						width: '50px',
						style: 'text-align: right;',
						group: [
							{
								title: '删除',
								event: function (row, index) {
									that.ajaxTask(obj.type == 'api_defense' ? 'del_url_white_chekc' : 'del_url_find', { url_find: row }, function (res) {
										if (res.status) that.render_apiDefense_or_wordsKey({ type: obj.type });
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								},
							},
						],
					},
				],
				data: res.msg,
				done: function (rdata) {},
			});
		});
	},
	/**
	 * @description 渲染url白名单
	 * @param {Number} obj [0]标准模式，[1]标准模式带参数,[2]增强模式
	 */
	render_url_white: function (obj, callback) {
		var that = this;
		if (obj === 0) {
			this.ajaxTask('get_rule', { ruleName: 'url_white' }, function (res) {
				that.url_config_list = res;
				that.refresh_table_view({
					el: '#white_rule_table',
					form_id: 'white_rule_table',
					height: 230,
					config: [
						{
							title: 'URL',
							templet: function (row, index) {
								return '<span class="overflow_hide" style="width: 410px;" title="' + row + '">' + row + '</span>';
							},
						},
						{
							title: '操作',
							width: '50px',
							style: 'text-align: right;',
							group: [
								{
									title: '删除',
									event: function (row, index) {
										that.ajaxTask('remove_url_white', { index: index }, function (res) {
											if (res.status) that.render_url_white(0);
											layer.msg(res.msg, { icon: res.status ? 1 : 2 });
										});
									},
								},
							],
						},
					],
					data: res,
					done: function (res) {
						if (callback) callback(res);
					},
				});
			});
		} else if (obj === 1) {
			this.ajaxTask('get_url_white_senior', function (res) {
				that.refresh_table_view({
					el: '#white_rule_param_table',
					form_id: 'white_rule_param_table',
					height: 330,
					config: [
						{
							title: 'URL',
							width: '262px',
							templet: function (row, index) {
								var url = Object.keys(row)[0];
								return '<span class="overflow_hide" style="width: 246px;" title="' + url + '">' + url + '</span>';
							},
						},
						{
							title: '参数值',
							width: '200px',
							templet: function (row) {
								var url = Object.keys(row)[0];
								var params = row[url];
								return params.length == 0 ? '-' : '<span class="overflow_hide" style="width: 184px;" title="' + params + '">' + params + '</span>';
							},
						},
						{
							title: '操作',
							width: '50px',
							style: 'text-align: right;',
							group: [
								{
									title: '删除',
									event: function (row, index) {
										var url = Object.keys(row)[0];
										var params = row[url].join(',');
										that.ajaxTask('del_url_white_senior', { url: url, param: params }, function (res) {
											if (res.status) that.render_url_white(1);
											layer.msg(res.msg, { icon: res.status ? 1 : 2 });
										});
									},
								},
							],
						},
					],
					data: res,
				});
			});
		} else {
			this.ajaxTask('get_golbls_cc', function (res) {
				var rdata = res.msg;
				that.refresh_table_view({
					el: '#white_rule_strong_table',
					form_id: 'white_rule_strong_table',
					height: 314,
					config: [
						{
							title: 'URL',
							templet: function (row, index) {
								return '<span class="overflow_hide" style="width: 410px;" title="' + row + '">' + row + '</span>';
							},
						},
						{
							title: '操作',
							width: '50px',
							style: 'text-align: right;',
							group: [
								{
									title: '删除',
									event: function (row, index) {
										that.ajaxTask('del_golbls_cc', { text: row }, function (res) {
											if (res.status) that.render_url_white(2);
											layer.msg(res.msg, { icon: res.status ? 1 : 2 });
										});
									},
								},
							],
						},
					],
					data: rdata,
					done: function (rdata) {
						if (callback) callback(rdata);
					},
				});
			});
		}
	},
	/**
	 * @description 渲染URL黑名单
	 */
	render_url_black: function (callback) {
		var that = this;
		this.ajaxTask('get_rule', { ruleName: 'url_black' }, function (res) {
			that.url_config_list = res;
			that.refresh_table_view({
				el: '#other_rule_table',
				form_id: 'other_rule_table',
				height: 270,
				config: [
					{
						title: 'URL',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 410px;" title="' + row + '">' + row + '</span>';
						},
					},
					{
						title: '操作',
						width: '50px',
						style: 'text-align: right;',
						group: [
							{
								title: '删除',
								event: function (row, index) {
									that.ajaxTask('remove_url_black', { index: index }, function (res) {
										if (res.status) that.render_url_black();
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								},
							},
						],
					},
				],
				data: res,
				done: function (res) {
					if (callback) callback(res);
				},
			});
		});
	},
	/**
	 * @description 渲染敏感字体替换表格
	 * @param {Object} obj 是否为站点，站点名称
	 */
	render_sansitive_table: function (obj, callback) {
		var that = this;
		var sDdata = obj.site ? that.site_config.body_character_string : that.overall_config.body_character_string;
		that.refresh_table_view({
			el: '#sensitive_text_table',
			form_id: 'sensitive_text_table', //用于重置
			height: 205,
			config: [
				{
					title: '敏感文字',
					templet: function (row, index) {
						for (var item in row) {
							return '<span class="overflow_hide" style="width: 210px;" title="' + item + '">' + item + '</span>';
						}
					},
				},
				{
					title: '替换文字',
					templet: function (row, index) {
						for (var ex in row) {
							return '<span class="overflow_hide" style="width: 210px;" title="' + row[ex] + '">' + row[ex] + '</span>';
						}
					},
				},
				{
					title: '操作',
					width: '50px',
					style: 'text-align: right;',
					group: [
						{
							title: '删除',
							event: function (row, index) {
								that.ajaxTask(obj.site ? 'del_body_site_rule' : 'del_body_rule', { siteName: obj.site, body: JSON.stringify(row) }, function (res) {
									if (res.status) {
										if (obj.site) {
											$.post('/plugin?action=a&name=btwaf&s=get_site_config_byname', { siteName: obj.site }, function (rdata) {
												that.site_config = rdata;
											});
										} else {
											$.post('/plugin?action=a&name=btwaf&s=get_config', function (rdata) {
												that.overall_config = rdata;
											});
										}
										setTimeout(function () {
											that.render_sansitive_table({ site: obj.site });
										}, 500);
									}
									layer.msg(res.msg, { icon: res.status ? 1 : 2 });
								});
							},
						},
					],
				},
			],
			data: sDdata,
			done: function (sDdata) {
				if (callback) callback(sDdata);
			},
		});
	},
	/**
	 * @description 渲染违禁词表格
	 */
	render_body_intercept_table: function (callback) {
		var that = this;
		this.ajaxTask('get_config', function (res) {
			var bWdata = res.body_intercept;
			that.ban_word_list = bWdata;
			that.refresh_table_view({
				el: '#body_intercept_table',
				form_id: 'body_intercept_table', //用于重置
				height: 205,
				config: [
					{
						title: '违禁词',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 410px;" title="' + row + '">' + row + '</span>';
						},
					},
					{
						title: '操作',
						width: '50px',
						style: 'text-align: right;',
						group: [
							{
								title: '删除',
								event: function (row, index) {
									that.ajaxTask('del_body_intercept', { text: row }, function (res) {
										if (res.status) that.render_body_intercept_table();
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								},
							},
						],
					},
				],
				data: bWdata,
				done: function (bWdata) {
					if (callback) callback(bWdata);
				},
			});
		});
	},
	/**
	 * @description 渲染CDN表格
	 * @param {Object} obj 站点名称
	 */
	render_cdn_table: function (obj, callback) {
		var that = this;
		this.ajaxTask('get_site_cdn_header', { siteName: obj.siteName }, function (res) {
			that.refresh_table_view({
				el: '#other_rule_table',
				form_id: 'other_rule_table',
				height: 275,
				config: [
					{
						title: 'header',
						templet: function (row, index) {
							return '<span class="overflow_hide" style="width: 410px;" title="' + row + '">' + row + '</span>';
						},
					},
					{
						title: '操作',
						width: '50px',
						style: 'text-align: right;',
						group: [
							{
								title: '删除',
								event: function (row, index) {
									that.ajaxTask('remove_site_cdn_header', { siteName: obj.siteName, cdn_header: row }, function (res) {
										that.render_cdn_table(obj);
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								},
							},
						],
					},
				],
				data: res,
				done: function (res) {
					if (callback) callback(res);
				},
			});
		});
	},
	/**
	 * @descripttion 渲染蜘蛛池列表
	 * @param {Number} num 蜘蛛类型
	 * @return: 无返回值
	 */
	render_spider_list: function (num, callback) {
		var that = this,
			_list = ['baidu', 'google', '360', 'sogou', 'yahoo', 'bingbot', 'bytespider'];
		if (typeof num == 'number') num = _list[num];
		$('#spider_list_info').empty();
		this.ajaxTask('get_rule', { ruleName: 'spider', spider: num }, function (res) {
			that.spider_data_list = res;
			var _data = [];
			for (var i = 0; i < res.length; i++) {
				_data.push({ ip: res[i] });
			}
			var spider_table = bt_tools.table({
				el: '#spider_list_info',
				height: '240',
				default: '蜘蛛池列表为空', // 数据为空时的默认提示
				data: _data,
				column: [
					{ type: 'checkbox', width: 20 },
					{
						title: 'IP',
						template: function (row, index) {
							return '<span>' + row.ip + '</span>';
						},
					},
					{
						title: '操作',
						type: 'group',
						width: 50,
						align: 'right',
						group: [
							{
								title: '删除',
								event: function (row, index) {
									bt.confirm({ title: '删除IP【' + row.ip + '】', msg: '删除IP后，可能会导致蜘蛛爬取失败，是否继续操作？' }, function () {
										that.ajaxTask('del_spider', { spider: num, ip: row.ip }, function (res) {
											if (res.status) that.render_spider_list(num);
											layer.msg(res.msg, { icon: res.status ? 1 : 2 });
										});
									});
								},
							},
						],
					},
				],
				tootls: [
					{
						type: 'batch', //batch_btn
						disabledSelectValue: '请选择需要批量操作的站点!',
						selectList: [
							{
								title: '删除IP',
								url: '/plugin?action=a&name=btwaf&s=del_spider',
								param: function (row) {
									return {
										spider: num,
										ip: row.ip,
									};
								},
								refresh: true,
								callback: function (_that) {
									bt.confirm({ title: '批量删除IP', msg: '批量删除IP后，可能会导致蜘蛛爬取失败，是否继续操作？' }, function () {
										var param = {};
										_that.start_batch(param, function (list) {
											var html = '';
											for (var i = 0; i < list.length; i++) {
												var item = list[i];
												html +=
													'<tr><td>' +
													item.ip +
													'</td><td><div style="float:right;"><span style="color:' +
													(item.request.status ? '#20a53a' : 'red') +
													'">' +
													(item.request.status ? '成功' : '失败') +
													'</span></div></td></tr>';
											}
											spider_table.$batch_success_table({
												title: '批量删除IP',
												th: 'IP',
												html: html,
											});
											that.render_spider_list(num);
										});
									});
								},
							},
						],
					},
				],
			});
		});
	},
	/**
	 * @description 站点防盗链数据获取
	 * @param {Object} obj 站点名称,站点id
	 */
	get_hotlinking_data: function (obj) {
		var that = this;
		var loadT = layer.msg('正在获取防盗链设置...', { time: 0, icon: 16, shade: [0.3, '#000'] });
		$.post('/site?action=GetSecurity', { name: obj.siteName, id: obj.id }, function (res) {
			layer.close(loadT);
			$('input[name=sec_fix]').val(res.fix);
			$('input[name=sec_domains]').val(res.domains);
			$('#hotlinking_status').attr('checked', res.status);
			$('#hotlinking_none').attr('checked', res.none);
		});
	},
	/**
	 * @description 设置受保护的URI地址
	 * @param {Object} obj 站点名称,规则名称
	 */
	set_defend_url_view: function (obj) {
		var that = this;
		layer.open({
			type: 1,
			title: '受保护的URI地址【' + obj.siteName + '】',
			area: ['580px', '550px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="defend_url_view" style="padding:25px 15px">\
                    <div><div class="waf-form-input">\
                            <input type="text" class="waf-input" name="url_defend_address" placeholder="URI地址，例如：/admin/update" style="margin-right:10px;width:200px"/>\
                            <input type="text" class="waf-input" name="url_defend_name" placeholder="参数名" style="margin-right:10px; width:110px"/>\
                            <input type="text" class="waf-input" name="url_defend_value" placeholder="参数值" style="width:110px"/>\
                            <button class="btn btn-success btn-sm va0 pull-right add_defend_region">添加</button>\
                        </div>\
                        <div id="defend_url_table"></div>\
                        <ul class="waf_tips_list mtl0 c7 ptb10">\
                            <li>可用于保护网站后台地址,API接口等非公众URI地址不被渗透</li>\
                            <li>参数名与参数值对大小写敏感</li>\
                            <li>设置受保护的URL,访问该URL时必需带有指定的参数名和参数值,否则将被防火墙拦截</li>\
                            <li>假设URI地址: /admin/admin.php 参数名: test 参数值: bt.cn</li>\
                            <li>正确的访问方式: /admin/admin.php?test=bt.cn</li>\
                        </ul>\
                    </div>\
				</div>',
			success: function (layero, index) {
				// 初次触发
				that.render_defend_url_table({ siteName: obj.siteName, ruleName: 'url_tell' });
				// 添加事件
				$('.add_defend_region').click(function () {
					var _address = $('[name=url_defend_address]'),
						_name = $('[name=url_defend_name]'),
						_val = $('[name=url_defend_value]');
					if (_address.val() == '' || _name.val() == '' || _val.val() == '') return layer.msg('请输入地址或参数', { icon: 2 });
					that.ajaxTask(
						'add_site_rule',
						{
							siteName: obj.siteName,
							ruleName: 'url_tell',
							ruleUri: _address.val(),
							ruleValue: _name.val(),
							rulePass: _val.val(),
						},
						function (res) {
							if (res.status) {
								that.render_defend_url_table({ siteName: obj.siteName, ruleName: 'url_tell' });
								_address.val('');
								_name.val('');
								_val.val('');
							}
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
						}
					);
				});
			},
		});
	},
	/**
	 * @description 导出导入视图
	 * @param {String} type IP/URL黑白名单
	 * @param {Booleans} data 是否导入
	 * @param {String} ip_data 导出的数据
	 */
	import_or_export_view: function (type, data, ip_data) {
		var that = this,
			_name = '';
		if (type.indexOf('ip_') == 0) {
			_name = 'IP' + (type == 'ip_white' ? '白' : '黑') + '名单数据';
		} else if (type.indexOf('url_') == 0) {
			_name = 'URL' + (type == 'url_white' ? '白' : '黑') + '名单数据';
		} else {
			_name = '禁止' + (type == 'drop_abroad' ? '海外' : '境内') + '访问数据';
		}
		if (type.indexOf('ip_') == 0 && ip_data) {
			var ip_export = '';
			$.each(ip_data, function (index, item) {
				ip_export += item[0] + '-' + item[1] + '\n';
			});
			ip_data = ip_export;
		} else if (type.indexOf('url_') == 0 && ip_data) {
			ip_data = ip_data.join('\n');
		} else {
			var arr = [];
			if (!data) {
				for (var i = 0; i < ip_data.length; i++) {
					arr.push(ip_data[i].join('-'));
				}
			}
			ip_data = data ? JSON.stringify(ip_data) : arr.join('\n');
		}

		layer.open({
			type: 1,
			title: (data ? '导入' : '导出') + _name,
			area: ['400px', '400px'],
			closeBtn: 2,
			shadeClose: false,
			btn: [data ? '确定' : '导出配置文件', '取消'],
			content:
				'<div class="pd20"><textarea rows="15" style="padding:5px 10px;width:100%;height:100%;border-radius:2px;border:1px solid #ccc;" placeholder="" name="config">' +
				(ip_data != undefined ? ip_data : '') +
				'</textarea></div>',
			success: function () {
				var _placeText = '';
				// 当导入为url黑白名单时
				if (data) {
					if (type.indexOf('url_') == 0) {
						_placeText = '一行一个，例如：\n/admin.php\n/user.php';
					} else if (type.indexOf('ip_') == 0) {
						_placeText = '导入格式如下导入格式如下一行一个(支持三种格式):\n192.168.1.1\n192.168.1.0/24\n192.168.10.1-192.168.10.255';
					} else {
						_placeText = '导入格式如下导入格式如下一行一个(支持三种格式):\n192.168.1.1\n192.168.1.0/24\n192.168.10.1-192.168.10.25';
					}
				} else {
					_placeText = '';
				}
				$('[name=config]').attr('placeholder', _placeText);
			},
			yes: function (layero, index) {
				var _config = $('[name=config]').val();
				if (data) {
					if (_config == '') return layer.msg('导入数据不能为空', { icon: 2 });
					if (type == 'drop_abroad' || type == 'drop_china') type = 'cn';
					var param = {
						s_Name: type,
						pdata: _config,
					};
					if (type.indexOf('url_') == 0) {
						if (_config.indexOf('[') === -1) param['json'] = 1;
					}
					that.ajaxTask('import_data', param, function (res) {
						if (res.status) {
							setTimeout(function () {
								layer.close(layero);
								if (type == 'ip_white') {
									that.render_ip_white();
								}
								if (type == 'ip_black') {
									$('.ip_region_table .tab_list .tab_block:eq(0)').click();
								}
								if (type == 'url_white') {
									$('.other_rule_table .tab_list .tab_block:eq(0)').click();
								}
								if (type == 'url_black') {
									that.render_url_black();
								}
								if (type == 'cn') {
									that.render_drop_abroad();
								}
							}, 1000);
						}
						layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					});
				} else {
					that.render_download_link(_config, type + '.json');
				}
				return false;
			},
		});
	},
	/**
	 * @description 导出导入视图【ua黑白名单，url关键词拦截】
	 * @param {String} type 类型
	 * @param {Booleans} data 是否导出
	 * @param {String} ban_data 导出的数据
	 */
	import_or_export_pure_array_view: function (type, data, other_data) {
		var that = this,
			_name = '';
		if (type == 'ua_black') {
			_name = 'UA黑名单';
		} else if (type == 'ua_white') {
			_name = 'UA白名单';
		} else {
			_name = 'URL关键词拦截';
		}
		layer.open({
			type: 1,
			title: (data ? '导入' : '导出') + _name,
			area: ['400px', '390px'],
			closeBtn: 2,
			shadeClose: false,
			btn: [data ? '确定' : '导出文件', '取消'],
			content:
				'<div class="pd20"><textarea rows="15" style="padding:5px 10px;width:100%;height:250px;border-radius:2px;border:1px solid #ccc;" placeholder="' +
				(data ? (type == 'key_words' ? '一行一个，例如：\nhello\nworld' : '一行一个，例如：\nuser_agent1\nuser_agent2') : '') +
				'" name="other">' +
				(other_data != undefined ? other_data.join('\n') : '') +
				'</textarea></div>',
			yes: function (layero, index) {
				var _other = $('[name=other]').val();
				if (data) {
					if (_other == '') return layer.msg('导入数据不能为空', { icon: 2 });
					var param = {
						pdata: _other,
					};
					if (_other.indexOf('[') === -1) param['json'] = 1;
					that.ajaxTask(type == 'ua_black' ? 'add_black_list' : type == 'ua_white' ? 'add_ua_list' : 'add_url_list', param, function (res) {
						if (res.status) {
							setTimeout(function () {
								layer.close(layero);
								if (type == 'ua_black') that.render_ua_black();
								if (type == 'ua_white') that.render_ua_white();
								if (type == 'key_words') that.render_apiDefense_or_wordsKey(type);
							}, 1000);
						}
						layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					});
				} else {
					that.render_download_link(_other, type + '.json');
				}
			},
		});
	},
	/**
	 * @description 违禁词导出导入视图
	 * @param {String} type 违禁词拦截
	 * @param {Booleans} data 是否导入
	 * @param {String} ban_data 导出的数据
	 */
	import_or_export_body_intercept_view: function (types, data, ban_data) {
		var that = this,
			_name = '违禁词';
		layer.open({
			type: 1,
			title: (data ? '导入' : '导出') + _name,
			area: ['400px', '390px'],
			closeBtn: 2,
			shadeClose: false,
			btn: [data ? '确定' : '导出', '取消'],
			content:
				'<div class="pd20"><textarea rows="15" style="padding:5px 10px;width:100%;height:250px;border-radius:2px;border:1px solid #ccc;" placeholder="' +
				(data ? '导入格式如下：一行一个，如果在同一行输入则视为一个' : '') +
				'" name="ban">' +
				(ban_data != undefined ? ban_data.toString().replace(/[,，]/g, '\n') : '') +
				'</textarea></div>',
			yes: function (layero, index) {
				var _ban = $('[name=ban]').val();
				if (data) {
					if (_ban == '') return layer.msg('导入数据不能为空', { icon: 2 });
					that.ajaxTask('import_body_intercept', { text: _ban }, function (res) {
						if (res.status) {
							setTimeout(function () {
								layer.close(layero);
								that.render_body_intercept_table(); //渲染表格
							}, 1000);
						}
						layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					});
				} else {
					that.render_download_link(_ban, 'banned.json');
				}
			},
		});
	},
	/**
	 * @descripttion 导入导出蜘蛛池
	 * @param {String} param
	 * @param {String} type
	 * @param {String} data
	 * @return: 无返回值
	 */
	import_or_export_spider_view: function (param, type, data) {
		var that = this;
		layer.open({
			type: 1,
			title: (type ? '导入' : '导出') + '蜘蛛池数据',
			area: ['400px', '390px'],
			closeBtn: 2,
			shadeClose: false,
			btn: [type ? '确定' : '导出配置文件', '取消'],
			content:
				'<div class="pd20"><textarea rows="15" style="padding:5px 10px;width:100%;height:100%;border-radius:2px;border:1px solid #ccc;" placeholder="' +
				(type ? '导入格式如下：[&#34;192.168.1.1&#34;,&#34;192.168.1.2&#34;]' : '') +
				'" name="config">' +
				(data != undefined ? JSON.stringify(data) : '') +
				'</textarea></div>',
			yes: function (layero, index) {
				var _config = $('[name=config]').val();
				if (type) {
					if (_config == '') return layer.msg('导入数据不能为空', { icon: 2 });
					layer.confirm('<span style="color:red">导入错误会导致蜘蛛爬取失败,非专业人员请勿操作。</span>', { title: '导入数据确认', closeBtn: 2, icon: 0 }, function () {
						that.ajaxTask('import_spider', { spider: param, ip_list: _config }, function (res) {
							setTimeout(function () {
								layer.close(layero);
								that.render_spider_list(param);
							}, 1000);
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
						});
					});
				} else {
					that.render_download_link(_config, 'spider.json');
				}
			},
		});
	},
	/**
	 * @description 导出/导入防火墙配置
	 */
	import_or_export_waf_config: function (is_import, config) {
		var that = this,
			passkey = '',
			btn = [];
		if (is_import) passkey = config;
		layer.open({
			type: 1,
			title: (is_import ? '导出' : '导入') + '防火墙全局配置',
			area: ['600px', is_import ? '490px' : '400px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="pd20"><textarea rows="15" style="padding:5px 10px;width:100%;height:265px;border-radius:2px;border:1px solid #ccc;" placeholder="' +
				(is_import ? '' : '请在此处粘贴加密配置文本') +
				'" name="ban">' +
				passkey +
				'</textarea><button class="btn btn-success changeCopykeys" style="font-size: 12px;padding: 5px 12px;margin-top: 5px;display:' +
				(is_import ? 'inline-block' : 'none') +
				';">复制</button><button class="btn btn-success import_or_export_keys" style="font-size: 12px;padding: 5px 12px;margin: 5px 0 0 5px;">' +
				(is_import ? '下载' : '导入') +
				'</button><ul class="waf_tips_list mtl0 c7 ptb10" style="display:' +
				(is_import ? 'block' : 'none') +
				';"><li>仅导出全局配置(CC配置,攻击次数拦截配置,IP黑白名单,UA黑白名单,URL黑白名单,敏感文字替换,URL关键词拦截)，不包含站点配置</li><li>GET,POST,URL,UA,Cookie仅导出响应码和开关状态，不包含内部规则</li><li>建议使用复制或下载按钮，选中复制有可能遗漏密钥</li></ul></div>',
			success: function () {
				// 复制
				$('.changeCopykeys').click(function () {
					bt.pub.copy_pass(passkey);
				});
				// 导出下载
				$('.import_or_export_keys').click(function () {
					switch ($(this).text()) {
						case '导入':
							var _ban = $('textarea[name=ban]').val();
							if (_ban == '') return layer.msg('导入数据不能为空', { icon: 2 });
							that.ajaxTask('import_sesings', { backup_data: _ban }, function (res) {
								if (res.status) {
									setTimeout(function () {
										layer.closeAll();
										that.refresh_data_total('home');
									}, 1000);
								}
								layer.msg(res.msg, { icon: res.status ? 1 : 2 });
							});
							break;
						case '下载':
							var _ban = $('textarea[name=ban]').val();
							that.render_download_link(_ban, 'waf_config.json');
							break;
					}
				});
			},
		});
	},
	/**
	 * @description 清空数据列表
	 */
	empty_data_list: function (type) {
		var that = this;
		layer.confirm('是否清空列表数据', { title: '清空列表', closeBtn: 2, icon: 0 }, function () {
			that.ajaxTask('empty_data', { type: type }, function (res) {
				if (res.status) {
					switch (type) {
						case 'ua_white':
							that.render_ua_white();
							break;
						case 'ua_black':
							that.render_ua_black();
							break;
						case 'ip_white':
							that.render_ip_white();
							break;
						case 'ip_black':
							that.render_ip_black(0);
							break;
						case 'url_white':
							that.render_url_white(0);
							break;
						case 'url_black':
							that.render_url_black();
						case 'key_words':
							that.render_apiDefense_or_wordsKey({ type: type });
							break;
					}
				}
				layer.msg(res.msg, { icon: res.status ? 1 : 2 });
			});
		});
	},
	/**
	 * @description 全局防火墙开关按钮
	 */
	waf_switch: function () {
		this.ajaxTask('set_open', function (res) {
			layer.msg(res.msg, { icon: res.status ? 1 : 2 });
			var _status = $('#waf_swicth_all').prop('checked');
			$('.global-set-item.global .global-set-item-body')
				.removeClass('bg-red bg-green')
				.addClass(_status ? 'bg-green' : 'bg-red');
		});
	},
	/**
	 * @description 站点防火墙开关
	 * @param {Object} obj 站点名称
	 */
	waf_switch_site: function (obj) {
		var that = this;
		this.ajaxTask('set_site_obj_open', { siteName: obj, obj: 'open' }, function (res) {
			if (res.status) that.refresh_data_total('site');
			layer.msg(res.msg, { icon: res.status ? 1 : 2 });
		});
	},
	/**全局配置方法结束 */

	/**站点设置方法开始 */
	/**
	 * @descripttion: 创建站点配置
	 */
	create_site_table: function (obj) {
		var that = this;
		var siteNamesList = [];
		(search = obj ? obj.search : ''), (param = {});
		if (search) param = { search: search };
		$('#site_table').unbind().empty();
		var site_table = bt_waf_tools.table({
			el: '#site_table',
			url: obj ? obj.url : '/btwaf/get_site_config3.json',
			load: true,
			class: 'waf_table',
			param: param,
			height: 700,
			default: '正在获取网站信息', //数据为空时的默认提示
			dataFilter: function (res) {
				if (res.data.length == 0) {
					setTimeout(function () {
						$('#site_table tbody tr:eq(0) td:eq(0)').html('当前数据为空');
					}, 10);
				}
				return res;
			},
			column: [
				{ fid: 'id', type: 'checkbox', class: '', width: 20 },
				{
					fid: 'siteName',
					title: '站点',
					width: 150,
					template: function (row, index) {
						var link = '<span title="' + row.siteName + '"><a class="btlink" data-event="site_table_siteName" href="javascript:;">' + row.siteName + '</a></span>';
						return link;
					},
					event: function (row, index) {
						that.set_site_config_view({ siteName: row.siteName });
					},
				},
				{
					fid: 'get',
					title: 'SQL注入防御',
					type: 'checkSpan',
					width: 100,
					label: [
						'拦截次数',
						function (row) {
							return row.total[0].value;
						},
					],
					active: function (row) {
						return row.sql_injection.open ? 'active' : '';
					},
					event: function (row, index) {
						that.ajaxTask('set_site_obj_open', { siteName: row.siteName, obj: 'sql_injection' }, function (res) {
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
						});
					},
				},
				{
					fid: 'post',
					title: 'XSS防御',
					type: 'checkSpan',
					width: 100,
					label: [
						'拦截次数',
						function (row) {
							return row.total[1].value;
						},
					],
					active: function (row) {
						return row.xss_injection.open ? 'active' : '';
					},
					event: function (row, index) {
						that.ajaxTask('set_site_obj_open', { siteName: row.siteName, obj: 'xss_injection' }, function (res) {
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
						});
					},
				},
				{
					fid: 'file_upload',
					title: '恶意文件上传',
					type: 'checkSpan',
					width: 100,
					label: [
						'拦截次数',
						function (row) {
							return row.total[6].value;
						},
					],
					active: function (row) {
						return row.file_upload.open ? 'active' : '';
					},
					event: function (row, index) {
						if (row.file_upload.open) {
							bt.confirm({ title: '关闭站点【' + row.siteName + '】恶意文件上传', msg: '关闭此功能后，将不会拦截木马上传攻击、恶意的文件，是否继续操作？', icon: 3, closeBtn: 2 }, function () {
								that.ajaxTask('set_site_obj_open', { siteName: row.siteName, obj: 'file_upload' }, function (res) {
									bt_tools.msg(res);
									if (res.status) row.file_upload.open = !row.file_upload.open;
								});
							});
						} else {
							that.ajaxTask('set_site_obj_open', { siteName: row.siteName, obj: 'file_upload' }, function (res) {
								bt_tools.msg(res);
								if (res.status) row.file_upload.open = !row.file_upload.open;
							});
						}
					},
				},
				{
					fid: 'user-agent',
					title: '恶意爬虫防御',
					type: 'checkSpan',
					width: 100,
					label: [
						'拦截次数',
						function (row) {
							return row.total[3].value;
						},
					],
					active: function (row) {
						return row['user-agent'] ? 'active' : '';
					},
					event: function (row, index) {
						that.ajaxTask('set_site_obj_open', { siteName: row.siteName, obj: 'user-agent' }, function (res) {
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
						});
					},
				},
				// {fid:'cookie',title:'Cookie', width: 100, label:['拦截次数',function(row){ return row.total[4].value}], active:function(row){return row.cookie?'active':''}, type:'checkSpan',width:'7%',event:function(row,index){
				// 		that.ajaxTask('set_site_obj_open',{siteName:row.siteName,obj:'cookie'},function(res){
				// 			layer.msg(res.msg,{icon:res.status?1:2});
				// 		});
				// }},
				{
					fid: 'drop_abroad',
					title: '禁国外',
					width: 100,
					active: function (row) {
						return row.drop_abroad ? 'active' : '';
					},
					type: 'check',
					width: '7%',
					event: function (row, index) {
						that.ajaxTask('set_site_obj_open', { siteName: row.siteName, obj: 'drop_abroad' }, function (res) {
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
						});
					},
				},
				{
					fid: 'drop_china',
					title: '禁国内',
					width: 100,
					active: function (row) {
						return row.drop_china ? 'active' : '';
					},
					type: 'check',
					width: '7%',
					event: function (row, index) {
						that.ajaxTask('set_site_obj_open', { siteName: row.siteName, obj: 'drop_china' }, function (res) {
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
						});
					},
				},
				{
					fid: 'cdn',
					title: 'CDN<a class="bt-ico-ask" title="CDN：当网站开启CDN时候获取IP的开关">?</a>',
					active: function (row) {
						return row.cdn ? 'active' : '';
					},
					type: 'check',
					width: '7%',
					event: function (row, index) {
						that.ajaxTask('set_site_obj_open', { siteName: row.siteName, obj: 'cdn' }, function (res) {
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
						});
					},
				},
				{
					fid: 'cc',
					title: 'CC防御',
					type: 'checkSpan',
					width: 100,
					label: [
						'拦截次数',
						function (row) {
							return row.total[2].value;
						},
					],
					active: function (row) {
						return row.cc.open ? 'active' : '';
					},
					event: function (row, index) {
						that.ajaxTask('set_site_obj_open', { siteName: row.siteName, obj: 'cc' }, function (res) {
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
						});
					},
				},
				{
					fid: 'open',
					type: 'switch',
					title: '状态',
					width: 70,
					event: function (row, index) {
						that.ajaxTask('set_site_obj_open', { siteName: row.siteName, obj: 'open' }, function (res) {
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
						});
					},
				},
				{
					title: '总拦截次数',
					width: 100,
					template: function (row) {
						var num = 0, title = '';
						for (var i = 0; i < row.total.length; i++) {
							num += row.total[i].value;
							title += row.total[i].name + '：' + row.total[i].value + '次\n';
						}
						return '<a class="'+ (num ? 'bterror' : '') +'" title="总拦截次数：'+ num +'次\n'+ title +'" style="cursor: pointer;">' + num + '</a>'
					},
					event: function (row, index, ev) {
						if(ev.target.className.indexOf('bterror') === -1) return layer.msg('总拦截次数为：0',{icon:6});
						bt.open({
							type: 1,
							area: '400px',
							title: '总拦截次数【'+ row.siteName +'】',
							closeBtn: 2,
							shadeClose: false,
							content: '<div id="total_num" style="padding: 10px 20px;"></div>',
							success:function(layero){
								bt_tools.table({
									el:'#total_num',
									data:row.total,
									column: [{
										fid: 'name',
										title: '类型',
									},{
										fid: 'value',
										title: '拦截次数',
										template:function(row){
											return '<span class="'+ (row.value ? 'red' : '') +'" title="拦截次数：'+ row.value +'次">' + row.value + '</span>'
										}
									}],
									success:function(){
										$(layero).css({
											top: ($(window).height() - $(layero).height()) / 2 + 'px',
										})
									}
								})
							}
						})
					}
				},
				{
					title: '操作',
					type: 'group',
					width: 130,
					align: 'right',
					group: [
						{
							template: function (row, index) {
								return '拦截记录';
							},
							event: function (row, index) {
								that.ajaxTask('get_logs_list', { siteName: row.siteName }, function (res) {
									if (res.length > 0) {
										that.get_site_logs_view(row, res);
									} else {
										layer.msg('暂无站点日志', { icon: 6 });
									}
								});
							},
						},
						{
							title: '设置',
							event: function (row, index) {
								that.set_site_config_view({ siteName: row.siteName });
							},
						},
					],
				},
			],
			success: function (data) {
				var res = data.data;
				if (res.length >= 1) {
					for (var i = 0; i < res.length; i++) {
						that.batch_config_sitename.push({ siteName: res[i].siteName });
					}
				}
				$('.search-input').val(search);
				$('.search-input')
					.unbind('keyup')
					.on('keyup', function (e) {
						if (e.keyCode == 13) {
							if ($(this).val() !== '') that.create_site_table({ url: '/plugin?action=a&s=get_search_sites&name=btwaf ', search: $(this).val() });
						}
					});
				$('.glyphicon-search')
					.unbind('click')
					.on('click', function () {
						if ($(this).prev().val() !== '') that.create_site_table({ url: '/plugin?action=a&s=get_search_sites&name=btwaf ', search: $(this).prev().val() });
					});
			},
			// 渲染完成
			tootls: [
				{
					type: 'batch', //batch_btn
					positon: ['left', 'bottom'],
					height: 200,
					placeholder: '请选择批量操作',
					buttonValue: '批量操作',
					disabledSelectValue: '请选择需要批量操作的网站!',
					selectList: [
						{
							url: '/btwaf/batch_site_all.json',
							group: [
								{ title: '开启SQL注入防御', param: { is_all: 0, obj: 'get', is_status: true } },
								{ title: '开启XSS防御', param: { is_all: 0, obj: 'post', is_status: true } },
								{ title: '开启恶意爬虫防御', param: { is_all: 0, obj: 'user-agent', is_status: true } },
								{ title: '开启CC防御', param: { is_all: 0, obj: 'cc', is_status: true } },
								{ title: '开启Cookie拦截', param: { is_all: 0, obj: 'cookie', is_status: true } },
								{ title: '开启禁国外拦截', param: { is_all: 0, obj: 'drop_abroad', is_status: true } },
								{ title: '开启禁国内拦截', param: { is_all: 0, obj: 'drop_china', is_status: true } },
								{ title: '开启CDN拦截', param: { is_all: 0, obj: 'cdn', is_status: true } },
								{ title: '开启状态', param: { is_all: 0, obj: 'open', is_status: true } },
								{ title: '关闭SQL注入防御', param: { is_all: 0, obj: 'get', is_status: false } },
								{ title: '关闭XSS防御', param: { is_all: 0, obj: 'post', is_status: false } },
								{ title: '关闭恶意爬虫防御', param: { is_all: 0, obj: 'user-agent', is_status: false } },
								{ title: '关闭CC防御', param: { is_all: 0, obj: 'cc', is_status: false } },
								{ title: '关闭Cookie拦截', param: { is_all: 0, obj: 'cookie', is_status: false } },
								{ title: '关闭禁国外拦截', param: { is_all: 0, obj: 'drop_abroad', is_status: false } },
								{ title: '关闭禁国内拦截', param: { is_all: 0, obj: 'drop_china', is_status: false } },
								{ title: '关闭CDN拦截', param: { is_all: 0, obj: 'cdn', is_status: false } },
								{ title: '关闭状态', param: { is_all: 0, obj: 'open', is_status: false } },
							],
							paramName: 'siteNames', //列表参数名,可以为空
							paramId: 'siteName', // 需要传入批量的id
							theadName: '站点名称',
							refresh: true,
							beforeRequest: function (list) {
								var arry = [];
								$.each(list, function (index, item) {
									arry.push(item.siteName);
								});
								return JSON.stringify(arry);
							},
						},
					],
				},
				{
					//分页显示
					type: 'page',
					positon: ['right', 'bottom'], // 默认在右下角
					pageParam: 'p', //分页请求字段,默认为 : p
					page: 1, //当前分页 默认：1
					numberParam: 'limit', //分页数量请求字段默认为 : limit
					number: 10, //分页数量默认 : 20条
					numberList: [10, 20, 50, 100, 200], // 分页显示数量列表
					numberStatus: true, //　是否支持分页数量选择,默认禁用
					jump: true, //是否支持跳转分页,默认禁用
				},
			],
		});
		function btwaf_batch(name, that, status) {
			bt.confirm({ title: '批量执行任务', msg: '是否' + (status ? '开启' : '关闭') + '选中站点' + name + '拦截，是否继续？', icon: 0 }, function (index) {
				layer.close(index);
				that.start_batch({}, function (list) {
					var html = '';
					for (var i = 0; i < list.length; i++) {
						var item = list[i];
						html +=
							'<tr><td>' +
							(item.siteName.length >= 15 ? item.siteName.substring(0, 15) + '...' : item.siteName) +
							'</td><td><div style="float:right;"><span style="color:' +
							(item.request.status ? '#20a53a' : 'red') +
							'">' +
							item.request.msg +
							'</span></div></td></tr>';
					}
					siteNamesList.length = 0;
					site_table.$batch_success_table({ title: '批量执行任务', th: '任务名称', html: html });
					site_table.$refresh_table_list(true);
				});
			});
		}
	},
	/**
	 * @descripttion 清理站点/封锁历史日志
	 * @return: 无返回值
	 */
	clean_site_or_history_log: function (_type) {
		var that = this,
			_selection = [],
			_isall = false;
		switch (_type) {
			case 'site':
				layer.open({
					type: 1,
					title: '清理站点日志',
					area: '450px',
					closeBtn: 2,
					skin: 'clean_log_data',
					btn: ['清理', '取消'],
					content:
						'<div class="waf-form pd20">\
						<div class="waf-line is_clean_site">\
							<span class="name-l">站点</span>\
							<div class="info-r"><div class="select-menu"></div></div>\
						</div>\
					</div>',
					success: function () {
						bt_waf.select({
							el: '.select-menu',
							method: 'get_site_config',
							data: {},
							config: { width: 260, placeholder: '请选择站点', ischeck: true, issearch: true },
							dataFilter: function (Fdata) {
								var _arry = [];
								$.each(Fdata, function (index, item) {
									_arry.push([item['siteName'], item['siteName']]);
								});
								return _arry;
							},
							formatRepoSelection: function (list, isall) {
								_selection = list;
								_isall = isall;
							},
						});
					},
					yes: function (index, layero) {
						if (_selection.length <= 0) return layer.msg('请选择站点', { icon: 0 });
						bt.simple_confirm({ title: '日志清理', msg: '清理选中站点的日志记录，是否继续操作？' }, function () {
							that.ajaxTask('remove_log', { safe_logs: 0, site_all: _isall ? 1 : 0, site_logs: JSON.stringify(_isall ? [] : _selection) }, function (res) {
								if (res.status) layer.close(index);
								layer.msg(res.msg, { icon: res.status ? 1 : 2 });
							});
						});
					},
				});
				break;
			case 'history':
				layer.confirm('清理所有封锁的日志记录，但已经封锁的IP不会被解封！', { title: '清理日志', closeBtn: 2, icon: 0 }, function () {
					that.ajaxTask('remove_log', { safe_logs: 1, site_all: 0, site_logs: JSON.stringify([]) }, function (res) {
						layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					});
				});
				break;
		}
	},
	/**
	 * @description 获取站点日志视图
	 * @param {Object} row 当前站点对象数据
	 * @param {Object} dateList 日志列表
	 */
	get_site_logs_view: function (row, dateList) {
		var that = this;
		layer.open({
			type: 1,
			title: '拦截日志-【' + that.escapeHTML(row.siteName) + '】',
			area: ['980px', '742px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'<div class="site_logs_table">\
						<div style="display: flex;justify-content: space-between;align-items: center;">\
							<div>\
								<div class="waf_date_select">\
									<div class="waf-title">选择日期：</div>\
									<div class="searcTime" style="display:inline-block"></div>\
								</div>\
								<div class="waf_date_select">\
										<input class="waf-inputs" id="time_choose" style="line-height: 16px;margin-left: -4px;border-left:0" placeholder="自定义时间" type="text" value="" lay-key="100001">\
								</div>\
							</div>\
							<div class="inlineBlock c3" style="float: right;font-size: 12px;">\
								IP过滤：\
								<div class="mt_search">\
									<input type="text" class="search_ip" placeholder="支持逗号分割IP，支持192.168.1.*搜索IP区间" name="search_ip" value="" style="margin:0">\
									<button type="button" class="btn btn-default btn-sm mr10 ipSearch" style="padding: 4px 10px;">搜索</button>\
									<div class="ipCompleteSearch" style="display: inline-block;">\
										<a class="btlink modeFilter">高级搜索</a>\
										<div class="complete_search_view hide" style="top: 60px;">\
											<div class="bt-form">\
												<div class="line">\
													<span class="tname">URL过滤：</span>\
													<div class="info-r">\
														<input type="text" class="search_url" placeholder="支持逗号分割URL" name="search_url" value="" style="margin:0">\
													</div>\
												</div>\
												<div class="line">\
													<span class="tname">UA过滤：</span>\
													<div class="info-r">\
														<input type="text" class="search_user_agent" placeholder="请输入UserAgent" name="search_user_agent" >\
													</div>\
												</div>\
											</div>\
										</div>\
									</div>\
								</div>\
							</div>\
						</div>\
						<div id="site_logs_table"></div>\
					</div>',
			success: function (layero, index) {
				var _html = '';
				$.each(that.time_cycle, function (index, item) {
					_html += '<span class="gt ' + (item.day == 1 ? 'on' : '') + '" style="float:none" title="' + item.title + '" data-index="' + item.day + '" >' + item.title + '</span>';
				});
				$('.site_logs_table').on('click', '.gt', function () {
					$(this).addClass('on').siblings().removeClass('on');
					var day = $(this).attr('data-index');
					that.get_site_logs(day, row.siteName, dateList[0]);
				});
				$('.searcTime').append(_html);
				that.render_site_logs({ siteName: row.siteName, start_time: dateList[0] });
				$('#time_choose').removeAttr('lay-key');
				laydate.render({
					elem: '#time_choose',
					range: true,
					value: '',
					done: function (value, startdate, endDate) {
						var timeA = value.split(' - ');
						$('#time_choose').val(value);
						if (timeA[0] == '') timeA[0] = dateList[0];
						that.render_site_logs({ siteName: row.siteName, start_time: timeA[0], end_time: timeA[1] });
					},
				});

				//高级搜索
				$('.site_logs_table').on('click', '.ipCompleteSearch', function (e) {
					var box = $(this).find('.complete_search_view');
					if ($(e.target).hasClass('modeFilter')) {
						if (box.hasClass('hide')) {
							$('.modeFilter').css('color', '#23527c');
							box.removeClass('hide');
						} else {
							box.addClass('hide');
							$('.modeFilter').removeAttr('style');
						}
					}
					$(document).one('click', function () {
						box.addClass('hide');
						$('.modeFilter').removeAttr('style');
					});
					e.stopPropagation();
				});
				//搜索
				$('.site_logs_table').on('click', '.ipSearch', function (e) {
					var param = {
						ip: $('.site_logs_table .search_ip').val(),
						serach_url: $('.site_logs_table .search_url').val(),
						user_agent: $('.site_logs_table .search_user_agent').val(),
						siteName: row.siteName,
					};
					that.render_site_logs({ url: '/plugin?action=a&s=get_site_safe_logs&name=btwaf', param: param });
				});
			},
		});
	},
	/**
	 * @description 计算站点日志时间
	 * @param {Object} day 天数
	 * @param {String} siteName 站点名称
	 */
	get_site_logs: function (day, siteName) {
		var that = this;
		var timeList = that.getBeforeDate(day),
			start_time = undefined,
			end_time = undefined,
			limit = $('.page_select_number').val();
		if (timeList.length > 2) {
			(start_time = timeList.pop()), (end_time = timeList[0]);
		} else {
			start_time = timeList.pop();
		}
		that.render_site_logs({ siteName: siteName, start_time: start_time, end_time: end_time, limit: limit });
	},
	/**
	 * @description 设置站点配置视图
	 * @param {Object} obj 站点名称
	 */
	set_site_config_view: function (obj, callback) {
		var that = this;
		layer.open({
			type: 1,
			title: '网站配置【 ' + obj.siteName + ' 】',
			area: ['760px', '610px'],
			closeBtn: 2,
			shadeClose: false,
			content:
				'\
			<div class="waf_site_body pd20">\
				<div class="waf_head_view">\
					<span class="pull-left" style="font-weight: 400;font-size: 16px;margin-right: 10px;">网站防火墙开关</span>\
					<div class="waf-switch pull-left">\
						<input class="btswitch btswitch-ios" id="waf_swicth_site" type="checkbox">\
						<label class="btswitch-btn" for="waf_swicth_site" onclick="bt_waf.waf_switch_site(\'' +
				obj.siteName +
				'\')"></label>\
					</div>\
				</div>\
				<div id="site_config_table"></div>\
				<ul class="waf_tips_list mtl0 c7 ptb10">\
					<li>注意: 此处大部分配置,仅对当前站点有效!</li>\
				</ul>\
			</div>',
			success: function (index, layero) {
				that.render_site_config(obj, function (res) {
					$('#waf_swicth_site').prop('checked', res.open);
				});
			},
		});
	},
	/**
	 * @description 渲染站点日志
	 * @param {Object} obj 站点名称,记录的日期，页数
	 */
	render_site_logs: function (obj, callback) {
		var that = this;
		$('#site_logs_table').empty();
		var _intercept = bt_waf_tools.table({
			el: '#site_logs_table',
			url: obj['url'] ? obj['url'] : '/btwaf/get_safe_logs_sql2.json',
			height: 560,
			load: true,
			param: obj['param'] ? obj['param'] : { siteName: obj.siteName, start_time: obj.start_time, end_time: obj.end_time, limit: obj.limit }, //参数
			class: 'waf_table',
			default: '没有日志记录', //数据为空时的默认提示
			column: [
				{ type: 'checkbox', class: '', width: 20 },
				{ fid: 'time_localtime', type: 'text', width: '140px', title: '开始时间' },
				{
					fid: 'ip',
					title: '用户IP',
					width: '110px',
					type: 'link',
					template: function (row) {
						return that.escapeHTML(row.ip);
					},
					event: function (row, index) {
						var ipv4Range = '';
						if (bt.check_ip(row.ip)) {
							ipv4Range =
								'<div class="mt10"><input type="checkbox" id="ipRangeInsulate"/><label for="ipRangeInsulate" style="font-weight: 400;margin: 0 0 0 5px;cursor: pointer;">是否拉黑整个IP段？</label></div>';
						}
						layer.confirm('是否将 <span style="color:red">' + row.ip + '</span> 添加到IP黑名单？' + ipv4Range, { title: '加入IP黑名单', closeBtn: 2, icon: 0 }, function () {
							if (bt.check_ip(row.ip)) {
								var isCheck = $('#ipRangeInsulate').is(':checked');
								if (!isCheck) {
									that.ajaxTask('add_ip_black', { start_ip: row.ip, end_ip: row.ip }, function (res) {
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								} else {
									var ipRange = row.ip.replace(/\d{1,3}$/, '0/24');
									bt_waf.http({
										method: 'import_data',
										data: { s_Name: 'ip_black', pdata: ipRange },
										success: function (res) {
											layer.msg(res.status ? '操作成功' : '添加失败', { icon: res.status ? 1 : 2 });
										},
									});
								}
							} else {
								that.ajaxTask('set_ipv6_back', { addr: row.ip }, function (res) {
									layer.msg(res.msg, { icon: res.status ? 1 : 2 });
								});
							}
						});
					},
				},
				{
					fid: 'type',
					title: '类型',
					type: 'text',
					width: '60px',
					template: function (row, index) {
						return '<span title="' + row.type + '">' + (row.type != null ? (row.type.length >= 8 ? row.type.substring(0, 8) + '...' : row.type) : row.type) + '</span>';
					},
				},
				{
					fid: 'url',
					type: 'text',
					title: 'URL地址',
					width: '160px',
					template: function (row, index) {
						var rule_arry,
							text = '';
						return (
							'<span title="' +
							that.escapeHTML(row.uri) +
							'">' +
							(row.type != null ? (row.uri.length >= 18 ? that.escapeHTML(row.uri).substring(0, 18) + '...' : that.escapeHTML(row.uri)) : that.escapeHTML(row.type)) +
							'</span>'
						);
					},
				},
				{
					fid: 'status',
					title: '状态',
					type: 'text',
					width: '60px',
					template: function (row, index) {
						return '已拦截';
					},
				},
				{
					fid: 'ip_country',
					type: 'text',
					title: 'IP归属地',
					width: '120px',
					template: function (row, index) {
						if (row.ip_country == '内网地址') return '<span title="' + row.ip_country + '">' + row.ip_country + '</span>';
						return '<span title="' + that.render_ip_country(row) + '">' + that.render_ip_country(row) + '</span>';
					},
				},
				{
					fid: 'filter_rule',
					title: '过滤器',
					width: '100px',
					template: function (row, index) {
						return (
							'<span title="' +
							row.filter_rule +
							'">' +
							(row.filter_rule != null ? (row.filter_rule.length >= 20 ? row.filter_rule.substring(0, 20) + '...' : row.filter_rule) : row.filter_rule) +
							'</span>'
						);
					},
				},
				{
					title: '操作',
					type: 'group',
					width: '160px',
					align: 'right',
					group: [
						{
							title: 'URL加白',
							event: function (row, index) {
								if (row.uri == '/') return layer.msg('当前ip的uri为根目录,无法执行误报操作！');
								var ipv4Range = '';
								if (row.uri.indexOf('?') !== -1 && row.uri.indexOf('=') !== -1)
									ipv4Range =
										'<div class="mt10"><input type="checkbox" id="urlRangeInsulate"/><label for="urlRangeInsulate" style="font-weight: 400;margin: 0 0 0 5px;cursor: pointer;">是否添加URI参数白名单？</label></div>';
								layer.confirm('加入URL白名单后此URL将不再进行防御，是否继续操作？' + ipv4Range, { title: '加入URL白名单', icon: 3, closeBtn: 2 }, function () {
									var rule_arry = row.incoming_value.indexOf('b"') > -1 ? row.incoming_value.substring(2, row.incoming_value.length - 1).split(' >> ') : row.incoming_value.split(' >> ');
									var isCheck = $('#urlRangeInsulate').is(':checked');
									if (row.http_log_path === 1) {
										$.post('/btwaf/get_logs', { path: row.http_log }, function (res) {
											var param = {
												url_rule: row.uri,
												error_log: row.ip + ' >> ' + row.incoming_value,
												http_log: res,
											};
											if (isCheck) param['param'] = 1;
											that.ajaxTask('wubao_url_white', param, function (res) {
												layer.msg(res.msg, { icon: res.status ? 1 : 2 });
												if (rule_arry[1] != undefined) {
													$.get('https://www.bt.cn/Api/add_waf_logs?data=' + rule_arry[1], function (rdata) {}, 'jsonp');
												}
											});
										});
									} else {
										var param = {
											url_rule: row.uri,
											error_log: row.ip + ' >> ' + row.incoming_value,
											http_log: row.http_log,
										};
										if (isCheck) param['param'] = 1;
										that.ajaxTask('wubao_url_white', param, function (res) {
											layer.msg(res.msg, { icon: res.status ? 1 : 2 });
											if (rule_arry[1] != undefined) {
												$.get('https://www.bt.cn/Api/add_waf_logs?data=' + rule_arry[1], function (rdata) {}, 'jsonp');
											}
										});
									}
								});
							},
						},
						{
							title: '详情',
							event: function (row, index) {
								that.create_details(row);
							},
						},
						{
							title: 'HTTP',
							event: function (row, index) {
								that.create_HTTP(row);
							},
						},
					],
				},
			],
			// 渲染完成
			tootls: [
				// { // 批量操作
				//     type: 'batch',//batch_btn
				//     positon: ['left', 'bottom'],
				//     config: {
				//         title: "误报",
				//         url: '/plugin?action=a&name=btwaf&s=wubao_url_white',
				//         load: true,
				//         param: function (row) {
				//             return { url_rule:row.uri };
				//         },
				//         callback: function (that) {
				//             console.log(_intercept)
				//             var flag = false;
				//             $.each(that.check_list,function(index,item){
				//                 if(item.uri == '/'){
				//                     layer.msg('当前选中的第'+(index+1)+'条数据uri为根目录,无法执行批量误报操作！')
				//                     flag = true;
				//                     return false;
				//                 }
				//             })
				//             if(!flag){
				//                 bt.show_confirm('批量删除误报', '<span style="color:red">是否执行批量误报反馈</br></span>', function (index) {
				//                     layer.close(index);
				//                     that.start_batch({}, function (list) {
				//                         var html = '';
				//                         for (var i = 0; i < list.length; i++) {
				//                             var item = list[i];
				//                             html += '<tr><td>' + item.ip + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + item.request.msg + '</span></div></td></tr>';
				//                             if(item.request.status){
				//                                 var rule_arry = item.incoming_value.indexOf('b"')>-1?item.incoming_value.substring(2,item.incoming_value.length-1).split(" >> "):item.incoming_value.split(" >> ");
				//                                 if (rule_arry[1] != undefined) { $.get('https://www.bt.cn/Api/add_waf_logs?data=' + rule_arry[1], function (rdata) { }, 'jsonp') }
				//                             }
				//                         }
				//                         _intercept.$batch_success_table({ title: '批量误报', th: 'IP', html: html });
				//                         _intercept.$refresh_table_list(true);
				//                     });
				//                 });
				//             }
				//         }
				//     }
				// },
				{
					//分页显示
					type: 'page',
					positon: ['right', 'bottom'], // 默认在右下角
					pageParam: 'p', //分页请求字段,默认为 : p
					page: 1, //当前分页 默认：1
					numberParam: 'limit', //分页数量请求字段默认为 : limit
					number: 15,
					numberList: [10, 15], // 分页显示数量列表
					numberStatus: true, //　是否支持分页数量选择,默认禁用
					jump: true, //是否支持跳转分页,默认禁用
				},
			],
		});
	},
	/**站点设置方法结束 */

	/**木马查杀方法开始 */
	/**
	 * @description 渲染扫描webshell
	 * @param {Object} obj 路径
	 */
	render_san_webshell: function (obj, callback) {
		var that = this;
		that.refresh_table_view({
			el: '#scan_webshell_table',
			form_id: 'scan_webshell_table', //用于重置
			height: 400,
			config: [
				{
					fid: '0',
					title: '文本名称',
					templet: function (row, index) {
						var _file = Object.keys(row)[0].split('/');
						return (
							'<a href="javascript:;" class="btlink file_rule_link" title="' +
							Object.keys(row)[0] +
							'"  onclick="bt.pub.on_edit_file(0,\'' +
							Object.keys(row)[0] +
							'\')" >' +
							_file[_file.length - 1] +
							'</a>'
						);
					},
				},
				{
					fid: '1',
					title: '规则',
					width: 200,
					class: 'file_rule table-text-cell',
					templet: function (row, index) {
						return '<span>' + row[Object.keys(row)[0]] + '</span>';
					},
				},
				{
					fid: 'total',
					title: '操作',
					width: 290,
					style: 'text-align: right;',
					group: [
						{
							title: '宝塔检测',
							event: function (row, index) {
								that.ajaxTask('send_baota', { filename: Object.keys(row)[0] }, function (res) {
									layer.msg(res.msg, { icon: res.status ? 1 : 2 });
								});
							},
						},
						{
							title: '第三方检测',
							event: function (row, index) {
								that.ajaxTask('upload_file_url', { filename: Object.keys(row)[0] }, function (res) {
									layer.msg(res.msg, { icon: res.status ? 1 : 2 });
								});
							},
						},
						{
							title: '打开文件',
							event: function (row, index) {
								bt.pub.on_edit_file(0, Object.keys(row)[0]);
							},
						},
						{
							title: '误报',
							event: function (row, index) {
								var _file = Object.keys(row)[0];
								layer.confirm('是否确定提交误报反馈？', { title: '误报反馈', icon: 3, closeBtn: 2 }, function () {
									that.ajaxTask('lock_not_webshell', { not_path: _file, path: obj['path'] }, function (res) {
										layer.msg(res.msg, { icon: res.status ? 1 : 2 });
									});
								});
							},
						},
					],
				},
			],
			data: obj.data,
			done: function (res) {
				$('#scan_webshell_table .fixed-table .file_rule').hover(
					function (e) {
						var _val = $(this).find('span').text(),
							_that = $(this);
						$(this).append('<div class="rule_down_icon" style="top:' + e.currentTarget.offsetTop + 'px;right:274px"><i class="iconfont iconxialadown" style="font-size: 20px;"></i></div>');
						$(this)
							.unbind('click')
							.click(function (e) {
								if (_that.find('.rule_mask').length === 0) {
									_that.append(
										'<div class="rule_mask" style="top:' + e.currentTarget.offsetTop + 'px;"><div class="content">' + _val + '</div><i class="iconfont iconguanbi" style="font-size: 25px;"></i></div>'
									);
								}
								e.preventDefault();
								e.stopPropagation();
							});
						$('.file_rule').on('click', '.iconguanbi', function (e) {
							$(this).parent().remove();
							_that.find('.rule_down_icon').remove();
							e.preventDefault();
							e.stopPropagation();
						});
					},
					function (e) {
						$(this).find('.rule_down_icon').remove();
					}
				);
				if (callback) callback(res);
			},
		});
	},
	/**
	 * @description 刷新webshell页面数据
	 * @param {String} type 选项卡>当前
	 */
	refresh_data_webshell: function (type) {
		var that = this;
		switch (type) {
			case 'webshell_list':
				that.render_webshell_list();
				break;
			case 'killing': //查杀
				that.render_san_webshell({ data: [] });
				break;
			case 'rule_list': //规则列表
				that.render_webshell_rule();
				break;
			case 'logs': //日志
				that.ajaxTask('get_log', function (res) {
					$('.webshell_logs').html(res);
					$('.webshell_logs').scrollTop(99999999);
				});
				break;
		}
	},
	/**
	 * @description 渲染木马文件列表
	 */
	render_webshell_list: function (callback) {
		var that = this;
		that.ajaxTask('Get_Recycle_bin', function (res) {
			that.refresh_table_view({
				el: '#webshell_list_table',
				form_id: 'webshell_list_table',
				height: 670,
				config: [
					{ fid: 'name', title: '文件名', width: 80 },
					{
						fid: 'dname',
						title: '原路径',
						width: 450,
						templet: function (row, index) {
							return (
								'<span title="' +
								row.dname +
								'" class="overflow_hide" style="width: 434px;"><a href="javascript:;" class="btlink source_file" data-filename="/www/server/panel/plugin/btwaf/Recycle/' +
								row.rname +
								'">' +
								row.dname +
								'</a></span>'
							);
						},
					},
					{
						fid: 'time',
						title: '隔离时间',
						width: 150,
						templet: function (row, index) {
							return '<span >' + bt.format_data(row.time) + '</span>';
						},
					},
					{
						title: '操作',
						type: 'group',
						align: 'right',
						width: 120,
						group: [
							{
								title: '恢复',
								event: function (row, index, ev, key, rthat) {
									var _html =
										'<div class="mt10"><input type="checkbox" id="fileRangeInsulate"/><label for="fileRangeInsulate" style="font-weight: 400;margin: 0 0 0 5px;cursor: pointer;">是否加入文件白名单？</label></div>';
									layer.confirm('从木马隔离箱中恢复[' + row['name'] + ']文件，是否继续？' + _html, { title: '恢复文件', closeBtn: 2, icon: 0 }, function () {
										var isCheck = $('#ipRangeInsulate').is(':checked');
										if (!isCheck) {
											that.ajaxTask('Re_Recycle_bin', { path: row['rname'] }, function (res) {
												layer.msg(res.msg, { icon: res.status ? 1 : 2 });
												if (res.status) rthat.$refresh_table_list(true);
											});
										} else {
											var loadT = bt.load('正在加入文件白名单，请稍候...');
											$.post('/plugin?action=a&name=btwaf&s=wubao_webshell', { path: row.rname }, function (res) {
												loadT.close();
												if (res.status) rthat.$refresh_table_list(true);
												layer.msg(res.msg, { icon: res.status ? 1 : 2 });
											});
										}
									});
								},
							},
							{
								title: '永久删除',
								event: function (row, index, ev, key, rthat) {
									layer.confirm('永久删除[' + row['name'] + ']文件后将无法恢复，是否继续？', { title: '删除文件', closeBtn: 2, icon: 0 }, function () {
										that.ajaxTask('Del_Recycle_bin', { path: row['rname'] }, function (res) {
											layer.msg(res.msg, { icon: res.status ? 1 : 2 });
											if (res.status) rthat.$refresh_table_list(true);
										});
									});
								},
							},
						],
					},
				],
				data: res,
				done: function (rdata) {
					$('#webshell_list_table td a.source_file').click(function () {
						var fileName = $(this).data('filename');
						bt.pub.on_edit_file(0, fileName);
					});
					if ($('#webshell_list_table td').length)
						if ($('#webshell_list_table td').eq(0).attr('colspan') !== 'undefined' && $('#webshell_list_table td').eq(0).attr('colspan'))
							$('#webshell_list_table td').eq(0).css('text-align', 'center');
				},
			});
		});
	},
	/**
	 * @description 渲染webshell规则
	 */
	render_webshell_rule: function (callback) {
		var that = this;
		that.ajaxTask('shell_get_rule', function (res) {
			that.refresh_table_view({
				el: '#webshell_rule_table',
				form_id: 'webshell_rule_table', //用于重置
				height: 700,
				config: [
					{
						fid: '1',
						title: '规则',
						templet: function (row, index) {
							return '<div class="" style="width:600px;word-break:break-all;line-height: 20px;">' + row + '</div>';
						},
					},
					{
						fid: '0',
						title: '操作',
						width: '50px',
						style: 'text-align: right;',
						group: [
							{
								title: '删除',
								event: function (row, index) {
									layer.confirm('是否删除该规则【 ' + row + ' 】，是否继续？', { title: '提示', btn: ['确定', '取消'], icon: 0, closeBtn: 2 }, function () {
										that.ajaxTask('shell_del_rule', { rule: row }, function (res) {
											if (res.status) that.refresh_data_webshell('rule_list');
											layer.msg(res.msg, { icon: res.status ? 1 : 2 });
										});
									});
								},
							},
						],
					},
				],
				data: res,
				done: function (res) {
					if (callback) callback(res);
				},
			});
		});
	},
	/**木马查杀方法结束 */

	/**
	 * @description 地区限制
	 */
	render_regional_restrictions: function () {
		var that = this;
		bt_tools.table({
			el: '#regional_restrictions',
			load: true,
			height: '500',
			default: '当前数据为空',
			url: '/plugin?action=a&name=btwaf&s=get_reg_tions',
			column: [
				{
					title: '地区',
					width: '300px',
					template: function (row, index) {
						var str = that.keyValues(row.region);
						return '<span class="overflow_hide" style="width: 284px;" title="' + str + '">' + str + '</span>';
					},
				},
				{
					title: '站点',
					width: '300px',
					template: function (row) {
						var str = that.keyValues(row.site);
						return '<span class="overflow_hide" style="width: 284px;" title="' + str + '">' + str + '</span>';
					},
				},
				{
					title: '类型',
					width: '90px',
					template: function (row) {
						return '<span>' + (row.types === 'refuse' ? '拦截' : '只放行') + '</span>';
					},
				},
				{
					title: '操作',
					type: 'group',
					width: '50px',
					align: 'right',
					group: [
						{
							title: '删除',
							event: function (row, index) {
								var site = [],
									region = [];
								$.each(row.site, function (index, item) {
									site.push(index);
								});
								$.each(row.region, function (index, item) {
									region.push(index);
								});
								that.ajaxTask('del_reg_tions', { site: site.toString(), types: row.types, region: region.toString() }, function (res) {
									if (res.status) that.render_regional_restrictions();
									layer.msg(res.msg, { icon: res.status ? 1 : 2 });
								});
							},
						},
					],
				},
			],
			tootls: false,
		});
	},
	/**
	 * @description 添加地区限制
	 */
	set_add_reg_tions_view: function () {
		var that = this,
			site_length = 0;
		layer.open({
			type: 1,
			title: '添加地区限制',
			area: '450px',
			closeBtn: 2,
			btn: ['添加', '取消'],
			skin: 'add-address',
			content: '<div class="waf-form pd20"></div>',
			success: function (layers, indexs) {
				addUrlRequest = bt_tools.form({
					el: '.waf-form',
					form: [
						{
							label: '类型',
							group: {
								name: 'types',
								width: '200px',
								type: 'select',
								list: [
									{ title: '拦截', value: 'refuse' },
									{ title: '只放行', value: 'accept' },
								],
							},
						},
					],
				});
				var robj = $('.bt-form'),
					reg_html = '',
					site_html = '',
					elName = ['multi_reg', 'multi_site'];
				$.post('/plugin?action=a&name=btwaf&s=city', function (res) {
					for (var i = 0; i < res.length; i++) {
						reg_html += '<li><a><span class="text">' + res[i] + '</span><span class="glyphicon check-mark"></span></a></li>';
					}
					robj.append('<div class="line" style="height: 45px;"><span class="tname">地区</span><div class="info-r ml0">' + that.multi_select_view(elName[0], reg_html) + '</div></div>');
					that.nulti_event(elName[0], res, '地区');
				});
				$.post('/plugin?action=a&name=btwaf&s=reg_domains', function (res) {
					var data = [];
					for (var i = 0; i < res.length; i++) {
						data.push(res[i].name);
						site_html += '<li><a><span class="text">' + res[i].name + '</span><span class="glyphicon check-mark"></span></a></li>';
					}
					site_length = data.length;
					robj.append('<div class="line" style="height: 45px;"><span class="tname">站点</span><div class="info-r ml0">' + that.multi_select_view(elName[1], site_html) + '</div></div>');
					that.nulti_event(elName[1], data, '站点');
				});
			},
			yes: function (indexs) {
				var formData = addUrlRequest.$get_form_value();
				var region = $('.multi_reg .btn .filter-option')
					.text()
					.replace('中国大陆以外的地区(包括[中国特别行政区:港,澳,台])', '海外')
					.replace('中国大陆(不包括[中国特别行政区:港,澳,台])', '中国')
					.replace('中国香港', '香港')
					.replace('中国澳门', '澳门')
					.replace('中国台湾', '台湾');
				var site_text = $('.multi_site .btn .filter-option').text(),
					site = '';
				if (site_length === site.split(',').length) {
					site = 'allsite';
				} else {
					site = site_text;
				}
				if (region.indexOf('请选择') > -1) return layer.msg('地区最少选一个!', { icon: 2 });
				if (site.indexOf('请选择') > -1) return layer.msg('站点最少选一个!', { icon: 2 });
				that.ajaxTask(
					'add_reg_tions',
					{
						region: region,
						types: formData.types,
						site: site,
					},
					function (res) {
						if (res.status) {
							layer.close(indexs);
							that.render_regional_restrictions();
						}
						layer.msg(res.msg, { icon: res.status ? 1 : 2 });
					}
				);
			},
		});
	},
	keyValues: function (obj) {
		var str = [];
		$.each(obj, function (index, item) {
			if (item == 1) {
				if (index == 'allsite') index = '所有站点';
				if (index == '海外') index = '中国大陆以外的地区(包括[港,澳,台])';
				if (index == '中国') index = '中国大陆(不包括[港,澳,台])';
				str.push(index);
			}
		});
		return str.toString();
	},
	//多选事件
	nulti_event: function (el, data, title) {
		var nameList = [];
		var show_domain_name = function () {
			var text = '';
			if (nameList.length > 0) {
				text = [];
				for (var i = 0; i < nameList.length; i++) {
					text.push(nameList[i]);
				}
				text = text.join(', ');
			} else {
				text = '请选择' + title + '...';
			}
			$('.' + el + ' .btn .filter-option').text(text);
			$('.' + el + ' .btn .filter-option').prop('title', text);
		};
		show_domain_name();
		$('.' + el + ' .btn').click(function (e) {
			$('.' + (el === 'multi_reg' ? 'multi_site' : 'multi_reg')).removeClass('open');
			var $parent = $(this).parent();
			$parent.toggleClass('open');
			$(document).one('click', function () {
				$parent.removeClass('open');
			});
			e.stopPropagation();
		});
		// 单选
		$('.' + el + ' .dropdown-menu li').click(function (e) {
			var $this = $(this);
			var index = $this.index();
			var name = data[index];
			$this.toggleClass('selected');
			$this.find('.glyphicon').toggleClass('glyphicon-ok');
			if ($this.hasClass('selected')) {
				nameList.push(name);
			} else {
				var remove_index = -1;
				for (var i = 0; i < nameList.length; i++) {
					if (nameList[i] == name) {
						remove_index = i;
						break;
					}
				}
				if (remove_index != -1) {
					nameList.splice(remove_index, 1);
				}
			}
			show_domain_name();
			e.stopPropagation();
		});
		// 全选
		$('.' + el + ' .bs-select-all').click(function () {
			nameList = [];
			for (var i = 0; i < data.length; i++) {
				nameList.push(data[i]);
			}
			$('.' + el + ' .dropdown-menu li').addClass('selected');
			$('.' + el + ' .dropdown-menu li .glyphicon').addClass('glyphicon-ok');
			show_domain_name();
		});
		// 取消全选
		$('.' + el + ' .bs-deselect-all').click(function () {
			nameList = [];
			$('.' + el + ' .dropdown-menu li').removeClass('selected');
			$('.' + el + ' .dropdown-menu li .glyphicon').removeClass('glyphicon-ok');
			show_domain_name();
		});
		$('.' + el + ' .bs-close').click(function () {
			$('.' + el).removeClass('open');
		});
	},
	//多选视图
	multi_select_view: function (el, html) {
		return (
			'<div class="btn-group bootstrap-select show-tick mr5 ' +
			el +
			'" style="float: left">\
			<button type="button" class="btn dropdown-toggle btn-default" style="height: 32px; line-height: 18px; font-size: 12px">\
				<span class="filter-option pull-left"></span>\
				<span class="bs-caret"><span class="caret"></span></span>\
			</button>\
			<div class="dropdown-menu open">\
				<div class="bs-actionsbox">\
					<div class="btn-group btn-group-sm btn-block">\
						<button type="button" class="actions-btn bs-select-all btn btn-default">全选</button>\
						<button type="button" class="actions-btn bs-deselect-all btn btn-default">取消全选</button>\
					</div>\
				</div>\
				<div class="dropdown-menu inner">' +
			html +
			'</div>\
				<div class="btn-group-bottom"><button type="button" class="actions-btn bs-close btn btn-success">确定</button></div>\
			</div>\
		</div>'
		);
	},
	/**封锁历史方法开始 */
	/**
	 * @description 渲染封锁历史列表
	 * @param {Object} obj 数据
	 */
	render_history_data: function (obj, callback) {
		var that = this;
		$('#history_table').empty();
		var _history = bt_waf_tools.table({
			el: '#history_table',
			url: obj ? obj.url : '/plugin?action=a&name=btwaf&s=get_safe_logs_sql',
			param: obj ? obj.param : {},
			height: 700,
			load: true,
			class: 'waf_table',
			default: '没有封锁记录', //数据为空时的默认提示
			column: [
				{ fid: 'id', type: 'checkbox', class: '', width: 20 },
				{
					fid: 'time',
					type: 'text',
					width: 150,
					title: '开始时间',
					template: function (row) {
						return '<span title="' + bt.format_data(row.time) + '" class="overflow_hide" style="width: 150px;">' + bt.format_data(row.time) + '</span>';
					},
				},
				{
					fid: 'ip',
					type: 'text',
					width: 150,
					title: 'IP',
					template: function (row, index) {
						return '<span>' + that.escapeHTML(row.ip) + '</span>';
					},
				},
				{
					fid: 'server_name',
					type: 'text',
					width: 150,
					title: '站点',
					template: function (row, index) {
						return '<span>' + that.escapeHTML(row.server_name) + '</span>';
					},
				},
				{
					fid: 'blockade',
					type: 'text',
					width: 120,
					title: '封锁原因',
					template: function (row, index) {
						if (row.blockade === 'upload') {
							return '恶意文件上传';
						}
						if (row.blockade === 'xss') {
							return '<span>xss拦截</span>';
						}
						if (row.blockade === 'sql') {
							return '<span>sql注入拦截</span>';
						}
						if (row.blockade === 'scan') {
							return '<span>扫描器拦截</span>';
						}
						if (row.blockade === 'user_agent') {
							return '<span>恶意爬虫拦截</span>';
						}
						if (row.blockade === 'inc') {
							return '多次恶意请求';
						}
						return row.blockade === 'cc' ? 'CC攻击' : '多次恶意请求';
					},
				},
				{
					fid: 'blocking_time',
					width: 120,
					type: 'text',
					title: '封锁时长',
					template: function (row, index) {
						return row.blocking_time + '秒';
					},
				},
				{
					fid: 'is_feng',
					width: 110,
					type: 'text',
					title: '状态',
					template: function (row, index) {
						return row.is_feng == 1 ? '<span style="color:red">封锁中</span>' : '已解封';
					},
				},
				{
					fid: 'ip_country',
					type: 'text',
					title: 'IP归属地',
					width: 130,
					template: function (row, index) {
						if (row.ip_country == '内网地址') return '<span title="' + row.ip_country + '">' + row.ip_country + '</span>';
						return '<span title="' + that.render_ip_country(row) + '">' + that.render_ip_country(row) + '</span>';
					},
				},
				{
					title: '操作',
					type: 'group',
					align: 'right',
					width: '400px',
					group: [
						{
							title: 'URL加白',
							event: function (row, index) {
								if (row.uri == '/') return layer.msg('当前ip的uri为根目录,无法执行误报操作！');
								layer.confirm('加入URL白名单后此URL将不再进行防御，是否继续操作？', { title: '加入URL白名单', icon: 3, closeBtn: 2 }, function () {
									// that.ajaxTask('wubao_url_white',{url_rule:row.uri,error_log:row.ip+' >> '+row.incoming_value,http_log: row.http_log},function(res){
									// 	layer.msg(res.msg, {icon:res.status?1:2});
									if (row.http_log_path === 1) {
										$.post('/btwaf/get_logs', { path: row.http_log }, function (res) {
											that.ajaxTask('wubao_url_white', { url_rule: row.uri, error_log: row.ip + ' >> ' + row.incoming_value, http_log: res }, function (res) {
												layer.msg(res.msg, { icon: res.status ? 1 : 2 });
											});
										});
									} else {
										that.ajaxTask('wubao_url_white', { url_rule: row.uri, error_log: row.ip + ' >> ' + row.incoming_value, http_log: row.http_log }, function (res) {
											layer.msg(res.msg, { icon: res.status ? 1 : 2 });
										});
									}
								});
							},
						},
						{
							title: '拉黑IP',
							event: function (row, index) {
								var ipv4Range = '';
								if (bt.check_ip(row.ip)) {
									ipv4Range =
										'<div class="mt10"><input type="checkbox" id="ipRangeInsulate"/><label for="ipRangeInsulate" style="font-weight: 400;margin: 0 0 0 5px;cursor: pointer;">是否拉黑整个IP段？</label></div>';
								}
								layer.confirm('是否将 <span style="color:red">' + row.ip + '</span> 添加到IP黑名单？' + ipv4Range, { title: '加入IP黑名单', closeBtn: 2 }, function () {
									if (bt.check_ip(row.ip)) {
										var isCheck = $('#ipRangeInsulate').is(':checked');
										if (!isCheck) {
											that.ajaxTask('add_ip_black', { start_ip: row.ip, end_ip: row.ip }, function (res) {
												layer.msg(res.msg, { icon: res.status ? 1 : 2 });
											});
										} else {
											var ipRange = row.ip.replace(/\d{1,3}$/, '0/24');
											bt_waf.http({
												method: 'import_data',
												data: { s_Name: 'ip_black', pdata: ipRange },
												success: function (res) {
													layer.msg(res.status ? '操作成功' : '添加失败', { icon: res.status ? 1 : 2 });
												},
											});
										}
									} else {
										that.ajaxTask('set_ipv6_back', { addr: row.ip }, function (res) {
											layer.msg(res.msg, { icon: res.status ? 1 : 2 });
										});
									}
								});
							},
						},
						{
							title: '解封IP',
							event: function (row, index) {
								if (row.is_feng) {
									layer.confirm('是否要从防火墙解封IP【' + row.ip + '】', { title: '解封IP地址', closeBtn: 2, icon: 0 }, function () {
										that.ajaxTask('remove_waf_drop_ip', { ip: row.ip }, function (res) {
											if (res.status) that.render_history_data();
											layer.msg(res.msg, { icon: res.status ? 1 : 2 });
										});
									});
								} else {
									layer.msg('IP已解封', { icon: 1 });
								}
							},
						},
						{
							title: '详情',
							event: function (row, index) {
								that.create_details(row);
							},
						},
						{
							title: 'HTTP',
							event: function (row, index) {
								that.create_HTTP(row);
							},
						},
					],
				},
			],
			success: function (data) {
				// 解封所有封锁
				$('.uncover_ip').click(function () {
					var _ip = $(this).attr('data-ip');
					layer.confirm('是否要从防火墙解封IP【' + _ip + '】', { title: '解封IP地址', closeBtn: 2, icon: 0 }, function () {
						that.ajaxTask('remove_waf_drop_ip', { ip: _ip }, function (res) {
							if (res.status) that.render_history_data();
							layer.msg(res.msg, { icon: res.status ? 1 : 2 });
						});
					});
				});
				if (callback) callback(res);
			},
			// 渲染完成
			tootls: [
				// { // 批量操作
				//     type: 'batch',//batch_btn
				//     positon: ['left', 'bottom'],
				//     config: {
				//         title: "误报",
				//         url: '/plugin?action=a&name=btwaf&s=wubao_url_white',
				//         load: true,
				//         param: function (row) {
				//             return { url_rule:row.uri };
				//         },
				//         callback: function (that) {
				//             var flag = false;
				//             $.each(that.check_list,function(index,item){
				//                 if(item.uri == '/'){
				//                     layer.msg('当前选中的第'+(index+1)+'条数据uri为根目录,无法执行批量误报操作！')
				//                     flag = true;
				//                     return false;
				//                 }
				//             })
				//             if(!flag){
				//                 bt.show_confirm('批量删除误报', '<span style="color:red">是否执行批量误报反馈</br></span>', function (index) {
				//                     layer.close(index);
				//                     that.start_batch({}, function (list) {
				//                         var html = '';
				//                         for (var i = 0; i < list.length; i++) {
				//                             var item = list[i];
				//                             html += '<tr><td>' + item.ip + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + item.request.msg + '</span></div></td></tr>';
				//                             if(item.request.status){
				//                                 var rule_arry = item.incoming_value.indexOf('b"')>-1?item.incoming_value.substring(2,item.incoming_value.length-1).split(" >> "):item.incoming_value.split(" >> ");
				//                                 if (rule_arry[1] != undefined) { $.get('https://www.bt.cn/Api/add_waf_logs?data=' + rule_arry[1], function (rdata) { }, 'jsonp') }
				//                             }
				//                         }
				//                         _history.$batch_success_table({ title: '批量误报', th: 'IP', html: html });
				//                         _history.$refresh_table_list(true);
				//                     });
				//                 });
				//             }
				//         }
				//     }
				// },
				{
					//分页显示
					type: 'page',
					positon: ['right', 'bottom'], // 默认在右下角
					pageParam: 'p', //分页请求字段,默认为 : p
					page: 1, //当前分页 默认：1
					numberParam: 'limit', //分页数量请求字段默认为 : limit
					number: 10, //分页数量默认 : 20条
					numberList: [10, 20, 50, 100, 200], // 分页显示数量列表
					numberStatus: true, //　是否支持分页数量选择,默认禁用
					jump: true, //是否支持跳转分页,默认禁用
				},
			],
		});
		function btwaf_batch(name, tips, that) {
			bt.show_confirm(name, tips, function (index) {
				layer.close(index);
				that.start_batch({}, function (list) {
					var html = '';
					for (var i = 0; i < list.length; i++) {
						var item = list[i];
						html += '<tr><td>' + (item.ip.length >= 15 ? item.ip.substring(0, 15) + '...' : item.ip) + '</td><td><div style="float:right;"><span style="color:#20a53a">操作成功</span></div></td></tr>';
					}
					_history.$batch_success_table({ title: '批量执行任务', th: '任务名称', html: html });
					_history.$refresh_table_list(true);
				});
			});
		}
	},
	/**
	 * @description 导出封is_import锁列表数据
	 */
	export_block_view: function () {
		var that = this;
		this.ajaxTask('import_ip_data', function (data) {
			layer.open({
				type: 1,
				title: '导出封锁中IP列表',
				area: ['400px', '390px'],
				closeBtn: 2,
				shadeClose: false,
				btn: ['导出文件', '取消'],
				content:
					'<div class="pd20"><textarea rows="15" style="padding:5px 10px;width:100%;height:253px;border-radius:2px;border:1px solid #ccc;" name="ip_block_list">' +
					data.join('\n') +
					'</textarea></div>',
				yes: function (layero, index) {
					that.render_download_link(data, '封锁中IP列表.json');
				},
			});
		});
	},
	/**封锁历史方法结束 */

	/**
	 * @description 渲染表格视图
	 * @param {Object} obj 提供ID,配置项
	 */
	refresh_table_view: function (obj) {
		var _thead = '<thead><tr>',
			_tbody = '',
			_config = obj.config,
			_data = obj.data,
			_event = {},
			that = this;
		$(obj.el)
			.css({ height: this.is_defined(typeof obj.height, obj.height, 'auto') })
			.addClass(this.is_defined(typeof obj.height, 'fixed-table-view'));
		this.waf_table_list[obj.form_id] = obj;
		this.waf_table_list[obj.form_id]['reset'] = function () {
			that.refresh_table_view(obj);
		};
		for (var i = 0; i < _config.length; i++) {
			_thead +=
				'<th ' +
				this.is_data_type({ name: 'width', data: _config[i] }) +
				this.is_data_type({ name: 'align', data: _config[i] }) +
				this.is_data_type({ name: 'style', data: _config[i] }) +
				'>' +
				_config[i].title +
				'</th>';
			if (_config[i]['event']) {
				_event[obj.form_id + '_' + _config[i].fid] = {
					name: obj.form_id + '_' + _config[i].fid,
					event: _config[i]['events'] !== undefined ? _config[i]['events'] : 'click',
					method: _config[i]['event'],
				};
			}
		}
		_thead += '</tr></thead>';
		_tbody += '<tbody>';
		if (obj.inverted) _data.reverse();
		for (var z = 0; z < _data.length; z++) {
			_tbody += '<tr data-index="' + z + '">';
			for (var j = 0; j < _config.length; j++) {
				var templet = '',
					_text = '';
				_tbody += '<td ' + this.is_data_type({ name: 'style', data: _config[j] }) + ' ' + this.is_data_type({ name: 'class', data: _config[j] }) + '>';
				if (_config[j].templet !== undefined && _config[j].event === undefined) {
					_text = _config[j].templet(_data[z], z);
					_tbody += _text;
				} else if (_config[j].group !== undefined) {
					var _arry = [];
					if (typeof _config[j].group === 'function') {
						_arry = _config[j].group(_data[z], z);
					} else {
						_arry = _config[j].group;
					}
					_tbody += '<span>';
					for (var y = 0; y < _arry.length; y++) {
						_tbody +=
							'<a class="btlink" ' +
							this.is_defined(typeof _arry[y]['event'], 'data-event="' + obj.form_id + '_' + _config[j].fid + '_' + y + '"') +
							this.is_data_type({ name: 'href', data: _config[y] }) +
							this.is_data_type({ name: 'class', data: _config[y] }) +
							this.is_data_type({ name: 'target', data: _config[y] }) +
							'>' +
							(_arry[y].templet == undefined ? _arry[y].title : _arry[y].templet(_arry[y], y)) +
							'</a>';
						if (y + 1 !== _arry.length) _tbody += '&nbsp;|&nbsp;';
						if (_arry[y]['event'] && !_event[obj.form_id + '_' + _config[j].fid + '_' + y]) {
							_event[obj.form_id + '_' + _config[j].fid + '_' + y] = {
								name: obj.form_id + '_' + _config[j].fid + '_' + y,
								event: _arry[y]['events'] !== undefined ? _arry[y]['events'] : 'click',
								method: _arry[y]['event'],
							};
						}
					}
					_tbody += '</span>';
				} else {
					_text = _data[z][_config[j].fid];
					if (_text !== '' && typeof _text !== 'undefined') {
						_tbody += '<span style="width: auto;" title="' + this.is_defined(typeof _config[j].tips, _text) + '">';
						switch (_config[j].type) {
							case 'text':
								_tbody += '<span ' + this.is_defined(typeof _config[j].event, 'data-event="' + obj.form_id + '_' + _config[j].fid + '"') + '>' + _text + '</span>';
								break;
							case 'link':
								_tbody +=
									'<a class="btlink" ' +
									this.is_defined(typeof _config[j].event, 'data-event="' + obj.form_id + '_' + _config[j].fid + '"') +
									this.is_data_type({ name: 'href', data: _config[j], val: _config[j]['href'] ? _text : false }) +
									this.is_data_type({ name: 'class', data: _config[j] }) +
									this.is_data_type({ name: 'target', data: _config[j] }) +
									'>' +
									(_config[j].templet == undefined ? _text : _config[j].templet(_data[z], z)) +
									'</a>';
								break;
							case 'checkbox':
								_tbody +=
									'<input type="checkbox" class="waf_td_checkbox" ' +
									(_data[z][_config[j].fid] ? 'checked' : '') +
									' ' +
									this.is_defined(typeof _config[j].event, 'data-event="' + obj.form_id + '_' + _config[j].fid + '"') +
									' />';
								break;
							case 'btswitch':
								_tbody +=
									'<input class="btswitch btswitch-ios" id="close_' +
									_config[j].fid +
									'_' +
									obj.form_id +
									'_' +
									z +
									'" ' +
									(_data[z][_config[j].fid] ? 'checked' : '') +
									' type="checkbox">' +
									'<label class="btswitch-btn" for="close_' +
									_config[j].fid +
									'_' +
									obj.form_id +
									'_' +
									z +
									'" ' +
									this.is_defined(typeof _config[j].event, 'data-event="' + obj.form_id + '_' + _config[j].fid + '"') +
									'></label>';
								break;
							case 'unselect':
								_tips = _config[j].tips ? _config[j].tips(_data[z]) : '';
								_open = typeof _data[z][_config[j].fid] == 'object' ? _data[z][_config[j].fid][_config[j].is_contain] : _data[z][_config[j].fid];
								_tbody +=
									'<span class="waf_unselect" ' +
									this.is_defined(typeof _config[j].event, 'data-event="' + obj.form_id + '_' + _config[j].fid + '"') +
									'><i class="waf-icon waf-icon-ok ' +
									(_open ? 'waf-checked' : '') +
									'"><span class="glyphicon glyphicon-ok" aria-hidden="true"></span></i><input type="checkbox" ' +
									(_open ? 'checked' : '') +
									'></span>' +
									(_tips === '' ? '' : '<span class="tipsval ' + (_tips > 0 ? 'grade_1' : '') + '" title="拦截次数:' + _tips + '">' + _tips + '</span>');
								break;
							default:
								_tbody += '<span ' + this.is_defined(typeof _config[j].event, 'data-event="' + obj.form_id + '_' + _config[j].fid + '"') + '>' + _text + '</span>';
								break;
						}
						_tbody += '</span>';
					} else {
						_tbody += '<span>--</span>';
					}
				}
				_tbody += '</td>';
			}
			_tbody += '</tr>';
		}
		if (_data.length === 0) {
			_tbody += '<tr><td colspan="' + _config.length + '" align="center">' + this.is_defined(typeof obj.tips, obj.tips, '当前数据为空') + '</td></tr>';
		}
		_tbody += '</tbody>';
		$(obj.el).html('<table class="' + this.is_defined(typeof obj.class, obj.class, 'waf_table  bt_table table table-hover') + '">' + _thead + _tbody + '</table>');
		if (obj.page) {
			if ($(obj.el).next().length == 0) {
				$(obj.el).after('<div class="waf_page">' + obj.page + '</div>');
			} else {
				$(obj.el).next().html(obj.page);
			}
		}
		this.bind_evnet_group(obj, _event);
		setTimeout(function () {
			obj.done && obj.done(obj.data, obj);
		}, 100);
		if (obj.height !== undefined) {
			$(obj.el + ' table').before('<table class="' + that.is_defined(typeof obj.class, obj.class, 'waf_table table bt_table ng-table table-hover fixed-table-thead') + '">' + _thead + '</table>');
			$(obj.el + ' .fixed-table-thead')
				.next()
				.addClass('fixed-table');
			$(obj.el + ' .fixed-table thead th').each(function (index, el) {
				var _offsetWidth = $(this)[0].offsetWidth - 20;
				$(obj.el + ' .fixed-table-thead thead th')
					.eq(index)
					.html(
						$(obj.el + ' thead th')
							.eq(index)
							.text() +
							'<div class="waf-fht-cell" style="width:' +
							_offsetWidth +
							'px">'
					);
			});
			if ($(obj.el + ' .fixed-table')[0].offsetHeight > parseFloat(obj.height)) {
				$(obj.el + ' .fixed-table-thead').addClass('fixed-table-shadow');
			}
			$(obj.el + ' .fixed-table-thead').css('top', $(obj.el).scrollTop());
			$(obj.el).scroll(function () {
				$(obj.el + ' .fixed-table-thead').css('top', $(this).scrollTop());
			});
		}
	},
	// 判断格式
	is_defined: function (is_val, num1, num2) {
		return is_val !== 'undefined' ? (num1 === undefined ? is_val : num1) : num2 === undefined ? '' : num2;
	},
	/**
	 * @description 判断数据类型 (仅用于表单渲染类型绑定)
	 * @param {string} obj 数据类型、数据
	 */
	is_data_type: function (obj) {
		if (obj.data === undefined) return 'href="javascript:;"';
		if (obj.data[obj.name] !== undefined) return obj.name + '="' + obj.data[obj.name] + '"';
		if (obj.name == 'href') {
			if (!obj.val) {
				return 'href="javascript:;" ';
			} else {
				return 'href="' + obj.val + '" ';
			}
		}
		return '';
	},
	/**
	 * @description 创建固定表头 (仅用于表单渲染类型绑定)
	 * @param {string} obj 数据类型、数据
	 */
	create_table_thead: function (obj) {
		// if(!obj) return true;
		var th = '';
		$.each(obj.list, function (index, item) {
			th += '<th ' + item[1] + '>' + item[0] + '</th>';
		});
		$(obj.el).html(
			'<table class="table table-hover fixed-table-shadow">\
				<thead>\
					<tr>' +
				th +
				'</tr>\
				</thead>\
			</table>'
		);
	},
	/**
	 * @description 绑定事件组 (仅用于表单渲染事件绑定)
	 * @param {string} obj 全部数据
	 * @param {string} events 调用的事件
	 */
	bind_evnet_group: function (obj, events) {
		for (var i in events) {
			(function (i) {
				$(obj.el + ' [data-event=' + events[i].name + ']').bind(events[i].event, function (e) {
					var _index = parseInt($(this).parent().parent().parent().attr('data-index')),
						_data = obj.data[_index];
					events[i].method(_data, _index, e, $(this));
				});
			})(i);
		}
	},
	getToday: function () {
		var mydate = new Date();
		var str = '' + mydate.getFullYear() + '-';
		str += mydate.getMonth() + 1 + '-';
		str += mydate.getDate();
		return str;
	},
	getBeforeDate: function (interval) {
		var date = new Date(),
			_year = date.getFullYear(),
			_month = date.getMonth() + 1,
			_day = date.getDate();

		var resultData = [];
		getDataList(_year, _month, _day);
		function mGetDate(year, month) {
			var d = new Date(year, month, 0);
			return d.getDate();
		}
		function getDataList(year, month, day) {
			if (day > 0) {
				for (var i = day; i > 0; i--) {
					var formatData = year + '-' + month + '-' + i;
					resultData.push(formatData);
					if (i == 1 && resultData.length < interval) {
						_length = month - 1 == 0 ? mGetDate(year - 1, 12) : mGetDate(year, month - 1);
						month - 1 == 0 ? getDataList(year - 1, 12, _length) : getDataList(year, month - 1, _length);
					}
					if (resultData.length == interval) {
						break;
					}
				}
			}
		}
		return resultData;
	},
	// 添加千位分界符
	addThousands: function (num) {
		var reg = /\d{1,3}(?=(\d{3})+$)/g;
		if (num && num.toString().indexOf('.') == -1) {
			return (num + '').replace(reg, '$&,');
		} else {
			return num.toString().replace(/(\d)(?=(\d{3})+\.)/g, function ($0, $1) {
				return $1 + ',';
			});
		}
	},
	// 规则转码
	escapeHTML: function (val) {
		val = '' + val;
		return val
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"/g, '&quot;')
			.replace(/'/g, '‘')
			.replace(/\(/g, '&#40;')
			.replace(/\&#60;/g, '&lt;')
			.replace(/\&#62;/g, '&gt;')
			.replace(/`/g, '&#96;')
			.replace(/=/g, '＝');
	},
	/**
	 * @descripttion 选项框多选搜索
	 * @param {Object} config.el                    选项框的元素/id（带#符号）
	 * @param {Object} config.url                   数据请求
	 * @param {Object} config.loading               请求时的提示语
	 * @param {Object} config.param                 请求所需参数
	 * @param {Object} config.dataFilter            请求数据处理（过滤成模板类型数据）
	 * @param {Object} config.config.width          选项框宽度
	 * @param {Object} config.config.name           选项框搜索的name值
	 * @param {Object} config.config.placeholder    选项框提示的文字
	 * @param {Object} config.config.ischeck        选项框是否多选
	 * @param {Object} config.config.issearch       选项框是否可搜索
	 * @param {Object} config.data                  选项框所能选择的数据
	 * @return {Function} callback
	 */
	select: function (config) {
		function RenderSelect(config) {
			this.config = config;
			this.init();
		}
		RenderSelect.prototype = {
			_event: [], //选中的数据
			inputShowText: '', //input位置显示的文本内容
			manyCheckArray: [], //多选时临时存放的数据（用于拼接数据
			init: function () {
				var that = this,
					_Obj = this.config;
				// 数据类型判断
				if (_Obj.method != undefined) {
					this.request_data_list();
				} else if (_Obj.data != undefined) {
					this.create_select_list();
				} else {
					return layer.msg('缺少method或data参数', { icon: 2 });
				}

				// 监听选项框 文档事件
				$(_Obj.el).on('click', function (e) {
					$(document).one('click', function (ev) {
						ev.stopPropagation();
						$(_Obj.el + ' .select-picker-search').removeClass('Select-moseDown');
						$(_Obj.el + ' .select-list-item').hide();
					});
					e.stopPropagation();
				});
				// 显示/隐藏下拉列表
				$(_Obj.el).on('click', '.select-picker-search', function (e) {
					if (!$(this).hasClass('Select-moseDown')) {
						$(this).addClass('Select-moseDown');
						$(_Obj.el + ' .select-list-item').show();
						$('input[name=query_list]').focus();
					} else {
						$(this).removeClass('Select-moseDown');
						$(_Obj.el + ' .select-list-item').hide();
					}
				});
				// 列表点击时
				$(_Obj.el).on('click', '.select-list-item li', function (ev) {
					var check_all = $('.checkAll'),
						_attr = $(this).data('attr'),
						_index = $(this).data('index');
					switch (_attr) {
						case 'all':
							if (!$(this).hasClass('active')) {
								$(this).addClass('active').siblings().addClass('active');
								that._event = $.extend(true, [], _Obj.data); //深拷贝数组否则影响原有数据
							} else {
								$(this).removeClass('active').siblings().removeClass('active');
								that._event = [];
							}
							break;
						default:
							if (!$(this).hasClass('active')) {
								_Obj.config.ischeck ? $(this).addClass('active') : $(this).addClass('active').siblings().removeClass('active');
								_Obj.config.ischeck ? that._event.push(_Obj.data[_index]) : (that._event = _Obj.data[_index]);
							} else {
								if (_Obj.config.ischeck) {
									$(this).removeClass('active');
									for (var i = 0; i < that._event.length; i++) {
										if (that._event[i][0] === _attr) that._event.splice(i, 1);
									}
								}
							}
							// 选择的数量等于原有数据时自动全选
							if (that._event.length == _Obj.data.length) {
								check_all.addClass('active');
							} else {
								check_all.removeClass('active');
							}
							break;
					}
					if (_Obj.config.ischeck) {
						//判断是否多选
						// 判断选择数量
						if (that._event.length < 1) {
							that.inputShowText = _Obj.config.placeholder;
						} else {
							that.manyCheckArray = [];
							$.each(that._event, function (k, showlist) {
								that.manyCheckArray.push(showlist[1]);
							});
							that.inputShowText = that.manyCheckArray.join(', ');
						}
					} else {
						// 单选时选中直接输入并关闭选择区
						that.inputShowText = _Obj.data[_index][1];
						$(_Obj.el + ' .select-picker-search').click();
					}
					// 输出内容
					$(_Obj.el + ' .picker-text-list')
						.attr('title', that.inputShowText)
						.html(that.inputShowText);
					_Obj.formatRepoSelection(that.manyCheckArray, that._event.length == _Obj.data.length);
					ev.stopPropagation();
					ev.preventDefault();
				});
				// 搜索功能
				$(_Obj.el).on('input', 'input[name=query_list]', function () {
					var _serach = $(this).val();
					if (_serach.trim() != '') {
						$('.select-list-item li').each(function () {
							var _span = $(this).find('span').html();
							if (_span.toLowerCase().indexOf(_serach.toLowerCase()) == -1) {
								$(this).hide();
							} else {
								$(this).show();
							}
						});
					} else {
						$('.select-list-item li').show();
					}
				});
			},
			/**
			 * @descripttion: 创建下拉列表
			 * @return: 无返回值
			 */
			create_select_list: function () {
				var _html = '',
					_li = '',
					obj = this.config,
					_config = this.config.config;
				_html +=
					'<div class="bt-select-full ' +
					(_config.ischeck ? 'many' : 'only-one') +
					'">' +
					'<div class="select-picker-search" style="width:' +
					_config.width +
					'px"><span class="picker-text-list" style="width:' +
					(_config.width - 35) +
					'px">' +
					_config.placeholder +
					'</span></div>' +
					'<span class="down-select-full"></span>' +
					'<div class="select-list-item">' +
					(_config.issearch ? '<input name="query_list" placeholder="字段模糊搜索" style="width:' + (_config.width - 20) + 'px">' : '') +
					'<ul>';

				// 多选时添加全部选中
				_config.ischeck ? (_li += '<li data-attr="all" class="checkAll"><div class="select-check-full"></div><span class="select-name-full">全部选中</span></li>') : '';
				$.each(obj.data, function (index, item) {
					_li +=
						'<li data-attr="' +
						item[0] +
						'" data-index="' +
						index +
						'">' +
						(_config.ischeck ? '<div class="select-check-full"></div>' : '') +
						'<span class="select-name-full">' +
						item[1] +
						'</span>' +
						'</li>';
				});
				_html += _li + '</ul></div></div>';
				$(obj.el).html(_html);
			},
			/**
			 * @descripttion: 请求API返回的数据
			 * @return: 无返回值
			 */
			request_data_list: function () {
				var that = this,
					obj = this.config;
				bt_waf.http({
					method: obj.method,
					data: obj.data,
					success: function (rdata) {
						if (obj.dataFilter) {
							obj.data = obj.dataFilter(rdata);
						} else {
							obj.data = rdata.data;
						}
						that.create_select_list();
					},
				});
			},
		};
		return new RenderSelect(config);
	},
	/**
	 * @description 渲染下载链接
	 * @param {String} content 下载内容
	 * @param {String} filename 文件名称
	 */
	render_download_link: function (content, filename) {
		// 创建隐藏的可下载链接
		var eleLink = document.createElement('a');
		eleLink.download = filename;
		eleLink.style.display = 'none';
		// 字符内容转变成blob地址
		var blob = new Blob([content]);
		eleLink.href = URL.createObjectURL(blob);
		// 触发点击
		document.body.appendChild(eleLink);
		eleLink.click();
		// 然后移除
		document.body.removeChild(eleLink);
	},
	/**
	 * @description 动态处理请求，设置全局ajaxList，api和提示语，遍历请求返回成功值
	 * @param {String} config 需要请求的api
	 * @param {Function} data 请求参数
	 * @param {Function} success 成功值
	 * @param {Function} error 失败值
	 */
	ajaxTask: function (config, data, success, error) {
		if (typeof config == 'string') {
			if (typeof data == 'object') {
				config = { method: config, data: data, success: success, error: error };
			} else if (typeof data == 'function') {
				config = { method: config, success: data };
				if (typeof success == 'function') {
					config.error = success;
				}
			}
		}
		if (config.middle === false) {
			config.success();
			return false;
		}
		this.http({
			tips: '正在' + this.ajaxList[config.method] + ',请稍候...',
			method: config.method,
			data: config.data || {},
			success: function (rdata) {
				if (config.success) config.success(rdata);
			},
			error: function (rdata) {
				if (config.error) config.error(rdata);
			},
		});
	},
	/**
	 * @description 请求方法封装
	 * @param {Object} 配置对象 例如 {tips:loading信息，false则关闭,data:参数,method:方法名称,success:成功函数,error:失败函数}
	 * @return void
	 */
	http: function (obj) {
		var loadT = '';
		if (obj.load == undefined) obj.load = 0;
		if (obj.url == undefined) {
			if (obj.plugin_name === undefined && this.plugin_name !== undefined) obj.plugin_name = this.plugin_name;
			if (!obj.plugin_name || !obj.method) {
				layer.msg('缺少插件方法', { icon: 2 });
				return false;
			}
		}
		if (obj.load === 0 || obj.tips != undefined) {
			loadT = layer.msg(obj.tips, { icon: 16, time: 0, shade: 0.1 });
		} else if (obj.load === 1 || (obj.tips == undefined && obj.load == undefined)) {
			loadT = layer.load();
		}
		$.ajax({
			type: 'POST',
			url: obj.url != undefined ? obj.url : '/plugin?action=a&name=' + obj.plugin_name + '&s=' + obj.method,
			// 		url:obj.url != undefined ? obj.url : ('json/' + obj.method +'.json'),
			data: obj.data || {},
			timeout: obj.timeout || 99999999,
			complete: function (res) {
				if (obj.tips !== false) layer.close(loadT);
			},
			success: function (rdata) {
				if (obj.check) {
					obj.success(rdata);
					return;
				}
				if (rdata.status === false) {
					if (obj.method !== 'get_nps') layer.msg(rdata.msg, { icon: 2 });
					return false;
				}
				obj.success(rdata);
			},
			error: function (ex) {
				if (!obj.error) {
					obj.msg || obj.msg == undefined ? layer.msg('The request process found an error!', { icon: 2 }) : '';
					return;
				}
				return obj.error(ex);
			},
		});
	},
};
bt_waf.init();
