<?php

declare(strict_types=1);

require dirname(__DIR__).'/vendor/autoload.php';

use Symfony\Component\Dotenv\Dotenv;

// One bootstrap per CLI process; return typed values to the application.
$keys = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'FEATURE_NEW_CHECKOUT', 'DB_PASSWORD_FILE'];
$external = [];
foreach ($keys as $key) {
    $external[$key] = isset($_ENV[$key]) || isset($_SERVER[$key]);
}
(new Dotenv())->loadEnv(__DIR__.'/.env');
$read = static fn (string $key): ?string => $_ENV[$key] ?? $_SERVER[$key] ?? null;
$host = $read('DB_HOST');
// Deliberately limited to simple DNS names/IPv4; IPv6 and Unix sockets need their own DSN rules.
if ($host === null || !preg_match('/\A[a-zA-Z0-9][a-zA-Z0-9.-]*\z/', $host)) {
    throw new RuntimeException('DB_HOST: simple hostname required');
}
$port = filter_var($read('DB_PORT'), FILTER_VALIDATE_INT,
    ['options' => ['min_range' => 1, 'max_range' => 65535]]);
if ($port === false) {
    throw new RuntimeException('DB_PORT: integer in range 1..65535 required');
}
$name = $read('DB_NAME');
if ($name === null || !preg_match('/\A[a-zA-Z0-9_]+\z/', $name)) {
    throw new RuntimeException('DB_NAME: letters, digits and underscore required');
}
$user = $read('DB_USER');
if ($user === null || $user === '') {
    throw new RuntimeException('DB_USER: required');
}
$flag = $read('FEATURE_NEW_CHECKOUT');
if (!in_array($flag, ['true', 'false'], true)) {
    throw new RuntimeException('FEATURE_NEW_CHECKOUT: true or false required');
}
$passwordPath = $read('DB_PASSWORD_FILE');
if (!$passwordPath || !is_file($passwordPath) || !is_readable($passwordPath)) {
    throw new RuntimeException('DB_PASSWORD_FILE: readable file required');
}
$password = @file_get_contents($passwordPath);
// The lab uses a text password file with an optional trailing newline.
if ($password === false || ($password = rtrim($password, "\r\n")) === '') {
    throw new RuntimeException('DB_PASSWORD_FILE: nonempty content required');
}
$databaseUrl = sprintf('postgresql://%s:%s@%s:%d/%s',
    rawurlencode($user), rawurlencode($password), $host, $port, $name);

$report = [];
foreach ($keys as $key) {
    $report[$key] = [
        'origin' => $external[$key] ? 'process-at-bootstrap' : 'dotenv',
        'present' => $read($key) !== null && $read($key) !== '',
        'valid' => true,
    ];
}
$report['DB_HOST']['public_demo_value'] = $host;
$report['DB_PASSWORD_FILE']['content_present'] = true;
$report['DATABASE_URL'] = ['present' => true, 'origin' => 'application', 'exported' => false];

return [
    'databaseUrl' => $databaseUrl,
    'featureNewCheckout' => $flag === 'true',
    'report' => $report,
];
