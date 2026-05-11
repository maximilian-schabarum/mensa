# mensa
Parsers for openmensa.org. The parsers runs in a [Github action](https://github.com/maximilian-schabarum/mensa/actions?query=workflow%3ARunParsers) and push the XML feeds to [Github pages](https://maximilian-schabarum.github.io/mensa/)

Fork of [mensahd](https://github.com/cvzi/mensahd) by [cvzi](https://github.com/cvzi)

Parser for [openmensa.org](https://openmensa.org/) for canteens of
[Studierendenwerk Frankfurt](https://www.swffm.de/essen-trinken/speiseplaene),
and [Canteen Taberna (Speyer)](https://www.speierlinghof.de/taberna/),

Parser für [openmensa.org](https://openmensa.org/) für die Mensen des
[Studierendenwerk Frankfurt](https://www.swffm.de/essen-trinken/speiseplaene),
und [Canteen Taberna (Speyer)](https://www.speierlinghof.de/taberna/),

|  Feeds       |                                         Status                                                                                                                  |                     Cron                                                                                                                                      |
|:------------:|:---------------------------------------------------------------------------------------------------------------------------------------------------------------:|:-------------------------------------------------------------------------------------------------------------------------------------------------------------:|
| today        | [![RunParsersToday](https://github.com/maximilian-schabarum/mensa/actions/workflows/updateFeedToday.yml/badge.svg)](https://github.com/maximilian-schabarum/mensa/actions/workflows/updateFeedToday.yml) | [*/15 3-12 * * 1-5](https://crontab.guru/#*/15_3-12_*_*_1-5 "Every 15 minutes from 3 through 12 on every day-of-week from Monday through Friday.") |
| all          | [![RunParsers](https://github.com/maximilian-schabarum/mensa/actions/workflows/updateFeed.yml/badge.svg)](https://github.com/maximilian-schabarum/mensa/actions/workflows/updateFeed.yml)                | [31 6,8 * * *](https://crontab.guru/#31_6,8_*_*_* "“At minute 31 past hour 6 and 8.” ")                                                                                                 |


Links:
*   See the resulting feeds at [https://maximilian-schabarum.github.io/mensa/](https://maximilian-schabarum.github.io/mensa/)
*   [Understand OpenMensa’s Parser Concept](https://doc.openmensa.org/parsers/understand/)
*   OpenMensa [XML schema](https://doc.openmensa.org/feed/v2/)
*   OpenMensa Android app on [f-droid](https://f-droid.org/en/packages/de.uni_potsdam.hpi.openmensa/), [playstore](https://play.google.com/store/apps/details?id=de.uni_potsdam.hpi.openmensa), [github](https://github.com/domoritz/open-mensa-android)
