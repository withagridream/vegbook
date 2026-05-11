"""
英語データ投入スクリプト
対象: crops, crop_categories, grow_environments, pests, pest_controls, fertilizers, glossary
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'vegbook.db'

# ------------------------------------------------------------------
# crop_categories
# ------------------------------------------------------------------
CATEGORIES_EN = {
    "果菜類":   "Fruiting Vegetables",
    "葉モノ野菜": "Leafy Vegetables",
    "根菜類":   "Root Vegetables",
    "ハーブ":   "Herbs",
    "豆類":    "Legumes",
    "イモ類":   "Tubers",
}

# ------------------------------------------------------------------
# grow_environments
# ------------------------------------------------------------------
ENVIRONMENTS_EN = {
    "ほ場":    "Field",
    "プランター": "Planter",
    "ベランダ":  "Balcony",
    "水耕栽培":  "Hydroponics",
    "室内":    "Indoors",
}

# ------------------------------------------------------------------
# pests
# ------------------------------------------------------------------
PESTS_EN = {
    "アブラムシ":           "Aphid",
    "ハダニ":              "Spider Mite",
    "コナジラミ":           "Whitefly",
    "オオタバコガ":          "Cotton Bollworm",
    "アオムシ（モンシロチョウ幼虫）": "Cabbage White Caterpillar",
    "コナガ":              "Diamondback Moth",
    "ネキリムシ（ヨトウムシ幼虫）": "Cutworm",
}

# ------------------------------------------------------------------
# pest_controls
# ------------------------------------------------------------------
PEST_CONTROLS_EN = {
    "防虫ネット":                          "Insect-proof net",
    "粘着シート（黄色）":                    "Yellow sticky trap",
    "木酢液":                             "Wood vinegar spray",
    "スミチオン乳剤":                       "Sumithion emulsion (malathion-based)",
    "粘着テープ除去・木酢液散布・天敵（テントウムシ）": "Remove with tape, spray wood vinegar, use ladybugs",
    "水スプレーで洗い流す・殺ダニ剤（バロックフロアブル）": "Wash off with water spray, apply miticide",
    "防虫ネット・BT剤（オルトラン）・手取り除去":  "Insect net, BT spray, hand removal",
    "防虫ネット・BT剤・天敵（コナガサムライコマユバチ）": "Insect net, BT spray, parasitic wasp",
    "株元を掘り起こして手取り・ネキリムシ防除剤":  "Dig around base and remove by hand, apply cutworm bait",
    "粘着テープ・木酢液散布":                 "Sticky tape, wood vinegar spray",
}

# ------------------------------------------------------------------
# fertilizers
# ------------------------------------------------------------------
FERTILIZERS_EN = {
    "化成肥料（8-8-8）":       "Compound fertilizer (8-8-8 NPK)",
    "骨粉":                  "Bone meal",
    "腐葉土":                 "Leaf mold",
    "液体肥料":               "Liquid fertilizer",
    "苦土石灰":               "Dolomitic lime",
    "完熟堆肥":               "Mature compost",
    "化成肥料8-8-8":          "Compound fertilizer 8-8-8 NPK",
    "液体肥料（ハイポネックス）":  "Liquid fertilizer (Hyponex)",
    "過リン酸石灰":            "Superphosphate",
}

# ------------------------------------------------------------------
# crops: (name, name_en, watering_en, sunlight_en, failure_points_en, harvest_sign_en, storage_en)
# ------------------------------------------------------------------
CROPS_EN = [
    ("トマト", "Tomato",
     "Water when topsoil dries out. Reduce watering during fruit-setting to improve sweetness.",
     "Full sun, 6+ hours of direct sunlight daily.",
     "Blossom-end rot from inconsistent watering; lateral shoots left unremoved reduce yield.",
     "Fruit turns fully red and yields slightly to gentle pressure.",
     "Store at room temperature (not refrigerated) for up to 1 week; refrigerate once cut."),

    ("シシトウ", "Shishito Pepper",
     "Water when topsoil dries out. Keep evenly moist.",
     "Full sun preferred; tolerates partial shade.",
     "Aphid and spider mite infestations; poor fruit set in extreme heat.",
     "Pick when fruit is about 5–6 cm long and still glossy green.",
     "Wrap in paper towel, refrigerate in a bag for up to 1 week."),

    ("ほうれん草", "Spinach",
     "Keep soil consistently moist; drought causes bolting.",
     "Full sun to partial shade.",
     "Bolts quickly in warm weather; sensitive to acidic soil — lime before planting.",
     "Harvest outer leaves first when plants reach 20–25 cm.",
     "Blanch and freeze; fresh leaves last 3–4 days refrigerated."),

    ("ピーマン", "Bell Pepper",
     "Water when topsoil dries. Consistent moisture prevents blossom drop.",
     "Full sun, 6+ hours daily.",
     "Aphids and spider mites; fruit drop in high heat above 35 °C.",
     "Pick when fruit is plump and skin is glossy; green stage is edible.",
     "Refrigerate in a bag for up to 2 weeks."),

    ("まくわうり", "Oriental Melon",
     "Water deeply but infrequently; reduce after fruit swells.",
     "Full sun essential.",
     "Powdery mildew; same family as cucumber — avoid planting together.",
     "Skin turns yellow and stem cracks slightly; sweet fragrance appears.",
     "Store at room temperature until ripe; refrigerate after cutting."),

    ("レタス", "Lettuce",
     "Keep soil evenly moist; dryness causes tip burn.",
     "Full sun to partial shade; partial shade reduces bolting in summer.",
     "Bolts in heat; tip burn from calcium deficiency in dry conditions.",
     "Harvest outer leaves when they reach full size; cut head before bolting.",
     "Wrap in damp paper towel and refrigerate for 3–5 days."),

    ("にんじん", "Carrot",
     "Water consistently; irregular watering causes root splitting.",
     "Full sun.",
     "Poor germination in dry soil; forked roots from stony or compacted soil.",
     "Shoulder of root shows above soil at 3–4 cm diameter; leaves are 30+ cm.",
     "Remove tops, store in damp newspaper in refrigerator for up to 2 weeks."),

    ("カブ", "Turnip",
     "Water when topsoil dries. Even moisture prevents cracking.",
     "Full sun to partial shade.",
     "Root cracking from irregular watering; clubroot disease in acidic soil.",
     "Root reaches 5–6 cm diameter and skin is smooth.",
     "Remove tops, refrigerate in a bag for up to 1 week."),

    ("ダイコン", "Daikon Radish",
     "Water when topsoil dries. Deep, even moisture for straight roots.",
     "Full sun.",
     "Forked roots in stony soil; keep the bed deeply tilled to 40 cm.",
     "Shoulder is 6–7 cm in diameter; skin is smooth and firm.",
     "Remove tops; store in cool dark place wrapped in newspaper for up to 2 weeks."),

    ("小松菜", "Komatsuna (Japanese Mustard Spinach)",
     "Keep soil evenly moist; dryness causes bitterness.",
     "Full sun to partial shade.",
     "Cabbage worm and flea beetle damage; use insect netting from the start.",
     "Harvest when leaves are 20–25 cm and still tender.",
     "Blanch and freeze; fresh leaves last 3–4 days refrigerated."),

    ("玉レタス", "Head Lettuce (Iceberg-type)",
     "Water consistently; avoid wetting leaves to prevent rot.",
     "Full sun to partial shade.",
     "Head fails to form in high heat; bolts quickly — time sowing for cool season.",
     "Head feels firm when gently squeezed.",
     "Wrap in plastic, refrigerate for up to 1 week."),

    ("キャベツ", "Cabbage",
     "Water when topsoil dries. Even moisture prevents head cracking.",
     "Full sun.",
     "Caterpillar damage; head cracks if left too long after maturity.",
     "Head feels firm and solid when pressed; outer leaves slightly pale.",
     "Wrap cut side in plastic wrap; refrigerate for up to 2 weeks."),

    ("きゅうり", "Cucumber",
     "Water daily in summer; keep soil consistently moist.",
     "Full sun, 6+ hours daily.",
     "Fusarium wilt in poor-draining soil; harvest frequently to encourage production.",
     "Fruit is 20–22 cm, deep green, and firm.",
     "Wrap individually, refrigerate for up to 5 days; avoid cold below 10 °C."),

    ("スティックセニョール", "Sprouting Broccoli",
     "Water when topsoil dries. Consistent moisture during head formation.",
     "Full sun.",
     "Same family as cabbage — vulnerable to caterpillars; use insect netting.",
     "Harvest central head before flowers open; side shoots follow.",
     "Refrigerate in a bag; use within 3–4 days for best flavor."),

    ("しょうが", "Ginger",
     "Keep soil consistently moist; mulch to retain moisture.",
     "Partial shade; direct midday sun can scorch leaves.",
     "Root rot in waterlogged soil; slow to sprout — do not overwater early on.",
     "Stems begin to yellow and dry out in autumn.",
     "Store unwashed in a cool, dry place; last several weeks."),

    ("エダマメ", "Edamame (Green Soybean)",
     "Water generously during flowering and pod-filling stages.",
     "Full sun.",
     "Stink bug damage during pod fill; plant in well-drained soil to avoid root rot.",
     "Pods are plump and bright green; seeds fill out the pod.",
     "Best eaten fresh; blanch and freeze within a day of harvest."),

    ("ミニトマト", "Cherry Tomato",
     "Water when topsoil dries. Inconsistent watering causes fruit cracking.",
     "Full sun, 6+ hours daily.",
     "Fruit cracking from sudden heavy rain; remove lateral shoots regularly.",
     "Fruit turns fully red or its variety color and detaches easily.",
     "Store at room temperature for up to 1 week; refrigerate once stem removed."),

    ("おくら", "Okra",
     "Water generously; drought causes poor pod development.",
     "Full sun; heat-loving crop.",
     "Pods become tough and fibrous if left too long — harvest every 2 days.",
     "Pod is 5–7 cm long and tender; tip bends easily.",
     "Refrigerate in a bag for up to 3 days; slice and freeze for longer storage."),

    ("ナス", "Eggplant",
     "Water deeply and consistently; moisture stress causes bitter fruit.",
     "Full sun, 6+ hours daily.",
     "Aphids and spider mites; hard 'stone' fruit from heat or drought stress.",
     "Skin is deep purple and glossy; flesh yields slightly to gentle press.",
     "Wrap in paper towel, refrigerate for up to 1 week; avoid cold below 10 °C."),

    ("とうもろこし", "Corn",
     "Water deeply, especially during silking and ear-filling.",
     "Full sun.",
     "Corn earworm; poor pollination if planted in a single row — plant in blocks.",
     "Silks turn brown and dry; kernels are plump and milky when pierced.",
     "Refrigerate immediately; best eaten within 1–2 days of harvest."),

    ("落花生", "Peanut",
     "Water when topsoil dries; reduce after flowering.",
     "Full sun.",
     "Poor pod development in hard soil; mound soil over base after flowering.",
     "Leaves turn yellow in autumn; dig up and check a few pods.",
     "Dry in sun for 2–3 weeks; store in cool dry place for months."),

    ("モロヘイヤ", "Molokhia (Jute Mallow)",
     "Water when topsoil dries; drought-tolerant once established.",
     "Full sun; heat-loving.",
     "Harvest before flowering — seeds and mature flowers are toxic.",
     "Leaves are glossy and tender before flower buds form.",
     "Blanch and freeze; fresh leaves last 2–3 days refrigerated."),

    ("ジャガイモ", "Potato",
     "Water when topsoil dries; reduce after stems begin to yellow.",
     "Full sun.",
     "Greening if tubers exposed to light — hill soil regularly; late blight in wet weather.",
     "Leaves and stems turn yellow and die back.",
     "Store in cool, dark, ventilated place for several months."),

    ("サツマイモ", "Sweet Potato",
     "Minimal watering once established; drought-tolerant.",
     "Full sun.",
     "Lush vine growth with poor tubers ('vine lushness') from excess nitrogen.",
     "Dig up a trial root in autumn; skin is set and roots are large.",
     "Cure at 30 °C for 4–5 days; store in cool dry place for months."),

    ("ヤマイモ（長いも）", "Japanese Mountain Yam",
     "Water when topsoil dries; avoid waterlogging.",
     "Full sun.",
     "Forked tubers in hard soil; dig bed deeply (60+ cm) before planting.",
     "Leaves yellow and stems die back in late autumn.",
     "Store unpeeled in cool dry place for several months."),

    ("サトイモ", "Taro",
     "Keep soil consistently moist; prefers humid conditions.",
     "Partial shade; tolerates low light.",
     "Root rot in waterlogged soil; cover corms well to prevent frost damage.",
     "Leaves yellow and die back in autumn.",
     "Store in cool, dry, frost-free place; do not refrigerate."),

    ("ニンニク", "Garlic",
     "Water when topsoil dries; reduce completely 2 weeks before harvest.",
     "Full sun.",
     "Bulb splitting from delayed harvest; rust disease in wet conditions.",
     "About half the leaves turn yellow; dig a test bulb to check size.",
     "Hang in bunches in well-ventilated shade to cure; lasts several months."),

    ("玉ねぎ", "Onion",
     "Water when topsoil dries; stop completely when necks begin to soften.",
     "Full sun.",
     "Bolting in cold spells after transplant; neck rot if harvested in wet weather.",
     "Top falls over naturally; necks soften and lie flat.",
     "Cure in sun for 1–2 weeks; hang in net bags in ventilated shade for months."),

    ("ネギ", "Japanese Bunching Onion (Negi)",
     "Water when topsoil dries; drought-tolerant once established.",
     "Full sun to partial shade.",
     "Root rot in waterlogged soil; mound soil regularly for blanching.",
     "Harvest when stalks are 30+ cm and firm.",
     "Wrap in newspaper, refrigerate for up to 2 weeks; freeze sliced."),

    ("白菜", "Napa Cabbage (Chinese Cabbage)",
     "Water consistently; dry conditions prevent head formation.",
     "Full sun.",
     "Caterpillar damage; head fails to form if temperatures stay above 25 °C.",
     "Head feels firm and heavy; outer leaves are slightly pale green.",
     "Wrap in newspaper, store in cool place for several weeks; refrigerate once cut."),
]

# ------------------------------------------------------------------
# glossary: (term, plain_en)
# ------------------------------------------------------------------
GLOSSARY_EN = {
    "青枯病":     "Bacterial wilt — soil-borne bacteria block water transport, causing plants to wilt and die rapidly despite moist soil.",
    "疫病":      "Late blight — fungal-like pathogen causing dark, water-soaked lesions on leaves and fruit, spreads rapidly in wet weather.",
    "半身萎凋病":  "Verticillium wilt — fungal disease that blocks vascular tissue on one side of the plant, causing half the plant to wilt.",
    "根こぶ病":   "Clubroot — soil-borne pathogen that causes swollen, distorted roots in brassicas; spreads in acidic, wet soil.",
    "うどんこ病":  "Powdery mildew — fungal disease coating leaves in white powder; thrives in dry conditions with high humidity.",
    "べと病":    "Downy mildew — fungal-like disease causing yellow patches on upper leaf surface with grey mold beneath; spreads in cool, moist weather.",
    "軟腐病":    "Soft rot — bacterial disease causing soft, foul-smelling decay, usually from wounds or waterlogged soil.",
    "炭疽病":    "Anthracnose — fungal disease causing dark, sunken lesions on fruit and stems; spreads in warm, wet conditions.",
    "ソウカ病":   "Common scab — bacterial disease causing rough, corky patches on potato skin; worse in alkaline, dry soil.",
    "蔓割病":    "Fusarium wilt — soil-borne fungus that infects roots and blocks water, causing vines to wilt; linked to crop rotation failure.",
    "根茎腐敗病":  "Rhizome rot — bacterial or fungal decay of underground stems (rhizomes), common in overly moist soil.",
    "チップバーン": "Tip burn — calcium-deficiency symptom causing brown, papery leaf edges; caused by rapid growth or inconsistent watering.",
    "アブラムシ":  "Aphid — tiny sap-sucking insects that cluster on new growth, transmit viruses, and attract ants.",
    "ハダニ":    "Spider mite — microscopic mites that cause silvery stippling on leaves; thrive in hot, dry conditions.",
    "アオムシ":   "Cabbage white caterpillar — green larva of the cabbage white butterfly; chews large holes in brassica leaves.",
    "コナガ":    "Diamondback moth — small moth whose larvae make small holes in brassica leaves; highly pesticide-resistant.",
    "アワノメイガ": "Asian corn borer — moth larva that bores into corn stalks and ears, causing them to snap or rot.",
    "カメムシ":   "Stink bug — shield-shaped bug that sucks plant sap, causing discolored spots on fruit and seeds.",
    "ネキリムシ":  "Cutworm — moth larva that lives in soil and cuts seedlings at the base overnight.",
    "キスジノミハムシ": "Striped flea beetle — small jumping beetle that chews tiny holes in brassica leaves, especially seedlings.",
    "ハマキムシ":  "Leafroller — moth larva that rolls leaves and feeds inside; mainly affects okra and fruit trees.",
    "連作障害":   "Crop rotation problem — yield loss and disease buildup from growing the same crop family in the same soil year after year.",
    "とう立ち":   "Bolting — premature flowering triggered by heat or long days; makes leaves tough and bitter.",
    "播種":     "Sowing — the act of planting seeds directly into soil or seed trays.",
    "定植":     "Transplanting — moving seedlings grown in trays or pots into their final growing position.",
    "元肥":     "Basal fertilizer — fertilizer mixed into the soil before planting to provide nutrients throughout the growing season.",
    "追肥":     "Top dressing — fertilizer applied to growing plants during the season to supplement nutrients.",
    "つるぼけ":   "Vine lushness — excessive leafy growth with poor fruit or tuber production, usually from too much nitrogen.",
    "又根":     "Forked root — a root vegetable that splits into two or more branches, usually from stony or compacted soil.",
    "倒伏":     "Lodging — plants falling over from wind, rain, or weak stems; common in tall crops like corn.",
    "石ナス":    "Stone eggplant — hard, bitter eggplant caused by heat stress, drought, or poor pollination.",
    "ほ場":     "Cultivation field — an outdoor plot of land used for growing crops; as opposed to containers or raised beds.",
    "萌芽":     "Sprouting — the initial emergence of shoots from seeds, bulbs, or tubers.",
    "子房柄":    "Peg (peanut) — the stalk that grows downward from a fertilized peanut flower to bury the developing pod in the soil.",
    "軟白":     "Blanching — excluding light from stems (e.g., leeks) by mounding soil to produce white, tender stalks.",
    "リビングマルチ": "Living mulch — low-growing plants used as ground cover beneath taller crops to retain moisture, suppress weeds, and reduce pests.",
    "苦土石灰":   "Dolomitic lime — calcium-magnesium carbonate used to raise soil pH and supply magnesium; applied before planting.",
    "過リン酸石灰": "Superphosphate — phosphorus-rich fertilizer that promotes root development and flowering.",
    "pH":      "Soil pH — measure of soil acidity or alkalinity on a scale of 1–14; most vegetables prefer 6.0–7.0.",
    "団粒構造":   "Aggregate soil structure — crumbly, well-aerated soil with clusters of particles that retain moisture and allow drainage.",
    "BT剤":    "BT insecticide — biological pesticide made from Bacillus thuringiensis bacteria; kills caterpillars without harming bees or mammals.",
    "木酢液":    "Wood vinegar — liquid byproduct of charcoal production; used diluted as a natural pest repellent and soil conditioner.",
    "防虫ネット":  "Insect-proof net — fine mesh netting placed over crops to physically block insects while allowing air and light through.",
    "コンパニオンプランツ": "Companion planting — growing two or more plant species together for mutual benefit such as pest repulsion or growth promotion.",
    "アリシン":   "Allicin — sulfur compound in garlic and onions responsible for their pungent smell; repels aphids, spider mites, and some soil pathogens.",
    "フィトンチッド": "Phytoncide — volatile compounds released by plants that repel insects or inhibit nearby plant or microbial growth.",
    "根粒菌":    "Rhizobium — nitrogen-fixing bacteria that live in root nodules of legumes and convert atmospheric nitrogen into a form plants can use.",
    "窒素固定":   "Nitrogen fixation — the conversion of atmospheric nitrogen gas into ammonia by soil bacteria, making it available as plant nutrition.",
    "拮抗菌":    "Antagonistic bacteria — beneficial soil microbes that compete with or suppress disease-causing pathogens around plant roots.",
    "根圏":     "Rhizosphere — the zone of soil immediately surrounding plant roots, rich in root secretions and microbial activity.",
    "忌避":     "Repellency — the effect of a smell or substance that deters insects or animals from approaching a plant.",
    "アレロパシー": "Allelopathy — the release of chemicals by a plant that inhibit or stimulate the growth of neighboring plants.",
}


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # crop_categories
    for ja, en in CATEGORIES_EN.items():
        conn.execute("UPDATE crop_categories SET name_en=? WHERE name=?", [en, ja])

    # grow_environments
    for ja, en in ENVIRONMENTS_EN.items():
        conn.execute("UPDATE grow_environments SET name_en=? WHERE name=?", [en, ja])

    # pests
    for ja, en in PESTS_EN.items():
        conn.execute("UPDATE pests SET name_en=? WHERE name=?", [en, ja])

    # pest_controls
    for ja, en in PEST_CONTROLS_EN.items():
        conn.execute("UPDATE pest_controls SET name_en=? WHERE name=?", [en, ja])

    # fertilizers
    for ja, en in FERTILIZERS_EN.items():
        conn.execute("UPDATE fertilizers SET name_en=? WHERE name=?", [en, ja])

    # crops
    for row in CROPS_EN:
        name, name_en, watering_en, sunlight_en, failure_points_en, harvest_sign_en, storage_en = row
        conn.execute("""
            UPDATE crops SET
                name_en=?, watering_en=?, sunlight_en=?,
                failure_points_en=?, harvest_sign_en=?, storage_en=?
            WHERE name=?
        """, [name_en, watering_en, sunlight_en, failure_points_en, harvest_sign_en, storage_en, name])

    # glossary
    for term, plain_en in GLOSSARY_EN.items():
        conn.execute("UPDATE glossary SET plain_en=? WHERE term=?", [plain_en, term])

    conn.commit()

    # 確認
    crops_done    = conn.execute("SELECT COUNT(*) FROM crops WHERE name_en IS NOT NULL").fetchone()[0]
    glossary_done = conn.execute("SELECT COUNT(*) FROM glossary WHERE plain_en IS NOT NULL").fetchone()[0]
    conn.close()

    print(f"crops    : {crops_done}/30 件更新")
    print(f"glossary : {glossary_done}/52 件更新")
    print("完了")


if __name__ == "__main__":
    main()
