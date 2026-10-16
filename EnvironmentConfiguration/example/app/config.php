<?php

declare(strict_types=1);

try {
    $config = require __DIR__.'/config-values.php';
    // Values stay in memory; print only allowlisted metadata and a synthetic public host.
    echo json_encode($config['report'], JSON_PRETTY_PRINT | JSON_THROW_ON_ERROR).PHP_EOL;
} catch (Throwable $error) {
    // Parser error messages may contain file contents. Never print them here.
    $message = $error instanceof RuntimeException && !$error instanceof \Symfony\Component\Dotenv\Exception\ExceptionInterface
        ? $error->getMessage() : 'Configuration could not be loaded';
    fwrite(STDERR, $message.PHP_EOL);
    exit(1);
}
