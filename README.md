# gta-map-assets

Зеркало части данных [gtadb.org](https://gtadb.org) для приложения Secret Base:
плитки карты GTA V (основной набор — **radar**, карта как в меню паузы игры; запасной — спутник)
и кадры игры к точкам «игра ↔ реальный мир».
Раздаётся через GitHub Pages: **https://appshalamov.github.io/gta-map-assets/**

Зачем: раньше приложение грузило всё прямо с `raw.githubusercontent.com/rolux/gtadb.org`.
Автор gtadb просит так не делать («Please do not fetch live data or media from gtadb.org –
simply `git pull`»), а у raw-адресов GitHub лимиты на анонимные запросы — в день выхода GTA VI
(19.11.2026) карта могла бы получать 429. Файлы взяты через git (blobless sparse-клон), как просит автор.

## Адреса

База: `https://appshalamov.github.io/gta-map-assets/` — пути те же, что в репозитории gtadb,
поэтому переключение = замена префикса `https://raw.githubusercontent.com/rolux/gtadb.org/main/`
на базу выше (только для плиток и `,ig.jpg`).

| Что | Шаблон |
|---|---|
| **Плитка GTA V, radar — основной набор** | `https://appshalamov.github.io/gta-map-assets/maps/tiles/5/radar/{z}/{z},{y},{x}.jpg` |
| Плитка GTA V, спутник (запасной) | `https://appshalamov.github.io/gta-map-assets/maps/tiles/5/satellite/{z}/{z},{y},{x}.jpg` |
| Кадр игры GTA V | `https://appshalamov.github.io/gta-map-assets/map/photos/5/{Lid},ig.jpg` |
| Кадр игры GTA VI | `https://appshalamov.github.io/gta-map-assets/map/photos/6/{Lid},ig.jpg` |
| Что лежит (зумы, число файлов, коммит gtadb) | `https://appshalamov.github.io/gta-map-assets/manifest.json` |

Плитки (оба набора): z = 0…6 (зум gtadb; в MapLibre это z + 2, т. е. minzoom 2 … maxzoom 8), мир 1024·2^z px,
плитка 256 px. Плиток вне карты (море по краям) в gtadb нет — по таким адресам 404, как и у gtadb.
GitHub Pages отдаёт `Access-Control-Allow-Origin: *` и `Cache-Control: max-age=600`.

## Что здесь есть (14.10.2026, gtadb `24af4bf`)

| Набор | Файлов | Объём |
|---|---:|---:|
| **Плитки GTA V radar**, z0 / z1 / z2 / z3 | 6 / 20 / 48 / 140 | 1,3 МБ |
| — z4 (мини-карта «Где в игре») | 513 | 2,4 МБ |
| — z5 | 1 961 | 6,8 МБ |
| — z6 | 7 632 | 20,4 МБ |
| Плитки GTA V satellite, z0 / z1 / z2 / z3 | 6 / 20 / 48 / 140 | 1,5 МБ |
| — z4 | 513 | 3,8 МБ |
| — z5 | 1 961 | 14,9 МБ |
| — z6 | 7 632 | 54,5 МБ |
| Кадры игры GTA V `,ig.jpg` | 947 | 38,6 МБ |
| Кадры игры GTA VI `,ig.jpg` | 714 | 58,2 МБ |
| **Итого** | **≈ 22 300** | **≈ 202 МБ** |

Самый большой файл — 1,97 МБ. Точные цифры после каждого обновления — в `manifest.json`.

## Решение по размеру

Один репозиторий, все зумы (0…6 — максимум, что есть в gtadb) двух наборов, без деления:
≈ 202 МБ при лимитах GitHub Pages ~1 ГБ на сайт, 100 МБ на файл и рекомендуемых 1–2 ГБ на репозиторий.
Запас — примерно 5×. Основной набор — radar (решение Игоря 14.10.2026: карта как в меню паузы игры);
satellite оставлен запасным, раз уже выложен. Мягкий лимит трафика Pages — ~100 ГБ в месяц:
средняя плитка radar z6 ≈ 3 КБ (спутник ≈ 7 КБ), кадр ≈ 40–80 КБ,
так что сеанс с картой и десятком кадров — порядка 1–3 МБ, т. е. десятки тысяч сеансов в месяц.
Если упрёмся в трафик — вынести на CDN (Cloudflare перед своим доменом) или разнести по репозиториям.

Кадры — только те, что нужны приложению (не все 4 600 из gtadb): ссылки `…/map/photos/{5|6}/{Lid},ig.jpg`
в `data/map/gta5.json` и `gta6.json` и точки слоя `gtadb_gta5.json` / `gtadb_gta6.json`
(основное приложение и `beta/data/map`)
(`points[i][0]` = Lid, `points[i][7] == 1` — кадр игры есть).

**Не переносится и не должно сюда попасть:**
- фото из жизни `,rl.jpg` — это скриншоты Google Street View, хранить их у себя нельзя; остаются ссылкой на gtadb;
- плитки GTA VI (yanis, dupzor и др.) — собраны по утечкам, карта GTA VI в приложении выключена;
- всё остальное из gtadb (GTA IV, слои hybrid / roadmap / terrain карты GTA V, данные, код).

## Обновление

Автоматически: GitHub Actions `sync-from-gtadb` (`.github/workflows/sync.yml`) раз в 3 часа берёт
`data/map` и `beta/data/map` из `appshalamov/gta-cheats-demo`, делает blobless sparse-клон gtadb, докачивает только
недостающие или изменившиеся файлы (сверка по git-хэшу), коммитит и пересобирает Pages.
Вручную запустить сразу после правки данных приложения:

```bash
gh workflow run sync.yml -R appshalamov/gta-map-assets
```

Локально (Mac, клон gtadb в `~/Developer/gtadb.org`, только стандартная библиотека Python):

```bash
python3 -I tools/sync_from_gtadb.py \
  --app-data "/Volumes/Work SSD/Система/Cloude/GTA 5:6 /cheats-pwa/data/map" \
  --app-data "/Volumes/Work SSD/Система/Cloude/GTA 5:6 /cheats-pwa/beta/data/map"
```

Файлы только добавляются и обновляются — то, что пропало из данных приложения, не удаляется
(старые версии приложения в кэше могут на это ссылаться).

Рабочая копия лежит на внешнем SSD (exFAT): macOS создаёт рядом с файлами служебные `._*` —
они в `.gitignore`. Из-за кластера exFAT 128 КБ папка занимает на диске ~5,5 ГБ при 202 МБ данных.
Сама git-папка — на Маке: `~/Developer/gta-map-assets.git` (в рабочей копии вместо папки `.git` лежит
файл `.git` со ссылкой). Внутри `.git` на exFAT те же `._*` ломают git («non-monotonic index»).
На другом Маке: `git clone https://github.com/appshalamov/gta-map-assets.git` — или поправить путь в файле `.git`.

## Свой домен

Сейчас бесплатный `appshalamov.github.io`. Свой домен: файл `CNAME` в корне + DNS (CNAME на
`appshalamov.github.io`) + `gh api -X PUT repos/appshalamov/gta-map-assets/pages -f cname=…`.
После смены — заменить базу в приложении.

## Источник и лицензия

- Данные и изображения: **gtadb.org (CC BY 4.0)** — https://map.gtadb.org,
  https://github.com/rolux/gtadb.org. Атрибуция: «gtadb.org and all contributors».
  Лицензия данных — `gtadb-LICENSE-DATA`, кода gtadb — `gtadb-LICENSE` (MIT).
  Изменения: файлы скопированы без изменений, взята только часть набора (см. выше).
- **Кадры и карта © Rockstar Games.** Grand Theft Auto — товарный знак Take-Two Interactive.
  Репозиторий не связан с Rockstar Games, Take-Two и gtadb.org.
- `tools/` и workflow — свои, MIT.
