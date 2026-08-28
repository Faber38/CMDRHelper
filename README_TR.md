# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) | [🇬🇧 English](README.md) | [🇫🇷 Français](README_FR.md) | [🇮🇹 Italiano](README_IT.md) | [🇳🇴 Norsk](README_NO.md) | [🇸🇪 Svenska](README_SV.md) | [🇫🇮 Suomi](README_FI.md) | [🇵🇱 Polski](README_PL.md) | [🇳🇱 Nederlands](README_NL.md) | [🇪🇸 Español](README_ES.md) | [🇹🇷 Türkçe](README_TR.md) | [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper](/docs/cmdrh.png)

**Elite Dangerous için kişisel yardımcı — keşif, sistem analizi ve Commander verileri**

Proje aktif olarak geliştirilmektedir.

## Özellikler

### Elite Dangerous Journal dosyaları

CMDRHelper, Elite Dangerous yerel Journal dosyalarını okuyarak yıldız sistemlerini, yıldızları, gezegenleri, uyduları, Belt Cluster'ları, taramaları, haritalamaları ve biyolojik/jeolojik sinyalleri işler.

### Görevler

CMDRHelper Journal görev olaylarını analiz eder ve aktif görevleri düzenli biçimde gösterir. NPC mesajları (`ReceiveText`) ile gelen teklifler de algılanabilir.

### Sistem ve Explorer görünümü

Bilinen gök cisimleri tür, mesafe, tarama/haritalama durumu, BIO/GEO sinyalleri ve değerlerle grafik olarak gösterilir.

### Gök cismi ayrıntıları

Bir gök cismine tıklamak mevcut fiziksel verileri, malzemeleri, BIO/GEO sinyallerini ve keşif değerlerini gösteren ayrıntılı görünümü açar.

## Sürüm 0.9.9

### Çok dilli arayüz ve çeviri kontrolü

- CMDRHelper artık **12 arayüz dilini** destekler: Almanca, İngilizce, Fransızca, İtalyanca, Norveççe (Bokmål), İsveççe, Fince, Lehçe, Felemenkçe, İspanyolca, Türkçe ve Yunanca.
- dil Ayarlar bölümünden seçilip kaydedilebilir.
- fallback: **seçilen dil → İngilizce → Almanca → çeviri anahtarı**.
- `tools/check_i18n.py`, `tr("...")` anahtarlarını, eksik/fazla anahtarları, tekrarları ve yer tutucuları kontrol eder.
- Linux'ta kontrol `start.sh` üzerinden otomatik çalışır ve uyarılar programın başlamasını engellemez.


### Weitere / Additional 0.9.9 improvements

Version 0.9.9 also contains the Explorer, system-map, BIO valuation, mission, screenshot, EDSM, usability and stability improvements documented in the German and English main README files. Those two files remain the most detailed release documentation.

## Technical requirements

`PySide6>=6.7,<7`, `numpy`, `Pillow>=10.0`

Linux:
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Windows: `install.bat`, then `start.bat`.

## License

CMDRHelper is free software released under **GNU General Public License Version 3 (GPL-3.0)**.

Copyright © 2026 **Holger Mangold (Faber38)**.

CMDRHelper is an independent community/hobby project and is not an official Frontier Developments product. **Elite Dangerous** and related names and content belong to their respective rights holders.

