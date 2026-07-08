"""Five German travel reports — the GraphRAG corpus (T2/02 corpus + two new ones).

The two additions make the graph interesting: madeira shares 'wandern' with the
alps report and 'meer' with the algarve report — connections a pure vector
search cannot see across documents.
"""

SAMPLE_DOCS: dict[str, str] = {
    "algarve": (
        "Familienzeit an der Algarve\n\n"
        "Zwei Wochen Portugal mit zwei Kindern unter zehn. Die Buchten bei Lagos sind "
        "flach und geschützt, ideal zum Planschen und Sandburgenbauen. Unser Apartment "
        "lag fünf Gehminuten vom Strand, der Vermieter stellte Kinderstühle und ein "
        "Reisebett.\n\n"
        "Preislich blieb es entspannt: Außerhalb der Ferien kostete das Apartment die "
        "Hälfte, und die Strandcafés hatten Kinderteller. Wer mit dem Nachwuchs ans Meer "
        "will, findet hier alles ohne Animation und Hotelbunker."
    ),
    "alpen": (
        "Hüttentour in den Stubaier Alpen\n\n"
        "Sieben Tage von Hütte zu Hütte, jeden Tag zwischen 800 und 1200 Höhenmeter. "
        "Die Etappen sind gut markiert, aber Trittsicherheit ist Pflicht, besonders am "
        "Gletscherrand.\n\n"
        "Übernachtet wird im Lager, reserviert werden muss Monate im Voraus. Wer Ruhe, "
        "Panorama und ehrliche Anstrengung sucht, wird hier glücklich — Badeurlaub ist "
        "das definitiv nicht."
    ),
    "tokio": (
        "Städtereise Tokio\n\n"
        "Fünf Tage Großstadt: U-Bahn im Minutentakt, Ramen um Mitternacht, Tempel "
        "zwischen Hochhäusern. Mit der IC-Karte funktioniert jeder Zug und jeder "
        "Automat.\n\n"
        "Teuer ist vor allem das Hotel; Essen und Nahverkehr sind günstiger als "
        "erwartet. Für Kultur, Technik und Essen die spannendste Stadt, die wir je "
        "besucht haben."
    ),
    "madeira": (
        "Levada-Wandern auf Madeira\n\n"
        "Eine Woche Wandern entlang der Levadas, der alten Wasserkanäle der Insel. Die "
        "Wege sind meist eben, aber schwindelfrei sollte man sein — und abends geht es "
        "zurück ans Meer, zum Baden in den Naturpools von Porto Moniz.\n\n"
        "Die Kombination macht den Reiz aus: vormittags Wandern im Lorbeerwald, "
        "nachmittags Atlantik. Für sportliche Paare ideal, mit kleinen Kindern sind "
        "einige Levadas zu ausgesetzt."
    ),
    "gardasee": (
        "Aktivurlaub am Gardasee\n\n"
        "Zwei Wochen mit der ganzen Familie am Nordufer: vormittags Surfen und Segeln "
        "bei verlässlichem Wind, nachmittags Baden am Kiesstrand, dazwischen Radtouren "
        "am Ufer.\n\n"
        "Die Campingplätze sind auf Familien eingestellt, und wer Wandern will, nimmt "
        "die Seilbahn auf den Monte Baldo — oben warten Panoramawege für jedes Niveau."
    ),
    "ostsee-winter": (
        "Winterwochenende an der Ostsee\n\n"
        "Ende Dezember an den leeren Strand von Usedom: Sturmspaziergänge, danach "
        "Sauna mit Meerblick und Fischbrötchen im beheizten Strandkorb. Die Kinder "
        "haben den Strand für sich allein.\n\n"
        "Im Winter kosten die Hotels die Hälfte, und die Thermen sind der Plan B für "
        "Regentage. Wer Ruhe sucht statt Sonne, findet hier das Kontrastprogramm zum "
        "Sommerurlaub."
    ),
}
