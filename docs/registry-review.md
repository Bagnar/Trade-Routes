# Проверка реестра источников — рабочий лист для основателя

Сгенерировано 13 сентября 2026 из `data/sources.yaml` и `data/facts`. Раздел 3 плана (`docs/expansion-plan.md`).

## Как проверять одну запись (3–5 минут)

1. Открыть домен. Убедиться, что это сайт государственного органа или международной организации, а не агрегатор, брокер или СМИ.
2. В `data/sources.yaml` у записи поставить `status: verified`. Если домен не тот — удалить запись или заменить домен.
3. Для строк «входная страница» найти на сайте раздел с самими правилами (пошлины, процедуры ввоза, лицензии, поддержка экспорта) и заменить адрес в `urls` на него. Одна страница — одна тема.
4. Для строк «недоступна с серверов GitHub» ничего не менять: сайт блокирует зарубежные адреса; открыть с российского или местного компьютера и, если страница есть, оставить как есть — читать её будем другим способом.
5. Сохранить, закоммитить. Ежедневная проверка на следующее утро прочитает новые адреса; результат виден на `/facts` и `/country/<код>`.

Правки лучше делать прямо на GitHub: открыть `data/sources.yaml`, нажать карандаш, изменить, «Commit changes». Ошибка в формате файла остановит конвейер с понятным сообщением в Actions, ничего не сломается навсегда.

## Канада (CA)

| id | сайт | орган | статус | страница | что показал конвейер |
|---|---|---|---|---|---|
| ca-cbsa | cbsa-asfc.gc.ca | Canada Border Services Agency (CBSA) | to_verify | https://www.cbsa-asfc.gc.ca/publications/dm-md/d9/d9-1-6-eng.html | прочитана 2026-09-12, фактов 8 |
| ca-cbsa | cbsa-asfc.gc.ca | Canada Border Services Agency (CBSA) | to_verify | https://www.cbsa-asfc.gc.ca/trade-commerce/tariff-tarif/2026/html/tblmod-eng.html | прочитана 2026-09-12, фактов 6 |
| ca-cbsa | cbsa-asfc.gc.ca | Canada Border Services Agency (CBSA) | to_verify | https://www.cbsa-asfc.gc.ca/services/carm-gcra/menu-eng.html | прочитана 2026-09-12, фактов 7 |
| ca-cbsa | cbsa-asfc.gc.ca | Canada Border Services Agency (CBSA) | to_verify | https://www.cbsa-asfc.gc.ca/import/courier/menu-eng.html | прочитана 2026-09-12, фактов 12 |
| ca-cbsa | cbsa-asfc.gc.ca | Canada Border Services Agency (CBSA) | to_verify | https://www.cbsa-asfc.gc.ca/sima-lmsi/mif-mev/menu-eng.html | прочитана 2026-09-12, фактов нет — входная страница |
| ca-tariff-finder | tariffinder.ca | Canada Tariff Finder (Trade Commissioner Service) | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| ca-cra | canada.ca | Canada Revenue Agency | to_verify | https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/gst-hst-businesses/charge-collect-imports-exports.html | прочитана 2026-09-12, фактов 21 |
| ca-gac-sanctions | international.gc.ca | Global Affairs Canada — sanctions and import/export controls | to_verify | https://www.international.gc.ca/world-monde/international_relations-relations_internationales/sanctions/current-actuelles.aspx?lang=eng | прочитана 2026-09-12, фактов 6 |
| ca-gac-sanctions | international.gc.ca | Global Affairs Canada — sanctions and import/export controls | to_verify | https://www.international.gc.ca/trade-commerce/controls-controles/export-exportations/index.aspx?lang=eng | прочитана 2026-09-12, фактов нет — входная страница |
| ca-cfia | inspection.canada.ca | Canadian Food Inspection Agency | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| ca-health | canada.ca | Health Canada — consumer product safety | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| ca-competition | competition-bureau.canada.ca | Competition Bureau — labelling (textile, consumer packaging) | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| ca-statcan | statcan.gc.ca | Statistics Canada — international merchandise trade | to_verify |  | страниц нет — нужен адрес раздела с правилами |

## Китай (CN)

| id | сайт | орган | статус | страница | что показал конвейер |
|---|---|---|---|---|---|
| cn-mofcom | mofcom.gov.cn | Ministry of Commerce (MOFCOM) | to_verify | http://english.mofcom.gov.cn/ | прочитана 2026-09-12, фактов 3 |
| cn-gacc | customs.gov.cn | General Administration of Customs (GACC) | to_verify | http://english.customs.gov.cn/ | прочитана 2026-09-12, фактов нет — входная страница |
| cn-sta | chinatax.gov.cn | State Taxation Administration | to_verify | https://www.chinatax.gov.cn/ | прочитана 2026-09-12, фактов нет — входная страница |
| cn-sinosure | sinosure.com.cn | China Export & Credit Insurance Corporation (Sinosure) | to_verify | https://www.sinosure.com.cn/en/ | прочитана 2026-09-12, фактов 5 |
| cn-ccpit | ccpit.org | China Council for the Promotion of International Trade (CCPI | to_verify | https://www.ccpit.org/ | прочитана 2026-09-12, фактов нет — входная страница |
| cn-customs-stats | customs.gov.cn | GACC — trade statistics | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| cn-nbs | stats.gov.cn | National Bureau of Statistics — regional industrial output | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| cn-miit | miit.gov.cn | Ministry of Industry and Information Technology — industrial | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| cn-cantonfair | cantonfair.org.cn | China Import and Export Fair (Canton Fair) — organised by Ch | to_verify |  | страниц нет — нужен адрес раздела с правилами |

## Россия (RU)

| id | сайт | орган | статус | страница | что показал конвейер |
|---|---|---|---|---|---|
| ru-fts | customs.gov.ru | Федеральная таможенная служба | to_verify | https://customs.gov.ru/uchastnikam-ved | недоступна с серверов GitHub |
| ru-minpromtorg | minpromtorg.gov.ru | Минпромторг | to_verify | https://minpromtorg.gov.ru/ | недоступна с серверов GitHub |
| ru-mcx | mcx.gov.ru | Минсельхоз — экспортные пошлины на зерно, поддержка АПК | to_verify | https://mcx.gov.ru/activity/state-support/measures/ | недоступна с серверов GitHub |
| ru-rec | exportcenter.ru | Российский экспортный центр (РЭЦ) | to_verify | https://www.exportcenter.ru/services/ | недоступна с серверов GitHub |
| ru-exiar | exiar.ru | ЭКСАР — страхование экспорта | to_verify | https://www.exiar.ru/ | недоступна с серверов GitHub |
| ru-fns | nalog.gov.ru | ФНС — НДС при экспорте | to_verify | https://www.nalog.gov.ru/rn77/taxation/taxes/nds/ | прочитана 2026-09-12, фактов 22 |
| ru-fsvps | fsvps.gov.ru | Россельхознадзор — фитосанитарные и ветеринарные сертификаты | to_verify | https://fsvps.gov.ru/export/ | прочитана 2026-09-12, фактов 2 |
| ru-government | government.ru | Правительство России — постановления о квотах и пошлинах | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| ru-rosstat | rosstat.gov.ru | Federal State Statistics Service (Rosstat) — regional output | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| ru-tpprf | tpprf.ru | ТПП РФ — сертификаты происхождения | to_verify | https://tpprf.ru/ru/services/sertifikatsiya/ | прочитана 2026-09-12, фактов нет — входная страница |
| eaeu-eec | eec.eaeunion.org | Евразийская экономическая комиссия — тариф ЕАЭС, соглашения  | to_verify | https://eec.eaeunion.org/comission/department/dotp/ | прочитана 2026-09-12, фактов 10 |

## Иран (IR)

| id | сайт | орган | статус | страница | что показал конвейер |
|---|---|---|---|---|---|
| ir-irica | irica.ir | Iran Customs Administration (IRICA) | unstable | https://irica.ir/ | недоступна с серверов GitHub |
| ir-tpo | tpo.ir | Trade Promotion Organization of Iran | unstable | https://tpo.ir/ | недоступна с серверов GitHub |
| ir-mimt | mimt.ir | Ministry of Industry, Mine and Trade | unstable | https://mimt.ir/ | недоступна с серверов GitHub |
| ir-cbi | cbi.ir | Central Bank of Iran — currency allocation for imports | unstable | https://www.cbi.ir/ | прочитана 2026-09-13, фактов 8 |
| ir-isiri | isiri.gov.ir | Iranian National Standards Organization | unstable | https://www.isiri.gov.ir/ | недоступна с серверов GitHub |

## Турция (TR)

| id | сайт | орган | статус | страница | что показал конвейер |
|---|---|---|---|---|---|
| tr-ticaret | ticaret.gov.tr | Ministry of Trade (Ticaret Bakanlığı) — export promotion, ex | to_verify | https://ticaret.gov.tr/ihracat | прочитана 2026-09-12, фактов 10 |
| tr-ticaret | ticaret.gov.tr | Ministry of Trade (Ticaret Bakanlığı) — export promotion, ex | to_verify | https://ticaret.gov.tr/ithalat | прочитана 2026-09-12, фактов 7 |
| tr-ticaret | ticaret.gov.tr | Ministry of Trade (Ticaret Bakanlığı) — export promotion, ex | to_verify | https://ticaret.gov.tr/gumruk-islemleri | прочитана 2026-09-12, фактов 5 |
| tr-tuik | tuik.gov.tr | Turkish Statistical Institute (TÜİK) — regional output and e | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| tr-sanayi | sanayi.gov.tr | Ministry of Industry and Technology — organised industrial z | to_verify | https://www.sanayi.gov.tr/ | прочитана 2026-09-12, фактов нет — входная страница |
| tr-invest | invest.gov.tr | Investment Office of the Presidency — sector and region prof | to_verify | https://www.invest.gov.tr/ | прочитана 2026-09-13, фактов 5 |
| tr-tim | tim.org.tr | Turkish Exporters Assembly (TİM) — statutory body under Law  | to_verify |  | страниц нет — нужен адрес раздела с правилами |

## Казахстан (KZ)

| id | сайт | орган | статус | страница | что показал конвейер |
|---|---|---|---|---|---|
| kz-kgd | kgd.gov.kz | Комитет государственных доходов Минфина РК (таможня | to_verify | https://kgd.gov.kz/ru/section/tamozhennoe-administrirovanie | прочитана 2026-09-12, фактов 2 |
| kz-eec | eaeunion.org | Евразийская экономическая комиссия — ЕТТ ЕАЭС | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| kz-adilet | adilet.zan.kz | Информационно-правовая система «Әділет» — законы и НПА РК | to_verify | https://adilet.zan.kz/rus/docs/K1700000123 | прочитана 2026-09-12, фактов нет — входная страница |
| kz-mti | gov.kz | Министерство торговли и интеграции РК | to_verify | https://www.gov.kz/memleket/entities/mti?lang=ru | прочитана 2026-09-12, фактов нет — входная страница |
| kz-qaztrade | qaztrade.org.kz | QazTrade — центр развития торговой политики (господдержка эк | to_verify | https://qaztrade.org.kz/ | прочитана 2026-09-13, фактов 8 |
| kz-kazakhexport | kazakhexport.kz | KazakhExport — экспортное страхование (государственная компа | to_verify | https://kazakhexport.kz/ | прочитана 2026-09-13, фактов 11 |
| kz-stat | stat.gov.kz | Бюро национальной статистики АСПиР РК | to_verify |  | страниц нет — нужен адрес раздела с правилами |

## Узбекистан (UZ)

| id | сайт | орган | статус | страница | что показал конвейер |
|---|---|---|---|---|---|
| uz-customs | customs.uz | Таможенный комитет Республики Узбекистан | to_verify | https://customs.uz/ru | прочитана 2026-09-12, фактов нет — входная страница |
| uz-lex | lex.uz | Национальная база данных законодательства Lex.uz | to_verify | https://lex.uz/ru/ | прочитана 2026-09-12, фактов 3 |
| uz-mift | mift.uz | Министерство инвестиций | to_verify | https://mift.uz/ru | недоступна с серверов GitHub |
| uz-export | export.uz | Агентство по продвижению экспорта при МИПТ | to_verify | https://export.uz/ | недоступна с серверов GitHub |
| uz-tax | soliq.uz | Налоговый комитет — НДС и акцизы при ввозе | to_verify | https://soliq.uz/ | недоступна с серверов GitHub |
| uz-stat | stat.uz | Агентство статистики при Президенте | to_verify |  | страниц нет — нужен адрес раздела с правилами |

## ОАЭ (AE)

| id | сайт | орган | статус | страница | что показал конвейер |
|---|---|---|---|---|---|
| ae-fca | icp.gov.ae | Federal Customs Authority (Federal Authority for Identity | to_verify | https://icp.gov.ae/en/ | прочитана 2026-09-12, фактов 3 |
| ae-moec | moec.gov.ae | Ministry of Economy — trade policy | to_verify | https://www.moec.gov.ae/en/cepa | прочитана 2026-09-13, фактов нет — входная страница |
| ae-tax | tax.gov.ae | Federal Tax Authority — VAT and excise on imports | to_verify | https://tax.gov.ae/en/ | прочитана 2026-09-12, фактов 10 |
| ae-dubai-customs | dubaicustoms.gov.ae | Dubai Customs | to_verify | https://www.dubaicustoms.gov.ae/en/ | прочитана 2026-09-12, фактов нет — входная страница |
| ae-legislation | uaelegislation.gov.ae | UAE Legislation (official legal portal) | to_verify | https://uaelegislation.gov.ae/en | прочитана 2026-09-13, фактов нет — входная страница |
| ae-moiat | moiat.gov.ae | Ministry of Industry and Advanced Technology — standards | to_verify |  | страниц нет — нужен адрес раздела с правилами |

## Германия (DE)

| id | сайт | орган | статус | страница | что показал конвейер |
|---|---|---|---|---|---|
| de-zoll | zoll.de | Zoll — Generalzolldirektion (таможня Германии) | to_verify | https://www.zoll.de/EN/Businesses/businesses_node.html | прочитана 2026-09-12, фактов 3 |
| de-bafa | bafa.de | BAFA — Bundesamt für Wirtschaft und Ausfuhrkontrolle (экспор | to_verify | https://www.bafa.de/DE/Aussenwirtschaft/Ausfuhrkontrolle/ausfuhrkontrolle_node.html | прочитана 2026-09-12, фактов 11 |
| de-bmwk | bmwk.de | Федеральное министерство экономики (внешнеэкономическая поли | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| de-gtai | gtai.de | Germany Trade & Invest (федеральное агентство) | to_verify | https://www.gtai.de/en/ | прочитана 2026-09-13, фактов нет — входная страница |
| de-gesetze | gesetze-im-internet.de | Gesetze im Internet — федеральные законы (BMJ) | to_verify | https://www.gesetze-im-internet.de/awg_2013/ | прочитана 2026-09-13, фактов 11 |
| de-gesetze | gesetze-im-internet.de | Gesetze im Internet — федеральные законы (BMJ) | to_verify | https://www.gesetze-im-internet.de/awv_2013/ | прочитана 2026-09-13, фактов 24 |
| de-destatis | destatis.de | Statistisches Bundesamt (Destatis) | to_verify |  | страниц нет — нужен адрес раздела с правилами |

## США (US)

| id | сайт | орган | статус | страница | что показал конвейер |
|---|---|---|---|---|---|
| us-cbp | cbp.gov | U.S. Customs and Border Protection | to_verify | https://www.cbp.gov/trade/basic-import-export | прочитана 2026-09-13, фактов нет — входная страница |
| us-cbp | cbp.gov | U.S. Customs and Border Protection | to_verify | https://www.cbp.gov/trade/forced-labor | прочитана 2026-09-13, фактов нет — входная страница |
| us-hts | usitc.gov | U.S. International Trade Commission — Harmonized Tariff Sche | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| us-hts-search | hts.usitc.gov | HTS search (USITC) | to_verify | https://hts.usitc.gov/ | прочитана 2026-09-12, фактов нет — входная страница |
| us-ita | trade.gov | International Trade Administration (trade.gov) — export guid | to_verify | https://www.trade.gov/export-solutions | прочитана 2026-09-12, фактов 6 |
| us-bis | bis.gov | Bureau of Industry and Security — export controls (EAR | to_verify | https://www.bis.gov/licensing | прочитана 2026-09-12, фактов 9 |
| us-ustr | ustr.gov | Office of the U.S. Trade Representative — Section 301 | to_verify | https://ustr.gov/issue-areas/enforcement/section-301-investigations | прочитана 2026-09-12, фактов 15 |
| us-federal-register | federalregister.gov | Federal Register — official notices (tariff actions | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| us-fda | fda.gov | Food and Drug Administration — food | to_verify | https://www.fda.gov/industry/import-program-food-and-drug-administration-fda | прочитана 2026-09-12, фактов 6 |
| us-cpsc | cpsc.gov | Consumer Product Safety Commission — toys | to_verify | https://www.cpsc.gov/Business--Manufacturing/Business-Education/Business-Guidance/Toy-Safety | прочитана 2026-09-12, фактов нет — входная страница |
| us-exim | exim.gov | Export-Import Bank of the United States | to_verify | https://www.exim.gov/ | прочитана 2026-09-12, фактов 7 |

## Индия (IN)

| id | сайт | орган | статус | страница | что показал конвейер |
|---|---|---|---|---|---|
| in-cbic | cbic.gov.in | Central Board of Indirect Taxes and Customs | to_verify | https://www.cbic.gov.in/ | прочитана 2026-09-12, фактов нет — входная страница |
| in-icegate | icegate.gov.in | ICEGATE — customs e-filing portal (CBIC) | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| in-dgft | dgft.gov.in | Directorate General of Foreign Trade — Foreign Trade Policy | to_verify | https://www.dgft.gov.in/CP/?opt=ft-policy | прочитана 2026-09-13, фактов нет — входная страница |
| in-dgft | dgft.gov.in | Directorate General of Foreign Trade — Foreign Trade Policy | to_verify | https://www.dgft.gov.in/CP/?opt=IEC | прочитана 2026-09-13, фактов нет — входная страница |
| in-commerce | commerce.gov.in | Ministry of Commerce and Industry | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| in-trade-portal | indiantradeportal.in | Indian Trade Portal (DGFT/FIEO) — tariffs and agreements by  | to_verify | https://www.indiantradeportal.in/ | прочитана 2026-09-12, фактов нет — входная страница |
| in-bis | bis.gov.in | Bureau of Indian Standards — mandatory certification | to_verify | https://www.bis.gov.in/product-certification/ | прочитана 2026-09-12, фактов нет — входная страница |
| in-fssai | fssai.gov.in | Food Safety and Standards Authority of India | to_verify | https://fssai.gov.in/cms/imports.php | прочитана 2026-09-12, фактов нет — входная страница |

## Вьетнам (VN)

| id | сайт | орган | статус | страница | что показал конвейер |
|---|---|---|---|---|---|
| vn-customs | customs.gov.vn | General Department of Viet Nam Customs (Tổng cục Hải quan) | to_verify | https://www.customs.gov.vn/ | прочитана 2026-09-12, фактов нет — входная страница |
| vn-moit | moit.gov.vn | Ministry of Industry and Trade (Bộ Công Thương) | to_verify | https://moit.gov.vn/ | прочитана 2026-09-13, фактов 3 |
| vn-mof | mof.gov.vn | Ministry of Finance — tariff schedules | to_verify | https://mof.gov.vn/ | прочитана 2026-09-12, фактов нет — входная страница |
| vn-vbpl | vbpl.vn | National legal database (Cơ sở dữ liệu quốc gia về văn bản p | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| vn-gso | gso.gov.vn | General Statistics Office (Cục Thống kê) | to_verify |  | страниц нет — нужен адрес раздела с правилами |

## Бразилия (BR)

| id | сайт | орган | статус | страница | что показал конвейер |
|---|---|---|---|---|---|
| br-receita | gov.br | Receita Federal — aduana (таможня) | to_verify | https://www.gov.br/receitafederal/pt-br/assuntos/aduana-e-comercio-exterior | прочитана 2026-09-12, фактов нет — входная страница |
| br-mdic | gov.br | Ministério do Desenvolvimento | to_verify | https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior | прочитана 2026-09-12, фактов нет — входная страница |
| br-siscomex | portalunico.siscomex.gov.br | Portal Único Siscomex — процедуры ввоза и вывоза | to_verify | https://portalunico.siscomex.gov.br/ | прочитана 2026-09-12, фактов нет — входная страница |
| br-planalto | planalto.gov.br | Presidência da República — законодательство (Planalto) | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| br-anvisa | gov.br | ANVISA — санитарный надзор (продукты | to_verify | https://www.gov.br/anvisa/pt-br/assuntos/importacao-e-exportacao | прочитана 2026-09-12, фактов нет — входная страница |
| br-apex | apexbrasil.com.br | ApexBrasil — агентство продвижения экспорта | to_verify | https://apexbrasil.com.br/ | прочитана 2026-09-12, фактов 8 |
| br-ibge | ibge.gov.br | IBGE — статистика | to_verify |  | страниц нет — нужен адрес раздела с правилами |

## Европейский союз (EU)

| id | сайт | орган | статус | страница | что показал конвейер |
|---|---|---|---|---|---|
| eu-taxud | taxation-customs.ec.europa.eu | European Commission DG TAXUD — TARIC | to_verify | https://taxation-customs.ec.europa.eu/customs-4_en | прочитана 2026-09-12, фактов 3 |
| eu-access2markets | trade.ec.europa.eu | Access2Markets (DG TRADE) — tariffs | to_verify | https://trade.ec.europa.eu/access-to-markets/en/home | прочитана 2026-09-12, фактов 3 |
| eu-eur-lex | eur-lex.europa.eu | EUR-Lex — законодательство ЕС | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| eu-trade-policy | policy.trade.ec.europa.eu | DG TRADE — trade policy | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| eu-sanctions-map | sanctionsmap.eu | EU Sanctions Map | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| eu-eurostat | ec.europa.eu | Eurostat — Comext trade statistics | to_verify |  | страниц нет — нужен адрес раздела с правилами |

## Санкционные органы, экспортный контроль, международные

| id | сайт | орган | статус | страница | что показал конвейер |
|---|---|---|---|---|---|
| sanc-ca | international.gc.ca | Global Affairs Canada — Special Economic Measures Act regula | to_verify | https://www.international.gc.ca/world-monde/international_relations-relations_internationales/sanctions/iran.aspx?lang=eng | прочитана 2026-09-12, фактов 18 |
| sanc-ca | international.gc.ca | Global Affairs Canada — Special Economic Measures Act regula | to_verify | https://www.international.gc.ca/world-monde/international_relations-relations_internationales/sanctions/russia-russie.aspx?lang=eng | прочитана 2026-09-12, фактов 33 |
| sanc-us-ofac | ofac.treasury.gov | Office of Foreign Assets Control (OFAC) — programs, SDN list | to_verify | https://ofac.treasury.gov/sanctions-programs-and-country-information/iran-sanctions | прочитана 2026-09-12, фактов 20 |
| sanc-us-ofac | ofac.treasury.gov | Office of Foreign Assets Control (OFAC) — programs, SDN list | to_verify | https://ofac.treasury.gov/sanctions-programs-and-country-information/russian-harmful-foreign-activities-sanctions | прочитана 2026-09-12, фактов 15 |
| sanc-eu | sanctionsmap.eu | EU Sanctions Map (Council of the EU / EEAS) | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| sanc-eu-commission | finance.ec.europa.eu | European Commission — sanctions (restrictive measures) overv | to_verify | https://finance.ec.europa.eu/eu-and-world/sanctions-restrictive-measures/sanctions-adopted-following-russias-military-aggression-against-ukraine_en | прочитана 2026-09-12, фактов 21 |
| sanc-uk-ofsi | gov.uk | Office of Financial Sanctions Implementation; UK sanctions l | to_verify | https://www.gov.uk/government/collections/uk-sanctions-on-russia | прочитана 2026-09-12, фактов 9 |
| sanc-uk-ofsi | gov.uk | Office of Financial Sanctions Implementation; UK sanctions l | to_verify | https://www.gov.uk/government/collections/uk-sanctions-on-iran | прочитана 2026-09-12, фактов нет — входная страница |
| wassenaar | wassenaar.org | Wassenaar Arrangement — dual-use goods and technologies cont | to_verify | https://www.wassenaar.org/control-lists/ | прочитана 2026-09-12, фактов 5 |
| eu-dual-use | policy.trade.ec.europa.eu | European Commission DG TRADE — Regulation (EU) 2021/821 dual | to_verify | https://policy.trade.ec.europa.eu/help-exporters-and-importers/exporting-dual-use-items_en | прочитана 2026-09-12, фактов 14 |
| us-bis | bis.gov | Bureau of Industry and Security (BIS) — Export Administratio | to_verify | https://www.bis.gov/regulations | прочитана 2026-09-12, фактов нет — входная страница |
| cn-mofcom-export-control | exportcontrol.mofcom.gov.cn | 商务部 (MOFCOM) — Export Control Law, dual-use items export con | to_verify | http://exportcontrol.mofcom.gov.cn/ | прочитана 2026-09-12, фактов 10 |
| ru-fstec | fstec.ru | ФСТЭК России — экспортный контроль, контрольные списки | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| wto-rtais | rtais.wto.org | WTO Regional Trade Agreements Information System (RTA-IS) | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| wto-ttd | ttd.wto.org | WTO Tariff & Trade Data | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| itc-gth | globaltradehelpdesk.org | Global Trade Helpdesk (ITC, UNCTAD, WTO) | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| un-comtrade | comtradeplus.un.org | UN Comtrade | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| wb-wits | wits.worldbank.org | World Bank WITS (World Integrated Trade Solution) — UNCTAD T | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| fbx | fbx.freightos.com | Freightos Baltic Index — контейнерные ставки по основным мар | to_verify |  | страниц нет — нужен адрес раздела с правилами |
| drewry-wci | drewry.co.uk | Drewry World Container Index | to_verify |  | страниц нет — нужен адрес раздела с правилами |

## Итого

- строк к проверке: 108; уже `verified`: 0
- записей без адресов страниц: 27
- входных страниц без фактов (заменить на раздел с правилами): 30
- недоступных с серверов GitHub (Россия, Иран, Узбекистан, немецкий портал законов): 12
