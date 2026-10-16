# Пример загрузки конфигурации PHP и Compose

Небольшой PHP CLI + Symfony Dotenv без подключения к БД. Итоговая конфигурация из статьи: defaults приложения, внешнее переопределение host, пароль из отдельного файла, сборка DSN в PHP, строгий стартовый feature flag. Все значения искусственные. `secrets/db-password.txt` намеренно содержит публичную fixture, а не рабочий пароль.

## Запуск

Нужны PHP >=8.2, Composer, Python 3; для контейнерного опыта Docker Compose. Composer lock и digest Docker image закреплены. Первое скачивание зависимостей требует сети.

```sh
composer install --no-plugins --no-scripts
python3 check.py
php dotenv-probe.php
docker compose -p env-guide-article run --rm --no-deps app
```

Запуск вручную:

```sh
DB_PASSWORD_FILE="$PWD/secrets/db-password.txt" php app/config.php
DB_HOST=from-process DB_PASSWORD_FILE="$PWD/secrets/db-password.txt" php app/config.php
```

Корневой `.env` содержит `DEMO_DB_HOST` для интерполяции Compose. Compose явно передаёт `DB_HOST` и путь `/run/secrets/db_password`; PHP сам читает `app/.env`. В начале статьи есть условный HTTP-порт для объяснения стадий Compose, а эта CLI-лаборатория порт не открывает. Контейнер без сети, persistent volumes и Docker socket; app/vendor смонтированы read-only.

`app/config-values.php` возвращает значения для приложения. `app/config.php` печатает только отчёт: искусственный публичный host и метаданные. Пароль и DSN остаются в памяти, не экспортируются в process env. Отчёт не доказывает безопасность произвольного вызывающего кода.

## Проверки

- PHP 8.5.9 локально; PHP 8.4.26 в официальном контейнере; Symfony Dotenv 7.4.18, Compose 2.38.2-desktop.1.
- `check.py`: defaults, внешнее переопределение, невалидные порт/boolean/host/имя БД, пустой user, пустой путь, отсутствующий и пустой файл секрета; безопасная ошибка парсинга; отсутствие пароля/DSN в отчёте; точный DSN со спецсимволами, обе boolean-ветки, отсутствие экспорта в env. Результаты: [local-results.json](local-results.json).
- `dotenv-probe.php`: local override меняет host и зависимый URL. Запускать без внешних `APP_ENV` и `ENV_GUIDE_*`; результат версии 7.4.18 — [dotenv-results.json](dotenv-results.json).
- Контейнер: host приходит из Compose, файл пароля прочитан, пароль и DSN отсутствуют в отчёте. [runtime-results.json](runtime-results.json).
- [Исторические результаты](history/first-draft/README.md) сохранены отдельно: они относятся к прежнему примеру с token и APP_DEBUG.

## Границы

`origin` различает process-at-bootstrap и dotenv, без точного имени исходного файла. `valid` означает только проверки этого кода. Host допускает упрощённое DNS/IPv4-подобное имя, без проверки существования или полноценной сетевой грамматики; имя БД — буквы/цифры/underscore. IPv6, Unix sockets и другие DSN требуют правил своего драйвера. Текстовый пароль допускает завершающий перевод строки; для бинарных ключей это правило не подходит.

`DB_PASSWORD_FILE` поддерживает наш код, это не автоматическая возможность любого образа. Feature flag читается при старте; динамического provider здесь нет. Сгенерированный DSN не проверялся подключением к PostgreSQL. Полный Symfony framework/cache, Laravel config cache, Kubernetes rotation и sandbox агентов здесь не испытаны.
