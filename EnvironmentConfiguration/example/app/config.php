<?php

declare(strict_types=1);

require dirname(__DIR__).'/vendor/autoload.php';

use Symfony\Component\Dotenv\Dotenv;

try {
    // Snapshot only keys used by the example, before Dotenv populates them.
    $keys = ['DB_HOST', 'DB_PORT', 'APP_DEBUG', 'APP_TOKEN_FILE'];
    $external = [];
    foreach ($keys as $key) {
        $external[$key] = isset($_ENV[$key]) || isset($_SERVER[$key]);
    }
    (new Dotenv())->loadEnv(__DIR__.'/.env');
    $read = static fn (string $key): ?string => $_ENV[$key] ?? $_SERVER[$key] ?? null;
    $host = $read('DB_HOST');
    if ($host === null || $host === '') {
        throw new RuntimeException('DB_HOST: required');
    }
    $port = filter_var($read('DB_PORT'), FILTER_VALIDATE_INT,
        ['options' => ['min_range' => 1, 'max_range' => 65535]]);
    if ($port === false) {
        throw new RuntimeException('DB_PORT: integer in range 1..65535 required');
    }
    $debugRaw = $read('APP_DEBUG');
    if (!in_array($debugRaw, ['true', 'false'], true)) {
        throw new RuntimeException('APP_DEBUG: true or false required');
    }
    $tokenPath = $read('APP_TOKEN_FILE');
    if (!$tokenPath || !is_file($tokenPath) || !is_readable($tokenPath)) {
        throw new RuntimeException('APP_TOKEN_FILE: readable file required');
    }
    $token = @file_get_contents($tokenPath);
    if ($token === false || rtrim($token, "\r\n") === '') {
        throw new RuntimeException('APP_TOKEN_FILE: nonempty content required');
    }
    // Actual values would be passed to typed application configuration here.
    // The diagnostic output contains only this example's public host and metadata.
    $report = [];
    foreach ($keys as $key) {
        $report[$key] = [
            'origin' => $external[$key] ? 'process-at-bootstrap' : 'dotenv',
            'present' => $read($key) !== null && $read($key) !== '',
            'valid' => true,
        ];
    }
    $report['DB_HOST']['public_demo_value'] = $host;
    $report['APP_TOKEN_FILE']['content_present'] = true;
    echo json_encode($report, JSON_PRETTY_PRINT | JSON_THROW_ON_ERROR).PHP_EOL;
} catch (Throwable $error) {
    // Do not print Dotenv parser exception messages: they may include file contents.
    $message = $error instanceof RuntimeException && !$error instanceof \Symfony\Component\Dotenv\Exception\ExceptionInterface
        ? $error->getMessage() : 'Configuration could not be loaded';
    fwrite(STDERR, $message.PHP_EOL);
    exit(1);
}
