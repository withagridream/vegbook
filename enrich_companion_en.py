"""companion_plants.effect_en 投入スクリプト"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'vegbook.db'

# (crop_name, companion_name, effect_en)
EFFECT_EN = [
    ("トマト",    "ニンニク",   "Allicin in garlic repels aphids and spider mites; also reported to suppress bacterial wilt."),
    ("トマト",    "ネギ",      "Antagonistic bacteria in leek roots suppress Fusarium wilt and reduce crop rotation problems."),
    ("トマト",    "レタス",    "Lettuce acts as a living mulch, retaining moisture and suppressing weeds around tomato roots."),
    ("トマト",    "ジャガイモ", "Both are Solanaceae; share late blight and bacterial wilt pathogens. Keep apart."),
    ("ミニトマト", "ニンニク",  "Allicin in garlic repels aphids and spider mites; also reported to suppress bacterial wilt."),
    ("ミニトマト", "ネギ",     "Antagonistic bacteria in leek roots suppress Fusarium wilt and reduce crop rotation problems."),
    ("ミニトマト", "レタス",   "Lettuce acts as a living mulch, retaining moisture and suppressing weeds around tomato roots."),
    ("ミニトマト", "ジャガイモ","Both are Solanaceae; share late blight and bacterial wilt pathogens. Avoid planting together."),
    ("ナス",      "ネギ",     "Antagonistic bacteria in leek rhizosphere suppress verticillium wilt and bacterial wilt in eggplant."),
    ("ナス",      "ニンニク",  "Garlic repels aphids and spider mites, reducing pest damage on eggplant."),
    ("ナス",      "ジャガイモ","Both are Solanaceae; share late blight and 28-spotted ladybird beetle. Do not plant together."),
    ("きゅうり",  "ネギ",     "Antagonistic bacteria in leek roots suppress Fusarium wilt (crown rot) in cucumber — a classic pairing."),
    ("きゅうり",  "ニンニク",  "Helps suppress aphids and powdery mildew on cucumber."),
    ("きゅうり",  "まくわうり","Same family (Cucurbitaceae); powdery mildew and downy mildew spread easily between them. Avoid."),
    ("ピーマン",  "ニンニク",  "Garlic repels aphids and spider mites; synergistic effect of capsaicin and allicin."),
    ("ピーマン",  "ネギ",     "Rhizosphere antagonistic bacteria suppress phytophthora blight in pepper."),
    ("シシトウ",  "ニンニク",  "Garlic repels aphids and spider mites, reducing pest damage."),
    ("シシトウ",  "ネギ",     "Rhizosphere antagonistic bacteria suppress phytophthora blight."),
    ("キャベツ",  "レタス",   "Phytoncides from lettuce repel cabbage white caterpillars and diamondback moths; mutually beneficial growth."),
    ("キャベツ",  "玉レタス",  "Phytoncides from head lettuce repel cabbage white caterpillars and diamondback moths."),
    ("キャベツ",  "ダイコン",  "Same family (Brassicaceae); striped flea beetles concentrate on both. Mixed planting amplifies damage."),
    ("白菜",      "レタス",   "Phytoncides from lettuce repel cabbage white caterpillars and diamondback moths."),
    ("白菜",      "ダイコン",  "Same family; share striped flea beetle and clubroot disease. Keep apart."),
    ("スティックセニョール", "レタス",  "Lettuce acts as a living mulch, retaining soil moisture. Also repels cabbage caterpillars."),
    ("スティックセニョール", "ダイコン","Same family (Brassicaceae); share clubroot infection. Avoid mixed planting."),
    ("にんじん",  "玉ねぎ",   "Volatile compounds from onion deter swallowtail butterfly egg-laying, reducing carrot pest damage."),
    ("にんじん",  "ネギ",     "Volatile compounds from leek deter swallowtail butterflies and carrot aphids."),
    ("カブ",      "レタス",   "Phytoncides from lettuce repel common brassica pests."),
    ("ダイコン",  "レタス",   "Lettuce acts as a living mulch, protecting daikon root base."),
    ("エダマメ",  "とうもろこし","Root nodule bacteria in edamame fix nitrogen and supply it to corn; mutually beneficial growth."),
    ("エダマメ",  "ネギ",     "Volatile compounds from leek may deter stink bugs that damage edamame pods."),
    ("落花生",    "とうもろこし","Root nodule bacteria in peanut fix nitrogen and supply it to corn; efficient use of field space."),
    ("ほうれん草", "ニンニク", "Allicin from garlic repels aphids, reducing pest damage on spinach."),
    ("小松菜",    "レタス",   "Phytoncides from lettuce repel cabbage white caterpillars and diamondback moths."),
    ("まくわうり", "ネギ",    "Antagonistic bacteria in leek rhizosphere suppress Fusarium wilt in cucurbits."),
    ("まくわうり", "きゅうり","Same family (Cucurbitaceae); powdery mildew and downy mildew spread easily. Avoid mixed planting."),
    ("おくら",    "ニンニク",  "Garlic repels aphids and helps reduce leafroller damage on okra."),
    ("おくら",    "モロヘイヤ","Both thrive in high heat and full sun; mixed planting makes efficient use of space."),
    ("しょうが",  "ネギ",     "Antagonistic bacteria in leek rhizosphere are expected to suppress rhizome rot in ginger."),
    ("しょうが",  "サトイモ",  "Both prefer partial shade and high humidity; mixed planting creates a complementary microclimate."),
    ("ジャガイモ", "ナス",    "Both are Solanaceae; share late blight and 28-spotted ladybird beetle. Do not plant together."),
    ("ジャガイモ", "トマト",  "Both are Solanaceae; late blight spreads easily between them. Avoid mixing in the field."),
    ("ジャガイモ", "ミニトマト","Both are Solanaceae; late blight spreads easily between them. Avoid mixing in the field."),
    ("ニンニク",  "にんじん",  "Allicin in garlic deters swallowtail butterfly; carrot volatile compounds repel garlic pests — mutual benefit."),
    ("ニンニク",  "レタス",   "Allicin from garlic repels aphids and protects lettuce."),
    ("玉ねぎ",    "にんじん",  "Onion volatiles deter swallowtail butterfly; carrot volatile compounds repel onion fly — mutual benefit."),
    ("玉ねぎ",    "レタス",   "Onion volatile compounds repel aphids and protect lettuce."),
    ("ネギ",      "にんじん",  "Volatile compounds from leek repel swallowtail butterflies and carrot aphids."),
    ("サツマイモ", "落花生",  "Root nodule bacteria in peanut fix nitrogen and supply it to sweet potato, reducing vine lushness."),
    ("とうもろこし", "エダマメ","Edamame fixes nitrogen and supplies it to corn; also improves air circulation and pollination."),
    ("とうもろこし", "落花生", "Peanut fixes nitrogen and supplies it to corn; mutually beneficial growth."),
]


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    name_to_id = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM crops")}

    updated = 0
    for crop_name, companion_name, effect_en in EFFECT_EN:
        crop_id      = name_to_id.get(crop_name)
        companion_id = name_to_id.get(companion_name)
        if not crop_id or not companion_id:
            print(f"[SKIP] {crop_name} × {companion_name}")
            continue
        conn.execute(
            "UPDATE companion_plants SET effect_en=? WHERE crop_id=? AND companion_id=?",
            [effect_en, crop_id, companion_id]
        )
        updated += 1

    conn.commit()
    conn.close()
    print(f"完了: {updated} 件更新")


if __name__ == "__main__":
    main()
