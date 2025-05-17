# Как сделать Modulith в Symfony

> **Modulith** — архитектурный стиль, при котором приложение остаётся монолитом, но код внутри разбит на модули (подпапки) по доменам. 


## Содержание

1. [Введение](#введение)
2. [Конфигурация модулей](#конфигурация-модулей)
3. [DI](#di)
4. [Routing](#routing)
5. [Doctrine](#doctrine)
6. [Утилиты и функции](#утилиты-и-функции)
7. [Database](#database)
8. [Заключение](#заключение)

## Введение

Классическая структура проектов выглядит так:

```shell
├── src
   ├── Command
   ├── Controller
   │   ├── Product
   │   └── User
   ├── Doctrine
   ├── Entity
   │   ├── Product.php
   │   └── User.php
   ├── Message
   ├── MessageHandler
   └── Kernel.php
```

Структура modulith в Symfony выглядела б так:

```shell
├── src
   ├── Product
   │   ├── Command
   │   ├── Controller
   │   ├── Doctrine
   │   ├── Entity
   │   ├── Message
   │   └── MessageHandler
   ├── User
   │    ├── Controller
   │    └── Entity
   └── Kernel.php
```

Разница в том, что в modulith каждый модуль (например Product, User) содержит все компоненты в своей папке, а не по всему проекту.

Если нужна доработка условной корзины, вы сразу знаете где находится весь код отвечающий за корзину, меньше конфликтов при слиянии

Вдобавок исчезают портянки файлов, когда открываете Entity, а там 30 файлов в столбик

Часто самая большая сложность возникает у людей при конфигурации модулей. 
Ничто нам не мешает запихать всю конфигурацию в один общий файл, например `config/services.yaml`, 
но из-за этого файл быстро станет раздуваться, что снизит его поддерживаемость и в нем будет единая точка связности модулей

Поэтому конфигурацию модулей лучше выносить в сами модули

## Конфигурация модулей

Чтобы собрать все маленькие конфиг файлы из модулей, надо сконфигурировать ядро Symfony сделать это:

`src/Kernel.php`

```php
<?php

declare(strict_types=1);

namespace App;

use Doctrine\DBAL\Types\Type;
use Symfony\Bundle\FrameworkBundle\Kernel\MicroKernelTrait;
use Symfony\Component\Config\Loader\LoaderInterface;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\Loader\Configurator\ContainerConfigurator;
use Symfony\Component\HttpKernel\Kernel as BaseKernel;
use Symfony\Component\Routing\Loader\Configurator\RoutingConfigurator;

class Kernel extends BaseKernel
{
    use MicroKernelTrait {
        configureContainer as baseConfigureContainer;
        configureRoutes as baseConfigureRoutes;
    }

    protected function configureContainer(ContainerConfigurator $container, LoaderInterface $loader, ContainerBuilder $builder): void
    {
        $this->baseConfigureContainer(container: $container, loader: $loader, builder: $builder);
        $configDir = $this->getConfigDir();

        $srcDir = $this->getProjectDir() . '/src';
        $container->import(resource: $srcDir . '/**/{di}.php');
        $container->import(resource: $srcDir . "/**/{di}_{$this->environment}.php");
    }

    private function configureRoutes(RoutingConfigurator $routes): void
    {
        $this->baseConfigureRoutes(routes: $routes);

        $srcDir = $this->getProjectDir() . '/src';

        $routes->import(resource: $srcDir . '/**/{routing}.php');
        $routes->import(resource: $srcDir . "/**/{routing}_{$this->environment}.php");
    }
}

```

## DI

Как видно, здесь мы подключаем файлы `di.php` в зависимости от окружения. Эти файлы отвечают за регистрацию сервисов в Symfony и за какие-либо частные настройки модуля

Поэтому важно сказать в основном конфиг-файле не мешать нам с кастомной загрузкой:

`config/services.yaml`

```yaml
services:
    _defaults:
        autowire: true
        autoconfigure: true

    App\:
        resource: '../src/'
        exclude:
            - '../src/Kernel.php'
            - '../src/*/{di,di_test,di_dev,routing,doctrine,functions}.php'
```

Пример конфигурации DI в модуле:

`src/YourModule/di.php`

```php
<?php

declare(strict_types=1);

use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\Loader\Configurator\ContainerConfigurator;

use function Symfony\Component\DependencyInjection\Loader\Configurator\param;

return static function (ContainerConfigurator $container, ContainerBuilder $containerBuilder): void {
    $services = $container->services();
    $services
        ->defaults()
        ->autowire()
        ->autoconfigure();

    $container->import(resource: __DIR__ . '/Resources/config/notifications.yaml');

    $services->alias(id: ArtifactUploadContextBuilderInterface::class, referencedId: ArtifactUploadContextBuilder::class);

    $services
        ->set(id: ArtifactNotificationsConfig::class)
        ->factory(factory: [null, 'create'])
        ->arg(key: '$parameters', value: param('artifact_notifications'));
};
```

Файлы с суффиксом окружения будут загружены в зависимости от ENV переменной среды окружения. Например для тестов я хочу выключить кеширование, или привязать стаб вместо основной реализации:

`src/YourModule/di_test.php`

```php
<?php

declare(strict_types=1);

use Symfony\Component\DependencyInjection\Loader\Configurator\ContainerConfigurator;

return static function (ContainerConfigurator $container): void {
    $services = $container->services();
    $services
        ->defaults()
        ->autowire()
        ->autoconfigure();

    $services->set(id: PackageProxyService::class)->arg(key: '$ttl', value: 0);
};

```

## Routing

Метод `configureRoutes` из `Kernel.php` ответственен за нахождение конфиг файлов регистрации роутов

Тогда основной конфиг файл будет выглядеть довольно минималистично

`config/routes.yaml`

```yaml
redirect:
  path: /
  controller: Symfony\Bundle\FrameworkBundle\Controller\RedirectController
  defaults:
    path: /api/docs
```

Пример регистрации роутов:

`src/YourModule/routing.php`

```php
<?php

declare(strict_types=1);

use Symfony\Component\Routing\Loader\Configurator\RoutingConfigurator;

return static function (RoutingConfigurator $routes): void {
    $routes
        ->import(resource: './Controller/', type: 'attribute')
        ->prefix(prefix: '/api');
};

```

Этот файл практически всегда выглядит одинаково и просто копипастится

## Doctrine

Для регистрации сущностей доктрины нужен отдельный конфиг:

`src/YourModule/doctrine.php`

```php
<?php

declare(strict_types=1);

use Symfony\Config\DoctrineConfig;

return static function (DoctrineConfig $doctrine): void {
    $emDefault = $doctrine->orm()->entityManager('default');

    $emDefault->autoMapping(true);
    $emDefault->mapping('Artifact')
        ->type('attribute')
        ->dir(__DIR__ . '/Entity')
        ->isBundle(false)
        ->prefix('App\Artifact\Entity')
        ->alias('App');
};
```

Для этого мы должны пояснить Symfony как найти и зарегистрирвать эти файлы:

`config/packages/doctrine_module_mapping.php`

```php
<?php

declare(strict_types=1);

use Symfony\Component\Finder\Finder;
use Symfony\Config\DoctrineConfig;

return static function (DoctrineConfig $doctrine): void {
    $finder = new Finder();
    $finder->files()->name(patterns: 'doctrine.php')->in(dirs: __DIR__ . '/../../src/**');

    $load = static fn(SplFileInfo $file) => include $file;

    foreach ($finder as $file) {
        $configurator = $load($file);

        if (is_callable(value: $configurator)) {
            $configurator($doctrine);
        }
    }
};

```

## Утилиты и функции

Я недолюбливаю Util классы с кучей статических методов, поэтому всякие микрофункции которые особо не отнести к какому-то классу, или вам не хочется создавать и инжектить всюду класс содержащий один метод, стоит выделять просто в неймспейс своего модуля:

`src/YourModule/functions.php`

```php
<?php

declare(strict_types=1);

namespace App\YourModule;

use InvalidArgumentException;

use function array_slice;

function getVendorPackageName(string $vendor, string $package): string
{
    return $vendor . '/' . $package;
}
```

Только надо сказать композеру как найти эти функции:

`composer.json`

```json
{
  "autoload": {
    "psr-4": {
      "App\\": "src/"
    },
    "files": [
      "src/YourModule/functions.php"
    ]
  }
}
```

Не забудь запустить `composer dump`, и сбросить кеш psalm/phpstan. После добавления новых конфиг-файлов стоит запустить `bin/console cache:clear` чтобы симфа нашла их и обновилась

## Database

Так же как код бьется на модули (namespace'ы), так же имеет смысл бить базу данных на схемы. Это очень легко сделать:

```php
#[ORM\Table(name: 'notification_settings', schema: 'notification')]
class NotificationSettings
```

Тогда открывая БД, не будет пугающего списка на 800 таблиц вперемешку

Да, какие-то схемы будут содержать одну таблицу, какие-то 5, но мне лично куда проще ориентироваться в бд имея эти группы в виде схем. 
Плюс гипотетически это будет легче распиливаться на сервисы, если понадобиться, 
и можно управлять доступами на схему, опять же, если понадобиться.

## Заключение

Понравилась статья? Подписывайся на мой [тгк](https://t.me/+rPaGqfiAC-QwNTI6)

Подход modulith позволяет сохранить монолитную природу приложения, не жертвуя поддерживаемостью. 

Модули изолируют бизнес-логику, упрощают тестирование и дают ощущение порядка в коде. 
Такой подход может помочь проект к возможному переходу на микросервисы в будущем, если он вообще потребуется.
