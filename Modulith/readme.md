
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

        $container->import(resource: $configDir . '/app_version.php');
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

В вашем `composer.json` добавьте

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

Не забудь запустить `composer dump`, и сбросить кеш psalm/phpstan. После добавления новых конфиг файлов стоит запустить `bin/console cache:clear`

Так же как код бьется на модули (namespace'ы), так же имеет смысл бить базу данных на схемы через аттрибут

```php
#[ORM\Table(name: 'notification_settings', schema: 'notification')]
class NotificationSettings
```

Тогда открывая БД, не будет пугающего списка на 800 таблиц вперемешку
