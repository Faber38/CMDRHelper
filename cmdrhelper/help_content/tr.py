"""Turkish content for contextual help."""


HELP_TOPICS = {
    "materials": (
        'Malzemeler',
        """<h2>Malzemeler</h2>
<h3>CMDRHelper</h3>
<p>Mühendislik malzemesi yönetimi: Raw, Manufactured ve Encoded kategorilerindeki 146 malzemenin tamamı; dereceler, kapasiteler ve istisnalarla birlikte. Komutana özel güncel stok, arama, filtreler, beş sade satır arka planı ve kaydedilen sütun genişliği/sırası görünümü kolaylaştırır. Bilinmeyen stok sıfırdan ayrı tutulur.</p>
<p>Odyssey envanteri: dördüncü malzeme sekmesi mallar, malzemeler, veriler ve tüketim malzemeleri için 223 katalog kimliği içerir. Gemi dolabı, sırt çantası ve güvenilir toplam ayrı tutulur; görev yığınları, görev durumu ve mühendislik kullanımı gösterilir. Pozitif stok sayıları altın rengindedir. Çevrilmemiş adlar İngilizce gösterilir.</p>
<p>Malzeme tüccarı araması (Tüccar ara → Rota planlayıcıyı aç): Spansh, istek üzerine komutanın mevcut sisteminden Raw, Manufactured ve Encoded için ayrı arama yapar. Carrier’lar dışlanır ve istasyon ayrıntıları doğrulanır. ly cinsinden mesafe sistemler arasındaki doğrudan uzaklıktır; topluluk verileri erişim garantisi vermez. Rota planlayıcısına aktarım yalnızca hedef sistemi ayarlar, rota başlatmaz. Odyssey tüccarı araması yoktur.</p>
<p>Bu ana bölüm, o anda görüntülenen komutanın mühendislik malzemelerini gösterir. CMDR görünümündeki seçim burada da geçerlidir; diğer komutanların verileri ayrı tutulur.</p>
<h3>Üç kategori</h3>
<p>Ham malzemeler, Üretilmiş malzemeler ve Kodlanmış veriler sekmeleri, Guardian ve Thargoid malzemeleri dahil katalogdaki 146 malzemenin tamamını içerir. Liste dereceye göre, her derece içinde de alfabetik olarak sıralanır.</p>
<h3>Stok ve çubuklar</h3>
<p>Sayılar stok / üst sınır değerini gösterir; örneğin Vanadyum 244 / 250. İlgili çubuk 97,6 % gösterir. Hiç sahip olunmamış malzemeler de stok güvenilir biçimde biliniyorsa 0 ile gösterilir.</p>
<p>Boş stoklar soluk kırmızıyla, az stoklar sarı/turuncuyla, neredeyse dolu veya dolu stoklar yeşille işaretlenir. Sayılar renklerden bağımsız olarak görünür kalır.</p>
<h3>Arama ve filtreler</h3>
<p>Arama, malzemenin görüntülenen ve İngilizce adını dikkate alır. Tüm filtrelerle birleştirilebilir: Tümü, Boş (0), Az (0’dan fazla, 20 % dahil), Neredeyse dolu (80 % dahil, 100 %’den az) ve Dolu (100 %). 20 % ile 80 % arasındaki değerler yalnızca Tümü altında görünür. Sekmeler ve filtreler sonraki başlatmada geri yüklenir.</p>
<h3>Bilinmeyen değerler</h3>
<p>Güvenilir ve tam bir stok bilgisi olmadan örneğin ? / 250 gösterilir. Üst sınır bilinmiyorsa 12 / ? gibi bir değer gösterilebilir. Her iki durumda da yüzde veya çubuk yoktur; bu malzemeler yalnızca Tümü altında görünür. Bilinmeyen derece, listenin sonunda ayrı bir grupta yer alır.</p>
<h3>Canlı güncelleme</h3>
<p>Yeni günlük olayları, malzeme takası, mühendislik, sentez veya malzeme ödüllerinden sonra da stoku otomatik günceller. İlk okuma sırasında yükleme bildirimi gösterilir. Yeni toplanan malzeme, Vanadyum +1 gibi bir ifadeyle kısa süreli vurgulanır; tüketim bir toplama bildirimi oluşturmaz.</p>
<h3>Malzeme adları</h3>
<p>Bir malzemenin adı seçilen dilde henüz mevcut değilse İngilizce görüntüleme adı kullanılır. Günlüğün dahili simgeleri mevcut görüntüleme adlarının yerini almaz.</p>
<h3>Odyssey</h3>
<p>“Çalıntı”, kayıtlı Elite verilerinde açıkça çalıntı olarak belirtilen envanter yığınını işaretler. Bu bilginin bulunmaması, çalıntı olmadığını doğrulamaz. Sahip kimliği biliniyorsa araç ipucunda “Sahip” olarak gösterilir; bilinmeyen bir sahip adı eklenmez.</p>
<p>“Güncel bulunabilirlik doğrulanmadı” araç ipucu, ilgili özel malzemelerin edinme kaynağının doğrulanmadığını belirtir. CMDRHelper güncel ve doğrulanmış edinme bilgisi veremez; bu, öğenin elde edilemez olduğu anlamına gelmez.</p>

<p>Malzemeler altındaki dördüncü sekme Mallar, Malzemeler, Veriler ve Sarf malzemeleri bölümlerini içerir. Dolap ve sırt çantası kişisel stokları gösterir. Filo Gemisi ✎, kendi filo geminizdeki mallar, malzemeler ve veriler için elle onaylanan özel stoku gösterir. Onaylamak, düzeltmek veya bilinmiyor olarak ayarlamak için çift tıklayın. — bilinmiyor demektir; 0 açıkça onaylanmalıdır. Toplam, dolap, sırt çantası ve filo gemisini yalnızca değerler biliniyor ve tutarlıysa içerir. Birden fazla yığında filo gemisi stoku özette bir kez gösterilir; yığınlar ayrı kalır. Sarf malzemeleri filo gemisi olmadan kişisel toplamı korur. FCMaterials tam bir filo gemisi envanteri değildir ve bu şekilde kullanılmaz. 1000 olan dolap sınırı eşya başına değil, kategori başınadır. Filo gemisi stoku son onaylanan değerden hesaplanır. Dolap değişiklikleri yalnızca kendi filo geminizde, açık kişisel işlemler çıkarıldıktan sonra karşılıklı işlenir. Barmendeki alım ve satımlar, özellikle diğer oyuncuların işlemleri, otomatik kaydedilmeden gerçek stoku değiştirebilir. Gerektiğinde çift tıklayarak yeniden onaylayın. Toplam, son onaylanan stoktan hesaplanan tahmini kullanır; garantili canlı sorgu değildir. Özel Odyssey deposu mallar, malzemeler ve veriler arasında 1.000 yeri paylaşır. Stok toplamı ancak tüm kalemler ve ek malzemeler sıfırlar dahil onaylandığında tam bilinir. Aksi halde asgari miktar gösterilir. Sınır aşılırsa değerler korunur ve Toplam bilinmez olur. Dolap, sırt çantası ve pazar rezervasyonları geminin özel malzeme stoku değildir.<br><b>! – Filo gemisi stokunu ayarla</b><br>Filo gemisi sütununa çift tıklayıp HER kalem için gemideki mevcut miktarı gir. TÜM boş kalemleri de açıkça 0 ile onayla.<br>— = henüz onaylanmadı / bilinmiyor<br>0 = açıkça onaylanmış boş stok</p>
<p>Barmendeki açık alım emirleri depo kapasitesi ayırır. Oyundaki doluluk mevcut malzeme stokunu aşabilir. Ayrılan kapasite malzeme değildir ve malzeme toplamlarına eklenmez. Yeterince güncel pazar verisi yoksa doluluk bilinmez. Diğer oyuncuların ticareti bu anlık görüntüyü değiştirebilir.</p>
<p>Kullanım, nesnenin kullanım işaretlerini gösterir. Görev, envanterdeki belirli yığının bir göreve bağlı olduğu anlamına gelir; nesne türünün genel olarak bir görev nesnesi olduğu anlamına gelmez. Normal ve göreve bağlı yığınlar ayrı tutulur. Görev tamamlandıktan sonra da günlük nesneyi envanterde gösterdiği sürece işaret korunur; görevin tamamlanması nesneyi otomatik olarak kaldırmaz. Araç ipucu görev numarasını ve bilinen durumunu gösterir. Mühendislik, statik Odyssey kataloğunun en az bir doğrulanmış kullanım bildiği anlamına gelir: giysi yükseltmesi, silah yükseltmesi, giysi modifikasyonu, silah modifikasyonu veya bir mühendisin kilidini açma. Tek tek kullanımlar araç ipucunda yer alır. İşaretin olmaması nesnenin işe yaramaz veya yalnızca ticaret için olduğu anlamına gelmez. Powerplay nesneleri ve diğer özel nesneler de gösterilebilir.</p>
<p>Arama, malzemelerin/nesnelerin görüntülenen yerel adlarını ve İngilizce adlarını bulur. Altı Odyssey filtresi şunlardır: Tümü (tüm nesneler), Görev (bir göreve bağlı yığınlar), Mühendislik (doğrulanmış mühendislik kullanımı olan nesneler), Sırt çantası (sırt çantası stoku sıfırdan büyük), Gemi dolabı (dolap stoku sıfırdan büyük) ve Stok 0 (güvenilir biçimde bilinen toplam stok 0). Bilinmeyen stok — değeri 0 değildir ve Stok 0 filtresine dahil edilmez. Ad çevirisi eksikse İngilizce ad kullanılır; bu nedenle seçilen dilde bazı adlar İngilizce kalabilir. Bu kasıtlıdır ve envanter mantığında bir çeviri hatası değildir.</p>
<p>Kişisel envanter arka planda otomatik olarak güncellenir. Doğrulanmış yeni toplamalar kısa süreli vurgulanabilir. Komutan değiştirildiğinde eski stoklar hemen kaldırılır. Alt sekmeler, filtreler, sütun genişlikleri ve sıralaması Odyssey için ayrı kaydedilir.</p>
<h3>Mining</h3>
<p>Malzemeler → Mining, mühendislik malzemelerinden ayrı olarak, şu anda bilinen 57 ticareti yapılabilir madencilik emtiasının ortak görünümüdür. Tek tablo hem gezegen yüzeyi hem de asteroit/halka madenciliğini kapsar. Sabit referans fiyatlar yalnızca yol göstericidir; canlı piyasa fiyatları değildir.</p>
<p><b>Sütunlar</b><br><b>Ham madde:</b> emtianın veya kaynağın adı.<br><b>SRV:</b> SRV içindeki doğrulanmış stok.<br><b>Gemi:</b> gemideki doğrulanmış stok.<br><b>Filo taşıyıcısı:</b> kendi carrier’ınızdaki stok; Elite tam kişisel envanter sağlamadığından başlangıç stoku elle onaylanmalıdır.<br><b>Toplam:</b> SRV + Gemi + Carrier, yalnızca üç stok da biliniyorsa. Aksi halde —; bilinmeyen sıfır değildir.<br><b>Ort. fiyat Cr/t:</b> güncel satış fiyatını garanti etmeyen sabit referans değeri. Eksik referans fiyatlar bilinmiyor olarak kalır.<br><b>Değer sınıfı:</b> YÜKSEK en az 100.000 Cr/t; ORTA 25.000–99.999 Cr/t; DÜŞÜK 25.000 Cr/t altında. Fiyat bilinmiyorsa değer sınıfı atanmaz.</p>
<p><b>Carrier stokunu onaylama</b><br>Elite Dangerous, CMDRHelper’a tam kişisel carrier envanteri sağlamaz. Bir emtia için bilinen başlangıç noktası oluşturmak için: 1. Carrier hücresine çift tıklayın. 2. Mevcut stoku 0 veya daha büyük bir tam sayı olarak girin. 3. Değeri uygulayarak elle onaylayın. 4. CMDRHelper bundan sonra geminiz ile kendi carrier’ınız arasındaki açık ve kesin CargoTransfer olaylarını otomatik izler. Araç ipucu elle onayı ve varsa sonraki otomatik güncellemeyi gösterir.</p>
<p><b>— = stok bilinmiyor</b><br>Onaylanmış başlangıç stoku olmadan tekil transferlerden güvenilir bir mutlak carrier stoku hesaplanamaz. Çift tıklayarak değeri istediğiniz zaman değiştirebilir, düzeltebilir veya bilinmiyor durumuna sıfırlayabilirsiniz. Bir transfer çelişkili ya da negatif sonuç oluşturacaksa stok yeniden bilinmiyor olarak işaretlenir ve elle tekrar onaylanmalıdır.</p>
<p><b>Gemi ve SRV</b><br>SRV ve gemi stokları doğrulanmış kargo verilerinden ayrı ayrı oluşturulur. Bilinmeyen miktarlar — olarak kalır. Tam kargo anlık görüntüleri hesaplanan değişikliklerden önce gelir.</p>
<p><b>↻ Yenile</b><br>SRV stoku ve gemi stoku doğrulanmış verilerle ayrı ayrı yenilenir. Onaylanmış carrier stoku bundan bağımsız olarak korunur. Normal canlı güncellemeler otomatik olarak devam eder. Yeşil hazır veya başarılı, renk animasyonu devam eden yenileme, kırmızı ise başarısız deneme anlamına gelir. Eksik ya da doğrulanamayan veriler boş stok olarak gösterilmez.</p>
<p><b>Filtreleri birleştirme</b><br>Kaynak araması ada göre filtreler. Değer sınıfı Tümü, YÜKSEK, ORTA ve DÜŞÜK seçeneklerini; köken ise Tümü, Gezegensel madencilik ve Asteroitler/Halkalar seçeneklerini sunar. “Yalnızca stoktakiler”, SRV, gemi veya carrier içindeki bilinen stoklardan en az biri pozitifse emtiayı gösterir. Bilinmeyen stoklar 0 sayılmaz ve başka bir konumdaki bilinen pozitif stoku gizlemez. Arama, değer sınıfı, köken ve stok filtresi birlikte kullanılabilir.</p>
<p><b>Keşif görünümünde ABBAU ×N</b><br>Tıklamak Malzemeler → Mining bölümünü açar ve köken filtresini otomatik olarak Gezegensel madencilik yapar. Keşif görünümünde ikinci bir Mining tablosu yoktur.</p>
<p><b>Sıralama ve genişlikler</b><br>Artan veya azalan sıralama için sütun başlıklarına tıklayın. Stoklar ve fiyatlar sayısal sıralanır; bilinmeyenler sona gelir. Genişlikleri ayarlamak için sütun sınırlarını fareyle sürükleyin. Sıralama, sütun genişlikleri ve değer sınıfı, köken ile Yalnızca stoktakiler filtre durumları kaydedilir.</p>
<p><b>Köken</b><br>Surface gezegen yüzeyi madenciliği, Asteroid asteroit/halka madenciliği demektir. Bazı kaynaklar her iki ortamdan gelir (Both) ve ilgili iki köken filtresinde de görünür.</p>""",
    ),'overview': ('Genel Bakış',
              '<h2>Genel Bakış</h2>\n'
              "<p>Genel bakış CMDRHelper'nin ana sayfasıdır. Şu anda aktif olan komutan hakkındaki "
              'en önemli bilgileri özetler ve günlüğün, konumun ve çevrimiçi hizmetlerin doğru '
              'şekilde tanınıp tanınmadığını bir bakışta gösterir.</p>\n'
              '\n'
              '<h3>Komutan ve gemi</h3>\n'
              "<p>Elit Tehlikeli Günlüğü'nden tanınan komutan ve halihazırda kullanımda olan gemi "
              'burada görüntülenir.</p>\n'
              '<p>CMDRHelper, Frontier Kimliğine (FID) dayalı olarak kişisel verileri ilgili '
              'komutana atar. Bu, farklı komutanlardan gelen verileri birbirinden ayrı tutar.</p>\n'
              '<p>Komutan değiştirilirken yeni komutana ait kayıtlı bilgiler yüklenir.</p>\n'
              '\n'
              '<p>CMDRHelper, Elite tarafından en son bildirilen oyun modunu gösterir. Open, Solo ve Özel grup, LoadGame üzerinden tanınır. Özel gruplarda Elite tarafından bildirilen grup adı değiştirilmeden gösterilir. Bu, Elite’ın şu anda çalıştığı anlamına gelmez.</p>\n'
              '<h3>günlük</h3>\n'
              "<p>CMDRHelper, ana veri kaynağı olarak Elite Dangerous'nin günlük dosyalarını "
              'kullanır.</p>\n'
              '<p>Günlük ekranı, günlük dosyalarının bulunup bulunmadığı ve aktif komutana atanıp '
              'atanmadığı konusunda bilgi verir. Yeni eksiksiz günlük girişleri oyun sırasında '
              'otomatik olarak işlenir.</p>\n'
              "<p>Zaten işlenmiş olan günlük alanları kaydedilir, böylece CMDRHelper'nin bir "
              'sonraki başlatılışında her günlüğü yeniden tam olarak değerlendirmesi '
              'gerekmez.</p>\n'
              '\n'
              '<h3>Mevcut konum</h3>\n'
              '<p>Şu anda bilinen yıldız sistemini ve günlükten bilindiği kadarıyla komutanın tam '
              'yerini gösterir.</p>\n'
              '<p>Konum, atlamalar, yanaşma ve diğer konum raporları gibi olaylarla güncellenir ve '
              'komutan bazında saklanır.</p>\n'
              '\n'
              '<h3>Görevler</h3>\n'
              '<p>Bu alan şu anda bilinen açık görevlerin sayısını gösterir.</p>\n'
              '<p>“Görevler →”, bilinen görev hedefleri ve durum '
              'bilgilerini içeren “Görevler ve Ödüller” ana bölümünü açar.</p>\n'
              '\n'
              '<h3>Son durum</h3>\n'
              '<p>“Son durum” bilinen son kalıcı komutan durumunu özetlemektedir. Bu, Elite '
              'Dangerous veya CMDRHelper yeniden başlatıldıktan sonra bile önemli bilgilerin geri '
              'yüklenmesine olanak tanır.</p>\n'
              '\n'
              '<h3>Son ziyaret edilen sistemler</h3>\n'
              '<p>Günlükte yakın zamanda ziyaret edilen veya tanınan sistemler burada '
              'görüntülenir.</p>\n'
              '<p>Liste, Komutanın son yolculuğuna hızlı bir genel bakış görevi görüyor.</p>\n'
              '<p>Ziyaret geçmişi canlı günlük takibinde de Location, FSDJump ve CarrierJump olaylarını dikkate alır. Aynı kesintisiz kalıştaki birden çok konum olayı tek ziyaret sayılır: A → A → A bir kez sayılır. Gerçek bir dönüş korunur: A → B → C → A dört ziyaret sayılır.</p>\n\n'
              '<h3>Çevrimiçi durum</h3>\n'
              '<p>Ana pencerenin üst kısmında ek durum göstergeleri vardır:</p>\n'
              '<ul>\n'
              '<li><b>Günlük tanındı</b>– CMDRHelper geçerli bir günlük kaynağı ve komutan kimliği '
              'tespit etti.</li>\n'
              '<li><b>EDSM</b>– FID aktif günlüğü için EDSM iletiminin mevcut durumunu '
              'gösterir.</li>\n'
              '<li><b>INARA</b>– FID aktif günlüğü için Inara iletiminin mevcut durumunu '
              'gösterir.</li>\n'
              '</ul>\n'
              '<p>Çevrimiçi erişim verileri her komutan için ayrı ayrı yönetilmektedir. Bir '
              "komutan asla başka bir komutanın API-Key'sini otomatik olarak kullanmaz.</p>\n"
              '\n'
              '<h3>Birden fazla komutan için önemli</h3>\n'
              '<p>Canlı veriler her zaman mevcut Elit Tehlikeli günlük oturumunda açıkça '
              'tanımlanan komutana bağlıdır.</p>\n'
              '<p>Bir görünümde yalnızca farklı bir komutanın görüntülenmesi, aktif canlı komutanı '
              'değiştirmez veya herhangi bir EDSM veya Inara yayınını etkilemez.</p>\n'
              '\n'
              '<h3>İpucu</h3>\n'
              '<p>Komutan, gemi veya konum oyunun mevcut durumuyla eşleşmiyorsa, önce üstteki '
              'günlük ekranını kontrol edin, ardından "Ayarlar" altında ayarlanan günlük klasörünü '
              'kontrol edin.</p>'
              '<p>Açık kırmızı, Solo altın rengi ve Özel Grup yeşil gösterilir; özel gruplarda bildirilen grup adı da görünür. Mod, mevcut günlüklerden yeniden oluşturulur ve yeni LoadGame kayıtlarıyla güncellenir.</p>\n<p>Son sistemlerdeki bir kayda tek tıklamak sistem adını panoya kopyalar. Kısa süreliğine “✓ Kopyalandı: &lt;Sistem&gt;” görünür.</p>\n'),
 'missions': (
        'Görevler ve Ödüller',
        """<h2>Görevler ve Ödüller</h2>
<p>Bu ana sayfa, günlükteki etkin komutanın görevlerini ve gözlemlenen ödüllerini gösterir. Ayrı CMDR görünümünde başka bir komutan seçmek bu sayfayı değiştirmez. Her komutanın verileri ayrı tutulur.</p>

<h3>Sayfanın kullanımı</h3>
<ol>
<li>“Görevler ve Ödüller” sayfasını açın ve listeden bir görev seçin.</li>
<li>“Durum” ve “GÖREV AYRINTILARI” bilgilerini inceleyin. “Sonraki adım” yol gösterir.</li>
<li>Gerekirse mevcut günlük verilerini yeniden okumak için “Günlüğü yenile” düğmesini kullanın.</li>
<li>Görev ödüllerini, “Kelle ödülleri” ve “Savaş tahvilleri” bölümlerini ayrı ayrı değerlendirin.</li>
</ol>

<h3>Liste ve ayrıntılar</h3>
<p>Liste, onaylanmış açık görevleri ve karşılaşmalardan tanınan geçici teklifleri içerir. Görev, sistem, gezegen / konum, durum, sonraki adım, ödül ve son tarihi gösterir. Bir satır seçildiğinde mevcut hedef ve ilerleme ayrıntıları açılır. Günlükte bulunmayan bilgiler bilinmiyor olarak kalır; geçici tekliflerin son tarihi bilinmez.</p>

<h3>Görev durumu</h3>
<p>Durum, mevcut görev, konum ve ilerleme verilerine göre belirlenir. Her görev türü tüm ara aşamaları sağlamaz.</p>
<ul>
<li><b>Görev kabul edildi / Yolda:</b> Görev biliniyor; hedefe varış henüz algılanmadı.</li>
<li><b>Hedef sistemde:</b> Hedef sistemdesiniz, ancak henüz belirlenen görev hedefine ulaşmadınız.</li>
<li><b>Görev hedefinde:</b> İlgili hedef istasyona veya gök cismine ulaşıldı.</li>
<li><b>Hedef değiştirildi:</b> Yeni bir görev hedefi bildirildi.</li>
<li><b>Yük alındı:</b> Görev kargosunun alındığı algılandı.</li>
<li><b>Teslimat sürüyor:</b> Bir teslimat kaydedildi; bilinen miktar ilerlemesi gösterilir.</li>
<li><b>Görev tamamlandı / Veri alındı:</b> İş veya veri toplama tamamlandı. Görev, örneğin “Görev terminaline dön” ile hâlâ açık olabilir. Bu, ödemenin yapıldığını henüz doğrulamaz.</li>
</ul>
<p>Algılanan tamamlanma, başarısızlık veya vazgeçme ilgili görevi açık görev listesinden kaldırır. Yeni ve eksiksiz bir görev durumu, eski kayıtların artık etkin olmadığını gösterebilir.</p>

<h3>Toplam ödül</h3>
<p>“Toplam ödül”, onaylanmış açık görevlerin bilinen kredi ödüllerini toplar. Bu, ödenmiş bir bakiye değildir. Geçici karşılaşma teklifleri, baş ödülleri ve savaş tahvilleri dahil edilmez.</p>

<h3>Karşılaşma görevleri</h3>
<p>Desteklenen uzay karşılaşmaları, henüz kesin bir MissionID olmasa da geçici “Karşılaşma görevi” teklifleri olarak görünebilir. Bu nedenle “Teklif edilen ödül” henüz onaylanmış açık bir görev ödülü değildir ve toplam ödüle dahil edilmez.</p>
<p>Daha sonraki günlük verileri bir teklifi bir görevle kesin olarak eşleştirirse ikisi birleştirilir. Eşleştirme belirsizse teklif geçici kalır. Onaylanmamış teklifler 24 saat sonra yerel olarak gizlenir; bu, oyundaki görev süresini belirtmez.</p>

<h3>Kelle ödülleri</h3>
<p>Bu bölüm yerel olarak gözlemlenen baş ödüllerini, toplam tutarı ve fraksiyon başına tutarları gösterir. Yalnızca kaydedilmiş verileri bilir; oyun bakiyesinin eksiksiz olduğunu garanti etmez. “Kayıt şu andan itibaren başlar.” kaydın başlangıcını belirtir; boşluklar “Tam olarak eşitlenmedi: bazı olaylar eksik olabilir.” ile bildirilir.</p>
<p>Algılanan bir baş ödülü tahsilatı veya ölüm, baş ödüllerinin tüm yerel bakiyesini sıfırlar. Bu, görev durumundan bağımsızdır.</p>

<h3>Savaş tahvilleri</h3>
<p>Burada, tahsil edildiği henüz algılanmamış gözlemlenen savaş tahvilleri fraksiyona göre gösterilir. Kayıt başlamadan önceki olası bakiye dahil değildir. Belirsizlik durumunda “Gözlemlenen tutar” ile “Bakiye tam olarak doğrulanmadı.” görünür.</p>
<p>Kesin olarak eşleştirilen bir tahsilat, belirtilen fraksiyonun gözlemlenen tutarını temizler; diğer fraksiyonlar korunur. Eşleştirme belirsizse tutarlar kalır ve “Tahsilat algılandı – bakiyeyi kontrol edin.” görünür. Algılanan ölüm, gözlemlenen savaş tahvillerini temizler.</p>

<h3>Yerel sıfırlama</h3>
<p>Bir ödül bölümündeki “Sıfırla…”, onaydan sonra yalnızca o bölümün etkin komutana ait yerel bakiyesini sıfırlar. <b>Bu işlem Elite Dangerous içindeki hiçbir değeri değiştirmez.</b> Baş ödülleri ve savaş tahvilleri ayrı sıfırlanır; görevler temizlenmez veya tamamlanmaz.</p>

<h3>Güncelleme ve yeniden başlatma</h3>
<p>Bilinen açık görevler ve yerel ödül bakiyeleri, Helper yeniden başlatıldığında korunur. Görev listesi içermeyen yeni bir günlük oturumu, açık görevleri otomatik olarak kaldırmaz. Kayıt boşlukları özellikle ödül bakiyelerinin eksik kalmasına neden olabilir. “Günlüğü yenile” yalnızca mevcut bilgileri okuyabilir; eksik oyun verilerini oluşturamaz.</p>
<p>Yerel görev görünümü Inara bağlantısı gerektirmez. Etkin komutan için yapılandırılmış ve etkinleştirilmiş bir bağlantı varsa desteklenen görev olayları ayrıca aktarılabilir.</p>""",
    ),
 'explorer': ('Kaşif',
              '<h2>Kaşif</h2>\n<h3>CMDRHelper</h3>\n<p>Sistem genel görünümü: yeni Elite tarzı görünüm, Explorer ve Kronik’te önceki küçük görünümün yerini alır. Yıldızlar ve gezegenler ana yapıyı, aşağıya dallanan uydular alt yapıyı oluşturur; çok yıldızlı sistemler okunaklı kalır. Yakınlaştırma, kaydırma, pencereye sığdırma ve gök cismine tıklama ayrıntılara erişim sağlar.</p>\n<p>Kompakt asteroit kuşakları: kümeler genel görünümde ve Explorer/Kronik’in normal sistem haritalarında kuşaklar halinde gruplanır. Her kümenin verileri korunur.</p>\n<p>Düzeltilmiş haritacılık: DSS haritalamasından sonraki tarama artık satılmamış keşif değerlerini, haritalama zamanını veya verimliliği sıfırlamaz. Hatalı kayıtlar başlangıçta mevcut ve komutana kesin olarak atanmış günlüklerden onarılır. Kaynaklar eksikse onarım bekler; veritabanını silmek gerekmez.</p>\n'
              '<p>Explorer, aktif komutan tarafından keşfedilen ve taranan sistemleri ve gök '
              'cisimlerini değerlendirir. Kendi Elite Dangerous günlük verilerinizi halihazırda '
              'mevcut olan ek bilgilerle birleştirir ve keşif, haritacılık, biyolojik/jeolojik '
              'sinyaller ve yüzey madenciliği verilerini bir arada görüntüler.</p>\n'
              '\n'
              '<h3>Mevcut sistem</h3>\n'
              '<p>Sistem hakkındaki mevcut bilgi düzeyi üst alanda özetlenmiştir.</p>\n'
              '<p>Bunlar, diğerlerinin yanı sıra şunları içerir:</p>\n'
              '<ul>\n'
              '<li>günlükte tanınmış ve hatta kayıtlı organlar</li>\n'
              '<li>mevcut sinyaller</li>\n'
              '<li>Değerleri tara</li>\n'
              '<li>haritacılık değerine zaten ulaşıldı</li>\n'
              '<li>tam olarak eşlenirse olası toplam değer</li>\n'
              '<li>BIO durumu ve tahmini BIO değerleri</li>\n'
              '<li>Henüz gönderilmemiş haritacılık ve BIO verileri</li>\n'
              '</ul>\n'
              '<p>Gösterilen değerler gerçekte mevcut verilere dayanmaktadır. Eksik bilgiler ayrı '
              'bir keşif olarak sunulmaz.</p>\n'
              '\n'
              '<h3>Sistem haritası</h3>\n'
              '<p>Sistem haritası, mevcut sistemdeki yıldızları, gezegenleri, ayları ve bilinen '
              'diğer cisimleri grafiksel olarak temsil eder.</p>\n'
              '<p>Ayrıntılı görünümünü açmak için bir gövdeye tıklanabilir.</p>\n'
              '<p>Ekranda diğer şeylerin yanı sıra vücut tipi, mesafe ve varsa tarama ve '
              'haritacılık değerlerinin yanı sıra özel keşif özellikleri de gösteriliyor.</p>\n'
              '\n'
              '<p>“Pencereye otomatik sığdır” varsayılan olarak açıktır ve seçiminizi yeniden başlatmalarda korur. Her yeni genel görünüm pencereye bir kez sığdırılır; açık pencerede etkinleştirmek de bir kez sığdırır. Ardından elle yakınlaştırmaya ve görünümü kaydırmaya devam edebilirsiniz. Yeniden elle sığdırmak için “Pencereye sığdır” düğmesi kullanılabilir.</p>\n'
              '\n'
              '<h3>İstasyonlar ve tesisler</h3>\n'
              '<p>“İSTASYONLAR (N)” sekmesi, Explorer’ın mevcut sistemindeki bilinen istasyonları ve tesisleri açılabilir kartlar halinde gösterir. Başlıktaki sayı, filtrelerin gizledikleri dahil tüm bilinen kayıtları kapsar. Liste, galaksideki bütün istasyonların eksiksiz bir dizini değildir.</p>\n'
              '<p>Temel kaynak, Elite günlüğünden yerel olarak bilinen gözlemlerdir. Spansh desteği açıkken ayrı istasyon önbelleğinden bilgiler eklenir. Kaynak “Journal”, “Spansh” veya “Journal + Spansh” olabilir; çelişen bilgilerde günlük verileri önceliklidir. Spansh buraya Fleet Carrier eklemez. Kendi carrier’ınız yerel olarak biliniyorsa gösterilebilir.</p>\n'
              '\n'
              '<h3>İstasyon araması, filtreler ve sıralama</h3>\n'
              '<p>“İstasyon adı ara…” istasyon adlarında veya ad parçalarında büyük/küçük harf ayrımı yapmadan anında arar. Boş arama adları sınırlamaz. Arama ve her iki filtre birlikte karşılanmalıdır.</p>\n'
              '<ul>\n'
              '<li><b>Tür:</b> Listeyi yörünge istasyonları, ileri karakollar, yüzey istasyonları, yerleşimler, mega gemiler, Fleet Carrier’lar veya diğer tesislerle sınırlar. “Tüm türler” tür sınırlamasını kaldırır.</li>\n'
              '<li><b>Bağlı gök cismi:</b> Bilinen bağlı gök cismini seçer. “Tüm gök cisimleri” tüm konumları kabul eder; kayıtlar bilinen bir cisme güvenle bağlanamadığında “Bilinmiyor” görünür.</li>\n'
              '<li><b>Sıralama ölçütü:</b> Başlangıçta “Ad” alanına göre alfabetik sıralanır. İsterseniz “Tür”, “Bağlı gök cismi” veya “Varış noktasına uzaklık” alanına göre artan sıralama seçebilirsiniz. Mesafe sayısal sıralanır; bilinmeyen mesafeler veya cisimler ilgili sıralamada sona gelir.</li>\n'
              '</ul>\n'
              '<p>Tıklanacak istasyon sütun başlıkları yoktur: seçim kutuları kartları sıralar. Arama, filtre ve sıralama ağ isteği başlatmaz. Sistem değişince arama ile tür ve cisim filtreleri sıfırlanır. Boş görünüm, bilinen kayıt olmaması ile kayıtların filtrelere uymamasını ayırt eder.</p>\n'
              '\n'
              '<h3>İstasyon ayrıntıları ve hizmetler</h3>\n'
              '<p>Ayrıntıları açmak veya kapatmak için istasyon kartının başlığına tıklayın. Biliniyorsa ad, tür, sistem, bağlı cisim, MarketID, son güncelleme ve kaynak gösterilir. Önizleme resmine çift tıklamak resim görüntüleyiciyi açar.</p>\n'
              '<p>Spansh, varış noktasına ışık saniyesi cinsinden mesafe, bağlılık, yönetim, kontrol eden grup, ekonomi bilgileri ve büyük, orta, küçük iniş alanlarının sayısını ekleyebilir. İstasyon verisi, sistem verisi ve indirme zamanları varsa ayrı gösterilir; yeni indirme, istasyon verisinin daha yeni olduğunu garanti etmez.</p>\n'
              '<p>Bilinen “Hizmetler”, örneğin “Pazar”, “Tersane”, “Donanım”, “Onarım”, “Yakıt ikmali” veya “Malzeme tüccarı” etiketli alanlar halinde görünür. Kart başlığında en fazla üç hizmet ve varsa kalanların sayısı gösterilir; kart açılınca CMDRHelper’ın tanıdığı tüm hizmetler görünür. Eksik bilgiler tahmin edilmez ve bir tesisin bulunmadığını kesin olarak göstermez.</p>\n'
              '\n'
              '<h3>Haritada istasyonlar ve güncelleme</h3>\n'
              '<p>Sistem haritası ve “Sistem genel görünümü” aynı bilinen istasyon bilgilerini kullanır. Güvenle eşleştirilmiş tesisler bağlı cismin yanında, diğerleri “Diğer tesisler” altında yer alır. Tıklama istasyon ayrıntılarını veya gruplar için önce bir seçim listesini açar.</p>\n'
              '<p>“Sistem genel görünümü” içinde “Spansh verilerini yenile”, o pencerede gösterilen sistemin Spansh istasyon bilgilerini günceller. Spansh istasyon bilgileri açık olmalı ve sistem kimliği bilinmelidir. Durum satırı devam eden istekleri, başarıyı, hatayı veya bugün zaten yapılan güncellemeyi bildirir. Hatalarda yerel bilgiler ve kullanılabilir önbellek verileri korunur. Otomatik istek, önbellek ve elle güncelleme kuralları ayarlar yardımında açıklanır.</p>\n'
              '\n'
              '<h3>BIO ×N</h3>\n'
              '<p>BIO ×N, oyun tarafından bildirilen bir vücudun biyolojik sinyallerinin sayısını '
              'belirtir.</p>\n'
              '<p>Sayı başlangıçta yalnızca kaç tane biyolojik sinyalin veya cinsin rapor '
              'edildiğini gösterir. Bu, otomatik olarak tüm biyolojik türlerin zaten bulunduğu '
              'veya analiz edildiği anlamına gelmez.</p>\n'
              '<p>Gerçek kendi organik keşifleri ayrı tutulur.</p>\n'
              '\n'
              '<h3>GEO × N</h3>\n'
              '<p>GEO ×N, oyun tarafından bildirilen bir cismin jeolojik sinyallerinin sayısını '
              'gösterir.</p>\n'
              '<p>Bunlar, örneğin fumaroller veya gayzerler gibi jeolojik özellikleri içerebilir. '
              'CMDRHelper yalnızca mevcut günlük/gövde verilerinden görünen bilgileri '
              'görüntüler.</p>\n'
              '\n'
              '<h3>ABBAU ×N</h3>\n'
              '<p>ABBAU ×N, Elite Dangerous tarafından bildirilen bir cismin gezegendeki '
              'madencilik sahalarının sayısını gösterir.</p>\n'
              '<p>Örnek:</p>\n'
              '<p><b>ABBAU ×12</b></p>\n'
              '<p>bu, bu cisim için 12 gezegensel maden sahasının rapor edildiği anlamına '
              'gelir.</p>\n'
              '<p>Rakam, tek bir yerden hangi ham maddenin çıkarılabileceğini söylemiyor.</p>\n'
              '\n'
              '<h3>Kendi madencilik buluntuları</h3>\n'
              '<p>Komutan Rhino ile yüzey madenciliği gerçekleştirdiyse CMDRHelper, ayrı olarak '
              'belgelenen kişisel bulguları saklar.</p>\n'
              '<p>Aşağıdakiler arasında bir ayrım yapılır:</p>\n'
              '<ul>\n'
              '<li>fiilen elde edilen mallar, ör. B. Ton cinsinden bakır</li>\n'
              '<li>madencilik sırasında toplanan ikincil malzemeler</li>\n'
              '<li>Vücudun genel yüzey malzemeleri</li>\n'
              '</ul>\n'
              '<p>Kişisel bulguya bir örnek şöyle olabilir:</p>\n'
              '<p><b>Bakır – 40 ton</b></p>\n'
              '<p>Bu bilgi, bu komutanın aslında oradan 40 ton bakır çıkardığı anlamına '
              'geliyor.</p>\n'
              '<p>Kişisel madencilik buluntuları her komutan için kaydedilir ve diğer komutanların '
              'buluntularıyla karıştırılmaz.</p>\n'
              '\n'
              '<h3>Gövde yüzey malzemeleri</h3>\n'
              '<p><code>Scan.Materials</code>bir gövdenin genel yüzey malzemesi bileşimini '
              'açıklar.</p>\n'
              '<p>Örneğin demir, nikel, kükürt veya diğer malzemeler yüzde değerleriyle '
              'görüntülenebilir.</p>\n'
              '<p>Bu değerlerin gezegensel maden deposunun hammaddeleriyle karıştırılmaması '
              'gerekir. Frontier, bu genel gövde malzemeleri ile ayrı bir madencilik sahasının '
              'içeriği arasında günlükte belgelenmiş doğrudan bir ilişki sunmamaktadır.</p>\n'
              '\n'
              '<h3>Dünyalaştırma</h3>\n'
              '<p>Dünyalaştırma sembolü veya etiketi, mevcut verilere göre bir gövdenin '
              'dünyalaştırma adayı olarak değerlendirildiğini gösterir.</p>\n'
              '\n'
              '<h3>İlk keşif</h3>\n'
              '<p>“Taraman sırasında zaten keşfedilmiş” ifadesi, o zamanki taramandan önceki durumu anlatır. Evet daha önce keşfedildiğini, Hayır o sırada henüz keşfedilmediğini belirtir; eksik bilgi Bilinmiyor olarak kalır. ★ tarama anındaki bir First Discovery adayını gösterir; bugün hâlâ mevcut olduğu garanti edilen resmî bir ilk keşif hakkını değil.</p>\n<p>Geçmişteki WasDiscovered=false veya WasMapped=false değeri, gökcisminin bugün hâlâ keşfedilmemiş ya da haritalanmamış olduğu anlamına gelmez. Bu gözlemler veri satışından veya yeniden ziyaretten sonra da geçmişe aittir. EDSM’de bilinme ayrı bir bilgidir ve Elite’te resmî keşfi kanıtlamaz. Buradan resmî ilk kâşif çıkarımı yapılmaz.</p>\n'
              '\n'
              '<h3>İlk haritalama</h3>\n'
              '<p>CMDRHelper şunları ayırt eder:</p>\n'
              '<ul>\n'
              '<li>◉ Tarama anında First Mapping adayı: sen taradığında henüz haritalanmamıştı</li>\n<li>◎ Senin tarafından haritalandı: kendi DSS haritalamanın tamamlandığı kaydedilmiş</li>\n<li>◉✓ Tarama anındaki adaylık ve kendi haritalaman belgelenmiş; resmî ilk hak doğrulanmamış</li>\n'
              '</ul>\n'
              '<p>“Taraman sırasında zaten haritalanmış” durumu keşiften bağımsız değerlendirilir. Eksik bilgi Bilinmiyor olarak kalır. Önceden keşfedilmiş bir gökcismi tarama sırasında henüz haritalanmamış olabilir. Kendi haritalaman resmî First Mapping etiketini doğrulamaz; birden fazla ziyarette kayıtlı taramaya göre zaman sırası da her zaman kanıtlanamaz.</p>\n<p>Kendi DSS haritalaman tamamlandığında haritalama zamanı, kullanılan sondalar ve verimlilik hedefi artık güvenilir biçimde kaydedilir. Sonraki taramalar mevcut bilgilerin kaybolmasına yol açmaz.</p>\n'
              '\n'
              '<h3>İniş yapılabilir</h3>\n'
              '<p>İnmeye elverişlilik göstergesi, bilinen verilere göre inişin mümkün olduğu '
              'cisimleri tanımlar.</p>\n'
              '\n'
              '<h3>Altın çerçeveler / değerli gövdeler</h3>\n'
              '<p>Gezgin ekranında özellikle değerli gövdeler vurgulanabilir.</p>\n'
              '<p>Altın çerçeve, ayarlanan eşiğin üzerindeki haritalama tahminini gösterir. Bir First Discovery işareti değildir; satılmamış verileri veya bugün hâlâ alınabilecek ilk keşif bonuslarını doğrulamaz.</p>\n'
              '<p>Vücudun değerinin ayrıntılı gösteriminin yerini almaz.</p>\n'
              '\n'
              '<h3>Değerlerin listesi</h3>\n'
              '<p>Değer listesi kayıtlı taramaya dayalı tahminler gösterir; henüz alınmamış garantili ödemeler değil. İlk hak bonusları doğrulanmamış kalır. Harita ve liste ipuçları ile gökcismi ayrıntıları aynı zamana bağlı durumları kullanır.</p>\n'
              '<p>Bir sistemdeki ilginç veya değerli gövdelerin hızlı bir şekilde '
              'karşılaştırılması için özellikle uygundur.</p>\n'
              '\n'
              '<h3>BIO / GEO / ABBAU</h3>\n'
              '<p>Bu görünüm biyolojik, jeolojik veya gezegensel madencilik sinyalleri bulunan gökcisimlerini '
              'gruplar.</p>\n'
              '<p>Bu, ilginç cisimlerin komple sistem haritasında tek tek aranmasına gerek '
              'olmadığı anlamına gelir.</p>\n'
              '<p>Kendi yüzey madenciliği verileriniz varsa kişisel madencilik bulgularınız da '
              'görülebilir.</p>\n'
              '<p>Explorer’ın ortak BIO / GEO / ABBAU tablosunda elle ayarlanan sütun genişlikleri yeniden açılışta ve program yeniden başlatıldığında korunur. Açılır pencerelerin kayıtlı sütun genişlikleri daha sağlam geri yüklenir; geçersiz değerlerde güvenli varsayılan genişlikler kullanılır.</p>\n\n'
              '<h3>Tabloların kullanımı</h3>\n<p>Değer listesinde ve BIO / GEO / ABBAU tablosunda sıralamak '
              'için sütun başlığına tıklayın; tekrar tıklamak yönü tersine çevirir. Genişlikleri değiştirmek '
              'için sütun sınırlarını fareyle sürükleyin. Sıralama ve sütun genişlikleri her tablo için ayrı '
              'kaydedilir. Gökcismi adları doğal sıralanır; örneğin A 2, A 10’dan önce gelir. Mesafeler, '
              'krediler ve adetler sayısal sıralanır. Durum, analiz ve ziyaret sütunları alfabetik olarak '
              'değil, anlamlarına göre sıralanır.</p>\n\n<h3>Gövde detayı</h3>\n'
              '<p>Bir gövdeye tıklamak ayrıntılı görünümü açar.</p>\n'
              '<p>Bilindiği kadarıyla burada şunlar görünebilir:</p>\n'
              '<ul>\n'
              '<li>Gövde Tipi</li>\n'
              '<li>yığın</li>\n'
              '<li>mesafe</li>\n'
              '<li>Yer çekimi</li>\n'
              '<li>atmosfer</li>\n'
              '<li>Karaya elverişlilik</li>\n'
              '<li>Dünyalaştırma durumu</li>\n'
              '<li>BIO/GEO sinyalleri</li>\n'
              '<li>gezegensel madencilik sahaları</li>\n'
              '<li>Yüzey malzemeleri</li>\n'
              '<li>kendi maden buluntuları</li>\n'
              '<li>Tarama değeri</li>\n'
              '<li>haritacılık değeri</li>\n'
              '<li>mevcut değer</li>\n'
              '</ul>\n'
              '<p>Her kurum tüm bilgilere sahip değildir.</p>\n'
              '\n'
              '<h3>BİYO tahminleri</h3>\n'
              '<p>CMDRHelper, uygun cisimlere ilişkin mevcut verilere dayanarak olası biyolojik '
              'keşifleri tahmin edebiliyor.</p>\n'
              '<p>Tahminler, belirli bir türün gerçekten var olacağının garantisi değildir. Keşif '
              'için karar verme yardımcısı olarak hizmet ederler.</p>\n'
              '<p>Tahmini BIO değerleri de tahmindir ve gerçek doğrulanmış bulgulardan ayrı olarak '
              'ele alınır.</p>\n'
              '\n'
              '<h3>Henüz gönderilmedi</h3>\n'
              '<p>CMDRHelper, komutanla ilgili bilinen haritacılık ve henüz gönderilmemiş BIO '
              'verilerini tutar.</p>\n'
              '<p>Haritacılık satışları ve biyolojik telif hakları, ilgili günlük olayları '
              'kullanılarak muhasebeleştirilir.</p>\n'
              '<p>Halihazırda satılmış olan haritacılık verileri yeniden yapılanma sonrasında '
              'tekrar açık görünmemelidir.</p>\n'
              '\n'
              '<h3>Otomatik göster</h3>\n'
              '<p>Değerli Gövdeler veya BIO Buluntuları gibi desteklenen Explorer ipuçları, sol '
              'kenar çubuğundaki anahtarlar kullanılarak otomatik olarak görüntülenebilir.</p>\n'
              '<p>Bu küçük canlı pencereler, oyun oynarken ek ipuçları görevi görür ve tam '
              'Explorer görünümünün yerini almaz.</p>\n'
              '<p>“Cargo”, aktif Journal-FID tarafından belirlenen Ship veya SRV’nin doğrulanmış yükünü gösterir. SRV Cargo hiçbir zaman Ship Cargo olarak devralınmaz; Limpetler toplam doluluğa dahildir ve Ad | Miktar tablosunda ayrı gösterilir.</p>\n'
              '<p>BIO ilerlemesi kısa gösterilir: 1/3 sarı, 2/3 mavi ve 3/3 yeşil; tamamlanmış “Tamamlandı” durumu da yeşildir. “otomatik göster” altında GEO’nun ayrı kaydedilen anahtarı vardır: yalnız BIO, yalnız GEO veya ikisi birlikte kullanılabilir.</p>\n<p>Kargo penceresi yüksekliğini içeriğe göre otomatik ayarlar. Çok sayıda kayıtta yükseklik sınırlanır ve tablo kaydırılabilir; seçilen genişlik ve pencere konumu korunur. Mevcut “Kargo HUD” anahtarı artık “otomatik göster” altındadır; kargo penceresinde ikinci bir anahtar bulunmaz.</p>\n\n'
              '<h3>Birkaç komutan</h3>\n'
              '<p>Kişisel keşif sonuçları, haritacılık, BIO buluntuları ve kendi yüzey madenciliği '
              'buluntuları ilgili komutana atanır.</p>\n'
              '<p>Bir cismin küresel astronomik özellikleri (örneğin, gezegendeki bilinen maden '
              'sahalarının sayısı) cismin kendi özellikleri olarak kalır.</p>\n'
              '\n'
              '<h3>İpucu</h3>\n'
              '<p>İlginç bir vücudunuz varsa detaylı görünüme tıklamaya değer. Burası genel gövde '
              'verileri, olası keşif sonuçları ve kendi komutanınız tarafından belgelenen gerçek '
              'bulgular arasında ayrım yapmak için en iyi yerdir.</p>'
              """

<h3>★ Favoriler</h3>
<p>Explorer’ın üst kısmındaki “★ Favoriler” düğmesi ayrı, yeniden kullanılabilen bir favoriler penceresi açar. Burada etkin komutan için sistemleri, gezegenleri/uyduları ve yüzey konumlarını kaydedersin.</p>
<p>Ada göre alfabetik sıralanan, kaydırılabilir liste; ad, tür, sistem, uygun olduğunda gökcismi ve enlem/boylam, kategori ve küçük bir resim önizlemesi gösterir. Serbest metin araması, tür filtresi ve kategori filtresi birlikte kullanılabilir. Arama; ad, sistem, gökcismi ve notu kapsar.</p>
<p>“Aç / Göster” kaydedilen bilgileri, notu ve daha büyük bir resim önizlemesini gösterir. “Explorer’da göster”, favori mevcut Explorer sistemine aitse ve ilgili veriler varsa mevcut sistem genel görünümünü veya gökcismi ayrıntı görünümünü açar. Diğer sistemler için kaydedilmiş favori verileri görünür kalır; sistemler arası rota hesaplanmaz.</p>

<h3>Mesafe filtresi</h3>
<p>“Mesafe filtresi” varsayılan olarak kapalıdır. “Azami mesafe:” başlangıçta 500 ly değerindedir; 1 ile 100.000 ly arasında ayarlanabilir. Mesafe, yerel olarak mevcut sistem koordinatları kullanılarak bilinen güncel sistemden hesaplanır. Yalnızca bu filtre için canlı ağ sorgusu yapılmaz.</p>
<p>Bilinen mesafesi sınırı aşan favoriler gizlenir. Mesafesi bilinmeyen favoriler görünür kalır. Güncel sistemin koordinatları eksikse mesafe filtresi hiçbir kaydı gizlemez. Arama, tür ve kategori filtreleri geçerliliğini korur. Sistem değişiminden sonra filtreleme otomatik yenilenir. Anahtarın durumu ve azami mesafe kaydedilir.</p>

<h3>Favorileri dışa aktarma</h3>
<p>“Dışa aktar”, etkin komutanın tüm favorilerini içeren taşınabilir bir ZIP oluşturur; yalnızca arama, tür, kategori veya mesafe filtreleriyle görünen kayıtları değil. favorites.json yapılandırılmış favori verilerini içerir; mevcut favori görselleri images/ altında bulunur. Paket Linux ve Windows arasında aktarılabilir.</p>
<p>Mevcut favoriler ve orijinal görseller değiştirilmez. Aynı içeriğe sahip görseller pakette yalnızca bir kez saklanır. Eksik veya bozuk görseller favori verilerinin dışa aktarılmasını engellemez. İçe ve dışa aktarmada dosya başına en fazla 32 MiB, sıkıştırılmamış paket içeriği için toplam 256 MiB sınırı vardır.</p>

<h3>Favorileri içe aktarma</h3>
<p>“İçe aktar” önce ZIP dosyasını denetler ve değişikliklerden önce yeni ve mevcut favorilerin özetini gösterir. İçe aktarılan favoriler o anda etkin olan komutana atanır. Yinelenenler tür, kategori, ad ve konuma göre belirlenir: bilinen sistem/gökcismi kimlikleri ve koordinatlar, bunlar yoksa sistem/gökcismi adları. Paket içindeki yinelenenler de dikkate alınır.</p>
<p>Algılanan tüm yinelenenlere aynı seçim uygulanır: “Atla” varsayılandır ve mevcut kayıtları korur; “Mevcut favoriyi değiştir” içe aktarılan verileri mevcut favoriye uygular; “Yeni kayıt olarak içe aktar” ek bir kayıt oluşturur. İptal edildiğinde hiçbir şey aktarılmaz.</p>
<p>Geçersiz favori verileri tüm içe aktarmayı engeller. İçe aktarma hatasında kısmi aktarım kalmaması için veritabanı değişiklikleri geri alınır. Eksik veya bozuk görseller geçerli verilerin içe aktarılmasını engellemez; bu favoriler görselsiz aktarılır. İçe aktarılan görseller CMDRHelper tarafından yerel olarak yönetilir.</p>

<h3>Sistem, gezegen veya mevcut konumu kaydetme</h3>
<ul>
<li>“★ Mevcut sistemi kaydet” mevcut sistemi yüzey koordinatları olmadan kaydeder.</li>
<li>“★ Gezegen / ay kaydet” mevcut sistemdeki bilinen bir gezegeni veya uyduyu seçmeni sağlar. Bu favoriye de yüzey koordinatları eklenmez.</li>
<li>“★ Mevcut konumu kaydet”, favoriler penceresinin üst kısmında diğer iki kaydetme seçeneğinin yanında bulunur ve gezegen gezgininde de kullanılabilir. Favoriler penceresinde düğme her zaman görünür kalır; geçerli güncel gezegen konum verileri ve etkin bir komutan olmadan devre dışıdır. Tıklandığında komutan, sistem, gökcismi, enlem ve boylam sabitlenir. Oyundaki sonraki hareketler, açık iletişim kutusundaki bu değerleri değiştirmez.</li>
</ul>
<p>İstediğin bir ad gir ve tam olarak bir kategori seç: Biyo, Jeo, Madencilik, Manzara, İniş yeri, İlginç veya Diğer. Not ve resim isteğe bağlıdır. Bilinen teknik kimlikler dahili olarak aktarılır; bunları girmen gerekmez. Enlem veya boylam 0,0 da geçerli koordinatlardır.</p>
<p>“Düzenle”; ad, kategori, not ve resmi değiştirir. Sistem, gökcismi ve kaydedilmiş koordinatlar korunur. Farklı bir yüzey konumu kaydetmek için o konumda yeni bir favori oluştur.</p>

<h3>Fare kullanmadan hızlı favori</h3>
<p>“Ayarlar → Hızlı favori” altında genel bir kısayol tuşunu serbestçe atayabilir, değiştirebilir veya kaldırabilirsin. Kurulumdan sonra varsayılan durum “Atanmamış” olur: CMDRHelper istenmeden hiçbir tuşu kaydetmez. Atama saklanır. Bir tuş birleşimi zaten kullanımdaysa veya sisteminde kullanılamıyorsa bir hata mesajı gösterilir; daha önce çalışan bir atama korunur.</p>
<p>Linux/X11 ve Windows üzerinde kısayol, Elite odaktayken de çalışır – yaya olarak, SRV’de ve gemide. Tuşa basıldığında yüzeydeki mevcut konum, etkin komutan için hemen kaydedilir; iletişim kutusu açılmaz ve fare kullanımı gerekmez. Komutan, sistem, gök cismi ve mevcut Latitude/Longitude değerleri o anda sabitlenir. Geçerli güncel gezegen koordinatları yoksa hiçbir şey kaydedilmez; eski koordinatlar yeniden kullanılmaz.</p>
<p>Favoriye “İşaretçi 07.09.2026 06:32:15” gibi benzersiz bir geçici ad ve “Diğer” kategorisi verilir. Normal favoriler penceresinde daha sonra adını değiştirebilir, başka bir kategori atayabilir, not veya resim ekleyebilirsin. Otomatik olarak ekran görüntüsü alınmaz veya içe aktarılmaz.</p>
<p>Yaklaşık iki saniye boyunca etkin Elite penceresinin doğrudan üzerinde gök cismi ve koordinatlarla birlikte “★ FAVORI KAYDEDILDI” görünür; konum mevcut değilse kısa süreliğine “⚠ GEZEGEN KOORDINATLARI YOK” gösterilir. Gösterim odağı almaz ve girdileri yakalamaz. Navigasyon HUD’u kapalıyken de çalışır ve ardından tamamen kaybolur. HUD açıkken sonrasında normal navigasyon gösterimi kalır. HUD anahtarının kayıtlı ayarı değiştirilmez. Gösterim, navigasyon HUD’u ile aynı üst katman altyapısını ve platform gereksinimlerini kullanır.</p>

<h3>Favori resimleri</h3>
<p>Favori resimleri, Resimler bölümünden ayrıdır. “Resim seç …” PNG, JPEG ve WebP biçimlerini kabul eder. CMDRHelper, seçilen resmi kendi favori resimleri klasörüne yalnızca kaydederken kopyalar. Orijinal dosya taşınmaz veya değiştirilmez.</p>
<p>“Son ekran görüntüsünü kullan”, her tıklamada yapılandırılmış ekran görüntüsü kaynak klasörünü yeniden okur ve tipik Elite dosya adlarına sahip okunabilir ekran görüntülerini arar. Bir ayar yoksa Windows veya Steam/Proton’daki olağan Elite ekran görüntüsü klasörleri dikkate alınır. Yapılandırılmış dönüştürme hedefindeki etkin komutana ait klasör de uygun dönüştürülmüş Elite ekran görüntüleri için aranır. Böylece orijinal BMP’si silinmiş olsa da dönüştürülmüş bir ekran görüntüsü bulunabilir. En yeni çekim zamanını belirlerken dosya adındaki açık zaman bilgisi, yoksa dosya zamanı esas alınır; dönüştürülmüş resimlerde dönüştürme zamanı yerine adda saklanan çekim zamanı kullanılır. CMDRHelper kendisi ekran görüntüsü almaz ve rastgele resim klasörlerini aramaz.</p>
<p>Kullanımdan önce dosya adı, çekim zamanı ve yeni yüklenmiş bir önizleme gösterilir. “Bu resmi kullan” ile onayla. Uygun ekran görüntüsü bulunamazsa “Resim seç …” seçeneğini kullanmaya devam edebilirsin. Elite BMP ekran görüntüleri dahili PNG kopyası olarak kaydedilir.</p>
<p>Bir resim düzenleme iletişim kutusunda değiştirilebilir veya “Resmi kaldır” ile seçimden çıkarılabilir. Kaydederken artık kullanılmayan dahili kopya silinir. Resim dosyası eksikse favori önizleme olmadan kullanılabilir durumda kalır.</p>
<p>Favori görselleri dışa aktarıma dahil edilebilir ve içe aktarımda yerel olarak kopyalanır. Paylaşılan dahili görsel kopyaları başka bir favori ihtiyaç duyduğu sürece korunur. İçe aktarma favorileri değiştirdiğinde eski görsel dosyaları şu anda önlem olarak saklanır.</p>

<h3>Favori hedefi ve komutan</h3>
<p>“▶ Rotaya git”, favorinin bilinen sistemini rota planlayıcıda hedef olarak ayarlar. Başlangıç mevcut davranışa göre güncel AppState üzerinden belirlenir; elle girilmiş başlangıç korunur. Otomatik rota hesaplanmaz. “◎ Koordinatlara git”, sistem, gökcismi ve geçerli koordinatlar kayıtlıysa mevcut HUD ile yüzey konumuna mevcut gezegen gezinmesini başlatır. Sisteme yolculuk ve yüzey gezinmesi, otomatik seyahat dizisi olmadan iki ayrı adımdır. Yüzey koordinatları olmadan yalnızca rota kullanılabilir; gerekli verileri eksik olan eylemler gizlenir.</p>
<p>Yüzey konumlarında “◎ Koordinatlara git”, kaydedilmiş gökcismini, enlemi, boylamı ve favori adını mevcut gezegen gezginine aktarır. Yeni hedef önceki hedefin yerini alır. Favorilerin kendi gezinme mantığı yoktur. Gezgin karar vermeye aynı şekilde devam eder: eşleşen geçerli gezegen verileri gezinmeyi etkinleştirir; aksi hâlde bu verileri bekler.</p>
<p>Favoriler yalnızca etkin komutana aittir. Komutan değiştirildiğinde liste güncellenir ve açık düzenleme iletişim kutusu iptal edilir. Hâlâ önceki komutanın favori hedefi olarak yönetilen bir hedef sonlandırılır. Günlükteki komutan seçimi bu favori listesini genişletmez.</p>
<p>“Sil” onay gerektirir ve yalnızca favori kaydını ve onun dahili resim kopyasını kaldırır. Orijinal ekran görüntüsü veya seçilen orijinal resim ile tüm Explorer, günlük ve gökcismi verileri korunur.</p>"""),
 'chronicle': (
        'Kronik',
        """<h2>Kronik</h2>
<h3>CMDRHelper</h3>
<p>Sistem genel görünümü: yeni Elite tarzı görünüm, Explorer ve Kronik’te önceki küçük görünümün yerini alır. Yıldızlar ve gezegenler ana yapıyı, aşağıya dallanan uydular alt yapıyı oluşturur; çok yıldızlı sistemler okunaklı kalır. Yakınlaştırma, kaydırma, pencereye sığdırma ve gök cismine tıklama ayrıntılara erişim sağlar.</p>
<p>Kompakt asteroit kuşakları: kümeler genel görünümde ve Explorer/Kronik’in normal sistem haritalarında kuşaklar halinde gruplanır. Her kümenin verileri korunur.</p>
<p>Chronicle, komutanın kişisel seyahat ve keşif geçmişidir. Daha önce ziyaret edilmiş sistemleri bulmak, bunları mekansal olarak temsil etmek ve bilinen keşifleri aramak için kalıcı olarak saklanan günlük bilgilerini kullanır.</p>

<h3>Ziyaret edilen sistemler</h3>
<p>Chronicle, ziyaret edilen sistemleri ve bunların Komutanın bildiği galaksideki konumlarını gösterir.</p>
<p>Varsa ilk ve son ziyaret ile bilinen vücut bilgileri dikkate alınır.</p>
<p>Bir dönem etkin olduğunda harita görünümündeki ziyaret sayısı, ilk ziyaret ve son ziyaret, filtrelenmiş gerçek sistem ziyaretlerini ifade eder.</p>
<p>Bu nedenle kronik yalnızca bir harita değil aynı zamanda daha önceki seyahat noktalarını ve keşifleri bulmaya yönelik bir araçtır.</p>

<h3>3 boyutlu harita</h3>
<p>Ziyaret edilen sistemler galaktik X/Y/Z koordinatları kullanılarak mekansal olarak temsil edilir.</p>
<p>Çalıştırma talimatları doğrudan haritanın üzerinde bulunur:</p>
<ul>
<li>Farenin sol düğmesini basılı tutun → görünümü döndürün</li>
<li>orta fare düğmesini basılı tutup sürükle → yakınlaştırma penceresi çiz</li>
<li>Farenin sağ düğmesini basılı tutun → görünümü taşıyın</li>
</ul>
<p>Küçük eksenli ekran, uzayda yönlendirmeye yardımcı olur.</p>

<p>Fare tekerleğiyle ek bir tuşa basmadan yakınlaştırabilir veya uzaklaştırabilirsin.</p>
<p>Haritanın boş bir alanına çift tıklamak başlangıçtaki eğik görünümü geri getirir, kaydırmayı sıfırlar ve görüntülenen tüm sistemleri pencereye sığdırır. Filtreler ve seçili sistem korunur.</p>
<p>Sol fare düğmesiyle döndürmeye başladığında tıkladığın sistem dönme merkezi olur. Boş alanda, galaktik düzlemde imlecin altındaki nokta kullanılır; görünüm neredeyse yataysa bunun yerine aynı düzlemdeki harita merkezi kullanılır. Hizalama da mevcut dönme merkezi etrafında döner.</p>
<p>Ayrıntı penceresini açmak için bir sisteme tıkla. Burada üstteki sistem adına veya yanındaki ⧉ kopyalama simgesine sol tıklamak panoya yalnızca sistem adını kopyalar. Kısa süre görünen ✓ kopyalamayı onaylar.</p>

<h3>Mevcut konum</h3>
<p>“Geçerli Konum” ile harita görünümü aktif komutanın halihazırda bilinen konumuna hizalanabilir veya bu konuma döndürülebilir.</p>
<p>Önce mevcut filtreler uygulanır. Yalnızca mevcut sistem sonuç haritasında yer alıyorsa görünüm o sisteme ortalanır.</p>
<p>Aksi takdirde “Mevcut sistem bu filtre seçimine dâhil değil.” mesajı gösterilir. Bu işlem filtreleri kaldırmaz.</p>

<h3>Hizala</h3>
<p>“Hizala”, yönelimi galaktik düzlemin üstten görünümüne döndürür. Kaydırma ve yakınlaştırma korunur.</p>
<p>Bu, çok fazla döndürme nedeniyle harita anlaşılmaz hâle geldiğinde yararlıdır.</p>

<h3>Kroniği yenile</h3>
<p>“Kroniği yenile”, kronik verilerini mevcut birleşik filtrelere göre yeniden yükler ve görünümü günceller. Serbest metin, etkin tarih sınırları ve madencilik filtreleri yeniden birlikte değerlendirilir; etkin filtreler göz ardı edilmez.</p>
<p>İşlev, günlük dosyalarını değiştirmez veya yeni keşif verileri oluşturmaz. Mevcut CMDRHelper verilerine göre geçmiş görünümünü günceller.</p>

<h3>Serbest metin araması</h3>
<p>Zaten bilinen içerik, “Arama geçmişi…” alanı kullanılarak aranabilir.</p>
<p>Arama, diğer hususların yanı sıra - eğer veritabanında mevcutsa - dikkate alır:</p>
<ul>
<li>Sistem adları</li>
<li>Gövde özellikleri</li>
<li>biyolojik veriler</li>
<li>Malzemeler</li>
<li>Kodeks verileri</li>
</ul>
<p>Serbest metin, dönem ve madencilik ortak bir filtre alanında bulunur. “Uygula”, ayarlanan filtreleri birlikte değerlendirir. Serbest metin alanında Enter, “Uygula” ile aynı birleşik filtrelemeyi başlatır.</p>

<h3>Başlangıç/Bitiş dönemi (UTC)</h3>
<p>“Başlangıç” ve “Bitiş”i kendi onay kutularıyla etkinleştir ve istediğin tarihi seç. Yalnızca tek bir sınır da kullanılabilir. Bir kutu etkin değilse o tarafta zaman kısıtlaması yoktur; iki kutu da etkin değilse dönem kısıtlanmaz.</p>
<ul>
<li><b>Başlangıç:</b> Seçilen UTC takvim gününün başlangıcından itibaren, başlangıç dâhil.</li>
<li><b>Bitiş:</b> Seçilen UTC takvim gününün tamamı, ertesi günün başlangıcından hemen öncesine kadar dâhil edilir.</li>
</ul>
<p>UTC, Eşgüdümlü Evrensel Zaman’dır. Tarih sınırları yerel saat dilimindeki takvim günlerine değil, UTC takvim günlerine karşılık gelir.</p>
<p>Filtrelemenin kaynağı, gerçek sistem ziyaretlerinin tutulduğu <code>system_visits</code> tablosudur. İlgili komutanın dönem içinde gerçek bir ziyareti gerekir. Kaydedilmiş <code>first_seen</code> ve <code>last_seen</code> değerleri gerçek bir ziyaretin yerini tutmaz: dönemin yalnızca daha önceki bir ilk ziyaret ile daha sonraki bir son ziyaret arasında kalması yeterli değildir.</p>
<p>Dönem, tek tek keşif, BIO, GEO veya madencilik olaylarını değil, ziyaretleri filtreler. Bilinen buluntu bilgileri ve madencilik miktarları kayıtlı toplam değerler olarak kalır. Başlangıç/Bitiş tek başına veya serbest metin ve madencilikle birlikte kullanılabilir.</p>
<p>Başlangıç, Bitiş’ten sonraysa “Başlangıç tarihi Bitiş tarihinden sonra olamaz.” mesajı gösterilir. Hiçbir veritabanı sorgusu başlatılmaz. Tarih sınırlarını düzeltip filtreleri yeniden uygula.</p>

<h3>Arama sonuçları</h3>
<p>İsabetler, tarih kartının altındaki mevcut sonuçlar listesinde görüntülenir.</p>
<p>Vuruş türüne bağlı olarak sistem ve gövdenin yanı sıra ek bilgiler de görünebilir.</p>
<p>Bir isabet, zaten bilinen ilgili sistemi veya gövdeyi bulmak ve mevcut ayrıntılı bilgiyi açmak için kullanılabilir.</p>

<h3>Sonuç yok</h3>
<p>Geçerli bir filtreleme hiçbir eşleşme bulamazsa harita ve rotalar temizlenir. Sonuç listesi temizlenip gizlenir, ayrıntı görünümü sıfırlanır ve açık bir kronik sistem ayrıntısı penceresi kapatılır.</p>
<p>Eski sonuçlar görünür kalmaz. Bu durumda arama metni, dönem ve madencilik filtrelerinin birleşimini ve ilgili görünümde kullanılan komutanı kontrol et.</p>

<h3>Gezegensel maden sahaları</h3>
<p>"Gezegensel madencilik sahaları" filtresi, özellikle Elite Dangerous'nin gezegensel madencilik sahalarını bildirdiği bilinen cisimleri aramak için kullanılabilir.</p>
<p>Temel ekran Explorer'dan bilinene karşılık gelir:</p>
<p><b>ABBAU ×N</b></p>
<p>Numara vücudun kendisine aittir ve komutanla ilgisi yoktur.</p>

<h3>En azından</h3>
<p>"En azından" seçeneğini kullanarak bir kuruluşun sahip olması gereken minimum gezegen madenciliği konumu sayısını belirleyebilirsiniz.</p>
<p>Örnek:</p>
<p><b>En az 20</b></p>
<p>yalnızca en azından aşağıdakileri içeren bilinen gövdeleri gösterir:</p>
<p><b>ABBAU ×20</b></p>
<p>Bu, özellikle geniş madencilik alanlarının özel olarak konumlandırılmasını mümkün kılar.</p>

<h3>Kendi maden buluntularım</h3>
<p>"Kendi maden buluntuları" durumunda arama, söz konusu komutanın kendisinin açık bir şekilde yüzey madenciliği yaptığı cesetlerle sınırlıdır.</p>
<p>Bu bilgiler kişisel yüzey madenciliği geçmişinden gelir ve komutan tarafından kesin bir şekilde ayrılır.</p>
<p>Bu nedenle bir vücut, kendi komutanının orada herhangi bir şeyi kaldırmasına gerek kalmadan küresel ABBAU ×N sinyallerine sahip olabilir.</p>

<h3>Ticari mal</h3>
<p>“Kendi madencilik buluntuları” etkinleştirilmişse, “Hammadde” seçimi de mevcuttur.</p>
<p>Liste yalnızca söz konusu komutanın halihazırda yüzey madenciliğinden kazandığı malları içeriyor.</p>
<p>Bu, tüm olası madencilik hammaddelerinin teorik bir listesi değildir.</p>
<p>EXAMPLE için listede örneğin şunlar bulunabilir:</p>
<ul>
<li>Tüm</li>
<li>bakır</li>
</ul>
<p>Daha sonra ek hammaddeler çıkarılırsa, bunlar otomatik olarak kişisel seçiminizde görünecektir.</p>

<h3>Hammaddeler için hedefli arama</h3>
<p>Örneğin, "Bakır" seçilirse ve ardından "Uygula"ya basılırsa, geçmiş yalnızca söz konusu komutanın bariz bir şekilde bakır çıkardığı cesetleri gösterecektir.</p>
<p>Örnek:</p>
<p><b>Example System / 2 — ABBAU ×12 — bakır 40 ton</b></p>
<p>Bu, kroniğin kişisel konum veri tabanı olarak kullanılabileceği anlamına gelir: daha önce çıkarılmış olan bir ham madde daha sonra tekrar bulunabilir.</p>

<h3>Tüm hammaddeler</h3>
<p>"Hammadde: Hepsi" ile eşleşen tüm kişisel yüzey madenciliği keşifleri dikkate alınır.</p>
<p>Bir gövde üzerinde birden fazla mal biliniyorsa o ana kadar elde edilen miktarlarla birlikte sergilenebilir.</p>
<p>Örnek:</p>
<p><b>ABBAU ×12 — Helyum-3 10 ton, bakır 40 ton</b></p>
<p>Miktarlar, ilgili komutanın kişisel madencilik değerleridir ve aslında günlük olaylarından belgelenmiştir.</p>
<p>Bir dönem etkinken de kişisel madencilik miktarları kayıtlı toplam miktarlar olarak kalır. <b>Bakır 40 t</b> otomatik olarak şu anlama gelmez: <b>seçilen dönemde 40 t</b>. Dönem, uygun bir sistem ziyareti gerektirir ancak gösterilen çıkarılmış miktarı bu dönemle sınırlamaz.</p>

<h3>Filtreleri birleştir</h3>
<p>Serbest metin, etkin Başlangıç/Bitiş sınırları ve madencilik filtreleri birleştirilebilir. Bir eşleşme, ayarlanan koşulları birlikte karşılamalıdır.</p>
<p>Örneğin:</p>
<ul>
<li>Gezegensel madencilik sahaları aktif</li>
<li>En az 20</li>
<li>Kendi madenciliği aktif bulundu</li>
<li>Hammadde bakır</li>
</ul>
<p>Söz konusu komutanın halihazırda bakır çıkarmış olduğu en az 20 gezegen maden sahasına sahip bilinen cesetleri arar.</p>
<p>Ek bir arama metni varsa o da dikkate alınır. Ayrıca bir dönem seçilmişse görüntülenen komutanın ilgili sistemi gerçekten o dönemde ziyaret etmiş olması gerekir; bakırın çıkarılması ise o dönemde gerçekleşmek zorunda değildir.</p>

<h3>Uygula</h3>
<p>“Uygula”, o anda ayarlanmış tüm arama, dönem ve madencilik filtreleriyle ortak bir filtreleme yapar:</p>
<ul>
<li>Serbest metin</li>
<li>Başlangıç, etkinse</li>
<li>Bitiş, etkinse</li>
<li>Gezegensel maden sahaları</li>
<li>Minimum sayı</li>
<li>Kendi maden buluntularım</li>
<li>Ticari mal, “Kendi maden buluntularım” etkinse</li>
</ul>
<p>Serbest metin alanında Enter tamamen aynı filtrelemeyi yapar. Serbest metin ve madencilik filtresi yoksa haritada işaretli komutanlar için normal harita yüklenir; varsa Başlangıç/Bitiş ile sınırlandırılır.</p>

<h3>Sıfırla</h3>
<p>“Sıfırla”, ortak filtre alanını ilk durumuna döndürür:</p>
<ul>
<li>Serbest metin temizlenir.</li>
<li>Başlangıç ve Bitiş devre dışı bırakılır; tarih alanları yeniden bugünün tarihini gösterir ve devre dışıdır.</li>
<li>Gezegensel maden sahaları devre dışı bırakılır.</li>
<li>Minimum sayı 0 olarak ayarlanır.</li>
<li>Kendi maden buluntularım devre dışı bırakılır.</li>
<li>Ticari mal “Tümü”ne döndürülür.</li>
</ul>
<p>Komutan seçimi korunur. Ardından bu harita seçimi için normal kronik yeniden yüklenir; önceki arama sonuçları ve ayrıntı görünümleri sıfırlanır.</p>

<h3>Komutan seçimi</h3>
<p>Chronicle, çeşitli tanınmış komutanlardan gelen verileri görüntüleyebilir.</p>
<p>Burada iki ayrı seçim kavramı vardır:</p>
<ul>
<li><b>Haritanın komutan seçimi:</b> Komutan kutuları, serbest metin/madencilik araması olmayan normal haritada hangi komutan rotalarının gösterileceğini belirler. Etkin bir dönem varsa dikkate alınır.</li>
<li><b>Görüntülenen komutan:</b> Kişisel serbest metin/madencilik aramaları görüntülenen komutanı (<code>viewed_commander_id</code>), yoksa etkin komutanı kullanır. Kişisel ticari mal listeleri de bu komutana göre belirlenir.</li>
</ul>
<p>Ancak kendi maden buluntularınız ve hammadde listeleriniz gibi kişisel bilgiler, gerçekte görüntülenen komutan için her zaman ayrı olarak değerlendirilir.</p>
<p>Bir komutan hammadde seçiminde münhasıran başka bir komutana ait olan herhangi bir maden bulgusunu görmez.</p>

<h3>Tüm komutanlar</h3>
<p>Harita/kronik ekranı birden fazla komutanı hesaba katabilir.</p>
<p>“Tüm komutanlar”, haritanın komutan seçimini ifade eder. Komutan kutuları kişisel serbest metin/madencilik aramalarını otomatik olarak birden fazla komutana genişletmez.</p>
<p>Bu, komutanla ilgili verilerin kişisel tahsisini değiştirmez. Bir sistemin veya cismin küresel astronomik özellikleri ortak kalır, kişisel bulgular ise ayrı kalır.</p>

<h3>Arama yardımı/açıklama</h3>
<p>Tarih araması ve ekranın anlamı hakkındaki ek bilgilere “Arama yardımı / açıklama” yoluyla erişilebilir.</p>
<p>Tıklanan bir arama terimi arama alanına aktarılır ve önceden ayarlanmış dönem/madencilik filtreleriyle birlikte çalıştırılır.</p>
<p>Bu bağlamla ilgili ana yardım, burada mevcut olan kısa çalıştırma talimatlarını tamamlar.</p>

<h3>İpucu</h3>
<p>Chronicle, özellikle uzun bir yolculuk sırasında keşfedilen ilginç yerleri bulmak için uygundur.</p>
<p>Örneğin yüzey madenciliği için şu yanıtları verebilir:</p>
<p>"Hangi gezegende bakır çıkardım?"</p>
<p>veya:</p>
<p>"Bilinen gezegenlerimden hangilerinde özellikle çok sayıda maden sahası var?"</p>""",
    ),
 'jump_tip': (
        'Analiz',
        """
<h2>Analiz</h2>
<p>Analiz, kişisel keşif geçmişinizi kullanır. Sistem analizi girilen prosedürel sistem adını değerlendirir; Geçmiş veriler, geçmiş bulgular ve yeniden değerlendirme ile önceki kod analizini korur. İkisi de karar desteğidir, keşif garantisi değildir.</p>
<h3>Karşılaştırma temeli</h3>
<p>Kütle kodu temel tahmini sağlar. Bölge ve aile bunu dikkatle iyileştirir. Küçük yerel örnekler daha büyük veri tabanına doğru dengelenir. Az veri belirsizlik demektir, kötü değerlendirme değil. Yeterince incelenmemiş sistemler olumsuz bulgu sayılmaz.</p>
<h3>Potansiyel endeksi</h3>
<p>Potansiyel endeksi 100, dengelenmiş keşif potansiyelinizin kişisel geçmiş ortalamasına karşılık gelir. Endeks bir yüzde olasılığı değildir. Tek tip haritalama senaryosu ve dengelenmiş uç değerler karşılaştırmayı sağlar; ortanca ve dengelenmiş potansiyel tahmini kredilerdir, garantili kazanç değildir.</p>
<h3>Önemli bulgular</h3>
<p>Sistemin son numarası değerlendirilmez: Plio Aip KN-B d13-201, Plio Aip KN-B d13 ailesine aittir. BIO yalnızca bilgi amaçlıdır ve ana değerlendirmeye katılmaz. Eksik analizler sıfır değer kanıtlamaz.</p>
<h3>Sistem analizi</h3>
<p>Bir sistem girip Analiz et seçeneğini kullanın veya Enter’a basın. Mevcut sistemi kullan, adı mevcut oyun durumundan alır. Analiz yalnızca kullanıcı eylemiyle yeniden hesaplanır. Karşılaştırma temeli ve sonuçlar düzeylerini belirtir; yerel karşılaştırma yoksa üst düzey deneyim kullanılır. Veri kalitesi öneriden ayrı gösterilir.</p>
<p>“Sistem” alanına serbestçe bir ad yazabilirsin. “Mevcut sistemi kullan” yalnızca alanı doldurur; ardından “Analiz et” veya Enter ile başlat. Ad, desteklenen prosedürel adlandırma kalıbına göre yerel olarak denetlenir. Burada çevrimiçi sistem çözümlemesi veya belirsiz adlar için seçim listesi yoktur.</p>
<p>Boş giriş, desteklenmeyen ad, uygun karşılaştırma verisinin eksikliği veya hata durumunda önceki sonucun yerine bir mesaj gösterilir. Başarılı analiz öneriyi, potansiyel endeksini ve yerel veri temelini gösterir. Karşılaştırma tablosunda kütle kodu, bölge ve aile, sistem sayısı ve veri temeliyle birlikte yer alır; aşağıda geçmiş değerler ve bilinen özel buluntular görünür.</p>
<h3>Geçmiş veriler</h3>
<p>Sistem koduna göre geçmiş bulgular. Bu değerler bugüne kadarki keşif deneyimini gösterir ve tek bir hedef sistem için doğrudan tahmin değildir. Veri temeli ve güvenilirlik, mevcut örnekleme ve sektörler arasındaki dağılımına göre karşılaştırma verilerinin güvenilirliğini açıklar.</p>
<p>“Geçmiş veriler” sekmesinde “Hedef” altında bir seyahat hedefi değil, bir buluntu türü seçersin: örneğin keşif hedefi, BIO cinsi veya BIO türü. İlk değerlendirme görünüm oluşturulurken yapılır. Hedefi veya asgari sayıyı değiştirdikten sonra “Yeniden değerlendir” düğmesine basana kadar önceki sıralama kalır.</p>
<p>Hedef seçiminin yanındaki sayı alanı kod başına asgari örneklemi belirler: 1 ile 50 incelenmiş sistem, başlangıçta 3. Daha az sisteme sahip kodlar veya seçilen buluntu türü için geçmişte hiç isabeti olmayanlar sıralamaya alınmaz.</p>
<p>“Geçmiş örüntüler” tablosu en fazla 50 kodu sıra, geçmiş başarı (isabetli sistemler / incelenmiş sistemler), isabet oranı ve kanıt gücüyle gösterir. Sıralama yalnızca isabet oranına değil, yumuşatılmış geçmiş değerlendirmeye dayanır. Her iki tablonun sırası sabittir; sütun sıralaması veya ayrıntı işlemi yoktur. Uygun kalıp bulunmadığında bir mesaj görünür; değerlendirme hatası sıralamayı temizler ve hata mesajı gösterir. Analiz bir seyahat rotası hesaplamaz.</p>
""",
    ),
 'route_planner': ('Rota planlayıcı',
                   """<h2>Rota planlayıcı</h2>
<h3>Genel bakış</h3>
<p>Planlayıcı, Spansh üzerinden sistemler arası rota hesaplar. “Gemi rotası” veya “Fleet Carrier / CTSVision” seçin. Ağ bağlantısı gerekir; CMDRHelper gemiyi veya carrier’ı yönetmez.</p>

<h3>Başlangıç ve hedef</h3>
<p>“Başlangıç sistemi”, siz özel bir başlangıç girene kadar etkin komutanın bilinen mevcut sistemini izler. Alanı boşaltmak bu davranışı geri getirir. “Hedef sistem” alanına tam adı yazın; favorilerden alınan hedef gemi rotasını hazırlar, hesaplamayı başlatmaz.</p>
<p>Başlangıç ve hedef kesin olarak tanımlanmalıdır. Benzer adlar yerine seçilmez. Bilinmeyen veya belirsiz adlarda bir mesaj gösterilir; girdiyi düzeltin.</p>

<h3>Gemi rotası</h3>
<p>Burada gemi seçimi yoktur: etkin geminin bilinen verileri teknik alanları doldurur. Kendi değişiklikleriniz elle girilmiş değerler olarak korunur. “Gemi verilerini uygula” mevcut gemi verilerini yeniden uygular. Eksiksiz, eksik, eski veya bilinmeyen FSD verisi uyarısını kontrol edin.</p>
<p>“Ana tank kapasitesi”, “Mevcut kargo”, “Temel kütle”, “Yedek tank kapasitesi”, “Yedek yakıt”, “FSD optimum kütlesi”, “Atlayış başına azami FSD yakıtı”, “Yakıt gücü”, “Yakıt çarpanı” ve “Menzil takviyesi” değerlerini kontrol edin. Sıçrama özellikleri bunlardan hesaplanır; normal gemi menzili için tek bir alan yoktur. Yük ve donanım gerçek menzili değiştirebilir.</p>

<h3>Gemi seçenekleri ve hesaplama</h3>
<p>“Rota algoritması” seçenekleri optimistic, pessimistic, fuel, fuel_jumps ve guided değerleridir. Seçim Spansh’e gönderilir.</p>
<p>Seçenekler “Süperşarj/nötron yıldızlarını kullan”, “Gemi zaten süperşarjlı başlar”, “FSD enjeksiyonlarını kullan”, “İkincil yıldızları hariç tut” ve “Yakıt alınabilen her yıldızda ikmal yap”: nötron desteği, önceden güçlendirilmiş başlangıç, FSD enjeksiyonları, ikincil yıldızlar ve yakıt durakları. “Spansh ile gemi rotası hesapla” ile başlatın.</p>

<h3>Carrier rotası</h3>
<p>“Fleet Carrier / CTSVision”, belirli bir carrier seçmeden veya yönetmeden rota planlar. “Depodaki trityum” ve “Carrier ambarındaki trityum” girin; toplam en fazla 25.000 t olabilir. “Hesaplanan carrier kütlesi”, 25.000 t ile bu iki miktarın toplamını gösterir.</p>
<p>“Azami atlama menzili” 1–500 ly arasında ayarlanır; varsayılan 500 ly’dir. “Spansh ile rota hesapla” hesaplamayı başlatır. Bu istek sırasında carrier hesaplama düğmesi devre dışıdır.</p>

<h3>Spansh ve bekleme</h3>
<p>Rota Spansh tarafından arka planda hesaplanır. Durum, isteği ve ardından başarıyı veya hatayı gösterir. Burada ticaret fiyatları veya istasyon bilgileri değil, rotalar işlenir. Görünümde devam eden hesaplamayı iptal düğmesi yoktur.</p>

<h3>Rota sonucu</h3>
<p>Liste rota sırasını korur: numara, sistem, sıçrama mesafesi ve kalan mesafe. Serbest sıralama yapılamaz. Gemi rotalarında tüketim, depodaki yakıt, nötron ve yakıt ikmali; carrier rotalarında trityum tüketimi de gösterilir.</p>
<p>Altta toplam mesafe, sıçrama sayısı ve tüketim veya tahmini trityum yer alır. Eksik değerler “–” olarak kalır. Planı oyundaki gerçek durumla karşılaştırın.</p>

<h3>İlerleme ve sonraki hedef</h3>
<p>Başarıyla hesaplanan gemi rotası otomatik olarak alınır. “Mevcut sistem”, “Sonraki hedef” ve “Rota durumu” konumu, sonraki adımı ve durumu gösterir. Liste korunur; tamamlanan adımlara ek onay işareti konmaz.</p>
<p>Rotanın sonraki veya daha ilerideki sistemine algılanan gemi sıçraması ilerlemeyi öne taşır ve bundan sonraki sistemin adını otomatik olarak panoya kopyalar. Tekrarlanan konum bildirimleri ve carrier sıçramaları bu ilerleme sıçramalarından sayılmaz.</p>
<p>Rotayı yüklemek adı otomatik kopyalamaz. İlk başta veya sonraki hedef bulunduğu sürece “Sonraki hedefi kopyala” kullanın. Yalnızca sistem adı kopyalanır: otomatik yapıştırma veya Elite’i yönetme yoktur.</p>

<h3>Sapma ve tamamlanma</h3>
<p>Kalan rotanın dışına sıçramak “Mevcut sistem rota dışında” gösterir. Rota ve önceki sonraki hedef korunur; otomatik yeniden hesaplama yapılmaz. Daha sonra eşleşen ileri bir sıçrama rotayı sürdürebilir. İsterseniz yeni bir rota hesaplayabilirsiniz.</p>
<p>Son sistemde “Rota tamamlandı” görünür. “Sonraki hedef”, “–” olur; kopyalama düğmesi kapanır ve yeni ad kopyalanmaz. Pano içeriği silinmez. Sonuç listesi kalır.</p>

<h3>CTSVision dışa aktarımı</h3>
<p>Yalnızca carrier rotasında “CTSVision için dışa aktar” vardır. Başarılı hesaplamadan sonra yeni bir CSV dosyası seçin. Dosya, CTSVision’da daha sonra kullanmak için rota sırasını ve mevcut mesafe, yakıt, trityum ve ikmal verilerini içerir.</p>
<p>Bu bir dosya aktarımıdır; doğrudan bağlantı veya otomatik carrier yönetimi değildir. Mevcut dosyaların üzerine yazılmaz. Dosya penceresini iptal etmek dosya oluşturmaz; yazma hataları bildirilir.</p>

<h3>Hatalar ve ipuçları</h3>
<p>Eksik sistemler, eksik veya geçersiz gemi parametreleri ve fazla trityum bildirilir. Gerekli depo, kütle ve FSD değerleri pozitif olmalıdır; yedek yakıt, yedek depo kapasitesini aşamaz.</p>
<p>Rota bulunamaması, ağ sorunları, uzun bekleme veya kullanılamayan Spansh yanıtı da uydurma sonuç yerine mesaj üretir. Yeniden hesaplamadan önce adları, gemi verilerini ve seçenekleri kontrol edin.</p>

<h3>Analiz ve komutan</h3>
<p>“Analiz”, “Sistem analizi” ve “Geçmiş veriler” ile sistemleri ve mevcut deneyimleri değerlendirir. Rota planlayıcı ise başlangıçla hedef arasındaki gerçek güzergâhı hesaplar.</p>
<p>Ön doldurma, etkin komutanı ve gemisini kullanır. CMDR görünümünde başka bir komutana bakmak bunu değiştirmez.</p>"""),
 'images': ('Resimler',
            '<h2>Resimler</h2>\n'
            '<p>“Görüntüler” bölümü Elite Dangerous ile çekilen ekran görüntülerini yönetir. '
            'CMDRHelper, yeni kayıtları otomatik olarak tanıyabilir, işleyebilir ve komutana '
            'dayalı bir galeride saklayabilir.</p>\n'
            '\n'
            '<h3>Kaynak klasörü</h3>\n'
            "<p>Kaynak klasör, Elite Dangerous'nin ekran görüntülerini BMP formatında kaydettiği "
            'klasördür.</p>\n'
            '<p>CMDRHelper bu klasörü yeni BMP dosyaları açısından izleyebilir. Otomatik işlemenin '
            'çalışması için doğru ekran görüntüsü klasörünün ayarlanması gerekir.</p>\n'
            '\n'
            '<h3>Hedef klasör</h3>\n'
            '<p>Hedef klasör, CMDRHelper tarafından işlenen görüntülerin ortak kök '
            'klasörüdür.</p>\n'
            '<p>Kullanıcı bu kök klasörü ayarlar. CMDRHelper, işlem sırasında gerekli komutanla '
            'ilgili alt klasörleri otomatik olarak oluşturur.</p>\n'
            '\n'
            '<h3>Ayarları kaydet</h3>\n<p>“Ayarları kaydet”, kaynak ve hedef klasörlerini, çıktı biçimini, aydınlatmayı ve iki onay kutusunu kaydeder. İzleme bu seçimlerle yeniden ayarlanır; mevcut BMP dosyaları bilinen olarak işaretlenir. Galeri de yenilenir.</p>\n<p>“Galeriyi yenile”, geçerli galeri filtresine göre mevcut görüntü dosyalarından galeriyi yeniden yükler. BMP dönüştürmesi başlatmaz.</p>\n\n<h3>Otomatik işleme</h3>\n'
            '<p>"Yeni BMP dosyalarını otomatik dönüştür" etkinleştirilirse ve geçerli kaynak ve hedef klasörler '
            'ayarlanmışsa, CMDRHelper, yeni BMP ekran görüntüleri için kaynak klasörü düzenli '
            'olarak kontrol eder.</p>\n'
            '<p>Etkinleştirildiğinde, mevcut BMP dosyaları başlangıçta biliniyor olarak '
            "işaretlenir ve sorulmadan otomatik olarak dönüştürülmez. Bunun için mevcut BMP'leri "
            'dönüştürmeye yönelik ayrı bir işlev mevcuttur.</p>\n'
            '<p>Yeni bir dosya, birbirini takip eden iki denetimde aynı sıfırdan farklı boyuta '
            'sahip olana kadar kuyruğa alınmaz. Sonuç olarak, halen devam eden bir yazma işlemi '
            'hemen işlenmez.</p>\n'
            '\n'
            '<h3>Resim dönüştürme</h3>\n'
            '<p>Kaynak olarak CMDRHelper, BMP dosyalarını işler. Hedef format olarak “PNG” veya '
            '“JPG” seçilebilir.</p>\n'
            '<p>JPG dosyaları 95 kalite seviyesinde kaydedilir. PNG dosyaları optimize edilmiş bir '
            'şekilde kaydedilir.</p>\n'
            '<p>Varsayılan olarak orijinal BMP dosyası korunur. "Başarılı dönüştürmeden sonra BMP’yi sil" '
            'etkinleştirilirse, kaynak BMP yalnızca hedef görüntü başarıyla kaydedildikten sonra '
            'silinecektir.</p>\n'
            '\n'
            '<h3>Görüntüyü aydınlat</h3>\n'
            '<p>Parlaklık, bir kaydırıcı ve bağlantılı sayı alanı kullanılarak yüzde 0 ila 50 '
            'arasında ayarlanır. Ayar kaydedilir.</p>\n'
            '<p>Daha sonra başlatılan her dönüşüm sırasında, hem yeni izlenen hem de manuel olarak '
            'başlatılan mevcut BMP dosyaları için otomatik olarak uygulanır. Yüzde 0 orijinal '
            'parlaklığı devralır; daha yüksek değerler, oluşturulan PNG veya JPG görüntüsünün '
            'parlaklığını buna göre artırır.</p>\n'
            '<p>İşlev yalnızca bir önizleme değildir ve daha sonra galeride seçilen bir görüntüye '
            'uygulanmaz. Değiştirilen parlaklık yeni hedef dosyaya kaydedilir.</p>\n'
            '<p>BMP dosyasının silinmesi de etkinleştirilmediği sürece kaynak BMP değişmeden '
            'kalır. Günlük, komutan ve keşif verileri değişmedi.</p>\n'
            '\n'
            '<h3>Komutanla ilgili depolama</h3>\n'
            "<p>Yeni ekran görüntüleri, aktif canlı AppState'te bulunan günlük kimliğine dayalı "
            "olarak gerçek oynayan Komutan'a atanır.</p>\n"
            '<p>Klasör yapısı komutan adını ve Frontier kimliğini içerir, örneğin:</p>\n'
            '<p><b>EXAMPLE_F12345678/</b></p>\n'
            '<p>FID, birden fazla komutanla bile görevin net olmasını sağlar. Bu, aynı isimdeki '
            'iki komutanın ayırt edilmesini sağlar.</p>\n'
            '\n'
            '<h3>dosya adları</h3>\n'
            '<p>Yeni işlenen görüntüler, yakalanma zamanını, komutanın adını ve (varsa) sıraya '
            'alınırken bilinen yıldız sistemini içeren bir ad alır.</p>\n'
            '<p>Örnek:</p>\n'
            '<p><b>2026-09-04_&#8203;13-18-22_&#8203;EXAMPLE_&#8203;Sol.png</b></p>\n'
            '<p>FID, yine görüntü dosyası adında değil, komutanla ilgili klasör adındadır.</p>\n'
            '\n'
            '<h3>Güvenli dosya adları</h3>\n'
            '<p>CMDRHelper, dosya ve klasör bileşenleri olarak kullanılmak üzere komutan ve sistem '
            'adlarını temizler.</p>\n'
            '<p>Yasadışı kontrol ve Windows karakterleri değiştirilir, boşluklar birleştirilir, '
            'sorunlu noktalar veya sondaki boşluklar kaldırılır ve CON veya NUL gibi ayrılmış '
            'Windows adları güvence altına alınır.</p>\n'
            '\n'
            '<h3>Kayıt süresi</h3>\n'
            '<p>Adlandırma için CMDRHelper, kararlı olarak tanınan BMP dosyasının değiştirilme '
            'zamanını kullanır. Ancak bu okunamıyorsa mevcut saat kullanılacaktır.</p>\n'
            '<p>Bu, adın genellikle sonraki dönüştürme zamanına değil kaynak dosyaya bağlı olduğu '
            'anlamına gelir.</p>\n'
            '\n'
            '<h3>Aynı saniyede birden fazla görüntü</h3>\n'
            '<p>Amaçlanan dosya adı zaten mevcutsa veya devam eden bir dönüştürme için ayrılmışsa, '
            'CMDRHelper onu sürekli olarak '
            'ekler <code>_2</code>,<code>_3</code>,<code>_4</code> vb.</p>\n'
            '<p>Bu, aynı zaman damgasına sahip başka bir ekran görüntüsünün mevcut bir hedef '
            'görüntünün üzerine yazmayacağı anlamına gelir.</p>\n'
            '\n'
            '<h3>İşlem sırasında komutan değişikliği</h3>\n'
            '<p>Bir ekran görüntüsü sıraya alınırken Komutan, FID ve sistem birlikte '
            'yakalanır.</p>\n'
            '<p>Daha sonra yapılacak bir komutan değişikliği, halihazırda bekleyen bu görüntünün '
            "atamasını değiştirmez. Bu, EXAMPLE'in ekran görüntüsünün daha sonra başka bir "
            'komutanın klasörüne yazılmayacağı anlamına gelir.</p>\n'
            '\n'
            '<h3>galeri</h3>\n'
            '<p>Galeri, seçilen filtreyle ilişkili dizinlerdeki PNG, JPG ve JPEG dosyalarını '
            'gösterir. Yeni, silinmiş veya taşınmış görüntüler düzenli olarak algılanır.</p>\n'
            '<p>Galeri filtresi, dosyaların depolama konumunu veya komutan atamasını '
            'değiştirmez.</p>\n'
            '\n'
            '<h3>Mevcut komutan</h3>\n'
            '<p>Geçerli Komutan filtresi, CMDR görünümünde o anda görüntülenen komutanın '
            'klasöründeki görüntüleri gösterir.</p>\n'
            '<p>Söz konusu komutan yalnızca galeri gösterimini belirler. Öte yandan, yeni bir '
            'canlı ekran görüntüsü atamak, sıraya alma sırasında etkin olan günlük kimliğini '
            'kullanır.</p>\n'
            '\n'
            '<h3>Tüm komutanlar</h3>\n'
            '<p>“Tüm Komutanlar” filtresi, bilinen tüm komutanların geçerli alt klasörlerindeki '
            'görselleri bir arada gösterir. Tanınmış kimliği olmayan kayıtlar için özel klasör de '
            'dikkate alınır.</p>\n'
            '<p>Dosyalar taşınmaz veya birleştirilmez.</p>\n'
            '\n'
            '<h3>Atanmadı</h3>\n'
            '<p>Atanmamış filtresi, doğrudan paylaşılan hedef kök klasörde bulunan desteklenen '
            'görüntü dosyalarını gösterir.</p>\n'
            '<p>Özellikle, komutanla ilgili alt klasörleri olmayan eski resimler görünür durumda '
            'kalır. CMDRHelper olaydan sonra onların bağlılığını tahmin etmeye çalışmaz.</p>\n'
            '\n'
            '<h3>Mevcut resimler</h3>\n'
            '<p>Kök klasörde zaten mevcut olan resimler otomatik olarak taşınmaz veya yeniden '
            'adlandırılmaz.</p>\n'
            '<p>PNG, JPG veya JPEG olarak mevcut oldukları sürece "Atanmamış" aracılığıyla '
            'erişilebilir olmaya devam ederler.</p>\n'
            '\n'
            '<h3>Resmi seçin ve görüntüleyin</h3>\n'
            '<p>Bir önizleme görüntüsüne basit bir tıklama, görüntüyü önizleme alanında '
            'ölçeklendirilmiş olarak gösterir ve dosya adını görüntüler.</p>\n'
            '<p>Çift tıklama, görüntülere yönelik işletim sistemi uygulama setini içeren dosyayı '
            'açar.</p>\n'
            '<p>Aynı anda birden fazla görüntü işaretlenebilir. Pencere boyutunu değiştirdiğinizde '
            'geçerli görüntünün önizlemesi sığacak şekilde yeniden ölçeklendirilir.</p>\n'
            '\n'
            '<h3>Resmi sil</h3>\n'
            '<p>İşaretlenen görüntüler “Seçilenleri sil” veya Sil tuşu kullanılarak silinebilir. '
            'Silmeden önce bir güvenlik sorgusu görüntülenir; Seçim yapılmadığında öncelikle '
            'gerekli seçime dikkat çekilir.</p>\n'
            '<p>Geçerli galeri filtresinin dizinlerinden yalnızca seçilen PNG/JPG/JPEG hedef '
            'dosyaları silinir. Orijinal BMP kaynak dosyası etkilenmez.</p>\n'
            '\n'
            '<h3>Hedef klasörü aç</h3>\n'
            '<p>“Hedef klasörü aç”, dosya yöneticisindeki depolama konumunu açar ve gerekirse '
            'paylaşılan kök klasörü oluşturur.</p>\n'
            '<p>"Geçerli Komutan" filtresi mevcut Komutan alt klasörünü açar. Henüz mevcut değilse '
            'veya başka bir filtre etkinse, paylaşılan kök klasör açılacaktır.</p>\n'
            '\n'
            '<h3>Görüntü yollarının güvenliği</h3>\n'
            '<p>CMDRHelper, silmeden önce her dosyanın kurallı yolunu kontrol eder. '
            'Yapılandırılmış hedef klasörün içinde ve doğrudan geçerli galeri filtresinin izin '
            'verdiği bir dizinde olmalıdır.</p>\n'
            '<p>Sembolik bağlantılar komutan klasörü veya galeri görseli olarak kullanılmaz ve '
            'galeri üzerinden silinmez. Hedef alanın dışındaki yollar ve geçiş yolları '
            'reddedilir.</p>\n'
            '\n'
            '<h3>Herhangi bir komutan tespit edilmezse</h3>\n'
            '<p>Yeni bir kaydı sıraya alırken Commander ve FID eksikse dosya beklemeye alınmayacak '
            've bilinen bir Komutana atanmayacaktır.</p>\n'
            '<p>Alt klasörde olacak <b>UNKNOWN_&#8203;UNKNOWN/</b> işlenmiş; Komutan için de '
            'kullanılan dosya adı <b>UNKNOWN</b>. Bu klasör, Ayrılmamış kök klasör filtresi '
            'aracılığıyla değil, Tüm Komutanlar aracılığıyla görüntülenebilir.</p>\n'
            '\n'
            '<h3>Birkaç komutan</h3>\n'
            '<p>Görüntü yönetimi için iki ayrı kural geçerlidir:</p>\n'
            '<ul>\n'
            '<li><b>Yeni görselleri kaydet:</b> Kuyruğa alındığında Commander ve FID ile etkin '
            'günlük kimliği, hedef klasörü belirler.</li>\n'
            '<li><b>Resimleri görüntüle:</b> Görüntülenen komutan veya seçilen galeri filtresi '
            'görünür görüntüleri belirler.</li>\n'
            '</ul>\n'
            '<p>Bu, EXAMPLE oynatılırken başka bir komutanın galerisinin, yeni ekran görüntüleri '
            'söz konusu komutanın klasörüne düşmeden görüntülenebileceği anlamına gelir.</p>\n'
            '\n'
            '<h3>İpucu</h3>\n'
            '<p>Paylaşılan bir ekran görüntüsü kök klasörü yeterlidir. CMDRHelper, yeni işlenen '
            'görüntüleri otomatik olarak Commander ve FID olarak ayırır.</p>\n'
            '<p>"Mevcut Komutan", "Tüm Komutanlar" ve "Atanmamış" seçenekleriyle kişisel galeri, '
            'tüm komutanların alt klasörleri ve kök klasördeki eski görüntüler arasında geçiş '
            'yapabilirsiniz.</p>\n'
            '<p>Daha yüksek parlaklık, karanlık fotoğraflarda yardımcı olabilir; dönüşüm sırasında '
            'yeni oluşturulan hedef görüntüyü etkiler.</p>'),
 'commander_view': (
        'CMDR görünümü',
        """<h2>CMDR görünümü</h2>
<h3>Komutan seçimi</h3>
<p>Üstteki seçim, kimin kayıtlı verilerini görüntülediğinizi belirler. ● Canlı aktif etkin günlük komutanını, Yalnızca görüntüleme başka bir kayıtlı profili gösterir. Seçim etkin günlük komutanını değiştirmez: ana “Görevler ve Ödüller” sayfası gerçekten oynayan komutanı kullanmaya devam eder. Adlar aynı olsa bile kişisel veriler FID ile ayrı tutulur. Bir profili görüntülemek çevrimiçi veri gönderimi başlatmaz.</p>

<h3>Genel bakış, servet ve MercCoins</h3>
<p>“Genel bakış”; ad, FID, durum, ilk ve son kayıt, ziyaret edilen sistemler, biyolojik/jeolojik bulgular, Codex kayıtları ve haritacılık satışları, konum, açık görevler, gemi, taşıyıcı ve bilinen tahminleriyle satılmamış biyolojik/haritacılık verilerini gösterir. “Servet” son kaydedilen kredi bakiyesidir. “Mercenary credits”, Frontier’ın bildirdiği değerleri gösterir: “Current”, “Total spent”, “Engineering”, “Gear” ve “Reported by Frontier: total earned”. Bu sayaçlar matematiksel olarak uyuşmayabilir; CMDRHelper bunları düzeltmez veya hayali işlem geçmişi oluşturmaz. Bilinmeyen değerler “–” olarak kalır.</p>

<h3>Görevler ve keşif</h3>
<p>“Görevler”, görüntülenen komutanın kayıtlı açık görevlerini durum, görev adı, hedef, bitiş zamanı ve ödülle gösterir. Tablo yalnızca inceleme içindir; ana sayfadaki görev ayrıntıları veya görev işlemleri burada yoktur. “Keşif”; satılmamış biyolojik/haritacılık verilerini, biyolojik bulguları, ilk ayak basışları, kişisel ve verimli haritalanan gök cisimlerini ve ziyaret edilen sistemleri gösterir. “Kronik” burada bir yer tutucudur; tam tarihçeyi ana menüden açabilirsiniz.</p>

<h3>Filo ve gemi ayrıntıları</h3>
<p>“Gemiler”, üstte mevcut veya son kullanılan gemiyi, altında komutanın kayıtlı filosunu gösterir. Ayrıntıları açmak için gemi kartının başlığına tıklayın. Kullanım, ad, tür, sıçrama menzili, kargo kapasitesi, boş kütle, konum veya zamana göre artan/azalan sıralayın; tüm gemileri ya da araç/avcı hangarı olanları filtreleyin. Yeşil, canlı veride etkin gemiyi belirtir; diğer renkler bilinen konumları gruplar. Ayrıntılarda kimlik, ShipID, konum, zamanlar, FSD/Guardian güçlendirici, menzil, kütle, kargo/yakıt kapasiteleri ve donanım durumu (tam, eksik veya eski) yer alır. Bilinen modül verileri hangarları, kalkanları ve takviyeleri, silahları ve yolcu kabinlerini ekler. Eksik bilgiler “–” olarak kalır.</p>

<h3>Kendi filo taşıyıcınız</h3>
<p>“Kendi Fleet Carrier”, kayıtlı kendi taşıyıcınızın adını, çağrı işaretini, CarrierID bilgisini, son konumunu ve güncelleme zamanını gösterir. Bunlar ticaret teklifleri veya madencilik stokları değildir.</p>

<h3>Kişisel gemi ve taşıyıcı resimleri</h3>
<p>Açılmış gemi ayrıntılarında “Gemi görseli seç…”, taşıyıcıda “Filo gemisi resmi seç…” kullanın. PNG, JPG/JPEG ve WEBP desteklenir. CMDRHelper, komutana ve gemiye veya taşıyıcıya özel yerel bir kopya saklar; yeniden başlatıldığında da korunur. Yeni seçim bu kopyayı değiştirir. “Kişisel görseli kaldır” kopyayı ve bağlantısını kaldırır; özgün resim dosyası korunur. Kişisel resim yoksa mevcut standart önizleme veya yer tutucu gösterilir. Taşıyıcı kesin olarak tanımlanamıyorsa resim seçimi devre dışıdır. Ekran görüntüleri otomatik eşleştirilmez.</p>

<h3>Resim görüntüleyici</h3>
<p>Mevcut bir gemi veya taşıyıcı resmine çift tıklamak, yalnızca küçük önizlemeyi değil resim dosyasını kullanan ayrı görüntüleyiciyi açar. Resim, oranları korunarak pencereye sığdırılır. Pencereyi büyütebilir veya ekranı kaplatabilir, Esc ya da kapatma düğmesiyle kapatabilirsiniz. Resimler arasında gezinme veya yakınlaştırma denetimi yoktur. Ana “Görseller” bölümü ise ekran görüntülerini yönetir.</p>

<h3>Gemi silme</h3>
<p>“Gemiyi sil…” açık onay gerektirir; varsayılan seçim iptaldir. İşlem yerel gemi kaydını, kayıtlı donanım verilerini ve kişisel resim kopyasını kaldırır. Mevcut veya son kullanılan gemi ile canlı veride etkin olarak tanınan gemi korunur; yeniden okuma sırasında silme engellenir. Yerel silme işareti, eski günlük verilerinin gemiyi hemen geri getirmesini önler. Silmeden sonra canlı günlükte bu geminin etkin olduğuna dair yeni ve kesin bir bildirim gemiyi geri getirebilir. Onaylanan yeniden okuma da işareti kaldırabilir. Silinen kişisel resim kopyası geri gelmez.</p>

<h3>Tüm gemileri yeniden okuma</h3>
<p>“Tüm gemileri yeniden oku…”, mevcut günlüklerden filo bilgilerini tekrar almak veya yerel olarak silinen gemileri bulmak için kullanışlıdır. Onaydan sonra bilinen günlük dosyaları ve ayarlanmış günlük klasöründeki dosyalar, görüntülenen komutan için yalnızca filo verileri amacıyla yeniden okunur. Elite’in çalışması gerekmez. Daha yeni kayıtlı bilgiler ve mevcut günlüklerde bulunmayan gemiler korunur; tanınan satışlar dikkate alınır. Başarıyla tamamlanırsa bu komutanın elle silme işaretleri kaldırılır. Mevcut kişisel resimler korunur; silinenler geri gelmez. Diğer komutanlar etkilenmez. Okuma veya uygulama başarısız olursa işaretler kalır: günlüklere erişimi kontrol edip yeniden deneyin.</p>

<h3>Yerel veriler ve güvenlik</h3>
<p>Kayıtlı bilgiler çevrimdışı ve yeniden başlatma sonrasında da görülebilir; bilinen son durumu temsil eder. Resimler, silme ve yeniden okuma yalnızca CMDRHelper’ı etkiler. Elite Dangerous’taki gemileri, taşıyıcıları veya kredileri değiştirmez, günlükleri yeniden yazmaz.</p>""",
    ),
 'settings': ('Ayarlar',
              '<h2>Ayarlar</h2>\n<h3>CMDRHelper</h3>\n<p>Daha iyi güncelleme bilgisi: Evet/Hayır penceresi kurulu ve mevcut sürümü, özet varsa en fazla altı yeniliği gösterir. Uzun listeler kaydırılırken eylemler erişilebilir kalır.</p>\n'
              '<p>"Ayarlar" alanı CMDRHelper\'nin Elite Dangerous, günlük dosyaları, veritabanı, '
              'çevrimiçi hizmetler, arayüz ve güncellemelerle nasıl çalışacağını belirler.</p>\n'
              '<p>Kimlik bilgileri ve yollardaki değişiklikler dikkatli bir şekilde yapılmalıdır. '
              'Komutanla ilgili ayarlar gerekirse Frontier ID tarafından ayrı olarak '
              'yönetilir.</p>\n\n<h3>Hızlı favori</h3>\n<p>“Hızlı favori” altında “Kısayol ata” ile genel bir kısayol atayabilir veya “Kısayolu değiştir” ile değiştirebilirsin. “Kısayolu kaldır” atamayı kaldırır; başlangıç durumu “Atanmamış” olur. Seçim kaydedilir. Kayıt çakışması bir mesaj gösterir. Kısayol, geçerli mevcut yüzey konumunu iletişim kutusu olmadan komutana ait favori olarak kaydeder, ekran görüntüsü oluşturmaz. Uygun konum verisi yoksa hiçbir şey kaydedilmez.</p>\n'
              '\n'
              '<h3>günlük</h3>\n'
              '<p>Günlük klasörü en önemli ayarlardan biridir. Elite Dangerous dosyasının '
              'bulunduğu klasörü işaret etmelidir.<code>Journal*.log</code> Kullanılan Windows veya '
              'Proton profilinin dosyaları.</p>\n'
              '<p>Günlükler diğer şeylerin yanı sıra şunları sağlar:</p>\n'
              '<ul>\n'
              '<li>Komutanın kimliği, konumu ve seyahati</li>\n'
              '<li>Görevler, gemiler ve varlıklar</li>\n'
              '<li>Keşif, haritacılık ve BIO verileri</li>\n'
              '<li>Yüzey madenciliği, paralı paralar ve desteklenen diğer durumlar</li>\n'
              '</ul>\n'
              '\n'
              '<h3>Günlük ekranı ve çalışması</h3>\n'
              '<p>Günlük grubu, klasör kümesini, bulunan günlük sayısını, en eski ve en yeni '
              'günlükleri, en yeni dosyanın adını ve son okunan girdinin zamanını gösterir.</p>\n'
              '<p>“Günlük klasörünü seç” klasörü değiştirir. “Şimdi oku” normal güncellemeyi hemen '
              'tetikler.</p>\n'
              '<p>Açıkça tanımlanabilir oturumlar FID kullanılarak atanır. Yeni tam girişler '
              'aşamalı olarak işlenir; Güvenli okuma konumları, her günlüğün bir sonraki '
              'başlatılışında gereksiz yere bütünüyle yeniden okunmasını önler.</p>\n'
              '\n'
              '<h3>veritabanı</h3>\n'
              '<p>CMDRHelper, gerekli verileri yerel bir SQLite veritabanında kalıcı olarak '
              'saklar. Buna küresel sistem ve vücut verilerinin yanı sıra açıkça bir komutana '
              'atanan bilgiler de dahildir.</p>\n'
              '<p>Ayarlar sayfası kaydedilen verilerle ilgili istatistikleri gösterir. CMDRHelper '
              'çalışırken veritabanı manuel olarak düzenlenmemelidir.</p>\n'
              '\n'
              '<h3>Günlük arşivini içe aktar</h3>\n'
              '<p>“Günlük arşivini içe aktar”, ayarlanan günlük klasörünün günlük dosyalarını '
              'veritabanıyla tamamen karşılaştırır. Halihazırda bilinen günlük alanları, kayıtlı '
              'içe aktarma bilgilerine göre dikkate alınır ve yeni veriler olarak körü körüne '
              'kopyalanmaz.</p>\n'
              '<p>Manüel olarak görülebilen bir içe aktarma sırasında ilerleme durumu, sayı ve o '
              'anda işlenen dosya görüntülenir. Tamamlamanın ardından CMDRHelper, içe aktarılan '
              'veya zaten bilinen verileri veya bir hatayı bildirir.</p>\n'
              '<p>Arşiv içe aktarma aynı zamanda açıkça atanmış günlüklerden desteklenen tarihsel '
              'bilgilerin yeniden öğrenilmesine de hizmet eder.</p>\n'
              '\n'
              '<h3>Komutanla ilgili veriler</h3>\n'
              "<p>CMDRHelper, kişisel bilgileri FID'ye ve ilgili dahili Komutan Kimliğine göre "
              'ayırır. Bunlara görevler, varlıklar, MercCoins, kişisel keşif ve çevrimiçi erişim '
              'dahildir ancak bunlarla sınırlı değildir.</p>\n'
              '<p>Bilinmeyen veya belirsiz bir günlük oturumu keyfi olarak bir komutana '
              'atanamaz.</p>\n'
              '\n'
              '<h3>Çevrimiçi Hizmetler</h3>\n'
              "<p>CMDRHelper, EDSM ve Inara'yi destekler. Her iki erişim de bilinen her komutan "
              'veya her FID için ayrı ayrı işlenir ve kaydedilir.</p>\n'
              '<p>Ayarlardaki seçim yalnızca kimin erişiminin o anda düzenlenmekte veya test '
              'edildiğini belirler. Yalnızca aktif günlük oturumu tarafından açıkça tanımlanan '
              'komutanın canlı gönderim yapmasına izin verilir.</p>\n'
              '\n'
              '<h3>Spansh istasyon bilgileri</h3>\n'
              '<p>“ÇEVRİMİÇİ HİZMETLER” altında “Spansh istasyon bilgilerini ekle”, Explorer ve sistem görünümlerine isteğe bağlı istasyon ve tesis bilgileri ekler. Seçenek başlangıçta kapalıdır. Komutan bilgileri değil, herkese açık sistem kimliği gönderilir; kişisel API anahtarı gerekmez. Bu seçenek ticaret pazarı aramasını yönetmez.</p>\n'
              '<p>Kapalıyken yalnızca yerel günlük bilgileri gösterilir ve yeni Spansh istasyon istekleri başlatılmaz; elle güncelleme de devre dışıdır. Mevcut istasyon önbelleği silinmez, ancak görünümü tamamlamak için kullanılmaz. Açmak, önbellek verilerini yeniden kullanılabilir kılar; tek başına ağ isteği başlatmaz.</p>\n'
              '\n'
              '<h3>Otomatik istasyon istekleri ve önbellek</h3>\n'
              '<p>Otomatik kontrol yalnızca etkin günlük komutanının farklı bir sisteme yeni canlı girişi algılandığında yapılır; örneğin gemi veya carrier sıçramasından ya da yeni doğrulanmış konum bildiriminden sonra. Programı başlatmak, komutan değiştirmek, arşiv içe aktarmak ve yalnızca Explorer’ı veya sistem görünümünü açmak otomatik istek başlatmaz.</p>\n'
              '<p>Ayrı istasyon önbelleği Helper yeniden başlatıldığında korunur. Üzerinden 7 günden az geçen bir indirme güncel sayılır ve yeni otomatik ağ isteğini önler. Eksik veya eski veriler, koşulları karşılayan bir sonraki canlı sistem girişinde güncellenebilir. Sistem başına yerel takvim gününde en fazla bir otomatik deneme yapılır; başarısızlık da sayılır ve bu sınır yeniden başlatmalarda korunur. Kayıtlı tüm sistemler arka planda sürekli güncellenmez. Kullanılabilir eski önbellek verileri çevrimdışıyken de gösterilebilir.</p>\n'
              '<p>Bu önbellek ticaret fiyatlarını değil, ek istasyon bilgilerini içerir. Satış, alış ve önerilerdeki Spansh topluluk pazar verilerinin ayrı, geçici RAM arama önbelleği vardır. Elite’te bizzat gözlemlediğiniz ticaret pazarı kayıtları ise ayrıca saklanır: yeniden başlatmadan sonra korunur, ancak yalnızca 24 saatten daha yeniyken geçerlidir.</p>\n'
              '\n'
              '<h3>İstasyon verilerini elle güncelleme</h3>\n'
              '<p>“Sistem genel görünümü” açıp “Spansh verilerini yenile” seçin. Kayıtlı tüm sistemler veya ticaret fiyatları değil, yalnızca bu penceredeki sistemin Spansh istasyon bilgileri güncellenir. Seçenek açık olmalıdır; bu sistem için devam eden istek sırasında işlem devre dışıdır.</p>\n'
              '<p>Elle güncelleme, 7 günlük süreyi ve o gün başarısız olmuş otomatik denemeyi atlayabilir. Sistem yerel takvime göre bugün zaten başarıyla indirilmişse yeni istek yapılmaz: “Spansh verileri bugün zaten güncellendi.” Başarılı indirme istasyon önbelleğini yeniler. Hatalarda yerel ve kullanılabilir önbellek verileri korunur; durum satırı başarısızlığı gösterir. Başarısız elle deneme tekrarlanabilir.</p>\n\n<h3>EDSM gökcismi verileri ve önbellek</h3>\n<p>“EDSM kullan”, Explorer’da etkin günlük komutanının mevcut sistemine ait ek gökcismi verilerini de denetler. “Çevrimiçi erişimi kaydet” sonrasında ve normal günlük güncellemelerinde kullanılabilir önbellek yüklenir veya EDSM arka planda sorgulanır. Bu herkese açık gökcismi sorgusu ağ gerektirir ancak API anahtarı gerektirmez; günlük yükleme ayrı bir işlemdir.</p>\n<p>Alınan gökcismi verileri sistem başına yerel olarak saklanır ve yeniden başlatmalar dahil en fazla 24 saat önbellekten kullanılabilir. Daha eski veriler uygun bir güncellemede yeni sorguya yol açar. İşlev kapalıyken bu önbellek görünüme veri eklemez ve yeni gökcismi sorguları başlamaz; önbellek dosyaları silinmez. Yerel günlük verileri kullanılabilir kalır. Sorgu hataları uydurma gökcisimleri oluşturmaz.</p>\n'
              '\n'
              '<h3>EDSM erişimi</h3>\n'
              "<p>“EDSM erişimi:” düzenlenecek komutanı seçer. Seçim, API-Key'nin saklanıp "
              'saklanmadığına bağlı olarak "kuruldu" veya "kurulmadı" ifadesini '
              'gösterecektir.</p>\n'
              '<p>Komutanın adı, gizli API-Key alanı, "EDSM Kullan", bir bağlantı testi ve son '
              'test durumu görünür.</p>\n'
              '<p>Her komutanın kendi uygun EDSM erişimine ihtiyacı vardır. Seçim, canlı '
              'yükleyiciyi bu komutana değiştirmez.</p>\n'
              '\n'
              "<h3>EDSM'yi kullanın ve test edin</h3>\n"
              '<p>“EDSM Kullan” seçilen FID için hizmeti etkinleştirir veya devre dışı bırakır. '
              'Eksik veya devre dışı bırakılmış kimlik bilgileri yerel günlük işlemeyi '
              'etkilemez.</p>\n'
              '<p>“EDSM bağlantısını test et” formda o anda görünen erişim verilerini kontrol '
              "eder. Başarılı bir test bağlantıyı doğrular ancak aktif günlük FID'yi veya canlı "
              'komutanı değiştirmez.</p>\n'
              '\n'
              '<h3>Inara erişimi</h3>\n'
              '<p>“Inara Erişimi:” aynı çoklu CMDR ilkesini izler. Etkinleştirme, Inara komutan '
              'adı ve API-Key, her FID için ayrı ayrı kaydedilir.</p>\n'
              '<p>Burada da seçim "kuruldu" veya "ayarlanmadı" olarak görünüyor. Bir komutanın '
              'anahtarı otomatik olarak başka bir komutan için kullanılmaz.</p>\n'
              '\n'
              "<h3>Inara'yi kullanın ve test edin</h3>\n"
              '<p>Inara aktif günlük FID için ayarlanıp etkinleştirildiğinde, CMDRHelper '
              'desteklenen seyahat, konum, görev ve gemi olaylarını iletebilir. Her günlük '
              "etkinliği Inara'ye gönderilmez.</p>\n"
              '<p>"Inara bağlantısını test et", canlı kumandayı değiştirmeden mevcut görünür '
              'erişim verilerini kontrol eder.</p>\n'
              '\n'
              '<h3>Inara giden kutusu</h3>\n'
              '<p>Desteklenen Inara olayları, ağ aktarımından önce bir giden kutusunda kalıcı '
              'olarak işaretlenir.</p>\n'
              '<p>Geçici hatalar bu girişlerin daha sonraki denemeler için korunmasına olanak '
              'tanır. Çalışan yalnızca benzersiz şekilde etkin olan FID günlüğünün giden kutusunu '
              'işler; Diğer komutanların girişleri dahil değildir.</p>\n'
              '\n'
              '<h3>Başlıktaki çevrimiçi durum</h3>\n'
              '<p>EDSM şu anda şunları gösteriyor:</p>\n'
              '<ul>\n'
              '<li><b>EDSM</b>– aktif FID için kullanılamaz veya devre dışı bırakılamaz</li>\n'
              '<li><b>EDSM bekliyor</b>– kurulum ve devam eden iletim olmadan</li>\n'
              '<li><b>EDSM şanzıman</b>– son EDSM işleme çalıştırması hatasız olarak sona erdi; '
              'Araç ipucu olayların gönderilip gönderilmediğini, günlük verilerinin işlenip '
              'işlenmediğini veya yeni veri bulunup bulunmadığını belirtir</li>\n'
              '<li><b>EDSM hatası</b>– son aktarım durumu yanlış</li>\n'
              '</ul>\n'
              '<p>Şu anda EDSM için ayrı olarak etiketlenmiş ek bir "EDSM aktif" durumu '
              'bulunmamaktadır.</p>\n'
              '<p>Inara şunları daha kesin bir şekilde ayırt eder:</p>\n'
              '<ul>\n'
              '<li><b>INARA çıktı</b>– aktif günlük FID için devre dışı bırakıldı</li>\n'
              "<li><b>INARA'ya hazır</b>– kuruldu ancak bu oturumda hâlâ onaylanmış iletim "
              'yok</li>\n'
              '<li><b>INARA iletimi</b>– işçi şu anda gönderiyor</li>\n'
              '<li><b>INARA aktif</b>– son gerçek transfer başarıyla onaylandı</li>\n'
              '<li><b>INARA hatası</b>– son aktarım girişimi başarısız oldu</li>\n'
              '</ul>\n'
              '\n'
              '<h3>API-Key güvenliği</h3>\n'
              "<p>API-Key'ler kişisel kimlik bilgileridir. Giriş alanları gizlidir; Bunlar, "
              'CMDRHelper veritabanında değil, uygulama ayarlarında komutanla ilgili olarak '
              'saklanır.</p>\n'
              '<p>Anahtarlar yayımlanmamalı, ekran görüntülerinde paylaşılmamalı veya herkese '
              'açık depolara eklenmemelidir.</p>\n'
              '\n'
              '<h3>Resimler/Ekran Görüntüleri</h3>\n'
              "<p>Kaynak Klasör, Hedef Klasör, PNG/JPG, Otomatik İşleme, BMP Silme ve yüzde 0'dan "
              "50'ye kadar Parlaklaştırma, Ayarlar sayfasında değil, yalnızca ana Görüntüler "
              'menüsünde bulunur.</p>\n'
              '<p>"Görüntüler"in bağlama duyarlı yardımında bu seçenekler ayrıntılı olarak '
              'açıklanmaktadır.</p>\n'
              '\n'
              '<h3>yüzey</h3>\n'
              '<p>Arayüz grubu, değerli kaşif gövdeleri için görünümü, dili, yazı tipini, yazı '
              'tipi boyutunu ve değer eşiğini içerir.</p>\n'
              '\n'
              '<h3>Karanlık ve aydınlık modu</h3>\n'
              '<p>Koyu ve açık görünüm arasında doğrudan geçiş yapabilirsiniz. Tema anında arayüze '
              've mevcut sistem ve geçmiş kartlarına uygulanarak kaydedilir.</p>\n'
              '\n'
              '<h3>Dil</h3>\n'
              '<p>Arayüz, aralarından seçim yapabileceğiniz on iki dil sunar. “Dili Kaydet” seçimi '
              "kaydeder; Mevcut widget'ların tamamen tek tip bir dönüşümü için CMDRHelper'nin "
              'yeniden başlatılması gerekir.</p>\n'
              '\n'
              '<h3>Yazı tipi ve yazı tipi boyutu</h3>\n'
              '<p>Yazı tipi ailesi ve yazı tipi boyutu 7 ila 24 punto arasında seçilebilir ve '
              'kaydedilebilir.</p>\n'
              '<p>Her iki değişiklik de yalnızca yeniden başlatmanın ardından tam olarak etkili '
              'olacaktır. Arayüz bunu açıkça gösteriyor.</p>\n'
              '\n'
              '<h3>Değer eşiği</h3>\n'
              '<p>Explorer değeri eşiği, cesetlerin özellikle değerli olarak vurgulandığı tahmini '
              'kredi değerini belirler. Değişiklik hemen kaydedilir ve ilgili Explorer ekranı '
              'güncellenir.</p>\n'
              '\n'
              '<h3>Otomatik gizle</h3>\n'
              '<p>"Değerli Bedenler" ve "BIO Buluntuları", Ayarlar sayfasında değil, sol kenar '
              'çubuğunda sabit bir şekilde bulunur.</p>\n'
              '<p>Anahtarlar kaydedilir ve keşif sırasında desteklenen küçük canlı ipucu '
              'pencerelerini kontrol eder. Değerli Bedenler için değer eşiği arayüz ayarlarında '
              'belirlenir.</p>\n'
              '\n'
              '<p>Cargo penceresi yalnızca aktif Journal-FID için doğrulanmış Cargo snapshotını kullanır. CMDR View içinde görüntülenen commander ve viewed_commander_id bu canlı pencereyi etkilemez. Ship için dolu / azami · boş gösterilir; CargoCapacity bilinmiyorsa hiçbir değer tahmin edilmez.</p>\n'
              '<p>“otomatik göster” altındaki “EDSM durum HUD’u” varsayılan olarak KAPALIDIR. Bir sisteme girdikten sonra Elite üzerinde yaklaşık 2,5 saniyelik kısa bir mesaj görünür. Aynı kalıştaki birden çok Location olayı yinelenen mesaj oluşturmaz; gerçek bir dönüşte yeniden sorgulanabilir.</p>\n<p>“EDSM: BİLİNİYOR” sistem için geçerli bir EDSM eşleşmesi demektir. “EDSM: BİLİNMİYOR” sistem eşleşmesi içermeyen geçerli bir EDSM yanıtıdır. “EDSM: YANIT YOK” ağ, HTTP, zaman aşımı hatası veya geçersiz yanıt demektir; asla doğrulanmış eşleşme yokluğu değildir. EDSM’de bilinmek Elite’te resmî keşif ile aynı değildir; ilk kâşif veya ilk bildiren adları vaat edilmez.</p>\n<p>Mesaj, navigasyon ve kargo HUD’larından bağımsız çalışır. Kalıcı HUD göstergeleri ve hızlı favori mesajları korunur. Sorgu arayüzü engellemez; terk edilmiş sistemlere gelen gecikmiş yanıtlar atılır.</p>\n\n'
              '<p>Yan çubuktaki “otomatik göster” anahtarları bağımsızdır: “Değerli gökcisimleri”, “BIO bulguları”, “GEO” ve “Kargo ambarı” ilgili canlı pencereleri denetler. “Kargo HUD” kaplamada kargoyu, “Navigasyon HUD” etkin gezegen navigasyonunu gösterir. Bu görüntüleme anahtarları kendileri çevrimiçi sorgu başlatmaz; HUD’lar Elite’in ön planda olmasını ve uygun verileri gerektirir.</p>\n<p>“EDSM durum HUD’u” ise “EDSM kullan”, gökcismi önbelleği ve API anahtarından bağımsız, kendine ait herkese açık bir EDSM ağ sorgusu gerektirir. Inara yüklemeleri ve Spansh istasyon bilgileri kendi hizmet anahtarlarına sahiptir; HUD anahtarları bunları etkinleştirmez.</p>\n\n<h3>Güncellemeler</h3>\n'
              '<p>Güncelleme grubu yüklü sürümü ve GitHub durumunu gösterir. Şimdi Kontrol Et, '
              'yeni planlanmış CMDRHelper sürümünü manuel olarak kontrol eder; Ayrıca, '
              'çalıştırmanın ardından gecikmeli bir otomatik kontrol gerçekleştirilir.</p>\n'
              '<p>Yeni bir sürüm mevcutsa CMDRHelper indirmeden ve yüklemeden önce soracaktır. '
              'Duyurulan bir veritabanı güncellemesi bu iletişim kutusunda ayrı olarak '
              'gösterilir.</p>\n'
              '<p>Mevcut kurulumlarda normalde şu yeterlidir: güncellemeyi yükle → CMDRHelper’ı başlat. BIO verileri, ziyaret geçmişi ve DSS üst verilerindeki gerekli geçmiş düzeltmeleri otomatik çalışır; veri yazan onarımlardan önce veritabanı yedeği alınır. Onarımlar sürümlüdür ve idempotenttir: başarılı revizyonlar her açılışta baştan sona yeniden çalıştırılmaz. Yeniden oluşturma için Elite günlükleri hâlâ mevcut, okunabilir ve tek bir commander’a kesin olarak atanabilir olmalıdır. Eksik kaynaklar uydurulmaz veya başarı sayılmaz; bekleyen onarımlar sonraki açılışta yeniden denenir. Normalde veritabanını silmek, elle betik çalıştırmak veya yeniden içe aktarmak gerekmez.</p>\n\n'
              '<h3>İndirme ilerlemesi</h3>\n'
              '<p>İndirme arka planda çalışır. Toplam boyut biliniyorsa CMDRHelper, dosya adını, '
              "alınan ve toplam MiB'yi, yüzdeyi, aktarım hızını ve tahmini kalan süreyi "
              'gösterir.</p>\n'
              '<p>Bilinen bir toplam boyut olmadan, ilerleme çubuğu meşgul modunda çalışır ve '
              'alınan veri miktarını ve belirlenebilirse hızı göstermeye devam eder. Kurulumdan '
              'önce indirilen ZIP kontrol edilir.</p>\n'
              '\n'
              '<h3>Güncellemeyi iptal et</h3>\n'
              '<p>“İndirmeyi iptal et” devam eden bir indirmeyi kontrollü bir şekilde sonlandırır. '
              'İptal edilen, eksik veya geçersiz bir indirme yüklenmeyecektir.</p>\n'
              '\n'
              "<h3>Windows'ta güncelleme</h3>\n"
              "<p>Windows'ta asıl güncelleme işlemi orijinal başlangıç \u200b\u200bkonsolundan "
              'bağımsız olarak devam eder. Bu nedenle konsolun kapatılması onu istemeden '
              'sonlandırmamalıdır.</p>\n'
              '<p>Dosya değişiklikleri başladıktan sonra bir hata oluşursa, mevcut geri alma '
              'yedeği önceki sürümü geri yüklemeye çalışır.</p>\n'
              '\n'
              '<h3>Güncellemeden sonra yeniden başlat</h3>\n'
              '<p>Başarılı bir kurulumun ardından güncelleyici, CMDRHelper uygulamasını öngörülen '
              'başlatma yolu üzerinden yeniden başlatır ve yeni işlemin kararlı çalışıp '
              'çalışmadığını kısaca denetler.</p>\n'
              '<p>Bir sürüm tek seferlik veri tabanı güncellemesi gerektiriyorsa günlük arşivi '
              'yeniden başlatmanın ardından yeniden değerlendirilecektir.</p>\n'
              '\n'
              '<h3>Birkaç komutan</h3>\n'
              '<p><b>Ayarlar seçimi = Kimin çevrimiçi erişimini düzenliyorum?</b></p>\n'
              '<p><b>Active Journal-FID = Kimlerin canlı yayın yapmasına izin verilir?</b></p>\n'
              '<p>Ne çevrimiçi hesap seçiminin ne de CMDR görünümünün, canlı yükleyiciyi salt '
              'görüntülenen bir komutana değiştirmesine izin verilmez.</p>\n'
              '\n'
              '<h3>Yardım</h3>\n'
              '<p>"? Yardım" sol kenar çubuğunda "otomatik gösteri"nin üzerinde bulunur ve o anda '
              'görünür olan ana menü alanının yardımını açar.</p>\n'
              '<p>“Ayarlar” alanındaki düğme bu ayar yardımını doğrudan açar.</p>\n'
              '\n'
              '<h3>İpucu</h3>\n'
              '<p>Yeniden yüklüyorsanız veya sorun yaşıyorsanız öncelikle şunları kontrol '
              'edin:</p>\n'
              '<ul>\n'
              '<li>doğru günlük klasörü ve tanınan komutan kimliği</li>\n'
              '<li>istenilen dil, tema, yazı tipi ve explorer değeri eşiği</li>\n'
              "<li>Doğru FID'ye çevrimiçi erişim</li>\n"
              '<li>Görüntü sorunları olması durumunda “Görüntüler” ana menüsündeki kaynak ve hedef '
              'klasörler</li>\n'
              '</ul>\n'
              '<p>Birden fazla komutan varsa her zaman görünür çevrimiçi erişim verilerinin hangi '
              'FID için geçerli olduğuna dikkat edin.</p>'),
    "planet_navigation": (
        'Gezegen navigasyonu',
        """<h2>Gezegen navigasyonu</h2>
<p>Gezegen navigatörü yalnızca bir gezegen veya ay üzerindeki belirli bir enlem/boylama uçmana yardımcı olur. Koordinatlarla bir hedef belirlersin ve oraya olan mesafeyi ve yönü görürsün.</p>
<p>Bu, yıldızlararası bir rota planlayıcısı değildir ve sistemler arası ya da sıçrama navigasyonunu üstlenmez. Gemini kendin kullanırsın.</p>

<h3>Navigatörü açma ve hedef girme</h3>
<p>Explorer’da “Gezegen navigasyonu” açıp “Manuel giriş …” seçin. Mevcut yüzey konumu olmadan da pencere açılabilir ve hedef önceden girilebilir.</p>
<ul>
<li><b>Gök cismi:</b> Listeden hedef gezegeni veya ayı seç ya da önceden algılanmış gök cismini kullan. Adı henüz listede yoksa gök cisminin adını kendin de girebilirsin. Emin değilsen sistem adı dâhil tam adı kullan.</li>
<li><b>Enlem:</b> Hedef enlemini −90° ile +90° arasında gir.</li>
<li><b>Boylam:</b> Hedef boylamını −180° ile +180° arasında gir. Her iki koordinatın da işaretine dikkat et.</li>
<li><b>Hedef adı:</b> Hedefini daha kolay tanımak için isteğe bağlı bir ad girebilirsin.</li>
</ul>
<p>“Hedef belirle” ile girişini onaylarsın. BodyID ve SystemAddress gibi teknik kimlikleri girmen gerekmez; bunlar normal kullanıcı girişleri değildir.</p>

<h3>Pusula ne zaman başlar?</h3>
<p>Bir hedef belirlendiğinde ve Elite ilgili gök cismi için geçerli gezegensel konum verileri sağladığında navigasyon otomatik olarak etkinleşir. Ayrı bir başlat düğmesine basman gerekmez.</p>
<p>Bu veriler henüz yoksa veya başka bir gök cismine aitse navigatör “Gezegen koordinatları bekleniyor …” mesajıyla bekler. Bu veriler gelmeden önce de bir hedef girebilirsin.</p>

<p>Etkin navigasyon için Elite’in hedef cisme ait geçerli koordinatları, cisim adı, yönü ve gezegen yarıçapı gerekir. İniş zorunlu değildir: uygun veriler yaklaşırken gelebilir. Geçerli konum yoksa veya başka cisimdeyseniz gezgin konum uydurmadan bekler.</p>

<h3>Mevcut konumu kaydetme</h3>
<p>“★ Mevcut konumu kaydet”, girilen navigasyon hedefini değil, doğrulanmış mevcut konumunuzu kaydeder. Geçerli Elite konumu, tanımlanmış komutan ve bilinen sistem gerekir. Eksikler varsa işlem devre dışıdır veya mesaj görünür.</p>
<p>Açılışta sistem, cisim ve koordinatlar sabitlenir. Favori penceresinde ad, kategori ve not düzenlenebilir, resim eklenebilir. Yalnızca “Kaydet” bu komutan için yerel kayıt oluşturur; iptal etmek hiçbir şey kaydetmez. Sonraki hareketler sabitlenen konumu değiştirmez.</p>

<h3>Kayıtlı konumları kullanma</h3>
<p>Explorer’da “★ Favoriler” açın. Kayıtlı bir yüzey yeri ve “◎ Koordinatlara git” seçerek cismi, koordinatları ve adı hedef olarak alın. Önceki hedefin yerini alır; başka cisimde gezgin uygun konum verilerini bekler.</p>
<p>“Düzenle” ad, kategori ve notu değiştirir. “Sil” onaydan sonra favoriyi kaldırır, Elite verilerini silmez. Favoriler yeniden başlatmada korunur ve komutana göre ayrılır; mevcut navigasyon hedefi yalnızca oturum boyunca geçerlidir.</p>

<h3>Gezegen küresi: 380 km’den fazla</h3>
<p>Hedef mesafesi 380 km’den büyük olduğunda navigatör gezegen küresini gösterir.</p>
<ul>
<li><b>Beyaz daire</b> kendi konumunu işaretler.</li>
<li><b>Küçük hedef noktası</b>, hedef gezegenin görünen tarafındaysa turuncudur.</li>
<li>Hedef görünmeyen arka taraftaysa hedef noktası kırmızı gösterilir.</li>
<li>Konumun gösterimde sabit kalır. Gezegen ve hedef, konumuna ve yönelimine göre gösterilir.</li>
</ul>
<p>Beyaz ok ileriye bakar; sarı ok hedefin göreli yönünü gösterir. Küre şematik bir yön bulma yardımcısıdır, coğrafi açıdan kesin bir arazi görünümü değildir. Kırmızı nokta kürenin arka tarafı demektir; otomatik olarak “geminin arkasında” anlamına gelmez.</p>

<h3>Perspektif ızgarası: 380 km dâhil olmak üzere</h3>
<p>Hedef mesafesi 380 km veya daha az olduğunda görünüm otomatik olarak eğimli bir perspektif ızgarasına geçer. Mesafe yeniden 380 km’nin üzerine çıkarsa küre tekrar görünür.</p>
<p>Enine çizgiler <b>50 km aralıklı bir mesafe ızgarası</b> oluşturur. Hedef noktası, mesafeye ve göreli yöne göre ızgaranın içine çizilir. Perspektif, yaklaşmanın devamında sana yardımcı olur; eğim nedeniyle aralıklar arkaya doğru daha sık görünür. İzleyeceğin gerçek rota için ayrıca hedef rotasına ve göreli yöne dikkat et.</p>

<h3>Navigasyon değerlerini doğru okuma</h3>
<ul>
<li><b>Hedef mesafesi:</b> Büyük gösterge, varsayımsal gezegen yüzeyi boyunca hedefe kalan mesafeyi gösterir.</li>
<li><b>Hedef koordinatları:</b> Hedef için girilen koordinat çifti; önce enlem, ardından boylam. Sen hareket ederken değişmeden kalır.</li>
<li><b>Güncel koordinatlar:</b> Elite’ten son doğrulanan koordinat çiftin; yine enlem / boylam.</li>
<li><b>Yüzey boyunca mesafe:</b> Hedef mesafesiyle aynı yüzey mesafesidir; ayrıntı görünümünde daha hassas yuvarlanmış olabilir. İkinci bir güzergâh veya havadan geçen doğrudan bir uzaysal mesafe değildir.</li>
<li><b>Kerteriz:</b> Güncel konumundan hedefe olan mutlak yön, pusula açısı olarak: 000° kuzey, 090° doğu, 180° güney ve 270° batıdır.</li>
<li><b>Baş yönü:</b> Elite’in bildirdiği güncel yönelimin. Şu anda nereye baktığını gösterir ve henüz kerterizle aynı olmak zorunda değildir.</li>
<li><b>Göreli yön:</b> Yönelimin ile kerteriz arasındaki fark; örneğin “23° sağa”, “10° sola” veya “Düz ileri”. 180° olduğunda hedef arkandadır.</li>
<li><b>Hedef rotası:</b> Elite HUD’ında dönebileceğin mutlak bir rota olarak vurgulanan kerteriz. Ek bir dönüş açısı değildir.</li>
</ul>
<p>Örnek: Baş yönün 051° ve hedef rotan 074° ise 23° sağa dönerek Elite pusulanın yaklaşık 074° göstermesini sağla. Uçuşa devam ederken kerteriz ve hedef rotası değişebilir; güncellenen değerleri izle.</p>
<p>Hedefle aynı konumda, bir kutupta veya gezegenin tam karşı noktasında yön tanımsız olabilir. Bu durumda navigatör uydurma bir rota yerine ilgili uyarıyı gösterir.</p>

<h3>Pencere boyutu</h3>
<p>Navigatör penceresinin boyutu serbestçe değiştirilebilir. Küre veya perspektif ızgarası, kullanılabilir alana orantılı olarak uyum sağlar. Minimum boyut, ayrıntılı değerlerin okunabilirliğini korur; küre yuvarlak kalır. Pencerenin konumu ve boyutu kaydedilir.</p>

<h3>Navigasyon HUD’ını açma</h3>
<p>Ana pencerenin solunda <b>otomatik göster → Navigasyon HUD</b> altındaki kutuyu işaretle. Geçerli gezegen navigasyonu olduğunda HUD, ön plandaki görünür Elite penceresinin doğrudan üzerinde belirir.</p>
<p>Üç satır gösterir:</p>
<ul>
<li>göreli yön</li>
<li>hedef rotası</li>
<li>mesafe</li>
</ul>
<p>HUD saydamdır, tıklamaları geçirir ve odağı almaz: oyunu opak bir alanla örtmez, fare tıklamalarını yakalamaz ve otomatik olarak belirdiğinde Elite’in giriş odağını elinden almaz.</p>
<p>Geçerli navigasyon veya kesin bir yön olmadığında otomatik olarak görünmez olur. Elite simge durumuna küçültüldüğünde veya ön planda olmadığında da gizlenir. Kenar çubuğundaki kutu yine de işaretli kalabilir; bu, o anki görünürlüğü değil, otomatik gösterim tercihini belirtir.</p>
<p>HUD yalnızca ek bir göstergedir. Normal navigatör ondan bağımsız çalışır; HUD kapalı veya kullanılamaz olduğunda da çalışmaya devam eder.</p>

<h3>Yeni bir hedef belirleme</h3>
<p>Aynı gök cisminde istediğin zaman “Manuel giriş …” seçeneğini yeniden açıp farklı koordinatlar belirleyebilirsin. Yeni hedef, önceki navigasyon hedefinin yerini alır. Uygun konum verileriyle pusula hemen güncellenir.</p>
<p>“Navigasyonu sonlandır” ile güncel hedefi kaldırırsın. Başka bir yaklaşma için yeni bir hedef belirlemen yeterlidir.</p>

<p>Pencereyi kapatmak hedefi kaldırmaz. Açık navigasyon HUD’ı devam edebilir; “Navigasyonu sonlandır” hedefi kaldırır. Doğru cisimden ayrılmak veya konum verilerini kaybetmek navigasyonu bekletir ve navigasyon HUD’ını gizler.</p>

<h3>Verilerin güncelliği ve sınırlar</h3>
<p>Navigasyon, Elite’in sağladığı durum verilerine dayanır. Güncellemeler oyun durumuna bağlı olarak gecikmeli gelebilir. Navigatördeki yaş göstergesi, son doğrulanan durum mesajından bu yana ne kadar zaman geçtiğini gösterir.</p>
<p>Yüzey mesafesi, varsayımsal bir küre üzerindeki en kısa yayı ifade eder. Bir arazi veya yol güzergâhı değildir. Navigatör, güzergâh üzerindeki engelleri veya arazi yüksekliklerini bilmez; uçuş yüksekliği, güvenli hız ve engellerden kaçınma senin sorumluluğunda kalır.</p>

<p>Mevcut konum Status.json’dan gelir; günlük, cisim ve sistem ilişkilerini tamamlar. Pencere ve etkin navigasyon HUD’ı gerektiğinde güncellemeleri sürdürür. Görünüm mevcut Elite verilerine bağlıdır; metre cinsinden kesinlik garantisi vermez.</p>

<h3>İpucu</h3>
<p>Yaklaşmadan önce gök cisminin adını ve hedef koordinatlarının işaretlerini kontrol et. Ardından Elite pusulasında hedef rotasına yönel ve göreli yönü ve mesafeyi izle. Navigatör bekliyorsa Elite’in hedef gök cismi için gezegen koordinatları sağlamaya başlayıp başlamadığını kontrol et.</p>""",
    ),
}

DIALOG_TITLE = 'Yardım – {area}'
CLOSE_LABEL = 'Kapat'


# Database update guidance; help itself remains version independent.
HELP_TOPICS["overview"] = (HELP_TOPICS["overview"][0], HELP_TOPICS["overview"][1] + '<h3>Veritabanı güncellemesi gerekli</h3><p>Veritabanı güncellemesi, yıldızlar, gezegenler ve uydular arasındaki eski kayıtlı ilişkileri düzeltir. Günlükler yalnızca okunur. Önce Elite Dangerous’ı kapat ve mümkünse geçmiş günlükleri hazır bulundur. CMDRHelper veritabanının tamamı önceden yedeklenir; hata durumunda değişiklikler geri alınır ve gerekirse yedek geri yüklenir. Yedek, güvenlik kopyası olarak saklanır. İptal ile güncellemeyi erteleyebilirsin.</p>')

HELP_TOPICS["settings"] = (HELP_TOPICS["settings"][0], HELP_TOPICS["settings"][1] + '<h3>Tanılama ve günlükler</h3><p>Ayarlar → Tanılama ve günlükler bölümünden günlük dosyasını açabilir veya tanılama paketi oluşturabilirsiniz. Günlükler, kurulum klasöründeki logs/ altındadır (cmdrhelper.log ve en fazla dört eski dosya). ZIP; temizlenmiş teknik günlükler, system_info.json ve diagnose_summary.txt içerir; Journal dosyaları, veritabanı, FID/komutan verileri, kimlik bilgileri, favoriler veya resimler içermez. Kişisel yollar yer tutucularla değiştirilir. Gizlilik filtresinden önceki eski günlüklerin içeriği atlanır. ZIP dosyasının kaydedileceği yeri seçin ve gerekirse destek ekibiyle paylaşın; dosya hiçbir zaman otomatik gönderilmez.</p>')

HELP_TOPICS["trade"] = (
    'Ticaret',
    """<h2>Ticaret</h2>
<h3>Ticarete genel bakış</h3>
<p>“Satış” malınızı satın alan pazarları bulur. “Satın al” satın almak istediğiniz belirli bir malı bulur. “Öneriler”, mevcut istasyonunuzda ne alıp koşullarınıza uygun olarak başka yerde kârla satabileceğinizi gösterir.</p>

<h3>Pazar verileri ve yaşı</h3>
<p>Satış ve alış, kaydedilmiş geçerli kendi pazar gözlemlerinizi Spansh üzerinden alınan topluluk pazar verileriyle otomatik olarak birleştirir. Önerilerde alış yalnızca mevcut, bizzat gözlemlediğiniz Elite pazarından yapılır; hedefler normalde kendi gözlemlerinizden ve Spansh'ten gelir. Topluluk sonuçları yalnızca geçici olarak bellekte tutulur.</p>
<p>Kendi gözlemleriniz dahil tüm pazar verileri belirli bir anı yansıtır. Fiyat, arz ve talep siz varana kadar değişebilir. Veri yaşını kontrol edin: bulunabilirlik ve kâr garanti edilmez.</p>
<p>Aynı pazar hem kendi gözleminizden hem de topluluktan biliniyorsa CMDRHelper daha yeni geçerli pazar kaydını kullanır.</p>

<h3>Mal seçme</h3>
<p>“Mal” alanına tıklayın, görünen ad, İngilizce ad veya sembolle arayın ve malı seçin. Almanca adlar bakımı yapılan Almanca mal kataloğundan gelir. Kullanılabilir çeviri yoksa İngilizce katalog adı veya okunabilir bir ad gösterilir.</p>

<h3>Satış</h3>
<p>Arama hem geçerli kendi pazar gözlemlerinizi hem de topluluk pazar verilerini kullanır. Malı, “Miktar (t)” ve filtreleri seçin; ardından “En iyi satışı bul” düğmesine basın. Girilen miktarı karşılayacak talebi olan alım teklifleri aranır. “Fiyat / t”, satışta alacağınız fiyattır. “Olası gelir” = fiyat × girilen miktar. Başlangıç noktası komutanın mevcut sistemidir. Varsayılan olarak en yüksek satış fiyatı önce gelir.</p>

<h3>Satın al</h3>
<p>Arama hem geçerli kendi pazar gözlemlerinizi hem de topluluk pazar verilerini kullanır. Malı, istenen miktarı ve filtreleri seçin; ardından “En ucuz alımı bul” düğmesine basın. Bildirilen “Arz” miktarın tamamına yetmelidir. “Fiyat / t” alış fiyatınızdır; “Toplam maliyet” = fiyat × istenen miktar. Başlangıç noktası mevcut sisteminizdir. Varsayılan olarak en düşük alış fiyatı önce gelir. Bu, belirli bir mal aramasıdır; kâr önerisi değildir.</p>

<h3>Filtreler ve sonuç tabloları</h3>
<ul>
<li><b>Yarıçap (ly):</b> başlangıç sisteminden hedef sisteme azami uzaklık.</li>
<li><b>Piyasa verisinin azami yaşı / Hedef verisinin yaşı:</b> pazar verisinin izin verilen azami yaşı; önerilerde hedef için geçerlidir.</li>
<li><b>Pist boyutu:</b> gereken asgari iniş alanı boyutu, istasyonun tam boyutu değil. “Orta” büyük alanları da kabul eder; “Tümü” boyutu sınırlamaz.</li>
<li><b>Fleet Carrier gemilerini dahil et:</b> taşıyıcıları dahil edin veya dışlayın.</li>
<li><b>Azami varış mesafesi (Ls):</b> varış yıldızından istasyona azami uzaklık. Boş alan sınırsız demektir. Yaklaşma uzaklığı bilinmeyen bir hedef bu filtreyi karşılayamaz.</li>
</ul>
<p>Kendi sonuçlarınıza ve topluluk sonuçlarına veri yaşı, yarıçap, iniş pisti, carrier ve varış mesafesi için aynı filtreler uygulanır. Eksik bilgiler tahmin edilmez. Sistem uzaklığı bilinmeyen veya etkin bir kısıtı karşıladığı doğrulanamayan hedefler dışlanır. Kendi pazarlarınızda özellikle iniş alanı ve yaklaşma verilerinin eksikliği önemlidir; taşıyıcılar dışlanıyorsa hedefin taşıyıcı olmadığı bilinmelidir.</p>
<p>Sıralamak için sütun başlıklarına tıklayın: sayılar sayısal değere, veri yaşı gerçek yaşa, iniş alanları boyut sınıfına göre sıralanır. Satış ve alış en fazla 100 sonuç gösterir. “Daha fazla sonuç var. Filtreleri daraltın.” sınırlı bir aramayı belirtir. Mevcut kendi sonuçlarınız ve topluluk sonuçları, liste sınırlandırılmadan önce birlikte fiyata göre sıralanır. Topluluk hizmetinin arama sınırları nedeniyle bunların genel olarak en iyi teklifler olduğu garanti edilmez.</p>
<p>Satış veya alış sırasında topluluk araması başarısız olursa uygun kendi sonuçlarınız kullanılabilir kalır. CMDRHelper bu durumda aramayı eksik olarak işaretler: daha iyi topluluk teklifleri eksik olabilir.</p>

<h3>Kendi pazar verileriniz</h3>
<p>Kenetlenmiş durumdayken Elite'teki mal pazarını açın. CMDRHelper çalışırken, mevcut istasyonla bağlantı güvenle kurulabiliyorsa pazar otomatik kaydedilir. Elle içe aktarma gerekmez. Pazarı yeniden açmak anlık kaydı günceller.</p>
<p>Her pazar ve komutan için 24 saatten yeni tek bir güncel kayıt tutulur. Eski kayıtlar otomatik kaldırılır; kalıcı fiyat geçmişi oluşturulmaz. Geçerli gözlemler Helper yeniden başlatıldığında korunur. “Kendi pazar verilerin: X istasyon”, etkin komutanın geçerli kendi istasyon pazarlarını sayar. Seçilen azami pazar verisi yaşı, kendi sonuçlarınız için de ayrıca geçerlidir.</p>
<ul>
<li><b>✓ Okundu:</b> Öneriler bölümünde mevcut istasyonun geçerli bir kişisel pazar kaydı vardır.</li>
<li><b>Mal pazarını aç:</b> Bu istasyon için kullanılabilir kişisel kayıt yoktur.</li>
<li><b>Pazar verisi eski:</b> Daha önce gösterilen kayıt artık geçerli değildir. Pazarı yeniden açın.</li>
</ul>
<p>Eski kayıt görünüm açılmadan önce kaldırılmışsa yine “Mal pazarını aç” görünür. Uçuşta önceki istasyon için olumlu durum gösterilmez.</p>

<h3>Öneriler</h3>
<p>Mevcut istasyon, o istasyonun geçerli kişisel kaydı ve boş kargo alanı güvenilir biçimde bilinen mevcut gemi gerekir. Dolu alan düşülür. Boş alan bilinmiyorsa veya kargo doluysa yeni arama başlatılamaz; miktar uydurulmaz. Kalkıştan sonra eski konum temel alınarak yeni hesap yapılmaz.</p>
<p>“Asgari kâr” değerini ayarlayın: 10 %, en az %10 marj sağlayan olanakları dikkate alır. Yerel olarak sunulan mallar aranır. Alış istasyonu hedef olarak kullanılmaz. Aynı hedef istasyon için (aynı MarketID) daha yeni geçerli kayıt kullanılır. Her mal için filtrelerinize uyan, kontrol edilmiş en yüksek “Olası kâr” değerli hedef gösterilir; bu mutlaka galaksinin en iyi hedefi değildir. Tablo en yüksek olası kârla başlar; “Kaynak”, “Elite yerel” veya “Spansh” gösterir, “Hedef verisinin yaşı” ise hedef verisinin yaşını belirtir.</p>

<h3>Yalnızca kendi pazar verilerim</h3>
<p>Bu onay kutusu yalnızca Öneriler altında bulunur. Satış ve alış otomatik olarak her iki kaynağı kullanır. Bu kutu önerileri, bizzat gözlemlediğiniz geçerli hedef pazarlarla sınırlar. Topluluk sorgusu yapılmaz; Spansh gerekmez. Yarıçap, hedef verisinin ek yaş sınırı, asgari kâr, iniş alanı, taşıyıcı ve yaklaşma filtreleri geçerliliğini korur ve mevcut bilgilerle doğrulanabilmelidir. Topluluk aramasını bilerek atlamak hata değildir ve aramayı eksik yapmaz. Böylece önceden ziyaret ettiğiniz istasyonlar arasında hızla arama yapabilirsiniz.</p>

<h3>Olası kâr ve miktar</h3>
<ul>
<li><b>Kâr / t:</b> hedefteki satış fiyatı − buradaki alış fiyatı. “Kâr %” = ton başına kâr ÷ alış fiyatı × 100.</li>
<li><b>Miktar (t):</b> boş kargo alanı, alış pazarının arzı ve hedefin talebi arasındaki en küçük miktar.</li>
<li><b>Olası kâr:</b> ton başına kâr × mümkün miktar; bilinen pazar kayıtlarına dayanan bir tahmin.</li>
</ul>
<p>Örnek: 280 t boş alan, 150 t arz, 20.000 t talep → mümkün miktar 150 t. Her mal tüm boş kargo alanını otomatik olarak dolduramaz.</p>

<h3>İşaretlenen ticaret uçuşu</h3>
<p>Onay kutusuyla yalnızca bir öneriyi hatırlanacak olarak işaretleyin. Başka bir seçim öncekini değiştirir. Ayrı not alanı malı, hedef istasyonu, hedef sistemi ve seçim anındaki “Olası kâr” değerini gösterir. Bu bir hatırlatma notudur; sürekli yeniden hesaplanan öneri değildir.</p>
<p>Not; satın alma, kargo değişikliği, kalkış, sistem değişikliği, kenetlenme ve pazar açılışında kalır. “Kaldır” ile veya işaret kaldırıldığında, yeni bir öneri araması gerçekten başladığında, komutan değiştiğinde ve Helper kapandığında silinir. Yeniden başlatmada korunmaz.</p>
<p>“Sistemi kopyala”, panoya yalnızca hedef sistemin adını kopyalar. Hedef istasyon notta görünmeye devam eder; rota oluşturulmaz.</p>

<h3>Arama, ilerleme ve iptal</h3>
<p>Aramaları elle başlatın. Öneriler birden fazla malı kontrol eder ve daha uzun sürebilir. Arama kapsamı belirlendikten sonra ilerleme çubuğu ve “Mallar kontrol ediliyor: x / y …” gerçekten kontrol edilen malları gösterir. “İptal” yalnızca iptal edilebilir arama sırasında kullanılabilir; sürmekte olan ağ yanıtı iptali geciktirebilir. Sekme değiştirmek aramayı iptal eder; satış/alışın ortak filtreleri korunur.</p>
<p>Bazı topluluk sorguları başarısız olursa veya arama sınırlarına ulaşılırsa geçerli, kontrol edilmiş öneriler görünür kalabilir. Eksik arama, sonuçların kontrol edilmiş veriler için geçerli olduğu ancak tüm malların veya hedeflerin tamamen incelenmediği anlamına gelir. Mesajı okuyun, sınırlara ulaşıldığında filtreleri daraltın veya daha sonra yeniden deneyin. Elle iptal, mevcut sonuç listesini kaldırır.</p>

<h3>Sorunlarda tanılama</h3>
<p>“Tanı bilgilerini kopyala”, sorun incelemesi için son biten öneri aramasının teknik bilgilerini kopyalar. Metin komutan/FID verisi veya pazar fiyatı içermez. Tanılama bellekte kalır; kalıcı tanılama dosyası oluşturulmaz ve hiçbir şey otomatik gönderilmez. Gerektiğinde kopyalanan metni desteğe kendiniz iletin.</p>

<h3>Bir ticaret uçuşu nasıl yapılır?</h3>
<ol>
<li>Bir istasyona kenetlenin ve Elite'teki mal pazarını açın.</li>
<li>“Ticaret” → “Öneriler” bölümünü açıp “Okundu” durumunu kontrol edin.</li>
<li>Asgari kâr ve filtreleri ayarlayıp “Öneri ara” seçin.</li>
<li>Hatırlamak istediğiniz öneriyi işaretleyin ve malı Elite'te satın alın.</li>
<li>Gerekirse “Sistemi kopyala” kullanıp hedefe uçun; istasyon notta görünür kalır.</li>
<li>Elite'te satın. Yeni pazarın kişisel verilerini de güncellemek için oradaki pazarı açın.</li>
</ol>""",
)
