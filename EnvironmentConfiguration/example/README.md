# Пример загрузки конфигурации PHP и Compose

Минимальный PHP CLI + Symfony Dotenv, без полного фреймворка и подключения к БД. Все значения демонстрационные. Fake token намеренно хранится в репозитории; настоящие credentials сюда не добавлять.

## Требования и запуск

PHP >=8.2, Composer, Python 3; для контейнерного опыта Docker Compose. Зависимость закреплена в composer.lock. Docker image закреплён digest; registry может потребоваться для первого скачивания.

```sh
composer install --no-plugins --no-scripts
python3 check.py
php dotenv-probe.php
docker compose -p env-guide-article run --rm --no-deps app
```

Локальный запуск без проверочного скрипта:

```sh
APP_TOKEN_FILE="$PWD/secrets/demo-token.txt" php app/config.php
DB_HOST=from-process APP_TOKEN_FILE="$PWD/secrets/demo-token.txt" php app/config.php
```

В Compose корневой .env участвует в интерполяции, DB_HOST передаётся явно. PHP сам читает app/.env. Secret выдаётся через /run/secrets/demo_token. Контейнер без сети, портов, persistent volumes и Docker socket; app/vendor монтируются read-only. Контейнер удаляется после команды.

## Что проверено

- PHP 8.5.9 локально, PHP 8.4.26 в официальном контейнере; Symfony Dotenv 7.4.18, Compose 2.38.2-desktop.1.
- Local check.py: defaults, process override, invalid port, invalid boolean, missing secret, fake secret отсутствует в stdout/stderr.
- Dotenv probe: local override меняет host, и зависимый URL пересчитывается с local host. Запускать в чистом окружении без APP_ENV и ENV_GUIDE_*.
- Runtime: host from-compose, file token прочитан, содержимого токена нет в выводе. Результат в runtime-results.json.

## Границы примера

origin различает только process-at-bootstrap и dotenv, не определяет точный исходный файл/CI-переменную. DB_HOST выводится как явно публичное искусственное значение; для production это требует отдельной политики. valid означает только выполненные проверки (для host — непустота), не полноценную схему всех настроек. APP_TOKEN_FILE — файловый путь, его содержимое не выводится; соглашение реализовано нашим кодом.

Нет проверки Laravel cache, полного Symfony container, Kubernetes rotation или sandbox агентов. Это не production-шаблон, а небольшой лабораторный пример для статьи.
