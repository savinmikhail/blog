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
  - quality
  - deploy

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
    - ./vendor/bin/php-cs-fixer fix src --dry-run --stop-on-violation

phpunit:
  stage: quality
  image: php:8.2
  variables:
    APP_ENV: test
  script:
    - ./vendor/bin/phpunit

composer:
  stage: quality
  image: composer:latest
  script:
    - composer normalize --diff --dry-run
    - composer validate
    - vendor/bin/composer-require-checker check --config-file=composer-require-checker.json
    - php8.2 vendor/bin/composer-unused
    - composer audit

di:
  stage: quality
  image: php:8.2
  script:
    - bin/console cache:clear --env=prod
    - bin/console lint:container --env=prod

schema-validate:
  stage: quality
  image: composer:latest
  script:
    - bin/console doctrine:schema:validate --skip-sync

rector:
  stage: quality
  image: composer:latest
  script:
    - vendor/rector/rector/bin/rector --dry-run

deptrac:
  stage: quality
  image: composer:latest
  script:
    - vendor/bin/deptrac --config-file=deptrac.modules.yaml --cache-file=var/.deptrac.modules.cache
    - vendor/bin/deptrac --config-file=deptrac.directories.yaml --cache-file=var/.deptrac.directories.cache

psalm:
   stage: quality
   image: composer:latest
   script:
     - vendor/vimeo/psalm/psalm

deploy:
  stage: deploy
  environment: production
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
    - echo "Application successfully deployed."
```
