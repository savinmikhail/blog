
`doctrine.php`
```php
<?php

declare(strict_types=1);

use App\Incident\Doctrine\Type\IncidentChangeCollectionType;
use Symfony\Config\DoctrineConfig;

return static function (DoctrineConfig $doctrine): void {
    $doctrine
        ->dbal()
        ->type('incident_change_collection')
        ->class(IncidentChangeCollectionType::class);
};

```

```php
<?php

declare(strict_types=1);

namespace App\Incident\Doctrine\Type;

use App\Incident\ApiPlatform\Model\IncidentChange\BooleanIncidentChange;
use App\Incident\ApiPlatform\Model\IncidentChange\IntIncidentChange;
use App\Incident\ApiPlatform\Model\IncidentChange\ReminderFrequencyTypeIncidentChange;
use App\Incident\ApiPlatform\Model\IncidentChange\StatusIncidentChange;
use App\Incident\ApiPlatform\Model\IncidentChange\StringIncidentChange;
use App\Incident\Entity\Enum\IncidentStatus;
use App\Incident\Entity\Enum\ReminderFrequencyType;
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\DBAL\Platforms\AbstractPlatform;
use Doctrine\DBAL\Types\JsonType;
use Symfony\Contracts\Translation\TranslatorInterface;

use function is_array;
use function sprintf;

class IncidentChangeCollectionType extends JsonType
{
    public const TYPE_NAME = 'incident_change_collection';
    private const TRANSLATE_DOMAIN = 'incident';

    private ?TranslatorInterface $translator = null;

    public function setTranslator(TranslatorInterface $translator): void
    {
        $this->translator = $translator;
    }

    public function convertToPHPValue($value, AbstractPlatform $platform): ?Collection
    {
        if ($value === null || $value === '{}' || $value === '[]') {
            return new ArrayCollection();
        }

        $data = parent::convertToPHPValue($value, $platform);

        if (!is_array(value: $data)) {
            return new ArrayCollection();
        }

        $changes = [];
        foreach ($data as $itemData) {
            $translation = $this->translator?->trans(id: sprintf('fields.%s', $itemData['field']), domain: self::TRANSLATE_DOMAIN);

            $changes[] = match ($itemData['field']) {
                'name',
                'informationMessage',
                'startDate',
                'lastReminder',
                'updatedAt' => new StringIncidentChange(
                    fieldName: $itemData['field'],
                    oldValue: $itemData['before'],
                    newValue: $itemData['after'],
                    translation: $translation,
                ),
                'sendReminder',
                'shouldNotify' => new BooleanIncidentChange(
                    fieldName: $itemData['field'],
                    oldValue: $itemData['before'],
                    newValue: $itemData['after'],
                    translation: $translation,
                ),
                'reminderFrequencyValue' => new IntIncidentChange(
                    fieldName: $itemData['field'],
                    oldValue: $itemData['before'],
                    newValue: $itemData['after'],
                    translation: $translation,
                ),
                'reminderFrequencyType' => new ReminderFrequencyTypeIncidentChange(
                    fieldName: $itemData['field'],
                    oldValue: ReminderFrequencyType::tryFrom(value: (string) $itemData['before']),
                    newValue: ReminderFrequencyType::tryFrom(value: (string) $itemData['after']),
                    translation: $translation,
                ),
                'status' => new StatusIncidentChange(
                    fieldName: $itemData['field'],
                    oldValue: IncidentStatus::tryFrom(value: (string) $itemData['before']),
                    newValue: IncidentStatus::tryFrom(value: (string) $itemData['after']),
                    translation: $translation,
                ),
                default => null
            };
        }

        return new ArrayCollection(elements: array_values(array: array_filter(array: $changes)));
    }

    public function convertToDatabaseValue($value, AbstractPlatform $platform): ?string
    {
        if (!$value instanceof Collection || $value->isEmpty()) {
            return parent::convertToDatabaseValue([], $platform);
        }

        return parent::convertToDatabaseValue($value->toArray(), $platform);
    }

    public function getName(): string
    {
        return self::TYPE_NAME;
    }

    public function requiresSQLCommentHint(AbstractPlatform $platform): bool
    {
        return true;
    }
}

```

the middleware

```php
<?php

declare(strict_types=1);

namespace App\Incident\Doctrine\Middleware;

use App\Incident\Doctrine\Type\IncidentChangeCollectionType;
use Doctrine\DBAL\Driver;
use Doctrine\DBAL\Driver\Middleware;
use Doctrine\DBAL\Types\Type;
use Symfony\Contracts\Translation\TranslatorInterface;

final readonly class IncidentChangeCollectionTypeMiddleware implements Middleware
{
    public function __construct(
        private TranslatorInterface $translator,
    ) {}

    public function wrap(Driver $driver): Driver
    {
        /** @var IncidentChangeCollectionType $type */
        $type = Type::getType(name: IncidentChangeCollectionType::TYPE_NAME);
        $type->setTranslator(translator: $this->translator);

        return $driver;
    }
}

```

`doctrine.yaml`

```yaml
doctrine:
    orm:
        dql:
            string_functions:
                JSONB_PATH_EXISTS: App\Main\Doctrine\Functions\JsonbPathExistsFunction
```

```php
<?php

declare(strict_types=1);

namespace App\Main\Doctrine\Functions;

use Doctrine\ORM\Query\AST\ASTException;
use Doctrine\ORM\Query\AST\Functions\FunctionNode;
use Doctrine\ORM\Query\AST\Node;
use Doctrine\ORM\Query\Parser;
use Doctrine\ORM\Query\SqlWalker;
use Doctrine\ORM\Query\TokenType;

use function sprintf;

class JsonbPathExistsFunction extends FunctionNode
{
    /**
     * Выражение DQL для поля JSONB.
     */
    public ?Node $jsonbFieldExpr = null;

    /**
     * Выражение DQL для JSONPath.
     */
    public ?Node $jsonpathExpr = null;

    /**
     * Разбирает DQL для функции JSONB_PATH_EXISTS.
     */
    public function parse(Parser $parser): void
    {
        // Имя функции уже распознано парсером
        $parser->match(token: TokenType::T_IDENTIFIER); // JSONB_PATH_EXISTS
        $parser->match(token: TokenType::T_OPEN_PARENTHESIS);

        // Парсим первый аргумент: выражение для поля JSONB
        // StringPrimary покрывает случаи типа 'e.field', 'LOWER(e.field)' и т.д.
        $this->jsonbFieldExpr = $parser->StringPrimary();

        $parser->match(token: TokenType::T_COMMA); // ,

        // Парсим второй аргумент: выражение для JSONPath (ожидаем строку или параметр)
        // StringPrimary также подходит для строковых литералов и входных параметров
        $this->jsonpathExpr = $parser->StringPrimary();

        $parser->match(token: TokenType::T_CLOSE_PARENTHESIS);
    }

    /**
     * Генерирует SQL для функции jsonb_path_exists.
     */
    public function getSql(SqlWalker $sqlWalker): string
    {
        if ($this->jsonbFieldExpr === null || $this->jsonpathExpr === null) {
            // Это не должно произойти, если parse отработал корректно, но для надежности
            throw new ASTException(message: 'JSONB_PATH_EXISTS requires two arguments.');
        }

        // Получаем SQL для каждого аргумента с помощью SqlWalker
        // SqlWalker позаботится о правильном форматировании имен полей, параметров и литералов
        $jsonbFieldSql = $sqlWalker->walkStringPrimary(stringPrimary: $this->jsonbFieldExpr);
        $jsonpathSql = $sqlWalker->walkStringPrimary(stringPrimary: $this->jsonpathExpr);

        // Формируем финальный SQL вызов функции PostgreSQL
        return sprintf('jsonb_path_exists(%s, %s::jsonpath)', $jsonbFieldSql, $jsonpathSql);
        // Примечание: Начиная с PostgreSQL 12, второй аргумент jsonb_path_exists
        // должен быть типа jsonpath. Используем ::jsonpath для явного приведения типа.
        // Если вы используете только строковые литералы или параметры, которые уже строки,
        // PostgreSQL может справиться с неявным приведением, но явное надежнее.
    }
}
```

you can use it like

```php

                // Условие 2: Поле description (JSONB) должно содержать объект в массиве changedFields,
                // у которого поле 'field' равно искомому $fieldName.
                // Используем кастомную DQL функцию JSONB_PATH_EXISTS.
                // JSONPath выражение: '$.changedFields[*] ? (@.field == $fieldNameParam)'
                // Где $fieldNameParam будет параметром, содержащим значение $fieldName.
                // Получаем имя поля из значения фильтра (e.g., 'name' from 'incident.updated.name')
                $fieldName = substr(string: $filterValue, offset: strlen(string: self::UPDATE_FIELD_PREFIX));

                // Формируем JSONPath выражение, вставляя имя поля как строку в условие
                // Пример: '$[*] ? (@.field == "name")'
                $jsonPathExpr = sprintf('\'$[*] ? (@.field == "%s")\'', $fieldName);
                $dqlCondition = sprintf(
                    'JSONB_PATH_EXISTS(%s.changes, %s) = true',
                    $alias,
                    $jsonPathExpr,
                );
                $andExpr->add(arg: $dqlCondition);
```

you can register it like that

```php

class Kernel extends BaseKernel
{
    public function boot(): void
    {
        parent::boot();
        if (!Type::hasType(name: ArtifactMetadataType::class)) {
            Type::addType(name: ArtifactMetadataType::class, className: ArtifactMetadataType::class);
        }
        /** @var ArtifactMetadataType $type */
        $type = Type::getType(name: ArtifactMetadataType::class);
        $type->setArtifactMetadataFactory(artifactMetadataFactory: $this->container->get(ArtifactMetadataFactory::class));
    }
}
```


doctrine может нормализовать к енаму не только строку но и массив если подсказать

```php
class Foo
{
    /**
     * globally enabled channels.
     * @var NotificationChannel[]
     */
    #[ORM\Column(type: Types::JSON, enumType: NotificationChannel::class)]
    #[Serializer\Groups(['read', 'write'])]
    private array $notificationChannels;
}
```
