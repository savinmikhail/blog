Why use pipeline? https://youtu.be/jFSSV1pdZTw?si=RY7jP0HmlCeI_mM9x

Мы будем рассматривать gitnlab ci/cd, потому что по моему опыту самый распространенный инструмент в коммерческой разработке

USEFUL LINKS:
- GitLab template examples: https://docs.gitlab.com/ci/examples/#cicd-templates
- GitLab template usage documentation: https://docs.gitlab.com/ci/yaml/includes/#include-a-single-configuration-file
- GitLab application security documentation: https://docs.gitlab.com/user/application_security/
- GitLab DevSecOps tutorial: https://gitlab-da.gitlab.io/tutorials/security-and-governance/devsecops/simply-vulnerable-notes/
- GitLab security scanner integration documentation: https://docs.gitlab.com/user/application_security/#security-scanning-without-auto-devops
- GitLab security and governance solutions: https://about.gitlab.com/solutions/security-compliance/
- GitLab DevSecOps demo application: https://gitlab.com/gitlab-da/tutorials/security-and-governance/devsecops/simply-vulnerable-notes
- PHP template https://gitlab.com/gitlab-org/gitlab/-/blob/master/lib/gitlab/ci/templates/PHP.gitlab-ci.yml
- Restrict test coverage decrease: https://rpadovani.com/gitlab-code-coverage#the-gitlab-pipeline-job

Trivy itself https://trivy.dev/latest/docs/target/container_image/

Джобы quality stage запускаются параллельно, поэтому нет смысла располагать их из расчета fail fast

Я расположу их в порядке легкости и важности внедрения в проект

Часть джоб актуальна только для symfony (di, schema validate)

```yaml
stages:
  - build
  - test
  - deploy
  - dast

include:
  - template: Jobs/Container-Scanning.gitlab-ci.yml # https://gitlab.com/gitlab-org/gitlab/-/blob/master/lib/gitlab/ci/templates/Jobs/Container-Scanning.gitlab-ci.yml
  - template: Jobs/Dependency-Scanning.gitlab-ci.yml # https://gitlab.com/gitlab-org/gitlab/-/blob/master/lib/gitlab/ci/templates/Jobs/Dependency-Scanning.gitlab-ci.yml
  - template: Jobs/SAST.gitlab-ci.yml # https://gitlab.com/gitlab-org/gitlab/-/blob/master/lib/gitlab/ci/templates/Jobs/SAST.gitlab-ci.yml
  - template: Jobs/Secret-Detection.gitlab-ci.yml # https://gitlab.com/gitlab-org/gitlab/-/blob/master/lib/gitlab/ci/templates/Jobs/Secret-Detection.gitlab-ci.yml
  - template: Jobs/SAST-IaC.gitlab-ci.yml # https://gitlab.com/gitlab-org/gitlab/-/blob/master/lib/gitlab/ci/templates/Jobs/SAST-IaC.gitlab-ci.yml
  - template: Security/DAST.gitlab-ci.yml # https://gitlab.com/gitlab-org/gitlab/-/blob/master/lib/gitlab/ci/templates/Security/DAST.gitlab-ci.yml
  - template: Security/API-Security.gitlab-ci.yml # https://gitlab.com/gitlab-org/gitlab/-/blob/master/lib/gitlab/ci/templates/Security/API-Security.gitlab-ci.yml

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

cs:
  stage: quality
  image: php:8.2
  script:
    - ./vendor/bin/php-cs-fixer fix src --dry-run --stop-on-violation # https://github.com/PHP-CS-Fixer/PHP-CS-Fixer

phpunit:
  stage: quality
  image: php:8.2
  variables:
    APP_ENV: test
  script:
    - ./vendor/bin/phpunit # https://github.com/sebastianbergmann/phpunit

composer:
  stage: quality
  image: composer:latest
  script:
    - composer normalize --diff --dry-run # https://github.com/ergebnis/composer-normalize
    - composer validate # https://getcomposer.org/doc/03-cli.md#validate
    - vendor/bin/composer-require-checker check --config-file=composer-require-checker.json # https://github.com/maglnet/ComposerRequireChecker
    - php8.2 vendor/bin/composer-unused # https://github.com/composer-unused/composer-unused
    - composer audit # https://getcomposer.org/doc/03-cli.md#audit

di: # чтобы проверить, что контейнер компилируется корректно в прод режиме
  stage: quality
  image: php:8.2
  script:
    - bin/console cache:clear --env=prod
    - bin/console lint:container --env=prod

schema-validate: # проверить корректность маппингов доктрины, без соединения с бд
  stage: quality
  image: php:8.2
  script:
    - bin/console doctrine:schema:validate --skip-sync

rector:
  stage: quality
  image: php:8.2
  script:
    - vendor/rector/rector/bin/rector --dry-run

deptrac: # валидация архитектурных правил
  stage: quality
  image: php:8.2
  script:
    - vendor/bin/deptrac --config-file=deptrac.modules.yaml --cache-file=var/.deptrac.modules.cache
    - vendor/bin/deptrac --config-file=deptrac.directories.yaml --cache-file=var/.deptrac.directories.cache

psalm: # проверка типов (и не только)
   stage: quality
   image: php:8.2
   script:
     - vendor/vimeo/psalm/psalm

deploy: # автоматическая доставка изменений на сервер (dev/stage/prod - для каждой будет своя джоба)
  stage: deploy
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
#  в более продвинутом варианте собираем docker image с кодом, vendor'ом, пушим в registry, и подменяем контейнер на сервере
    - echo "Application successfully deployed."
```

примеры конфигов

### `rector.php`

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

### `phpunit.xml.dist`

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

### `psalm.xml.dist`

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

### `deptrac.directories.yaml`

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

### `composer-unused.php`
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

### `php-cs-fixer.php`
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

## примеры найденных ошибок

### kics

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