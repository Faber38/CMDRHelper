"""Trade partial-result notice, separate from the protected help translations."""

_COMMUNITY_FAILURE = {
    'de': 'Eigene Marktdaten gefunden. Die Community-Suche ist fehlgeschlagen; die angezeigten Ergebnisse sind unvollständig. Bessere Community-Angebote können fehlen.',
    'en': 'Own market data found. The community search failed; the displayed results are incomplete. Better community offers may be missing.',
    'fr': 'Données de marché personnelles trouvées. La recherche communautaire a échoué ; les résultats affichés sont incomplets. De meilleures offres communautaires peuvent manquer.',
    'it': 'Trovati dati di mercato propri. La ricerca della comunità non è riuscita; i risultati mostrati sono incompleti. Potrebbero mancare offerte migliori della comunità.',
    'no': 'Egne markedsdata funnet. Fellesskapssøket mislyktes; resultatene som vises er ufullstendige. Bedre tilbud fra fellesskapet kan mangle.',
    'sv': 'Egna marknadsdata hittades. Communitysökningen misslyckades; resultaten som visas är ofullständiga. Bättre communityerbjudanden kan saknas.',
    'fi': 'Omia markkinatietoja löytyi. Yhteisöhaku epäonnistui; näytetyt tulokset ovat puutteellisia. Parempia yhteisön tarjouksia saattaa puuttua.',
    'pl': 'Znaleziono własne dane rynkowe. Wyszukiwanie społecznościowe nie powiodło się; wyświetlane wyniki są niepełne. Może brakować lepszych ofert społeczności.',
    'nl': 'Eigen marktgegevens gevonden. De communityzoekopdracht is mislukt; de getoonde resultaten zijn onvolledig. Betere communityaanbiedingen kunnen ontbreken.',
    'es': 'Se han encontrado datos de mercado propios. La búsqueda comunitaria ha fallado; los resultados mostrados están incompletos. Pueden faltar mejores ofertas de la comunidad.',
    'tr': 'Kendi piyasa verileriniz bulundu. Topluluk araması başarısız oldu; gösterilen sonuçlar eksik. Daha iyi topluluk teklifleri eksik olabilir.',
    'el': 'Βρέθηκαν δικά σας δεδομένα αγοράς. Η αναζήτηση κοινότητας απέτυχε· τα εμφανιζόμενα αποτελέσματα είναι ελλιπή. Ενδέχεται να λείπουν καλύτερες προσφορές της κοινότητας.',
}


def community_failure_text(language):
    return _COMMUNITY_FAILURE.get(language, _COMMUNITY_FAILURE['en'])

_MARKET_NOTICE = {
    'de': 'Marktdaten stammen aus eigenen Elite-Beobachtungen und/oder Community-Meldungen. Preise und Mengen können inzwischen abweichen. Bitte das Datenalter beachten.',
    'en': 'Market data comes from your Elite observations and/or community reports. Prices and quantities may have changed. Please check the data age.',
    'fr': 'Les données de marché proviennent de vos observations Elite et/ou de rapports communautaires. Les prix et quantités peuvent avoir changé. Vérifiez leur ancienneté.',
    'it': 'I dati di mercato provengono dalle tue osservazioni in Elite e/o dalla comunità. Prezzi e quantità possono essere cambiati. Controlla l’età dei dati.',
    'no': 'Markedsdata kommer fra dine Elite-observasjoner og/eller fellesskapsrapporter. Priser og mengder kan ha endret seg. Sjekk dataenes alder.',
    'sv': 'Marknadsdata kommer från dina Elite-observationer och/eller communityrapporter. Priser och mängder kan ha ändrats. Kontrollera datans ålder.',
    'fi': 'Markkinatiedot perustuvat omiin Elite-havaintoihisi ja/tai yhteisön ilmoituksiin. Hinnat ja määrät ovat voineet muuttua. Tarkista tietojen ikä.',
    'pl': 'Dane rynkowe pochodzą z własnych obserwacji w Elite i/lub zgłoszeń społeczności. Ceny i ilości mogły się zmienić. Sprawdź wiek danych.',
    'nl': 'Marktgegevens komen uit je eigen Elite-waarnemingen en/of communitymeldingen. Prijzen en hoeveelheden kunnen veranderd zijn. Controleer de ouderdom van de gegevens.',
    'es': 'Los datos de mercado proceden de tus observaciones en Elite y/o de informes de la comunidad. Los precios y cantidades pueden haber cambiado. Comprueba la antigüedad de los datos.',
    'tr': 'Piyasa verileri kendi Elite gözlemlerinizden ve/veya topluluk bildirimlerinden gelir. Fiyatlar ve miktarlar değişmiş olabilir. Verilerin yaşını kontrol edin.',
    'el': 'Τα δεδομένα αγοράς προέρχονται από δικές σας παρατηρήσεις στο Elite ή/και αναφορές κοινότητας. Οι τιμές και οι ποσότητες μπορεί να έχουν αλλάξει. Ελέγξτε την ηλικία των δεδομένων.',
}


def market_notice_text(language):
    return _MARKET_NOTICE.get(language, _MARKET_NOTICE['en'])
