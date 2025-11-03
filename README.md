# Foodgram — социальный сервис публикации рецептов

Foodgram — платформa, где пользователи публикуют рецепты, добавляют их в избранное и в корзину покупок, подписываются на авторов и получают автоматический **список покупок** по выбранным рецептам. Проект реализован согласно ТЗ и схемe OpenAPI.

> **Документация API (Redoc):** `/api/docs/redoc.html`  
> **Бэкенд админ-панель:** `/admin/`

---

## Возможности
- Регистрация и аутентификация пользователей (Djoser, токены).
- Публикация рецептов с ингредиентами и тегами.
- Поиск ингредиентов по вхождению названия.
- Фильтрация рецептов по тегам, избранному и корзине.
- Подписки на авторов; лента рецептов подписок.
- Добавление/удаление рецептов в избранное и корзину.
- Выгрузка PDF со списком покупок по корзине.
- Документация API по OpenAPI/Redoc.
- Полная работа через Docker Compose (PostgreSQL, backend, frontend, nginx).
  
---

## Технологии
- **Backend:** Python 3.12, Django 5.1, DRF 3.15, Djoser, Pillow, django-filter
- **DB:** PostgreSQL 13 (локально можно SQLite)
- **Infra:** Docker, Docker Compose, Nginx, Gunicorn
- **Auth:** TokenAuthentication (DRF authtoken, Djoser)
- **CI/CD:** GitHub Actions → Docker Hub → сервер (Compose)
- **Прочее:** python-dotenv, drf-extra-fields

---

## Архитектура контейнеров
- `db` — PostgreSQL 13
- `backend` — Django + Gunicorn (`0.0.0.0:8888`)
- `frontend` — одноразовый контейнер сборки CRA; копирует build в том `static_volume`
- `nginx` — отдаёт SPA и статику, проксирует `/api` и `/admin` на backend, отдаёт `/api/docs/`

**Тома:**
- `pg_data` — данные Postgres
- `static_volume` — собранный фронтенд + статика админки/DRF
- `media_volume` — медиафайлы Django

---

## Переменные окружения (`.env`)
Пример `.env` (используется и локально, и в проде):
```
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432

SECRET_KEY=your-django-secret
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,backend,foodgram-evg.duckdns.org
```

---

## Локальный запуск (Docker)
1. Установите Docker Desktop/Engine.
2. Создайте `.env` в корне репозитория (см. пример выше).
3. Запустите оркестрацию:
   ```bash
   cd infra
   docker compose up -d --build
   ```
4. Проверьте:
   - Фронтенд SPA: `http://localhost/`
   - Документация API: `http://localhost/api/docs/redoc.html`
   - Админка: `http://localhost/admin/`

Статические файлы:
- Фронтенд билд копируется контейнером `frontend` в `static_volume` (смонтирован в Nginx по `/static`).
- Статика админки/DRF собирается энтрипоинтом бэкенда в том же томе.

Если нужно заново собрать статику и фронт-билд:
```bash
docker compose up -d --force-recreate frontend
docker compose restart nginx
```

---

## Управление зависимостями (pip-tools)
В каталоге `backend/`:
```bash
# базовые
pip-compile -o requirements/requirements.txt requirements/requirements.in

# прод
pip-compile -o requirements/requirements.prod.txt requirements/requirements.prod.in

# тесты
pip-compile -o requirements/requirements.test.txt requirements/requirements.test.in
```

---

## Тесты
### Локально
По умолчанию в `settings.py` база — **SQLite**. Просто:
```bash
cd backend
pip install -r requirements/requirements.test.txt
pytest -q
```

### В CI
GitHub Actions поднимает сервис PostgreSQL и разворачивает зависимости тестов + prod (для клиента БД), затем запускает pytest.

---

## Продакшен-деплой (Docker Compose)
На сервере (Linux), структура в каталоге `~/foodgram`:
```
~/foodgram
├── .env
├── docker-compose.production.yml
├── nginx.conf
└── docs/
    ├── openapi-schema.yml
    └── redoc.html
```
Запуск/обновление:
```bash
docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml up -d
docker image prune -f
```

**Внешний Nginx (за пределами Compose)** проксирует домен `foodgram-evg.duckdns.org` на `127.0.0.1:8888`. Пример server-блока:
```nginx
server {
    listen 80;
    server_name foodgram-evg.duckdns.org;

    client_max_body_size 20M;

    location / {
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://127.0.0.1:8888;
    }
}
```
### HTTPS
Установите certbot и выпустите сертификат:
```bash
sudo apt-get update && sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d foodgram-evg.duckdns.org
```

---

## CI/CD (GitHub Actions → Docker Hub → сервер)
Пайплайн:
1. **Линт бекенда (flake8)**
2. **Тесты бекенда** (PostgreSQL как сервис)
3. **Сборка и пуш образов**:  
   `eexailee/foodgram_backend:latest` и `eexailee/foodgram_frontend:latest`
4. **Деплой на сервер**: копирование `docker-compose.production.yml`, `nginx.conf`, `docs/*` и `docker compose pull / up`.

Секреты в репозитории GitHub:
- `DOCKER_USERNAME`, `DOCKER_PASSWORD`
- `HOST`, `USER`, `SSH_KEY`, `SSH_PASSPHRASE`
- (опционально) `TELEGRAM_TOKEN`, `TELEGRAM_TO`

---

## Полезные команды
```bash
# Логи
docker compose logs -f backend
docker compose logs -f nginx

# Создание суперпользователя
docker compose exec backend python manage.py createsuperuser

# Загрузка ингредиентов (management command)
docker compose exec backend python manage.py load_ingredients
```

---

## Demo admin account (для проверки админ-панели)

URL: `/admin/`  
**Логин:** `admin@example.com`  
**Пароль:** `admin_pass`

---

## Ссылки проекта
- Автор: **[Евгений Димитриев](https://github.com/eeXaiLee)**
- Репозиторий: **https://github.com/eeXaiLee/foodgram**
- API (Redoc): `/api/docs/redoc.html`
- Админ-панель: `/admin/`
