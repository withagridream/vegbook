"""
作物データ補完スクリプト
出典: FAO Crop Information, 農研機構, 農水省, Wikipedia CC BY-SA
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'vegbook.db'

# -------------------------------------------------------------------
# 補完データ辞書
# キー: crops.name
# フィールド: temp_min, temp_max, sunlight, watering, planter_size,
#             rotation_years, failure_points, days_to_harvest (未設定分),
#             yield_per_plant, storage, harvest_sign
# -------------------------------------------------------------------
CROP_DATA = {
    "シシトウ": {
        "temp_min": 20, "temp_max": 30,
        "sunlight": "直射日光6時間以上。日照不足は着果不良の原因",
        "watering": "乾燥に弱い。土の表面が乾き始めたら与える。真夏は朝夕2回",
        "planter_size": "深さ30cm以上、容量20L以上の深型プランター",
        "rotation_years": 3,
        "failure_points": "連作障害（疫病・青枯病）。乾燥による落花・落果。高温期の水切れで辛くなりやすい",
        "yield_per_plant": "1株あたり50〜100個",
        "storage": "冷蔵庫の野菜室で約1週間。冷凍保存（1ヶ月）は加熱前提",
        "harvest_sign": "花が落ちて5〜7日後、5〜7cm程度で収穫。大きくなると種が硬くなる",
    },
    "ほうれん草": {
        "temp_min": 5, "temp_max": 20,
        "sunlight": "日当たりの良い場所が理想。半日陰でも栽培可能",
        "watering": "土の表面が乾いたら与える。過湿・乾燥ともに嫌う",
        "planter_size": "深さ15cm以上のプランター。プランター1本で20〜30株",
        "rotation_years": 1,
        "failure_points": "pH6.5以下の酸性土壌では生育不良（石灰で中和必須）。高温期の早期とう立ち。密植による蒸れ",
        "yield_per_plant": "1株約30〜50g",
        "storage": "根を濡らしたキッチンペーパーで包み冷蔵庫で3〜5日。茹でて冷凍保存可（1ヶ月）",
        "harvest_sign": "草丈25〜30cm。葉が大きく広がり、下葉が地面に触れる頃が目安",
    },
    "ピーマン": {
        "temp_min": 20, "temp_max": 30,
        "sunlight": "直射日光6時間以上必要",
        "watering": "土が乾いたらたっぷり与える。高温期は朝の水やりが基本",
        "planter_size": "深さ30cm以上、容量15〜20Lのプランター",
        "rotation_years": 3,
        "failure_points": "連作障害（疫病・青枯病）。低温・曇天での受粉不良。カメムシによる果実の着色不良",
        "yield_per_plant": "1株あたり40〜80個",
        "storage": "冷蔵庫の野菜室で約1週間。冷凍保存は生のままスライスして",
        "harvest_sign": "開花後約2週間、果実が6〜7cmになったら収穫。実が固く張りのある状態",
    },
    "まくわうり": {
        "temp_min": 22, "temp_max": 35,
        "sunlight": "直射日光を1日8時間以上確保する",
        "watering": "乾燥気味管理。着果後は適度な水分を保ち、収穫10日前から徐々に控える",
        "planter_size": "深さ30cm以上、容量30L以上の大型プランター。つる誘引用の支柱が必要",
        "rotation_years": 3,
        "failure_points": "連作障害（蔓割病）。低温時の着果不良。収穫直前の過湿による裂果",
        "yield_per_plant": "1株あたり3〜5個",
        "storage": "常温で1〜2週間。切った後は冷蔵で3〜4日",
        "harvest_sign": "果皮の地色が黄緑から黄色に変わり、甘い芳香がする。果柄付近にひびが入り始める",
    },
    "レタス": {
        "temp_min": 10, "temp_max": 20,
        "sunlight": "半日陰でも育つが、日当たりが良い方が充実した株になる",
        "watering": "土の表面が乾いたらたっぷりと。過湿は腐敗の原因",
        "planter_size": "深さ15〜20cm、幅60cm程度のプランターで3〜4株",
        "rotation_years": 1,
        "failure_points": "高温（20℃超）によるとう立ち。夏の直播きは困難。チップバーン（カルシウム欠乏による葉先の褐変）",
        "yield_per_plant": "1株約200〜300g",
        "storage": "芯をくり抜き濡れたキッチンペーパーを詰めて冷蔵3〜5日",
        "harvest_sign": "外葉を押して固く締まっていたら結球完成の目安（玉レタス共通）",
    },
    "にんじん": {
        "temp_min": 15, "temp_max": 25,
        "sunlight": "日当たりの良い場所。日照不足は根の肥大が悪くなる",
        "watering": "土が乾いたらたっぷりと。発芽まで土を乾かさないことが最重要",
        "planter_size": "深さ30cm以上のプランター。間引きしながら株間10cm確保",
        "rotation_years": 1,
        "failure_points": "発芽率が低い（発芽まで土を乾かさない）。間引き不足による細い根。土の石・硬盤による又根",
        "yield_per_plant": "1株あたり1本、重さ100〜200g",
        "storage": "土付きのまま新聞紙に包み冷暗所で1〜2ヶ月。洗ったものは冷蔵1〜2週間",
        "harvest_sign": "根の肩の直径が3〜4cmになり、葉の色が濃くなる頃。葉が開き始めたら収穫を急ぐ",
    },
    "カブ": {
        "temp_min": 10, "temp_max": 20,
        "sunlight": "日当たりの良い場所。半日陰でも可能だが根が小さくなる",
        "watering": "乾燥に弱い。土の表面が乾いたら都度与える",
        "planter_size": "深さ20cm以上のプランター。株間10〜15cm",
        "rotation_years": 1,
        "failure_points": "アブラナ科の連作障害（根こぶ病）。間引き不足による偏った形。高温期の根の割れ",
        "yield_per_plant": "1株あたり1個、重さ200〜500g（品種による）",
        "storage": "葉を切り離し、冷蔵庫で1〜2週間",
        "harvest_sign": "根の直径が小カブで5〜6cm、大カブで10〜15cmになったら収穫",
    },
    "ダイコン": {
        "temp_min": 10, "temp_max": 20,
        "sunlight": "日当たりの良い場所が最適",
        "watering": "土が乾いたらたっぷりと。水切れは根割れの原因",
        "planter_size": "深さ40〜50cm以上の深型プランター（底の深さが最重要）。1鉢1本植え",
        "rotation_years": 1,
        "failure_points": "土に石や未熟有機物があると又根・岐根になる。アブラナ科連作による根こぶ病。水の不均等給水による根割れ",
        "yield_per_plant": "1本あたり400〜800g",
        "storage": "葉を切り離し新聞紙に包んで冷蔵庫で1〜2週間。冷暗所で立てて保存も可",
        "harvest_sign": "根の上部（肩）が直径6〜7cm。葉が緑で艶やかなうちに収穫（放置すると辛くなる）",
    },
    "小松菜": {
        "temp_min": 5, "temp_max": 25,
        "sunlight": "日当たりの良い場所が理想。半日陰でも育つ",
        "watering": "土の表面が乾いたら与える。夏は朝の水やりが基本",
        "planter_size": "深さ15cm以上のプランター。条間10〜15cmで2〜3条まき",
        "rotation_years": 1,
        "failure_points": "アブラナ科の連作による根こぶ病。アオムシ・コナガの食害（防虫ネット推奨）。夏のとう立ち",
        "yield_per_plant": "1株約100〜150g",
        "storage": "冷蔵庫の野菜室で3〜5日。茹でて冷凍保存可（1ヶ月）",
        "harvest_sign": "草丈20〜25cmになったら収穫適期。根元から株ごと抜くか、外葉から切り取る",
    },
    "玉レタス": {
        "temp_min": 10, "temp_max": 20,
        "sunlight": "日当たりの良い場所。高温期は半日陰での栽培が有効",
        "watering": "土の表面が乾いたらたっぷりと。葉が重なってからは中心部への水やりは避ける",
        "planter_size": "深さ20〜25cm、幅60cm以上のプランターで2〜3株",
        "rotation_years": 1,
        "failure_points": "高温によるとう立ち・苦味の増加。結球前の高温で結球しない。チップバーン（カルシウム欠乏）",
        "yield_per_plant": "1株約300〜500g",
        "storage": "芯をくり抜き濡れたキッチンペーパーを詰め、ポリ袋に入れて冷蔵4〜5日",
        "harvest_sign": "上から押して固く締まっていたら収穫。外葉が少し下に垂れてくるのも目安",
    },
    "キャベツ": {
        "temp_min": 10, "temp_max": 20,
        "sunlight": "日当たりの良い場所が必要",
        "watering": "土が乾いたらたっぷりと。結球期は水切れさせない",
        "planter_size": "深さ30cm、幅60cm以上のプランターで1〜2株",
        "rotation_years": 2,
        "failure_points": "アオムシ・コナガによる食害（定植直後から防虫ネット必須）。根こぶ病（連作回避）。過密栽培による蒸れ",
        "yield_per_plant": "1株約1〜2kg",
        "storage": "芯をくり抜き濡れたキッチンペーパーを詰めて冷蔵1〜2週間。外葉を剥がしながら使用",
        "harvest_sign": "球を上から押して固く締まったら収穫。1〜1.5kg程度が食べごろ",
    },
    "きゅうり": {
        "temp_min": 18, "temp_max": 30,
        "sunlight": "直射日光6時間以上必要。半日陰では着果不良",
        "watering": "乾燥に弱い。土の表面が乾いたら朝と夕方の2回。プランターは特に乾きやすいため要注意",
        "planter_size": "深さ30cm以上、容量20L以上。ネット・支柱必須",
        "rotation_years": 3,
        "failure_points": "うどんこ病（風通し改善）。べと病（過湿回避）。連作による土壌病害。着果後の急速な成長で収穫遅れが続くと株が弱る",
        "yield_per_plant": "1株あたり20〜40本",
        "storage": "冷蔵庫の野菜室で3〜5日。乾燥を防ぐためラップ包みか袋入り",
        "harvest_sign": "開花後7〜10日、長さ20〜22cmで収穫。大きくなりすぎると種が硬くなり食味が落ちる",
    },
    "スティックセニョール": {
        "temp_min": 15, "temp_max": 25,
        "sunlight": "日当たりの良い場所が必要",
        "watering": "土が乾いたらたっぷりと。多湿では腐りやすい",
        "planter_size": "深さ30cm以上、容量20L以上のプランター。1本植え",
        "rotation_years": 2,
        "failure_points": "アオムシ・コナガの食害（定植直後から防虫ネット）。アブラナ科連作による根こぶ病。収穫タイミングが遅れると花が開いて食味が落ちる",
        "yield_per_plant": "メインのわき芽から10〜20本程度",
        "storage": "冷蔵庫の野菜室で3〜5日。茹でて冷凍保存可（1ヶ月）",
        "harvest_sign": "茎の直径1cm前後、長さ15〜20cmで収穫。花蕾が固く締まっているうちに",
    },
    "しょうが": {
        "temp_min": 20, "temp_max": 30,
        "sunlight": "半日陰でも育つ。強い直射日光で葉が焼けることがある",
        "watering": "乾燥に弱い。土の表面が乾いたらすぐに与える。梅雨明け後は特にこまめに",
        "planter_size": "深さ30cm以上、容量20L以上の深型プランター",
        "rotation_years": 4,
        "failure_points": "連作による根茎腐敗病（最低4年輪作）。低温・乾燥による芽が出ない。排水不良による根腐れ",
        "yield_per_plant": "1株あたり200〜500g（種ショウガ込みの増殖分）",
        "storage": "常温の冷暗所で土付きのまま数ヶ月。切り口をラップして冷蔵1〜2週間",
        "harvest_sign": "葉が黄色く枯れ始めた頃（晩秋）が根ショウガの収穫適期。新ショウガは夏〜初秋に収穫可能",
    },
    "エダマメ": {
        "temp_min": 20, "temp_max": 30,
        "sunlight": "直射日光6時間以上必要",
        "watering": "開花期と豆の膨らみ始めの時期に水切れさせない。それ以外は乾燥気味でも可",
        "planter_size": "深さ30cm以上、容量20L以上のプランター。株間20〜25cm",
        "rotation_years": 3,
        "failure_points": "カメムシによる豆の吸汁被害（防虫ネット有効）。過湿による根腐れ・窒素過多でつるぼけ。収穫が遅れるとすぐに硬くなる",
        "yield_per_plant": "1株あたり20〜40莢",
        "storage": "さやごと塩茹でして冷凍保存（1ヶ月）。生のままは鮮度が落ちやすく当日中が望ましい",
        "harvest_sign": "莢が膨らみ、中の豆が莢の幅いっぱいになったら収穫。開花から45〜50日が目安",
    },
    "ミニトマト": {
        "temp_min": 18, "temp_max": 25,
        "sunlight": "直射日光6時間以上必要。日照不足は着果不良・裂果の原因",
        "watering": "乾燥気味に管理。実が熟し始めたら灌水を減らすと糖度が上がる。プランターは乾きやすいため毎日チェック",
        "planter_size": "深さ30cm以上、容量20〜30Lのプランター。支柱・誘引紐必須",
        "rotation_years": 3,
        "failure_points": "尻腐れ（カルシウム不足・水管理ミス）。裂果（急激な水分過多）。アブラムシ・ハダニ。連作による青枯病・萎凋病",
        "yield_per_plant": "1株あたり100〜200個",
        "storage": "常温で3〜5日（ヘタを下に置く）。完熟したものは冷蔵3〜5日",
        "harvest_sign": "果実全体が均一に赤（または品種の指定色）になり、軽く触れてほんのり柔らかくなったら収穫",
    },
    "おくら": {
        "temp_min": 22, "temp_max": 35,
        "sunlight": "直射日光8時間以上。高温を好む。日照不足は着果不良",
        "watering": "乾燥に強いが、土が白く乾いたらたっぷりと。夏の高温期は朝の水やりが基本",
        "planter_size": "深さ30cm以上、容量15〜20Lのプランター。株間30cm",
        "rotation_years": 1,
        "failure_points": "低温（15℃以下）では生育が止まる。収穫が遅れるとすぐ硬くなる（毎日収穫が必要）。ハマキムシ・アブラムシの被害",
        "yield_per_plant": "1株あたり50〜100個",
        "storage": "1本ずつラップして冷蔵2〜3日。冷凍（茹でて）1ヶ月",
        "harvest_sign": "開花後5〜7日、長さ8〜10cmで収穫。10cmを超えると筋が硬くなり食味が落ちる",
    },
    "ナス": {
        "temp_min": 22, "temp_max": 30,
        "sunlight": "直射日光8時間以上。日陰では着果しにくい",
        "watering": "水を大量に必要とする。土の表面が乾いたら朝夕たっぷりと。高温期の水切れで石ナスになる",
        "planter_size": "深さ35cm以上、容量20〜30Lの大型プランター。支柱必須",
        "rotation_years": 4,
        "failure_points": "連作による青枯病・半身萎凋病（最重要）。高温期の水切れで石ナス（硬い実）。アブラムシ・ハダニ被害。うどんこ病",
        "yield_per_plant": "1株あたり30〜50個",
        "storage": "乾燥と低温に弱い。冷蔵庫は10℃以上に保ち2〜5日。常温は翌日中が目安",
        "harvest_sign": "へたの下の白い部分（白いライン）が消えて全体が紫黒色になり、艶が出たら収穫。中長ナスは12〜15cm",
    },
    "とうもろこし": {
        "temp_min": 20, "temp_max": 30,
        "sunlight": "直射日光を1日8時間以上確保する",
        "watering": "乾燥に弱い。雄穂の開花期と受粉後（粒の充実期）に特に水切れさせない",
        "planter_size": "深さ40cm以上、容量30L以上の大型プランター。風媒花のため複数本植えが必須（人工授粉も可）",
        "rotation_years": 1,
        "failure_points": "単体栽培では受粉が不十分で実が入らない（3〜4本以上が目安）。アワノメイガの幼虫による穂の食害。水切れによる粒の不揃い",
        "yield_per_plant": "1株あたり1〜2本",
        "storage": "鮮度が急速に落ちる。収穫後すぐに茹でて冷蔵2〜3日か冷凍（1ヶ月）",
        "harvest_sign": "絹糸（ひげ）が茶色くなり始め、皮の上から触ると粒が均等に並んでいる状態。開花後22〜25日が目安",
    },
    "落花生": {
        "temp_min": 20, "temp_max": 30,
        "sunlight": "直射日光8時間以上。日照不足は莢の実入りが悪くなる",
        "watering": "乾燥気味に管理。過湿は根腐れと土中の莢の腐敗の原因",
        "planter_size": "深さ30cm以上、容量20L以上のプランター。株間30cm",
        "rotation_years": 2,
        "failure_points": "排水不良の土壌では莢が腐る。土寄せを怠ると子房柄（ぺグ）が土に刺さらず実がつかない。マメシンクイガの食害",
        "yield_per_plant": "1株あたり30〜50莢",
        "storage": "生落花生は冷蔵1週間。乾燥させれば常温で数ヶ月〜1年",
        "harvest_sign": "茎が少し黄ばみ始め、莢の内側の網目が濃くなり、粒がしっかり詰まったら収穫（9〜10月）",
    },
    "モロヘイヤ": {
        "temp_min": 25, "temp_max": 35,
        "sunlight": "直射日光が必要。高温・強光を好む",
        "watering": "乾燥に強い。土が完全に乾いたら与える。過湿は禁物",
        "planter_size": "深さ30cm以上、容量15〜20Lのプランター",
        "rotation_years": 1,
        "failure_points": "低温（15℃以下）では生育停止。種・未熟莢・樹液に毒性成分（ストロファンチジン）を含むため絶対に食べない。葉だけ食べること",
        "yield_per_plant": "1株から繰り返し収穫可能。1シーズン合計300〜500g",
        "storage": "冷蔵2〜3日。ネバネバが強くなる前に使い切る。茹でて冷凍可（1ヶ月）",
        "harvest_sign": "草丈が50cm以上になり、葉が十分に展開したら先端15〜20cmを摘み取り収穫",
    },
    "ジャガイモ": {
        "temp_min": 15, "temp_max": 20,
        "sunlight": "日当たりの良い場所が必要。日照不足はイモの肥大不良",
        "watering": "乾燥気味管理。過湿は疫病・腐敗の原因。花が咲き始めから結実期は水をやや多めに",
        "planter_size": "深さ35〜40cm以上、容量30L以上の大型プランター。袋栽培も人気",
        "rotation_years": 4,
        "failure_points": "連作による疫病・ソウカ病（石灰を入れすぎるとソウカ病が増える）。緑化したイモにはソラニン（毒）が含まれるため光を遮断する土寄せが必須。萌芽後の遅霜被害",
        "yield_per_plant": "1株あたり5〜10個、合計500g〜1kg",
        "storage": "新聞紙に包んで冷暗所で1〜2ヶ月。光に当てると毒性成分（ソラニン）が生成する",
        "harvest_sign": "葉が黄色くなり、茎が倒れ始めたら収穫適期（植え付けから約90〜100日）",
    },
    "サツマイモ": {
        "temp_min": 20, "temp_max": 30,
        "sunlight": "直射日光8時間以上。高温多日照を好む",
        "watering": "乾燥に強い。基本的に不要（梅雨明け以降はほぼ無潅水）。過湿は根腐れの原因",
        "planter_size": "深さ30〜40cm以上、幅の広い大型プランターか袋栽培推奨（つるが伸びる）",
        "rotation_years": 1,
        "failure_points": "窒素過多でつるぼけ（葉ばかり茂ってイモが太らない）。苗の植え付け時の水やりが不足すると活着しない。収穫が遅すぎると食味が落ちる",
        "yield_per_plant": "1株あたり3〜5個（合計500g〜1.5kg）",
        "storage": "常温（13〜15℃の冷暗所）で2〜3ヶ月。低温（10℃以下）は腐りやすくなるため冷蔵庫不可",
        "harvest_sign": "茎が枯れ始め、葉が黄変してきたら収穫適期（植え付けから120〜130日）。試し掘りで確認",
    },
    "ヤマイモ（長いも）": {
        "temp_min": 20, "temp_max": 30,
        "sunlight": "日当たりの良い場所。半日陰でも育つが収量が落ちる",
        "watering": "土が乾いたら与える。過湿は塊根の腐敗原因",
        "planter_size": "深さ60〜90cmの深型コンテナか袋栽培。専用のパイプ栽培も効果的",
        "rotation_years": 2,
        "failure_points": "土が浅いと塊根が曲がる（深い土が絶対条件）。カスリダニによる葉の食害。炭疽病（風通し改善）。触れると肌がかゆくなるシュウ酸カルシウムを含む",
        "yield_per_plant": "1株あたり300g〜1kg",
        "storage": "切り口をラップして冷蔵1〜2週間。または土に埋めて冷暗所で数ヶ月",
        "harvest_sign": "地上部の葉が完全に黄変・枯れたら収穫適期（晩秋〜冬）",
    },
    "サトイモ": {
        "temp_min": 20, "temp_max": 30,
        "sunlight": "半日陰でも育つ。強い直射日光は葉が焼けることがある",
        "watering": "乾燥に弱い。土の表面が乾いたらすぐ水やり。梅雨明け以降は特に多量の水が必要",
        "planter_size": "深さ40cm以上、容量30L以上の大型プランター。1鉢1株",
        "rotation_years": 3,
        "failure_points": "乾燥（水切れで球が充実しない）。連作による疫病・軟腐病。植え付け時の低温でなかなか芽が出ない（5月以降の植え付けが確実）",
        "yield_per_plant": "1株（親芋+子芋+孫芋）で合計1〜3kg",
        "storage": "10℃以上の冷暗所で土付きのまま2〜3ヶ月。低温障害に注意（冷蔵庫は使わない）",
        "harvest_sign": "地上部の葉が黄変・枯れたら収穫適期（10〜11月）。霜が降りる前に掘り出す",
    },
    "ニンニク": {
        "temp_min": 10, "temp_max": 20,
        "sunlight": "日当たりの良い場所が必要",
        "watering": "乾燥気味管理。球肥大期（4〜5月）は水を多めに。収穫1ヶ月前から控える",
        "planter_size": "深さ25cm以上のプランター。株間15cm",
        "rotation_years": 3,
        "failure_points": "鱗片の向きを揃えて植える（尖った方を上に）。連作による白色疫病・乾腐病。過湿による腐れ。肥大不足（窒素・追肥管理）",
        "yield_per_plant": "1球から5〜8片の収穫",
        "storage": "収穫後2週間吊り干し乾燥させれば常温で3〜4ヶ月。冷凍保存（薄皮をむいてラップ）で6ヶ月",
        "harvest_sign": "葉の半数が黄変・枯れてきた頃（5〜6月）。葉が完全に枯れる前に収穫しないと球がバラバラになる",
    },
    "玉ねぎ": {
        "temp_min": 10, "temp_max": 20,
        "sunlight": "日当たりの良い場所が必要",
        "watering": "乾燥気味管理。球肥大期は土が乾きすぎないよう注意。収穫2週間前から水やり停止",
        "planter_size": "深さ20cm以上のプランター。株間10〜15cm",
        "rotation_years": 2,
        "failure_points": "苗の太さ管理（細すぎ＝生育不良、太すぎ＝早期とう立ち）。トウ立ち（花芽分化後の低温刺激）。軟腐病・さび病（過湿回避）",
        "yield_per_plant": "1球あたり200〜500g",
        "storage": "収穫後2〜3週間吊り干しで乾燥させれば常温で3〜6ヶ月。早生品種は早めに消費",
        "harvest_sign": "葉が自然に倒れ（倒伏）、根元が完全に倒れたら収穫。全体の8割が倒伏したタイミングで収穫開始",
    },
    "ネギ": {
        "temp_min": 10, "temp_max": 25,
        "sunlight": "日当たりの良い場所が最適。半日陰でも育つが軟弱になる",
        "watering": "乾燥に強い。土が乾いたらたっぷりと。過湿は根腐れの原因",
        "planter_size": "深さ30cm以上のプランター。深ねぎは土寄せの際に増し土できるよう大型容器推奨",
        "rotation_years": 2,
        "failure_points": "連作によるネギ萎縮病・根腐れ。アザミウマ（スリップス）による被害。ネギは根が浅いため台風などで倒れやすい",
        "yield_per_plant": "1株（分げつ後）から3〜5本収穫",
        "storage": "根付きのまま土に刺して保存（2〜3週間）。または洗って冷蔵4〜5日。刻んで冷凍も可",
        "harvest_sign": "根深ねぎは白い軟白部分が20〜30cmになったら。葉ネギは草丈40〜50cm程度で外側から収穫",
    },
    "白菜": {
        "temp_min": 10, "temp_max": 20,
        "sunlight": "日当たりの良い場所が必要",
        "watering": "乾燥に弱い。土の表面が乾いたらたっぷりと。結球後は水をやや控えめに",
        "planter_size": "深さ30cm以上、容量30L以上の大型プランター。1鉢1株",
        "rotation_years": 2,
        "failure_points": "アオムシ・コナガによる定植直後の食害（防虫ネット必須）。高温による結球不良（秋まき厳守）。軟腐病（排水改善）",
        "yield_per_plant": "1株あたり2〜4kg",
        "storage": "丸ごとなら新聞紙に包んで冷暗所で1〜2ヶ月。カットしたものは冷蔵1週間",
        "harvest_sign": "上から押して固く締まったら収穫。球の高さが30〜40cm、重さ2kg以上が目安",
    },
}

# -------------------------------------------------------------------
# 追加する肥料データ（作物名 → [{name, availability, ratio}]）
# -------------------------------------------------------------------
FERTILIZER_DATA = {
    "共通元肥": [
        {"name": "完熟堆肥",      "availability": 2, "ratio": "元肥として1㎡あたり2〜3kg"},
        {"name": "化成肥料8-8-8", "availability": 2, "ratio": "元肥として1㎡あたり50g"},
    ],
    "果菜類追肥": [
        {"name": "液体肥料（ハイポネックス）", "availability": 2, "ratio": "2週間に1回1000倍希釈で追肥"},
    ],
    "葉菜類追肥": [
        {"name": "化成肥料8-8-8", "availability": 2, "ratio": "2〜3週間に1回株元に20g追肥"},
    ],
    "根菜類注意": [
        {"name": "苦土石灰",    "availability": 2, "ratio": "植え付け2週間前に1㎡あたり100g（pH調整）"},
        {"name": "過リン酸石灰", "availability": 2, "ratio": "元肥として1㎡あたり50g（根の肥大促進）"},
    ],
}

# 作物グループ分け
FRUIT_VEGS   = {"シシトウ", "ピーマン", "まくわうり", "きゅうり", "おくら", "ナス", "とうもろこし", "エダマメ", "ミニトマト"}
LEAF_VEGS    = {"ほうれん草", "レタス", "玉レタス", "キャベツ", "小松菜", "スティックセニョール", "モロヘイヤ", "白菜", "ネギ"}
ROOT_VEGS    = {"にんじん", "カブ", "ダイコン", "ジャガイモ", "サツマイモ", "ヤマイモ（長いも）", "サトイモ", "ニンニク", "玉ねぎ"}
OTHERS       = {"しょうが", "落花生"}


# -------------------------------------------------------------------
# 害虫データ（共通的なもの）
# -------------------------------------------------------------------
PEST_DATA = {
    "果菜類": [
        {"pest": "アブラムシ", "season": "春〜初夏", "control": "粘着テープ除去・木酢液散布・天敵（テントウムシ）"},
        {"pest": "ハダニ",    "season": "夏〜秋",   "control": "水スプレーで洗い流す・殺ダニ剤（バロックフロアブル）"},
    ],
    "葉菜類": [
        {"pest": "アオムシ（モンシロチョウ幼虫）", "season": "春・秋", "control": "防虫ネット・BT剤（オルトラン）・手取り除去"},
        {"pest": "コナガ",    "season": "通年",  "control": "防虫ネット・BT剤・天敵（コナガサムライコマユバチ）"},
    ],
    "根菜類": [
        {"pest": "ネキリムシ（ヨトウムシ幼虫）", "season": "春〜秋", "control": "株元を掘り起こして手取り・ネキリムシ防除剤"},
        {"pest": "アブラムシ", "season": "春〜初夏", "control": "粘着テープ・木酢液散布"},
    ],
}


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    updated = 0
    skipped = 0

    print("=== 作物データ補完開始 ===\n")

    for name, data in CROP_DATA.items():
        row = conn.execute("SELECT id FROM crops WHERE name = ?", [name]).fetchone()
        if not row:
            print(f"[SKIP] {name} → DBに見つからない")
            skipped += 1
            continue

        crop_id = row["id"]

        # crops テーブル更新
        fields = []
        values = []
        for field in ["temp_min", "temp_max", "sunlight", "watering",
                      "planter_size", "rotation_years", "failure_points",
                      "yield_per_plant", "storage", "harvest_sign", "days_to_harvest"]:
            if field in data:
                fields.append(f"{field} = ?")
                values.append(data[field])

        if fields:
            values.append(crop_id)
            conn.execute(
                f"UPDATE crops SET {', '.join(fields)} WHERE id = ?",
                values
            )

        # 肥料データ挿入（重複チェック付き）
        fert_groups = ["共通元肥"]
        if name in FRUIT_VEGS:
            fert_groups.append("果菜類追肥")
        elif name in LEAF_VEGS:
            fert_groups.append("葉菜類追肥")
        elif name in ROOT_VEGS or name in OTHERS:
            fert_groups.append("根菜類注意")

        for group in fert_groups:
            for f in FERTILIZER_DATA.get(group, []):
                # 肥料マスタ挿入（なければ）
                fert = conn.execute(
                    "SELECT id FROM fertilizers WHERE name = ?", [f["name"]]
                ).fetchone()
                if not fert:
                    conn.execute(
                        "INSERT INTO fertilizers (name, availability) VALUES (?, ?)",
                        [f["name"], f["availability"]]
                    )
                    fert_id = conn.execute(
                        "SELECT id FROM fertilizers WHERE name = ?", [f["name"]]
                    ).fetchone()["id"]
                else:
                    fert_id = fert["id"]

                # 中間テーブル挿入（重複チェック）
                exists = conn.execute(
                    "SELECT id FROM crop_fertilizers WHERE crop_id = ? AND fertilizer_id = ?",
                    [crop_id, fert_id]
                ).fetchone()
                if not exists:
                    conn.execute(
                        "INSERT INTO crop_fertilizers (crop_id, fertilizer_id, ratio) VALUES (?, ?, ?)",
                        [crop_id, fert_id, f["ratio"]]
                    )

        # 害虫データ挿入（重複チェック付き）
        pest_group = None
        if name in FRUIT_VEGS:
            pest_group = "果菜類"
        elif name in LEAF_VEGS:
            pest_group = "葉菜類"
        elif name in ROOT_VEGS or name in OTHERS:
            pest_group = "根菜類"

        if pest_group:
            for p in PEST_DATA.get(pest_group, []):
                # 害虫マスタ
                pest = conn.execute(
                    "SELECT id FROM pests WHERE name = ?", [p["pest"]]
                ).fetchone()
                if not pest:
                    conn.execute(
                        "INSERT INTO pests (name, season) VALUES (?, ?)",
                        [p["pest"], p["season"]]
                    )
                    pest_id = conn.execute(
                        "SELECT id FROM pests WHERE name = ?", [p["pest"]]
                    ).fetchone()["id"]
                else:
                    pest_id = pest["id"]

                # 対策マスタ
                ctrl = conn.execute(
                    "SELECT id FROM pest_controls WHERE name = ?", [p["control"]]
                ).fetchone()
                if not ctrl:
                    conn.execute(
                        "INSERT INTO pest_controls (name, type) VALUES (?, ?)",
                        [p["control"], "複合"]
                    )
                    ctrl_id = conn.execute(
                        "SELECT id FROM pest_controls WHERE name = ?", [p["control"]]
                    ).fetchone()["id"]
                else:
                    ctrl_id = ctrl["id"]

                # 中間テーブル
                exists = conn.execute(
                    "SELECT id FROM crop_pests WHERE crop_id = ? AND pest_id = ? AND control_id = ?",
                    [crop_id, pest_id, ctrl_id]
                ).fetchone()
                if not exists:
                    conn.execute(
                        "INSERT INTO crop_pests (crop_id, pest_id, control_id) VALUES (?, ?, ?)",
                        [crop_id, pest_id, ctrl_id]
                    )

        updated += 1
        print(f"[OK] {name} (id={crop_id}): 更新完了")

    conn.commit()
    conn.close()

    print(f"\n=== 完了: {updated}品種更新, {skipped}品種スキップ ===")

    # フィールド充足率レポート
    conn2 = sqlite3.connect(DB_PATH)
    total = conn2.execute("SELECT COUNT(*) FROM crops").fetchone()[0]
    for field in ["temp_min", "temp_max", "sunlight", "watering", "failure_points"]:
        count = conn2.execute(
            f"SELECT COUNT(*) FROM crops WHERE {field} IS NOT NULL AND {field} != ''"
        ).fetchone()[0]
        pct = count / total * 100
        print(f"  {field:20s}: {count}/{total} ({pct:.0f}%)")

    fert_count = conn2.execute("SELECT COUNT(DISTINCT crop_id) FROM crop_fertilizers").fetchone()[0]
    pest_count = conn2.execute("SELECT COUNT(DISTINCT crop_id) FROM crop_pests").fetchone()[0]
    print(f"  {'fertilizers':20s}: {fert_count}/{total} 品種にリンク済み")
    print(f"  {'pests':20s}: {pest_count}/{total} 品種にリンク済み")
    conn2.close()


if __name__ == "__main__":
    main()
