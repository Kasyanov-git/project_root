```mermaid
graph TD
  Main(Main page) -->|Авторизация не выполнена| Auth[Авторизация]
  Auth -->|Успешная авторизация| Profile[Профиль]
  Profile -->|Просмотр профиля| Credit[Количество доступных кредитов]
  Profile -->|Выбор модели и загрузка файла| ModelSelection[Выбор модели и загрузка файла]
  ModelSelection -->|Просмотр стоимости моделей| ModelCost[Стоимость моделей]
  ModelSelection --> Billing{ Проверка ЛС на баланс}
  Billing -->| Кредитов хватает | Predict[ Расчет предсказания, списывания балансов ]
  Billing -->| Кредитов НЕ хватает | ModelSelection
  Predict -->|Просмотр результатов| Result[Окно результатов]
  Profile -->|Деавторизация| Logout(Выход)
  ModelSelection --> Profile
  Result --> Profile
  Auth -->|Регистрация| Registration[Регистрация]
  Registration --> Auth
  Logout --> Auth

```