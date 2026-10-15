Как организовывать .env файлы?

во многих проектах есть только один .env файл, и он в течение полугода уже превращается в помойку - порты для сервисов, ключи для приложения, фича флаги и проч

еще хуже дела обстоят в laravel проектах (по сравнению с symfony), потому что там принято не коммитить .env файл, а вести документацию в .env.example, конечно дока становится неактуальной. вдобавок в PHP-мире для коммитящихся примеров конфигов часто встречается суффикс .dist, а в Laravel почему-то закрепился именно .env.example

## .env можно коммитить

коммитить .env можно и нужно, важно лишь не хранить реальные продовые секреты в гите, ведь не все ваши переменные это секретные секреты?

к примеру так может выглядеть закоммиченный файл .env

```dotenv
# .env
POSTGRES_DB=app
POSTGRES_USER=app
POSTGRES_PASSWORD=change-me-in-.env.local
APP_HTTP_PORT=8080
GRAFANA_ADMIN_PASSWORD=change-me-in-.env.local
```

дальше наша задача при деплое на прод проверять, что эти переменные переопределены

переопределять их в файле, который трекается гитом, -- плохая идея, будут потом конфликты при git pull

поэтому это решается иерархией файлов

мы можем завести файл .env.local, загитигнорить его и там переопределить любые переменные, свойственные именно данной машине

при этом удобный подход - генерить этот файл в ci/cd из gitlab ci variables типа file, чтобы не прыгать по ssh

кто пишет на симфе - привычен к этому:

```text
.env              # закоммиченные значения по умолчанию
.env.local        # загитигноренные перегрузки
.env.test         # закоммиченные дефолты для тестов, например переопределение транспорта с rabbitmq на in-memory
.env.prod         # закоммиченные значения для прода, которые не зависят от стенда, например какие-то фича флаги или настройки - POSTGRES_SSLMODE=require, GRAFANA_SERVE_FROM_SUB_PATH=true
.env.prod.local   # можно делать и так, но обычно нет нужды, так как на одном стенде редко совмещаются разные режимы (дев и прод)
.env.local.php    # конкретно оптимизация в симфе, чтоб не парсить все эти файлы каждый раз. Он собирает один пхп массив с учетом иерархии, интерполяции и проч. Если он присутствует в файловой системе, то симфа будет читать только его
```

при подобном подходе мы уже заметно выигрываем с тем, что нам надо проверять\менять при релизах, и с тем, насколько трудно ориентироваться в файле

на чистой пыхе или в других фреймворках можно загрузить это через vlucas\dotenv или symfony\dotenv

кстати, для ориентации бывает делают визуальные группы комментариями. Опять же, в симфони это рецепты флекса как правило делают, но можно и не только в симфе делать руками

```dotenv
### < k8s
K8S_UI_ENABLED=true
K8S_UI_HOST=
K8S_UI_TLS_SECRET_NAME=
### > k8s

### < grafana
GRAFANA_PORT=3000
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=change-me-in-.env.local
GRAFANA_TELEGRAM_ENABLED=0
GRAFANA_TELEGRAM_BOT_TOKEN=
GRAFANA_TELEGRAM_CHAT_ID=
GRAFANA_HOST=
GRAFANA_TLS_SECRET_NAME=
### > grafana
```

## Разделяйте env приложения и env инфраструктуры

Следующим заметным улучшением организации будет не мешать runtime-настройки приложения и настройки инфраструктуры.
у нас есть, например, порты композа, настройки графаны и проч - это не имеет никакого отношения к самому приложению, и наоборот, всякие фича флаги приложения не нужны окружению, смешивая их мы ничего хорошего не получаем
можно сделать так:

```text
.env                  # infra defaults: compose project, ports, image, domains
.env.local            # local/private infra overrides

app/.env              # app runtime defaults: APP_ENV, LOG_LEVEL, DSN templates
app/.env.local        # app-only local secrets: API_KEY, APP_SECRET
```

например .env

```dotenv
COMPOSE_PROJECT_NAME=mock
POSTGRES_DB=app
POSTGRES_USER=app
POSTGRES_PASSWORD=change-me-in-.env.local
APP_HTTP_PORT=8080
APP_GRAFANA_ADMIN_PASSWORD=change-me-in-.env.local
```

app/.env

```dotenv
APP_ENV=dev
DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}?serverVersion=16&charset=utf8"
VOICE_STT_PROVIDER=aitunnel
```

таким образом мы получаем srp, и нам проще поддерживать переменные

## Подключение файлов

встает вопрос, как сказать докеру обрабатывать несколько енв файлов да еще и с приоритетом

можно сделать либо аргументом команды:

```bash
docker compose --env-file .env --env-file .env.local -f docker-compose.yml up -d
```

Либо экспортировать в сессию:

```bash
COMPOSE_ENV_FILES=.env,.env.local
```

Это переменные для самого Compose: интерполяция `${POSTGRES_PASSWORD}`, `${APP_HTTP_PORT}`, `${IMAGE_TAG}` в compose-файлах.

если переменные нужны в контейнере именно, то можно вот так прокинуть:

```yaml
services:
  app:
    env_file:
      - path: ./app/.env
        required: true
      - path: ./app/.env.local
        required: false
```

но это оч редко когда нужно, потому что Postgres не нужен Telegram token, nginx не нужен API_KEY, exporter не нужен OpenAI key и т.п.

`env_file` скорее нужен контейнерам, где приложение реально читает env из process environment. Symfony в dev-сетапе часто вообще получает `app/.env` через volume вместе с кодом, так что ей не обязательно прокидывать этот файл через Compose.

Глобального env_file "для всего docker compose" по сути нет.

для примера репозитория с таким подходом можете посмотреть - https://github.com/savinmikhail/symfony-template-docker

если у вас в проекте не только докер, но и helm\ansible и т.п., можно загружать через мейкфайл

```makefile
# Загружаем переменные из .env и .env.local (локальный имеет приоритет)
ifneq (,$(wildcard .env))
include .env
export
endif

ifneq (,$(wildcard .env.local))
include .env.local
export
endif
```

Хороший практический паттерн: в Makefile держать переменные с готовыми compose-командами:

```makefile
PROD_COMPOSE := docker compose --env-file .env --env-file .env.local -f docker-compose.yml -f docker-compose.prod.yml
DEV_COMPOSE := docker compose --env-file .env --env-file .env.local

up-prod:
	$(PROD_COMPOSE) up -d --wait --remove-orphans
	
up:
	$(DEV_COMPOSE) up -d
```

Тогда режимы dev/prod видны явно, и команду легко скопировать для ручного запуска.

дополнительно можете почитать о приоритетах енв переменных в докер композе у Валентина Удальцова - https://t.me/phpyh/918

## Интерполяция работает не везде одинаково

Кстати, в примере выше могли заметить интерполяцию переменных - она работает в symfony\dotenv и в docker compose

но при этом shell source, Makefile include, Symfony Dotenv и Docker Compose - это четыре разных парсера. У них разные правила кавычек, комментариев, default values и expansion.
Поэтому лучше не считать .env "универсальным форматом, который везде работает одинаково". Это скорее семейство похожих форматов.

это удобно в основном для DSN переменных, чтоб руками их не поддерживать, а прокидывать в контейнер из докер композа

например

```yaml
services:
  php:
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

## Deploy должен падать на дефолтных секретах

при деплое на стенд надо как-то следить, что мы заменили все секреты на сложные, иначе через неделю будет на вашей VPS-ке майниться крипта, говорю по своему опыту

у меня для этого есть скрипт, который запускается при деплое

```bash
#!/bin/sh
set -eu

mode=${1:-prod}
failed=0

require_secret() {
  var_name=$1
  insecure_default=$2
  eval "value=\${$var_name-}"

  if [ -z "${value}" ]; then
    echo "Missing required production env: ${var_name}" >&2
    failed=1
    return
  fi

  case "${value}" in
    "${insecure_default}"|change-me-in-.env.local|local-db-password-change-me)
      echo "Refusing production deploy: ${var_name} still uses a committed placeholder/default." >&2
      failed=1
      ;;
  esac
}

is_true() {
  case "${1:-}" in
    1|true|TRUE|yes|YES|on|ON)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

require_if_enabled() {
  enabled_var=$1
  required_var=$2
  eval "enabled_value=\${$enabled_var-}"

  if is_true "${enabled_value}"; then
    require_secret "${required_var}" ""
  fi
}

case "${mode}" in
  prod)
    require_secret POSTGRES_PASSWORD app
    require_secret APP_MINIO_ROOT_PASSWORD minio123
    require_secret IDENTITY_EXCHANGE_SECRET dev-identity-exchange-secret
    require_if_enabled POSTGRES_BACKUP_S3_ENABLED POSTGRES_BACKUP_S3_ENDPOINT
    require_if_enabled POSTGRES_BACKUP_S3_ENABLED POSTGRES_BACKUP_S3_REGION
    require_if_enabled POSTGRES_BACKUP_S3_ENABLED POSTGRES_BACKUP_S3_BUCKET
    require_if_enabled POSTGRES_BACKUP_S3_ENABLED POSTGRES_BACKUP_S3_ACCESS_KEY
    require_if_enabled POSTGRES_BACKUP_S3_ENABLED POSTGRES_BACKUP_S3_SECRET_KEY
    ;;
  monitoring)
    require_secret APP_GRAFANA_ADMIN_PASSWORD admin
    require_if_enabled APP_GRAFANA_TELEGRAM_ENABLED APP_GRAFANA_TELEGRAM_BOT_TOKEN
    require_if_enabled APP_GRAFANA_TELEGRAM_ENABLED APP_GRAFANA_TELEGRAM_CHAT_ID
    ;;
  *)
    echo "Unknown verification mode: ${mode}" >&2
    exit 1
    ;;
esac

if [ "${failed}" -ne 0 ]; then
  case "${mode}" in
    prod)
      echo "Override the production secrets in .env.local or the deployment environment and rerun make up-prod." >&2
      ;;
    monitoring)
      echo "Override the monitoring secrets in .env.local or the deployment environment and rerun make up-monitoring." >&2
      ;;
  esac
  exit 1
fi
```

И если значение пустое или осталось placeholder'ом:

```text
Refusing production deploy: POSTGRES_PASSWORD still uses a committed placeholder/default.
```

удобно даже при одном стенде, а если их 3? у меня была работа где было 8 стендов, и управление енвами превращалось в кромешный ад

## Генерация секретов должна быть командой

но с такой валидацией возникает желание заменить пароль на проде просто на admin123, потому что я лентяй

поэтому пользуюсь своим скриптом, который содержит в себе список паролей\секретов и требования к ним (по длине\формату)

я могу запустить

```bash
make gen-secrets
```

и получить:

```dotenv
POSTGRES_PASSWORD=K7xQeE5A0nZcJQEr3wF0AmYlUjZ8duQp
APP_SECRET=7Uj7ExlTnYzoy6N9mW2D2E5qZ0e2qLxXMP4n9x1uXH1JgS2U1l3iA0oYtQeP4b8R
GRAFANA_ADMIN_PASSWORD=x8TlnsYoZ2DUkqv11Xd7I4eKcRMLUj47
```

результат каждый раз рандомный

В простом варианте достаточно bash-скрипта, который читает /dev/urandom и генерит alnum/token-url-safe строки нужной длины.
Главное, чтобы формат подходил потребителям: без символов, которые ломают dotenv, shell, URL или DSN.

мой скрипт выглядит так

```bash
#!/bin/sh
set -eu

secret_length=${SECRET_LENGTH:-32}
app_secret_length=${APP_SECRET_LENGTH:-64}

generate_secret() {
  length=$1
  LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c "${length}"
  printf '\n'
}

if [ "$#" -eq 0 ]; then
  echo "Usage: SECRET_LENGTH=32 APP_SECRET_LENGTH=64 $0 VAR_NAME [VAR_NAME ...]" >&2
  exit 1
fi

for var_name in "$@"; do
  case "${var_name}" in
    APP_SECRET)
      value=$(generate_secret "${app_secret_length}")
      ;;
    *)
      value=$(generate_secret "${secret_length}")
      ;;
  esac

  printf '%s=%s\n' "${var_name}" "${value}"
done
```

## Чем валидировать env

Я бы делил проверки на несколько уровней.

1. Синтаксис dotenv-файлов:

    ```bash
    dotenv-linter check .env app/.env
    ```

   Он ловит дубли ключей, кривой delimiter, пустые значения, проблемы с форматированием.

2. Итоговый Compose:

    ```bash
    docker compose --env-file .env --env-file .env.local config
    docker compose config --environment
    ```

   Это показывает, что Compose реально увидел после интерполяции.

3. Runtime schema приложения.

   В Symfony - env processors (`int:`, `bool:`, `resolve:`) плюс явные application-level checks там, где переменная критична.

4. Production guard.

   Отдельный скрипт, который знает запрещенные значения:

    ```text
    empty
    change-me
    change-me-in-.env.local
    admin
    password
    auth_service
    dev-identity-exchange-secret
    ```

5. Secret scanning.

   Gitleaks в pre-commit и CI:

    ```bash
    gitleaks dir . --verbose
    ```

Gitleaks еще можно использовать, он будет ругаться, если найдет закоммиченные секреты

а как вы организовываете работу с env?
