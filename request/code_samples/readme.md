```php
<?php

namespace App\Request;

use Symfony\Component\Validator\Constraints as Assert;

final class CreateUserRequest
{
    #[Assert\NotBlank(message: 'Email is required')]
    #[Assert\Email]
    public string $email;

    #[Assert\NotBlank(message: 'Password cannot be empty')]
    #[Assert\Length(min: 8, minMessage: 'Password must be at least 8 characters long')]
    public string $password;
}

```

```php
<?php

namespace App\Controller;

use App\Request\CreateUserRequest;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\Routing\Annotation\Route;
use Symfony\Component\HttpKernel\Attribute\MapRequestPayload;

final class UserController extends AbstractController
{
    #[Route('/users', methods: ['POST'])]
    public function create(#[MapRequestPayload] CreateUserRequest $payload): JsonResponse
    {
        // Here you already have a validated DTO.
        // Business logic starts clean.
        return $this->json([
            'email' => $payload->email,
            'status' => 'user created',
        ]);
    }
}

```

```php
<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Component\HttpKernel\Attribute;

use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\Controller\ArgumentResolver\RequestPayloadValueResolver;
use Symfony\Component\HttpKernel\ControllerMetadata\ArgumentMetadata;
use Symfony\Component\Validator\Constraints\GroupSequence;

/**
 * Controller parameter tag to map the query string of the request to typed object and validate it.
 *
 * @author Konstantin Myakshin <molodchick@gmail.com>
 */
#[\Attribute(\Attribute::TARGET_PARAMETER)]
class MapQueryString extends ValueResolver
{
    public ArgumentMetadata $metadata;

    /**
     * @param array<string, mixed>                    $serializationContext       The serialization context to use when deserializing the query string
     * @param string|GroupSequence|array<string>|null $validationGroups           The validation groups to use when validating the query string mapping
     * @param class-string                            $resolver                   The class name of the resolver to use
     * @param int                                     $validationFailedStatusCode The HTTP code to return if the validation fails
     */
    public function __construct(
        public readonly array $serializationContext = [],
        public readonly string|GroupSequence|array|null $validationGroups = null,
        string $resolver = RequestPayloadValueResolver::class,
        public readonly int $validationFailedStatusCode = Response::HTTP_NOT_FOUND,
        public readonly ?string $key = null,
    ) {
        parent::__construct($resolver);
    }
}

```

```json
{
  "type": "https://symfony.com/errors/validation",
  "title": "Validation Failed",
  "status": 422,
  "detail": "name: Значение слишком короткое. Должно быть равно 2 символам или больше.",
  "violations": [
    {
      "propertyPath": "name",
      "title": "Значение слишком короткое. Должно быть равно 2 символам или больше."
    }
  ]
}
```

```php
<?php
namespace App\Controller;

use App\Entity\User;
use Doctrine\ORM\EntityManagerInterface;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;
use Symfony\Component\PasswordHasher\Hasher\UserPasswordHasherInterface;

class AuthController extends AbstractController
{
    private function validateLoginData(?string $email, ?string $password): ?array
    {
        if (!$email || !$password) {
            return ['error' => 'Email and password required', 'code' => Response::HTTP_BAD_REQUEST];
        }
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            return ['error' => 'Invalid email', 'code' => Response::HTTP_BAD_REQUEST];
        }
        return null;
    }

    #[Route('/login', name: 'user_login', methods: ['POST'])]
    public function login(Request $request, EntityManagerInterface $em, UserPasswordHasherInterface $passwordHasher): Response
    {
        $data = json_decode($request->getContent(), true);
        $email = $data['email'] ?? null;
        $password = $data['password'] ?? null;

        $validationError = $this->validateLoginData($email, $password);
        if ($validationError) {
            return $this->json(['error' => $validationError['error']], $validationError['code']);
        }

        $user = $em->getRepository(User::class)->findOneBy(['email' => $email]);
        if (!$user || !$passwordHasher->isPasswordValid($user, $password)) {
            return $this->json(['error' => 'Invalid credentials'], Response::HTTP_UNAUTHORIZED);
        }

        // Здесь можно добавить генерацию JWT или сессионного токена
        return $this->json(['message' => 'Login successful']);
    }
}

```

```php
<?php

final class RequestDtoResolver implements ArgumentValueResolverInterface
{
    public function resolve(Request $request, ArgumentMetadata $argument): iterable
    {
        $dtoClass = $argument->getType();
        $content = $request->getContent();

        if (empty($content) && !empty($request->request->all())) {
            $content = json_encode($request->request->all());
        }

        if (empty($content)) {
            throw new BadRequestHttpException('Empty request body');
        }

        $dto = $this->serializer->deserialize($content, $dtoClass, 'json');

        $errors = $this->validator->validate($dto);

        if (count($errors) > 0) {
            $messages = [];
            foreach ($errors as $error) {
                $messages[$error->getPropertyPath()] = $error->getMessage();
            }
            throw new BadRequestHttpException(message: json_encode($messages, JSON_UNESCAPED_UNICODE));
        }

        yield $dto;
    }
}

```

```php
// ...
use App\Entity\Author;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Validator\Validator\ValidatorInterface;

// ...
public function author(ValidatorInterface $validator): Response
{
    $author = new Author();

    // ... do something to the $author object

    $errors = $validator->validate($author);

    if (count($errors) > 0) {
        /*
         * Uses a __toString method on the $errors variable which is a
         * ConstraintViolationList object. This gives us a nice string
         * for debugging.
         */
        $errorsString = (string) $errors;

        return new Response($errorsString);
    }

    return new Response('The author is valid! Yes!');
}
```