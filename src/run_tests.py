from rag import answer_query

TEST_CASES = [
    # (soru, kategori)
    ("What is Garen's ultimate ability?", "ability - net soru"),
    ("yasuo q", "ability - kısa/harf"),
    ("caitlyn ulti", "ability - 'ulti' eş anlamlısı"),
    ("miss fortne passiv", "ability - yazım hatası + boşluklu isim"),
    ("veigar lane", "öznitelik - lane"),
    ("ahri region", "öznitelik - region"),
    ("garen role", "öznitelik - role"),
    ("assassin champions", "listeleme - role"),
    ("which champions are from ionia", "listeleme - region"),
    ("top laner champions", "listeleme - lane"),
    ("mage champs", "listeleme - role (büyük küme)"),
    ("What is Yasuo's ultimate?", "genel bilgi - dolaylı"),
    ("tell me about zoe", "genel bilgi - lore"),
    ("what abilities does wukong have", "genel bilgi - tüm yetenekler"),
    ("kim bilir the rock'ı", "cevapsız - alakasız soru"),
    ("what is arcane season 3 release date", "cevapsız - League evreni dışı"),
    ("xX_yasuo_Xx nedir", "cevapsız - uydurma isim"),
    ("", "edge case - boş soru"),
    ("asdkfjaskldfj", "edge case - anlamsız girdi"),
    ("compare garen and darius", "genel bilgi - karşılaştırma"),
]


def run_tests():
    results = []
    for question, category in TEST_CASES:
        if not question.strip():
            results.append((question, category, "(atlandı - boş soru)"))
            continue

        print(f"[{category}] Soru: {question}")
        try:
            answer = answer_query(question)
        except Exception as e:
            answer = f"HATA: {e}"
        print(f"Cevap: {answer}\n")
        results.append((question, category, answer))

    with open("test_results.txt", "w", encoding="utf-8") as f:
        for question, category, answer in results:
            f.write(f"KATEGORİ: {category}\n")
            f.write(f"SORU: {question}\n")
            f.write(f"CEVAP: {answer}\n")
            f.write("-" * 60 + "\n\n")

    print(f"\n{len(results)} test tamamlandı. Sonuçlar test_results.txt dosyasına yazıldı.")


if __name__ == "__main__":
    run_tests()