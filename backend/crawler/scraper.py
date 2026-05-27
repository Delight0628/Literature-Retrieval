"""Scrapling 爬虫核心模块 - 实现双层信息采集

策略：使用 Scrapling 的 Fetcher 进行网页爬取，配合 requests/httpx 作为备选。
当爬取失败时，使用内置的文学知识库作为 fallback。
"""

import sys
import re
import json
from scrapling.fetchers import Fetcher
from typing import Optional

sys.stdout.reconfigure(encoding='utf-8')

# 文学作品主题模块定义
LITERARY_MODULES = [
    {"id": "background", "name": "时代背景", "keywords": ["背景", "时代", "历史", "创作背景"]},
    {"id": "author", "name": "作者介绍", "keywords": ["作者", "生平", "简介", "屈原"]},
    {"id": "text", "name": "原文注释", "keywords": ["原文", "注释", "翻译", "注解"]},
    {"id": "art", "name": "艺术特色", "keywords": ["艺术", "特色", "手法", "表现手法"]},
    {"id": "famous", "name": "名句赏析", "keywords": ["名句", "名言", "赏析", "名句名篇"]},
    {"id": "influence", "name": "后世影响", "keywords": ["影响", "评价", "地位", "文学地位"]},
]

# 内置文学知识库（当爬取失败时使用）
LITERARY_DATABASE = {
    "离骚": {
        "abstract": "《离骚》是中国战国时期楚国诗人屈原创作的诗篇，是中国古代最长的抒情诗。这是一首政治抒情诗，当作于屈原被放逐之后。此诗以诗人自述身世、遭遇、心志为中心。前半篇反复倾诉诗人对楚国命运和人民生活的关心，表达要求革新政治的愿望，和坚持理想、虽逢灾厄也绝不与邪恶势力妥协的意志；后半篇通过神游天界、追求实现理想和失败后欲以身殉的陈述，反映出诗人热爱国家和人民的思想感情。全诗运用美人香草的比喻、大量的神话传说和丰富的想象，形成绚烂的文采和宏伟的结构，表现出积极的浪漫主义精神，并开创了中国文学史上的「骚体」诗歌形式，对后世产生了深远的影响。",
        "background": "《离骚》创作于战国时期楚国，当时楚国面临秦国的威胁，政治腐败，屈原因主张联齐抗秦而被流放。这首诗大约作于公元前300年左右，是屈原在流放期间创作的代表作。诗中反映了战国时期楚国的社会矛盾和屈原的政治理想。",
        "author": "屈原（约公元前340年—公元前278年），战国时期楚国诗人、政治家。芈姓，屈氏，名平，字原，又自云名正则，字灵均。屈原是中国历史上第一位伟大的爱国诗人，中国浪漫主义文学的奠基人，被誉为中华诗祖、辞赋之祖。他是楚辞的创立者和代表作者，开辟了香草美人的传统。屈原的出现，标志着中国诗歌进入了一个由集体歌唱到个人独创的新时代。",
        "text": "帝高阳之苗裔兮，朕皇考曰伯庸。摄提贞于孟陬兮，惟庚寅吾以降。皇览揆余初度兮，肇锡余以嘉名：名余曰正则兮，字余曰灵均。纷吾既有此内美兮，又重之以修能。扈江离与辟芷兮，纫秋兰以为佩。汩余若将不及兮，恐年岁之不吾与。朝搴阰之木兰兮，夕揽洲之宿莽。日月忽其不淹兮，春与秋其代序。惟草木之零落兮，恐美人之迟暮。不抚壮而弃秽兮，何不改乎此度？乘骐骥以驰骋兮，来吾道夫先路！",
        "art": "《离骚》在艺术上具有极高的成就：1. 开创了香草美人的比兴传统，以香草比喻高洁品格，以恶草比喻奸佞小人；2. 运用了大量神话传说和丰富的想象，构建了一个瑰丽的艺术世界；3. 采用了楚国方言和民歌形式，创造了独特的骚体诗；4. 结构宏大，情感激昂，具有强烈的浪漫主义色彩；5. 语言优美，音韵和谐，具有极高的文学价值。",
        "famous": "1. '路漫漫其修远兮，吾将上下而求索' —— 表达了追求真理的坚定决心；2. '长太息以掩涕兮，哀民生之多艰' —— 表现了对人民疾苦的深切同情；3. '亦余心之所善兮，虽九死其犹未悔' —— 表达了坚持理想的决心；4. '举世皆浊我独清，众人皆醉我独醒' —— 表现了高洁的品格；5. '惟草木之零落兮，恐美人之迟暮' —— 表达了对时光流逝的感慨。",
        "influence": "《离骚》对后世产生了深远的影响：1. 开创了中国浪漫主义文学传统；2. 形成了香草美人的比兴手法，影响了后世无数诗人；3. 屈原的爱国精神成为中华民族的精神象征；4. 楚辞成为中国文学的重要源头之一；5. 端午节的设立与纪念屈原有关，成为中国重要的传统节日。"
    },
    "红楼梦": {
        "abstract": "《红楼梦》是中国古代四大名著之首，清代作家曹雪芹创作的章回体长篇小说。又名《石头记》《金玉缘》。小说以贾、史、王、薛四大家族的兴衰为背景，以贾宝玉、林黛玉、薛宝钗的爱情婚姻故事为主线，真实、生动地描写了十八世纪上半叶中国末期封建社会的全部生活。",
        "background": "《红楼梦》创作于18世纪中叶的清朝乾隆年间，当时中国封建社会已走向衰落，资本主义萌芽开始出现。曹雪芹以自身的家族兴衰经历为素材，创作了这部伟大的现实主义作品。",
        "author": "曹雪芹（约1715年—约1763年），名沾，字梦阮，号雪芹，又号芹溪、芹圃。清代小说家。出身于一个百年望族的大官僚地主家庭，后因家庭的衰败而饱尝了人生的辛酸。他以坚韧不拔的毅力，历经多年艰辛，终于创作出极具思想性、艺术性的伟大作品《红楼梦》。",
        "famous": "1. '满纸荒唐言，一把辛酸泪。都云作者痴，谁解其中味'；2. '假作真时真亦假，无为有处有还无'；3. '世事洞明皆学问，人情练达即文章'；4. '机关算尽太聪明，反误了卿卿性命'；5. '一朝春尽红颜老，花落人亡两不知'。",
        "influence": "《红楼梦》是中国古典小说的巅峰之作，被誉为'中国封建社会的百科全书'。它不仅在中国文学史上占有重要地位，还形成了专门的学术研究领域'红学'，对后世文学创作产生了深远影响。"
    },
    "滕王阁序": {
        "abstract": "《滕王阁序》全称《秋日登洪府滕王阁饯别序》，是唐代文学家王勃创作的一篇骈文。文章由洪州的地势、人才写到宴会，写滕王阁的壮丽，眺望的广远，扣紧秋日，景色鲜明；再从宴会娱游写到人生遇合，抒发身世之感；最后写自己的志向，并对宴会主人表示感谢。",
        "author": "王勃（约650年—约676年），字子安，汉族，唐代文学家。古绛州龙门（今山西河津）人，出身儒学世家，与杨炯、卢照邻、骆宾王并称为'初唐四杰'，王勃为四杰之首。",
        "famous": "1. '落霞与孤鹜齐飞，秋水共长天一色'；2. '关山难越，谁悲失路之人；萍水相逢，尽是他乡之客'；3. '老当益壮，宁移白首之心；穷且益坚，不坠青云之志'；4. '时运不齐，命途多舛'。",
        "influence": "《滕王阁序》是初唐骈文的代表作，以其华美的辞藻、深邃的意境和激昂的情感著称，被誉为'千古第一骈文'。其中的名句至今仍被广泛引用。"
    }
}


def _scrapling_fetch(url: str) -> Optional[object]:
    """使用 Scrapling Fetcher 获取页面"""
    try:
        page = Fetcher.get(url)
        if page.status == 200:
            return page
    except Exception as e:
        print(f"Scrapling 爬取失败 {url}: {e}")
    return None


def _extract_text_from_page(page) -> str:
    """从 Scrapling 页面对象提取文本"""
    try:
        body = page.css('body')
        if body:
            text = body[0].text.strip()
            return text
    except Exception:
        pass
    return ""


def _try_scrapling_search(query: str) -> dict:
    """尝试使用 Scrapling 爬取搜索结果"""
    result = {"abstract": "", "url": "", "source": ""}

    # 尝试多个搜索 URL
    search_urls = [
        f"https://baike.baidu.com/item/{query}",
    ]

    for url in search_urls:
        try:
            page = _scrapling_fetch(url)
            if page:
                text = _extract_text_from_page(page)
                if text and len(text) > 50:
                    # 提取摘要（取前200字）
                    result["abstract"] = text[:200] + "..." if len(text) > 200 else text
                    result["url"] = url
                    result["source"] = "百度百科"
                    break
        except Exception as e:
            print(f"爬取失败: {e}")

    return result


def _normalize_query(query: str) -> str:
    """标准化查询关键词，支持中英文模糊匹配"""
    # 英文到中文的映射
    en_to_cn = {
        "li sao": "离骚",
        "li Sao": "离骚",
        "lisao": "离骚",
        "hong lou meng": "红楼梦",
        "dream of the red chamber": "红楼梦",
        "teng wang ge xu": "滕王阁序",
        "preface to the prince teng's pavilion": "滕王阁序",
    }
    query_lower = query.lower().strip()
    if query_lower in en_to_cn:
        return en_to_cn[query_lower]

    # 检查本地数据库是否有精确匹配
    if query in LITERARY_DATABASE:
        return query

    # 模糊匹配
    for key in LITERARY_DATABASE:
        if query in key or key in query:
            return key

    return query


def general_search(query: str) -> dict:
    """第一层：泛化检索 - 获取模块列表和概要"""

    # 标准化查询
    normalized_query = _normalize_query(query)

    # 1. 首先尝试爬取
    scrapling_result = _try_scrapling_search(normalized_query)

    # 2. 检查本地数据库
    local_data = LITERARY_DATABASE.get(normalized_query, {})

    # 3. 合并数据（优先使用爬取结果）
    abstract = scrapling_result.get("abstract") or local_data.get("abstract", "")

    # 4. 构建模块列表
    modules = []
    for module in LITERARY_MODULES:
        # 从本地数据库或爬取结果中提取模块内容
        summary = local_data.get(module["id"], "")
        source = "本地知识库" if summary else "系统默认"

        if not summary and abstract:
            # 从摘要中提取相关内容
            summary = _extract_module_summary_from_abstract(abstract, module)
            if summary:
                source = scrapling_result.get("source", "百度百科")

        if not summary:
            summary = "暂无概要信息，请点击查看详细内容"

        modules.append({
            "id": module["id"],
            "name": module["name"],
            "summary": summary,
            "source": source,
            "source_url": scrapling_result.get("url", ""),
        })

    return {"query": query, "modules": modules}


def _extract_module_summary_from_abstract(abstract: str, module: dict) -> str:
    """从摘要文本中提取与特定模块相关的内容"""
    keywords = module.get("keywords", [])
    sentences = re.split(r'[。！？；\n]', abstract)

    relevant_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence or len(sentence) < 5:
            continue
        for keyword in keywords:
            if keyword in sentence:
                relevant_sentences.append(sentence)
                break

    if relevant_sentences:
        result = "。".join(relevant_sentences[:3])
        if len(result) > 200:
            result = result[:200] + "..."
        return result

    if abstract and len(abstract) > 20:
        return abstract[:200] + "..." if len(abstract) > 200 else abstract

    return ""


def deep_search(query: str, module_id: str) -> dict:
    """第二层：深度检索 - 获取选定模块的详细内容"""

    # 标准化查询
    normalized_query = _normalize_query(query)

    # 找到模块信息
    module_info = next(
        (m for m in LITERARY_MODULES if m["id"] == module_id),
        {"id": module_id, "name": module_id, "keywords": [normalized_query]},
    )

    results = {
        "module": module_info,
        "content": "",
        "sources": [],
        "images": [],
    }

    # 1. 首先尝试爬取
    scrapling_result = _try_scrapling_search(normalized_query)
    if scrapling_result.get("abstract"):
        results["content"] = scrapling_result["abstract"]
        results["sources"].append({
            "name": scrapling_result.get("source", "百度百科"),
            "url": scrapling_result.get("url", ""),
        })

    # 2. 从本地数据库获取详细内容
    local_data = LITERARY_DATABASE.get(normalized_query, {})
    if local_data.get(module_id):
        results["content"] = local_data[module_id]
        if not results["sources"]:
            results["sources"].append({
                "name": "本地知识库",
                "url": "",
            })

    # 3. 如果内容仍然为空，提供默认提示
    if not results["content"]:
        results["content"] = f"暂未找到关于「{query}」的{module_info['name']}详细信息。\n\n建议尝试其他关键词或稍后重试。"

    return results
