<?php

declare(strict_types=1);
require __DIR__.'/vendor/autoload.php';

$directory = sys_get_temp_dir().'/dotenv-probe-'.bin2hex(random_bytes(8));
mkdir($directory, 0700);
try {
    file_put_contents($directory.'/.env', <<<'ENV'
APP_ENV=dev
ENV_GUIDE_HOST=base
ENV_GUIDE_URL="https://${ENV_GUIDE_HOST}/path"
ENV
    );
    file_put_contents($directory.'/.env.local', "ENV_GUIDE_HOST=local\n");
    (new Symfony\Component\Dotenv\Dotenv())->loadEnv($directory.'/.env');
    $result = [
        'host' => $_ENV['ENV_GUIDE_HOST'],
        'url' => $_ENV['ENV_GUIDE_URL'],
        'version' => Composer\InstalledVersions::getPrettyVersion('symfony/dotenv'),
    ];
    if ($result['host'] !== 'local' || $result['url'] !== 'https://local/path') {
        throw new RuntimeException('Unexpected synthetic interpolation result');
    }
    echo json_encode($result, JSON_PRETTY_PRINT | JSON_THROW_ON_ERROR).PHP_EOL;
} finally {
    unlink($directory.'/.env');
    unlink($directory.'/.env.local');
    rmdir($directory);
}
