Veri katmanı: SQLite (`database/champions.db`), her şampiyon parçası (chunk)
için metin + embedding vektörü (`qwen3-embedding-0.6b`, 1024 boyut) + yapılandırılmış
metadata (region, role, lane, resource) saklar.

## Kurulum

```powershell
git clone https://github.com/auzungol/LoLGPT.git
cd LoLGPT
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

[Foundry Local CLI](https://learn.microsoft.com/azure/ai-foundry/foundry-local/get-started)'ın
kurulu olduğundan emin olun:
```powershell
winget install Microsoft.FoundryLocal
```

## Veriyi Hazırlama

```powershell
cd src
python fetch_champions.py   # Data Dragon'dan şampiyon verisini çeker
python ingest.py            # Embedding üretip SQLite'a yazar (ilk çalıştırmada uzun sürebilir)
```

## Kullanım

**Komut satırı:**
```powershell
python main.py
```

**Web arayüzü (Streamlit):**
```powershell
streamlit run app.py
```

## Örnek Sorular

- `yasuo q` / `yasuo q'sunu söyle`
- `veigar lane` / `veigar koridoru`
- `assassin champions` / `suikastçılar`
- `which champions are from ionia` / `hangi şampiyonlar ionialı`
- `caitlyn ultisi nedir`
- `zoe'yi anlat`
- `garen vs darius`

---

## Mühendislik Kararları

Bu bölüm, projeyi orijinal planın üstüne geliştirirken alınan, planda doğrudan
yer almayan ama gerçek kullanımda gerekli hâle gelen tasarım kararlarını
belgeler.

### 1. Hibrit retrieval: "Neden her şey semantic search'e gitmiyor?"

Plan, RAG'ı klasik "embed → benzerlik ara → LLM'e ver" akışıyla tanımlıyor.
Uygulama sırasında şunu gördük: **ability harfi ("yasuo q"), koridor, bölge,
rol, kaynak gibi sorular aslında birer arama/özetleme sorusu değil, birer
veritabanı sorgusu.** Bu tür sorularda semantic search + LLM kullanmak hem
yavaş hem de küçük yerel modelde (bkz. Bölüm 4) hataya açık.

Bu yüzden SQLite'ı sadece embedding deposu değil, **filtrelenebilir yapılandırılmış
metadata deposu** olarak da kullandık — `region`, `role`, `lane`, `resource`
sütunları eklenerek. Bir soru şu üç kategoriden birine giriyorsa, sistem LLM'e
hiç gitmeden SQL'den kesin cevap veriyor:

- **Listeleme:** "mage champions", "hangi şampiyonlar ionialı"
- **Ability harfi:** "yasuo q", "caitlyn ultisi"
- **Tekil öznitelik:** "veigar lane", "garen kaynak"

Geri kalan her şey (lore, karşılaştırma, açık uçlu "X'i anlat" soruları, kapsam
dışı sorular) hâlâ tam RAG akışından (semantic search + context injection +
LLM generation) geçiyor — **sistem karakterini kaybetmiyor**, sadece yapısal
olarak kesin cevaplanabilir bir alt küme için hız/güvenilirlik kazanıyor. Bu,
üretim RAG sistemlerinde "routing" veya "hibrit structured+unstructured
retrieval" olarak bilinen standart bir pratiktir.

### 2. Yazım hatası ve dil toleransı (fuzzy matching)

Gerçek kullanıcılar champion isimlerini, rol/bölge/koridor terimlerini her
zaman doğru yazmıyor ("veifar" → Veigar, "kordor" → koridor, "assassins" tek
başına, İngilizce/Türkçe karışık kullanım). Python'un yerleşik `difflib`
kütüphanesiyle karakter-benzerliği tabanlı bir fuzzy eşleştirme katmanı
eklendi (`retrieval.py`, `regions.py`, `roles.py`, `lanes.py`, `abilities.py`).

Bunu eklerken karşılaşılan asıl mühendislik problemi **yanlış-pozitif riskiydi**:
genel kelimeler kısa champion isimleriyle rastgele yüksek benzerlik
gösterebiliyor (örn. `"assassin"` ~ `"kassadin"` %75, `"kaynak"` ~ `"kayn"` %80).
Çözüm iki katmanlı: (1) role/region/lane/listeleme kelimeleri gibi genel
terimler fuzzy champion aramasından `_STOPWORDS` ile hariç tutuldu, (2) çok
kelimeli isimlerin boşluksuz yazımını (`"miss fortune"` → `missfortune`)
yakalamak için kullanılan birleştirme mantığı, **rastgele bir alt dize
eşleşmesi değil, ardışık kelime birleşimlerine tam eşitlik** arayacak şekilde
sıkılaştırıldı — aksi halde "ahri kaynak" gibi bir sorgu, boşluklar silinince
oluşan metnin içinde tesadüfen geçen "kayn" harflerini yanlışlıkla Kayn
şampiyonuyla eşleştiriyordu.

### 3. Lane (koridor) verisi — elle derlenmiş

Planın önerdiği Data Dragon API'si, embedding/RAG için gereken lore ve yetenek
verisini sağlıyor ama **koridor (Top/Jungle/Mid/ADC/Support) bilgisini resmi
olarak vermiyor** — Riot bu veriyi hiçbir public API'de yayınlamıyor. Üçüncü
parti (resmi olmayan) kaynaklara bağımlı kalmak yerine, 173 şampiyonun koridor
bilgisi `lanes.py` içinde elle derlendi. Bu, projenin RAG/otomasyon felsefesinden
bir sapma değil, API'nin sağlamadığı bir yapılandırılmış veriyi tamamlayan
bilinçli bir mühendislik kararı — tıpkı planın SQLite'ı "filtrelenebilir
metadata deposu" olarak önermesi gibi, kaynağı ne olursa olsun veri
sorgulanabilir hale getiriliyor. Birkaç yeni şampiyonun (`locke`, `yunara`,
`zaahen`) koridoru doğrulanamadığı için şeffaf şekilde `"Unknown"` bırakıldı.

### 4. Donanım kısıtlaması: neden `top_k` düşük tutuluyor

Foundry Local, chat modelini (`phi-3.5-mini`) ve embedding modelini
(`qwen3-embedding-0.6b`) **aynı anda CPU'da** çalıştırıyor. Geliştirme/test
sırasında, `top_k` (semantic search'te LLM'e gönderilen chunk sayısı) yüksek
tutulduğunda (örn. 12+) iki sorunla karşılaşıldı:

- **Context aşırı büyüyünce native runtime isteği iptal ediyor** ("Operation
  was cancelled" hatası) — büyük olasılıkla bellek baskısı altında.
- **Alakasız ek chunk'lar modelin kafasını karıştırıyor** — özellikle tek bir
  champion zaten kesin eşleştiğinde, ekstra semantic sonuçlar gürültüden
  başka bir şey katmıyor.

Bu gözlem üzerine iki optimizasyon yapıldı: `main.py`/`app.py`'de `top_k`
düşük (5) tutuldu, ve `retrieval.py`'de bir champion zaten isim/fuzzy eşleşmesiyle
kesin bulunduysa **semantic doldurma tamamen atlanıyor** (`get_top_chunks`
içindeki `if mentioned_champions: return results` satırı) — hem prompt küçülüyor
hem cevap kalitesi artıyor. Bu, planın "Performance & Debugging" (Faz 3, Hafta 5)
bölümünde önerilen "retrieve edilen chunk sayısını azaltma" optimizasyonunun
doğrudan uygulanmasıdır.

### 5. Hata toleransı

LLM çağrısı (özellikle donanım baskısı altında) ara sıra başarısız olabildiği
için, `rag.py`'de bir kerelik otomatik yeniden deneme eklendi; ikinci deneme de
başarısız olursa program çökmek yerine kullanıcıya nazik bir hata mesajı
gösterip çalışmaya devam ediyor.

## Bilinen Sınırlamalar

- **Donanım gereksinimi:** 8 GB'tan az RAM'e sahip makinelerde açık uçlu
  sorularda yavaşlama, tutarsız çıktı veya nadiren "Operation was cancelled"
  hatası görülebilir. Yapılandırılmış sorular bundan etkilenmez.
- **Ability açıklamalarının Türkçe çevirisi**, küçük yerel modelin kapasitesine
  bağlı olarak bazı açık uçlu sorularda tutarsız çıkabiliyor; bu durumda
  soruyu İngilizce sormak daha güvenilir sonuç verir.
- **Region tespiti** lore metnindeki anahtar kelimelere dayanır; birkaç
  şampiyon (Bard, Ryze, Kindred gibi) evren içinde kasıtlı olarak bölgesizdir,
  bu doğru bir sınıflandırmadır, hata değildir.

## Proje Yapısı
- **src/**

- config.py # Model isimleri, dosya yolları
- fetch_champions.py # Data Dragon'dan veri çekme
- ingest.py # Chunk'lama, embedding, SQLite'a yazma
- embedding.py # Foundry Local embedding client
- database.py # SQLite şema ve sorgu fonksiyonları
- retrieval.py # Semantic + isim tabanlı hibrit retrieval
- regions.py / roles.py / lanes.py / abilities.py # Yapılandırılmış eşleştirme
- rag.py # Ana orkestrasyon: routing + LLM çağrısı
- main.py # CLI arayüzü
- app.py # Streamlit web arayüzü
- data/champions/ # Üretilen şampiyon metinleri (fetch_champions.py çıktısı)
- database/ # SQLite veritabanı (ingest.py çıktısı)