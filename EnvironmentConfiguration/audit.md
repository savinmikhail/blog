# Аудит актуальности материалов env

Дата: 16 октября 2026. Текущая редакционная переработка после `9f6bdc6`. Проверены согласованность документов, ссылки, неизменность исходных снимков и обновлённый пример. Внешние ссылки всего исследовательского архива массово не перепроверялись; production не исследовался.

## Что изменилось

- Статья и outline сохраняют 13 разделов, но следуют эволюции одного приложения: один flat-файл → разделение/загрузка → кеш → интерполяция → секреты → динамические флаги. Feature flags теперь §10; LLM-агенты внутри безопасной диагностики §11.
- Исследовательская карта, project cases и flags notes обновлены под новые номера. Историческое первое ревью отделено от двух текущих независимых ревью.
- Запускаемый пример теперь читает DB_PASSWORD_FILE, строит DSN из компонентов и строго разбирает FEATURE_NEW_CHECKOUT. В памяти остаются значения для приложения; CLI печатает allowlisted metadata и искусственный host.
- Предыдущие local/runtime JSON с token и APP_DEBUG сохранены побайтно в example/history/first-draft/. Текущие snapshots описывают новый код, а не подменяют результаты прежнего запуска.
- Исходная заметка, raw JSON исследований/опытов, lock и версии parser probe не переписаны.

## Проверки и границы

- 15 локальных сценариев: defaults/override, типы/диапазоны/пустота, файл секрета, точная сборка DSN со спецсимволами, обе boolean-ветки, отсутствие экспорта credentials в process env и отсутствие пароля/DSN в отчёте. Отдельный malformed dotenv сценарий проверяет generic stderr без synthetic marker.
- PHP lint, JSON/lock parsing, Python AST, fences, локальные Markdown targets, TOC anchors и совпадение 13 numbered H2 статьи/outline.
- Symfony Dotenv 7.4.18: local override пересчитывает host и зависимый URL. Composer lock не менялся.
- Compose 2.38.2-desktop.1 / PHP 8.4.26: текущий контейнерный пример получает host из Compose, читает password-file, не выводит пароль или DSN. Image digest сохранён. Контейнер без сети и подключения к БД.
- Редакторский агент прочитал авторские статьи CI/CD и zsh; четыре точечных замечания устранены и повторно проверены. Технический агент нашёл P2 о loadEnv/bootEnv/Flex; исправление проверено, 15 локальных сценариев повторно прошли. Незакрытых замечаний этих двух проходов нет.
- Полный Symfony framework/Flex/cache, Laravel cache, Kubernetes, dynamic flag provider и политики AI-агентов не запускались. Они изложены по документации. DSN не проверялся реальным подключением к PostgreSQL; это лаборатория загрузки конфигурации.
- Код Interviews/auth-service не менялся, production-инциденты и exploitable vulnerability не заявляются. Предыдущий аудит `9f6bdc6` остаётся частью Git-истории.

## Пофайловая инвентаризация

Всего 45 файлов материалов; vendor исключён и не коммитится.

| Файл | Роль и результат |
|---|---|
| [README.md](README.md) | Карта материалов и границы выполненных проверок |
| [article.md](article.md) | Текущий сквозной гайд, 13 разделов; оглавление и ссылки проверены |
| [audience-data/stackexchange-search.json](audience-data/stackexchange-search.json) | Неизменённый ранний опыт/датированный снимок; область проверки не расширена |
| [audience-data/stackexchange-selected.json](audience-data/stackexchange-selected.json) | Неизменённый ранний опыт/датированный снимок; область проверки не расширена |
| [audience-data/trends-observation.json](audience-data/trends-observation.json) | Неизменённый ранний опыт/датированный снимок; область проверки не расширена |
| [audience-demand.md](audience-demand.md) | Исследовательская справка; исходные источники и датированные границы сохранены |
| [audience-ecosystems.md](audience-ecosystems.md) | Исследовательская справка; исходные источники и датированные границы сохранены |
| [audit.md](audit.md) | Текущая инвентаризация и ограничения доказательств |
| [config-alternatives.md](config-alternatives.md) | Исследовательская справка; исходные источники и датированные границы сохранены |
| [config-vulnerabilities.md](config-vulnerabilities.md) | Исследовательская справка; исходные источники и датированные границы сохранены |
| [ecosystems-research.md](ecosystems-research.md) | Исследовательская справка; исходные источники и датированные границы сохранены |
| [editorial-review.md](editorial-review.md) | Новое независимое ревью; все 4 замечания закрыты повторной проверкой |
| [example/.env](example/.env) | Текущий runnable example/документация; согласован со статьёй и проверен |
| [example/.gitignore](example/.gitignore) | Текущий runnable example/документация; согласован со статьёй и проверен |
| [example/README.md](example/README.md) | Текущий runnable example/документация; согласован со статьёй и проверен |
| [example/app/.env](example/app/.env) | Текущий runnable example/документация; согласован со статьёй и проверен |
| [example/app/config-values.php](example/app/config-values.php) | Текущий runnable example/документация; согласован со статьёй и проверен |
| [example/app/config.php](example/app/config.php) | Текущий runnable example/документация; согласован со статьёй и проверен |
| [example/check.py](example/check.py) | Текущий runnable example/документация; согласован со статьёй и проверен |
| [example/compose.yaml](example/compose.yaml) | Текущий runnable example/документация; согласован со статьёй и проверен |
| [example/composer.json](example/composer.json) | Неизменённый manifest/lock/снимок; версия сохранена |
| [example/composer.lock](example/composer.lock) | Неизменённый manifest/lock/снимок; версия сохранена |
| [example/dotenv-probe.php](example/dotenv-probe.php) | Текущий runnable example/документация; согласован со статьёй и проверен |
| [example/dotenv-results.json](example/dotenv-results.json) | Неизменённый manifest/lock/снимок; версия сохранена |
| [example/history/first-draft/README.md](example/history/first-draft/README.md) | Исторический результат token/APP_DEBUG до редакционной переработки; JSON сохранён побайтно |
| [example/history/first-draft/local-results.json](example/history/first-draft/local-results.json) | Исторический результат token/APP_DEBUG до редакционной переработки; JSON сохранён побайтно |
| [example/history/first-draft/runtime-results.json](example/history/first-draft/runtime-results.json) | Исторический результат token/APP_DEBUG до редакционной переработки; JSON сохранён побайтно |
| [example/local-results.json](example/local-results.json) | Новый результат запуска текущего кода на искусственных данных |
| [example/runtime-results.json](example/runtime-results.json) | Новый результат запуска текущего кода на искусственных данных |
| [example/secrets/db-password.txt](example/secrets/db-password.txt) | Текущий runnable example/документация; согласован со статьёй и проверен |
| [experiments/README.md](experiments/README.md) | Неизменённый ранний опыт/датированный снимок; область проверки не расширена |
| [experiments/format-probe.py](experiments/format-probe.py) | Неизменённый ранний опыт/датированный снимок; область проверки не расширена |
| [experiments/format-results.json](experiments/format-results.json) | Неизменённый ранний опыт/датированный снимок; область проверки не расширена |
| [experiments/leak-probe.py](experiments/leak-probe.py) | Неизменённый ранний опыт/датированный снимок; область проверки не расширена |
| [experiments/leak-results.json](experiments/leak-results.json) | Неизменённый ранний опыт/датированный снимок; область проверки не расширена |
| [experiments/probe.py](experiments/probe.py) | Неизменённый ранний опыт/датированный снимок; область проверки не расширена |
| [experiments/results.json](experiments/results.json) | Неизменённый ранний опыт/датированный снимок; область проверки не расширена |
| [feature-flags-research.md](feature-flags-research.md) | Источники и ограничения сохранены; ссылка на раздел 10 |
| [original-note.md](original-note.md) | Неизменяемый исходник; побайтное сравнение с первым архивным коммитом |
| [outline.md](outline.md) | Текущие 13 разделов и краткое содержание, порядок совпадает со статьёй |
| [project-cases.md](project-cases.md) | Кодовые доказательства сохранены; номера разделов обновлены |
| [research.md](research.md) | Карта доказательств; новый пример и два текущих ревью |
| [review.md](review.md) | Историческое ревью редакции 755804d; актуальные ревью обозначены отдельно |
| [secrets-research.md](secrets-research.md) | Исследовательская справка; исходные источники и датированные границы сохранены |
| [technical-review.md](technical-review.md) | Новое независимое ревью; P2 о loadEnv/bootEnv закрыт, 15 сценариев повторно прошли |
