# Foodgram — социальная сеть для возможности делиться своими рецептами 

[![Main Foodgram workflow](https://github.com/SadOnsGit/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/SadOnsGit/foodgram/actions/workflows/main.yml)

<img width="981" height="977" alt="image" src="https://github.com/user-attachments/assets/f7788f65-1bd3-449b-82da-15da521276c0" />



## Foodgram — это социальная сеть, где пользователи могут:
- Регистрироваться и входить (Djoser, токены)
- Просмотривать профили, менять пароля
- Загружать/удалять аватар
- Создавать, просмотривать, редактировать и удалять свои рецепты
- Искать ингредиенты по началу названия
- Фильтровать рецепты по тегам, автору, «в избранном», «в корзине»
- Добавлять/удалять рецепты в избранное
- Добавлять/удалять рецепты в список покупок и скачивать общий список (ингредиенты суммируются)
- Подписываться на авторов, отписываться и просматривать свои подписки
- Получать короткую ссылку на рецепт


## Технологический стек

- **Backend**: Django / Django REST Framework
- **База данных**: PostgreSQL
- **Веб-сервер**: Nginx
- **Деплой**: Docker
- **CI/CD**: GitHub Actions
- **Образы**: Docker Hub

## Как развернуть проект локально

1. Клонируйте репозиторий к себе:
   ```bash
   git clone https://github.com/SadOnsGit/foodgram.git
    ```

### Настройка CI/CD

1. Файл workflow находится в директории:

    ```bash
    .github/workflows/main.yml
    ```

2. Для  его адаптации перейдите в настройки своего репозитория — Settings, выберите на панели слева Secrets and Variables → Actions, нажмите New repository secret и добавьте переменные:

    ```bash
    DOCKER_USERNAME - имя пользователя в DockerHub

    DOCKER_PASSWORD - пароль пользователя в DockerHub

    HOST - ip адресс сервера

    USER - имя пользователя на сервере

    SSH_KEY - приватный ключ сервера

    SSH_PASSPHRASE - фраза от ключа ssh
    ```

## Перенесите файл .env к себе на сервер

1. Зайти в папку foodgram и перенесите кофигурации на сервер после nano ctr + s - сохранение; ctr + x закрыть файл:

    ```bash
    cd foodgram
    sudo nano .env
    ```

2. Конфигурация .env:

    ```bash
    POSTGRES_DB=foodgram
    POSTGRES_USER=foodgram_user
    POSTGRES_PASSWORD=foodgram_password
    DB_HOST=db
    DB_PORT=5432
    SECRET_KEY= Секретный ключ Django
    DB_NAME=foodgram
    ALLOWED_HOSTS= ваш ip, 127.0.0.1, localhost, ваш домен
    DEBUG=False
    ```

## Перенесите файл .env к себе на сервер
1. Обновите Actions на GitHub главной ветке происходит deploy проекта на сервер.

## Что нужно сделать

Настроить запуск проекта Foodgram в контейнерах и CI/CD с помощью GitHub Actions

## Просмотр спецификации API и фронтенд

Находясь в папке nginx, выполните команду docker-compose up. При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ —  спецификацию API.

## Автор

[Иcхаков Айдар](https://github.com/sadonsgit)

Контакты:
[sadonsgithub@yandex.ru](mailto:sadonsgithub@yandex.ru)

Телеграм:
[@exceptdev](https://t.me/exceptdev)