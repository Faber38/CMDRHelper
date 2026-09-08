# CMDRHelper V3 (3.0)

[🇩🇪 Deutsch](README_DE.md) \| [🇬🇧 English](README.md) \| [🇫🇷
Français](README_FR.md) \| [🇮🇹 Italiano](README_IT.md) \| [🇳🇴
Norsk](README_NO.md) \| [🇸🇪 Svenska](README_SV.md) \| [🇫🇮
Suomi](README_FI.md) \| [🇵🇱 Polski](README_PL.md) \| [🇳🇱
Nederlands](README_NL.md) \| [🇪🇸 Español](README_ES.md) \| [🇹🇷
Türkçe](README_TR.md) \| [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper -- Elite Dangerous için yardımcı
pilotunuz](cmdrhelper/assets/readme/cmdrhelper_readme_tr.png)

**Elite Dangerous için kişisel yardımcı – keşif, gezinme ve komutan verileri bir bakışta**

CMDRHelper, Elite Dangerous’ın yerel günlüklerini inceleyen ve `Status.json` dosyasındaki gezegen konum verilerini kullanan bağımsız bir masaüstü uygulamasıdır. İlginç gökcisimlerini belirlemene, kaydedilmiş yerlere dönmene ve yolculuklarınla bulgularını incelemene yardımcı olur. Kişisel veriler yeniden başlatmadan sonra korunur ve komutanlara göre ayrı tutulur.

## Explorer

Explorer mevcut sistemi üç görünümde gösterir:

- **Sistem haritası:** bilinen yıldızların, gezegenlerin ve uyduların grafik gösterimi. Bir gökcismine tıklamak ayrıntılarını açar. “Tümünü göster” sistem genel görünümünü açar.
- **Değer listesi:** bilinen gökcisimlerinin tarama ve haritalama değerleri, elde edilmiş değer ve olası toplam değer. İşaretler, dünyalaştırma adaylarını, olası ilk keşifleri ve ilk haritalamaları bulmayı kolaylaştırır.
- **BIO / GEO / MADENCİLİK:** biyolojik ve jeolojik sinyaller, gezegen madencilik sahaları ve doğrulanmış kişisel bulgular.

Analizler, bildirilen sinyalleri gerçek kişisel bulgulardan ayırır. **BIO ×N** bildirilen sinyal sayısıdır; tamamen analiz edilmiş türlerin onayı değildir. **MADENCİLİK ×N**, gezegen madencilik sahalarını sayar ancak her birinin ham madde içeriğini açıklamaz. Kişisel olarak çıkarılan ticari mallar, madencilik sırasında toplanan yan malzemeler ve gökcisminin genel malzeme bileşimi ayrı tutulur.

Explorer ayrıca tahmini BIO değerlerini, kişisel analizlerin ilerlemesini ve henüz satılmamış haritalama ve BIO verilerini gösterir. Değerler mevcut günlük ve gökcismi bilgilerine dayanır; eksik veriler kişisel keşif gibi sunulmaz. Ek EDSM verileri, kişisel bulgulardan ayrılması gereken dış kaynaklı bilgilerdir.

Gökcismi ayrıntıları mevcut fiziksel özellikleri, atmosferi, halkaları, malzemeleri ve keşif bilgilerini içerir. Gösterimlerde uygun dokular ve bazı özel astronomik nesneler için animasyonlar kullanılır. Cargo bölümü o anda kullanılan geminin veya SRV’nin bilinen yükünü ve kapasitesini gösterir; Rhino’da yük ile kişisel madencilik bulguları ayrı bilgilerdir.

Explorer’ın üst kısmında **★ Favoriler | Gezegen navigasyonu | Tümünü göster** bulunur. Favoriler ve gezegen gezinmesi kendi pencerelerini açar; Explorer’ın üç görünümü kullanılabilir kalır.

## Gezegen gezinmesi

Gezegen gezgini yalnızca **bir gezegen veya uydudaki belirli enlem/boylama** uçmana yardımcı olur. Yıldız sistemleri arasındaki seyahatler için ayrı rota planlayıcı vardır.

### Hedefi gir ve uç

Hedef gökcismini seç veya mümkün olduğunda otomatik algılanan mevcut gökcismini kullan. Enlem, boylam ve isteğe bağlı hedef adı gir. BodyID veya SystemAddress gibi teknik bilgileri girmen gerekmez. **0,0** da geçerli bir koordinattır.

Elite, ilgili gökcismi için geçerli gezegen konum verileri sağladığında pusula otomatik etkinleşir. Uygun veriler yoksa gezgin bekleme durumunu gösterir. Aynı gökcisminde istediğin zaman yeni bir koordinat hedefi belirleyebilirsin; önceki hedefin yerini alır.

### Yaklaşma sırasındaki gösterim

| Hedef mesafesi | Gösterim |
| --- | --- |
| **380 km’den fazla** | Kendi konumun beyaz bir daire, hedef küçük bir nokta olarak gezegen küresinde gösterilir. Hedef görünür tarafta turuncu, gizli arka tarafta kırmızıdır. Oyuncunun konumu gösterimde sabit kalır; gezegen ve hedef buna göre gösterilir. |
| **380 km ve altı** | Yaklaşmayı sürdürmek için **50 km mesafe aralıkları** ve içine çizilmiş hedef konumuyla eğik perspektif ızgarasına otomatik geçiş. |

Gezgin penceresi serbestçe yeniden boyutlandırılabilir. Küre veya perspektif ızgarası mevcut alana orantılı olarak uyarlanır; ayrıntılı değerler okunabilir kalır.

### Gezinme değerlerini anlama

- **Hedef koordinatları:** hedefin kaydedilmiş enlem ve boylamı.
- **Mevcut koordinatlar:** son geçerli kendi gezegen konumun.
- **Hedef mesafesi / Yüzey mesafesi:** küresel yüzey boyunca hedefe hesaplanan mesafe; büyük mesafe göstergesi ve ayrıntılı değer aynı mesafeyi farklı yuvarlamalarla gösterir.
- **Kerteriz:** mevcut konumdan hedefe mutlak yön.
- **Heading:** Elite’in bildirdiği mevcut yönelimin.
- **Göreli yön:** heading ile kerteriz arasındaki fark; örneğin “23° sağa”, “sola” veya “düz”.
- **Hedef rotası:** Elite HUD’unda dönebileceğin mutlak rota. Kerterize karşılık gelir ve ek bir göreli dönüş açısı değildir.

Örnek: **Heading 051° → Hedef rotası 074° = 23° sağa**.

Gezinme oyunun durum verilerine bağlıdır; güncellemeler oyun durumuna göre gecikmeli gelebilir. Yüzey mesafesi bir arazi veya yol rotası değildir. Güzergâhtaki engeller ve arazi yükseklikleri hesaba katılmaz.

## Gezinme HUD’u

Soldaki **otomatik göster → Navigasyon HUD** altında doğrudan Elite’in üzerinde isteğe bağlı ek gösterimi açabilirsin. Geçerli gezegen gezinmesinde şunları gösterir:

- göreli yön,
- mutlak hedef rotası,
- mesafe.

HUD saydamdır, tıklamaları geçirir ve odağı almaz: fare tıklamalarını veya giriş odağını oyundan çalmaz. Geçerli gezinme yoksa otomatik görünmez olur; kenar çubuğundaki kutu işaretli kalabilir. Normal gezgin HUD’dan bağımsız çalışır.

HUD, oyun içinde **Linux/X11** ve **Elite ile Windows 11** üzerinde test edilmiştir. Windows’ta birden fazla monitör, eşleşen monitör adlarına göre değil geometrileri ve Elite penceresinin konumuna göre eşleştirilir.

## Favoriler

**Explorer → ★ Favoriler**, ayrı ve yeniden kullanılabilen bir pencere açar. Favoriler **etkin komutana** aittir. Komutan değişimi görünümü günceller; günlükteki komutan seçimi favori listesini genişletmez.

### Üç tür kaydetme

Üst eylem satırı şunları sunar:

| Eylem | Kaydedilen favori |
| --- | --- |
| **★ Mevcut sistemi kaydet** | Yüzey koordinatları olmadan mevcut sistem. |
| **★ Gezegen / ay kaydet** | Mevcut sistemden seçilmiş bilinen bir gezegen veya uydu, yüzey koordinatları olmadan. |
| **★ Mevcut konumu kaydet** | Mevcut sistem, gökcismi, enlem ve boylam içeren bir yüzey konumu. |

Konum düğmesi her zaman görünür kalır ve yalnızca geçerli güncel gezegen konum verileri ve etkin komutan varsa kullanılabilir. **Tıklama, düzenleme iletişim kutusu açılmadan önce komutanı, sistemi, gökcismini ve koordinatları sabitler.** Oyundaki sonraki hareketler bu konumu değiştirmez. Aynı kaydetme akışı gezegen gezgininde de bulunur. Bilinen dahili kimlikler otomatik aktarılır; koordinat uydurulmaz.

Bir ad ve tam olarak bir kategori seç: **Biyo, Jeo, Madencilik, Manzara, İniş yeri, İlginç veya Diğer**. Not ve resim isteğe bağlıdır.

### Bulma, görüntüleme ve düzenleme

Ada göre alfabetik sıralanmış, kaydırılabilir liste; ad, tür, sistem, gerektiğinde gökcismi ve koordinatlar, kategori ve küçük resim önizlemesi gösterir. **Serbest metin araması, tür ve kategori filtreleri** birleştirilebilir. Arama; ad, sistem, gökcismi ve notu kapsar.

**Aç / Göster**, kaydedilmiş bilgileri, notu ve daha büyük resim önizlemesini gösterir. **Explorer’da göster**, favori mevcut Explorer sistemine aitse ve ilgili veriler varsa mevcut sistem genel görünümünü veya gökcismi ayrıntılarını kullanır. Diğer sistemler için kaydedilmiş favori bilgileri kullanılabilir kalır.

**Düzenle**; ad, kategori, not ve resmi değiştirir. Sistem, gökcismi ve kaydedilmiş koordinatlar canlı değerlerle değiştirilmez. Başka bir konum için yeni yüzey favorisi oluştur.

**Sil**, onay ister ve yalnızca favori kaydını ve dahili resim kopyasını kaldırır. Explorer, günlük ve gökcismi verileri korunur.

### Favori resimleri ve son ekran görüntüsü

Favori resimleri **normal Resimler bölümünden tamamen ayrıdır**. CMDRHelper, favori resimleri klasöründe kendi dahili kopyasını yönetir (standart veri düzeninde `data/favorites/images/`). Orijinal taşınmaz veya değiştirilmez.

- **Resim seç …**, PNG, JPEG veya WebP kabul eder ve önizleme gösterir. Dahili kopya yalnızca kaydederken oluşur.
- **Son ekran görüntüsünü kullan**, her tıklamada gerçek ekran görüntüsü kaynak klasörünü yeniden tarar. Ayrıca yapılandırılmış dönüştürme hedefindeki etkin komutanın klasöründe bulunan uygun dönüştürülmüş Elite ekran görüntülerini dikkate alır. Böylece otomatik dönüştürme BMP’sini silmiş olsa da yeni ekran görüntüsü kullanılabilir kalır.
- Genel resim klasörlerinden rastgele resimler değil, uygun Elite veya dönüştürme adlarına sahip okunabilir dosyalar sunulur. Sıralama için dosya adındaki açık çekim zamanı, yoksa dosya zamanı kullanılır. Dönüştürülmüş resimlerde dönüştürme zamanı değil, adda saklanan çekim zamanı kullanılır.
- Bulunan ekran görüntüsünü kabul etmeden önce dosya adını, çekim zamanını ve yeni yüklenmiş önizlemeyi görürsün. **Bu resmi kullan** ile onayla. Uygun ekran görüntüsü bulunamazsa elle resim seçimi kullanılabilir kalır. CMDRHelper kendisi ekran görüntüsü almaz.

Bir resim daha sonra değiştirilebilir veya kaldırılabilir. Gereksiz dahili kopyalar favori kaydedilirken veya silinirken kaldırılır. **Favori eylemleri hiçbir zaman orijinal ekran görüntüsünü veya seçilmiş orijinal resmi silmez.** Dahili resim dosyası eksikse favori önizleme olmadan kullanılabilir kalır.

### Yüzey favorisini hedef olarak kullanma

**▶ Hedefe git**, kaydedilmiş gökcismini, enlemi, boylamı ve favori adını mevcut gezegen gezginine aktarır ve önceki hedefi değiştirir. Favorilerin kendi gezinme mantığı yoktur. Uygun geçerli gezegen verileri gezinmeyi başlatır; aksi hâlde gezgin her zamanki gibi bekler.

Diğer komutanların favorileri kendi hedeflerin olarak kullanılamaz. Komutan değişimi, hâlâ önceki komutanın favori hedefi olarak yönetilen bir hedefi sonlandırır. Sistem ve gökcismi favorileri mevcut bilgileri gösterir; kendi rota planlamaları yoktur.

## Günlük

Günlük, kaydedilmiş seyahat ve bulgu geçmişindir. **3D seyahat haritası**, ziyaret edilen sistemleri ve komutan rotalarını gösterir. Sistem ve gökcismi ayrıntıları bilinen BIO, GEO, malzeme, Codex ve madencilik bilgilerini yeniden bulmana yardımcı olur.

### Birleşik filtreler

**Uygula** veya **serbest metin alanında Enter**, ayarlanmış tüm filtreleri birlikte çalıştırır:

- serbest metin,
- isteğe bağlı **Başlangıç** ve **Bitiş**,
- **Gezegensel maden sahaları** ve **En az**,
- **Kendi maden buluntularım** ve **Ticari mal**.

**Arama yardımı / Açıklama** içindeki bir terim arama alanına aktarılır ve mevcut dönem ve madencilik filtreleriyle birlikte çalıştırılır.

### UTC dönemi

Başlangıç ve Bitiş kendi kutularıyla etkinleştirilir. Yalnızca tek sınır da kullanılabilir; kutu işaretli değilse o tarafta zaman kısıtlaması yoktur. **Başlangıç**, seçilen UTC takvim gününün başlangıcını dahil eder. **Bitiş**, seçilen UTC gününün tamamını kapsar. UTC ortak zaman temelidir, yerel takvim zamanın değildir.

**Gerçek sistem ziyaretleri** belirleyicidir: en az bir kayıtlı ziyaret dönemin içinde olmalıdır. Sistemin yalnızca ilk veya son kez bilinmesi ziyaretin yerini tutmaz. Dönem etkinken haritadaki ziyaret sayısı, ilk ve son ziyaret, filtrelenmiş ziyaretleri ifade eder.

Dönem; tekil keşif, BIO, GEO veya madencilik olaylarını değil ziyaretleri filtreler. Bilinen bulgu bilgileri ve kişisel madencilik miktarları kaydedilmiş **toplam değerler** olarak kalır. **Dönem etkinken “Bakır 56 t”, otomatik olarak “bu dönemde 56 t” anlamına gelmez.** Başlangıç Bitiş’ten sonraysa hata gösterilir ve veritabanı sorgusu başlatılmaz.

### Komutan ve yenileme

**Haritanın komutan seçimi**, gösterilen komutan rotalarını belirler. Kişisel serbest metin ve madencilik aramaları ise görüntülenen veya etkin komutana aittir. Harita kutuları kişisel aramaları otomatik olarak birden çok komutana genişletmez.

**Günlüğü yenile**, verileri yeniden yükler ve etkin filtreleri tekrar çalıştırır. **Mevcut konum**, önce mevcut filtre durumunu uygular ve yalnızca mevcut sistem sonuç haritasında varsa ona merkezlenir. Aksi hâlde bir mesaj görünür; filtreler korunur.

**Sıfırla**, serbest metni temizler, Başlangıç/Bitiş’i kapatır ve görünen tarih alanlarını sıfırlar. Madencilik kutuları temizlenir, asgari sayı 0 ve ticari mal Tümü olur. Komutan seçimi korunur; ardından normal günlük yüklenir.

**Sonuç yoksa**, harita ve rotalar temizlenir, sonuç listesi temizlenip gizlenir, ayrıntı gösterimi sıfırlanır ve açık günlük sistem ayrıntısı penceresi kapatılır. Eski sonuçlar görünür kalmaz.

### Harita denetimleri

- Sol fare düğmesiyle sürükleme: döndürme.
- Sağ fare düğmesiyle sürükleme: kaydırma.
- Orta fare düğmesiyle sürükleme: yakınlaştırma çerçevesi çizme.
- Fare tekerleği: yakınlaştırma.
- **Hizala:** yönelimi galaktik üstten görünüme döndürür; kaydırma ve yakınlaştırma korunur.

## Resimler ve otomatik ekran görüntüsü dönüştürme

**Resimler** bölümünde Elite ekran görüntüsü kaynak klasörünü ve dönüştürme hedefini ayarlarsın. Otomatik dönüştürme, yeni BMP ekran görüntülerini **PNG veya JPEG** biçimine çevirir. Ayarlanabilir aydınlatma mevcuttur. Başlangıçta zaten bulunan BMP’ler yalnızca izlemeyi açarak geriye dönük otomatik dönüştürülmez; onlar için elle dönüştürme vardır.

Dönüştürülmüş dosya adları çekim zamanı, komutan ve sistem bilgisini içerir; dosyalar komutan bazında saklanır. Otomatik atama, etkin günlük komutanını izler. Galeride farklı seçim bu etkin komutanı değiştirmez.

**Başarılı dönüştürmeden sonra orijinal BMP’yi silme** seçeneği yalnızca bu dönüştürmeye aittir ve ayrı bir ayardır. Favori resimleri yönetiminden bağımsızdır.

Galeri, uygun dönüştürülmüş resimleri önizlemeyle gösterir. Yeniden gösterildiğinde tekrar okunur; yenileme de güncel dosyaları dikkate alır. Seçim ve büyük önizleme birlikte güncellenir. Seçili resim kaybolursa mevcut başka bir resim seçilir veya önizleme temizlenir. Resimler bölümünde ayrıca kendi resim seçimi ve onaylı silme işlevi vardır.

## Diğer görünümler

- **Genel bakış:** etkin komutan, gemi, konum, günlük algılama, açık görevler ve çevrimiçi durum.
- **Görevler:** bilinen hedefleri, ilerlemesi ve tamamlanma durumuyla kalıcı olarak saklanan açık görevler. Eksik bilgiler tamamlanmaz veya uydurulmaz.
- **CMDR:** servet, rütbeler, istatistikler, MercCoins, gemiler/filo ve bilinen Fleet Carrier konumu. MercCoins, uygulamanın hesapladığı bir bakiye olarak değil Frontier’in bildirdiği toplamlar olarak gösterilir.
- **Rota planlayıcı:** Spansh ile gemi ve Fleet Carrier için ayrı planlama. Hesaplanan carrier rotaları CTSVision için CSV olarak dışa aktarılabilir. Hesaplama dış hizmete bağlantı gerektirir.

## Komutan, yerel veriler ve çevrimiçi hizmetler

CMDRHelper, etkin komutanı mevcut günlük oturumunun Frontier kimliğinden tanır. Kişisel keşif, görevler, servet, favoriler ve çevrimiçi erişim bilgileri ayrı saklanır. Başka bir komutanı yalnızca görüntülemek, canlı komutanı veya yüklemelerinin atamasını değiştirmez.

Yerel SQLite veritabanı bilinen sistemleri, gökcisimlerini ve kişisel geçmişi yeniden başlatmalarda korur. Yeni tamamlanmış günlük kayıtları oyun sırasında işlenir; kaydedilmiş okuma konumları gereksiz yeniden okumayı önler. Konum veya komutan yanlışsa önce günlük algılamayı ve ayarlardaki günlük klasörünü kontrol et.

**EDSM**, ek sistem verileri sağlayabilir. İlgili hizmet etkin komutanın kendi erişim bilgileriyle ayarlanıp etkinleştirildiyse desteklenen günlük verileri **EDSM ve Inara’ya** gönderilebilir. Bir komutan otomatik olarak başkasının API anahtarını kullanmaz. Yerel kayıt, kullanılabilir çevrimiçi bağlantıdan bağımsız çalışır.

## Diller ve bağlamsal yardım

Arayüz **12 dili** destekler: **DE, EN, FR, IT, NO, SV, FI, PL, NL, ES, TR, EL** – Almanca, İngilizce, Fransızca, İtalyanca, Norveççe, İsveççe, Fince, Lehçe, Felemenkçe, İspanyolca, Türkçe ve Yunanca.

Şu anda **dil başına 937 UI-i18n anahtarı** vardır. **? Yardım**, **10 ayrıntılı bağlamsal yardım konusunu 12 dilin tamamında** sunar. Favoriler Explorer yardımının parçasıdır; gezegen gezinmesinin doğrudan gezginden erişilen kendi konusu vardır. Yardım, mevcut arayüz dilini kullanır ve katalog veya kayıt eksikse Almancaya geri döner.

## Gereksinimler

| Platform | Python |
| --- | --- |
| **Windows** | **Python 3.10 veya daha yeni, x64 zorunlu.** Mevcut sürümler için yapay üst sınır yoktur. Sonraki gerçek paket ve içe aktarma kontrolleri belirleyicidir. |
| **Linux** | **Python 3.10 veya üzeri**, 64 bit önerilir. Python sürümüne uygun venv modülü bulunmalıdır. |

Gerekli paketler `requirements.txt` içindedir:

```text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

Kurulum bu bağımlılıkları indirir. Günlük analizi ve gezegen gezinmesi için yerel Elite dosyaları erişilebilir olmalıdır. Linux’ta Elite, Steam/Proton üzerinden çalışabilir; gerçek günlük ve ekran görüntüsü yolları CMDRHelper’da ayarlanır. Yukarıdaki Linux HUD desteği X11 içindir.

## Linux’ta kurulum

Projenin veya sürümün tamamını çıkar ve proje klasöründe çalıştır:

```bash
./install.sh
./start.sh
```

Betikler yalnızca bu kurulumun yerel `venv` ortamını kullanır. Sembolik betik bağlantılarını çözer, Python ve pip’i kontrol eder ve kişisel verilere veya Elite günlüklerine dokunmadan bozuk yerel ortamı onarabilir. Eksik sistem paketleri otomatik kurulmaz; venv modülü eksikse yükleyici bildirir. Mevcut Linux kurulum yolu değişmeden kalır.

## Windows’ta kurulum

1. ZIP’in tamamını ayrı bir klasöre çıkar.
2. **install.bat** dosyasını başlat. Birlikte verilen **install-windows.ps1** dosyasını çağırır.
3. Başarılı kurulumdan sonra CMDRHelper’ı **start.bat** ile başlat.

Mevcut **Python 3.10 ve üzeri x64**, yapay sürüm üst sınırı olmadan kabul edilir. Gelecekteki bir Python sürümü yalnızca sürüm numarası yüzünden reddedilmez. Uygun mevcut Python veya kullanılabilir yerel venv, gereksiz otomatik Python kurulumunu önler.

Uygun Python yoksa yükleyici, onayından sonra **winget** aracılığıyla otomatik kurulum sunar. Bunun için bilinçli olarak sabit **Python 3.14 x64** sürüm serisi seçilmiştir; bu seçim mevcut Python sürümleri için açık uçlu kuraldan ayrıdır. Otomatik kurulum mümkün değilse yükleyici hatayı bildirir.

Yükleyici yalnızca **bu CMDRHelper kopyasının yerel venv ortamını** oluşturur, kontrol eder veya onarır; gereksinimleri kurar ve **pip check** ile **PySide6, PySide6.QtWidgets, numpy ve PIL** içe aktarma kontrollerini çalıştırır. Ortamın kullanılabilirliğine yalnızca bu gerçek kontroller karar verir. Başarısız olurlarsa kurulum anlaşılır bir hata mesajıyla durur. Başka sanal ortamlar onarılmaz veya değiştirilmez.

## Tanılama ve dağıtım paketleri

Sorunlarda günlük ve çevrimiçi durum göstergeleri ile `logs` klasöründeki kayıt dosyaları yardımcı olur. Kişisel veriler yerel saklanır; favorilerin yedeği veritabanının yanında dahili resim kopyalarını da içermelidir.

Kendi dağıtım paketini oluşturmak için `./create_release.sh` kullanılabilir. Program sürümü merkezi olarak `cmdrhelper/version.py` içinde yönetilir ve dağıtım betiği tarafından okunur. Paket program kodu ve varlıkları içerir; kişisel veritabanı, venv, Git veya önbellek dosyalarını içermez.

## Görsel ve video materyalleri / Media Credits

CMDRHelper, bazı özel astronomik nesneler için **NASA Scientific
Visualization Studio (NASA SVS)** görselleştirmelerini kullanır. İlgili
medyaların hakları kendi hak sahiplerinde kalır ve NASA SVS sayfalarında
belirtilen bilgilere göre credit verilir.

### Nötron yıldızı

-   CMDRHelper dosyası: `star_neutron.webm`
-   Kaynak: NASA Scientific Visualization Studio, **Neutron Star
    Animations** (SVS ID 20267)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animatörler: Walt Feimer (KBR Wyle Services, LLC) ve Lisa Poje
    (USRA)
-   Kaynak: https://svs.gsfc.nasa.gov/20267/

### Kara delik

-   CMDRHelper dosyası: `black_hole.mp4` veya projede kullanılan video
    dosyası uzantısı
-   Kaynak: NASA Scientific Visualization Studio, **Black Hole Accretion
    Disk Visualization** (SVS ID 13326)
-   Credit: **NASA's Goddard Space Flight Center/Jeremy Schnittman**
-   Kaynak: https://svs.gsfc.nasa.gov/13326/

### Süper kütleli kara delik

-   CMDRHelper dosyası: `black_hole_supermassive.mp4` veya projede
    kullanılan video dosyası uzantısı
-   Kaynak: NASA Scientific Visualization Studio (SVS ID 14576)
-   Credit: **NASA's Goddard Space Flight Center/J. Schnittman and B.
    Powell**
-   Kaynak: https://svs.gsfc.nasa.gov/14576/

### Beyaz cüce

-   CMDRHelper dosyası: `star_white_dwarf.webm`
-   kullanılan NASA medyası: **White Dwarf establishing shot**
    (`WDStar_4k_60fps_ProRes.webm`)
-   Kaynak: NASA Scientific Visualization Studio, **Type Ia Supernovae
    Animations** (SVS ID 20344)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animatör: Adriana Manrique Gutierrez (USRA)
-   Producer: Scott Wiessinger (USRA)
-   Kaynak: https://svs.gsfc.nasa.gov/20344/

Bu kaynakların ve credit bilgilerinin belirtilmesi, CMDRHelper'ın NASA
tarafından desteklendiği, onaylandığı veya yayımlandığı anlamına gelmez.
NASA medyasının yeniden kullanımında orijinal kaynaklardaki ilgili
açıklamalar ve çoğaltma yönergeleri geçerlidir.

## Lisans

CMDRHelper özgür yazılımdır ve **GNU General Public License Version 3
(GPL-3.0)** kapsamında yayımlanır.

Kaynak kod GPL-3.0 koşullarına uygun olarak kullanılabilir,
değiştirilebilir ve yeniden dağıtılabilir. Türetilmiş sürümlerin
dağıtımında da GPL-3.0 koşulları geçerlidir.

Copyright © 2026 **Holger Mangold (Faber38)**.

Tam lisans koşulları `LICENSE` dosyasında bulunur.

## Elite Dangerous hakkında not

CMDRHelper bağımsız bir topluluk/hobi projesidir ve Frontier
Developments'ın resmi bir ürünü değildir.

**Elite Dangerous** ve ilgili adlar ile içerikler kendi hak sahiplerine
aittir.
