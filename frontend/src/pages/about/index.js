import { Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

const About = () => {
  return (
    <Main>
      <MetaTags>
        <title>О проекте — Foodgram</title>
        <meta name="description" content="Foodgram — сервис для публикации кулинарных рецептов с избранным и списком покупок." />
        <meta property="og:title" content="О проекте — Foodgram" />
        <meta property="og:description" content="Создавайте рецепты, добавляйте в избранное и скачивайте список покупок в один клик." />
      </MetaTags>

      <Container>
        <h1 className={styles.title}>Foodgram — «Продуктовый помощник»</h1>

        <div className={styles.content}>
          <div>
            <h2 className={styles.subtitle}>Что это?</h2>
            <div className={styles.text}>
              <p className={styles.textItem}>
                Учебный pet-project, собранный в рамках курса Яндекс Практикума. Сервис позволяет публиковать рецепты, добавлять их в избранное,
                подписываться на авторов и формировать список покупок по ингредиентам.
              </p>
              <p className={styles.textItem}>
                Регистрация простая: подтверждение e-mail не требуется — можно указать любой адрес.
              </p>
            </div>

            <h2 className={styles.subtitle}>Основные возможности</h2>
            <ul className={styles.text}>
              <li className={styles.textItem}>Публикация рецептов с ингредиентами и тегами</li>
              <li className={styles.textItem}>Избранное и подписки на авторов</li>
              <li className={styles.textItem}>Список покупок: суммирование ингредиентов и скачивание .txt</li>
              <li className={styles.textItem}>Короткая ссылка на рецепт</li>
              <li className={styles.textItem}>Поиск ингредиентов по префиксу</li>
              <li className={styles.textItem}>Открытый доступ к рецептам и тегам без авторизации</li>
            </ul>

            <h2 className={styles.subtitle}>Как начать</h2>
            <ol className={styles.text}>
              <li className={styles.textItem}>Зарегистрируйтесь или войдите в аккаунт</li>
              <li className={styles.textItem}>Создайте рецепт: добавьте ингредиенты и теги</li>
              <li className={styles.textItem}>Добавьте в избранное или в корзину — скачайте список покупок</li>
            </ol>
          </div>

          <aside>
            <h2 className={styles.additionalTitle}>Ссылки</h2>
            <div className={styles.text}>
              <p className={styles.textItem}>
                Репозиторий:{" "}
                <a href="https://github.com/eeXaiLee/foodgram" target="_blank" rel="noreferrer" className={styles.textLink}>
                  github.com/eeXaiLee/foodgram
                </a>
              </p>
              <p className={styles.textItem}>
                API (OpenAPI):{" "}
                <a href="/docs/redoc.html" className={styles.textLink}>
                  /docs/redoc.html
                </a>
              </p>
              <p className={styles.textItem}>
                Автор:{" "}
                <a href="https://github.com/eeXaiLee" target="_blank" rel="noreferrer" className={styles.textLink}>
                  eeXaiLee
                </a>
              </p>
            </div>
          </aside>
        </div>
      </Container>
    </Main>
  )
}

export default About
