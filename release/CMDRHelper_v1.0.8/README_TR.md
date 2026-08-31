# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) \| [🇬🇧 English](README.md) \| [🇫🇷
Français](README_FR.md) \| [🇮🇹 Italiano](README_IT.md) \| [🇳🇴
Norsk](README_NO.md) \| [🇸🇪 Svenska](README_SV.md) \| [🇫🇮
Suomi](README_FI.md) \| [🇵🇱 Polski](README_PL.md) \| [🇳🇱
Nederlands](README_NL.md) \| [🇪🇸 Español](README_ES.md) \| [🇹🇷
Türkçe](README_TR.md) \| [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper -- Elite Dangerous için yardımcı
pilotunuz](cmdrhelper/assets/readme/cmdrhelper_readme_tr.png)

**Elite Dangerous için kişisel yol arkadaşınız -- keşif, sistem analizi
ve Commander verileri tek bakışta**

CMDRHelper, **Elite Dangerous** için bağımsız bir masaüstü
uygulamasıdır. Oyunun yerel Journal dosyalarındaki bilgileri analiz eder
ve anlaşılır bir şekilde sunar. Amaç, bir sistemi keşfederken nelerin
zaten bilindiğini, hangi gök cisimlerinin ilgi çekici olduğunu ve
Commander'ın kendi keşifleri ile haritalamalarını hızlıca gösteren
kişisel bir yardımcı sunmaktır.

Proje hâlen aktif olarak geliştirilmektedir.

## İşlevlere genel bakış

### Elite Dangerous Journal'ları

CMDRHelper yerel Journal dosyalarını okur ve diğerlerinin yanı sıra
yıldız sistemlerini, yıldızları, gezegenleri, uyduları, Belt
Cluster'ları, taramaları, haritalamaları ve biyolojik/jeolojik
sinyalleri işler. Commander'ın kendi verileri, tamamlayıcı harici
bilgilerden ayrı olarak gösterilebilir.

### Görevler

CMDRHelper, Elite Dangerous Journal'larındaki görev olaylarını analiz
eder ve aktif görevleri anlaşılır biçimde gösterir. Görev durumu ve
ilgili Journal olayları takip edilir.

Oyun sırasında NPC mesajları (`ReceiveText`) üzerinden gelen görev
teklifleri de tanınabilir ve sonraki görev eşleştirmesine dahil
edilebilir. Elite Dangerous her görev türü için tüm bilgileri aynı
Journal olayında sağlamadığından, eşleştirme mevcut Journal verilerinden
adım adım oluşturulur.

### Sistem ve Explorer görünümü

Bir sistemde bilinen cisimler grafiksel olarak gösterilir ve doğrudan
seçilebilir. CMDRHelper diğerlerinin yanı sıra şunları gösterebilir:

-   cismin adı ve türü
-   sistem içindeki uzaklığı
-   Commander tarafından taranmış veya yalnızca harici kaynaktan
    biliniyor
-   daha önce keşfedilmiş ve haritalanmış
-   olası ilk keşif ve olası First Mapping
-   Commander tarafından haritalanmış
-   verimli haritalama
-   biyolojik ve jeolojik sinyaller
-   tarama ve haritalama değerleri

BIO sinyalleri ilgili cisim üzerinde belirgin şekilde vurgulanır.
Eşleştirme sistem bazında yapılır; böylece farklı yıldız sistemlerindeki
BodyID değerleri birbirine karıştırılmaz.

### Cisim ayrıntı görünümü

Bir cisme tıklandığında ayrıntılı bir görünüm açılır. Mevcut verilere
bağlı olarak cisim türü, kütle, uzaklık, yerçekimi, atmosfer,
volkanizma, iniş yapılabilirliği, terraforming durumu, materyaller,
BIO/GEO sinyalleri, tarama değeri, haritalama değeri ve keşif durumu
gösterilir.

Eksik bilgiler bilinmiyor olarak gösterilir ve kesin veriymiş gibi
sunulmaz.

## Cisimlerin grafiksel gösterimi

CMDRHelper; High Metal Content Worlds, Metal Rich Bodies, Rocky Bodies,
Icy Bodies, Rocky Ice Worlds, Earth-like Worlds, Water Worlds, Ammonia
Worlds, çeşitli gaz devi sınıfları, su veya amonyak tabanlı yaşama sahip
gaz devleri, helyum açısından zengin gaz devleri, farklı yıldız
sınıfları ve Belt Cluster'lar dahil olmak üzere çok sayıda cisim türü
için özel grafiklere sahiptir.

Genel görünümlerde normal PNG görüntüleri kullanılır. Birçok cisim için
animasyonlu ayrıntı görünümünde kullanılmak üzere ayrıca **2:1
equirectangular `_texture.png`** bulunur.

### Dönen 3D gezegenler

Uygun 2:1 dokular dönen bir küre üzerine yansıtılır. CPU renderer, ek
OpenGL/PyOpenGL bağımlılığı olmadan **PySide6 ve NumPy** ile çalışır.
Küre projeksiyonu, yavaş dönüş, aydınlatma, kenar karartması ve
atmosferik kenar efektini içerir.

### Animasyonlu yaşam biçimleri

Yaşam içeren gaz devleri için farklı animasyonlar bulunur:

**Water Life:** hale ve hareketli kuyruklara sahip, camgöbeği/turkuaz
renkli süzülen organizmalar.

**Ammonia Life:** titreşen çekirdeğe, kısa liflere ve daha yavaş
harekete sahip, mor/kehribar tonlarında yarı saydam özel organizmalar.

### Animasyonlu Belt Cluster'lar

Belt Cluster'lar küre olarak gösterilmez. Ayrıntı görünümü; ayrı
asteroitler, farklı boyut ve derinlikler, kendi dönüşleri, bireysel
sürüklenme, paralaks efekti, kraterler ve hafif toz/parçacık efektleri
içeren prosedürel bir asteroit alanı oluşturur.

## Tamamlayıcı veri kaynağı olarak EDSM

CMDRHelper kendi Journal verileri ile EDSM bilgilerini birbirinden
ayırabilir. Kaynak buna göre kendi Journal'ı, EDSM veya kendi
Journal'ı + EDSM olarak işaretlenir. Kendi Journal verileri özellikle
önemlidir, çünkü ilgili Commander'ın gerçekte neleri bizzat taradığını
veya haritaladığını gösterir.

CMDRHelper yeni Journal verilerini otomatik olarak EDSM'ye aktarabilir.
Güncel dinamik EDSM Discard listesi dikkate alınır; böylece yalnızca
EDSM'nin istediği olaylar gönderilir. Aktarım ilerlemesi her Journal
dosyası için güvenli şekilde kaydedilir. İlk etkinleştirmede önceden
mevcut eski Journal'lar yeniden bütünüyle gönderilmez.

EDSM durumu doğrudan genel görünümün üst kısmında gösterilir. Yeşil
gösterge aktarımın çalıştığını belirtir; hatalar kırmızı gösterilir ve
ayrıca CMDRHelper günlüğüne kaydedilir.

## Yerel veritabanı

CMDRHelper SQLite kullanır. Aşağıdaki kurallar geçerlidir:

-   `cmdrhelper/database.py` program kodudur ve sürüme dahildir.
-   `data/cmdrhelper.db` kişisel Commander verilerini içerir ve
    **dağıtılmaz**.
-   Yeni kurulumda yerel veritabanı ilgili kullanıcı için yeniden
    oluşturulur.

Böylece hiçbir kişisel Commander verisi sürümle birlikte dağıtılmaz.

## Tanılama ve günlük dosyası

CMDRHelper, tanılama ve hata ayıklama için kendi dönen günlük dosyasını
tutar. Önemli program, Journal, veritabanı ve EDSM olayları kaydedilir.
EDSM günlük kaydı azaltılmıştır; böylece yalnızca EDSM tarafından
reddedilen Journal olayları normal günlüğü gereksiz yere doldurmaz,
başarılı aktarımlar, uyarılar ve hatalar ise görünür kalır.

## Platformlar

CMDRHelper Python ve PySide6 ile geliştirilmiştir ve **Linux ile
Windows** için tasarlanmıştır. Geliştirme ağırlıklı olarak Linux altında
yapılır; Windows, birlikte verilen batch dosyaları kullanılarak
kurulabilir.

## Gereksinimler

Python 3 ve `requirements.txt` içindeki paketler:

``` text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

## Linux altında kurulum

``` bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Alternatif olarak mevcut Linux başlangıç betikleri kullanılabilir.

## Windows altında kurulum

Windows için `install.bat` ve `start.bat` kullanılması öngörülmüştür.

`install.bat` Python 3'ü kontrol eder, `venv` oluşturur, pip'i günceller
ve `requirements.txt` içeriğini kurar. Ardından CMDRHelper `start.bat`
üzerinden başlatılır.

## Sürüm oluşturma

``` bash
./create_release.sh
```

Sürüm numarası doğrudan betikte belirlenir. Oluşturulan ZIP dosyası
program kodunu ve asset'leri içerir; ancak kişisel veritabanını, sanal
Python ortamını veya Git, önbellek ve editör dosyalarını içermez.

## Sürüm 1.0.8

**Sürüm 1.0.8**, keşif için kişisel bir atlayış önerisi ekler,
uluslararasılaştırmayı daha da tamamlar ve Keşif canlı pencereleriyle
Kronik haritasının görünümünü iyileştirir.

### Atlayış ipucu ve atlayış önerisi

-   yeni **“Atlayış ipucu”** bölümü kendi yerel keşif veritabanınızı analiz
    eder ve seçilen bir keşif hedefi için hangi prosedürel sistem kodlarının
    özellikle ilgi çekici olabileceğini gösterir.
-   seçilebilen hedefler arasında genel BIO bulguları, bilinen BIO cinsleri
    ve türleri, değerli keşif gökcisimleri, terraform adayları, Su Dünyaları,
    Dünya benzeri gezegenler ve Amonyak Dünyaları bulunur.
-   sıralama, bir kodla daha önce incelenen sistemleri, isabetleri, isabet
    oranını, kayıtlı bulguları ve mevcut örneklem büyüklüğünü dikkate alır.
    Ayarlanabilir minimum incelenmiş sistem sayısı, çok küçük veri
    kümelerinin gereğinden fazla değerlendirilmesini önler.
-   CMDRHelper, Galaksi Haritası’nda aranabilecek tercih edilen kodları,
    örneğin `ZL-Z b` veya `NR-C d` gibi birleşimleri vurgular.
-   öneri yalnızca **kendi önceki keşif geçmişinize** ve orada kayıtlı
    bulgulara dayanır. İstatistiksel bir yönlendirmedir ve **bulgu garantisi
    vermez**.

### Uluslararasılaştırma

-   uluslararasılaştırma daha da tamamlandı ve Almanca referansla yeniden
    karşılaştırıldı.
-   desteklenen **12 arayüz dilinin** tamamı artık aynı eksiksiz **560 çeviri
    anahtarı** kümesine sahiptir.
-   **atlayış ipucu ve atlayış önerisi** için yeni ve daha önce eksik olan
    çeviriler desteklenen tüm dillere eklendi.
-   anahtar kümeleri, sıraları ve biçimlendirme yer tutucuları tüm dil
    dosyalarında eşitlendi.

### Keşif canlı pencereleri ve ayarlar

-   Keşif ayarlarına **“Değerli gökcisimleri”** ve **“BIO bulguları”**
    pencerelerinin otomatik gösterimi için yeni açıklayıcı araç ipuçları
    eklendi.
-   araç ipuçları, ayarlanan değer eşiğine veya algılanan BIO ya da GEO
    sinyallerine göre her pencerenin ne zaman otomatik açıldığını açıklar.
-   Commander tarafından zaten haritalanmış değerli gökcisimleri küçük canlı
    pencerede artık açık hedef olarak gösterilmez.
-   tamamen analiz edilmiş BIO gökcisimleri BIO canlı penceresinden kaybolur;
    aynı gökcisminin DSS ile henüz haritalanmamış GEO bölümü görünür kalır.

### Kronik

-   Kronik haritasının yönü, pozitif Z ekseni yukarıyı gösterecek şekilde
    düzeltildi. Kayıtlı Elite `StarPos` koordinatları değişmeden kalır.

## Sürüm 1.0

**Sürüm 1.0** ile CMDRHelper, planlanan temel kapsamın ilk eksiksiz
geliştirme aşamasına ulaşır.

Sürüm 1.0'a kadar olan önemli değişiklikler ve genişletmeler:

### Cisim ve yıldız gösteriminin tamamlanması

-   desteklenen gezegen, yıldız ve özel nesne türleri için görsel
    materyaller daha da tamamlandı.
-   ek yıldız sınıfları ve özel yıldız türleri, genel varsayılan
    gösterime dönmek yerine kendi grafikleriyle gösteriliyor.
-   uygun cisimler için dönen 2:1 equirectangular dokular ayrıntı
    görünümünde kullanılmaya devam ediyor.
-   özel astronomik nesneler ayrıntı görünümünde ayrıca uygun videolarla
    gösterilebiliyor.
-   nötron yıldızları, beyaz cüceler, kara delikler ve süper kütleli
    kara delikler böylece çok daha özgün bir görünüme kavuşuyor.
-   kullanılan harici görsel ve video materyalleri, **"Görsel ve video
    materyalleri / Media Credits"** bölümünde kaynak ve credit
    bilgileriyle belgeleniyor.

### Çok dilliliğin tamamlanması

-   kullanıcı arayüzü çevirileri desteklenen diller için tamamlandı ve
    ortak bir anahtar kümesine göre eşitlendi.
-   **12 arayüz dilinin** tamamı aynı eksiksiz çeviri anahtarı kümesini
    kullanıyor.
-   otomatik çeviri denetimi eksik, fazla ve yinelenen anahtarların yanı
    sıra farklı biçimlendirme placeholder'larını da kontrol ediyor.
-   Almanca, kullanıcı arayüzü ve sonraki dokümantasyon için eksiksiz
    olarak bakımı yapılan referans sürüm işlevi görüyor.

### Sürüm 0.9.9'dan bu yana değişiklikler

### Çok dillilik ve çeviri denetimi

-   kullanıcı arayüzü merkezi bir çok dilli sisteme geçirildi.
-   CMDRHelper artık **12 arayüz dilini** destekliyor: **Almanca,
    İngilizce, Fransızca, İtalyanca, Norveççe (Bokmål), İsveççe, Fince,
    Lehçe, Felemenkçe, İspanyolca, Türkçe ve Yunanca**.
-   dil ayarlardan seçilip kaydedilebilir; dil adları seçim alanında
    kendi dillerinde gösterilir.
-   eksik çeviriler tanımlanmış bir fallback sırası kullanır: **seçilen
    dil → İngilizce → Almanca → çeviri anahtarı**.
-   çeviriler merkezi olarak `cmdrhelper/i18n/` altındaki dil
    dosyalarında bulunur.
-   yeni geliştirici aracı `tools/check_i18n.py` otomatik olarak şunları
    kontrol eder:
    -   programda kullanılan `tr("...")` anahtarları,
    -   eksik veya fazla çeviri anahtarları,
    -   yinelenen anahtarlar,
    -   `{system}` veya `{count}` gibi farklı biçimlendirme
        placeholder'ları.
-   Linux altında i18n denetimi başlangıç sırasında `start.sh` üzerinden
    otomatik olarak çalıştırılır. Bulunan çeviri sorunları açıkça
    bildirilir, ancak programın başlamasını engellemez.
-   görev ve Journal işleme, seçilen CMDRHelper arayüz dilinden ayrı
    tutulmaya devam eder; böylece Elite Dangerous'ın dahili verileri
    yerelleştirilmiş görüntü metinlerine bağımlı olmaz.

### Explorer ve sistem haritası

-   sistem haritasındaki Parent/Child yapısı yeniden düzenlendi:
    yıldızlar, gezegenler, uydular ve Belt Cluster'lar Journal
    hiyerarşisine göre yerleştiriliyor.
-   tüm sistemin kompakt küçük resim görünümünü sunan yeni **"Tümünü
    göster"** işlevi.
-   küçük resim görünümündeki cisimlere tıklanabilir; ana harita
    ardından doğrudan seçilen cisme geçer.
-   büyük sistem haritalarında geliştirilmiş gezinme:
    -   fare tekerleği haritayı yatay olarak hareket ettirir.
    -   sağ fare düğmesini basılı tutup yukarı/aşağı sürüklemek haritayı
        dikey olarak hareket ettirir.
-   cisimlerin görsel boyutları gerçek yarıçapa göre daha belirgin
    ölçeklendirilir.
-   BIO, GEO, Terraforming, ilk keşif ve First Mapping gösterimi ve
    işaretlemesi daha da geliştirildi.
-   Explorer'da yeni **değer listesi**: gezegenler ve uydular mevcut
    tahmini haritalama değerlerine göre satır satır sıralanır.
-   değer listesi artık **First Mapping mümkün**, **zaten haritalanmış**
    ve **Commander tarafından haritalanmış** durumlarını açıkça ayırır.
-   gerçekten elde edilen haritalama değeri değer listesinde özellikle
    vurgulanırken durum ve meta veriler bilinçli olarak daha sade
    gösterilir.
-   son satıştan bu yana tüm sistemlerdeki açık haritalama ve BIO
    değerleri için yeni **"Henüz teslim edilmedi"** görünümü; haritalama
    ve BIO ayrı ayrı sıfırlanır.
-   açık Explorer değerleri ana pencerede sarı renkle vurgulanır;
    böylece henüz satılmamış veriler hemen fark edilir.

### Explorer canlı pencereleri

-   keşif sırasında otomatik olarak gösterilen, serbestçe
    konumlandırılabilen **değerli cisimler ve BIO bulguları için canlı
    pencereler**.
-   canlı pencerelerin konumu ve boyutu kaydedilir ve bir sonraki
    gösterimde yeniden kullanılır.
-   başka bir yıldız sistemine geçildiğinde canlı pencereler otomatik
    olarak kapatılır ve temizlenir; yeni sistemde uygun veriler
    algılandığında yeniden görünürler.
-   **"Değerli cisimler"** penceresi, şu anda elde edilebilecek
    haritalama değeri ayarlarda seçilen eşiğe ulaşan tüm gezegen ve
    uyduları otomatik olarak içerir.
-   aynı ayarlanabilir eşik artık değer listesindeki sarı vurguyu,
    değerli cisimler canlı penceresini ve **sistem haritasındaki altın
    çerçeveyi** kontrol eder.
-   **BIO canlı penceresi**, oyun sırasında cisimleri, tanınan cins veya
    türleri, tarama ilerlemesini ve bilinen Vista Genomics değerlerini
    kompakt biçimde gösterir.
-   BIO bulguları ana penceredekiyle aynı renk mantığını kullanır: gri =
    DSS/FSS ile algılandı, beyaz = ilk örnek, sarı = ikinci örnek, yeşil
    = analiz tamamlandı.
-   kısmen belirlenmiş BIO sinyallerinde gezegen otomatik olarak
    genişletilir ve ayrı bulgular kendi satırlarında gösterilir; henüz
    bilinmeyen sinyaller görünür kalır.
-   bir cisimdeki tüm BIO türleri tamamen analiz edildiğinde gezegen
    tekrar kompakt yeşil bir özet satırına daraltılır.
-   genel DSS/FSS cins adları, `ScanOrganic` aracılığıyla somut BIO türü
    bilinir bilinmez otomatik olarak onunla değiştirilir.
-   bilinen tekil değerler doğrudan ilgili BIO bulgusunun yanında
    gösterilir; tamamen bilinen cisimler ayrıca toplam değeri gösterir.
-   canlı pencereler hafif kırmızımsı kahverengi bir arka plana
    sahiptir; böylece oyun sırasında CMDRHelper ana penceresinden açıkça
    ayrılır.

### BIO analizi

-   biyolojik veriler normal haritalama değerlerinden ayrı analiz edilir
    ve gösterilir.
-   biyolojik sinyal tespit edilen tüm cisimleri içeren ayrı bir **BIO
    gezegen listesi**.
-   `SAASignalsFound` veya `FSSBodySignals` içindeki BIO cinsleri mevcut
    Journal'lardan geriye dönük olarak da alınır.
-   `ScanOrganic` içindeki somut BIO türleri ve varyantları doğrudan
    listede gösterilir.
-   her BIO bulgusunun tarama ilerlemesi renklerle gösterilir:
    -   gri = yalnızca DSS/FSS üzerinden biliniyor
    -   beyaz = ilk örnek
    -   sarı = ikinci örnek
    -   yeşil = üçüncü örnek / analiz tamamlandı
-   bilinen Vista Genomics temel değeri, BIO türü kesin olarak
    belirlendiği anda gösterilir.
-   tamamen analiz edilmiş BIO örneklerinin temel değerinin gösterimi.
-   olası **First Logged toplam değerinin ×5** gösterimi.
-   bilinen BIO değerleri mevcut satış verileriyle tamamlanabilir.
-   değeri bilinmeyen türler analizde işaretlenir.
-   BIO durumu açık, ziyaret edilmiş ve tamamen analiz edilmiş
    durumlarını birbirinden ayırır.

### Görevler

-   `MissionRedirected` işleme geliştirildi.
-   yönlendirilmiş görevler ad, yeni hedef sistem veya yeni hedef
    istasyon ile önceki hedefe ilişkin bilgileri devralabilir.
-   bazı durumlarda daha önce eksiksiz bir `MissionAccepted` kaydı
    bulunmasa bile görevler yeniden oluşturulabilir.
-   görev sütunlarının genişliği serbestçe ayarlanabilir; seçilen
    genişlikler kaydedilir.
-   **şu anda açık olan tüm görevlerin toplam ödülünün** gösterimi.

### Görseller ve ekran görüntüleri

-   galeri ve önizleme içeren ayrı ekran görüntüsü alanı.
-   yeni Elite Dangerous BMP ekran görüntülerinin otomatik
    dönüştürülmesi.
-   PNG veya JPG olarak çıktı.
-   başarılı dönüştürmeden sonra BMP dosyasının isteğe bağlı silinmesi.
-   %0 ile %50 arasında ayarlanabilir parlaklık düzeltmesi.
-   Steam/Proton altında Elite ekran görüntüsü klasörünün daha rahat
    kullanımı.
-   dosyalar dışarıdan silindikten sonra galeri de güncellenir.
-   otomatik dönüştürme ve silme seçeneklerinin görünürlüğü
    iyileştirildi.

### Çevrimiçi hizmetler

-   otomatik EDSM Journal aktarımı daha da entegre edildi ve ana
    penceredeki durum alanında görünür hale getirildi.
-   aktarım, bekleme, hata ve devre dışı EDSM durumları.
-   daha sonra eklenecek otomatik aktarım için hazırlık olarak Inara
    durum göstergesi.

### Kullanım ve kararlılık

-   arayüz yazı tipi ve yazı boyutu ayarlardan seçilebilir ve yeniden
    başlatmadan sonra tüm arayüze uygulanabilir.
-   ayarlar sayfası kaydırılabilir; böylece daha küçük pencere
    boyutlarında da tüm seçeneklere erişilebilir.
-   sol kenar çubuğunda görünür **"Çıkış"** düğmesi.
-   Single Instance kilidi ikinci bir program örneğinin yanlışlıkla aynı
    anda başlatılmasını önler.
-   zaten görünür olan Explorer widget'ını doğrudan render etmeden
    güvenli sistem küçük resim görünümü.
-   arayüz, Journal işleme, veritabanı ve güncelleme sürecinde çeşitli
    iyileştirmeler.

## Proje durumu

CMDRHelper geliştirme aşamasındadır. Kullanıcı arayüzü, veri modeli ve
gösterim biçimi hâlâ değişebilir. Daha fazla cisim türü, Journal işlevi,
Explorer işlevi, veri kaynağı ve hesaplama planlanmaktadır. Linux ve
Windows üzerinde testler devam etmektedir.

CMDRHelper kişisel bir araç olarak başladı ve adım adım daha kapsamlı
bir Elite Dangerous yardımcısına dönüştürülmektedir.

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
