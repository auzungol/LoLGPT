from rag import answer_query


def main():
    print("=== LoLGPT — League of Legends Champion Q&A ===")
    print("Şampiyonlar hakkında soru sor. Çıkmak için 'exit' yaz.\n")

    while True:
        question = input("Soru: ").strip()
        if not question:
            continue
        if question.lower() in ("exit", "quit", "çık"):
            print("Görüşürüz!")
            break

        print("Düşünüyor...")
        answer = answer_query(question, top_k=12)
        print(f"\nCevap: {answer}\n")


if __name__ == "__main__":
    main()