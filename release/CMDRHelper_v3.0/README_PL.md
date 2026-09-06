# CMDRHelper V3 (3.0)

[🇩🇪 Deutsch](README_DE.md) \| [🇬🇧 English](README.md) \| [🇫🇷
Français](README_FR.md) \| [🇮🇹 Italiano](README_IT.md) \| [🇳🇴
Norsk](README_NO.md) \| [🇸🇪 Svenska](README_SV.md) \| [🇫🇮
Suomi](README_FI.md) \| [🇵🇱 Polski](README_PL.md) \| [🇳🇱
Nederlands](README_NL.md) \| [🇪🇸 Español](README_ES.md) \| [🇹🇷
Türkçe](README_TR.md) \| [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper -- Twój drugi pilot w Elite Dangerous](cmdrhelper/assets/readme/cmdrhelper_readme_pl.png)

**Osobisty towarzysz Elite Dangerous – eksploracja, nawigacja i dane dowódcy w jednym miejscu**

CMDRHelper to samodzielna aplikacja komputerowa analizująca lokalne dzienniki Elite Dangerous i korzystająca z planetarnych danych pozycji z `Status.json`. Pomaga rozpoznawać interesujące ciała niebieskie, wracać do zapisanych miejsc oraz przeglądać podróże i odkrycia. Dane osobiste pozostają po ponownym uruchomieniu i są rozdzielone według dowódców.

## Explorer

Explorer przedstawia bieżący system w trzech widokach:

- **Mapa systemu:** graficzne przedstawienie znanych gwiazd, planet i księżyców. Kliknięcie ciała niebieskiego otwiera szczegóły. „Pokaż wszystko” otwiera przegląd systemu.
- **Lista wartości:** wartości skanowania i kartografii znanych ciał, już osiągnięta wartość i możliwy potencjał całkowity. Oznaczenia pomagają rozpoznać kandydatów do terraformowania, możliwe pierwsze odkrycia i pierwsze mapowania.
- **BIO / GEO / WYDOBYCIE:** sygnały biologiczne i geologiczne, planetarne miejsca wydobycia i potwierdzone osobiste znaleziska.

Analizy rozróżniają zgłoszone sygnały i rzeczywiste osobiste znaleziska. **BIO ×N** oznacza zgłoszoną liczbę sygnałów, a nie potwierdzenie w pełni przeanalizowanych gatunków. **WYDOBYCIE ×N** liczy planetarne miejsca wydobycia bez ujawniania ich poszczególnych surowców. Osobiście wydobyte towary, materiały poboczne zebrane podczas wydobycia i ogólny skład materiałowy ciała pozostają rozdzielone.

Explorer pokazuje także szacunkowe wartości BIO, postęp osobistych analiz oraz niesprzedane dane kartograficzne i BIO. Wartości opierają się na dostępnych informacjach dziennika i ciał; brakujące dane nie są przedstawiane jako osobiste odkrycia. Dodatkowe dane EDSM to informacje zewnętrzne, które należy odróżniać od własnych znalezisk.

Szczegóły ciał obejmują dostępne właściwości fizyczne, atmosferę, pierścienie, materiały i informacje o odkryciach. Wizualizacje używają odpowiednich tekstur, a dla wybranych szczególnych obiektów astronomicznych także animacji. Sekcja Cargo pokazuje znany ładunek i pojemność obecnie używanego statku lub SRV; w przypadku Rhino ładunek i osobiste znaleziska wydobywcze pozostają odrębnymi danymi.

U góry Explorera znajdują się **★ Ulubione | Nawigacja planetarna | Pokaż wszystko**. Ulubione i nawigacja planetarna otwierają własne okna; trzy widoki Explorera pozostają dostępne.

## Nawigacja planetarna

Nawigator planetarny służy wyłącznie do dolotu do określonej **szerokości/długości geograficznej na planecie lub księżycu**. Podróżom między systemami gwiezdnymi służy osobny planer tras.

### Wpisz cel i leć

Wybierz docelowe ciało lub użyj bieżącego, rozpoznawanego automatycznie, gdy to możliwe. Wpisz szerokość i długość geograficzną oraz opcjonalną nazwę celu. Nie musisz podawać technicznych danych, takich jak BodyID czy SystemAddress. **0,0** także jest prawidłową współrzędną.

Gdy Elite dostarczy prawidłowe planetarne dane pozycji dla odpowiedniego ciała, kompas aktywuje się automatycznie. Bez pasujących danych nawigator pokazuje stan oczekiwania. W każdej chwili możesz ustawić nowy cel współrzędnych na tym samym ciele; zastępuje on poprzedni.

### Widok podczas dolotu

| Odległość do celu | Widok |
| --- | --- |
| **Więcej niż 380 km** | Kula planety z własną pozycją jako białym okręgiem i celem jako małą kropką. Cel jest pomarańczowy po widocznej stronie, a czerwony po niewidocznej stronie tylnej. Pozycja gracza pozostaje stała na ekranie; planeta i cel są przedstawiane względem niej. |
| **Do 380 km włącznie** | Automatyczne przejście na nachyloną siatkę perspektywiczną z **odstępami odległości 50 km** i zaznaczoną pozycją celu do dalszego dolotu. |

Rozmiar okna nawigatora można swobodnie zmieniać. Kula lub siatka perspektywiczna dostosowuje się proporcjonalnie do miejsca; szczegółowe wartości pozostają czytelne.

### Znaczenie wartości nawigacyjnych

- **Współrzędne celu:** zapisana szerokość i długość geograficzna celu.
- **Aktualne współrzędne:** ostatnia prawidłowa własna pozycja planetarna.
- **Odległość do celu / Odległość po powierzchni:** obliczona odległość do celu po powierzchni kuli; duży odczyt i wartość szczegółowa pokazują tę samą odległość z różnym zaokrągleniem.
- **Namiar:** bezwzględny kierunek od bieżącej pozycji do celu.
- **Heading:** bieżące własne ustawienie zgłoszone przez Elite.
- **Kierunek względny:** różnica między headingiem a namiarem, np. „23° w prawo”, „w lewo” lub „prosto”.
- **Kurs do celu:** bezwzględny kurs, na który możesz skręcić według HUD-u Elite. Odpowiada namiarowi i nie jest dodatkowym względnym kątem skrętu.

Przykład: **Heading 051° → Kurs do celu 074° = 23° w prawo**.

Nawigacja zależy od danych stanu gry; aktualizacje mogą przychodzić z opóźnieniem zależnie od jej stanu. Odległość po powierzchni nie jest trasą terenową ani drogową. Przeszkody i wysokości terenu na trasie nie są uwzględniane.

## HUD nawigacyjny

Po lewej pod **pokazuj automatycznie → HUD nawigacji** możesz włączyć opcjonalny dodatkowy widok bezpośrednio nad Elite. Przy prawidłowej nawigacji planetarnej pokazuje:

- kierunek względny,
- bezwzględny kurs do celu,
- odległość.

HUD jest przezroczysty, przepuszcza kliknięcia i nie przejmuje fokusu: nie odbiera grze kliknięć myszy ani fokusu wprowadzania. Bez prawidłowej nawigacji staje się automatycznie niewidoczny; pole na pasku bocznym może pozostać zaznaczone. Zwykły nawigator działa niezależnie od HUD-u.

HUD został przetestowany w grze pod **Linux/X11** oraz **Windows 11 z Elite**. W Windows dopasowanie wielu monitorów opiera się na ich geometrii i pozycji okna Elite, a nie zgodności nazw monitorów.

## Ulubione

**Explorer → ★ Ulubione** otwiera osobne okno używane ponownie. Ulubione należą do **aktywnego dowódcy**. Zmiana dowódcy odświeża widok; wybór dowódców w kronice nie rozszerza listy ulubionych.

### Zapisywanie trzech typów

Górny wiersz działań oferuje:

| Działanie | Zapisany ulubiony |
| --- | --- |
| **★ Zapisz bieżący system** | Bieżący system bez współrzędnych powierzchniowych. |
| **★ Zapisz planetę / księżyc** | Wybrana znana planeta lub księżyc bieżącego systemu bez współrzędnych powierzchniowych. |
| **★ Zapisz bieżącą pozycję** | Miejsce na powierzchni z bieżącym systemem, ciałem, szerokością i długością geograficzną. |

Przycisk pozycji pozostaje zawsze widoczny i jest dostępny tylko przy prawidłowych bieżących planetarnych danych pozycji i aktywnym dowódcy. **Kliknięcie utrwala dowódcę, system, ciało i współrzędne przed otwarciem okna edycji.** Późniejsze ruchy w grze nie zmieniają tej pozycji. Ten sam sposób zapisu jest dostępny w nawigatorze planetarnym. Znane wewnętrzne identyfikatory są przejmowane automatycznie; współrzędne nie są wymyślane.

Nadaj nazwę i dokładnie jedną kategorię: **Bio, Geo, Wydobycie, Widok, Lądowisko, Ciekawe lub Inne**. Notatka i obraz są opcjonalne.

### Wyszukiwanie, oglądanie i edycja

Przewijana lista, posortowana alfabetycznie według nazw, pokazuje nazwę, typ, system, w odpowiednich przypadkach ciało i współrzędne, kategorię i mały podgląd obrazu. **Wyszukiwanie tekstowe oraz filtry typu i kategorii** można łączyć. Wyszukiwanie obejmuje nazwę, system, ciało i notatkę.

**Otwórz / Pokaż** wyświetla zapisane informacje, notatkę i większy podgląd obrazu. **Pokaż w Explorerze** używa istniejącego przeglądu systemu lub szczegółów ciała, jeśli ulubiony należy do bieżącego systemu Explorera i są dostępne odpowiednie dane. Dla innych systemów zapisane informacje ulubionego pozostają dostępne.

**Edytuj** zmienia nazwę, kategorię, notatkę i obraz. System, ciało i zapisane współrzędne nie są zastępowane wartościami na żywo. Dla innej pozycji utwórz nowy ulubiony powierzchniowy.

**Usuń** wymaga potwierdzenia i usuwa wyłącznie rekord ulubionego i jego wewnętrzną kopię obrazu. Dane Explorera, dziennika i ciał zostają zachowane.

### Obrazy ulubionych i ostatni zrzut ekranu

Obrazy ulubionych są **całkowicie oddzielone od zwykłej sekcji Obrazy**. CMDRHelper zarządza własną wewnętrzną kopią w folderze obrazów ulubionych (`data/favorites/images/` przy standardowym układzie danych). Oryginał nie jest przenoszony ani zmieniany.

- **Wybierz obraz …** przyjmuje PNG, JPEG lub WebP i pokazuje podgląd. Wewnętrzna kopia powstaje dopiero przy zapisie.
- **Użyj ostatniego zrzutu ekranu** przy każdym kliknięciu ponownie skanuje rzeczywisty folder źródłowy zrzutów. Uwzględnia też odpowiednie przekonwertowane zrzuty Elite w folderze aktywnego dowódcy wewnątrz skonfigurowanego celu konwersji. Nowy zrzut pozostaje więc dostępny, jeśli automatyczna konwersja usunęła już jego BMP.
- Proponowane są czytelne pliki o pasujących nazwach Elite lub konwersji, a nie dowolne obrazy z ogólnych folderów. Kolejność określa jednoznaczny czas wykonania w nazwie pliku, a w przeciwnym razie czas pliku. Dla obrazów po konwersji używany jest czas wykonania zapisany w nazwie, a nie czas konwersji.
- Przed przyjęciem znalezionego zrzutu widzisz nazwę pliku, czas wykonania i świeżo wczytany podgląd. Potwierdź przez **Użyj tego obrazu**. Jeśli nie znaleziono pasującego zrzutu, wybór ręczny pozostaje dostępny. CMDRHelper sam nie wykonuje zrzutów ekranu.

Obraz można później zastąpić lub usunąć. Niepotrzebne kopie wewnętrzne są usuwane przy zapisywaniu lub usuwaniu ulubionego. **Działania na ulubionych nigdy nie usuwają oryginalnego zrzutu ani wybranego oryginalnego obrazu.** Gdy brakuje wewnętrznego pliku obrazu, ulubiony działa bez podglądu.

### Ulubiony powierzchniowy jako cel

**▶ Do celu** przekazuje zapisane ciało, szerokość, długość geograficzną i nazwę ulubionego do istniejącego nawigatora planetarnego, zastępując jego poprzedni cel. Ulubione nie mają własnej logiki nawigacji. Odpowiednie prawidłowe dane planetarne uruchamiają nawigację; w przeciwnym razie nawigator czeka jak dotąd.

Ulubionych innych dowódców nie można używać jako własnych celów. Zmiana dowódcy kończy cel nadal obsługiwany jako ulubiony cel poprzedniego dowódcy. Ulubione systemów i ciał wyświetlają istniejące informacje, bez własnego planowania tras.

## Kronika

Kronika to zapisana historia twoich podróży i znalezisk. Jej **mapa podróży 3D** pokazuje odwiedzone systemy i trasy dowódców. Szczegóły systemów i ciał pomagają odnaleźć znane informacje BIO, GEO, o materiałach, Codex i wydobyciu.

### Połączone filtry

**Zastosuj** lub **Enter w polu tekstowym** uruchamia razem wszystkie ustawione filtry:

- tekst,
- opcjonalne **Od** i **Do**,
- **Planetarne miejsca wydobycia** i **Co najmniej**,
- **Moje odkrycia wydobywcze** i **Towar**.

Termin z **Pomocy wyszukiwania / Legendy** trafia do pola wyszukiwania i jest uruchamiany razem z już ustawionymi filtrami okresu i wydobycia.

### Okres w UTC

Od i Do aktywuje się oddzielnymi polami wyboru. Można ustawić jedną granicę; bez zaznaczenia danej granicy nie ma ograniczenia czasu z tej strony. **Od** włącza początek wybranego dnia kalendarzowego UTC. **Do** obejmuje cały wybrany dzień UTC. UTC jest wspólną podstawą czasu, a nie twoim lokalnym czasem kalendarzowym.

Decydują **rzeczywiste wizyty w systemach**: co najmniej jedna zapisana wizyta musi mieścić się w okresie. Sam pierwszy lub ostatni moment poznania systemu nie zastępuje wizyty. Przy aktywnym okresie liczba wizyt oraz pierwsza i ostatnia wizyta na mapie dotyczą przefiltrowanych wizyt.

Okres filtruje wizyty, a nie pojedyncze zdarzenia odkryć, BIO, GEO czy wydobycia. Znane informacje o znaleziskach i osobiste ilości wydobycia pozostają zapisanymi **wartościami całkowitymi**. **„Miedź 56 t” przy aktywnym okresie nie oznacza automatycznie „56 t w tym okresie”.** Jeśli Od jest późniejsze niż Do, pojawia się błąd i nie rozpoczyna się zapytanie do bazy.

### Dowódca i odświeżanie

**Wybór dowódców mapy** określa wyświetlane trasy. Osobiste wyszukiwania tekstowe i wydobywcze dotyczą natomiast oglądanego lub aktywnego dowódcy. Pola wyboru mapy nie rozszerzają automatycznie osobistego wyszukiwania na wielu dowódców.

**Odśwież kronikę** ponownie ładuje dane i uruchamia aktywne filtry. **Bieżąca pozycja** najpierw stosuje bieżące filtry, a następnie centruje aktualny system tylko wtedy, gdy znajduje się on na wynikowej mapie. W przeciwnym razie pojawia się komunikat; filtry zostają zachowane.

**Resetuj** czyści tekst, wyłącza Od/Do i przywraca widoczne pola dat. Pola wydobycia są odznaczane, minimalna liczba staje się 0, a towar Wszystkie. Wybór dowódców pozostaje; następnie ładowana jest zwykła kronika.

Przy **braku wyników** mapa i trasy są czyszczone, lista wyników czyszczona i ukrywana, szczegóły resetowane, a otwarte okno szczegółów systemu kroniki zamykane. Stare wyniki nie pozostają na ekranie.

### Obsługa mapy

- Przeciągnij lewym przyciskiem myszy: obrót.
- Przeciągnij prawym przyciskiem: przesunięcie.
- Przeciągnij środkowym przyciskiem: narysowanie ramki powiększenia.
- Kółko myszy: powiększanie.
- **Wyrównaj:** przywraca orientację do galaktycznego widoku z góry; przesunięcie i powiększenie pozostają zachowane.

## Obrazy i automatyczna konwersja zrzutów ekranu

W sekcji **Obrazy** ustawiasz folder źródłowy zrzutów Elite i cel konwersji. Automatyczna konwersja przetwarza nowe BMP na **PNG lub JPEG**. Dostępne jest regulowane rozjaśnianie. BMP istniejące już przy uruchomieniu nie są automatycznie przetwarzane wstecz przez samo włączenie monitorowania; służy do tego konwersja ręczna.

Nazwy przekonwertowanych plików zawierają czas wykonania, dowódcę i system; pliki są przechowywane według dowódców. Automatyczne przypisanie podąża za dowódcą aktywnego dziennika. Inny wybór galerii nie zmienia tego aktywnego dowódcy.

Opcja **usunięcia oryginalnego BMP po pomyślnej konwersji** należy wyłącznie do tej konwersji i ma własne ustawienie. Jest niezależna od zarządzania obrazami ulubionych.

Galeria pokazuje odpowiednie przekonwertowane obrazy z podglądem. Przy ponownym wyświetleniu jest odczytywana na nowo; odświeżanie również uwzględnia aktualne pliki. Wybór i duży podgląd aktualizują się wspólnie. Gdy wybrany obraz znika, wybierany jest istniejący obraz lub podgląd jest czyszczony. Sekcja Obrazy ma również własny wybór obrazów i usuwanie z potwierdzeniem.

## Pozostałe widoki

- **Przegląd:** aktywny dowódca, statek, pozycja, wykrycie dziennika, otwarte misje i status online.
- **Misje:** trwale zapisane otwarte misje ze znanymi celami, postępem i stanem ukończenia. Brakujące dane nie są uzupełniane ani wymyślane.
- **CMDR:** majątek, rangi, statystyki, MercCoins, statki/flota i znana pozycja Fleet Carriera. MercCoins są wyświetlane jako sumy zgłoszone przez Frontier, a nie samodzielnie obliczone saldo.
- **Planer tras:** osobne planowanie dla statku i Fleet Carriera ze Spansh. Obliczone trasy carriera można eksportować do CSV dla CTSVision. Obliczenia wymagają połączenia z usługą zewnętrzną.

## Dowódca, lokalne dane i usługi online

CMDRHelper identyfikuje aktywnego dowódcę po Frontier ID z bieżącej sesji dziennika. Osobista eksploracja, misje, majątek, ulubione i dane dostępu online są przechowywane osobno. Samo oglądanie innego dowódcy nie zmienia dowódcy na żywo ani przypisania jego wysyłek.

Lokalna baza SQLite zachowuje znane systemy, ciała i osobistą historię po restartach. Nowe kompletne wpisy dziennika są przetwarzane podczas gry; zapisane pozycje odczytu zapobiegają zbędnemu ponownemu czytaniu. Jeśli pozycja lub dowódca są nieprawidłowe, sprawdź najpierw wykrywanie dziennika i jego folder w ustawieniach.

**EDSM** może dostarczać dodatkowe dane systemów. Obsługiwane dane dziennika mogą być przesyłane do **EDSM i Inara**, gdy dana usługa jest skonfigurowana i włączona z własnymi danymi dostępu aktywnego dowódcy. Dowódca nie używa automatycznie klucza API innego dowódcy. Lokalne zapisywanie działa niezależnie od dostępności połączenia online.

## Języki i pomoc kontekstowa

Interfejs obsługuje **12 języków**: **DE, EN, FR, IT, NO, SV, FI, PL, NL, ES, TR, EL** – niemiecki, angielski, francuski, włoski, norweski, szwedzki, fiński, polski, niderlandzki, hiszpański, turecki i grecki.

Obecnie jest **937 kluczy UI-i18n na język**. **? Pomoc** udostępnia **10 szczegółowych tematów pomocy kontekstowej we wszystkich 12 językach**. Ulubione należą do pomocy Explorera; nawigacja planetarna ma własny temat dostępny bezpośrednio z nawigatora. Pomoc używa bieżącego języka interfejsu i zachowuje niemiecki jako zapasowy przy braku katalogu lub wpisu.

## Wymagania

| Platforma | Python |
| --- | --- |
| **Windows** | **Python 3.10 lub nowszy, wymagany x64.** Brak sztucznego górnego limitu dla istniejących wersji. Decydują późniejsze rzeczywiste kontrole pakietów i importów. |
| **Linux** | Bez zmian **Python od 3.10 do 3.13**, zalecane 64 bity. Musi być dostępny moduł venv odpowiadający wersji Pythona. |

Wymagane pakiety znajdują się w `requirements.txt`:

```text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

Instalacja pobiera te zależności. Lokalne pliki Elite muszą być dostępne do analizy dzienników i nawigacji planetarnej. Pod Linuksem Elite może działać przez Steam/Proton; rzeczywiste ścieżki dzienników i zrzutów ustawiasz w CMDRHelper. Opisane wsparcie HUD-u dla Linuksa dotyczy X11.

## Instalacja pod Linuksem

Rozpakuj kompletny projekt lub wydanie i uruchom w folderze projektu:

```bash
./install.sh
./start.sh
```

Skrypty używają wyłącznie lokalnego `venv` tej instalacji. Rozwiązują dowiązania symboliczne skryptów, sprawdzają Python i pip i mogą naprawić uszkodzone lokalne środowisko bez naruszania danych osobistych ani dzienników Elite. Brakujące pakiety systemowe nie są instalowane automatycznie; instalator zgłasza brak modułu venv. Dotychczasowa instalacja linuksowa pozostaje bez zmian.

## Instalacja pod Windows

1. Rozpakuj kompletny ZIP do osobnego folderu.
2. Uruchom **install.bat**, który wywołuje dołączony **install-windows.ps1**.
3. Po udanej instalacji uruchom CMDRHelper przez **start.bat**.

Istniejący **Python od 3.10 wzwyż, x64**, jest akceptowany bez sztucznego górnego limitu. Przyszła wersja Pythona nie jest odrzucana wyłącznie ze względu na numer. Odpowiedni istniejący Python lub użyteczny lokalny venv zapobiega niepotrzebnej automatycznej instalacji Pythona.

Jeśli nie ma odpowiedniego Pythona, instalator po uzyskaniu zgody oferuje automatyczną instalację przez **winget**. Celowo wybrano do tego stałą serię wersji **Python 3.14 x64**; wybór jest oddzielny od otwartej reguły dla już istniejących wersji. Jeśli automatyczna instalacja nie jest możliwa, instalator zgłasza błąd.

Instalator tworzy, sprawdza lub naprawia tylko **lokalny venv tej kopii CMDRHelper**, instaluje zależności i wykonuje **pip check** oraz kontrole importów **PySide6, PySide6.QtWidgets, numpy i PIL**. Dopiero te rzeczywiste sprawdzenia rozstrzygają o użyteczności środowiska. Ich niepowodzenie przerywa instalację z czytelnym komunikatem. Inne środowiska wirtualne nie są naprawiane ani zastępowane.

## Diagnostyka i pakiety wydania

W razie problemów pomagają wskaźniki dziennika i statusu online oraz logi w folderze `logs`. Dane osobiste są przechowywane lokalnie; kopia zapasowa ulubionych musi zawierać wewnętrzne kopie obrazów oprócz bazy danych.

Własny pakiet wydania można utworzyć przez `./create_release.sh`. Wersja programu jest zarządzana centralnie w `cmdrhelper/version.py` i odczytywana przez skrypt wydania. Pakiet zawiera kod i zasoby, ale bez osobistej bazy danych, venv, plików Git ani pamięci podręcznej.

## Materiały graficzne i wideo / Media Credits

CMDRHelper wykorzystuje dla wybranych specjalnych obiektów
astronomicznych wizualizacje **NASA Scientific Visualization Studio
(NASA SVS)**. Poszczególne materiały pozostają własnością ich
właścicieli praw i są oznaczane zgodnie z informacjami o autorstwie
podanymi na stronach NASA SVS.

### Gwiazda neutronowa

-   Plik CMDRHelper: `star_neutron.webm`
-   Źródło: NASA Scientific Visualization Studio, **Neutron Star
    Animations** (SVS ID 20267)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animatorzy: Walt Feimer (KBR Wyle Services, LLC) i Lisa Poje (USRA)
-   Źródło: https://svs.gsfc.nasa.gov/20267/

### Czarna dziura

-   Plik CMDRHelper: `black_hole.mp4` lub rozszerzenie pliku wideo
    używane w projekcie
-   Źródło: NASA Scientific Visualization Studio, **Black Hole Accretion
    Disk Visualization** (SVS ID 13326)
-   Credit: **NASA's Goddard Space Flight Center/Jeremy Schnittman**
-   Źródło: https://svs.gsfc.nasa.gov/13326/

### Supermasywna czarna dziura

-   Plik CMDRHelper: `black_hole_supermassive.mp4` lub rozszerzenie
    pliku wideo używane w projekcie
-   Źródło: NASA Scientific Visualization Studio (SVS ID 14576)
-   Credit: **NASA's Goddard Space Flight Center/J. Schnittman and B.
    Powell**
-   Źródło: https://svs.gsfc.nasa.gov/14576/

### Biały karzeł

-   Plik CMDRHelper: `star_white_dwarf.webm`
-   użyty materiał NASA: **White Dwarf establishing shot**
    (`WDStar_4k_60fps_ProRes.webm`)
-   Źródło: NASA Scientific Visualization Studio, **Type Ia Supernovae
    Animations** (SVS ID 20344)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animatorka: Adriana Manrique Gutierrez (USRA)
-   Producer: Scott Wiessinger (USRA)
-   Źródło: https://svs.gsfc.nasa.gov/20344/

Podanie tych źródeł i informacji o autorstwie nie oznacza, że CMDRHelper
jest wspierany, certyfikowany lub wydawany przez NASA. W przypadku
dalszego wykorzystania materiałów NASA obowiązują odpowiednie informacje
i zasady reprodukcji podane w oryginalnych źródłach.

## Licencja

CMDRHelper jest wolnym oprogramowaniem i jest publikowany na warunkach
**GNU General Public License Version 3 (GPL-3.0)**.

Kod źródłowy może być używany, modyfikowany i rozpowszechniany zgodnie z
warunkami GPL-3.0. Przy rozpowszechnianiu wersji pochodnych również
obowiązują warunki GPL-3.0.

Copyright © 2026 **Holger Mangold (Faber38)**.

Pełne warunki licencji znajdują się w pliku `LICENSE`.

## Informacja dotycząca Elite Dangerous

CMDRHelper jest niezależnym projektem społecznościowym/hobbystycznym i
nie jest oficjalnym produktem Frontier Developments.

**Elite Dangerous** oraz powiązane nazwy i treści są własnością
odpowiednich właścicieli praw.
