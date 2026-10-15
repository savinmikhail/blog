# Исследование: конфигурация, dotenv и происхождение значений

Проверено по первичной документации 16 октября 2026. Это исследовательские заметки, не готовая статья. Эксперименты ниже предложены, но не выполнены. Версии зависимостей в статье должны быть зафиксированы отдельно; ссылки current/latest дрейфуют.

## Вывод для редакции

Сильная статья получается не из списка файлов `.env`, а из вопроса: «Кто, когда и для какого процесса вычисляет значение — и кому после этого оно доступно?» Иерархия файлов решает воспроизводимость; отдельный канал секретов решает доступ; маскирование решает представление; это три независимых свойства.

Не выдавать разделение `.env` и `.env.local` за новую практику. Можно дать новое прикладное соединение: воспроизводимый пример двойной интерполяции + схема происхождения значения + безопасный диагностический отчёт для человека/AI вместо полного дампа.

## Есть ли единая спецификация

Node прямо пишет, что общей формальной спецификации dotenv нет, и определяет свою. Значения из файлов — строки, в том числе `true`, `0` и JSON-подобные значения. Допустимые имена определены регулярным выражением. Поэтому «dotenv — shell script» нельзя переносить на все инструменты. [Node Environment Variables](https://nodejs.org/api/environment_variables.html)

12-factor — методология, а не RFC синтаксиса `.env`. Она рекомендует выносить меняющуюся между deployments конфигурацию из кода и управлять отдельными переменными, предостерегая от комбинаторного разрастания именованных наборов окружений. Это полезный контрапункт универсальному совету плодить `.env.prod`, `.env.staging`, `.env.customerN`. [12-factor Config](https://12factor.net/config)

Вывод автора: намерение «версионировать безопасные defaults» обоснованно, но имя файла и порядок загрузки следует брать у фреймворка. Иначе команда заводит собственный протокол поверх чужого.

## Экосистемы: короткая карта различий

### Symfony

Низкий → высокий приоритет стандартной загрузки: `.env`, `.env.local`, `.env.<environment>`, `.env.<environment>.local`; реальные env обычно выше. В test `.env.local` пропускается. Можно явно включить `overrideExistingVars`, поэтому правило «реальное окружение всегда побеждает» условно. Несекретные общие `.env` коммитятся, local — нет. `dump-env` создаёт `.env.local.php`, после чего текстовые файлы не парсятся обычным способом. `debug:dotenv` показывает происхождение и значения; `debug:container --env-vars` тоже показывает значения. Удобно для отладки, опасно пересылать без фильтрации. [Symfony configuration](https://symfony.com/doc/current/configuration.html#overriding-environment-values-via-env-local)

### Laravel

Конвенция обратная: `.env` не коммитить, держать `.env.example`. Внешние env переопределяют файл. Внешний `APP_ENV`/`--env` выбирает `.env.[APP_ENV]`, если он есть. Это не универсальная Symfony-иерархия. После `config:cache` `.env` перестаёт загружаться; `env()` вне config получает только внешнее окружение. Значит, «поменял файл — поменял приложение» может быть ложным. Laravel также поддерживает шифрование env-файла, но ключ дешифровки всё равно требует отдельного канала. [Laravel configuration](https://laravel.com/docs/12.x/configuration)

### Node

Встроенный `--env-file`: реальное окружение приоритетнее файла; при нескольких флагах поздний файл перекрывает предыдущий. Нет встроенного соглашения, автоматически выбирающего `.env.production.local` для любого Node-проекта: это может делать framework/обвязка. Для публикации фиксировать конкретную LTS, потому что поддержка флагов и multiline менялась. [Node CLI](https://nodejs.org/api/cli.html#--env-filefile)

### Python / python-dotenv

`load_dotenv()` по умолчанию не перекрывает существующие env; `override=True` меняет и приоритет интерполяции. Раскрывает `${NAME}`, не `$NAME`. `dotenv_values()` возвращает словарь; можно самостоятельно объединить shared → secret → `os.environ`. Однако каждое чтение файла уже интерполирует его отдельно: позднее объединение словарей не обязано пересчитать ранее построенный URL. `KEY` без `=` и `KEY=` — разные случаи. [python-dotenv](https://bbc2.github.io/python-dotenv/)

### Spring Boot

Здесь единица конфигурации — property source, не dotenv-файл. Из обычных источников: config data ниже OS env, ниже Java system properties, ниже command line (полный порядок содержит дополнительные источники). Есть profiles, imports, типизированное связывание. `configtree:` читает файлы в каталоге как свойства, включая mounted secrets из `/run/secrets/`. Это позволяет приложению потреблять секрет как файл без промежуточного экспорта в env. [Spring Externalized Configuration](https://docs.spring.io/spring-boot/reference/features/external-config.html)

### ASP.NET Core

Стандартный application config, высокий → низкий: CLI, env, development user secrets, `appsettings.{Environment}.json`, `appsettings.json`, fallback host config. Host config имеет отдельные правила и ранние bootstrap values. `__` в env представляет иерархию ключей. Значит, env может служить транспортом структурированной конфигурации, а не единственным местом её хранения. [ASP.NET configuration](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/configuration/?view=aspnetcore-10.0)

## Compose: две разные задачи с похожими именами

Для интерполяции YAML Compose использует shell/свои env-файлы. Сам факт наличия ключа в host `.env` не передаёт его контейнеру. Передача требует `environment`, service `env_file` либо иного явного механизма. Несколько `--env-file` читаются по порядку, поздние переопределяют ранние. `config --environment` показывает входные значения интерполяции. [Compose interpolation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/)

Для окружения контейнера есть свой порядок: явный `run -e` выше настроек сервиса; service `environment` перекрывает `env_file`, тот перекрывает image ENV. Host environment участвует лишь через выбранный механизм переноса/подстановки — не автоматически. При объяснении разделять явное значение `FOO=x` и перенос `FOO` без значения: для переноса источник разрешается дополнительно. [Compose precedence](https://docs.docker.com/compose/how-tos/environment-variables/envvars-precedence/)

В service `env_file` поздний файл перекрывает ранний. `environment` выше даже при пустом/неопределённом значении. `required: false` доступен с Compose 2.24; `format: raw` — с 2.30: raw сохраняет `$` и кавычки как есть, это контроль парсинга, НЕ маскирование/шифрование. Обычный парсер обрабатывает quoted/unquoted значения по своим правилам. [Compose service specification](https://docs.docker.com/reference/compose-file/services/#env_file)

Предупреждение редактору: в официальном tutorial попадается пример `docker compose up -e ...`; не копировать непроверенным. Для воспроизводимого CLI override использовать документированный `docker compose run -e ...` либо shell prefix для интерполяции.

## Kubernetes уже разделяет конфигурацию и секреты

ConfigMap предназначен для несекретных данных, Secret — для секретных. Это семантическое и операционное разделение, а не магическое шифрование. Secret по умолчанию хранится в etcd без encryption at rest. Нужны RBAC, encryption at rest, ограничение доступа контейнеров; право создавать Pod в namespace может дать косвенный доступ к его секретам. Не писать «base64 защищает данные». [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)

Способ доставки меняет поведение обновлений. ConfigMap в environment не обновляется без restart Pod; projected volume обновляется eventually, но subPath не получает эти обновления. После изменения файла само приложение ещё должно перечитать данные — это отдельная ответственность. [Kubernetes ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)

Авторский вывод: классификация secret/public полезна и до Kubernetes, но она не должна смешиваться с механизмом доставки (env/file/API) и жизненным циклом (startup/reload/rotation).

## Пример зрелого маскирования

Spring Actuator `/env`, `/configprops`, `/quartz` по умолчанию маскируют ВСЕ значения. Можно настроить `show-values` и `SanitizingFunction`. Это полезнее для статьи, чем совет искать в имени ключа `PASSWORD`: безопасный default не угадывает чувствительность. Включение показа авторизованным пользователям — отдельное решение; оно не меняет права процесса на исходные данные. [Spring Actuator sanitization](https://docs.spring.io/spring-boot/reference/actuator/endpoints.html#actuator.endpoints.sanitization)

## Что добавить своего: контракт конфигурации

Предложение автора, не существующий стандарт:

```yaml
DATABASE_URL:
  type: dsn
  sensitivity: secret
  required: true
  scope: app
  reload: restart
PUBLIC_BASE_URL:
  type: url
  sensitivity: public
  required: true
  scope: app
  reload: restart
```

Из него можно строить `.env.example`, проверку обязательности/типов и безопасный diagnostic report. Не печатать actual secret или его хеш по умолчанию: короткие/низкоэнтропийные секреты позволяют перебор. Достаточно `present`, `valid`, `origin`, `override chain`, `restart required`. Для public-поля разрешать показ только по allowlist. Значения должны редактироваться до записи в логи, артефакты CI и модельный контекст.

Особенно интересный момент для читателя: неправильный override способен заменить не только credential, но и endpoint. Поэтому полезно проверять origin/host/protocol DSN без печати user/password и не считать любую строку из окружения доверенной.

## Синтетические эксперименты для статьи (не запускались)

1. Один ключ `EXAMPLE_COLOR` во всех источниках, значения `from-shell/from-base/from-local/from-service`. Вывести только его и версию загрузчика. Получить таблицу фактического победителя для каждого режима.
2. Разделить `DB_HOST`, `DB_PASSWORD`, `DATABASE_URL`. Построить URL в base-файле, изменить компоненты поздним override. Проверить, пересобирает ли загрузчик уже вычисленный URL. Повторить отдельно для Symfony, Python dict merge, Compose. Не объявлять результат общим заранее.
3. Матрица парсеров: `$NAME`, `${NAME}`, одинарные/двойные кавычки, `#` с пробелом/без, `EMPTY=`, отсутствующий ключ, multiline, `$` в синтетическом пароле. Сравнить Node native, Compose, python-dotenv. Результаты привязать к версиям.
4. Compose с двумя отдельными значениями: interpolation key выбирает image tag, service env_file задаёт app key. Показать, что первый отсутствует в `env` контейнера, если не передан явно. Затем `environment` с пустой строкой перекрывает env_file.
5. Laravel config:cache: поменять синтетический `.env` после кеша, сравнить `env()` и `config()`; явно очистить кеш после эксперимента.
6. K8s local test: одинаковый public config доставить через env и volume, поменять ConfigMap, проверить env нового/старого Pod и eventually файл. Секретов не использовать, проверять только модель обновления.

Ценность статьи — маленький проверяемый лабораторный репозиторий с golden-output и одной схемой data flow. Энциклопедию всех загрузчиков лучше оставить приложением, чтобы не утопить историю пользователя.
