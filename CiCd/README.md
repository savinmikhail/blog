# Практическое руководство по настройке CI/CD для PHP проектов

![img_1.png](img_1.png)

## Содержание
1. [Почему CI/CD полезен и для бизнеса и для разработки](#почему-cicd-полезен-и-для-бизнеса-и-для-разработки)
2. [Этапы пайплайна](#этапы-пайплайна)
    - [Build](#build)
    - [Test](#test)
    - [Deploy](#deploy)
    - [DAST](#dast)
3. [Полный пример](#полный-пример)

## Почему CI/CD полезен и для бизнеса и для разработки

[Доклад о том, зачем использовать пайплайны?](https://youtu.be/jFSSV1pdZTw?si=RY7jP0HmlCeI_mM9x) 

CI/CD расшифровывается как Continuous Integration / Continuous Delivery. 
Под первой частью подразумевается постоянная интеграция нового кода в основную ветку (чему способствуют проверки качества кода перед вливанием). 
Под вторым подразмевается частый деплой новых версий деплоя (деплоим не раз в месяц, а 3 раза в неделю например), 
чему способствуют проверки качества кода (не боимся что недотестили) + автоматическое развертывания приложения (всем видно доехало или нет,
снижаем человеческий фактор, меньше рутинной работы)

Цена багов и уязвимостей найденных на проде несомненно выше таковых найденых еще до того, как код был смержен в master, 
поэтому имеет и коммерческий смысл делать shift left в отношении проверки кода на качество и безопасность

Часто проверки кода располагают в pre-commit hooks, это менее надежно - разработчик скорее всего рано или поздно отключит их, 
плюс это замедляют работу в feature ветке, когда ты хочешь сначала накидать решение которое работает, 
а потом уже отрефакторить его, чтоб оно было более поддерживаемое

Интеграция различных инструментов контроля качества кода прокачивает ваши харды, потому что дает фидбек, что вы плохо написали и как это исправить

Чем больше проверок в пайплайне, тем меньше смысла в проведении code-review, потому что если пайплайн зеленый, то уже малая вероятность неправильных типов / кодстайла / архитектуры. 
Конечно могут оставаться неоптимальные решения, неправильно понятая бизнес логика

Чем больше проверок в пайплайне, тем меньше Fear driven development - если ваши изменения прошли сквозь пайплайн, 
то вряд ли вы написали что-то, что сразу упадет. А если и написали, то виноват пайплайн, который это не нашел. 
Стоит задуматься, как можно изменить пайплайн, чтобы он в следующий раз не пропустил такой код

Чем больше проверок в пайплайне, тем медленнее вносятся изменения в код, поэтому не рекомендую затаскивать все возможные инструменты сразу. 
Многие инструменты имеют функционал baseline, другие инструменты имеют настраиваемую сложность или фильтры найденных уязвимостейч, то облегчает их интеграцию.

## Этапы пайплайна

Часть расписанных здесь джоб актуальна только для symfony (например di, schema validate)

Мы будем рассматривать GitLab CI/CD, потому что по моему опыту самый распространенный инструмент в коммерческой разработке

Джобы в test stage запускаются параллельно, поэтому нет смысла располагать их из расчета fail fast

![img_2.png](img_2.png)

Я расположу их в порядке легкости и важности внедрения в проект (на мой субъективный взгляд)

Есть [готовые шаблоны](https://gitlab.com/gitlab-org/gitlab/-/blob/master/lib/gitlab/ci/templates/Security/DAST-API.gitlab-ci.yml) для DAST jobs приспособлены для Ultimate подписки, поэтому переписаны

Этапы (stages) пайплайна:

        ┌─────────┐     ┌───────────┐     ┌──────────┐     ┌─────────┐
        │  Build  │ →   │   Test    │ →   │  Deploy  │ →   │  DAST   │
        └─────────┘     └───────────┘     └──────────┘     └─────────┘

Каждый эта содержит набор задач (jobs), каждая задача может запускать несколько команд

GitLab Runner [автоматически](https://docs.gitlab.com/ci/runners/configure_runners/#git-strategy) клонирует ваш репозиторий в контейнер с джобой прежде чем выполнять указанный script

Приведу здесь используемые мной конфиги для ряда job, чтобы было проще вам взять и использовать пайплайн. Конечно стоит изучить самостоятельно особенности каждого инструмента

Приведу здесь примеры violations, которые репортуют инструменты, чтобы у вас сложилось представление, какой инструмент какую пользу может принести

Создадим файл `.gitlab-ci.yaml`

Опишем stages пайплайна

```yaml
stages:
  - build
  - test
  - deploy
  - DAST
```

### Build
Нам нужен образ приложения, в котором будем выполнять проверки качества кода. Но как правило такой образ вы не хотите деплоить, так как установлены dev зависимости, возможно включен xdebug и т.д.
Поэтому мы будем собирать 2 образа
Чтобы собрать образ, нам нужен докер, в то же время сама джоба сборки образа будет запускаться в докере, поэтому нам нужен dind (Docker-in-Docker), который запускает docker daemon в себе, и мы сможем использовать docker команды.
Чтобы не заморачиваться с установкой в этот контейнер композера, я вынес билд приложения в отдельную джобу:

```yaml
build_dev_dependencies:
   stage: build
   image: composer:latest
   script:
      - composer install --no-interaction
   artifacts:
      paths:
         - vendor/
         - . # приложение автоматически клонируется в job, добавим в артефакт чтоб не клонировать дважды и не было проблем с workdir
```

Сборка образа 

```yaml
build_dev_image:
   services:
      - name: docker:dind
        alias: dind
   image: docker:20.10.16
   stage: build
   variables:
      GIT_STRATEGY: none # отключаем клонирование приложения в контейнер
   before_script:
      - docker login -u gitlab-ci-token -p $CI_JOB_TOKEN $CI_REGISTRY
   script:
      - docker build -t $DEV_IMAGE ./.docker/dev
      - docker push $DEV_IMAGE # пушим image в registry гитлаба
   needs: [build_dev_dependencies] # будет ждать пока build_dev_dependencies job не будет выполнена
```

По большей части то же самое сделаем для prod сборки

```yaml
build_prod_dependencies:
   stage: build
   image: composer:latest
   variables:
      APP_ENV: prod
      APP_DEBUG: 0
   script:
      - composer install --no-dev --optimize-autoloader --no-interaction
      - composer dump-env prod
   artifacts:
      paths:
         - vendor/
         - .
   only:
      - tags
```
Здесь мы не устанавливаем dev зависимости, и ускоряем работу autoloader: https://getcomposer.org/doc/articles/autoloader-optimization.md#optimization-level-1-class-map-generation
И оптимизируем чтение .env* файлов: https://symfony.com/doc/current/deployment.html#b-configure-your-environment-variables
Так же мы не хотим на каждый чих собирать prod сборку, поэтому конфигурируем запуск только когда был выпущен релиз (а значит и тег):
```yaml
   only:
      - tags
```

Сборка образа:
```yaml
build_prod_image:
   services:
      - name: docker:dind
        alias: dind
   image: docker:20.10.16
   stage: build
   variables:
      GIT_STRATEGY: none
   before_script:
      - docker login -u gitlab-ci-token -p $CI_JOB_TOKEN $CI_REGISTRY
   script:
      - docker build -t $PROD_IMAGE ./.docker/prod
      - docker push $PROD_IMAGE
      - docker push $CI_REGISTRY_IMAGE:latest
   needs: [build_prod_dependencies]
   only:
      - tags
```

Обратите внимание, что собирается с другого dockerfile:

```yaml
   - docker build -t $PROD_IMAGE ./.docker/prod
```

Теперь эти образы мы можем переиспользовать в дальнейших джобах, стягивая их с registry.

### Test

#### PHP-CS-Fixer

https://github.com/PHP-CS-Fixer/PHP-CS-Fixer

Это линтер. Замечательно то, что он правит все найденные несоответствия конфигу автоматически, поэтому самый легкий для внедрения, в то же время очень важный, так как больше никогда вам не придется думать об оформлении кода

```yaml
cs:
   stage: test
   image: $DEV_IMAGE
   variables:
      GIT_STRATEGY: none
   script:
      - ./vendor/bin/php-cs-fixer -v --config=.php-cs-fixer.dist.php fix --dry-run --stop-on-violation --diff
```

используем флаг `--dry-run`, чтобы в пайплайне у нас ничего не правилось, но просто находились ошибки. 
`--stop-on-violation` нужен для оптимизации - после первой же найденной ошибки мы можем упасть, и не искать остальные

пример конфига

<details>

<summary><strong>php-cs-fixer.php</strong></summary>

```php
<?php

declare(strict_types=1);

use PhpCsFixer\Config;
use PhpCsFixer\Finder;
use PHPyh\CodingStandard\PhpCsFixerCodingStandard;

$finder = (new Finder())
    ->in(__DIR__)
    ->exclude('var')
    ->append([
        __FILE__,
        __DIR__ . '/bin/console',
    ]);

$config = (new Config())
    ->setCacheFile(__DIR__ . '/var/.php-cs-fixer.cache')
    ->setFinder($finder);

(new PhpCsFixerCodingStandard())->applyTo($config);

return $config;

```

</details>

![img_4.png](img_4.png)

#### PHPUnit

```yaml
phpunit:
  stage: test
  image: $DEV_IMAGE
  services: # нам нужен контейнер с базой данных для тестов
    - name: postgres:14
      alias: postgres
  variables:
    APP_ENV: test
    DATABASE_URL: "pgsql://postgres:postgres@postgres:5432/test_db"
    POSTGRES_DB: test_db
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
    GIT_STRATEGY: none
  before_script:
     - apt-get update && apt-get install -y postgresql-client
     - until pg_isready -h postgres -p 5432 -U postgres; do sleep 1; done # ждем пока база внутри контейнера будет готова
     - bin/console doctrine:database:create --if-not-exists
     - bin/console doctrine:migrations:migrate --no-interaction
  script:
    - XDEBUG_MODE=coverage php ./vendor/bin/phpunit --colors=never --coverage-text --coverage-cobertura=coverage.cobertura.xml --log-junit phpunit-report.xml --do-not-cache-result
  coverage: '/^\s*Lines:\s*\d+.\d+\%/'
  artifacts:
    when: always
    reports:
      junit: phpunit-report.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.cobertura.xml
```

флаг `--colors=never` нужен чтобы проще доставать регуляркой покрытие
`--coverage-text` выводит результат выполнения в консоль
`--do-not-cache-result` оптимизация
`--log-junit phpunit-report.xml` - опционально, выводит репорт в UI гитлаба:

![img.png](img.png)


пример конфига

<details>

<summary><strong>phpunit.xml.dist</strong></summary>

```xml
<?xml version="1.0" encoding="UTF-8"?>
<phpunit xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:noNamespaceSchemaLocation="vendor/phpunit/phpunit/phpunit.xsd"
         bootstrap="tests/bootstrap.php"
         cacheDirectory="var/phpunit"
         requireCoverageMetadata="true"
         beStrictAboutOutputDuringTests="true"
         failOnRisky="true"
         failOnWarning="true"
>
    <php>
        <ini name="display_errors" value="1"/>
        <ini name="error_reporting" value="-1"/>
        <server name="APP_ENV" value="test" force="true"/>
    </php>

    <testsuites>
        <testsuite name="default">
            <directory>tests</directory>
        </testsuite>
    </testsuites>

    <source restrictDeprecations="true" restrictNotices="true" restrictWarnings="true">
        <include>
            <directory>src</directory>
        </include>
    </source>
</phpunit>
```
</details>

#### Composer

```yaml
composer:
   variables:
      GIT_STRATEGY: none
   stage: test
   image: $DEV_IMAGE
   script:
      - composer normalize --diff --dry-run
      - composer validate # 
      - vendor/bin/composer-require-checker check --config-file=composer-require-checker.json # 
      - php8.2 vendor/bin/composer-unused # 
      - composer audit # 
      -  # 
```

[composer normalize](https://github.com/ergebnis/composer-normalize)  форматирует `composer.json` в стандартный вид - например, сортирует поля в порядке востребованности - редко используемые поля (например `repositories`) ставятся ниже чем часто используемые (например `requires`)

[composer validate](https://getcomposer.org/doc/03-cli.md#validate) - валидирует `composer.json` против [схемы](https://getcomposer.org/schema.json), и проверяет синхронизацию с `composer.lock`

[composer-require-checker](https://github.com/maglnet/ComposerRequireChecker) - проверяет что вы не используете в коде транзитивные зависимости, чтобы вы могли явно добавить их в `require`, дабы в один момент они не выпали из сборки

[vendor/bin/composer-unused](https://github.com/composer-unused/composer-unused) - проверяет, что у вас не стоит пакетов, которые вы нигде не используете

[composer audit](https://getcomposer.org/doc/03-cli.md#audit) - проверяет наличие уязвимостей в установленных библиотеках (на удивление часто падает - раз в каждые месяца 2)

[composer check-platform-reqs](https://getcomposer.org/doc/03-cli.md#check-platform-reqs) - проверяет, что на сервере установлены все необходимые для работы приложения расширения

Пример конфига для `composer-unused`

<details>

<summary><strong>composer-unused.php</strong></summary>

```php
<?php

declare(strict_types=1);

use ComposerUnused\ComposerUnused\Configuration\Configuration;
use ComposerUnused\ComposerUnused\Configuration\NamedFilter;

return static fn(Configuration $config): Configuration => $config
    ->addNamedFilter(NamedFilter::fromString('baldinof/roadrunner-bundle'))
    ->addNamedFilter(NamedFilter::fromString('doctrine/doctrine-migrations-bundle'))
    ->addNamedFilter(NamedFilter::fromString('phpstan/phpdoc-parser'))
    ->addNamedFilter(NamedFilter::fromString('revolt/event-loop-adapter-react'))
    ->addNamedFilter(NamedFilter::fromString('symfony/dotenv'))
    ->addNamedFilter(NamedFilter::fromString('symfony/flex'))
    ->addNamedFilter(NamedFilter::fromString('symfony/monolog-bundle'))
    ->addNamedFilter(NamedFilter::fromString('symfony/runtime'))
    ->addNamedFilter(NamedFilter::fromString('symfony/security-bundle'));
```

</details>

#### Psalm

<details>

<summary><strong>psalm.xml.dist</strong></summary>

```xml
<?xml version="1.0"?>
<psalm
    cacheDirectory="var/psalm"
    checkForThrowsDocblock="true"
    checkForThrowsInGlobalScope="true"
    disableSuppressAll="true"
    ensureArrayStringOffsetsExist="true"
    errorLevel="1"
    findUnusedCode="false"
    findUnusedBaselineEntry="true"
    findUnusedPsalmSuppress="true"
    findUnusedVariablesAndParams="true"
    memoizeMethodCallResults="true"
    reportMixedIssues="true"
    sealAllMethods="true"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns="https://getpsalm.org/schema/config"
    xsi:schemaLocation="https://getpsalm.org/schema/config vendor/vimeo/psalm/config.xsd"
>
    <projectFiles>
        <directory name="config"/>
        <directory name="public"/>
        <directory name="src"/>
        <directory name="telephantast"/>
        <directory name="tests"/>
        <file name="bin/console"/>
        <ignoreFiles>
            <directory name="var"/>
            <directory name="vendor"/>
        </ignoreFiles>
    </projectFiles>

    <forbiddenFunctions>
        <function name="dd"/>
        <function name="die"/>
        <function name="dump"/>
        <function name="echo"/>
        <function name="empty"/>
        <function name="eval"/>
        <function name="exit"/>
        <function name="print"/>
        <function name="print_r"/>
        <function name="var_export"/>
    </forbiddenFunctions>

    <issueHandlers>
        <MissingThrowsDocblock>
            <errorLevel type="suppress">
                <directory name="tests"/>
            </errorLevel>
        </MissingThrowsDocblock>
        <MixedAssignment errorLevel="suppress"/>
    </issueHandlers>

    <ignoreExceptions>
        <classAndDescendants name="LogicException"/>
        <classAndDescendants name="RuntimeException"/>
        <classAndDescendants name="ReflectionException"/>
        <classAndDescendants name="JsonException"/>
        <classAndDescendants name="Doctrine\DBAL\Exception"/>
        <classAndDescendants name="Psr\Container\ContainerExceptionInterface"/>
    </ignoreExceptions>

    <stubs>
        <file name="stubs/Bunny/AbstractClient.phpstub"/>
        <file name="stubs/Bunny/Async/Client.phpstub"/>
        <file name="stubs/Bunny/Channel.phpstub"/>
        <file name="stubs/Psr/Container/ContainerInterface.phpstub"/>
        <file name="stubs/React/Promise/PromiseInterface.phpstub"/>
    </stubs>
</psalm>
```
</details>

#### Rector

https://github.com/rectorphp/rector

<details>

<summary><strong>rector.php</strong></summary>

```php
<?php

declare(strict_types=1);

use Rector\Config\RectorConfig;
use Rector\Php80\Rector\Class_\StringableForToStringRector;
use Rector\Php83\Rector\ClassMethod\AddOverrideAttributeToOverriddenMethodsRector;

return RectorConfig::configure()
    ->withPaths([
        __DIR__ . '/bin/console',
        __DIR__ . '/config',
        __DIR__ . '/public',
        __DIR__ . '/src',
        __DIR__ . '/tests',
    ])
    ->withParallel()
    ->withCache(__DIR__ . '/var/rector')
    ->withPhpSets(php82: true)
    ->withSkip([
        StringableForToStringRector::class,
        AddOverrideAttributeToOverriddenMethodsRector::class,
    ]);

```
</details>

#### Deptrack
Создаем много конфигурационных файлов под каждый вид проверок: например для директорий в приложении, для модулей в src, для package-by-feature в модулях и тп, не стоит все пихать в один файл

<details>

<summary><strong>deptrac.directories.yaml</strong></summary>

```yaml

deptrac:
    analyser:
        types:
            - class
            - class_superglobal
            - file
            - function
            - function_call
            - function_superglobal
            - use

    paths:
        - bin
        - config
        - migrations
        - public
        - src
        - tests

    layers:
        - { name: bin,        collectors: [ { type: directory, value: ./bin/.* } ] }
        - { name: migrations, collectors: [ { type: directory, value: ./migrations/.* } ] }
        - { name: public,     collectors: [ { type: directory, value: ./public/.* } ] }
        - { name: src,        collectors: [ { type: directory, value: ./src/.* } ] }
        - { name: tests,      collectors: [ { type: directory, value: ./tests/.* } ] }

    ruleset:
        bin: [src]
        migrations:
        public: [src]
        tests: [src]
```
</details>

#### KICS

</details>

<details>

<summary><strong>Пример violation</strong></summary>

```json
{
    "id": "f1a0bb482c0f478d4b6592a51da84de5f42cb34b4e185a46baad7c622ffa96f4",
    "category": "sast",
    "name": "Missing User Instruction",
    "description": "A user should be specified in the dockerfile, otherwise the image will run as root",
    "cve": "kics_id:fd54f200-402c-4333-a5a4-36ef6709af2f:2:0",
    "severity": "Critical",
    "scanner": {
        "id": "kics",
        "name": "kics"
    },
    "location": {
        "file": "Docker/Dockerfile",
        "start_line": 2
    },
    "identifiers": [
        {
            "type": "kics_id",
            "name": "Missing User Instruction",
            "value": "fd54f200-402c-4333-a5a4-36ef6709af2f",
            "url": "https://docs.docker.com/engine/reference/builder/#user"
        }
    ]
}
```

</details>

### Check coverage

для работы джобы надо создать access token с правами `read_api`
перейти в репозиторий -> settings -> ci/cd -> variables, добавить переменную с ключом CHECK_COVERAGE_TOKEN, значением в виде токена. Стоит сделать ее masked,  чтоб не было видно в логах и убрать флаг protected variable, чтоб оно работало со всех веток

https://gitlab.com/api/v4/projects/67384433/pipelines/1689770968/jobs
code coverage сохраняется как один из параметров джобы, и мы можем его достать
```json
{
   "id": 9251826755,
   "status": "success",
   "stage": "test",
   "name": "phpunit",
   "ref": "develop",
   "tag": false,
   "coverage": 0.73,
   "allow_failure": false,
   "created_at": "2025-02-26T15:06:42.001Z",
   "started_at": "2025-02-26T15:13:05.482Z",
   "finished_at": "2025-02-26T15:15:02.498Z",
   "erased_at": null,
   "duration": 117.015687,
   "queued_duration": 2.547127,
   "user": {
     "id": 22031530,
     "username": "savinmikhail",
     "name": "Mikhail",
     "state": "active",
     "locked": false,
     "avatar_url": "https://secure.gravatar.com/avatar/b875f06f4a5b59fb1c051d348aee7c06c32fa04277ac9dfef77a1f01a72ebc87?s=80&d=identicon",
     "web_url": "https://gitlab.com/savinmikhail",
     "created_at": "2024-07-11T14:59:57.200Z",
     "bio": "",
     "location": "",
     "public_email": null,
     "skype": "",
     "linkedin": "",
     "twitter": "",
     "discord": "",
     "website_url": "",
     "organization": "",
     "job_title": "",
     "pronouns": null,
     "bot": false,
     "work_information": null,
     "followers": 0,
     "following": 0,
     "local_time": null
   },
   "commit": {
     "id": "7fc44cab4baefb4745d2d4e0b9641059d99570bd",
     "short_id": "7fc44cab",
     "created_at": "2025-02-26T22:06:35.000+07:00",
     "parent_ids": [
       "58f54851649537ae88f1e89e798deb90b3397689"
     ],
     "title": "update .gitlab-ci.yml",
     "message": "update .gitlab-ci.yml\n",
     "author_name": "Mikhail",
     "author_email": "salazar290720035017@gmail.com",
     "authored_date": "2025-02-26T22:06:35.000+07:00",
     "committer_name": "Mikhail",
     "committer_email": "salazar290720035017@gmail.com",
     "committed_date": "2025-02-26T22:06:35.000+07:00",
     "trailers": {

     },
     "extended_trailers": {

     },
     "web_url": "https://gitlab.com/savinmikhail1/online-shop/-/commit/7fc44cab4baefb4745d2d4e0b9641059d99570bd"
   },
   "pipeline": {
     "id": 1689770968,
     "iid": 40,
     "project_id": 67384433,
     "sha": "7fc44cab4baefb4745d2d4e0b9641059d99570bd",
     "ref": "develop",
     "status": "running",
     "source": "push",
     "created_at": "2025-02-26T15:06:41.879Z",
     "updated_at": "2025-02-26T15:06:43.058Z",
     "web_url": "https://gitlab.com/savinmikhail1/online-shop/-/pipelines/1689770968"
   },
   "web_url": "https://gitlab.com/savinmikhail1/online-shop/-/jobs/9251826755",
   "project": {
     "ci_job_token_scope_enabled": false
   },
   "artifacts": [
     {
       "file_type": "cobertura",
       "size": 2623,
       "filename": "cobertura-coverage.xml.gz",
       "file_format": "gzip"
     }
   ],
   "runner": {
     "id": 12270845,
     "description": "1-green.saas-linux-small-amd64.runners-manager.gitlab.com/default",
     "ip_address": null,
     "active": true,
     "paused": false,
     "is_shared": true,
     "runner_type": "instance_type",
     "name": "gitlab-runner",
     "online": true,
     "status": "online"
   },
   "runner_manager": {
     "id": 57464191,
     "system_id": "s_deaa2ca09de7",
     "version": "17.7.0~pre.103.g896916a8",
     "revision": "896916a8",
     "platform": "linux",
     "architecture": "amd64",
     "created_at": "2024-12-20T16:35:28.539Z",
     "contacted_at": "2025-02-26T15:15:07.123Z",
     "ip_address": "10.1.5.248",
     "status": "online"
   },
   "artifacts_expire_at": "2025-03-28T15:13:53.503Z",
   "archived": false,
   "tag_list": []
 }
```

пример аутпута 
![img_3.png](img_3.png)

#### Nuclei

<details>

<summary><strong>nuclei</strong></summary>

```json
{
  "info": {
    "name": "PHPinfo Page - Detect",
    "author": [
      "pdteam",
      "daffainfo",
      "meme-lord",
      "dhiyaneshdk",
      "wabafet",
      "mastercho"
    ],
    "tags": [
      "config",
      "exposure",
      "phpinfo"
    ],
    "description": "PHPinfo page was detected. The output of the phpinfo() command can reveal sensitive and detailed PHP environment information.\n",
    "severity": "low",
    "metadata": {
      "max-request": 25
    },
    "classification": {
      "cve-id": null,
      "cwe-id": [
        "cwe-200"
      ]
    },
    "remediation": "Remove PHP Info pages from publicly accessible sites, or restrict access to authorized users only."
  }
}
```

</details>

#### Trivy

<details>

<summary><strong>Trivy</strong></summary>

```json
{
    "id": "024fd5bd42b3cfed92af89216a3c074c97c20b35",
    "severity": "High",
    "location": {
        "dependency": {
            "package": {
                "name": "libxml2"
            },
            "version": "2.9.14+dfsg-1.3~deb12u1"
        },
        "operating_system": "debian 12.9",
        "image": "registry.gitlab.com/tsyren-dashidymbrylov/online-shop:master"
    },
    "identifiers": [
        {
            "type": "cve",
            "name": "CVE-2024-25062",
            "value": "CVE-2024-25062",
            "url": "https://access.redhat.com/errata/RHSA-2024:2679"
        }
    ],
    "links": [
        {
            "url": "https://access.redhat.com/errata/RHSA-2024:2679"
        },
        {
            "url": "https://access.redhat.com/security/cve/CVE-2024-25062"
        },
        {
            "url": "https://bugzilla.redhat.com/2262726"
        },
        {
            "url": "https://bugzilla.redhat.com/show_bug.cgi?id=2262726"
        },
        {
            "url": "https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-25062"
        },
        {
            "url": "https://errata.almalinux.org/9/ALSA-2024-2679.html"
        },
        {
            "url": "https://errata.rockylinux.org/RLSA-2024:3626"
        },
        {
            "url": "https://gitlab.gnome.org/GNOME/libxml2/-/issues/604"
        },
        {
            "url": "https://gitlab.gnome.org/GNOME/libxml2/-/tags"
        },
        {
            "url": "https://linux.oracle.com/cve/CVE-2024-25062.html"
        },
        {
            "url": "https://linux.oracle.com/errata/ELSA-2024-3626.html"
        },
        {
            "url": "https://nvd.nist.gov/vuln/detail/CVE-2024-25062"
        },
        {
            "url": "https://ubuntu.com/security/notices/USN-6658-1"
        },
        {
            "url": "https://ubuntu.com/security/notices/USN-6658-2"
        },
        {
            "url": "https://www.cve.org/CVERecord?id=CVE-2024-25062"
        }
    ],
    "details": {
        "vulnerable_package": {
            "name": "Vulnerable Package",
            "type": "text",
            "value": "libxml2:2.9.14+dfsg-1.3~deb12u1"
        },
        "vendor_status": {
            "name": "Vendor Status",
            "type": "text",
            "value": "affected"
        }
    },
    "description": "An issue was discovered in libxml2 before 2.11.7 and 2.12.x before 2.12.5. When using the XML Reader interface with DTD validation and XInclude expansion enabled, processing crafted XML documents can lead to an xmlValidatePopElement use-after-free.",
    "solution": "No solution provided"
}
```
</details>

#### Gitleaks

<details>

<summary><strong>Gitleaks</strong></summary>

```json
{
    "id": "f24458cd78b17036e70038cb3386ac1b6d1d985160a5101d528197a2c114ce4a",
    "category": "secret_detection",
    "name": "Password in URL",
    "description": "Password in URL\n\nFor general guidance on handling security incidents with regards to leaked keys, please see the GitLab documentation on\n[Credential exposure to the internet](https://docs.gitlab.com/ee/security/responding_to_security_incidents.html#credential-exposure-to-public-internet).",
    "cve": ".env:a013fea9cebb7f3c805ca0c7d1ec17bac4bbe3c18079eb0b45f96a0ce11f18b6:Password in URL",
    "severity": "Critical",
    "confidence": "Unknown",
    "raw_source_code_extract": "amqp://guest:guest@localhost:5672/%2f/messages",
    "scanner": {
        "id": "gitleaks",
        "name": "Gitleaks"
    },
    "location": {
        "file": ".env",
        "commit": {
            "author": "Tsyren Dashidymbrylov",
            "date": "2025-02-16T04:27:25Z",
            "message": "Update .gitlab-ci.yml file",
            "sha": "6e36ee79de5fe9405e5cbac0dedbcff530d72363"
        },
        "start_line": 34
    },
    "identifiers": [
        {
            "type": "gitleaks_rule_id",
            "name": "Gitleaks rule ID Password in URL",
            "value": "Password in URL"
        }
    ]
}
```
</details>

### Deploy

### DAST

## Полный пример

<details>

<summary><strong>.gitlab-ci.yml</strong></summary>

```yaml
stages:
  - build
  - test
  - deploy
  - DAST

variables:
  CONTAINER_TEST_IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG
  DOCKER_IMAGE: $CONTAINER_TEST_IMAGE

cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - vendor/

build:
  stage: build
  image: composer:latest
  script:
    - composer install --prefer-dist --no-interaction
  artifacts:
    paths:
      - vendor/

build_image:
  services:
    - name: docker:dind
      alias: dind
  image: docker:20.10.16
  stage: build
  script:
    - docker login -u gitlab-ci-token -p $CI_JOB_TOKEN $CI_REGISTRY
    - docker pull $CI_REGISTRY_IMAGE:latest || true
    - docker build --tag $CONTAINER_TEST_IMAGE --tag $CI_REGISTRY_IMAGE:latest ./Docker
    - docker push $CONTAINER_TEST_IMAGE
    - docker push $CI_REGISTRY_IMAGE:latest
  needs: [build]
  rules:
    - changes:
        - Docker/**/*

cs:
  stage: test
  image: php:8.2
  script:
    - ./vendor/bin/php-cs-fixer fix src --dry-run --stop-on-violation # https://github.com/PHP-CS-Fixer/PHP-CS-Fixer

phpunit:
  stage: test
  image: $DOCKER_IMAGE
  services:
    - name: postgres:14
      alias: postgres
  variables:
    APP_ENV: test
    DATABASE_URL: "pgsql://postgres:postgres@postgres:5432/test_db"
    POSTGRES_DB: test_db
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
  script:
    - apt-get update && apt-get install -y postgresql-client
    - until pg_isready -h postgres -p 5432 -U postgres; do sleep 1; done
    - bin/console doctrine:database:create --if-not-exists --env=test
    - bin/console doctrine:migrations:migrate --no-interaction --env=test
    - XDEBUG_MODE=coverage php ./vendor/bin/phpunit --coverage-text --coverage-cobertura=coverage.cobertura.xml --coverage-clover=coverage.xml
  coverage: '/^\s*Lines:\s*\d+.\d+\%/'
  artifacts:
    when: always
    paths:
      - coverage.cobertura.xml
      - coverage.xml

check_coverage:
  image: alpine:latest
  stage: test
  needs: [phpunit]
  variables:
    JOB_NAME: phpunit
    TARGET_BRANCH: master
  before_script:
    - apk add --update --no-cache curl jq
  rules:
    - if: '$CI_COMMIT_BRANCH != $TARGET_BRANCH'  # Only run on MRs, not on the main branch
  script:
    # Get the latest successful pipeline ID from the target branch
    - TARGET_PIPELINE_ID=$(curl -s "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/pipelines?ref=${TARGET_BRANCH}&status=success&private_token=${PRIVATE_TOKEN}" | jq ".[0].id")

    # Fetch the coverage percentage from the target branch's last successful pipeline
    - TARGET_COVERAGE=$(curl -s "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/pipelines/${TARGET_PIPELINE_ID}/jobs?private_token=${PRIVATE_TOKEN}" | jq --arg JOB_NAME "$JOB_NAME" '.[] | select(.name==$JOB_NAME) | .coverage' | tr -d '"')

    # Fetch the current coverage from this pipeline
    - CURRENT_COVERAGE=$(curl -s "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/pipelines/${CI_PIPELINE_ID}/jobs?private_token=${PRIVATE_TOKEN}" | jq --arg JOB_NAME "$JOB_NAME" '.[] | select(.name==$JOB_NAME) | .coverage' | tr -d '"')

    # Validate if coverage values are available
    - |
      if [ -z "$TARGET_COVERAGE" ]; then 
        echo "No previous coverage data found. Skipping check."; 
        exit 0;
      fi

    - |
      if [ -z "$CURRENT_COVERAGE" ]; then 
        echo "Failed to retrieve current coverage data."; 
        exit 1;
      fi

    # Convert to numeric and compare
    - |
      TARGET_COVERAGE=$(echo "$TARGET_COVERAGE" | awk '{print int($1)}')
      CURRENT_COVERAGE=$(echo "$CURRENT_COVERAGE" | awk '{print int($1)}')

      if [ "$CURRENT_COVERAGE" -lt "$TARGET_COVERAGE" ]; then 
        echo "Coverage decreased from ${TARGET_COVERAGE}% to ${CURRENT_COVERAGE}%! Merge request blocked.";
        exit 1;
      else 
        echo "Coverage check passed: ${CURRENT_COVERAGE}% (previous: ${TARGET_COVERAGE}%)";
      fi

phpmd:
  stage: test
  image: php:8.2
  script:
    - vendor/bin/phpmd src json phpmd.xml --reportfile phpmd_result.json
  artifacts:
    when: always
    paths:
      - phpmd_result.json

migrations_rollback_test:
  stage: test
  image: $DOCKER_IMAGE
  services:
    - name: postgres:14
      alias: postgres
  variables:
    APP_ENV: test
    DATABASE_URL: "pgsql://postgres:postgres@postgres:5432/test_db"
    POSTGRES_DB: test_db
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
  script:
    - apt-get update && apt-get install -y postgresql-client
    - until pg_isready -h postgres -p 5432 -U postgres; do sleep 1; done
    - bin/console doctrine:database:create --if-not-exists --env=test
    - bin/console doctrine:migrations:migrate --no-interaction --env=test
    - bin/console doctrine:migrations:migrate first --no-interaction --env=test
    - bin/console doctrine:migrations:migrate --no-interaction --env=test

composer:
  stage: test
  image: composer:latest
  script:
    - composer normalize --diff --dry-run # https://github.com/ergebnis/composer-normalize
    - composer validate # https://getcomposer.org/doc/03-cli.md#validate
    - vendor/bin/composer-require-checker check --config-file=composer-require-checker.json # https://github.com/maglnet/ComposerRequireChecker
    - php8.2 vendor/bin/composer-unused # https://github.com/composer-unused/composer-unused
    - composer audit # https://getcomposer.org/doc/03-cli.md#audit

di: # чтобы проверить, что контейнер компилируется корректно в прод режиме
  stage: test
  image: php:8.2
  script:
    - bin/console cache:clear --env=prod
    - bin/console lint:container --env=prod

schema-validate: # проверить корректность маппингов доктрины, без соединения с бд
  stage: test
  image: php:8.2
  script:
    - bin/console doctrine:schema:validate --skip-sync

rector:
  stage: test
  image: php:8.2
  script:
    - vendor/rector/rector/bin/rector --dry-run

deptrac: # валидация архитектурных правил
  stage: test
  image: php:8.2
  script:
    - vendor/bin/deptrac --config-file=deptrac.modules.yaml --cache-file=var/.deptrac.modules.cache
    - vendor/bin/deptrac --config-file=deptrac.directories.yaml --cache-file=var/.deptrac.directories.cache

psalm: # проверка типов (и не только)
  stage: test
  image: php:8.2
  script:
    - vendor/bin/psalm

trivy_container_scan:
  image:
    name: docker.io/aquasec/trivy:latest
    entrypoint: [""]
  variables:
    # No need to clone the repo, we exclusively work on artifacts. See
    # https://docs.gitlab.com/ee/ci/runners/configure_runners.html#git-strategy
    GIT_STRATEGY: none
    TRIVY_USERNAME: "$CI_REGISTRY_USER"
    TRIVY_PASSWORD: "$CI_REGISTRY_PASSWORD"
    TRIVY_AUTH_URL: "$CI_REGISTRY"
    TRIVY_NO_PROGRESS: "true"
    TRIVY_CACHE_DIR: ".trivycache/"
    FULL_IMAGE_NAME: $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG
  script:
    - trivy --version
    # update vulnerabilities db
    - time trivy image --download-db-only
    # Builds report and puts it in the default workdir $CI_PROJECT_DIR, so `artifacts:` can take it from there
    - time trivy image --exit-code 0 --format template --template "@/contrib/gitlab.tpl"
      --output "$CI_PROJECT_DIR/gl-container-scanning-report.json" "$FULL_IMAGE_NAME"
    # Prints full report
    - time trivy image --exit-code 0 "$FULL_IMAGE_NAME"
    # Fail on critical vulnerabilities
    - time trivy image --exit-code 1 --severity CRITICAL "$FULL_IMAGE_NAME"
  cache:
    paths:
      - .trivycache/
  # Enables https://docs.gitlab.com/ee/user/application_security/container_scanning/ (Container Scanning report is available on GitLab EE Ultimate or GitLab.com Gold)
  artifacts:
    when: always
    name: gl-container-scanning-report.json
    paths:
      - gl-container-scanning-report.json
    reports:
      container_scanning: gl-container-scanning-report.json
  stage: test

kics-ioc-scan:
  stage: test
  image:
    name: checkmarx/kics:latest
    entrypoint: [""]
  script:
    - kics scan --no-progress -p ${PWD} -o ${PWD} --report-formats json --output-name kics-results
  artifacts:
    when: always
    name: kics-results.json
    paths:
      - kics-results.json

gitleaks_secret_detection:
  stage: test
  image:
    name: zricethezav/gitleaks:latest
    entrypoint: [""]
  script:
    - gitleaks dir . --report-path gitleaks-report.json
  artifacts:
    when: always
    paths:
      - gitleaks-report.json

deploy: # автоматическая доставка изменений на сервер (dev/stage/prod - для каждой будет своя джоба)
  stage: deploy
  when: manual
  only:
    - master   # или main/develop/release.x.x.x
  script:
    - echo "Deploying the application..."
    #    здесь будет кастомная логика. в самом простом виде
    #     - ssh $HOST:$USER \
    #     && cd $PATH_TO_PROJECT \
    #     && git clone $LINK \
    #     && bin/console bin/console clear:cache \
    #     && bin/console doctrine:migration:migrate
    #  в более продвинутом варианте подменяем контейнер на сервере сбилженным image'м
    - echo "Application successfully deployed."

dast_nuclei:
  stage: DAST
  image: golang:latest
  variables:
    TARGET_URL: https://your-app/
  before_script:
    - go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
  script:
    - echo "Target url" $TARGET_URL
    - curl -I $TARGET_URL || echo "Target is unreachable"
    - nuclei -u $TARGET_URL -jsonl nuclei-report.jsonl || true
  artifacts:
    when: always
    paths:
      - nuclei-report.jsonl

```
</details>

## USEFUL LINKS:
- GitLab template examples: https://docs.gitlab.com/ci/examples/#cicd-templates
- GitLab template usage documentation: https://docs.gitlab.com/ci/yaml/includes/#include-a-single-configuration-file
- GitLab application security documentation: https://docs.gitlab.com/user/application_security/
- GitLab DevSecOps tutorial: https://gitlab-da.gitlab.io/tutorials/security-and-governance/devsecops/simply-vulnerable-notes/
- GitLab security scanner integration documentation: https://docs.gitlab.com/user/application_security/#security-scanning-without-auto-devops
- GitLab security and governance solutions: https://about.gitlab.com/solutions/security-compliance/
- GitLab DevSecOps demo application: https://gitlab.com/gitlab-da/tutorials/security-and-governance/devsecops/simply-vulnerable-notes
- PHP template https://gitlab.com/gitlab-org/gitlab/-/blob/master/lib/gitlab/ci/templates/PHP.gitlab-ci.yml
- Restrict test coverage decrease: https://rpadovani.com/gitlab-code-coverage#the-gitlab-pipeline-job

https://dev.to/muhamadhhassan/adding-phpunit-test-log-and-coverage-to-gitlab-cicd-33b5
https://docs.gitlab.com/ci/testing/unit_test_reports/
объяснить отсутсвие инструментов infection, yaml lint. добавить чек обновлений для композера раз в 2 недели. добавить comments-density to avoid tech debt