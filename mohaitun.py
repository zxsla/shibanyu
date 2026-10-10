# -*- coding: utf-8 -*-
"""
摸海豚 · TVBox / 影视壳 Python 聚合站源（单文件，200 个子源）
数据来源：海豚影视 TVBox 配置（去广告/跑马灯清理版）
· 每个子源一个大分类，按分组排序：追剧 / 动漫 / 短剧 / 直播 / 听书 / 音乐 / 其他 / 采集
· 站内分类 + 地区筛选（大陆/香港/台湾/日本/韩国/欧美/泰国/印度/其他）
· 全站并发搜索，结果带
· 多 User-Agent 轮换；去除 TG/官网/关注/公告/跑马灯等广告条目和简介里的广告
· 播放：直链（m3u8/mp4…）直接播，网页地址交给壳解析；智能识别视频格式
· 封面直连，防盗链图床自动加 @Referer=，无图换默认封面
· 子源远程下载缓存 24 小时，加载失败 2 分钟后自动重试
"""
import os, re, sys, json, time, types, random, base64, hashlib, tempfile, threading
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, wait

sys.path.append('..')
from base.spider import Spider as BaseSpider

SEP = '@@'
AREAS = ['全部', '大陆', '香港', '台湾', '日本', '韩国', '欧美', '泰国', '印度', '其他']
# ---- 封面 ----
PIC_PROXY = False
DEFAULT_PIC = 'https://mpimg.cn/view.php/1dcb211cf3b75f932fb13c6fe98a80f7.jpeg'
PIC_REFERER = {
'doubanio.com': 'https://movie.douban.com/',
'douban.com': 'https://movie.douban.com/',
'hdslb.com': 'https://www.bilibili.com/',
'douyinpic.com': 'https://live.douyin.com/',
'byteimg.com': 'https://www.douyin.com/',
'qpic.cn': 'https://v.qq.com/',
'iqiyipic.com': 'https://www.iqiyi.com/',
'ykimg.com': 'https://www.youku.com/',
'xmcdn.com': 'https://www.ximalaya.com/',
'tuxiaobei.com': 'https://www.tuxiaobei.com/',
'sinaimg.cn': 'https://weibo.com/',
'alicdn.com': 'https://www.taobao.com/',
}
UAS = [
'okhttp/4.12.0',
'Mozilla/5.0 (Linux; Android 13; M2102J2SC) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
'Dalvik/2.1.0 (Linux; U; Android 12; SM-G9910 Build/SP1A.210812.016)',
]
# ---- 站点表：(key, 显示名, 分组, py地址/cms接口, 可搜索) ----
# 由海豚影视配置生成，已去重、去广告文案、按分组排序
SITES = [
    ('1234影视', '1234影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/1234影视.py', 1),
    ('30剧集网', '30剧集网', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/30剧集网.py', 1),
    ('456dy', '456电影网', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/456电影网.py', 1),
    ('4K影视', '4K影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/4K影视.py', 1),
    ('4K影视仓', '4K影视仓', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/4K影视仓.py', 1),
    ('55影院', '55影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/55影院(关梯).py', 1),
    ('58vy', '58影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/58影视.py', 1),
    ('6080影视', '6080影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/6080影视.py', 1),
    ('6080新视觉', '6080新视觉', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/6080新视觉.py', 1),
    ('66大片网', '66大片网', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/66大片网.py', 1),
    ('808yr', '808影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/808影院.py', 1),
    ('99短剧网', '99短剧网', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/99短剧网.py', 1),
    ('Auete影视', 'Auete影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/Auete影视.py', 1),
    ('CNFLIX', 'CNFLIX', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/CNFLIX.py', 1),
    ('EcoHub影视', 'EcoHub影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/EcoHub影视.py', 1),
    ('FoFo影院', 'FoFo影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/FoFo影院.py', 1),
    ('FreeOK', 'FreeOK', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/FreeOK.py', 1),
    ('GimyTV剧迷', 'GimyTV剧迷', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/GimyTV剧迷.py', 1),
    ('LIBVIO', 'LIBVIO', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/LIBVIO.py', 1),
    ('PTT线上看', 'PTT线上看', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/PTT线上看.py', 1),
    ('VIP兔', 'VIP兔', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/VIP兔.py', 1),
    ('VS影院', 'VS影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/VS影院.py', 1),
    ('ZIP0影视', 'ZIP0影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/ZIP0影视.py', 1),
    ('ik4k影院', 'ik4k影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/ik4k影院.py', 1),
    ('pomo', 'pomo', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/pomo.py', 1),
    ('vidhub', 'vidhub', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/vidhub.py', 1),
    ('一起影视', '一起影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/一起影视.py', 1),
    ('qw', '七味', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/七味.py', 1),
    ('qmvm', '七猫影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/七猫影视.py', 1),
    ('云朵视频', '云朵视频', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/云朵视频(关梯).py', 1),
    ('云途影视', '云途影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/云途影视.py', 1),
    ('人人视频', '人人视频', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/人人视频.py', 1),
    ('仙腾影院', '仙腾影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/仙腾影院.py', 1),
    ('YK', '优酷视频', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/优酷视频.py', 1),
    ('ddyy', '低端影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/低端影视.py', 1),
    ('sdvy', '兄弟影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/兄弟影视.py', 1),
    ('兔岛影院', '兔岛影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/兔岛影院.py', 1),
    ('8tdy', '八天电影', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/八天电影.py', 1),
    ('八度影院', '八度影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/八度影院.py', 1),
    ('八戒影视', '八戒影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/八戒影视.py', 1),
    ('gqc', '共青春影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/共青春影院.py', 1),
    ('nmvm', '农民影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/农民影视.py', 1),
    ('初见影视', '初见影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/初见影视.py', 1),
    ('刷不停短剧', '刷不停短剧', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/刷不停短剧.py', 1),
    ('jok', '剧OK', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/剧OK.py', 1),
    ('剧下饭4K', '剧下饭4K', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/剧下饭4K.py', 1),
    ('nnyy', '努努影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/努努影院.py', 1),
    ('hstv', '华数TV', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/华数TV.py', 1),
    ('华谊影视', '华谊影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/华谊影视.py', 1),
    ('厂长影视', '厂长影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/厂长影视.py', 1),
    ('厂长资源', '厂长资源', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/厂长资源.py', 1),
    ('kkvm', '可可影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/可可影视.py', 1),
    ('君念影院', '君念影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/君念影院.py', 1),
    ('咕噜咕噜', '咕噜咕噜', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/咕噜咕噜.py', 1),
    ('咸鱼影视', '咸鱼影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/咸鱼影视.py', 1),
    ('ww', '哇哇APP', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/哇哇APP.py', 1),
    ('ddvm', '嘀嗒影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/嘀嗒影视.py', 1),
    ('夏日影院', '夏日影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/夏日影院.py', 1),
    ('多多影视', '多多影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/多多影视.py', 1),
    ('dnyy', '多瑙影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/多瑙影院.py', 1),
    ('大白鲨影院', '大白鲨影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/大白鲨影院.py', 1),
    ('大马猴', '大马猴', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/大马猴.py', 1),
    ('teys', '太乙影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/太乙影视.py', 1),
    ('QU', '奇优影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/奇优影院.py', 1),
    ('qdvm', '奇点影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/奇点影视.py', 1),
    ('奈非工厂', '奈非工厂', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/奈非工厂.py', 1),
    ('好剧屋', '好剧屋', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/好剧屋.py', 1),
    ('好好看', '好好看', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/好好看.py', 1),
    ('wstv', '威视TV', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/威视TV.py', 1),
    ('宅男影视', '宅男影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/宅男影视.py', 1),
    ('小宝影院', '小宝影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/小宝影院.py', 1),
    ('小蜜蜂影院', '小蜜蜂影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/小蜜蜂影院.py', 1),
    ('山水影视', '山水影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/山水影视.py', 1),
    ('开心影院', '开心影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/开心影院.py', 1),
    ('开端影视', '开端影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/开端影视.py', 1),
    ('影巢movie', '影巢movie', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/影巢movie.py', 1),
    ('影视大全', '影视大全', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/影视大全.py', 1),
    ('wkvm', '悟空影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/悟空影视.py', 1),
    ('懂片帝AI', '懂片帝AI', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/懂片帝AI.py', 1),
    ('手机影院', '手机影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/手机影院.py', 1),
    ('搜剧AI', '搜剧AI', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/搜剧AI.py', 1),
    ('无极电影网', '无极电影网', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/无极电影网(关梯).py', 1),
    ('XH', '星河影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/星河影视.py', 1),
    ('xc', '星辰影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/星辰影院.py', 1),
    ('ysxq', '映像星球', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/映像星球.py', 1),
    ('未来影院', '未来影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/未来影院(关梯).py', 1),
    ('极速追剧', '极速追剧', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/极速追剧.py', 1),
    ('果果短剧', '果果短剧', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/果果短剧.py', 1),
    ('zzvm', '枝枝影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/枝枝影视.py', 1),
    ('枫叶4K', '枫叶4K', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/枫叶4K.py', 1),
    ('枫叶影院', '枫叶影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/枫叶影院.py', 1),
    ('knvm', '柯南影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/柯南影视.py', 1),
    ('楓林網', '楓林網', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/楓林網.py', 1),
    ('橘汁视频', '橘汁视频', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/橘汁视频.py', 1),
    ('dsys', '毒舌影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/毒舌影视.py', 1),
    ('永乐视频', '永乐视频', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/永乐视频.py', 1),
    ('泡泡影院', '泡泡影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/泡泡影院.py', 1),
    ('nvm', '泥视频', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/泥视频.py', 1),
    ('洛雪TV', '洛雪TV', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/洛雪TV.py', 1),
    ('rb', '热播APP', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/热播APP.py', 1),
    ('ayf', '爱壹帆影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/爱壹帆.py', 1),
    ('爱奇艺', '爱奇艺', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/爱奇艺.py', 1),
    ('ikbot', '爱看机器人', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/爱看机器人.py', 1),
    ('独播库', '独播库', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/独播库.py', 1),
    ('GZ', '瓜子APP', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/瓜子APP.py', 1),
    ('电影侠', '电影侠', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/电影侠.py', 1),
    ('界影视', '界影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/界影视.py', 1),
    ('白洋影院', '白洋影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/白洋影院.py', 1),
    ('百花影院', '百花影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/百花影院.py', 1),
    ('看剧AI', '看剧AI', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/看剧AI.py', 1),
    ('看戏影视', '看戏影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/看戏影视.py', 1),
    ('真狼影视', '真狼影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/真狼影视.py', 1),
    ('xmvm', '神马影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/神马影视.py', 1),
    ('第七影院', '第七影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/第七影院.py', 1),
    ('第九短剧网', '第九短剧网', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/第九短剧网.py', 1),
    ('绿色影视', '绿色影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/绿色影视.py', 1),
    ('网飞TV', '网飞TV', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/网飞TV.py', 1),
    ('网飞猫影视', '网飞猫影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/网飞猫影视(关梯).py', 1),
    ('美剧天堂', '美剧天堂', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/美剧天堂.py', 1),
    ('腾爱优芒B', '腾爱优芒B', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/腾爱优芒B.py', 1),
    ('txvm', '腾讯视频', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/腾讯视频.py', 1),
    ('MGtv', '芒果TV', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/芒果TV.py', 1),
    ('芭蕉剧场', '芭蕉剧场', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/芭蕉剧场.py', 1),
    ('cbh', '茶杯狐', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/茶杯狐.py', 1),
    ('草莓影视', '草莓影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/草莓影视.py', 1),
    ('dttv', '蛋挞TV', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/蛋挞TV.py', 1),
    ('蝶卡影视', '蝶卡影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/蝶卡影视.py', 1),
    ('袋鼠影视', '袋鼠影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/袋鼠影视.py', 1),
    ('guanfeng', '观风影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/观风影视.py', 1),
    ('视觉影院', '视觉影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/视觉影院.py', 1),
    ('豆花影视', '豆花影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/豆花影视.py', 1),
    ('达达兔影院', '达达兔影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/达达兔影院(关梯).py', 1),
    ('迷你影视', '迷你影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/迷你影视.py', 1),
    ('jgvy', '追光影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/追光影视.py', 1),
    ('追剧达人', '追剧达人', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/追剧达人.py', 1),
    ('追影', '追影', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/追影.py', 1),
    ('cjjh', '采集聚合', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/采集聚合.py', 1),
    ('JP', '金牌APP', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/金牌APP.py', 1),
    ('青牛影视', '青牛影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/青牛影视.py', 1),
    ('青鸟影视', '青鸟影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/青鸟影视.py', 1),
    ('hxq', '韩小圈', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/韩小圈.py', 1),
    ('风尚影视', '风尚影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/风尚影视.py', 1),
    ('飞快TV', '飞快TV', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/飞快TV.py', 1),
    ('飞流视频', '飞流视频', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/飞流视频.py', 1),
    ('飞牛影视', '飞牛影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/飞牛影视.py', 1),
    ('饭搭子影视', '饭搭子影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/饭搭子影视.py', 1),
    ('首映网', '首映网', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/首映网.py', 1),
    ('xhvm', '骚火影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/骚火影视.py', 1),
    ('高清点播', '高清点播', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/高清点播.py', 1),
    ('魔法影视', '魔法影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/魔法影视.py', 1),
    ('qlys', '麒麟影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/麒麟影视.py', 1),
    ('mtyy', '麦田影院', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/麦田影院.py', 1),
    ('MH', '麻花影视', '追剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/麻花影视.py', 1),
    ('MiFun', 'MiFun动漫', '动漫', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/MiFun动漫.py', 1),
    ('animexin', 'animexin', '动漫', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/animexin.py', 1),
    ('共和国动漫', '共和国动漫', '动漫', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/共和国动漫.py', 1),
    ('动漫啦', '动漫啦(羊壳观看)', '动漫', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/动漫啦.py', 1),
    ('动漫巴士', '动漫巴士', '动漫', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/动漫巴士.py', 1),
    ('樱之空动漫', '樱之空动漫', '动漫', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/樱之空动漫.py', 1),
    ('路漫漫', '路漫漫', '动漫', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/路漫漫(关梯).py', 1),
    ('青空次元', '青空次元', '动漫', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/青空次元.py', 1),
    ('黑猫动漫', '黑猫动漫', '动漫', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/黑猫动漫.py', 1),
    ('七星短剧', '七星短剧', '短剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/七星短剧.py', 1),
    ('喜福网', '喜福短剧', '短剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/喜福短剧.py', 1),
    ('在线短剧', '在线短剧', '短剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/在线短剧.py', 1),
    ('开心短剧', '开心短剧', '短剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/开心短剧.py', 1),
    ('悟圣短剧', '悟圣短剧', '短剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/悟圣短剧.py', 1),
    ('smdj', '星芽短剧', '短剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/星芽短剧.py', 1),
    ('映刻短剧', '映刻短剧', '短剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/映刻短剧.py', 1),
    ('毒舌短剧', '毒舌短剧', '短剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/毒舌短剧.py', 1),
    ('hmjc', '河马剧场', '短剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/河马剧场.py', 1),
    ('短剧大全', '短剧大全', '短剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/短剧大全.py', 1),
    ('短剧巴士', '短剧巴士', '短剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/短剧巴士.py', 1),
    ('djjh', '短剧聚合', '短剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/短剧聚合.py', 1),
    ('石榴短剧', '石榴短剧', '短剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/石榴短剧.py', 1),
    ('红果短剧', '红果短剧', '短剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/红果短剧.py', 1),
    ('红豆短剧', '红豆短剧', '短剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/红豆短剧.py', 1),
    ('蚕驰短剧网', '蚕驰短剧网', '短剧', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/蚕驰短剧网.py', 1),
    ('kf', '咖啡体育直播', '直播', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/咖啡直播.py', 1),
    ('blzb', '哔哩直播', '直播', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/哔哩直播.py', 1),
    ('央视频', '央视频', '直播', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/央视频.py', 1),
    ('youtube2', '油管直播', '直播', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/油管直播.py', 1),
    ('sm', '熊猫直播', '直播', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/熊猫直播.py', 1),
    ('jhzb', '聚合直播', '直播', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/聚合直播.py', 1),
    ('275ts', '275听书', '听书', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/275听书.py', 1),
    ('听友听书', '听友听书', '听书', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/听友听书.py', 1),
    ('ytb', '悦听吧', '听书', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/悦听吧.py', 1),
    ('易听书网', '易听书网', '听书', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/易听书网.py', 1),
    ('起点有声', '起点有声', '听书', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/起点有声.py', 1),
    ('djyy', 'DJ呦呦', '音乐', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/DJ呦呦.py', 1),
    ('QQ音乐', 'QQ音乐', '音乐', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/QQ音乐.py', 1),
    ('千千音乐', '千千音乐', '音乐', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/千千音乐.py', 1),
    ('影子音乐', '影子音乐', '音乐', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/影子音乐.py', 1),
    ('kwms', '酷我音乐', '音乐', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/酷我音乐.py', 1),
    ('音乐聚合', '音乐聚合', '音乐', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/音乐聚合.py', 1),
    ('ASMR吧', 'ASMR吧', '其他', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/ASMR吧.py', 1),
    ('星梦Asmr', '星梦Asmr', '其他', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/星梦Asmr.py', 1),
    ('youtube', '油管,py', '其他', 'https://ghfast.top/https://raw.githubusercontent.com/phu889/kjh998/refs/heads/main/py/油管.py', 1),
    ('cj_360资源', '360', '采集', 'https://360zy.com/api.php/provide/vod', 1),
    ('API_如意', '如意影视', '采集', 'https://cj.rycjapi.com/api.php/provide/vod', 1),
]

BLOCK_WORDS = ('伦理', '三级', '写真', '两性', '擦边', '福利', '成人', '里番')
PROMO = re.compile(r'(TG频道|t\.me/|telegram|官网|关注|公众号|QQ群|微信群|请勿受骗|免费接口|置顶|公告|跑马灯|海豚影视|@hshsjk)', re.I)


def region_of(area):
    a = str(area or '').split(',')[0].split('/')[0].strip()
    if not a:
        return ''
    for k, v in (('香港', '香港'), ('澳门', '香港'), ('台湾', '台湾'), ('大陆', '大陆'), ('内地', '大陆'),
                 ('中国', '大陆'), ('国产', '大陆'), ('日本', '日本'), ('韩国', '韩国'), ('泰国', '泰国'),
                 ('印度', '印度'), ('美国', '美国')):
        if k in a:
            return v
    if any(w in a for w in ('英国', '法国', '德国', '意大利', '西班牙', '加拿大', '澳大利亚', '俄罗斯', '欧美',
                            '爱尔兰', '荷兰', '比利时', '瑞典', '丹麦', '挪威', '波兰', '新西兰', '墨西哥', '巴西')):
        return '欧美'
    return '其他'


def clean_text(t):
    t = re.sub(r'<[^>]+>', '', str(t or ''))
    t = re.sub(r'&nbsp;|&amp;|&lt;|&gt;|&quot;', ' ', t)
    t = re.sub(r'(https?://\S+|www\.\S+)', '', t)
    t = re.sub(r'[^。！\n]*(QQ群|微信|公众号|电报|TG|telegram|关注|跑马灯|广告|请勿受骗|海豚影视)[^。！\n]*[。！]?', '', t, flags=re.I)
    return re.sub(r'[ \t]+', ' ', t).strip()


def direct_or_parse(url, header=None):
    """智能识别：直链直接播，否则交给壳解析"""
    url = (url or '').strip()
    hd = header or {'User-Agent': UAS[2]}
    if re.search(r'\.(m3u8|mp4|flv|mkv|mp3|m4a|aac|ts|webm|mov|avi)(\?|$)', url, re.I):
        return {'parse': 0, 'jx': 0, 'url': url, 'header': hd}
    return {'parse': 1, 'jx': 1, 'url': url, 'header': hd}

class CMS(object):
    """苹果 CMS / type1 json 接口（采集站）"""
    def __init__(self, host, arg=''):
        self.h = host
        self.arg = arg

    def get(self, url, headers=None, timeout=10):
        hd = {'User-Agent': random.choice(UAS)}
        hd.update(headers or {})
        return self.h.fetch(url, headers=hd, timeout=timeout)

    def getjson(self, url, headers=None, timeout=10):
        try:
            return self.get(url, headers, timeout).json()
        except Exception:
            return {}

    def init(self, ext=''):
        pass

    def api(self, q):
        base = self.arg
        joiner = '&' if '?' in base else '?'
        return self.getjson(base + joiner + q.lstrip('?'))

    def vod(self, v):
        reg = region_of(v.get('vod_area'))
        name = v.get('vod_name', '')
        return {'vod_id': str(v.get('vod_id', '')), 'vod_name': (f'【{reg}】' if reg else '') + name,
                'vod_pic': v.get('vod_pic', ''), 'vod_remarks': v.get('vod_remarks', '') or str(v.get('vod_year', ''))}

    def ok(self, v):
        return not any(w in str(v.get('type_name', '')) + str(v.get('vod_name', '')) for w in BLOCK_WORDS)

    def homeContent(self, f):
        d = self.api('ac=list')
        cls = [{'type_id': str(c['type_id']), 'type_name': c['type_name']} for c in d.get('class', [])
               if not any(w in c['type_name'] for w in BLOCK_WORDS)]
        if not cls:
            seen = {}
            for v in (d.get('list') or []):
                tid, tn = str(v.get('type_id', '')), str(v.get('type_name', ''))
                if tid and tn and tid not in seen and not any(w in tn for w in BLOCK_WORDS):
                    seen[tid] = tn
            cls = [{'type_id': k, 'type_name': v} for k, v in seen.items()]
        return {'class': cls}

    def homeVideoContent(self):
        d = self.api('ac=detail&pg=1')
        return {'list': [self.vod(v) for v in d.get('list', []) if self.ok(v)]}

    def categoryContent(self, tid, pg, f, ext):
        d = self.api(f'ac=detail&t={quote(str(tid))}&pg={pg}')
        lst = [self.vod(v) for v in d.get('list', []) if self.ok(v)]
        return {'list': lst, 'page': int(pg), 'pagecount': int(d.get('pagecount') or (int(pg) + (1 if lst else 0))),
                'limit': 20, 'total': int(d.get('total') or 9999)}

    def detailContent(self, ids):
        d = self.api(f'ac=detail&ids={ids[0]}')
        if not d.get('list'):
            return {'list': []}
        v = d['list'][0]
        froms = (v.get('vod_play_from') or '').split('$$$')
        urls = (v.get('vod_play_url') or '').split('$$$')
        pairs = [(a, b.strip('#')) for a, b in zip(froms, urls) if b]
        pairs.sort(key=lambda p: 0 if '.m3u8' in p[1] else 1)
        vod = self.vod(v)
        vod.update({'type_name': v.get('type_name', ''), 'vod_year': v.get('vod_year', ''),
                    'vod_area': v.get('vod_area', ''), 'vod_actor': clean_text(v.get('vod_actor')),
                    'vod_director': clean_text(v.get('vod_director')),
                    'vod_content': clean_text(v.get('vod_content') or v.get('vod_blurb')),
                    'vod_play_from': '$$$'.join(p[0] for p in pairs), 'vod_play_url': '$$$'.join(p[1] for p in pairs)})
        return {'list': [vod]}

    def searchContent(self, key, quick, pg='1'):
        d = self.api(f'ac=detail&wd={quote(key)}&pg={pg}')
        return {'list': [self.vod(v) for v in d.get('list', []) if self.ok(v)]}

    def playerContent(self, flag, id, vip):
        return direct_or_parse(id)

    def localProxy(self, param):
        return None

class Spider(BaseSpider):
    def getName(self):
        return '摸海豚'

    def init(self, extend=''):
        self.subs = {}
        self.home_cache = {}
        self.failed = {}
        self.area_cache = {}
        self.lock = threading.Lock()
        self.meta = {s[0]: s for s in SITES}
        self.cache_dir = os.path.join(tempfile.gettempdir(), 'mohaitun')
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
        except Exception:
            pass

    def fetch(self, url, headers=None, timeout=10, **kw):
        hd = {'User-Agent': random.choice(UAS)}
        hd.update(headers or {})
        return BaseSpider.fetch(self, url, headers=hd, timeout=timeout, **kw)

    def post(self, url, data=None, json=None, headers=None, timeout=10, **kw):
        hd = {'User-Agent': random.choice(UAS)}
        hd.update(headers or {})
        if json is not None:
            return BaseSpider.post(self, url, json=json, headers=hd, timeout=timeout, **kw)
        return BaseSpider.post(self, url, data=data, headers=hd, timeout=timeout, **kw)

    def _py_source(self, key, url):
        path = os.path.join(self.cache_dir, hashlib.md5(key.encode()).hexdigest() + '.py')
        fresh = os.path.exists(path) and time.time() - os.path.getmtime(path) < 86400
        if not fresh:
            try:
                r = self.fetch(url, headers={'User-Agent': 'okhttp/4.12.0'}, timeout=25)
                txt = r.content.decode('utf-8', 'ignore')
                if 'class Spider' in txt:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(txt)
                    return txt
            except Exception:
                pass
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                return f.read()
        return ''

    def sub(self, key):
        if key in self.subs:
            return self.subs[key]
        if time.time() - self.failed.get(key, 0) < 120:
            return None
        with self.lock:
            if key in self.subs:
                return self.subs[key]
            meta = self.meta.get(key)
            if not meta:
                return None
            _, name, grp, arg, _s = meta
            obj = None
            try:
                if grp == '采集':
                    obj = CMS(self, arg)
                    obj.init('')
                else:
                    src = self._py_source(key, arg)
                    if src:
                        mod = types.ModuleType('mht_' + hashlib.md5(key.encode()).hexdigest()[:8])
                        mod.__file__ = os.path.join(self.cache_dir, key + '.py')
                        exec(compile(src, mod.__file__, 'exec'), mod.__dict__)
                        obj = mod.Spider()
                        try:
                            obj.init('')
                        except TypeError:
                            obj.init()
            except Exception:
                obj = None
            if obj is None:
                self.failed[key] = time.time()
            else:
                self.subs[key] = obj
            return obj

    def call(self, key, fn, *a):
        s = self.sub(key)
        if s is None:
            return {}
        try:
            r = getattr(s, fn)(*a)
            if isinstance(r, str):
                r = json.loads(r) if r.strip().startswith('{') else {}
            return r or {}
        except Exception:
            return {}

    def wrap(self, key, vods):
        out = []
        for v in vods or []:
            vid = str(v.get('vod_id', ''))
            name = str(v.get('vod_name', ''))
            if not vid or PROMO.search(name) or vid.startswith('pinned') or any(w in name for w in BLOCK_WORDS):
                continue
            x = dict(v)
            x['vod_id'] = key + SEP + vid
            x['vod_pic'] = self.fix_pic(x.get('vod_pic'))
            out.append(x)
        return out

    def fix_pic(self, pic):
        pic = str(pic or '').strip()
        if not pic or pic.startswith('data:') or not re.match(r'^(https?:)?//', pic):
            return DEFAULT_PIC
        if pic.startswith('//'):
            pic = 'https:' + pic
        if pic.startswith('http://'):
            pic = 'https://' + pic[7:]
        if ' ' in pic:
            pic = pic.replace(' ', '%20')
        if '@Referer=' in pic or '@User-Agent=' in pic or '127.0.0.1' in pic or 'localhost' in pic:
            return pic
        host = re.sub(r'^https?://', '', pic).split('/')[0].split(':')[0]
        ref = next((v for k, v in PIC_REFERER.items() if host.endswith(k)), None)
        if ref:
            return pic + '@Referer=' + ref
        return pic

    def fill_area(self, key, lst):
        need = [v for v in lst if not v.get('vod_area') and v['vod_id'] not in self.area_cache]
        def one(v):
            d = self.call(key, 'detailContent', [v['vod_id'].split(SEP, 1)[1]]).get('list') or [{}]
            self.area_cache[v['vod_id']] = str(d[0].get('vod_area') or '')
        if need:
            pool = ThreadPoolExecutor(max_workers=8)
            futs = [pool.submit(one, v) for v in need[:30]]
            wait(futs, timeout=12)
            pool.shutdown(wait=False)
        for v in lst:
            if not v.get('vod_area'):
                v['vod_area'] = self.area_cache.get(v['vod_id'], '')

    def tag_area(self, v):
        reg = region_of(v.get('vod_area'))
        if reg and not str(v.get('vod_remarks', '')).startswith('【'):
            v['vod_remarks'] = f'【{reg}】' + str(v.get('vod_remarks') or '')

    def site_home(self, key):
        if not (self.home_cache.get(key) or {}).get('class'):
            r = self.call(key, 'homeContent', True)
            cls = [c for c in (r.get('class') or []) if isinstance(c, dict) and c.get('type_id') is not None and c.get('type_name')
                   and not PROMO.search(str(c.get('type_name', '')))
                   and not any(w in str(c.get('type_name', '')) for w in BLOCK_WORDS)]
            self.home_cache[key] = {'class': cls, 'filters': r.get('filters') or {}}
        return self.home_cache[key]

    def homeContent(self, filter):
        classes, filters = [], {}
        for key, name, grp, arg, _s in SITES:
            classes.append({'type_id': key, 'type_name': f'【{grp}】{name}'})
        for key, name, grp, arg, _s in SITES:
            h = self.home_cache.get(key)
            fl = []
            if h and h.get('class'):
                fl.append({'key': '__c', 'name': '分类',
                           'value': [{'n': c['type_name'], 'v': str(c['type_id'])} for c in h['class']]})
            fl.append({'key': '__area', 'name': '地区', 'value': [{'n': r, 'v': r} for r in AREAS]})
            filters[key] = fl
        return {'class': classes, 'filters': filters}

    def homeVideoContent(self):
        return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        key = tid
        extend = dict(extend or {})
        h = self.site_home(key)
        if not h['class']:
            return {'list': [], 'page': int(pg), 'pagecount': int(pg), 'limit': 20, 'total': 0}
        sub_tid = extend.pop('__c', None) or str(h['class'][0]['type_id'])
        area = extend.pop('__area', '全部') or '全部'
        r = self.call(key, 'categoryContent', sub_tid, str(pg), True, extend)
        lst = self.wrap(key, r.get('list', []))
        if area != '全部' and lst:
            self.fill_area(key, lst)
            lst = [v for v in lst if region_of(v.get('vod_area')) == area]
        for v in lst:
            self.tag_area(v)
        return {'list': lst, 'page': int(r.get('page') or pg),
                'pagecount': int(r.get('pagecount') or (int(pg) + (1 if lst else 0))),
                'limit': int(r.get('limit') or 20), 'total': int(r.get('total') or 9999)}

    def detailContent(self, ids):
        key, vid = ids[0].split(SEP, 1)
        r = self.call(key, 'detailContent', [vid])
        lst = r.get('list') or []
        if not lst:
            return {'list': []}
        vod = dict(lst[0])
        vod['vod_id'] = ids[0]
        vod['vod_pic'] = self.fix_pic(vod.get('vod_pic'))
        vod['vod_content'] = clean_text(vod.get('vod_content'))
        vod['vod_actor'] = clean_text(vod.get('vod_actor'))
        vod['vod_director'] = clean_text(vod.get('vod_director'))
        urls = []
        for line in str(vod.get('vod_play_url', '')).split('$$$'):
            eps = []
            for ep in line.split('#'):
                if not ep:
                    continue
                if '$' in ep:
                    n, u = ep.split('$', 1)
                else:
                    n, u = '播放', ep
                eps.append(f'{n}${key}{SEP}{u}')
            urls.append('#'.join(eps))
        vod['vod_play_url'] = '$$$'.join(urls)
        if vod.get('vod_area'):
            reg = region_of(vod.get('vod_area'))
            vod['vod_area'] = f"{vod['vod_area']}（{reg}）" if reg and reg not in str(vod['vod_area']) else vod['vod_area']
        return {'list': [vod]}

    def searchContent(self, key, quick, pg='1'):
        keys = [s[0] for s in SITES if s[4]]
        res = {}
        def one(k):
            res[k] = self.wrap(k, self.call(k, 'searchContent', key, quick, str(pg)).get('list', []))[:30]
        pool = ThreadPoolExecutor(max_workers=15)
        futs = [pool.submit(one, k) for k in keys]
        wait(futs, timeout=20)
        pool.shutdown(wait=False)
        out = []
        for k in keys:
            sname = self.meta[k][1]
            for v in res.get(k, []):
                reg = region_of(v.get('vod_area'))
                v['vod_name'] = f'【{sname}】' + (f'【{reg}】' if reg else '') + str(v.get('vod_name', ''))
                out.append(v)
        return {'list': out, 'page': int(pg), 'pagecount': int(pg) + 1 if out else int(pg)}

    def searchContentPage(self, key, quick, pg):
        return self.searchContent(key, quick, pg)

    def playerContent(self, flag, id, vipFlags):
        if SEP not in id:
            return direct_or_parse(id)
        key, pid = id.split(SEP, 1)
        r = self.call(key, 'playerContent', flag, pid, vipFlags)
        if not r or not r.get('url'):
            return direct_or_parse(pid)
        url = r['url']
        if r.get('parse', 1) == 1 and re.search(r'\.(m3u8|mp4|flv|mkv|mp3|m4a)(\?|$)', url, re.I):
            r['parse'] = 0
            r['jx'] = 0
        if 'header' not in r:
            r['header'] = {'User-Agent': UAS[2]}
        return r

    def isVideoFormat(self, url):
        return bool(re.search(r'\.(m3u8|mp4|flv|mkv)(\?|$)', url or '', re.I))

    def manualVideoCheck(self):
        pass

    def localProxy(self, param):
        for s in self.subs.values():
            try:
                r = s.localProxy(param) if s else None
                if r:
                    return r
            except Exception:
                continue
        return None

    def liveContent(self, url):
        return ''

    def destroy(self):
        for s in self.subs.values():
            try:
                s.destroy()
            except Exception:
                pass
