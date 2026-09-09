"""Translation contracts for the four-paragraph quick-favorite help section.

Phrase anchors encode the reviewed claims, including their negations. They
supplement structural/UI-label checks; they are not an automatic language review.
"""
from importlib import import_module
import re
import unittest

from cmdrhelper.help_content import HELP_LANGUAGES, help_topic


# One group per German master paragraph. Each anchor protects a distinct claim
# (actions/default/conflicts, frozen surface save, later editing, temporary HUD).
CLAIMS = {
    'en': (
        ('freely set, change or remove a global hotkey', 'by default', 'does not register any key without being asked',
         'binding is saved', 'already in use or unavailable', 'previously working binding is retained'),
        ('on foot, in the SRV and in the ship', 'while Elite has focus', 'immediately saves the current surface location',
         'active commander', 'without a dialog or mouse interaction', 'commander, system, body', 'frozen at that moment',
         'Nothing is saved without valid current planetary coordinates', 'earlier coordinates are not reused'),
        ('unique provisional name', 'normal favorites window', 'later rename', 'another category', 'add a note or add an image',
         'No screenshot is automatically taken or imported'),
        ('approximately two seconds', 'directly over the active Elite window with the body and coordinates',
         'if the location is unavailable', 'appears briefly', 'does not take focus or intercept input',
         'navigation HUD switched off', 'disappears completely', 'HUD switched on', 'normal navigation display remains',
         'saved HUD switch setting is not changed', 'same overlay infrastructure and platform requirements'),
    ),
    'fr': (
        ('librement définir, modifier ou supprimer un raccourci clavier global', 'par défaut',
         'n’enregistre aucune touche sans demande explicite', 'attribution est sauvegardée',
         'déjà utilisée ou indisponible', 'attribution qui fonctionnait auparavant est conservée'),
        ('lorsque Elite a le focus', 'à pied, en SRV et à bord du vaisseau', 'enregistre immédiatement la position actuelle à la surface',
         'commandant actif', 'sans boîte de dialogue ni utilisation de la souris', 'commandant, le système, le corps',
         'figés à cet instant', 'Sans coordonnées planétaires actuelles valides, rien n’est enregistré',
         'anciennes coordonnées ne sont pas réutilisées'),
        ('nom provisoire unique', 'fenêtre habituelle des favoris', 'ensuite le renommer', 'autre catégorie',
         'ajouter une note ou une image', 'Aucune capture d’écran n’est automatiquement prise ni importée'),
        ('environ deux secondes', 'directement au-dessus de la fenêtre active d’Elite avec le corps et les coordonnées',
         'si la position est indisponible', 's’affiche brièvement', 'ne prend pas le focus et n’intercepte aucune entrée',
         'HUD de navigation est désactivé', 'disparaît complètement', 'HUD est activé',
         'affichage normal de navigation reste ensuite visible', 'réglage enregistré du commutateur du HUD n’est pas modifié',
         'même infrastructure de superposition et les mêmes prérequis de plateforme'),
    ),
    'el': (
        ('ορίσεις ελεύθερα, να αλλάξεις ή να καταργήσεις ένα καθολικό πλήκτρο συντόμευσης', 'προεπιλογή',
         'δεν καταχωρίζει κανένα πλήκτρο χωρίς να του ζητηθεί', 'αντιστοίχιση αποθηκεύεται',
         'χρησιμοποιείται ήδη ή δεν είναι διαθέσιμος', 'προηγούμενη αντιστοίχιση που λειτουργούσε διατηρείται'),
        ('όταν το Elite έχει την εστίαση', 'πεζός, στο SRV και στο σκάφος', 'αποθηκεύεται αμέσως η τρέχουσα θέση στην επιφάνεια',
         'ενεργό διοικητή', 'χωρίς παράθυρο διαλόγου και χωρίς χρήση ποντικιού', 'διοικητής, το σύστημα, το ουράνιο σώμα',
         'παγιώνονται εκείνη τη στιγμή', 'Χωρίς έγκυρες τρέχουσες πλανητικές συντεταγμένες δεν αποθηκεύεται τίποτα',
         'παλαιότερες συντεταγμένες δεν επαναχρησιμοποιούνται'),
        ('μοναδικό προσωρινό όνομα', 'κανονικό παράθυρο αγαπημένων', 'αργότερα να το μετονομάσεις', 'άλλη κατηγορία',
         'προσθέσεις σημείωση ή εικόνα', 'Δεν λαμβάνεται ούτε εισάγεται αυτόματα κανένα στιγμιότυπο οθόνης'),
        ('περίπου δύο δευτερόλεπτα', 'απευθείας πάνω από το ενεργό παράθυρο του Elite', 'ουράνιο σώμα και τις συντεταγμένες',
         'αν η θέση δεν είναι διαθέσιμη', 'εμφανίζεται για λίγο', 'δεν παίρνει την εστίαση και δεν δεσμεύει καμία είσοδο',
         'απενεργοποιημένο το HUD πλοήγησης', 'εξαφανίζεται εντελώς', 'HUD είναι ενεργοποιημένο',
         'παραμένει στη συνέχεια η κανονική ένδειξη πλοήγησης', 'αποθηκευμένη ρύθμιση του διακόπτη του HUD δεν αλλάζει',
         'ίδια υποδομή επικάλυψης και τις ίδιες απαιτήσεις πλατφόρμας'),
    ),
    'it': (
        ('impostare liberamente, modificare o rimuovere una scorciatoia da tastiera globale', 'per impostazione predefinita',
         'non registra alcun tasto senza che venga richiesto', 'assegnazione viene salvata', 'già in uso o non è disponibile',
         'assegnazione precedentemente funzionante viene mantenuta'),
        ('mentre Elite ha il focus', 'a piedi, nell’SRV e nella nave', 'salva immediatamente la posizione attuale sulla superficie',
         'comandante attivo', 'senza finestre di dialogo e senza usare il mouse', 'comandante, il sistema, il corpo',
         'fissati in quel momento', 'Senza coordinate planetarie attuali valide non viene salvato nulla',
         'coordinate precedenti non vengono riutilizzate'),
        ('nome provvisorio univoco', 'normale finestra dei preferiti', 'in seguito rinominarlo', 'altra categoria',
         'aggiungere una nota o un’immagine', 'Nessuno screenshot viene acquisito o importato automaticamente'),
        ('circa due secondi', 'direttamente sopra la finestra attiva di Elite con il corpo e le coordinate',
         'se la posizione non è disponibile', 'compare brevemente', 'non prende il focus e non intercetta gli input',
         'HUD di navigazione disattivato', 'scompare completamente', 'HUD attivato', 'rimane la normale visualizzazione di navigazione',
         'impostazione salvata dell’interruttore dell’HUD non viene modificata',
         'stessa infrastruttura di sovrimpressione e gli stessi requisiti di piattaforma'),
    ),
    'no': (
        ('fritt angi, endre eller fjerne en global hurtigtast', 'som standard', 'registrerer ingen tast uten at du ber om det',
         'Tilordningen lagres', 'allerede er i bruk eller ikke er tilgjengelig', 'tidligere fungerende tilordning beholdes'),
        ('mens Elite har fokus', 'til fots, i SRV-en og i skipet', 'lagrer den aktuelle posisjonen på overflaten umiddelbart',
         'aktive kommandanten', 'uten dialog og uten bruk av mus', 'Kommandant, system, himmellegeme', 'fryses i det øyeblikket',
         'Uten gyldige aktuelle planetkoordinater lagres ingenting', 'tidligere koordinater brukes ikke på nytt'),
        ('unikt foreløpig navn', 'vanlige favorittvinduet', 'senere gi den nytt navn', 'annen kategori',
         'legge til et notat eller et bilde', 'Ingen skjermbilder tas eller importeres automatisk'),
        ('omtrent to sekunder', 'direkte over det aktive Elite-vinduet med himmellegeme og koordinater', 'hvis posisjonen mangler',
         'kort', 'tar ikke fokus og fanger ikke opp inndata', 'navigasjons-HUD-et er slått av', 'forsvinner deretter helt',
         'HUD-et er slått på', 'vanlige navigasjonsvisningen stående etterpå', 'lagrede innstillingen for HUD-bryteren endres ikke',
         'samme overleggsløsning og plattformkrav'),
    ),
    'sv': (
        ('fritt ange, ändra eller ta bort en global snabbtangent', 'som standard', 'registrerar ingen tangent utan att du ber om det',
         'Tilldelningen sparas', 'redan används eller inte är tillgänglig', 'tidigare fungerande tilldelning behålls'),
        ('när Elite har fokus', 'till fots, i SRV:n och i skeppet', 'sparar omedelbart den aktuella positionen på ytan',
         'aktiva befälhavaren', 'utan dialogruta och utan att använda musen', 'Befälhavare, system, himlakropp', 'fryses i det ögonblicket',
         'Utan giltiga aktuella planetkoordinater sparas ingenting', 'tidigare koordinater återanvänds inte'),
        ('unikt tillfälligt namn', 'vanliga favoritfönstret', 'senare byta namn', 'annan kategori', 'lägga till en anteckning eller en bild',
         'Ingen skärmbild tas eller importeras automatiskt'),
        ('ungefär två sekunder', 'direkt över det aktiva Elite-fönstret med himlakropp och koordinater', 'om positionen saknas',
         'en kort stund', 'tar inte fokus och fångar inte upp inmatning', 'navigations-HUD:en är avstängd', 'försvinner sedan helt',
         'HUD:en är påslagen', 'vanliga navigationsvisningen kvar efteråt', 'sparade inställningen för HUD-reglaget ändras inte',
         'samma överläggslösning och plattformskrav'),
    ),
    'fi': (
        ('vapaasti määrittää, vaihtaa tai poistaa yleisen pikanäppäimen', 'oletus', 'ei rekisteröi mitään näppäintä pyytämättä',
         'Määritys tallennetaan', 'jo käytössä tai ei ole käytettävissä', 'aiempi toimiva määritys säilytetään'),
        ('Eliten ollessa aktiivinen', 'jalan, SRV:ssä ja aluksessa', 'tallentaa nykyisen sijainnin pinnalla heti', 'aktiiviselle komentajalle',
         'ilman valintaikkunaa ja hiiren käyttöä', 'Komentaja, järjestelmä, taivaankappale', 'lukitaan sillä hetkellä',
         'Ilman kelvollisia ajantasaisia planeettakoordinaatteja mitään ei tallenneta', 'aiempia koordinaatteja ei käytetä uudelleen'),
        ('yksilöllisen väliaikaisen nimen', 'Tavallisessa suosikki-ikkunassa', 'myöhemmin nimetä sen uudelleen', 'toisen luokan',
         'lisätä muistiinpanon tai kuvan', 'Kuvakaappausta ei oteta eikä tuoda automaattisesti'),
        ('Noin kahden sekunnin', 'suoraan aktiivisen Elite-ikkunan päällä', 'taivaankappaleen ja koordinaattien', 'jos sijainti puuttuu',
         'näkyy lyhyesti', 'ei vie kohdistusta eikä kaappaa syötteitä', 'navigointi-HUD:n ollessa pois päältä', 'katoaa sitten kokonaan',
         'HUD on päällä', 'tavallinen navigointinäyttö jää näkyviin', 'HUD-kytkimen tallennettua asetusta ei muuteta',
         'samaa peittokuvan toteutusta ja samoja alustavaatimuksia'),
    ),
    'pl': (
        ('dowolnie ustawić, zmienić lub usunąć globalny skrót klawiszowy', 'domyślny stan',
         'nie rejestruje żadnego klawisza bez polecenia użytkownika', 'Przypisanie jest zapisywane', 'już zajęta lub niedostępna',
         'poprzednie działające przypisanie zostaje zachowane'),
        ('gdy Elite ma fokus', 'pieszo, w SRV i w statku', 'natychmiast zapisuje aktualną pozycję na powierzchni', 'aktywnego dowódcy',
         'bez okna dialogowego i bez użycia myszy', 'Dowódca, system, ciało niebieskie', 'utrwalone w tej chwili',
         'Bez prawidłowych aktualnych współrzędnych planetarnych nic nie jest zapisywane', 'wcześniejsze współrzędne nie są ponownie używane'),
        ('unikalną tymczasową nazwę', 'zwykłym oknie ulubionych', 'później zmienić jego nazwę', 'inną kategorię', 'dodać notatkę lub obraz',
         'Żaden zrzut ekranu nie jest automatycznie wykonywany ani importowany'),
        ('około dwie sekundy', 'bezpośrednio nad aktywnym oknem Elite', 'ciałem niebieskim i współrzędnymi', 'jeśli pozycja jest niedostępna',
         'na krótko', 'nie przejmuje fokusu i nie przechwytuje danych wejściowych', 'wyłączonym HUD-zie nawigacji', 'znika całkowicie',
         'włączonym HUD-zie', 'pozostaje potem zwykły widok nawigacji', 'Zapisane ustawienie przełącznika HUD-u nie jest zmieniane',
         'tej samej infrastruktury nakładki i wymagań platformy'),
    ),
    'nl': (
        ('vrij een globale sneltoets instellen, wijzigen of verwijderen', 'standaard', 'registreert geen toets zonder dat je daarom vraagt',
         'toewijzing wordt opgeslagen', 'al in gebruik is of op je systeem niet beschikbaar', 'eerder werkende toewijzing blijft behouden'),
        ('terwijl Elite de focus heeft', 'te voet, in de SRV en in het schip', 'huidige locatie op het oppervlak onmiddellijk op',
         'actieve commandant', 'zonder dialoogvenster en zonder muisbediening', 'Commandant, systeem, hemellichaam', 'op dat moment vastgelegd',
         'Zonder geldige actuele planetaire coördinaten wordt niets opgeslagen', 'eerdere coördinaten worden niet opnieuw gebruikt'),
        ('unieke voorlopige naam', 'normale favorietenvenster', 'later een andere naam geven', 'andere categorie',
         'een notitie toevoegen of een afbeelding toevoegen', 'geen screenshot automatisch gemaakt of geïmporteerd'),
        ('ongeveer twee seconden', 'direct boven het actieve Elite-venster met het hemellichaam en de coördinaten', 'als de locatie ontbreekt',
         'verschijnt kort', 'neemt geen focus over en onderschept geen invoer', 'navigatie-HUD is uitgeschakeld', 'verdwijnt daarna volledig',
         'HUD is ingeschakeld', 'blijft daarna de normale navigatieweergave over', 'opgeslagen instelling van de HUD-schakelaar wordt niet gewijzigd',
         'dezelfde overlay-infrastructuur en platformvereisten'),
    ),
    'es': (
        ('asignar libremente, cambiar o eliminar un atajo de teclado global', 'estado predeterminado', 'no registra ninguna tecla sin que se lo pidas',
         'asignación se guarda', 'ya está en uso o no está disponible', 'se conserva cualquier asignación anterior que funcionara'),
        ('mientras Elite tiene el foco', 'a pie, en el SRV y en la nave', 'guarda inmediatamente la ubicación actual en la superficie',
         'comandante activo', 'sin diálogo y sin usar el ratón', 'comandante, el sistema, el cuerpo', 'fijados en ese momento',
         'Sin coordenadas planetarias actuales válidas no se guarda nada', 'no se reutilizan coordenadas anteriores'),
        ('nombre provisional único', 'ventana habitual de favoritos', 'cambiarle el nombre más tarde', 'otra categoría', 'añadir una nota o una imagen',
         'No se toma ni se importa ninguna captura de pantalla automáticamente'),
        ('unos dos segundos', 'directamente sobre la ventana activa de Elite con el cuerpo y las coordenadas', 'si la ubicación no está disponible',
         'aparece brevemente', 'no toma el foco ni intercepta entradas', 'HUD de navegación desactivado', 'desaparece por completo',
         'HUD activado', 'visualización normal de navegación permanece después', 'ajuste guardado del interruptor del HUD no se modifica',
         'misma infraestructura de superposición y los mismos requisitos de plataforma'),
    ),
    'tr': (
        ('genel bir kısayol tuşunu serbestçe atayabilir, değiştirebilir veya kaldırabilirsin', 'varsayılan durum',
         'istenmeden hiçbir tuşu kaydetmez', 'Atama saklanır', 'zaten kullanımdaysa veya sisteminde kullanılamıyorsa', 'daha önce çalışan bir atama korunur'),
        ('Elite odaktayken', 'yaya olarak, SRV’de ve gemide', 'yüzeydeki mevcut konum', 'etkin komutan için hemen kaydedilir',
         'iletişim kutusu açılmaz ve fare kullanımı gerekmez', 'Komutan, sistem, gök cismi', 'o anda sabitlenir',
         'Geçerli güncel gezegen koordinatları yoksa hiçbir şey kaydedilmez', 'eski koordinatlar yeniden kullanılmaz'),
        ('benzersiz bir geçici ad', 'Normal favoriler penceresinde', 'daha sonra adını değiştirebilir', 'başka bir kategori', 'not veya resim ekleyebilirsin',
         'Otomatik olarak ekran görüntüsü alınmaz veya içe aktarılmaz'),
        ('Yaklaşık iki saniye', 'etkin Elite penceresinin doğrudan üzerinde gök cismi ve koordinatlarla', 'konum mevcut değilse',
         'kısa süreliğine', 'odağı almaz ve girdileri yakalamaz', 'Navigasyon HUD’u kapalıyken', 'tamamen kaybolur',
         'HUD açıkken', 'sonrasında normal navigasyon gösterimi kalır', 'HUD anahtarının kayıtlı ayarı değiştirilmez',
         'aynı üst katman altyapısını ve platform gereksinimlerini'),
    ),
}


def section(language):
    # Locate the reviewed section by its localized title, independent of new topics.
    text = help_topic('explorer', language).text
    title = import_module('cmdrhelper.i18n.' + language).TRANSLATIONS['quick_favorite.title']
    matches = [block for block in re.findall(r'<h3>.*?(?=<h3>|$)', text, re.S)
               if title.casefold() in block.split('</h3>', 1)[0].casefold()]
    if len(matches) != 1:
        raise AssertionError(f'{language}: expected exactly one quick-favorite help section')
    return matches[0]


class QuickFavoriteHelpTests(unittest.TestCase):
    def test_every_translation_has_the_complete_reviewed_claims(self):
        self.assertEqual(set(CLAIMS), set(HELP_LANGUAGES) - {'de'})
        for language, groups in CLAIMS.items():
            paragraphs = re.findall(r'<p>(.*?)</p>', section(language), re.S)
            self.assertEqual(len(paragraphs), 4, language)
            for index, anchors in enumerate(groups):
                for anchor in anchors:
                    with self.subTest(language=language, paragraph=index+1, claim=anchor):
                        self.assertIn(anchor.casefold(), paragraphs[index].casefold())

    def test_localized_labels_marker_category_and_both_overlay_messages(self):
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                ui = import_module('cmdrhelper.i18n.' + language).TRANSLATIONS
                paragraphs = re.findall(r'<p>(.*?)</p>', section(language), re.S)
                self.assertIn(ui['settings.title'] + ' → ' + ui['quick_favorite.title'], paragraphs[0])
                self.assertIn(ui['quick_favorite.unassigned'], paragraphs[0])
                for term in ('Linux/X11', 'Windows', 'Elite', 'SRV', 'Latitude', 'Longitude'):
                    self.assertIn(term, paragraphs[1])
                self.assertIn(ui['quick_favorite.marker'] + ' 07.09.2026 06:32:15', paragraphs[2])
                self.assertIn(ui['favorites.category.other'], paragraphs[2])
                self.assertIn('★ ' + ui['quick_favorite.saved'].upper(), paragraphs[3])
                self.assertIn('⚠ ' + ui['quick_favorite.no_coordinates'].upper(), paragraphs[3])

    def test_explorer_structure_and_all_sections_are_nonempty(self):
        master = help_topic('explorer', 'de').text
        structure = lambda text: re.findall(r'<(/?[a-z0-9]+)(?: [^>]*)?>', text)
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                text = help_topic('explorer', language).text
                self.assertEqual(structure(text), structure(master))
                sections = re.findall(r'<h3>(.*?)</h3>(.*?)(?=<h3>|$)', text, re.S)
                self.assertEqual(len(sections), 26)
                for heading, body in sections:
                    self.assertTrue(heading.strip())
                    self.assertRegex(body, r'<(?:p|ul)>')
                    self.assertTrue(re.sub(r'<[^>]+>', '', body).strip())
                self.assertEqual(structure(section(language)), ['h3', '/h3'] + ['p', '/p'] * 4)

    def test_new_translations_have_no_german_residue_or_placeholders(self):
        master_paragraphs = re.findall(r'<p>(.*?)</p>', section('de'), re.S)
        german = (r'Schnell-Favorit|Nicht belegt|Sonstiges|Einstellungen|Tastendruck|Mausbedienung|'
                  r'Oberflächenstandort|eingefroren|Fehlermeldung|FAVORIT GESPEICHERT|'
                  r'KEINE PLANETAREN KOORDINATEN|ausgeschaltetem|vorläufigen Namen|zwei Sekunden')
        for language in CLAIMS:
            with self.subTest(language=language):
                text = section(language)
                self.assertNotRegex(text, german)
                self.assertNotRegex(text, r'\{[^}]+\}')
                for paragraph in master_paragraphs:
                    self.assertNotIn(paragraph, text)


if __name__ == '__main__':
    unittest.main()
