# Аудит актуальности материалов env

Дата: 16 октября 2026. Проверены все 36 файлов, закоммиченных до этого обновления, и новые материалы. Это аудит согласованности досье и ограничений доказательств; внешние ссылки всего архива массово не перепроверялись, production не исследовался.

## Основные исправления

- research.md больше не содержит конкурирующий план из восьми разделов, статус «статья ещё не написана» или общий запрет считать Docker runtime проверенным. Вместо этого — текущая карта и отдельная матрица done/partial/not run.
- outline.md и article.md сохраняют 13 одинаковых верхних разделов; feature flags включены в §6.
- ecosystem/secrets notes различают ранние идеи опытов и выполненные subsets. Полный Symfony DI/Laravel/K8s, inspect, runtime dollar-count и agent policies не объявлены проверенными.
- audience notes содержат датированные данные и исторические варианты заголовков, а не второй принятый план.
- review.md помечен снимком редакции 755804d; его итог не распространяется автоматически на добавленные позже paragraphs.
- experiments/README требует Python >=3.11 для tomllib и отделяет свой config-only scope от runtime example/.
- raw JSON, composer.lock и original-note.md не переписаны; версии разных опытов намеренно не унифицированы.

## Пофайловая инвентаризация исходных 36 файлов

| Файл | Роль и результат проверки |
|---|---|
| [README.md](README.md) | Актуальный документ; 13 разделов и роли синхронизированы |
| [article.md](article.md) | Актуальный документ; 13 разделов и роли синхронизированы |
| [audience-data/stackexchange-search.json](audience-data/stackexchange-search.json) | Датированный результат/lock; байты и версии сохранены |
| [audience-data/stackexchange-selected.json](audience-data/stackexchange-selected.json) | Датированный результат/lock; байты и версии сохранены |
| [audience-data/trends-observation.json](audience-data/trends-observation.json) | Датированный результат/lock; байты и версии сохранены |
| [audience-demand.md](audience-demand.md) | Датированная справка; редакционные планы/статусы связаны с текущей картой |
| [audience-ecosystems.md](audience-ecosystems.md) | Датированная справка; редакционные планы/статусы связаны с текущей картой |
| [config-alternatives.md](config-alternatives.md) | Датированная справка; редакционные планы/статусы связаны с текущей картой |
| [config-vulnerabilities.md](config-vulnerabilities.md) | Датированная справка; редакционные планы/статусы связаны с текущей картой |
| [ecosystems-research.md](ecosystems-research.md) | Датированная справка; редакционные планы/статусы связаны с текущей картой |
| [example/.env](example/.env) | Код/fixture проверенного примера; изменений нет, runtime scope прежний |
| [example/.gitignore](example/.gitignore) | Код/fixture проверенного примера; изменений нет, runtime scope прежний |
| [example/README.md](example/README.md) | Код/fixture проверенного примера; изменений нет, runtime scope прежний |
| [example/app/.env](example/app/.env) | Код/fixture проверенного примера; изменений нет, runtime scope прежний |
| [example/app/config.php](example/app/config.php) | Код/fixture проверенного примера; изменений нет, runtime scope прежний |
| [example/check.py](example/check.py) | Код/fixture проверенного примера; изменений нет, runtime scope прежний |
| [example/compose.yaml](example/compose.yaml) | Код/fixture проверенного примера; изменений нет, runtime scope прежний |
| [example/composer.json](example/composer.json) | Датированный результат/lock; байты и версии сохранены |
| [example/composer.lock](example/composer.lock) | Датированный результат/lock; байты и версии сохранены |
| [example/dotenv-probe.php](example/dotenv-probe.php) | Код/fixture проверенного примера; изменений нет, runtime scope прежний |
| [example/dotenv-results.json](example/dotenv-results.json) | Датированный результат/lock; байты и версии сохранены |
| [example/local-results.json](example/local-results.json) | Датированный результат/lock; байты и версии сохранены |
| [example/runtime-results.json](example/runtime-results.json) | Датированный результат/lock; байты и версии сохранены |
| [example/secrets/demo-token.txt](example/secrets/demo-token.txt) | Код/fixture проверенного примера; изменений нет, runtime scope прежний |
| [experiments/README.md](experiments/README.md) | Требование Python >=3.11, scope config-only уточнены |
| [experiments/format-probe.py](experiments/format-probe.py) | Скрипт раннего опыта; код не изменён |
| [experiments/format-results.json](experiments/format-results.json) | Датированный результат/lock; байты и версии сохранены |
| [experiments/leak-probe.py](experiments/leak-probe.py) | Скрипт раннего опыта; код не изменён |
| [experiments/leak-results.json](experiments/leak-results.json) | Датированный результат/lock; байты и версии сохранены |
| [experiments/probe.py](experiments/probe.py) | Скрипт раннего опыта; код не изменён |
| [experiments/results.json](experiments/results.json) | Датированный результат/lock; байты и версии сохранены |
| [original-note.md](original-note.md) | Архив исходника; байты сохранены, прежние советы не текущая инструкция |
| [outline.md](outline.md) | Актуальный документ; 13 разделов и роли синхронизированы |
| [research.md](research.md) | Актуальный документ; 13 разделов и роли синхронизированы |
| [review.md](review.md) | Историческое ревью 755804d; добавлена явная граница снимка |
| [secrets-research.md](secrets-research.md) | Датированная справка; редакционные планы/статусы связаны с текущей картой |

## Новые материалы

- [project-cases.md](project-cases.md): обезличенные уроки и кодовые ссылки Interviews/auth-service. Затронутые evidence files Interviews clean на указанном HEAD, auth-service clean при чтении. Это не deployed/runtime verification.
- [feature-flags-research.md](feature-flags-research.md): OpenFeature provider/API и конкретный PHP SDK lifecycle, не обещание мгновенного обновления.
- Этот audit.md: инвентаризация и результаты проверки текущей редакции.

## Проверки

- JSON/lock parse, Python AST, закрытие Markdown fences и существование всех локальных Markdown targets (кроме неизменяемого original-note, который не принимается за действующие команды).
- Все 13 numbered H2 статьи совпадают с outline; текущие оглавление/таблицы не меняют верхнюю структуру.
- Byte comparison датированных JSON/lock с исходной редакцией; original-note дополнительно сравнен с первым архивным commit 4a2a6f1.
- Код примера не менялся, runtime/PHP проверки заново не запускались: результаты остаются датированными наблюдениями. Новые project lessons основаны на read-only code inspection и synthetic generator test, не на исправлении приложений.
- Независимое повторное ревью новых технических вставок: P1/P2 не обнаружены. Проверены startup env/dynamic flags, cached propagation, два канала доставки, argv, генератор и code/runtime границы.
- Четыре оформительских замечания ревью устранены: audit создан, historical scope вынесен в начало review, отсутствие agent-policy experiments сформулировано однозначно, оба новых досье добавлены в карту research.
- Повторный content review не выдаётся за повторный запуск интеграционных тестов или security audit приложений.
