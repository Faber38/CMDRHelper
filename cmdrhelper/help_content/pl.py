"""Polish content for contextual help."""


HELP_TOPICS = {
    "materials": (
        'Materiały',
        """<h2>Materiały</h2>
<h3>CMDRHelper v3.2</h3>
<p>Zarządzanie materiałami inżynieryjnymi: wszystkie 146 materiałów Raw, Manufactured i Encoded wraz z klasami, pojemnościami i wyjątkami. Aktualne zapasy dowódcy, wyszukiwanie, filtry, pięć subtelnych teł wierszy oraz zapisana szerokość i kolejność kolumn ułatwiają przeglądanie. Nieznany stan pozostaje odróżniony od zera.</p>
<p>Ekwipunek Odyssey: czwarta karta zawiera 223 tożsamości katalogowe towarów, komponentów, danych i przedmiotów zużywalnych. Schowek, plecak i wiarygodna suma pozostają oddzielne; widoczne są stosy misji, status i zastosowania inżynieryjne. Dodatnie ilości mają złoty kolor. Brakujące tłumaczenia nazw zastępuje angielski.</p>
<p>Wyszukiwanie handlarzy materiałami (Znajdź handlarza → Otwórz planer trasy): na żądanie Spansh szuka osobno Raw, Manufactured i Encoded od bieżącego systemu dowódcy. Carriery są wykluczane, a dane stacji weryfikowane. Odległość w ly jest bezpośrednia między systemami; dane społeczności nie gwarantują dostępu. Przekazanie do planera ustawia tylko system docelowy i nie uruchamia trasy. Brak wyszukiwania handlarzy Odyssey.</p>
<p>Ta główna sekcja pokazuje materiały inżynieryjne aktualnie przeglądanego dowódcy. Wybór w widoku CMDR obowiązuje również tutaj; dane innych dowódców pozostają oddzielone.</p>
<h3>Trzy kategorie</h3>
<p>Karty Surowce, Materiały wytworzone i Dane kodowane zawierają wszystkie 146 materiałów katalogowych, w tym materiały Guardian i Thargoid. Lista jest posortowana według stopnia, a w obrębie każdego stopnia alfabetycznie.</p>
<h3>Stan i paski</h3>
<p>Liczby pokazują stan / maksimum, na przykład Wanad 244 / 250. Odpowiadający pasek pokazuje 97,6 %. Materiały, których nigdy nie posiadano, również pojawiają się ze stanem 0, jeśli stan jest wiarygodnie znany.</p>
<p>Puste zapasy są oznaczone stonowaną czerwienią, niewielkie żółcią/pomarańczem, a prawie pełne lub pełne zielenią. Liczby pozostają widoczne niezależnie od kolorów.</p>
<h3>Wyszukiwanie i filtry</h3>
<p>Wyszukiwanie uwzględnia wyświetlaną i angielską nazwę materiału. Można je łączyć ze wszystkimi filtrami: Wszystkie, Puste (0), Mało (powyżej 0 do 20 % włącznie), Prawie pełne (od 80 % do poniżej 100 %) i Pełne (100 %). Wartości między 20 % a 80 % pojawiają się tylko w filtrze Wszystkie. Karty i filtry są przywracane przy następnym uruchomieniu.</p>
<h3>Nieznane wartości</h3>
<p>Bez wiarygodnego pełnego stanu wyświetlane jest na przykład ? / 250. Przy nieznanym maksimum może pojawić się 12 / ?. W obu przypadkach nie ma wartości procentowej ani paska; takie materiały pojawiają się wyłącznie w filtrze Wszystkie. Nieznany stopień trafia do osobnej grupy na końcu listy.</p>
<h3>Aktualizacja na żywo</h3>
<p>Nowe zdarzenia dziennika automatycznie aktualizują stan, również po wymianie materiałów, pracach inżynieryjnych, syntezie lub nagrodach w materiałach. Podczas pierwszego odczytu pojawia się komunikat o wczytywaniu. Świeżo zebrany materiał jest krótko wyróżniany oznaczeniem takim jak Wanad +1; zużycie nie powoduje powiadomienia o zebraniu.</p>
<h3>Nazwy materiałów</h3>
<p>Jeśli nazwa materiału nie jest jeszcze dostępna w wybranym języku, pojawia się jego angielska nazwa wyświetlana. Wewnętrzne symbole dziennika nie zastępują istniejących nazw wyświetlanych.</p>
<h3>Odyssey</h3>
<p>Czwarta karta w sekcji Materiały zawiera Towary, Komponenty, Dane i Materiały eksploatacyjne. Schowek i Plecak pokazują swoje stany oddzielnie. Łącznie pokazuje sumę tylko wtedy, gdy oba stany są wiarygodnie zgodne. Nieaktualny stan plecaka celowo nie jest pokazywany jako bieżący ani dodawany do sumy; ? oznacza stan nieznany lub obecnie niemożliwy do wiarygodnego odtworzenia. Limit 1000 dotyczy każdej kategorii schowka, nie pojedynczych przedmiotów. Powyższy przykład materiałów inżynieryjnych nie określa indywidualnego maksimum dla przedmiotów Odyssey. Dla materiałów eksploatacyjnych nadal nie ma w pełni zweryfikowanej reguły pojemności, więc nie jest wyświetlana niepotwierdzona pojemność.</p>
<p>Zastosowanie pokazuje oznaczenia zastosowań przedmiotu. Misja oznacza, że konkretny stos w ekwipunku jest przypisany do misji, a nie że dany typ przedmiotu jest z zasady przedmiotem misyjnym. Zwykłe stosy i stosy powiązane z misją pozostają oddzielone. Nawet po ukończeniu misji przedmiot pozostaje oznaczony, dopóki dziennik wykazuje go w ekwipunku; ukończenie nie usuwa go automatycznie. Podpowiedź pokazuje numer misji i znany status. Inżynieria oznacza, że statyczny katalog Odyssey zna co najmniej jedno potwierdzone zastosowanie: ulepszenie kombinezonu, ulepszenie broni, modyfikację kombinezonu, modyfikację broni lub odblokowanie inżyniera. Poszczególne zastosowania są podane w podpowiedzi. Brak oznaczenia nie oznacza, że przedmiot jest bezużyteczny lub nadaje się wyłącznie do handlu. Mogą być też wyświetlane przedmioty Powerplay i inne przedmioty specjalne.</p>
<p>Wyszukiwanie znajduje wyświetlane lokalne i angielskie nazwy materiałów/przedmiotów. Sześć filtrów Odyssey to Wszystkie (wszystkie przedmioty), Misja (stosy przypisane do misji), Inżynieria (przedmioty z potwierdzonym zastosowaniem inżynieryjnym), Plecak (stan plecaka większy od zera), Schowek (stan schowka większy od zera) i Stan 0 (wiarygodnie znany stan łączny równy 0). Nieznany stan ? nie jest równy 0 i nie należy do filtra Stan 0. Brakujące tłumaczenia nazw zastępuje nazwa angielska, dlatego niektóre nazwy mogą pozostać angielskie w wybranym języku. Jest to zamierzone i nie stanowi błędu tłumaczenia logiki ekwipunku.</p>
<p>Ekwipunek jest automatycznie aktualizowany w tle. Potwierdzone nowe zebrania mogą być krótko wyróżniane. Przy zmianie dowódcy stare stany są natychmiast usuwane. Podkarty, filtry, szerokości i kolejność kolumn są zapisywane oddzielnie dla Odyssey.</p>""",
    ),'overview': ('Przegląd',
              '<h2>Przegląd</h2>\n'
              '<p>Przegląd to strona główna CMDRHelper. Podsumowuje najważniejsze informacje o '
              'aktualnie aktywnym dowódcy i pokazuje w mgnieniu oka, czy dziennik, lokalizacja i '
              'usługi internetowe są prawidłowo rozpoznawane.</p>\n'
              '\n'
              '<h3>Dowódca i statek</h3>\n'
              '<p>Tutaj wyświetlany jest dowódca rozpoznany w Elite Dangerous Journal i aktualnie '
              'używany statek.</p>\n'
              '<p>CMDRHelper przypisuje dane osobowe odpowiedniemu dowódcy na podstawie '
              'identyfikatora Frontier (FID). Dzięki temu dane pochodzące od różnych dowódców są '
              'oddzielone od siebie.</p>\n'
              '<p>Podczas zmiany dowódcy ładowane są zapisane informacje powiązane z nowym '
              'dowódcą.</p>\n'
              '\n'
              '<h3>dziennik</h3>\n'
              '<p>CMDRHelper wykorzystuje pliki dziennika Elite Dangerous jako główne źródło '
              'danych.</p>\n'
              '<p>Wyświetlanie dziennika informuje, czy znaleziono pliki dziennika i przypisano je '
              'do aktywnego dowódcy. Nowe, kompletne wpisy do dziennika są automatycznie '
              'przetwarzane podczas rozgrywki.</p>\n'
              '<p>Obszary dziennika, które zostały już przetworzone, są zapisywane, dzięki czemu '
              'CMDRHelper nie musi ponownie w pełni oceniać każdego dziennika przy następnym '
              'uruchomieniu.</p>\n'
              '\n'
              '<h3>Aktualna lokalizacja</h3>\n'
              '<p>Pokazuje aktualnie znany układ gwiezdny oraz – o ile wiadomo z dziennika – '
              'dokładną lokalizację dowódcy.</p>\n'
              '<p>Lokalizacja jest aktualizowana na podstawie zdarzeń, takich jak skoki, dokowanie '
              'i inne raporty o pozycji, i zapisywana na podstawie poleceń dowódcy.</p>\n'
              '\n'
              '<h3>Misje</h3>\n'
              '<p>W tym obszarze wyświetlana jest liczba aktualnie znanych otwartych misji.</p>\n'
              '<p>Przycisk lub pozycja menu „Misje” przenosi Cię do pełnego widoku misji ze '
              'znanymi celami misji i informacjami o statusie.</p>\n'
              '\n'
              '<h3>Ostatni bastion</h3>\n'
              '<p>„Ostatni stan” podsumowuje ostatni znany trwały stan dowódcy. Umożliwia to '
              'przywrócenie ważnych informacji nawet po ponownym uruchomieniu Elite Dangerous lub '
              'CMDRHelper.</p>\n'
              '\n'
              '<h3>Systemy końcowe</h3>\n'
              '<p>Tutaj wyświetlane są ostatnio odwiedzone systemy lub rozpoznane w '
              'dzienniku.</p>\n'
              '<p>Lista służy jako szybki przegląd ostatniej podróży Komendanta.</p>\n'
              '<p>Historia wizyt uwzględnia Location, FSDJump i CarrierJump także podczas bieżącego odczytu dziennika. Wiele zdarzeń pozycji w ramach jednego nieprzerwanego pobytu liczy się jako jedna wizyta: A → A → A liczy się raz. Prawdziwy powrót jest zachowany: A → B → C → A to cztery wizyty.</p>\n\n'
              '<h3>Stan online</h3>\n'
              '<p>W górnej części okna głównego znajdują się dodatkowe wskaźniki stanu:</p>\n'
              '<ul>\n'
              '<li><b>Dziennik rozpoznany</b>– CMDRHelper wykrył prawidłowe źródło dziennika i '
              'tożsamość dowódcy.</li>\n'
              '<li><b>EDSM</b>– pokazuje aktualny stan transmisji EDSM dla aktywnego dziennika '
              'FID.</li>\n'
              '<li><b>INARA</b>– pokazuje aktualny stan transmisji Inara dla aktywnego dziennika '
              'FID.</li>\n'
              '</ul>\n'
              '<p>Dane dostępowe online zarządzane są oddzielnie dla każdego dowódcy. Dowódca '
              'nigdy automatycznie nie używa API-Key innego dowódcy.</p>\n'
              '\n'
              '<h3>Ważne dla wielu dowódców</h3>\n'
              '<p>Bieżące dane zawsze zależą od dowódcy, który został wyraźnie zidentyfikowany '
              'podczas bieżącej sesji dziennika Elite Dangerous.</p>\n'
              '<p>Samo wyświetlenie innego dowódcy w widoku nie zmienia aktywnego dowódcy na żywo '
              'ani nie wpływa na żadną transmisję EDSM lub Inara.</p>\n'
              '\n'
              '<h3>Wskazówka</h3>\n'
              '<p>Jeśli dowódca, statek lub lokalizacja nie odpowiadają aktualnemu stanowi gry, '
              'najpierw sprawdź wyświetlacz dziennika u góry, a następnie sprawdź folder dziennika '
              'ustawiony w „Ustawieniach”.</p>'),
 'missions': ('Misje',
              '<h2>Misje</h2>\n'
              '<p>Widok misji przedstawia misje aktualnie oglądanego dowódcy znanego z Elite '
              'Dangerous Journal. CMDRHelper zapisuje dane misji dla każdego dowódcy, dzięki czemu '
              'otwarte misje zostaną zachowane nawet po ponownym uruchomieniu Elite Dangerous lub '
              'CMDRHelper.</p>\n'
              '\n'
              '<h3>Misje otwarte</h3>\n'
              '<p>Wychodzą nowe misje<code>MissionAccepted</code>przejęte i zapisane na '
              'stałe.</p>\n'
              '<p>Dopóki nie nastąpi ostatnie wydarzenie misji, misja pozostaje otwarta. Nowa '
              'sesja gry bez listy misji może nie usunąć automatycznie znanych otwartych '
              'misji.</p>\n'
              '\n'
              '<h3>Stan misji</h3>\n'
              '<p>CMDRHelper przetwarza między innymi następujące zmiany statusów:</p>\n'
              '<ul>\n'
              '<li>Misja przyjęta</li>\n'
              '<li>Misja zakończona</li>\n'
              '<li>Misja nie powiodła się</li>\n'
              '<li>Misja przerwana</li>\n'
              '<li>Cel misji zmieniony</li>\n'
              '<li>Postęp w zakresie wspieranych misji związanych z ładunkiem/składem</li>\n'
              '</ul>\n'
              '<p>Ostatnie wydarzenie zmienia jedynie powiązaną z nim misję.</p>\n'
              '\n'
              '<h3>Misje z dziennika</h3>\n'
              '<p>Elite Dangerous dostarcza informacji o misji na temat różnych wydarzeń w '
              'dzienniku. CMDRHelper łączy te zdarzenia w trwały stan misji.</p>\n'
              '<p>Prawdziwe wydarzenie z pełną misją może służyć jako wiarygodna migawka. Jeśli '
              'zabraknie takiego wydarzenia, starsze misje otwarte nie zostaną zamknięte tylko z '
              'tego powodu.</p>\n'
              '\n'
              '<h3>Cele i miejsca</h3>\n'
              '<p>W zakresie, w jakim Elite dostarcza informacje w dzienniku, CMDRHelper '
              'pokazuje:</p>\n'
              '<ul>\n'
              '<li>System docelowy</li>\n'
              '<li>Stacja docelowa lub miejsce docelowe</li>\n'
              '<li>Celuj w planetę lub ciało</li>\n'
              '<li>Oznaczenie misji</li>\n'
              '<li>znany postęp</li>\n'
              '<li>aktualny stan</li>\n'
              '</ul>\n'
              '<p>Nie każda misja dostarcza wszystkich informacji. Brakujące dane nie zostały '
              'wymyślone przez CMDRHelper.</p>\n'
              '\n'
              '<h3>Trwałość i restart</h3>\n'
              '<p>Misje otwarte zapisywane są w bazie danych dowódców.</p>\n'
              '<p>Oznacza to, że zostaną one zachowane nawet jeśli:</p>\n'
              '<ul>\n'
              '<li>Elite Dangerous zostanie zakończony i uruchomiony ponownie później</li>\n'
              '<li>CMDRHelper jest zamknięty pomiędzy</li>\n'
              '<li>Nowa sesja dziennika początkowo nie zawiera żadnych wydarzeń misji</li>\n'
              '</ul>\n'
              '<p>Tylko udokumentowane wydarzenie misji zmienia zapisany stan.</p>\n'
              '\n'
              '<h3>Kilku dowódców</h3>\n'
              '<p>Misje są ściśle oddzielone od dowódcy.</p>\n'
              '<p>Wydarzenie misji jest przydzielane wyłącznie dowódcy, którego sesja dziennika '
              'została jednoznacznie zidentyfikowana. Nie można wyświetlać ani modyfikować misji '
              'innego dowódcy.</p>\n'
              '\n'
              '<h3>Misje osierocone lub nieaktualne</h3>\n'
              '<p>Jeśli starsze dane dziennika lub poprzedni import sprawią, że misja pozostanie '
              'otwarta, mimo że już jej nie ma w grze, można skorzystać z istniejącej funkcji '
              'resetowania/czyszczenia misji osieroconych.</p>\n'
              '<p>Tej funkcji należy używać tylko wtedy, gdy jest jasne, że wyświetlana misja nie '
              'jest już aktywna.</p>\n'
              '\n'
              '<h3>Usługi internetowe</h3>\n'
              '<p>Obsługiwane zdarzenia misji mogą być dodatkowo przesyłane do Inara, jeśli dla '
              'aktywnego dziennika FID skonfigurowano ważny i aktywowany dostęp Inara.</p>\n'
              '<p>Brakujące lub nieosiągalne połączenie Inara nie ma wpływu na lokalne '
              'przechowywanie misji.</p>\n'
              '\n'
              '<h3>Wskazówka</h3>\n'
              '<p>Jeśli misja nie pojawia się lub pokazuje nieprawidłowy status, najpierw sprawdź, '
              'czy Elite Dangerous nie zapisał już odpowiedniego zdarzenia misji w dzienniku.</p>\n'
              '<p>CMDRHelper może wyświetlać tylko informacje, które dziennik faktycznie dostarcza '
              'lub które zostały już zapisane z poprzednich unikalnych wydarzeń misji.</p>'),
 'explorer': ('Odkrywca',
              '<h2>Odkrywca</h2>\n<h3>CMDRHelper v3.2</h3>\n<p>Widok całego systemu: nowy układ w stylu Elite zastępuje miniaturę w Explorerze i Kronice. Gwiazdy i planety tworzą główną strukturę, a księżyce odgałęziają się poniżej; układy wielogwiazdowe pozostają czytelne. Zoom, przewijanie, dopasowanie do okna i kliknięcie ciała umożliwiają dostęp do szczegółów.</p>\n<p>Zwarte pasy asteroid: skupiska są grupowane w pasy w widoku ogólnym oraz zwykłych mapach Explorera i Kroniki. Wszystkie dane poszczególnych skupisk są zachowane.</p>\n<p>Poprawiona kartografia: skan po mapowaniu DSS nie zeruje już niesprzedanych wartości eksploracji, czasu mapowania ani wydajności. Błędne wpisy są naprawiane przy starcie z dostępnych dzienników jednoznacznie przypisanych do dowódcy. Bez źródeł naprawa oczekuje; nie trzeba usuwać bazy danych.</p>\n'
              '<p>Eksplorator ocenia systemy i ciała niebieskie odkryte i zeskanowane przez '
              'aktywnego dowódcę. Łączy Twoje własne dane z dziennika Elite Dangerous z już '
              'dostępnymi dodatkowymi informacjami i wyświetla razem eksplorację, kartografię, '
              'sygnały biologiczne/geologiczne i dane dotyczące górnictwa odkrywkowego.</p>\n'
              '\n'
              '<h3>Aktualny system</h3>\n'
              '<p>Aktualny poziom wiedzy o systemie podsumowany jest w górnym obszarze.</p>\n'
              '<p>Należą do nich między innymi:</p>\n'
              '<ul>\n'
              '<li>ciała znane, a nawet odnotowane w czasopiśmie</li>\n'
              '<li>istniejących sygnałów</li>\n'
              '<li>Skanuj wartości</li>\n'
              '<li>wartość kartograficzna została już osiągnięta</li>\n'
              '<li>możliwa wartość całkowita, jeśli jest w pełni odwzorowana</li>\n'
              '<li>Status BIO i szacunkowe wartości BIO</li>\n'
              '<li>Dane kartograficzne i BIO, które nie zostały jeszcze przesłane</li>\n'
              '</ul>\n'
              '<p>Podane wartości opierają się na faktycznie dostępnych danych. Brakujące '
              'informacje nie są przedstawiane jako osobne odkrycie.</p>\n'
              '\n'
              '<h3>Mapa systemu</h3>\n'
              '<p>Mapa systemu graficznie przedstawia gwiazdy, planety, księżyce i inne znane '
              'ciała w bieżącym układzie.</p>\n'
              '<p>Można kliknąć obiekt, aby otworzyć jego szczegółowy widok.</p>\n'
              '<p>Wyświetlacz pokazuje między innymi typ ciała, odległość i – jeśli są dostępne – '
              'wartości skanowania i kartografii, a także specjalne właściwości eksploracji.</p>\n'
              '\n'
              '<h3>ORGANICZNE ×N</h3>\n'
              '<p>BIO ×N oznacza liczbę sygnałów biologicznych ciała zgłaszanych przez grę.</p>\n'
              '<p>Liczba początkowo wskazuje jedynie, ile sygnałów biologicznych lub rodzajów '
              'zgłoszono. Nie oznacza to automatycznie, że wszystkie gatunki biologiczne zostały '
              'już znalezione lub przeanalizowane.</p>\n'
              '<p>Rzeczywiste własne odkrycia organiczne przechowywane są oddzielnie.</p>\n'
              '\n'
              '<h3>GEO×N</h3>\n'
              '<p>GEO ×N pokazuje liczbę sygnałów geologicznych ciała zgłoszonych przez grę.</p>\n'
              '<p>Mogą to być na przykład obiekty geologiczne, takie jak fumarole lub gejzery. '
              'CMDRHelper wyświetla tylko informacje, które wynikają z istniejących danych '
              'kroniki/treści.</p>\n'
              '\n'
              '<h3>ABBAU ×N</h3>\n'
              '<p>ABBAU ×N pokazuje liczbę planetarnych miejsc wydobycia ciała zgłoszoną przez '
              'Elite Dangerous.</p>\n'
              '<p>Przykład:</p>\n'
              '<p><b>ABBAU ×24</b></p>\n'
              '<p>oznacza, że \u200b\u200bdla tego ciała zgłoszono 24 planetarne miejsca '
              'wydobycia.</p>\n'
              '<p>Liczba nie mówi, jaki surowiec można wydobyć w jednym miejscu.</p>\n'
              '\n'
              '<h3>Własne znaleziska górnicze</h3>\n'
              '<p>Jeśli dowódca faktycznie przeprowadził górnictwo odkrywkowe za pomocą Rhino, '
              'CMDRHelper przechowuje osobiste ustalenia udokumentowane osobno.</p>\n'
              '<p>Rozróżnia się:</p>\n'
              '<ul>\n'
              '<li>faktycznie uzyskane towary, np. B. Miedź w tonach</li>\n'
              '<li>materiały wtórne zebrane podczas wydobycia</li>\n'
              '<li>ogólne materiały powierzchniowe ciała</li>\n'
              '</ul>\n'
              '<p>Przykładem osobistego znaleziska może być:</p>\n'
              '<p><b>Miedź – 56 t</b></p>\n'
              '<p>Z tej informacji wynika, że \u200b\u200bkomendant ten faktycznie wydobył tam 56 '
              'ton miedzi.</p>\n'
              '<p>Osobiste znaleziska górnicze są zapisywane dla każdego dowódcy i nie są mieszane '
              'ze znaleziskami innych dowódców.</p>\n'
              '\n'
              '<h3>Materiały powierzchniowe ciała</h3>\n'
              '<p><code>Scan.Materials</code>opisuje ogólny skład materiału powierzchniowego '
              'ciała.</p>\n'
              '<p>Na przykład żelazo, nikiel, siarka lub inne materiały mogą być wyświetlane w '
              'wartościach procentowych.</p>\n'
              '<p>Wartości tych nie należy mylić z surowcami planetarnego składu wydobywczego. '
              'Frontier nie podaje w czasopiśmie żadnego udokumentowanego bezpośredniego związku '
              'pomiędzy tymi ogólnymi materiałami korpusu a zawartością konkretnego miejsca '
              'wydobycia.</p>\n'
              '\n'
              '<h3>Terraformowanie</h3>\n'
              '<p>Symbol lub etykieta terraformacji wskazuje, że ciało jest uważane za kandydata '
              'do terraformowania na podstawie dostępnych danych.</p>\n'
              '\n'
              '<h3>Pierwsze odkrycie</h3>\n'
              '<p>„Już odkryte w chwili twojego skanu” opisuje stan przed tamtym skanowaniem. Tak oznacza wcześniej odkryte, Nie oznacza jeszcze wtedy nieodkryte; brak informacji pozostaje stanem Nieznanym. ★ oznacza kandydata do First Discovery w chwili skanowania, a nie gwarantowane oficjalne pierwszeństwo nadal dostępne dzisiaj.</p>\n<p>Historyczne WasDiscovered=false lub WasMapped=false nie oznacza, że ciało nadal jest nieodkryte lub niezmapowane dzisiaj. Obserwacje pozostają historyczne po sprzedaży danych lub ponownej wizycie. Obecność w EDSM to odrębna informacja, która nie dowodzi oficjalnego odkrycia w Elite. Nie wywodzi się z niej oficjalnego pierwszego odkrywcy.</p>\n'
              '\n'
              '<h3>Pierwsze mapowanie</h3>\n'
              '<p>CMDRHelper rozróżnia:</p>\n'
              '<ul>\n'
              '<li>◉ Kandydat do First Mapping w chwili skanowania: jeszcze niezmapowane podczas twojego skanowania</li>\n<li>◎ Zmapowane przez ciebie: zapisano ukończenie twojego mapowania DSS</li>\n<li>◉✓ Potwierdzony kandydat podczas skanowania i własne mapowanie; oficjalne pierwszeństwo niepotwierdzone</li>\n'
              '</ul>\n'
              '<p>„Już zmapowane w chwili twojego skanu” jest oceniane niezależnie od odkrycia. Brak informacji pozostaje stanem Nieznanym. Wcześniej odkryte ciało mogło być jeszcze niezmapowane podczas skanowania. Twoje mapowanie nie potwierdza oficjalnego oznaczenia First Mapping; po wielu wizytach nie zawsze znana jest również kolejność względem zapisanego skanowania.</p>\n<p>Ukończenie własnego mapowania DSS zapisuje teraz niezawodnie czas mapowania, użyte sondy i cel wydajności. Późniejsze skanowania nie powodują już utraty istniejących informacji.</p>\n'
              '\n'
              '<h3>Wiejski bar</h3>\n'
              '<p>Wskaźnik możliwości lądowania identyfikuje ciała, na których według znanych '
              'danych możliwe jest lądowanie.</p>\n'
              '\n'
              '<h3>Złote ramy / cenne ciała</h3>\n'
              '<p>Szczególnie cenne ciała można wyróżnić na wyświetlaczu eksploratora.</p>\n'
              '<p>Złota ramka oznacza szacowaną wartość mapowania powyżej ustawionego progu. Nie jest znacznikiem First Discovery i nie potwierdza niesprzedanych danych ani premii za pierwszeństwo dostępnych jeszcze dzisiaj.</p>\n'
              '<p>Nie zastępuje szczegółowego wyświetlania wartości ciała.</p>\n'
              '\n'
              '<h3>Lista wartości</h3>\n'
              '<p>Lista wartości pokazuje szacunki według zapisanego skanowania, a nie gwarantowane zaległe wypłaty. Premie za pierwszeństwo pozostają niepotwierdzone. Podpowiedzi mapy i listy oraz szczegóły ciała używają tych samych stanów odniesionych do czasu skanowania.</p>\n'
              '<p>Jest szczególnie przydatny do szybkiego porównywania interesujących lub '
              'wartościowych obiektów w systemie.</p>\n'
              '\n'
              '<h3>ORGANICZNE / GEO / DEGRADACJA</h3>\n'
              '<p>Pogląd ten grupuje ciała posiadające sygnały biologiczne, geologiczne lub '
              'planetarne.</p>\n'
              '<p>Oznacza to, że interesujących obiektów nie trzeba wyszukiwać pojedynczo na całej '
              'mapie systemu.</p>\n'
              '<p>Jeśli posiadasz własne dane dotyczące górnictwa odkrywkowego, widoczne mogą być '
              'również Twoje osobiste znaleziska górnicze.</p>\n'
              '<p>Ręcznie zmienione szerokości kolumn wspólnej tabeli BIO / GEO / ABBAU w Eksploratorze pozostają po ponownym otwarciu i restarcie programu. Szerokości kolumn okien podręcznych są przywracane odporniej na błędy; nieprawidłowe wartości zastępują bezpieczne szerokości domyślne.</p>\n\n'
              '<h3>Szczegóły ciała</h3>\n'
              '<p>Kliknięcie na bryłę otwiera widok szczegółowy.</p>\n'
              '<p>O ile wiadomo, mogą się tam pojawić:</p>\n'
              '<ul>\n'
              '<li>Typ ciała</li>\n'
              '<li>masa</li>\n'
              '<li>dystans</li>\n'
              '<li>Powaga</li>\n'
              '<li>atmosfera</li>\n'
              '<li>Możliwość lądowania</li>\n'
              '<li>Stan terraformowania</li>\n'
              '<li>Sygnały BIO/GEO</li>\n'
              '<li>planetarne miejsca wydobywcze</li>\n'
              '<li>Materiały powierzchniowe</li>\n'
              '<li>własne znaleziska górnicze</li>\n'
              '<li>Wartość skanowania</li>\n'
              '<li>wartość kartograficzna</li>\n'
              '<li>aktualna wartość</li>\n'
              '</ul>\n'
              '<p>Nie każdy organ posiada wszystkie informacje.</p>\n'
              '\n'
              '<h3>Prognozy BIO</h3>\n'
              '<p>CMDRHelper może oszacować możliwe odkrycia biologiczne w oparciu o istniejące '
              'dane dotyczące odpowiednich ciał.</p>\n'
              '<p>Przewidywania nie stanowią gwarancji, że dany gatunek rzeczywiście będzie '
              'obecny. Służą jako pomoc w podejmowaniu decyzji podczas eksploracji.</p>\n'
              '<p>Szacowane wartości BIO są również przewidywaniami i są traktowane oddzielnie od '
              'faktycznie potwierdzonych wyników.</p>\n'
              '\n'
              '<h3>Jeszcze nie przesłane</h3>\n'
              '<p>CMDRHelper przechowuje znaną kartografię dowódcy i dane BIO, które nie zostały '
              'jeszcze przesłane.</p>\n'
              '<p>Sprzedaż kartografii i tantiemy biologiczne są rozliczane przy użyciu '
              'odpowiednich wydarzeń w dzienniku.</p>\n'
              '<p>Dane kartograficzne, które zostały już sprzedane, po rekonstrukcji nie powinny '
              'być ponownie wyświetlane jako otwarte.</p>\n'
              '\n'
              '<h3>Pokaż samochód</h3>\n'
              '<p>Obsługiwane wskazówki eksploratora, takie jak cenne ciała lub znaleziska BIO, '
              'mogą być automatycznie wyświetlane za pomocą przełączników na lewym pasku '
              'bocznym.</p>\n'
              '<p>Te małe, aktywne okna służą jako dodatkowe wskazówki podczas gry i nie zastępują '
              'pełnego widoku Eksploratora.</p>\n'
              '<p>„Cargo” pokazuje potwierdzoną zawartość Ship lub SRV określonego przez aktywną Journal-FID. SRV Cargo nigdy nie jest przejmowane jako Ship Cargo; Limpety wliczają się do całkowitego obciążenia i są wyświetlane oddzielnie w tabeli Nazwa | Ilość.</p>\n'
              '<p>Postęp BIO jest zwięzły: 1/3 żółte, 2/3 niebieskie i 3/3 zielone; ukończony stan „Gotowe” też jest zielony. W „pokazuj automatycznie” GEO ma własny zapisywany przełącznik: tylko BIO, tylko GEO lub oba razem.</p>\n<p>Okno ładowni automatycznie dostosowuje wysokość do zawartości. Przy wielu wpisach wysokość jest ograniczona, a tabelę można przewijać; wybrana szerokość i pozycja okna pozostają zachowane. Istniejący przełącznik „HUD ładowni” znajduje się teraz w „pokazuj automatycznie”, bez dodatkowego przełącznika w oknie ładowni.</p>\n\n'
              '<h3>Kilku dowódców</h3>\n'
              '<p>Wyniki osobistych poszukiwań, znaleziska kartograficzne, znaleziska BIO i własne '
              'znaleziska z górnictwa odkrywkowego przydzielane są odpowiedniemu dowódcy.</p>\n'
              '<p>Globalne właściwości astronomiczne ciała – na przykład liczba znanych '
              'planetarnych miejsc wydobycia – pozostają właściwościami samego ciała.</p>\n'
              '\n'
              '<h3>Wskazówka</h3>\n'
              '<p>Jeśli masz ciekawą sylwetkę, warto kliknąć na widok szczegółowy. To najlepsze '
              'miejsce, aby rozróżnić ogólne dane dotyczące ciała, możliwe wyniki eksploracji i '
              'faktyczne znaleziska udokumentowane przez twojego dowódcę.</p>'
              """

<h3>★ Ulubione</h3>
<p>Przycisk „★ Ulubione” u góry Explorera otwiera osobne okno ulubionych, które jest używane ponownie. Zapisujesz w nim systemy, planety/księżyce i miejsca na powierzchni dla aktywnego dowódcy.</p>
<p>Przewijana lista, posortowana alfabetycznie według nazw, pokazuje nazwę, typ, system, w odpowiednich przypadkach ciało niebieskie i szerokość/długość geograficzną, kategorię oraz mały podgląd obrazu. Wyszukiwanie tekstowe oraz filtry typu i kategorii można stosować wspólnie. Wyszukiwanie obejmuje nazwę, system, ciało niebieskie i notatkę.</p>
<p>„Otwórz / Pokaż” pokazuje zapisane dane, notatkę i większy podgląd obrazu. „Pokaż w Explorerze” otwiera istniejący przegląd systemu lub szczegóły ciała niebieskiego, jeśli ulubiony należy do bieżącego systemu Explorera i dostępne są odpowiednie dane. W przypadku innych systemów zapisane dane ulubionego pozostają widoczne; trasa między systemami nie jest obliczana.</p>

<h3>Zapisywanie systemu, planety lub bieżącej pozycji</h3>
<ul>
<li>„★ Zapisz bieżący system” zapisuje bieżący system bez współrzędnych powierzchniowych.</li>
<li>„★ Zapisz planetę / księżyc” pozwala wybrać znaną planetę lub księżyc w bieżącym systemie. Ten ulubiony również nie otrzymuje współrzędnych powierzchniowych.</li>
<li>„★ Zapisz bieżącą pozycję” znajduje się u góry okna ulubionych, obok dwóch pozostałych opcji zapisu, i jest też dostępny w nawigatorze planetarnym. W oknie ulubionych przycisk jest zawsze widoczny i pozostaje nieaktywny bez prawidłowych bieżących danych pozycji planetarnej i aktywnego dowódcy. Kliknięcie utrwala dowódcę, system, ciało niebieskie, szerokość i długość geograficzną. Późniejszy ruch w grze nie zmienia tych wartości w otwartym oknie dialogowym.</li>
</ul>
<p>Wpisz dowolną nazwę i wybierz dokładnie jedną kategorię: Bio, Geo, Wydobycie, Widok, Lądowisko, Ciekawe lub Inne. Notatka i obraz są opcjonalne. Znane identyfikatory techniczne są przejmowane wewnętrznie; nie musisz ich wpisywać. Szerokość lub długość geograficzna 0,0 to również prawidłowe współrzędne.</p>
<p>„Edytuj” zmienia nazwę, kategorię, notatkę i obraz. System, ciało niebieskie i zapisane współrzędne zostają zachowane. Aby zapisać inne miejsce na powierzchni, utwórz nowy ulubiony w tej pozycji.</p>

<h3>Szybki ulubiony bez myszy</h3>
<p>W sekcji „Ustawienia → Szybki ulubiony” możesz dowolnie ustawić, zmienić lub usunąć globalny skrót klawiszowy. Po instalacji domyślny stan to „Nie przypisano”: CMDRHelper nie rejestruje żadnego klawisza bez polecenia użytkownika. Przypisanie jest zapisywane. Jeśli kombinacja jest już zajęta lub niedostępna w twoim systemie, pojawia się komunikat o błędzie; poprzednie działające przypisanie zostaje zachowane.</p>
<p>W systemach Linux/X11 i Windows skrót działa również wtedy, gdy Elite ma fokus – pieszo, w SRV i w statku. Naciśnięcie klawisza natychmiast zapisuje aktualną pozycję na powierzchni dla aktywnego dowódcy, bez okna dialogowego i bez użycia myszy. Dowódca, system, ciało niebieskie i aktualne wartości Latitude/Longitude zostają utrwalone w tej chwili. Bez prawidłowych aktualnych współrzędnych planetarnych nic nie jest zapisywane; wcześniejsze współrzędne nie są ponownie używane.</p>
<p>Ulubiony otrzymuje unikalną tymczasową nazwę, na przykład „Znacznik 07.09.2026 06:32:15”, oraz kategorię „Inne”. W zwykłym oknie ulubionych możesz później zmienić jego nazwę, przypisać inną kategorię, dodać notatkę lub obraz. Żaden zrzut ekranu nie jest automatycznie wykonywany ani importowany.</p>
<p>Przez około dwie sekundy bezpośrednio nad aktywnym oknem Elite wyświetla się „★ ULUBIONY ZAPISANY” wraz z ciałem niebieskim i współrzędnymi; jeśli pozycja jest niedostępna, na krótko pojawia się „⚠ BRAK WSPÓŁRZĘDNYCH PLANETARNYCH”. Komunikat nie przejmuje fokusu i nie przechwytuje danych wejściowych. Działa również przy wyłączonym HUD-zie nawigacji, po czym znika całkowicie. Przy włączonym HUD-zie pozostaje potem zwykły widok nawigacji. Zapisane ustawienie przełącznika HUD-u nie jest zmieniane. Komunikat korzysta z tej samej infrastruktury nakładki i wymagań platformy co HUD nawigacji.</p>

<h3>Obrazy ulubionych</h3>
<p>Obrazy ulubionych są oddzielone od sekcji Obrazy. „Wybierz obraz …” obsługuje PNG, JPEG i WebP. Dopiero przy zapisie CMDRHelper kopiuje wybrany obraz do własnego folderu obrazów ulubionych. Oryginalny plik nie jest przenoszony ani zmieniany.</p>
<p>„Użyj ostatniego zrzutu ekranu” przy każdym kliknięciu ponownie odczytuje skonfigurowany folder źródłowy zrzutów ekranu i szuka czytelnych zrzutów o nazwach typowych dla Elite. Bez ustawionego folderu uwzględniane są standardowe katalogi zrzutów Elite w Windows lub Steam/Proton. Przeszukiwany jest też folder aktywnego dowódcy w skonfigurowanym miejscu docelowym konwersji, aby znaleźć pasujące przekonwertowane zrzuty Elite. Dzięki temu przekonwertowany zrzut można znaleźć nawet po usunięciu jego oryginalnego BMP. O najnowszym czasie wykonania decyduje jednoznaczny znacznik czasu w nazwie pliku, a w przeciwnym razie czas pliku; dla obrazów po konwersji liczy się czas wykonania zapisany w nazwie, a nie czas konwersji. CMDRHelper sam nie wykonuje zrzutów ekranu ani nie przeszukuje dowolnych folderów z obrazami.</p>
<p>Przed użyciem wyświetlane są nazwa pliku, czas wykonania i świeżo wczytany podgląd. Potwierdź przyciskiem „Użyj tego obrazu”. Jeśli nie znaleziono odpowiedniego zrzutu, nadal możesz użyć „Wybierz obraz …”. Zrzuty BMP z Elite są zapisywane jako wewnętrzna kopia PNG.</p>
<p>Obraz można zastąpić w oknie edycji lub odznaczyć przyciskiem „Usuń obraz”. Zapis usuwa nieużywaną już kopię wewnętrzną. Jeśli brakuje pliku obrazu, ulubiony pozostaje użyteczny bez podglądu.</p>

<h3>Cel ulubionego i dowódca</h3>
<p>„▶ Do trasy” ustawia znany system ulubionego jako cel w planerze tras. Punkt początkowy korzysta z aktualnego AppState zgodnie z dotychczasowym zachowaniem; ręcznie wpisany początek zostaje zachowany. Trasa nie jest obliczana automatycznie. „◎ Do współrzędnych” uruchamia istniejącą nawigację planetarną do miejsca na powierzchni z istniejącym HUD, jeśli zapisano system, ciało niebieskie i prawidłowe współrzędne. Podróż do systemu i nawigacja po powierzchni to dwa oddzielne kroki bez automatycznej sekwencji podróży. Bez współrzędnych powierzchniowych dostępna jest tylko trasa; działania bez wymaganych danych są ukrywane.</p>
<p>Dla miejsc na powierzchni „◎ Do współrzędnych” przekazuje zapisane ciało niebieskie, szerokość, długość geograficzną i nazwę ulubionego do istniejącego nawigatora planetarnego. Nowy cel zastępuje poprzedni. Ulubione nie mają własnej logiki nawigacji. Nawigator nadal decyduje sam: pasujące prawidłowe dane planetarne uruchamiają nawigację; w przeciwnym razie czeka na te dane.</p>
<p>Ulubione należą wyłącznie do aktywnego dowódcy. Zmiana dowódcy odświeża listę i odrzuca otwarte okno edycji. Cel nadal obsługiwany jako ulubiony cel poprzedniego dowódcy zostaje zakończony. Wybór dowódców w kronice nie rozszerza tej listy ulubionych.</p>
<p>„Usuń” wymaga potwierdzenia i usuwa tylko rekord ulubionego oraz jego wewnętrzną kopię obrazu. Oryginalny zrzut ekranu lub wybrany oryginalny obraz oraz wszystkie dane Explorera, dziennika i ciał niebieskich zostają zachowane.</p>"""),
 'chronicle': (
        'Kronika',
        """<h2>Kronika</h2>
<h3>CMDRHelper v3.2</h3>
<p>Widok całego systemu: nowy układ w stylu Elite zastępuje miniaturę w Explorerze i Kronice. Gwiazdy i planety tworzą główną strukturę, a księżyce odgałęziają się poniżej; układy wielogwiazdowe pozostają czytelne. Zoom, przewijanie, dopasowanie do okna i kliknięcie ciała umożliwiają dostęp do szczegółów.</p>
<p>Zwarte pasy asteroid: skupiska są grupowane w pasy w widoku ogólnym oraz zwykłych mapach Explorera i Kroniki. Wszystkie dane poszczególnych skupisk są zachowane.</p>
<p>Kronika to osobista historia podróży i odkryć dowódcy. Wykorzystuje trwale przechowywane informacje z dziennika do wyszukiwania systemów, które zostały już odwiedzone, do ich przestrzennego przedstawienia i wyszukiwania znanych odkryć.</p>

<h3>Odwiedzone systemy</h3>
<p>Kronika pokazuje odwiedzone systemy i ich lokalizacje w galaktyce znanej Komendantowi.</p>
<p>Jeśli to możliwe, pod uwagę brana jest pierwsza i ostatnia wizyta oraz znane informacje o organizmie.</p>
<p>Przy aktywnym okresie liczba wizyt, pierwsza wizyta i ostatnia wizyta w widoku mapy odnoszą się do przefiltrowanych rzeczywistych wizyt w systemach.</p>
<p>Kronika jest zatem nie tylko mapą, ale także narzędziem umożliwiającym odnalezienie dotychczasowych celów podróży i odkryć.</p>

<h3>Mapa 3D</h3>
<p>Odwiedzane układy są reprezentowane przestrzennie za pomocą galaktycznych współrzędnych X/Y/Z.</p>
<p>Instrukcja obsługi znajduje się bezpośrednio nad mapą:</p>
<ul>
<li>Przytrzymaj lewy przycisk myszy → obróć widok</li>
<li>przytrzymaj środkowy przycisk myszy i przeciągnij → narysuj okno powiększenia</li>
<li>Przytrzymaj prawy przycisk myszy → przesuń widok</li>
</ul>
<p>Mały wyświetlacz osi pomaga w orientacji w przestrzeni.</p>

<h3>Aktualna pozycja</h3>
<p>Dzięki „Aktualnej pozycji” widok mapy można wyrównać lub przywrócić do aktualnie znanej lokalizacji aktywnego dowódcy.</p>
<p>Najpierw stosowane są aktualne filtry. Widok jest centrowany na bieżącym systemie tylko wtedy, gdy znajduje się on na wynikowej mapie.</p>
<p>W przeciwnym razie pojawia się „Bieżący system nie jest objęty tym wyborem filtrów.” Filtry nie są przez to wyłączane.</p>

<h3>Wyrównaj</h3>
<p>„Wyrównaj” przywraca orientację do widoku płaszczyzny galaktyki z góry. Przesunięcie i powiększenie zostają zachowane.</p>
<p>Jest to przydatne, gdy liczne obroty sprawiły, że mapa stała się nieczytelna.</p>

<h3>Odśwież Kronikę</h3>
<p>„Odśwież Kronikę” ponownie ładuje dane kroniki według aktualnych połączonych filtrów i odświeża widok. Tekst, włączone granice dat i filtry wydobycia są ponownie oceniane wspólnie; aktywne filtry nie są ignorowane.</p>
<p>Funkcja nie zmienia plików dziennika ani nie tworzy nowych danych eksploracyjnych. Po prostu aktualizuje wyświetlaną historię w oparciu o istniejące dane CMDRHelper.</p>

<h3>Wyszukiwanie dowolne</h3>
<p>Znaną już treść można wyszukiwać korzystając z pola „Historia wyszukiwania…”.</p>
<p>Przy wyszukiwaniu uwzględniane są – jeśli są dostępne w bazie – m.in.:</p>
<ul>
<li>Nazwy systemów</li>
<li>Cechy ciała</li>
<li>dane biologiczne</li>
<li>Przybory</li>
<li>Dane Kodeksu</li>
</ul>
<p>Tekst, okres i wydobycie znajdują się we wspólnym obszarze filtrów. „Zastosuj” ocenia ustawione filtry łącznie. Enter w polu tekstowym uruchamia to samo wspólne filtrowanie co „Zastosuj”.</p>

<h3>Okres Od/Do (UTC)</h3>
<p>Włącz „Od” i „Do” za pomocą odpowiednich pól wyboru i wybierz datę. Można też użyć tylko jednej granicy. Bez zaznaczonego pola po danej stronie nie ma ograniczenia czasowego; bez obu zaznaczeń okres nie jest ograniczany.</p>
<ul>
<li><b>Od:</b> Od początku wybranego dnia kalendarzowego UTC włącznie.</li>
<li><b>Do:</b> Uwzględniany jest cały wybrany dzień kalendarzowy UTC, aż do chwili bezpośrednio przed początkiem następnego dnia.</li>
</ul>
<p>UTC to uniwersalny czas koordynowany. Granice dat odnoszą się do dni kalendarzowych UTC, a nie dni w twojej lokalnej strefie czasowej.</p>
<p>Filtrowane są rzeczywiste wizyty w systemach z <code>system_visits</code>. Wymagana jest rzeczywista wizyta danego dowódcy w wybranym okresie. Zapisane wartości <code>first_seen</code> i <code>last_seen</code> nie zastępują prawdziwej wizyty: samo położenie okresu między wcześniejszą pierwszą a późniejszą ostatnią wizytą nie wystarcza.</p>
<p>Okres filtruje wizyty, a nie pojedyncze zdarzenia odkrycia, BIO, GEO czy wydobycia. Znane informacje o znaleziskach i wydobyte ilości pozostają zapisanymi wartościami łącznymi. Od/Do można używać samodzielnie albo razem z tekstem i filtrami wydobycia.</p>
<p>Jeśli Od jest późniejsze niż Do, pojawia się „Data Od nie może być późniejsza niż data Do.” Nie jest uruchamiane żadne zapytanie do bazy danych. Popraw granice dat i ponownie zastosuj filtry.</p>

<h3>Wyniki wyszukiwania</h3>
<p>Trafienia wyświetlane są na liście istniejących wyników pod kartą kroniki.</p>
<p>W zależności od rodzaju trafienia może pojawić się system i korpus oraz dodatkowe informacje.</p>
<p>Trafienie może zostać wykorzystane do znalezienia odpowiedniego, znanego już układu lub korpusu i otwarcia istniejących szczegółowych informacji.</p>

<h3>Brak wyników</h3>
<p>Jeśli prawidłowe filtrowanie nie znajduje wyników, mapa i trasy są czyszczone. Lista wyników jest czyszczona i ukrywana, widok szczegółów jest resetowany, a otwarte okno szczegółów systemu kroniki jest zamykane.</p>
<p>Stare wyniki nie pozostają widoczne. Sprawdź wtedy połączenie tekstu wyszukiwania, okresu i filtrów wydobycia oraz dowódcę używanego w danym widoku.</p>

<h3>Planetarne miejsca wydobycia</h3>
<p>Filtru „Planetne miejsca wydobycia” można użyć do wyszukiwania znanych obiektów, dla których Elite Dangerous zgłosił miejsca wydobycia planet.</p>
<p>Podstawowy wyświetlacz odpowiada temu znanemu z Explorera:</p>
<p><b>ABBAU ×N</b></p>
<p>Numer należy do samego korpusu i nie jest powiązany z dowódcą.</p>

<h3>Co najmniej</h3>
<p>Używając opcji „Co najmniej” możesz określić minimalną liczbę planetarnych miejsc wydobycia, jakie powinna posiadać jednostka.</p>
<p>Przykład:</p>
<p><b>Co najmniej 20</b></p>
<p>pokazuje tylko znane ciała z co najmniej:</p>
<p><b>ABBAU ×20</b></p>
<p>Umożliwia to specyficzną lokalizację szczególnie rozległych obszarów górniczych.</p>

<h3>Moje odkrycia wydobywcze</h3>
<p>W przypadku „Własnych znalezisk górniczych” przeszukanie ogranicza się do zwłok, w przypadku których dany dowódca w sposób oczywisty sam przeprowadził eksploatację odkrywkową.</p>
<p>Informacje te pochodzą z osobistej historii górnictwa odkrywkowego i są ściśle oddzielone od dowódcy.</p>
<p>Jednostka może zatem mieć globalne sygnały ABBAU ×N bez konieczności usuwania przez własnego dowódcę czegokolwiek.</p>

<h3>Towar</h3>
<p>Jeżeli aktywna jest opcja „Własne znaleziska górnicze”, dostępna jest także opcja „Surowiec”.</p>
<p>Na liście znajdują się wyłącznie towary, które dany dowódca faktycznie zdobył już w górnictwie odkrywkowym.</p>
<p>Nie jest to teoretyczna lista wszystkich możliwych surowców wydobywczych.</p>
<p>Dla FABER38 lista może na przykład zawierać:</p>
<ul>
<li>Wszystko</li>
<li>miedź</li>
</ul>
<p>Jeżeli w późniejszym terminie faktycznie zostaną wydobyte dodatkowe surowce, automatycznie pojawią się one w Twoim osobistym wyborze.</p>

<h3>Ukierunkowane wyszukiwanie surowców</h3>
<p>Na przykład, jeśli wybierzesz „Miedź”, a następnie naciśniesz „Zastosuj”, historia pokaże tylko ciała, na których dany dowódca w sposób oczywisty wydobywał miedź.</p>
<p>Przykład:</p>
<p><b>Prua Hypai NV-E c28-66/2 — ABBAU ×24 — miedź 56 t</b></p>
<p>Oznacza to, że kronikę można wykorzystać jako osobistą bazę lokalizacyjną: wydobyty już surowiec można później ponownie odnaleźć.</p>

<h3>Wszystkie surowce</h3>
<p>W przypadku opcji „Surowiec: Wszystko” uwzględniane są wszystkie pasujące osobiste odkrycia w zakresie górnictwa odkrywkowego.</p>
<p>Jeżeli na korpusie znanych jest kilka towarów, można je wyświetlić razem z ilościami, jakie dotychczas uzyskali.</p>
<p>Przykład:</p>
<p><b>ABBAU ×24 — Hel-3 18 t, miedź 56 t</b></p>
<p>Ilości są osobistymi wartościami górniczymi odpowiedniego dowódcy, które faktycznie są udokumentowane na podstawie wydarzeń w dzienniku.</p>
<p>Także przy aktywnym okresie osobiste wydobyte ilości pozostają zapisanymi ilościami łącznymi. <b>Miedź 56 t</b> nie oznacza automatycznie <b>56 t w wybranym okresie</b>. Okres wymaga pasującej wizyty w systemie, ale nie ogranicza wyświetlanej wydobytej ilości do tego okresu.</p>

<h3>Połącz filtry</h3>
<p>Tekst, włączone granice Od/Do i filtry wydobycia można łączyć. Wynik musi spełniać ustawione warunki jednocześnie.</p>
<p>Na przykład:</p>
<ul>
<li>Aktywne miejsca wydobycia planet</li>
<li>Co najmniej 20</li>
<li>Aktywne są własne znaleziska górnicze</li>
<li>Surowiec miedź</li>
</ul>
<p>wyszukuje znane ciała z co najmniej 20 planetarnymi miejscami wydobywczymi, w których wspomniany dowódca sam wydobywał już miedź.</p>
<p>Dodatkowy tekst wyszukiwania również jest uwzględniany. Jeśli dodano okres, przeglądany dowódca musi rzeczywiście odwiedzić odpowiedni system w tym okresie; samo wydobycie miedzi nie musi przypadać na ten okres.</p>

<h3>Zastosuj</h3>
<p>„Zastosuj” wykonuje wspólne filtrowanie ze wszystkimi aktualnie ustawionymi filtrami wyszukiwania, okresu i wydobycia:</p>
<ul>
<li>Tekst</li>
<li>Od, jeśli włączone</li>
<li>Do, jeśli włączone</li>
<li>Planetarne miejsca wydobycia</li>
<li>Minimalna liczba</li>
<li>Moje odkrycia wydobywcze</li>
<li>Towar, jeśli „Moje odkrycia wydobywcze” jest włączone</li>
</ul>
<p>Enter w polu tekstowym wykonuje dokładnie to samo filtrowanie. Bez tekstu i filtrów wydobycia ładowana jest zwykła mapa dla dowódców zaznaczonych na mapie, w razie potrzeby ograniczona przez Od/Do.</p>

<h3>Resetuj</h3>
<p>„Resetuj” przywraca wspólny obszar filtrów do stanu początkowego:</p>
<ul>
<li>Tekst jest czyszczony.</li>
<li>Od i Do są wyłączane; pola dat ponownie pokazują dzisiejszą datę i są nieaktywne.</li>
<li>Planetarne miejsca wydobycia są wyłączane.</li>
<li>Minimalna liczba jest ustawiana na 0.</li>
<li>Moje odkrycia wydobywcze jest wyłączane.</li>
<li>Towar jest przywracany do „Wszystkie”.</li>
</ul>
<p>Wybór dowódców zostaje zachowany. Następnie zwykła kronika jest ponownie ładowana dla tego wyboru mapy; poprzednie wyniki wyszukiwania i widoki szczegółów są resetowane.</p>

<h3>Wybór dowódcy</h3>
<p>Kronika może wyświetlać dane różnych znanych dowódców.</p>
<p>Istnieją dwa odrębne rodzaje wyboru:</p>
<ul>
<li><b>Wybór dowódców mapy:</b> Pola wyboru dowódców określają, których dowódców trasy są widoczne na zwykłej mapie bez wyszukiwania tekstowego lub wydobywczego. Włączony okres jest uwzględniany.</li>
<li><b>Przeglądany dowódca:</b> Osobiste wyszukiwania tekstowe lub wydobywcze używają przeglądanego dowódcy (<code>viewed_commander_id</code>), a w jego braku aktywnego dowódcy. Od niego zależą również osobiste listy towarów.</li>
</ul>
<p>Jednakże dane osobowe, takie jak własne znaleziska górnicze i listy surowców, są zawsze oceniane oddzielnie dla faktycznie przeglądanego dowódcy.</p>
<p>Dowódca nie widzi w swoim wyborze surowców żadnych odkryć górniczych, które należą wyłącznie do innego dowódcy.</p>

<h3>Wszyscy dowódcy</h3>
<p>Wyświetlanie mapy/kroniki może uwzględniać wielu dowódców.</p>
<p>„Wszyscy dowódcy” odnosi się do wyboru dowódców mapy. Pola wyboru dowódców nie rozszerzają automatycznie osobistych wyszukiwań tekstowych lub wydobywczych na wielu dowódców.</p>
<p>Nie zmienia to przydziału osobowego danych dowódcy. Globalne właściwości astronomiczne układu lub ciała pozostają wspólne, osobiste ustalenia pozostają odrębne.</p>

<h3>Pomoc w poszukiwaniu/legenda</h3>
<p>Dodatkowe informacje na temat wyszukiwania kroniki i znaczenia wyświetlacza można uzyskać poprzez „Pomoc wyszukiwania / legenda”.</p>
<p>Kliknięty termin trafia do pola wyszukiwania i jest wyszukiwany wraz z już ustawionymi filtrami okresu i wydobycia.</p>
<p>Ta kontekstowa pomoc główna uzupełnia dostępną tam krótką instrukcję obsługi.</p>

<h3>Wskazówka</h3>
<p>Kronika szczególnie nadaje się do wyszukiwania ciekawych miejsc, które odkryto podczas dłuższej podróży.</p>
<p>Na przykład w przypadku górnictwa odkrywkowego może odpowiedzieć:</p>
<p>„Na której planecie wydobywałem kiedykolwiek miedź?”</p>
<p>Lub:</p>
<p>„Które z moich znanych planet mają szczególnie dużą liczbę miejsc wydobycia?”</p>""",
    ),
 'jump_tip': ('Wskazówka dotycząca skoku',
              '<h2>Wskazówka dotycząca skoku</h2>\n'
              '<p>Wskazówka skoku wspiera eksplorację poprzez ocenę znanych już danych systemowych '
              'i wyróżnianie interesujących systemów docelowych.</p>\n'
              '<p>Funkcja ma służyć jako pomoc w podejmowaniu decyzji. Nie gwarantuje, że '
              'rekomendowany system faktycznie zawiera rzadkie lub szczególnie cenne '
              'znaleziska.</p>\n'
              '\n'
              '<h3>Podstawa oceny</h3>\n'
              '<p>CMDRHelper wykorzystuje istniejące informacje z dziennika i bazy danych do oceny '
              'znanych wzorców w nazwach systemów i klasach systemów.</p>\n'
              '<p>Można uwzględnić między innymi skróty systemowe, znane już typy nadwozia i '
              'wcześniejsze znaleziska.</p>\n'
              '\n'
              '<h3>Skrót systemowy</h3>\n'
              '<p>Wiele proceduralnie generowanych systemów w Elite Dangerous zawiera kombinacje '
              'liter i cyfr, które identyfikują określone grupy systemów.</p>\n'
              '<p>CMDRHelper może statystycznie ocenić te skróty i pokazać, w jakich grupach w '
              'znanych dotychczas danych częściej pojawiały się interesujące znaleziska.</p>\n'
              '\n'
              '<h3>Dokonaj ponownej oceny</h3>\n'
              '<p>Dzięki opcji „Re-evaluate” istniejąca baza danych jest ponownie '
              'analizowana.</p>\n'
              '<p>Wykorzystywane są zapisane dane dowódcy. Funkcja nie tworzy nowych elitarnych '
              'danych ani nie modyfikuje plików dziennika.</p>\n'
              '\n'
              '<h3>Lista wyników</h3>\n'
              '<p>Lista wyników pokazuje najciekawsze skróty systemowe lub kandydatów według '
              'aktualnej oceny.</p>\n'
              '<p>W zależności od istniejącej bazy danych mogą znajdować się tam informacje '
              'o:</p>\n'
              '<ul>\n'
              '<li>ciekawe klasy planetarne</li>\n'
              '<li>odkrycia biologiczne</li>\n'
              '<li>Wodne światy</li>\n'
              '<li>ciała nadające się do terraformowania</li>\n'
              '<li>inne godne uwagi wyniki poszukiwań</li>\n'
              '</ul>\n'
              '<p>pojawić się.</p>\n'
              '\n'
              '<h3>Prawdopodobieństwo zamiast gwarancji</h3>\n'
              '<p>Wysoka wartość lub dobry ranking oznacza jedynie, że dany wzorzec częściej '
              'wiązał się z interesującymi wynikami w dotychczas ocenianych danych.</p>\n'
              '<p>To nie jest gwarancja.</p>\n'
              '<p>Polecany system może w dalszym ciągu być zupełnie nieciekawy, natomiast nisko '
              'oceniony system może zawierać cenne znaleziska.</p>\n'
              '\n'
              '<h3>Własna baza danych</h3>\n'
              '<p>Końcówka skoku współpracuje ze znanymi już danymi dowódcy.</p>\n'
              '<p>Im więcej systemów i organów jest rejestrowanych w miarę upływu czasu, tym '
              'większa staje się osobista baza danych do celów oceny.</p>\n'
              '<p>Oznacza to, że ranking może później ulec zmianie.</p>\n'
              '\n'
              '<h3>Kilku dowódców</h3>\n'
              '<p>Oceny osobiste przeprowadzane są na zasadzie każdego dowódcy.</p>\n'
              '<p>Dane innego dowódcy nie mogą niezauważone fałszować osobistych ocen.</p>\n'
              '<p>Z drugiej strony, globalne podstawowe dane astronomiczne mogą być udostępniane, '
              'o ile nie odzwierciedlają osobistych ustaleń dowódcy.</p>\n'
              '\n'
              '<h3>Wykorzystaj w praktyce</h3>\n'
              '<p>Wskazówka dotycząca skoków jest szczególnie przydatna, jeśli do wyboru jest '
              'kilka możliwych miejsc docelowych i wymagana jest dodatkowa pomoc w podjęciu '
              'decyzji.</p>\n'
              '<p>Nie zastępuje kompletnego narzędzia do planowania trasy i nie oblicza '
              'bezpiecznej, optymalnej trasy.</p>\n'
              '<p>Punkt menu „Planowanie trasy” umożliwia planowanie konkretnych tras.</p>\n'
              '\n'
              '<h3>Wskazówka</h3>\n'
              '<p>Użyj końcówki skoku jako dodatkowej pomocy w eksploracji:</p>\n'
              '<p>„Według moich wcześniejszych danych, który system wydaje mi się ciekawszy?”</p>\n'
              '<p>Nie jako prognoza:</p>\n'
              '<p>„Gwarantujemy, że w tym systemie znajdzie się konkretne znalezisko”.</p>'),
 'route_planner': ('Planowanie trasy',
                   '<h2>Planowanie trasy</h2>\n<h3>CMDRHelper v3.2</h3>\n<p>Ulepszony planer tras: start automatycznie śledzi bieżący system do ręcznego wpisania innego; wyczyszczenie pola przywraca automatykę. Statki i carriery używają dokładnie sprawdzonych adresów ID64 zamiast podobnych nazw. „Unable to find route” oznacza brak znalezionej trasy; sprawdź cele, zasięg i ustawienia.</p>\n'
                   '<p>Planer tras wspiera planowanie dłuższych podróży statkiem lub Fleet '
                   'Carrier. CMDRHelper może korzystać z zewnętrznych danych o trasie z Spansh i '
                   'przygotowywać zaplanowaną trasę do dalszego wykorzystania.</p>\n'
                   '\n'
                   '<h3>Zacznij i zakończ</h3>\n'
                   '<p>Do obliczenia trasy wymagany jest system początkowy i docelowy.</p>\n'
                   '<p>W miarę możliwości CMDRHelper może wykorzystywać obecnie znany system '
                   'Dowódcy jako punkt wyjścia. Początek i koniec należy sprawdzić przed '
                   'obliczeniem.</p>\n'
                   '\n'
                   '<h3>Statek lub Fleet Carrier</h3>\n'
                   '<p>Planista trasy rozróżnia podróże zwykłym statkiem i Fleet Carrier.</p>\n'
                   '<p>W obu przypadkach stosuje się różne wymagania i metody obliczeń. Dlatego '
                   'przed planowaniem należy wybrać odpowiedni rodzaj trasy.</p>\n'
                   '\n'
                   '<h3>Trasa statku</h3>\n'
                   '<p>W przypadku trasy statku uwzględniane są właściwości skoku znane lub '
                   'wprowadzone dla aktywnego statku.</p>\n'
                   '<p>W zależności od dostępnych danych, w planowaniu można uwzględnić dane FSD, '
                   'dane statku, masę, paliwo i inne parametry skoku.</p>\n'
                   '<p>Wyznaczona trasa stanowi pomoc w planowaniu. Zmiany statku lub jego masy '
                   'mogą zmienić rzeczywistą odległość skoku osiągalną w grze.</p>\n'
                   '\n'
                   '<h3>Trasa przewoźnika flotowego</h3>\n'
                   '<p>Fleet Carrier mają inne zasady skoków niż zwykłe statki.</p>\n'
                   '<p>CMDRHelper wykorzystuje planowanie przewoźnika Spansh dla odpowiednich '
                   'tras.</p>\n'
                   '<p>Trasa służy do planowania sekwencji skoków. Rzeczywiste zużycie trytu i '
                   'dostępny zasięg mogą również zależeć od masy i aktualnego stanu nośnika.</p>\n'
                   '\n'
                   '<h3>Spansh</h3>\n'
                   '<p>Do faktycznego obliczenia trasy CMDRHelper może skorzystać z usługi '
                   'zewnętrznej Spansh.</p>\n'
                   '<p>Żądanie jest przetwarzane w tle, dzięki czemu interfejs pozostaje sprawny '
                   'podczas dłuższych obliczeń.</p>\n'
                   '<p>CMDRHelper nie ma wpływu na dostępność i czas reakcji serwisu '
                   'zewnętrznego.</p>\n'
                   '\n'
                   '<h3>obliczenie</h3>\n'
                   '<p>Po rozpoczęciu kalkulacji zapytanie zostaje przekazane wybranemu planiście '
                   'trasy.</p>\n'
                   '<p>W zależności od trasy i usługi obliczenia mogą zająć trochę czasu. W tym '
                   'czasie nie należy niepotrzebnie rozpoczynać drugiego identycznego '
                   'obliczenia.</p>\n'
                   '\n'
                   '<h3>Wynik</h3>\n'
                   '<p>Pomyślnie obliczona trasa pokazuje zamierzone systemy lub punkty skoku w '
                   'ich kolejności.</p>\n'
                   '<p>W zależności od rodzaju trasy pojawiają się dodatkowe informacje dotyczące '
                   'dystansu, skoków, paliwa lub trytu oraz inne dostępne dane trasy.</p>\n'
                   '\n'
                   '<h3>Trasa i aktualny dowódca</h3>\n'
                   '<p>Obecny system i statek można – o ile są wyraźnie znane w aktywnym AppState '
                   '– wykorzystać do wstępnego przypisania lub do wsparcia planowania.</p>\n'
                   '<p>Jednak rzeczywista trasa pozostaje planem i nie zmienia żadnych danych '
                   'dziennika ani dowódcy.</p>\n'
                   '\n'
                   '<h3>Eksport CTSVision</h3>\n'
                   '<p>Obliczone trasy przewoźników flotowych można wyeksportować jako plik CSV '
                   'dla CTSVision.</p>\n'
                   '<p>Oznacza to, że trasa nośna zaplanowana w CMDRHelper może być następnie '
                   'wykorzystana w CTSVision do sterowania skokami lub przetwarzania trasy.</p>\n'
                   '<p>Eksport nie zmienia trasy w CMDRHelper.</p>\n'
                   '\n'
                   '<h3>plik CSV</h3>\n'
                   '<p>Wyeksportowany plik zawiera dane trasy wymagane dla CTSVision w zamierzonej '
                   'kolejności.</p>\n'
                   '<p>Plik nie powinien być zmieniany strukturalnie w sposób niekontrolowany po '
                   'eksporcie, jeśli ma być następnie wczytany przez CTSVision.</p>\n'
                   '\n'
                   '<h3>Błędy i usługi zewnętrzne</h3>\n'
                   '<p>Jeśli nie można uzyskać dostępu do Spansh lub usługa zwróci błąd, '
                   'CMDRHelper wyświetli odpowiedni komunikat o błędzie.</p>\n'
                   '<p>Błąd w obliczaniu trasy online nie powoduje zmiany danych lokalnego dowódcy '
                   'ani dziennika.</p>\n'
                   '\n'
                   '<h3>Planowanie trasy i wskazówka dotycząca skoków</h3>\n'
                   '<p>Wskazówki dotyczące skoków i planowanie trasy spełniają różne zadania:</p>\n'
                   '<ul>\n'
                   '<li>Wskazówka skoku ocenia możliwe interesujące cele eksploracji na podstawie '
                   'istniejących danych.</li>\n'
                   '<li>Planowanie trasy oblicza konkretną trasę między punktem początkowym a '
                   'miejscem docelowym.</li>\n'
                   '</ul>\n'
                   '<p>Dlatego dobra wskazówka dotycząca skoków nie jest automatycznie częścią '
                   'optymalnej trasy.</p>\n'
                   '\n'
                   '<h3>Kilku dowódców</h3>\n'
                   '<p>Jeśli używane są dane dowódcy, takie jak bieżący system lub statek, '
                   'pochodzą one z aktywnego aktywnego AppState i muszą być tam wyraźnie '
                   'przypisane.</p>\n'
                   '<p>Samo spojrzenie na innego dowódcę w widoku CMDR nie przełącza planisty '
                   'trasy na jego system lub statek.</p>\n'
                   '<p>Samo wyliczenie trasy nie powoduje zmiany danych osobowych innego '
                   'dowódcy.</p>\n'
                   '\n'
                   '<h3>Wskazówka</h3>\n'
                   '<p>Przed długą podróżą zawsze sprawdź jeszcze raz:</p>\n'
                   '<ul>\n'
                   '<li>Układ startowy</li>\n'
                   '<li>System docelowy</li>\n'
                   '<li>Typ trasy statek/przewoźnik</li>\n'
                   '<li>w przypadku tras statków – podstawowy statek, FSD i parametry skoku</li>\n'
                   '<li>w przypadku tras przewoźników dostępna rezerwa trytu</li>\n'
                   '</ul>\n'
                   '<p>W przypadku podróży przewoźnikiem flotowym zaleca się zaplanowanie '
                   'wystarczających rezerw na podróż powrotną lub nieplanowane objazdy.</p>'),
 'images': ('Kino',
            '<h2>Kino</h2>\n'
            '<p>Sekcja „Obrazy” zarządza zrzutami ekranu wykonanymi za pomocą Elite Dangerous. '
            'CMDRHelper może automatycznie rozpoznawać nowe nagrania, przetwarzać je i '
            'przechowywać w galerii na podstawie dowódcy.</p>\n'
            '\n'
            '<h3>Folder źródłowy</h3>\n'
            '<p>Folder źródłowy to folder, w którym Elite Dangerous zapisuje swoje zrzuty ekranu w '
            'formacie BMP.</p>\n'
            '<p>CMDRHelper może monitorować ten folder pod kątem nowych plików BMP. Aby '
            'automatyczne przetwarzanie działało, należy ustawić prawidłowy folder zrzutów '
            'ekranu.</p>\n'
            '\n'
            '<h3>Folder docelowy</h3>\n'
            '<p>Folder docelowy jest wspólnym folderem głównym dla obrazów przetwarzanych przez '
            'CMDRHelper.</p>\n'
            '<p>Użytkownik ustawia ten folder główny. CMDRHelper automatycznie tworzy wymagane '
            'podfoldery związane z dowódcą podczas przetwarzania.</p>\n'
            '\n'
            '<h3>Automatyczne przetwarzanie</h3>\n'
            '<p>Jeśli włączona jest opcja „Automatyczna konwersja” i ustawione są prawidłowe '
            'foldery źródłowe i docelowe, CMDRHelper regularnie sprawdza folder źródłowy pod kątem '
            'nowych zrzutów ekranu BMP.</p>\n'
            '<p>Po aktywacji istniejące pliki BMP są początkowo oznaczane jako znane i nie są '
            'automatycznie konwertowane bez pytania. W tym celu dostępna jest osobna funkcja '
            'konwersji istniejących BMP.</p>\n'
            '<p>Nowy plik nie jest umieszczany w kolejce, dopóki w dwóch kolejnych sprawdzeniach '
            'nie osiągnie tego samego, niezerowego rozmiaru. W rezultacie operacja zapisu, która '
            'nadal trwa, nie jest przetwarzana natychmiast.</p>\n'
            '\n'
            '<h3>Konwersja obrazu</h3>\n'
            '<p>Jako źródło CMDRHelper przetwarza pliki BMP. Jako format docelowy można wybrać '
            '„PNG” lub „JPG”.</p>\n'
            '<p>Pliki JPG są zapisywane na poziomie jakości 95. Pliki PNG są zapisywane w '
            'zoptymalizowany sposób.</p>\n'
            '<p>Domyślnie zachowywany jest oryginalny plik BMP. Jeśli włączona jest opcja „Usuń '
            'BMP po konwersji”, źródłowy BMP zostanie usunięty dopiero po pomyślnym zapisaniu '
            'obrazu docelowego.</p>\n'
            '\n'
            '<h3>Rozjaśnij obraz</h3>\n'
            '<p>Jasność można regulować w zakresie od 0 do 50 procent za pomocą suwaka i '
            'powiązanego pola liczbowego. Ustawienie zostało zapisane.</p>\n'
            '<p>Jest on automatycznie stosowany podczas każdej późniejszej konwersji - zarówno w '
            'przypadku nowo monitorowanych, jak i ręcznie inicjowanych istniejących plików BMP. 0 '
            'procent przejmuje pierwotną jasność; wyższe wartości odpowiednio zwiększają jasność '
            'wygenerowanego obrazu PNG lub JPG.</p>\n'
            '<p>Funkcja nie stanowi czystego podglądu i nie jest później stosowana do obrazu '
            'wybranego w galerii. Zmieniona jasność zostanie zapisana w nowym pliku '
            'docelowym.</p>\n'
            '<p>Źródłowy BMP pozostaje niezmieniony, chyba że aktywowano również usuwanie pliku '
            'BMP. Dane dziennika, dowódcy i eksploracji nie ulegają zmianie.</p>\n'
            '\n'
            '<h3>Pamięć związana z dowódcą</h3>\n'
            '<p>Nowe zrzuty ekranu są przypisywane do aktualnie grającego dowódcy na podstawie '
            'tożsamości dziennika obecnego w aktywnym stanie aplikacji na żywo.</p>\n'
            '<p>Struktura folderów zawiera nazwę dowódcy i identyfikator Frontier, na '
            'przykład:</p>\n'
            '<p><b>FABER38_F12520967/</b></p>\n'
            '<p>Dzięki FID zadanie jest jasne nawet w przypadku wielu dowódców. Pozwala to '
            'rozróżnić dwóch dowódców o tym samym nazwisku.</p>\n'
            '\n'
            '<h3>nazwy plików</h3>\n'
            '<p>Nowe przetworzone zdjęcia otrzymują nazwę z czasem wykonania, imieniem dowódcy i – '
            'jeśli jest dostępny – układem gwiezdnym znanym w kolejce.</p>\n'
            '<p>Przykład:</p>\n'
            '<p><b>2026-09-04_13-18-22_FABER38_Prua-Hypai-RB-D-c29-71.png</b></p>\n'
            '<p>FID znajduje się w nazwie folderu powiązanego z dowódcą, a nie ponownie w nazwie '
            'pliku obrazu.</p>\n'
            '\n'
            '<h3>Bezpieczne nazwy plików</h3>\n'
            '<p>CMDRHelper oczyszcza nazwy dowódców i systemów do wykorzystania jako składniki '
            'plików i folderów.</p>\n'
            '<p>Niedozwolona kontrola i znaki systemu Windows są zastępowane, białe znaki są '
            'ujednolicane, problematyczne kropki lub spacje końcowe są usuwane, a zastrzeżone '
            'nazwy systemu Windows, takie jak CON lub NUL, są zabezpieczane.</p>\n'
            '\n'
            '<h3>Czas nagrywania</h3>\n'
            '<p>Do nazewnictwa CMDRHelper wykorzystuje czas modyfikacji stabilnie rozpoznanego '
            'pliku BMP. Bieżący czas zostanie użyty tylko wtedy, gdy nie będzie można tego '
            'odczytać.</p>\n'
            '<p>Oznacza to, że nazwa zwykle zależy od pliku źródłowego, a nie od czasu późniejszej '
            'konwersji.</p>\n'
            '\n'
            '<h3>Wiele obrazów w tej samej sekundzie</h3>\n'
            '<p>Jeśli zamierzona nazwa pliku już istnieje lub jest zarezerwowana dla trwającej '
            'konwersji, CMDRHelper stale ją dodaje<code>_2</code>,<code>_3</code>,<code>_4</code>i '
            'tak dalej.</p>\n'
            '<p>Oznacza to, że kolejny zrzut ekranu z tym samym znacznikiem czasu nie zastąpi '
            'istniejącego obrazu docelowego.</p>\n'
            '\n'
            '<h3>Zmiana dowódcy w trakcie przetwarzania</h3>\n'
            '<p>Commander, FID i system są rejestrowane razem podczas umieszczania w kolejce '
            'zrzutu ekranu.</p>\n'
            '<p>Późniejsza zmiana dowódcy nie powoduje zmiany przypisania tego już oczekującego '
            'obrazu. Oznacza to, że zrzut ekranu FABER38 nie jest później zapisywany do folderu '
            'innego dowódcy.</p>\n'
            '\n'
            '<h3>galeria</h3>\n'
            '<p>Galeria pokazuje pliki PNG, JPG i JPEG z katalogów powiązanych z wybranym filtrem. '
            'Regularnie wykrywane są nowe, usunięte lub przeniesione obrazy.</p>\n'
            '<p>Filtr galerii nie zmienia lokalizacji przechowywania ani przypisania dowódcy '
            'plików.</p>\n'
            '\n'
            '<h3>Obecny dowódca</h3>\n'
            '<p>Filtr Obecny dowódca pokazuje obrazy z folderu dowódcy aktualnie przeglądanego w '
            'widoku CMDR.</p>\n'
            '<p>Dowódca, o którym mowa, decyduje jedynie o sposobie wyświetlania galerii. Z '
            'drugiej strony przypisanie nowego zrzutu ekranu na żywo wykorzystuje tożsamość '
            'dziennika aktywną podczas kolejkowania.</p>\n'
            '\n'
            '<h3>Wszyscy dowódcy</h3>\n'
            '<p>Filtr „Wszyscy dowódcy” pokazuje razem obrazy z prawidłowych podfolderów '
            'wszystkich znanych dowódców. Uwzględniany jest także specjalny folder na nagrania bez '
            'rozpoznanej tożsamości.</p>\n'
            '<p>Pliki nie są przenoszone ani łączone.</p>\n'
            '\n'
            '<h3>Nie przydzielono</h3>\n'
            '<p>Filtr Nieprzypisane wyświetla obsługiwane pliki obrazów znajdujące się '
            'bezpośrednio w udostępnionym docelowym folderze głównym.</p>\n'
            '<p>W szczególności widoczne pozostają starsze obrazy bez podfolderów związanych z '
            'dowódcą. CMDRHelper nie próbuje odgadnąć ich przynależności po fakcie.</p>\n'
            '\n'
            '<h3>Istniejące obrazy</h3>\n'
            '<p>Obrazy, które już istnieją w folderze głównym, nie są automatycznie przenoszone '
            'ani zmieniane ich nazwy.</p>\n'
            '<p>Pozostają one dostępne poprzez opcję „Nieprzypisane”, o ile są dostępne w formacie '
            'PNG, JPG lub JPEG.</p>\n'
            '\n'
            '<h3>Wybierz i wyświetl obraz</h3>\n'
            '<p>Proste kliknięcie obrazu podglądu powoduje wyświetlenie przeskalowanego obrazu w '
            'obszarze podglądu i wyświetlenie jego nazwy pliku.</p>\n'
            '<p>Podwójne kliknięcie otwiera plik z aplikacją systemu operacyjnego ustawioną dla '
            'obrazów.</p>\n'
            '<p>Można zaznaczyć wiele obrazów jednocześnie. Po zmianie rozmiaru okna podgląd '
            'bieżącego obrazu zostanie przeskalowany w celu dopasowania.</p>\n'
            '\n'
            '<h3>Usuń obraz</h3>\n'
            '<p>Zaznaczone obrazy można usunąć za pomocą przycisku „Usuń wybrane” lub klawisza '
            'Usuń. Przed usunięciem pojawia się zapytanie zabezpieczające; W przypadku braku '
            'selekcji najpierw wskazywany jest niezbędny wybór.</p>\n'
            '<p>Z katalogów bieżącego filtra galerii zostaną usunięte tylko wybrane pliki docelowe '
            'PNG/JPG/JPEG. Nie ma to wpływu na oryginalny plik źródłowy BMP.</p>\n'
            '\n'
            '<h3>Otwórz folder docelowy</h3>\n'
            '<p>„Otwórz folder docelowy” otwiera lokalizację przechowywania w menedżerze plików i, '
            'jeśli to konieczne, tworzy współdzielony folder główny.</p>\n'
            '<p>Filtr „Aktualny dowódca” otwiera istniejący podfolder dowódcy. Jeśli jeszcze nie '
            'istnieje lub aktywny jest inny filtr, zostanie otwarty współdzielony folder '
            'główny.</p>\n'
            '\n'
            '<h3>Bezpieczeństwo ścieżek obrazowych</h3>\n'
            '<p>Przed usunięciem CMDRHelper sprawdza ścieżkę kanoniczną każdego pliku. Musi '
            'znajdować się w skonfigurowanym folderze docelowym i bezpośrednio w katalogu '
            'dozwolonym przez bieżący filtr galerii.</p>\n'
            '<p>Dowiązania symboliczne nie są używane jako foldery poleceń ani obrazy galerii i '
            'nie są usuwane za pośrednictwem galerii. Ścieżki poza obszarem docelowym i ścieżki '
            'przejścia są odrzucane.</p>\n'
            '\n'
            '<h3>Jeśli nie wykryto żadnego dowódcy</h3>\n'
            '<p>Jeśli podczas kolejkowania nowego nagrania brakuje Commandera i FID, plik nie '
            'zostanie wstrzymany i nie zostanie przypisany do znanego Commandera.</p>\n'
            '<p>Będzie w podfolderze<b>NIEZNANY_NIEZNANY/</b>obrobiony; nazwa pliku używana '
            'również w przypadku Commandera<b>NIEZNANY</b>. Folder ten można przeglądać poprzez '
            'opcję Wszystkie dowódcy, a nie poprzez filtr Nieprzydzielonego folderu głównego.</p>\n'
            '\n'
            '<h3>Kilku dowódców</h3>\n'
            '<p>Do zarządzania wizerunkiem odnoszą się dwie odrębne zasady:</p>\n'
            '<ul>\n'
            '<li><b>Zapisz nowe obrazy:</b>Aktywna tożsamość dziennika z programem Commander i FID '
            'po umieszczeniu w kolejce określa folder docelowy.</li>\n'
            '<li><b>Zobacz obrazy:</b>Wyświetlane przez dowódcę lub wybrany filtr galerii określa '
            'widoczne obrazy.</li>\n'
            '</ul>\n'
            '<p>Oznacza to, że galerię innego dowódcy można przeglądać podczas gry w FABER38, bez '
            'konieczności umieszczania nowych zrzutów ekranu w folderze danego dowódcy.</p>\n'
            '\n'
            '<h3>Wskazówka</h3>\n'
            '<p>Wystarczy udostępniony folder główny zrzutów ekranu. CMDRHelper automatycznie '
            'rozdziela nowo przetworzone obrazy na Commander i FID.</p>\n'
            '<p>Za pomocą opcji „Aktualny dowódca”, „Wszyscy dowódcy” i „Nieprzypisane” możesz '
            'przełączać się między galerią osobistą, podfolderami wszystkich dowódców i starszymi '
            'obrazami w folderze głównym.</p>\n'
            '<p>Wyższa jasność może pomóc w przypadku ciemnych zdjęć; wpływa to na nowo utworzony '
            'obraz docelowy podczas konwersji.</p>'),
 'commander_view': ('Widok CMDR',
                    '<h2>Widok CMDR</h2>\n'
                    '<p>Widok CMDR podsumowuje trwale przechowywane dane osobowe dowódcy.</p>\n'
                    '<p>Umożliwia także przełączanie pomiędzy znanymi dowódcami CMDRHelper i '
                    'przeglądanie ich własnych danych. Dane osobowe oddzielane są za pomocą '
                    'identyfikatora Frontier (FID).</p>\n'
                    '\n'
                    '<h3>Wybierz Dowódcę</h3>\n'
                    '<p>Jeśli znanych jest kilku dowódców, możesz skorzystać z powyższej opcji, '
                    'aby określić, czyje zapisane informacje będą wyświetlane. Ten dowódca jest '
                    'uważany za dowódcę.</p>\n'
                    '<p>Na wyświetlaczu jest to oznaczone jako „Live Active” lub „View Only”.</p>\n'
                    '\n'
                    '<h3>Uważany za dowódcę i dowódcę na żywo</h3>\n'
                    '<p>Wybranie innego dowódcy w widoku CMDR nie czyni go aktywnym dowódcą '
                    'dziennika.</p>\n'
                    '<p>Dowódca na żywo jest ustalany wyłącznie na podstawie aktualnie '
                    'jednoznacznie zidentyfikowanej sesji dziennika Elite Dangerous. W ten sposób '
                    'można przeglądać historię innego dowódcy, podczas gdy Elite Dangerous będzie '
                    'nadal działać z FABER38.</p>\n'
                    '\n'
                    '<h3>Identyfikator Frontier (FID)</h3>\n'
                    '<p>FID to stabilny identyfikator dowódcy Frontier.</p>\n'
                    '<p>CMDRHelper wykorzystuje go i wyodrębniony z niego wewnętrzny identyfikator '
                    'dowódcy, aby bezpiecznie oddzielić dane osobowe. Dowódcy o podobnych lub '
                    'identycznych nazwiskach również pozostają rozdzieleni.</p>\n'
                    '\n'
                    '<h3>Przegląd</h3>\n'
                    '<p>Zakładka „Przegląd” pokazuje tylko zapisane na stałe informacje dotyczące '
                    'danego dowódcy:</p>\n'
                    '<ul>\n'
                    '<li>Nazwa dowódcy, FID i status „Na żywo aktywny” lub „Tylko '
                    'przeglądanie”</li>\n'
                    '<li>pierwszy i ostatni znany raz</li>\n'
                    '<li>Liczba odwiedzonych systemów, odkryć biologicznych i geograficznych, '
                    'wpisów do kodeksu i sprzedaży kartografii</li>\n'
                    '<li>Ostatnia znana lokalizacja i liczba otwartych misji</li>\n'
                    '<li>obecny lub ostatni statek</li>\n'
                    '<li>Fleet Carrier i lokalizacja przewoźnika</li>\n'
                    '<li>Aktywa</li>\n'
                    '<li>otwarte dane osobowe i otwarte dane kartograficzne, w tym istniejące '
                    'szacunki</li>\n'
                    '</ul>\n'
                    '\n'
                    '<h3>Aktywa/Kredyty</h3>\n'
                    '<p>Pole „Aktywa” pokazuje ostatnio zapisane saldo kredytowe danego dowódcy z '
                    'odpowiedniego zdarzenia w dzienniku, w formacie np.<b>1 234 567 kr</b>.</p>\n'
                    '<p>CMDRHelper nie dodaje fikcyjnych dochodów ani wydatków, jeśli nie ma '
                    'nowego, bezpiecznego statusu dziennika.</p>\n'
                    '\n'
                    '<h3>Monety najemników</h3>\n'
                    '<p>Monety najemników pochodzą z pól MercCoins dostarczonych przez Elite '
                    'Dangerous<code>Statistics → Bank_Account</code>i są zapisywane dla dowódcy '
                    'jako migawka Frontier.</p>\n'
                    '<p>Widoczne są:</p>\n'
                    '<ul>\n'
                    '<li>Aktualny</li>\n'
                    '<li>Razem wydane</li>\n'
                    '<li>Inżynieria</li>\n'
                    '<li>sprzęt</li>\n'
                    '<li>Zgłoszone przez Frontier: zarobione ogółem</li>\n'
                    '</ul>\n'
                    '\n'
                    '<h3>Aktualne i wydania</h3>\n'
                    '<p>„Aktualne” spektakle<code>MercCoins_Current</code>. „Całkowite wydane” '
                    'przejmuje kontrolę<code>MercCoins_Total_Spent</code>.</p>\n'
                    '<p>„Inżynieria” i „Sprzęt” pokazują udziały zgłoszone oddzielnie przez '
                    'Frontier<code>MercCoins_Spent_On_Engineering</code>I<code>MercCoins_Spent_On_MercGear</code>.</p>\n'
                    '<p>Dla przykładu FABER38 aktualny stan magazynowy<b>1275</b>w '
                    'sumie<b>220</b>spędzony i odszedł<b>220</b>zgłoszony do inżynierii.</p>\n'
                    '\n'
                    '<h3>Ogólnie zasłużone</h3>\n'
                    '<p>Pokazuje się „Zgłoszone przez Frontier: ogólnie '
                    'zarobione”.<code>MercCoins_Total_Earned</code>. CMDRHelper nie oblicza na tej '
                    'podstawie własnego bilansu.</p>\n'
                    '<p>Wartość skumulowana Frontier nie musi być matematycznie zgodna z bieżącym '
                    'stanem magazynowym i wykazanymi wydatkami. Na przykład jednocześnie można '
                    'zgłosić 1275 bieżących, 25 zarobionych ogółem i 220 wydanych ogółem.</p>\n'
                    '<p>CMDRHelper nie koryguje tych wartości, ale wyświetla poszczególne liczniki '
                    'Frontier bez zmian.</p>\n'
                    '\n'
                    '<h3>Dlaczego nie mieć własnego bilansu MercCoins?</h3>\n'
                    '<p>Elite Dangerous nie zapewnia unikalnego zapisu w dzienniku dla każdego '
                    'indywidualnego otrzymania lub wydania monet najemników. MercCoins pojawiają '
                    'się jako sumy w Statistics.</p>\n'
                    '<p>W związku z tym samodzielnie obliczona historia rezerwacji nie byłaby '
                    'wiarygodna. Zamiast tego CMDRHelper zapisuje najnowszą znaną migawkę '
                    'Frontier.</p>\n'
                    '\n'
                    '<h3>Misje</h3>\n'
                    '<p>Zakładka „Misje” pokazuje zapisane misje danego dowódcy w formie tabeli ze '
                    'statusem, nazwą misji, celem, czasem wygaśnięcia i nagrodą.</p>\n'
                    '\n'
                    '<h3>badanie</h3>\n'
                    '<p>Karta Eksploracja pokazuje otwarte dane biologiczne, otwarte dane '
                    'kartograficzne, odkrycia biologiczne, pierwsze kroki, samodzielnie i '
                    'skutecznie zmapowane ciała oraz liczbę odwiedzonych systemów.</p>\n'
                    '<p>Dedykowana zakładka „Kronika” w widoku CMDR jest obecnie nadal elementem '
                    'zastępczym. Pełną kronikę znajdziesz w pozycji menu głównego o tej samej '
                    'nazwie.</p>\n'
                    '\n'
                    '<h3>Statki/Flota</h3>\n'
                    '<p>Zakładka „Statki” początkowo pokazuje aktywny lub ostatnio używany statek '
                    'z nazwą statku, typem statku, lokalizacją i identyfikatorem statku.</p>\n'
                    '<p>Zapisane statki danego dowódcy pojawiają się pod nimi jako karty '
                    'rozszerzalne. Można je sortować rosnąco lub malejąco według:</p>\n'
                    '<ul>\n'
                    '<li>ostatnio lub obecnie używany</li>\n'
                    '<li>Nazwa statku lub typ statku</li>\n'
                    '<li>maksymalny zasięg skoku</li>\n'
                    '<li>Ładowność lub masa pusta</li>\n'
                    '<li>ostatnia znana lokalizacja lub czas</li>\n'
                    '</ul>\n'
                    '<p>Możesz także filtrować według wszystkich statków, statków z hangarem '
                    'samochodowym lub statków z hangarem myśliwskim.</p>\n'
                    '\n'
                    '<h3>Szczegóły statku</h3>\n'
                    '<p>Otwarta mapa statku pokazuje – jeśli została zapisana – identyfikator '
                    'statku, identyfikator statku, lokalizację, ostatni czas, maksymalny zasięg '
                    'skoku, wzmacniacz FSD i Guardian, masę, pojemność ładunku i zbiornika, a '
                    'także czas i status załadunku.</p>\n'
                    '<p>Jeśli dostępne są dane modułów, podsumowane są także hangar pojazdów i '
                    'myśliwców, generator tarcz i wzmacniacz tarcz, wzmocnienia tarcz Strażników, '
                    'broń, wzmocnienia kadłuba i modułów oraz kabiny pasażerskie.</p>\n'
                    '<p>Stan ładowania może być kompletny, niekompletny lub nieaktualny. Brakujące '
                    'informacje są wyświetlane jako „–” i nie są uzupełniane.</p>\n'
                    '\n'
                    '<h3>Fleet Carrier</h3>\n'
                    '<p>W przypadku zapisanego niestandardowego Fleet Carrier widok pokazuje nazwę '
                    'operatora, znak wywoławczy, identyfikator operatora, ostatnią lokalizację i '
                    'czas ostatniej aktualizacji.</p>\n'
                    '\n'
                    '<h3>Trwały stan dowódczy</h3>\n'
                    '<p>Ważne informacje o dowódcy pozostają trwale zapisane. Umożliwia to ponowne '
                    'wyświetlenie znanych wartości po ponownym uruchomieniu CMDRHelper lub Elite '
                    'Dangerous bez konieczności ponownego pełnego oceniania każdego '
                    'dziennika.</p>\n'
                    '<p>Nowe unikalne zdarzenia w dzienniku aktualizują zapisany stan.</p>\n'
                    '\n'
                    '<h3>Rekonstrukcja historyczna</h3>\n'
                    '<p>W przypadku funkcji dodanych później CMDRHelper może jednorazowo '
                    'przeszukiwać istniejące obszary dziennika, które są wyraźnie przypisane do '
                    'dowódcy, w celu uzyskania już znanych informacji.</p>\n'
                    '<p>Można na przykład zastosować starsze migawki MercCoins. Powtarzane '
                    'kontrole nie mają na celu tworzenia duplikatów danych i nie zmieniają '
                    'normalnych pozycji odczytu dziennika.</p>\n'
                    '\n'
                    '<h3>Kilku dowódców</h3>\n'
                    '<p>W szczególności pod względem dowódców odrębne pozostają:</p>\n'
                    '<ul>\n'
                    '<li>Zasoby i misje</li>\n'
                    '<li>własna kartografia i znaleziska organiczne</li>\n'
                    '<li>Historia górnictwa odkrywkowego i monety najemników</li>\n'
                    '<li>Dane uwierzytelniające online</li>\n'
                    '<li>zrzuty ekranu związane z dowódcą</li>\n'
                    '</ul>\n'
                    '<p>Globalne właściwości astronomiczne układu lub ciała można jednak '
                    'wykorzystać łącznie.</p>\n'
                    '\n'
                    '<h3>Wpływ na inne poglądy</h3>\n'
                    '<p>Zmiana danego dowódcy aktualizuje sam widok CMDR, osobisty wybór surowców '
                    'wydobywczych w kronice oraz, przy odpowiednim filtrze, galerię zrzutów '
                    'ekranu.</p>\n'
                    '<p>Nie zastępuje rzeczywistego dowódcy na żywo do przetwarzania dzienników '
                    'lub przesyłania online.</p>\n'
                    '\n'
                    '<h3>Inara i EDSM</h3>\n'
                    '<p>Dostępami Inara i EDSM zarządza się oddzielnie, odpowiednio dla każdego '
                    'dowódcy i FID.</p>\n'
                    '<p>Samo spojrzenie na dowódcę nie rozpoczyna transmisji za pomocą API-Key. '
                    'Tylko aktywny dziennik FID jest istotny dla przesyłania na żywo.</p>\n'
                    '<p>Zarządzanie danymi dostępowymi odbywa się w „Ustawieniach” w obszarze '
                    'usług online.</p>\n'
                    '\n'
                    '<h3>Wskazówka</h3>\n'
                    '<p>Użyj widoku CMDR, jeśli chcesz zobaczyć zapisane dane osobowe konkretnego '
                    'dowódcy.</p>\n'
                    '<p><b>Widok CMDR = Kogo chcę przeglądać?</b></p>\n'
                    '<p><b>Active Journal-FID = Kto właściwie teraz gra?</b></p>\n'
                    '<p>To rozdzielenie zapobiega mieszaniu danych osobowych lub plików '
                    'przesyłanych online od różnych dowódców.</p>'),
 'settings': ('Ustawienia',
              '<h2>Ustawienia</h2>\n<h3>CMDRHelper v3.2</h3>\n<p>Lepsza informacja o aktualizacji: okno Tak/Nie pokazuje wersję zainstalowaną i dostępną oraz do sześciu zmian, jeśli istnieje podsumowanie. Długie listy można przewijać, a działania pozostają dostępne. Widok jest instalowany z v3.2; niezmieniony klient v3.1 jeszcze go nie pokazuje.</p>\n'
              '<p>Obszar „Ustawienia” określa sposób współpracy CMDRHelper z Elite Dangerous, '
              'plikami dziennika, bazą danych, usługami online, interfejsem i aktualizacjami.</p>\n'
              '<p>Zmiany poświadczeń i ścieżek należy wprowadzać ostrożnie. W razie potrzeby '
              'ustawieniami związanymi z dowódcą zarządza się oddzielnie za pomocą identyfikatora '
              'Frontier.</p>\n'
              '\n'
              '<h3>dziennik</h3>\n'
              '<p>Folder dziennika jest jednym z najważniejszych ustawień. Musi wskazywać folder, '
              'w którym znajduje się plik Elite Dangerous<code>Dziennik*.log</code>pliki używanego '
              'profilu Windows lub Proton.</p>\n'
              '<p>W czasopismach podaje się m.in.:</p>\n'
              '<ul>\n'
              '<li>Tożsamość dowódcy, lokalizacja i podróż</li>\n'
              '<li>Misje, statki i zasoby</li>\n'
              '<li>Dane eksploracyjne, kartograficzne i BIO</li>\n'
              '<li>Górnictwo odkrywkowe, monety najemników i inne obsługiwane stany</li>\n'
              '</ul>\n'
              '\n'
              '<h3>Wyświetlanie i obsługa dziennika</h3>\n'
              '<p>Grupa dzienników pokazuje zestaw folderów, liczbę znalezionych dzienników, '
              'najstarsze i najnowsze dzienniki, nazwę najnowszego pliku i godzinę ostatniego '
              'przeczytanego wpisu.</p>\n'
              '<p>„Wybierz folder dziennika” zmienia folder. „Przeczytaj teraz” natychmiast '
              'uruchamia normalną aktualizację.</p>\n'
              '<p>Wyraźnie identyfikowalne sesje są przypisywane za pomocą FID. Nowe kompletne '
              'wpisy są przetwarzane przyrostowo; Bezpieczne pozycje odczytu zapobiegają '
              'niepotrzebnemu ponownemu odczytaniu każdego dziennika w całości przy następnym '
              'uruchomieniu.</p>\n'
              '\n'
              '<h3>baza danych</h3>\n'
              '<p>CMDRHelper trwale przechowuje wymagane dane w lokalnej bazie danych SQLite. '
              'Obejmuje to globalne dane dotyczące systemu i ciała, a także informacje wyraźnie '
              'przypisane dowódcy.</p>\n'
              '<p>Strona ustawień pokazuje statystyki dotyczące zapisanych danych. Bazy danych nie '
              'należy edytować ręcznie podczas działania CMDRHelper.</p>\n'
              '\n'
              '<h3>Importuj archiwum czasopism</h3>\n'
              '<p>„Importuj archiwum dziennika” całkowicie porównuje pliki dziennika w ustawionym '
              'folderze dziennika z bazą danych. Znane już obszary dziennika są brane pod uwagę na '
              'podstawie zapisanych informacji importowych i nie są ślepo powielane jako nowe '
              'dane.</p>\n'
              '<p>Podczas ręcznie widocznego importu wyświetlany jest postęp, liczba i aktualnie '
              'przetwarzany plik. Po zakończeniu CMDRHelper zgłasza zaimportowane lub już znane '
              'dane lub błąd.</p>\n'
              '<p>Import archiwum służy także do ponownego uczenia się obsługiwanych informacji '
              'historycznych z wyraźnie przypisanych czasopism.</p>\n'
              '\n'
              '<h3>Dane dotyczące dowódcy</h3>\n'
              '<p>CMDRHelper oddziela dane osobowe w oparciu o FID i powiązany wewnętrzny '
              'identyfikator dowódcy. Należą do nich między innymi misje, zasoby, MercCoins, '
              'eksploracja osobista i dostęp online.</p>\n'
              '<p>Nieznana lub niejednoznaczna sesja dziennika nie może być arbitralnie przypisana '
              'dowódcy.</p>\n'
              '\n'
              '<h3>Usługi internetowe</h3>\n'
              '<p>CMDRHelper obsługuje EDSM i Inara. Obydwa dostępy są przetwarzane i zapisywane '
              'oddzielnie dla każdego znanego dowódcy lub każdego FID.</p>\n'
              '<p>Wybór w ustawieniach określa jedynie, czyj dostęp jest aktualnie edytowany lub '
              'testowany. Tylko dowódca wyraźnie zidentyfikowany przez aktywną sesję dziennika '
              'może wysyłać na żywo.</p>\n'
              '\n'
              '<h3>Dostęp EDSM dla</h3>\n'
              '<p>„EDSM dostęp dla:” wybiera dowódcę do edycji. Wybór pokaże „ustawiony” lub „nie '
              'skonfigurowany” w zależności od tego, czy przechowywany jest API-Key.</p>\n'
              '<p>Widoczne są nazwa dowódcy, ukryte pole API-Key, „Use EDSM”, test połączenia oraz '
              'jego ostatni status testu.</p>\n'
              '<p>Każdy dowódca potrzebuje własnego odpowiedniego dostępu EDSM. Wybór nie powoduje '
              'przełączenia modułu przesyłającego na żywo na tego dowódcę.</p>\n'
              '\n'
              '<h3>Użyj i przetestuj EDSM</h3>\n'
              '<p>„Użyj EDSM” włącza lub wyłącza usługę dla wybranego FID. Brakujące lub '
              'dezaktywowane poświadczenia nie mają wpływu na przetwarzanie dziennika '
              'lokalnego.</p>\n'
              '<p>„Testuj połączenie EDSM” sprawdza dane dostępowe aktualnie widoczne w '
              'formularzu. Pomyślny test potwierdza połączenie, ale nie powoduje zmiany aktywnego '
              'dziennika FID ani aktywnego dowódcy.</p>\n'
              '\n'
              '<h3>Dostęp Inara dla</h3>\n'
              '<p>„Inara Dostęp dla:” działa zgodnie z tą samą zasadą wielu CMDR. Aktywacja, nazwa '
              'dowódcy Inara i API-Key są zapisywane osobno dla każdego FID.</p>\n'
              '<p>Również tutaj wybór pokazuje „skonfigurowany” lub „nie skonfigurowany”. Klucz '
              'jednego dowódcy nie jest automatycznie używany przez innego dowódcę.</p>\n'
              '\n'
              '<h3>Użyj i przetestuj Inara</h3>\n'
              '<p>Po skonfigurowaniu i włączeniu Inara dla aktywnego dziennika FID, CMDRHelper '
              'może przesyłać obsługiwane zdarzenia związane z podróżą, lokalizacją, misją i '
              'statkiem. Nie każde zdarzenie dziennika jest wysyłane do Inara.</p>\n'
              '<p>„Testuj połączenie Inara” sprawdza aktualnie widoczne dane dostępowe bez zmiany '
              'aktualnego dowódcy.</p>\n'
              '\n'
              '<h3>Skrzynka nadawcza Inara</h3>\n'
              '<p>Obsługiwane zdarzenia Inara są trwale oznaczane w skrzynce nadawczej przed '
              'transmisją sieciową.</p>\n'
              '<p>Błędy tymczasowe umożliwiają zachowanie tych wpisów do późniejszych prób. Proces '
              'roboczy przetwarza jedynie skrzynkę nadawczą jednoznacznie aktywnego dziennika FID; '
              'Wpisy od innych dowódców nie są uwzględniane.</p>\n'
              '\n'
              '<h3>Stan online w nagłówku</h3>\n'
              '<p>EDSM obecnie pokazuje:</p>\n'
              '<ul>\n'
              '<li><b>EDSM</b>– nie można używać ani dezaktywować dla aktywnego FID</li>\n'
              '<li><b>EDSM czeka</b>– skonfigurowane i bez bieżącej transmisji</li>\n'
              '<li><b>Przekładnia EDSM</b>– ostatni przebieg przetwarzania EDSM zakończył się bez '
              'błędów; Etykietka informuje, czy zdarzenia zostały wysłane, dane dziennika zostały '
              'przetworzone lub nie znaleziono nowych danych</li>\n'
              '<li><b>Błąd EDSM</b>– ostatni status transmisji jest nieprawidłowy</li>\n'
              '</ul>\n'
              '<p>Obecnie nie ma dodatkowego, oddzielnie oznaczonego stanu „EDSM aktywny” dla '
              'EDSM.</p>\n'
              '<p>Inara rozróżnia bardziej precyzyjnie:</p>\n'
              '<ul>\n'
              '<li><b>INARA odpada</b>– wyłączone dla aktywnego dziennika FID</li>\n'
              '<li><b>INARA gotowa</b>– skonfigurowane, ale nadal bez potwierdzonej transmisji w '
              'tej sesji</li>\n'
              '<li><b>Przekładnia INARA</b>– pracownik aktualnie wysyła</li>\n'
              '<li><b>INARA aktywna</b>– ostatni faktyczny przelew został pomyślnie '
              'potwierdzony</li>\n'
              '<li><b>Błąd INARY</b>– ostatnia próba transferu nie powiodła się</li>\n'
              '</ul>\n'
              '\n'
              '<h3>Zabezpieczenie API-Key</h3>\n'
              '<p>API-Key to dane uwierzytelniające osobiste. Pola wejściowe są ukryte; Są one '
              'przechowywane w ustawieniach aplikacji, a nie w bazie danych CMDRHelper, związanej '
              'z dowódcą.</p>\n'
              '<p>Kluczy nie należy publikować, udostępniać na zrzutach ekranu ani dodawać do '
              'publicznych repozytoriów.</p>\n'
              '\n'
              '<h3>Obrazy/zrzuty ekranu</h3>\n'
              '<p>Folder źródłowy, folder docelowy, PNG/JPG, automatyczne przetwarzanie, usuwanie '
              'BMP i rozjaśnianie od 0 do 50 procent znajdują się wyłącznie w głównym menu Obrazy, '
              'a nie na stronie Ustawienia.</p>\n'
              '<p>Pomoc kontekstowa „Obrazy” szczegółowo opisuje te opcje.</p>\n'
              '\n'
              '<h3>powierzchnia</h3>\n'
              '<p>Grupa interfejsów obejmuje wygląd, język, czcionkę, rozmiar czcionki i próg '
              'wartości dla wartościowych treści eksploratora.</p>\n'
              '\n'
              '<h3>Tryb ciemny i jasny</h3>\n'
              '<p>Możesz bezpośrednio przełączać się pomiędzy ciemnym i jasnym wyglądem. Motyw '
              'jest natychmiast stosowany do interfejsu oraz istniejących kart systemowych i '
              'historycznych i zapisywany.</p>\n'
              '\n'
              '<h3>Język</h3>\n'
              '<p>Interfejs oferuje dwanaście języków do wyboru. „Zapisz język” zapisuje wybór; W '
              'takim przypadku wymagane jest ponowne uruchomienie CMDRHelper, aby uzyskać '
              'całkowicie jednolitą konwersję istniejących widżetów.</p>\n'
              '\n'
              '<h3>Czcionka i jej rozmiar</h3>\n'
              '<p>Można wybrać i zapisać rodzinę czcionek i rozmiar czcionki od 7 do 24 pkt.</p>\n'
              '<p>Obie zmiany zaczną w pełni obowiązywać dopiero po ponownym uruchomieniu. '
              'Interfejs wyraźnie to wskazuje.</p>\n'
              '\n'
              '<h3>Próg wartości</h3>\n'
              '<p>Próg wartości Eksploratora określa szacunkową wartość kredytu, od której '
              'wyróżniane są ciała szczególnie wartościowe. Zmiana zostanie natychmiast zapisana i '
              'zaktualizuje odpowiedni wyświetlacz Eksploratora.</p>\n'
              '\n'
              '<h3>Automatyczne ukrywanie</h3>\n'
              '<p>„Precious Bodies” i „BIO Finds” są na stałe umieszczone na lewym pasku bocznym, '
              'a nie na stronie Ustawienia.</p>\n'
              '<p>Przełączniki są zapisywane i kontrolują obsługiwane małe okna podpowiedzi na '
              'żywo podczas eksploracji. Próg wartości dla Wartościowych Ciał ustawia się w '
              'ustawieniach interfejsu.</p>\n'
              '\n'
              '<p>Okno Cargo używa wyłącznie snapshotu Cargo potwierdzonego dla aktywnej Journal-FID. Commander oglądany w CMDR View oraz viewed_commander_id nie wpływają na to okno live. Dla Ship wyświetlane jest zajęte / maksymalne · wolne; jeśli CargoCapacity jest nieznana, wartość nie jest szacowana.</p>\n'
              '<p>„HUD statusu EDSM” w „pokazuj automatycznie” jest domyślnie WYŁĄCZONY. Po wejściu do systemu nad Elite pojawia się komunikat na około 2,5 sekundy. Kolejne zdarzenia Location podczas tego samego pobytu nie dublują komunikatów; prawdziwy powrót pozwala sprawdzić system ponownie.</p>\n<p>„EDSM: ZNANY” oznacza prawidłowy wynik EDSM dla systemu. „EDSM: NIEZNANY” oznacza prawidłową odpowiedź EDSM bez wyniku dla systemu. „EDSM: BRAK ODPOWIEDZI” oznacza błąd sieci, HTTP, przekroczenie czasu lub nieprawidłową odpowiedź, nigdy potwierdzony brak wyniku. Obecność w EDSM nie jest oficjalnym odkryciem w Elite; nie obiecuje się nazw pierwszych odkrywców ani zgłaszających.</p>\n<p>Komunikat działa niezależnie od HUD nawigacji i ładowni. Stałe wskazania HUD i komunikaty szybkiego ulubionego pozostają zachowane. Zapytanie nie blokuje interfejsu; opóźnione odpowiedzi dotyczące opuszczonych już systemów są odrzucane.</p>\n\n'
              '<h3>Aktualizacje</h3>\n'
              '<p>Grupa aktualizacji pokazuje zainstalowaną wersję i stan GitHub. Sprawdź teraz '
              'ręcznie sprawdza dostępność nowej zaplanowanej wersji CMDRHelper; Ponadto po '
              'uruchomieniu następuje opóźniona automatyczna kontrola.</p>\n'
              '<p>Jeśli dostępna jest nowa wersja, CMDRHelper zapyta przed pobraniem i instalacją. '
              'Zapowiedziana aktualizacja bazy danych jest pokazywana osobno w tym oknie '
              'dialogowym.</p>\n'
              '<p>W istniejących instalacjach zwykle wystarczy: zainstalować aktualizację → uruchomić CMDRHelper. Niezbędne historyczne poprawki danych BIO, wizyt i metadanych DSS wykonują się automatycznie; przed naprawami zapisującymi dane powstaje kopia zapasowa bazy. Naprawy są wersjonowane i idempotentne: pomyślnych rewizji nie wykonuje się w całości przy każdym starcie. Odtworzenie wymaga dzienników Elite, które nadal istnieją, są czytelne i jednoznacznie przypisane do commandera. Brakujące źródła nie są wymyślane ani uznawane za sukces; niedokończone naprawy są ponawiane przy kolejnym starcie. Zwykle nie potrzeba usuwania bazy, ręcznych skryptów ani ponownego importu.</p>\n\n'
              '<h3>Pobierz postęp</h3>\n'
              '<p>Pobieranie przebiega w tle. Jeśli znany jest całkowity rozmiar, CMDRHelper '
              'pokazuje nazwę pliku, otrzymane i całkowite MiB, procent, szybkość transferu i '
              'szacowany pozostały czas.</p>\n'
              '<p>Bez znanego całkowitego rozmiaru pasek postępu działa w trybie zajętym i nadal '
              'pokazuje ilość odebranych danych oraz – jeśli można to określić – szybkość. Przed '
              'instalacją sprawdzany jest pobrany plik ZIP.</p>\n'
              '\n'
              '<h3>Anuluj aktualizację</h3>\n'
              '<p>„Anuluj pobieranie” kończy trwające pobieranie w kontrolowany sposób. Przerwane, '
              'niekompletne lub nieprawidłowe pobieranie nie zostanie zainstalowane.</p>\n'
              '\n'
              '<h3>Zaktualizuj w systemie Windows</h3>\n'
              '<p>W systemie Windows rzeczywisty proces aktualizacji jest kontynuowany niezależnie '
              'od oryginalnej konsoli startowej. Dlatego zamknięcie konsoli nie powinno jej '
              'przypadkowo zakończyć.</p>\n'
              '<p>Jeżeli po rozpoczęciu zmian w plikach wystąpi błąd, istniejąca kopia zapasowa '
              'typu rollback podejmie próbę przywrócenia poprzedniej wersji.</p>\n'
              '\n'
              '<h3>Uruchom ponownie po aktualizacji</h3>\n'
              '<p>Po udanej instalacji aktualizator CMDRHelper uruchamia się ponownie zgodnie z '
              'zamierzoną ścieżką startową i krótko sprawdza, czy nowy proces działa '
              'stabilnie.</p>\n'
              '<p>Jeśli wydanie wymaga jednorazowej aktualizacji bazy danych, archiwum dziennika '
              'również zostanie ponownie ocenione po ponownym uruchomieniu.</p>\n'
              '\n'
              '<h3>Kilku dowódców</h3>\n'
              '<p><b>Wybór ustawień = Czyj dostęp online edytuję?</b></p>\n'
              '<p><b>Active Journal-FID = Kto może transmitować na żywo?</b></p>\n'
              '<p>Ani wybór konta online, ani widok CMDR nie pozwalają na przełączenie osoby '
              'przesyłającej na żywo na dowódcę tylko do przeglądania.</p>\n'
              '\n'
              '<h3>Pomoc</h3>\n'
              '<p>„? Pomoc” znajduje się na lewym pasku bocznym nad „auto pokazem” i otwiera pomoc '
              'aktualnie widocznego obszaru menu głównego.</p>\n'
              '<p>W obszarze „Ustawienia” przycisk otwiera bezpośrednio pomoc dotyczącą '
              'ustawień.</p>\n'
              '\n'
              '<h3>Wskazówka</h3>\n'
              '<p>Jeśli przeprowadzasz ponowną instalację lub masz problemy, sprawdź '
              'najpierw:</p>\n'
              '<ul>\n'
              '<li>prawidłowy folder dziennika i rozpoznana tożsamość dowódcy</li>\n'
              '<li>żądany język, motyw, czcionka i próg wartości eksploratora</li>\n'
              '<li>Dostęp online do prawidłowego FID</li>\n'
              '<li>W przypadku problemów z obrazem, foldery źródłowe i docelowe w menu głównym '
              '„Obrazy”.</li>\n'
              '</ul>\n'
              '<p>Jeśli jest kilku dowódców, zawsze zwracaj uwagę, którego FID dotyczą widoczne '
              'dane dostępowe online.</p>'),
    "planet_navigation": (
        'Nawigacja planetarna',
        """<h2>Nawigacja planetarna</h2>
<p>Nawigator planetarny służy wyłącznie do dolotu do określonej szerokości/długości geograficznej na planecie lub księżycu. Podajesz cel za pomocą współrzędnych i otrzymujesz odległość oraz kierunek do niego.</p>
<p>Nie jest to planer tras międzygwiezdnych i nie obsługuje nawigacji między systemami ani skoków. Samodzielnie pilotujesz statek.</p>

<h3>Otwieranie nawigatora i wprowadzanie celu</h3>
<p>W przeglądzie otwórz „Nawigacja planetarna” i wybierz „Wprowadzanie ręczne …”.</p>
<ul>
<li><b>Ciało niebieskie:</b> Wybierz docelową planetę lub księżyc z listy albo użyj już rozpoznanego ciała. Możesz też samodzielnie wpisać jego nazwę, jeśli jeszcze nie ma go na liście. W razie wątpliwości użyj pełnej nazwy wraz z nazwą systemu.</li>
<li><b>Szerokość geograficzna:</b> Podaj szerokość celu między −90° a +90°.</li>
<li><b>Długość geograficzna:</b> Podaj długość celu między −180° a +180°. Zwróć uwagę na znak obu współrzędnych.</li>
<li><b>Nazwa celu:</b> Opcjonalnie możesz podać nazwę, aby łatwiej rozpoznać cel.</li>
</ul>
<p>„Ustaw cel” zatwierdza wprowadzone dane. Nie musisz wpisywać technicznych identyfikatorów takich jak BodyID i SystemAddress; nie są to zwykłe dane wprowadzane przez użytkownika.</p>

<h3>Kiedy uruchamia się kompas?</h3>
<p>Gdy cel jest ustawiony, a Elite dostarcza prawidłowe planetarne dane pozycji dla odpowiedniego ciała, nawigacja włącza się automatycznie. Nie musisz naciskać osobnego przycisku startu.</p>
<p>Jeśli tych danych jeszcze brakuje lub dotyczą innego ciała, nawigator czeka z komunikatem „Oczekiwanie na współrzędne planetarne …”. Cel można wprowadzić jeszcze przed otrzymaniem tych danych.</p>

<h3>Globus planety: ponad 380 km</h3>
<p>Gdy odległość do celu jest większa niż 380 km, nawigator wyświetla globus planety.</p>
<ul>
<li><b>Biały okrąg</b> oznacza twoją pozycję.</li>
<li><b>Mały punkt celu</b> jest pomarańczowy, gdy cel leży po widocznej stronie planety.</li>
<li>Jeśli cel znajduje się po zasłoniętej tylnej stronie, punkt celu jest wyświetlany na czerwono.</li>
<li>Twoja pozycja pozostaje nieruchoma w widoku. Planeta i cel są przedstawiane względem twojej pozycji i orientacji.</li>
</ul>
<p>Biała strzałka wskazuje przód; żółta strzałka wskazuje względny kierunek celu. Globus jest schematyczną pomocą orientacyjną, a nie geograficznie dokładnym widokiem terenu. Czerwony punkt oznacza tylną stronę globusa, a nie automatycznie „za twoim statkiem”.</p>

<h3>Siatka perspektywiczna: do 380 km włącznie</h3>
<p>Przy odległości do celu nie większej niż 380 km widok automatycznie przełącza się na pochyloną siatkę perspektywiczną. Jeśli odległość ponownie wzrośnie powyżej 380 km, powróci globus.</p>
<p>Linie poprzeczne tworzą <b>siatkę odległości co 50 km</b>. Punkt celu jest nanoszony wewnątrz siatki zgodnie z odległością i kierunkiem względnym. Perspektywa pomaga w dalszym dolocie; nachylenie sprawia, że odstępy wyglądają na gęstsze w głębi. Aby ustalić właściwy kurs sterowania, obserwuj również kurs do celu i kierunek względny.</p>

<h3>Prawidłowe odczytywanie wartości nawigacyjnych</h3>
<ul>
<li><b>Odległość do celu:</b> Duży odczyt pokazuje pozostałą odległość do celu wzdłuż umownej powierzchni planety.</li>
<li><b>Współrzędne celu:</b> Wprowadzona para współrzędnych celu: najpierw szerokość, potem długość geograficzna. Nie zmienia się podczas twojego ruchu.</li>
<li><b>Aktualne współrzędne:</b> Twoja ostatnia potwierdzona para współrzędnych z Elite, również szerokość / długość geograficzna.</li>
<li><b>Odległość po powierzchni:</b> Ta sama odległość po powierzchni co odległość do celu, ewentualnie dokładniej zaokrąglona w widoku szczegółowym. Nie jest to druga trasa ani bezpośrednia odległość przestrzenna przez powietrze.</li>
<li><b>Namiar:</b> Bezwzględny kierunek do celu z twojej aktualnej pozycji, wyrażony kątem kompasowym: 000° to północ, 090° wschód, 180° południe, a 270° zachód.</li>
<li><b>Kierunek dziobu:</b> Twoja aktualna orientacja podawana przez Elite. Pokazuje, w którą stronę jesteś teraz zwrócony, i nie musi jeszcze pokrywać się z namiarem.</li>
<li><b>Kierunek względny:</b> Różnica między twoją orientacją a namiarem, na przykład „23° w prawo”, „10° w lewo” lub „Prosto”. Przy 180° cel znajduje się za tobą.</li>
<li><b>Kurs do celu:</b> Wyróżniony namiar jako kurs bezwzględny, na który możesz obrócić statek według HUD-u Elite. Nie jest to dodatkowy kąt obrotu.</li>
</ul>
<p>Przykład: przy kierunku dziobu 051° i kursie do celu 074° obróć się o 23° w prawo, aż kompas Elite pokaże około 074°. Podczas dalszego lotu namiar i kurs do celu mogą się zmieniać; kieruj się aktualizowanymi wartościami.</p>
<p>W tej samej pozycji co cel, na biegunie lub w punkcie dokładnie po przeciwnej stronie planety kierunek może być nieokreślony. Nawigator wyświetla wtedy odpowiedni komunikat zamiast wymyślonego kursu.</p>

<h3>Rozmiar okna</h3>
<p>Rozmiar okna nawigatora można swobodnie zmieniać. Globus lub siatka perspektywiczna dopasowują się proporcjonalnie do dostępnego miejsca. Minimalny rozmiar zapewnia czytelność wartości szczegółowych; globus pozostaje okrągły. Pozycja i rozmiar okna są zapisywane.</p>

<h3>Włączanie HUD-u nawigacyjnego</h3>
<p>Po lewej stronie głównego okna zaznacz pole pod <b>pokazuj automatycznie → HUD nawigacyjny</b>. Przy prawidłowej nawigacji planetarnej HUD pojawia się bezpośrednio nad widocznym oknem Elite na pierwszym planie.</p>
<p>Wyświetla trzy wiersze:</p>
<ul>
<li>kierunek względny</li>
<li>kurs do celu</li>
<li>odległość</li>
</ul>
<p>HUD jest przezroczysty, przepuszcza kliknięcia i nie przejmuje fokusu: nie zasłania gry nieprzezroczystym obszarem, nie przechwytuje kliknięć myszy i nie odbiera Elite fokusu wprowadzania danych przy automatycznym wyświetlaniu.</p>
<p>Bez prawidłowej nawigacji lub jednoznacznego kierunku automatycznie staje się niewidoczny. Ukrywa się również, gdy Elite jest zminimalizowane lub nie znajduje się na pierwszym planie. Pole na pasku bocznym może mimo to pozostać zaznaczone; oznacza preferencję automatycznego wyświetlania, a nie aktualną widoczność.</p>
<p>HUD jest tylko dodatkowym wyświetlaczem. Zwykły nawigator działa niezależnie od niego, także przy wyłączonym lub niedostępnym HUD-zie.</p>

<h3>Ustawianie nowego celu</h3>
<p>Na tym samym ciele możesz w dowolnym momencie ponownie otworzyć „Wprowadzanie ręczne …” i ustawić inne współrzędne. Nowy cel zastępuje poprzedni cel nawigacyjny. Przy odpowiednich danych pozycji kompas aktualizuje się natychmiast.</p>
<p>„Zakończ nawigację” usuwa aktualny cel. Aby wykonać kolejny dolot, wystarczy ustawić nowy cel.</p>

<h3>Aktualność danych i ograniczenia</h3>
<p>Nawigacja opiera się na danych stanu dostarczanych przez Elite. Aktualizacje mogą docierać z opóźnieniem zależnym od stanu gry. Wskaźnik wieku danych w nawigatorze pokazuje czas, jaki upłynął od ostatniego potwierdzonego komunikatu stanu.</p>
<p>Odległość po powierzchni opisuje najkrótszy łuk na umownej kuli. Nie jest trasą terenową ani drogową. Nawigator nie zna przeszkód ani wysokości terenu wzdłuż trasy; wysokość lotu, bezpieczna prędkość i omijanie przeszkód pozostają twoim zadaniem.</p>

<h3>Wskazówka</h3>
<p>Przed dolotem sprawdź nazwę ciała oraz znaki współrzędnych celu. Następnie ustaw się według kursu do celu na kompasie Elite i obserwuj kierunek względny oraz odległość. Jeśli nawigator czeka, sprawdź, czy Elite dostarcza już współrzędne planetarne dla docelowego ciała.</p>""",
    ),
}

DIALOG_TITLE = 'Pomoc – {area}'
CLOSE_LABEL = 'Zamknij'
