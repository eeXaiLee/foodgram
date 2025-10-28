import { Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

const Technologies = () => {
  return (
    <Main>
      <MetaTags>
        <title>Технологии — Foodgram</title>
        <meta name="description" content="Стек технологий проекта Foodgram: Python, Django, DRF, React, Docker и инструменты качества." />
        <meta property="og:title" content="Технологии — Foodgram" />
        <meta property="og:description" content="Backend, Frontend, Инфраструктура и инструменты качества." />
      </MetaTags>

      <Container>
        <h1 className={styles.title}>Технологии</h1>

        <div className={styles.content}>
          <div>
            <h2 className={styles.subtitle}>Backend</h2>
            <ul className={styles.text}>
              <li className={styles.textItem}>Python 3.12</li>
              <li className={styles.textItem}>Django 5.1</li>
              <li className={styles.textItem}>Django REST Framework</li>
              <li className={styles.textItem}>Djoser (аутентификация)</li>
              <li className={styles.textItem}>PostgreSQL</li>
            </ul>

            <h2 className={styles.subtitle}>Frontend</h2>
            <ul className={styles.text}>
              <li className={styles.textItem}>React</li>
              <li className={styles.textItem}>react-router</li>
              <li className={styles.textItem}>CSS-модули</li>
              <li className={styles.textItem}>react-meta-tags</li>
            </ul>

            <h2 className={styles.subtitle}>Инфраструктура и деплой</h2>
            <ul className={styles.text}>
              <li className={styles.textItem}>Docker, Docker Compose</li>
              <li className={styles.textItem}>Nginx, Gunicorn (продакшен веб-сервер и WSGI)</li>
              <li className={styles.textItem}>.env конфигурация</li>
            </ul>

            <h2 className={styles.subtitle}>Качество и тестирование</h2>
            <ul className={styles.text}>
              <li className={styles.textItem}>flake8 (код-стайл)</li>
              <li className={styles.textItem}>pytest (юнит/интеграционные тесты backend)</li>
              <li className={styles.textItem}>
                OpenAPI/Redoc: <a href="/docs/redoc.html" className={styles.textLink}>/docs/redoc.html</a>
              </li>
            </ul>

            <h2 className={styles.subtitle}>Архитектура на уровне сервиса</h2>
            <div className={styles.text}>
              <p className={styles.textItem}>
                Monorepo: фронтенд (React) + backend (Django/DRF). API — REST.
                Медиа и статика раздаются через Nginx; backend работает за Gunicorn.
                Деплой и локальный старт контейнеризованы Docker Compose.
              </p>
            </div>
          </div>
        </div>
      </Container>
    </Main>
  )
}

export default Technologies
