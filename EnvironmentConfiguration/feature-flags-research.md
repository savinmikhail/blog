# Feature flags и жизненный цикл конфигурации

Проверено по первичным источникам 16 октября 2026. В статье тема включена в раздел 10; число верхних разделов остаётся 13. Сервисы feature flags и SDK в лаборатории не устанавливались.

## Различия

| Механизм | Когда меняется значение | Что важно |
|---|---|---|
| Startup env/config object | При создании процесса/объекта | Правка файла не обновляет снимок сама по себе |
| File loader с reload | При предусмотренном перечитывании | Доставка файла и reload — отдельные события |
| Dynamic DB/API store | При чтении/refresh выбранного клиента | Кеш, TTL, propagation, fallback |
| Frontend build-time flag | При новой сборке bundle | Backend runtime env не перепишет доставленный JS |

Архитектурный вывод: env подходит для bootstrap-настроек, динамический store — для оперативного переключения/targeting/rollout. Пересоздание контейнера с новым env не обязательно требует нового образа или release кода. «Хранится в БД» не гарантирует динамику, если читатель загрузил флаг один раз.

## Первичные источники

- [OpenFeature providers](https://openfeature.dev/docs/reference/concepts/provider/) — provider связывает SDK и источник вычисления; может оборачивать vendor SDK, REST API или локальные данные. OpenFeature не выбирает хранилище.
- [Evaluation API](https://openfeature.dev/specification/sections/flag-evaluation/) — default и context, error/default semantics; подробная metadata зависит от provider. API не обещает конкретный polling/TTL.
- [Unleash PHP caching](https://docs.getunleash.io/sdks/php#caching) — PSR-16 cache, обычный TTL и stale-cache при ошибке fetch. Не переносить общую схему background polling других SDK на PHP. Числовые defaults не включены в статью, потому что зависят от версии/настройки.
- [Unleash lifecycle](https://docs.getunleash.io/concepts/feature-flags#feature-flag-lifecycle) — временные флаги и их удаление; долгоживущие operational toggles требуют другой политики.

Рекомендации о владельце, правах изменения, аудите, допустимой устарелости и фиксации решения на время одной операции — инженерные выводы. Feature flag не заменяет authorization или entitlement check. Safe fallback зависит от функции, не всегда false. Значения флагов не являются каналом хранения credentials.

## Кодовые примеры из собственных проектов

В [project-cases.md](project-cases.md) зафиксированы readonly flags и startup Config objects. Их название и env bool не доказывают наличие dynamic flag storage. Чтение checkout не доказывает deployed поведение.
