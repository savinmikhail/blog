# Исследование и актуальная карта гайда по env

Актуализировано 16 октября 2026 после подготовки полного черновика и его ревью. Это карта материалов и доказательств; текущий текст — [article.md](article.md), единственная принятая структура — [outline.md](outline.md), 13 разделов. Ранний план из восьми разделов заменён, дублирующий план здесь не поддерживается.

## Состояние материалов

| Материал | Роль и актуальный статус |
|---|---|
| [article.md](article.md) | Полный черновик, ещё не опубликован на Хабре |
| [outline.md](outline.md) | Принятая структура из 13 разделов; feature flags внутри жизненного цикла конфигурации |
| [review.md](review.md) | Исторический снимок первого ревью и его повторной проверки; не автоматическая гарантия для последующих правок |
| [original-note.md](original-note.md) | Побайтно сохранённый исходник; содержит прежние советы, которые статья уточняет; не текущая инструкция |
| [example/README.md](example/README.md) | Проверенный PHP + Symfony Dotenv + Compose пример |
| [experiments/README.md](experiments/README.md) | Ранние parser/config-only опыты; их границы не расширяются от появления runtime-примера |
| [ecosystems-research.md](ecosystems-research.md) | Справка о соглашениях загрузчиков с уточнениями по версии Symfony |
| [secrets-research.md](secrets-research.md) | Справка о доступе, доставке, маскировании и агентах |
| [config-alternatives.md](config-alternatives.md) | Форматы/контракты/вычисление/доставка как отдельные решения |
| [config-vulnerabilities.md](config-vulnerabilities.md) | Конкретные CVE и условия атак, без эксплуатации CVE |
| [audience-demand.md](audience-demand.md), [audience-ecosystems.md](audience-ecosystems.md) | Датированная выборка вопросов; не monthly search volume |
| [project-cases.md](project-cases.md) | Обезличенные уроки из кода Interviews/auth-service; один synthetic generator test, не production audit |
| [feature-flags-research.md](feature-flags-research.md) | Первичные источники dynamic flag lifecycle; SDK не запускался |
| [audit.md](audit.md) | Пофайловый аудит актуальности и границ доказательств |

## Что проверено экспериментально

| Проверка | Артефакт | Что доказано и чего не доказывает |
|---|---|---|
| Node/Bash/Make/Compose читают один файл | [experiments/results.json](experiments/results.json) | Различия EXPANDED/LITERAL для записанных версий; Compose-строка — вывод config, не runtime dollar-count |
| Compose shell и два --env-file | [experiments/results.json](experiments/results.json) | В этой конфигурации shell перекрывает поздний файл, поздний — ранний; отдельный service env_file задаёт другие ключи |
| Config выводит искусственный env-secret | [experiments/leak-results.json](experiments/leak-results.json) | Plaintext присутствует в resolved environment; file-secret definition содержит путь; inspect не проверялся |
| chmod 600, чтение владельцем | [experiments/leak-results.json](experiments/leak-results.json) | Владелец читает; другой UID и Linux permissions этим не проверены |
| JSON duplicates / TOML / source | [experiments/format-results.json](experiments/format-results.json) | Последний JSON key в Python; TOML duplicate error; Bash исполняет printf, Node сохраняет строку |
| PHP defaults, process override, validation | [example/local-results.json](example/local-results.json) | Порт/boolean/missing file, fake secret отсутствует в stdout/stderr этого примера |
| Symfony Dotenv loadEnv интерполяция слоёв | [example/dotenv-results.json](example/dotenv-results.json) | В 7.4.18 host и зависимый URL получили local значение; нельзя переносить stale-DSN результат другой реализации |
| PHP внутри Compose, file secret | [example/runtime-results.json](example/runtime-results.json) | DB_HOST пришёл из Compose, token-file прочитан, token отсутствует в выводе; не полный Symfony framework и не prod audit |

Версии не усредняются: ранний parser probe использовал Node 26.10.0, format probe — 24.20.0; PHP локально 8.5.9, в контейнере 8.4.26; Symfony Dotenv 7.4.18. Зафиксированные версии и digest находятся рядом с результатами.

## Что остаётся документальной проверкой или дальнейшим опытом

- Laravel config:cache и полный Symfony DI/cache/dump workflow описаны по документации, не испытаны этим примером.
- Docker inspect, runtime dollar-count, actual mount permissions отдельного UID не проверены. Runtime-пример из example/ не закрывает эти задачи автоматически.
- Kubernetes env против volume, subPath/reload и ротация описаны по документации, локального кластера для теста не создавалось.
- Python dotenv multi-file dictionary merge описан по документации; пакет в лабораторию не добавлялся.
- Политики AI-агентов, direct Read против subprocess/MCP и credentials proxy экспериментально не проверялись; настоящие ключи не использовались.
- Dynamic feature-flag store/SDK не установлен и не запускался. Чтение кода собственных проектов не доказывает deployed/runtime состояние.
- CVE приведены по advisory; уязвимые версии не эксплуатировались.

Это отдельные направления дальнейшей валидации, не условия, что статья «ещё не написана».

## Редакционные решения, принятые в тексте

- Формат — широкий практический гайд; вопросы «не загрузилось / старое значение / утекло» помогают навигации, но не сужают согласованный охват.
- Env process, файл, загрузчик, типизированная конфигурация, кеш и dynamic flags различаются явно.
- Приоритеты Compose разделены на интерполяцию модели и окружение сервиса; далее приложение имеет собственную загрузку.
- Советы о коммите несекретных defaults учитывают соглашения Symfony/Laravel, local overrides не редактируют tracked файл.
- COMPOSE_ENV_FILES экспортируется; разделение infra/app сопровождается явной передачей значений.
- Bash source, Make include и Symfony command substitution рассматриваются как исполнение с конкретными предпосылками.
- Полная provenance-цепочка не обещается: пример различает process-at-bootstrap и dotenv.
- Маскирование, шифрование, scanning и ограничения чтения решают разные задачи.
- Контракт конфигурации не объявляется новым стандартом: JSON Schema, CUE и dotenvx Envfile уже покрывают части задачи.

## Существующие публикации и границы новизны

Это ограниченная выборка, а не доказательство, что «все разработчики знают» или «нигде не обсуждалось»:

- [Python dotenv](https://habr.com/ru/articles/472674/) и [несколько env-файлов Compose](https://habr.com/ru/posts/842636/) — базовые механизмы давно обсуждались; полные тексты этих двух страниц не использовались для сравнительного анализа пропусков.
- [Docker secrets](https://habr.com/ru/articles/872128/) — полный текст просмотрен; важно развести runtime Compose secrets, Swarm и BuildKit. Технический источник — [официальный Compose how-to](https://docs.docker.com/compose/how-tos/use-secrets/).
- [Доставка секретов разработчику](https://habr.com/ru/companies/yandex_praktikum/articles/801047/) — полный текст просмотрен, уже есть разделение сред, TTL и сессионная доставка.

Прикладная ценность гайда — собрать совместимую модель, сопоставить реализации и дать воспроизводимые примеры с явно обозначенными границами. Исследование источников не подменяет собственный опыт, а собственный код не доказывает поведение всех стеков.
