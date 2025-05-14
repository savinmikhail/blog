## Как сделать modulith в symfony?

Modulith — это архитектурный подход, при котором приложение остаётся монолитом на уровне деплоя, но внутри него код разделён на независимые модули с чёткими интерфейсами и ограниченными зонами ответственности.

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

Traditional Symfony architecture:
```shell
├── src
   ├── Command
   ├── Controller
   ├── Doctrine
   ├── Entity
   ├── Message
   ├── MessageHandler
   └── Kernel.php
```

The key difference is that in Modulith, each module (like Product, User) contains its own complete set of components, while in traditional Symfony architecture, all components are grouped by their type across the entire application.

```shell
├── src
   ├── Product
   │   ├── Command
   │   ├── Controller
   │   ├── Doctrine
   │   ├── Entity
   │   ├── Message
   │   └── MessageHandler
   ├── User
   │    ├── Controller
   │    └── Entity
   └── Kernel.php

```

Часто самая большая сложность возникает у людей при конфигурации модулей. Ничто нам не мешает запихать всю конфигурацию в один общий файл, например `config/services.yaml`, но из-за этого файл быстро станет раздуваться, что снизит его поддерживаемость и в нем будет единая точка связности модулей

Поэтому конфигурацию модулей лучше выносить в сами модули

Чтобы собрать все маленькие конфиг файлы из модулей, надо сконфигурировать ядро симфы сделать это:


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

Как видно здесь мы подключаем файлы `di.php` в зависимости от окружения. Эти файлы отвечают за регистрацию сервисов в симфе и за какие-то частные настройки модуля

Поэтому важно сказать в основном конфиг файле не мешать нам с кастомной загрузкой:

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

А метод `configureRoutes` ответственен за нахождение конфиг файлов регистрации роутов

Тогда основной конфиг файл будет выглядеть довольно минималистично

`config/routes.yaml`

```yaml
redirect:
  path: /
  controller: Symfony\Bundle\FrameworkBundle\Controller\RedirectController
  defaults:
    path: /api/docs
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

Для этого мы должны пояснить симфе как найти и зарегистрирвать эти файлы:

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

Так же как код бьется на модули (namespace'ы), так же имеет смысл бить базу данных на схемы. Это очень легко сделать:

```php
#[ORM\Table(name: 'notification_settings', schema: 'notification')]
class NotificationSettings
```

Тогда открывая БД, не будет пугающего списка на 800 таблиц вперемешку

Да, какие-то схемы будут содержать одну таблицу, какие-то 5, но мне лично куда проще ориентироваться в бд имея эти группы в виде схем. Плюс гипотетически это будет легче распиливаться на сервисы, если понадобиться, и можно управлять доступами на схему, опять же, если понадобиться.
