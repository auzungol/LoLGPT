# LoLGPT — Yerel League of Legends Şampiyon Asistanı

Microsoft Foundry Local kullanarak tamamen çevrimdışı çalışan, League of Legends
şampiyonları hakkında soru cevaplayan bir RAG (Retrieval-Augmented Generation)
uygulaması. Bu proje, [Foundry Local ile Local RAG Uygulaması Geliştirme]
(https://techcommunity.microsoft.com/blog/azuredevcommunityblog/building-your-first-local-rag-application-with-foundry-local/4501968)
yaz okulu planı temel alınarak geliştirilmiştir.

## Özellikler

- **Tamamen yerel/çevrimdışı** — hiçbir veri internete gönderilmez, tüm çıkarım
  (embedding + chat) Foundry Local ile cihazda çalışır.
- **173 şampiyon**, Riot'un resmi Data Dragon API'sinden otomatik çekilir.
- **Hibrit retrieval:** yapılandırılmış sorular (ability, koridor, bölge, rol,
  kaynak, listeleme) SQLite'tan anında ve LLM'e gitmeden cevaplanır; açık uçlu
  sorular (lore, karşılaştırma, genel bilgi) semantic search + local LLM ile
  cevaplanır.
- **Türkçe ve İngilizce** soru desteği (yazım hatası toleransı dahil).
- **Streamlit tabanlı web arayüzü.**

