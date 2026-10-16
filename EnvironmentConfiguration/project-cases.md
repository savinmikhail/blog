# Практические случаи из собственных проектов

Дата чтения: 16 октября 2026. Read-only разбор Interviews и auth-service; последнее имя подтверждено пользователем. Настоящие dotenv/credentials/keys не читались, production не проверялся, проекты не менялись. В статье используются обезличенные механизмы. Пути ниже относительны к соответствующему локальному репозиторию, не являются публичными ссылками.

HEAD при чтении: Interviews `eba6e1fa02f07d38153981b8a5e1b65ae5666c12`; auth-service `ac2df6b4d91a1b68f8cf4d769e4c4e0458574b75`. Это идентификаторы checkout, не доказательства текущего deployed состояния. Затронутые доказательные файлы Interviews соответствуют указанному HEAD (git status пустой для всех 18 файлов); auth-service был clean. Выводы относятся к прочитанному коду, не production.

| Урок | Кодовое доказательство | Что можно утверждать |
|---|---|---|
| Безопасный helper не закрывает предыдущий Make include | Interviews: `Makefile:59-67,87`; `scripts/dotenv-for-check.py:11-28` | Проверять весь entrypoint; эксплуатации через полный pipeline не проводилось |
| Проверка и запуск могут использовать разные грамматики и приоритеты | auth-service: `Makefile:3-9,27-35`; `deployments/verify-prod-env.sh:4-16` | Make, shell и Compose читают одинаковые файлы разными механизмами; конкретная prod-коллизия не наблюдалась |
| Есть второй expansion внутри приложения | auth-service: `app/internal/platform/config/config.go:13-15`; `config_test.go:132-150` | Составная строка может вычисляться после Compose; существующие тесты прочитаны, не запускались |
| Env feature flag остаётся snapshot | Interviews: `app/src/StudentContext/StudentContextFeatureFlags.php:7-14`, `app/config/services.yaml:145-150`; auth-service: `app/cmd/auth-service/main.go:21-27` | Readonly DI/config-object сам не перечитывает изменённое env; поведение конкретного web lifecycle зависит от запуска |
| Один файл доставляется двумя путями | Interviews: `docker-compose.yml:31-61`; `docker-compose.prod.yml:6-11`; `docker/php/conf/www.conf:16` | Env при создании контейнера и mounted file могут обновляться независимо; фактическое stale значение в prod не установлено |
| Обновление ConfigMap/Secret и rollout приложения — разные операции | auth-service: `deployments/helm/auth-service/templates/deployment.yaml:20-25,75-79`; `redis.yaml:35-38`, `postgres.yaml:35-38` | В app template нет аналогичной checksum/config аннотации; нельзя по одному chart объявлять весь deployment сломанным |
| Диагностика может сравнивать отношения без раскрытия | Interviews: `scripts/local/check-identity-config.py:35-85` | Есть helper comparison matches/MISMATCH; его simplified parser не является точным runtime provenance |
| Писателю env нужны scope, permissions и atomicity | Interviews: `scripts/local/check-identity-config.py:88-125`; `scripts/merge_dotenv.sh:12-75` | Есть dev guard/allowlist/temp/replace; это не доказательство отсутствия race conditions и обновления существующего bind mount |
| Секрет скрыт в ошибке, но попадает в argv | auth-service: `deployments/verify-prod-env.sh:49-68` | Аудитировать передачу между процессами; доступность argv внешнему читателю зависит от ОС и не тестировалась |
| Генератор тоже является парсером | auth-service: `deployments/scripts/gen_secrets_env.py:13-39` | На synthetic input проверены неверные ключи для комментария с '=', export и quoted placeholder; production файл не использовался |
| «Env не обновился» бывает другим checkout | Interviews: `scripts/local/compose-run.sh:41-67`; `scripts/local/doctor.sh:75-100` | Есть проверка project/mount/checkout; не факт, что пользователь сейчас запускает неправильный проект |

## Выполненный синтетический опыт с генератором

Прочитан модуль генератора auth-service без вызова main. Во временном файле использованы только `# note=example`, `TOKEN="change-me"`, `export MODE=dev`. Его текущий split-parser получил ключи `# note`, `TOKEN`, `export MODE`; quoted placeholder не был распознан как placeholder. Это результат конкретного самописного скрипта, а не python-dotenv.

## Как включено в гайд

- Раздел 5: конкурирующие каналы доставки и один владелец интерполяции.
- Раздел 6: startup toggles против dynamic feature flags; наличие таблицы/ConfigMap само по себе не даёт обновления.
- Раздел 8: весь pipeline, а не безопасность последнего helper.
- Раздел 10: отношения между настройками, argv, генератор/запись/backup/mount.
- Раздел 13: идентичность реального потребителя и симптомы устаревшего флага.

Потенциальные улучшения собственного кода здесь не реализуются. Этот материал не является заявлением об инциденте или exploitable production vulnerability.
