В этом видео я покажу, как буквально **одной строчкой кода** валидировать запросы в Symfony 
и сразу получать аккуратный JSON с ошибками

Большинство новичков делают всё вручную — парсят Request, пихают данные в DTO через рефлексию, 
сами дергают валидатор и собирают ответ с ошибками.

![request_example.png](images/filter_var.png)

![request_example.png](images/argument_value_resolver.png)

Большинство примеров в интернете толкают ровно туда же. Даже в официальной доке примеры с кучей ручного труда.
![request_example.png](images/doc_example_custom_response.png)

На деле же Symfony умеет делать все это автоматически.

Для начала нам нужно создать DTO под реквест и навесить атрибуты валидации на поля:
![request_example.png](images/request_example.png)

В контроллере же просто принимаем этот DTO как аргумент метода.
![ray-so-export (1).png](images/controller_with_maprequestpayload.png)

Но Symfony пока не знает, как создать этот объект — и тут мы подсказываем ему через атрибут:
это либо `MapRequestPayload` — для POST, PATCH, PUT запросов.
либо `MapQueryString` — для GET и DELETE.

И все на этом, объект уже смаплен и провалидирован.

По умолчанию при провале валидации:
 MapRequestPayload вернёт 422.
А MapQueryString вернёт 404.
Всё можно переопределить через аргумент validationFailedStatusCode.

![ray-so-export (3).png](images/mapquerystring.png)

В результате мы имеем вот такой красивый ответ, который фронт легко замапит к своим полям:

![ray-so-export (2).png](images/json_response.png)

Теперь у нас меньше кода, меньше багов и чище контроллеры.

Больше разборов — в моём телеграм-канале.

Приятного кодинга
