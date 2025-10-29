# Shop Bot

Демонстрационный бот, реализующий покупку вещей в интернете.

## Установка

1. Склонируйте репозиторий себе на компьютер:

```
git clone git@github.com:async1o/aiogram_with_middleware.git
```

2. Перейдите в директорию проекта:

```
cd aiogram_with_middleware.git
```

3. Создайте файл .env и заполните необходимые поля:

```
TOKEN=
DB_NAME=
DB_HOST=
DB_PORT=
DB_USER=
DB_PASS=
ADMIN_IDS=[]
```

4. Запустите бота:

```
docker compose up --build
```
## Использование

User:
```
**/start** - Начинает новый диалог
/catalog - Открывает каталог товаров
/cart - Открывает корзину товаров
```
Admin:
```
/admin - Отрывает админ-панель
/users_count - Выводит кол-во пользователей в бд
/broadcast <текст> - Осуществляет рассылку по всем 
```
