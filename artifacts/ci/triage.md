# Первичный разбор результатов безопасности

> Сводка составлена по фактическим отчётам сохранённого успешного прогона. Это первое решение, а не замена ручной проверки специалистом.

| Источник | Находка | Уровень / риск | Файл, компонент или адрес | Стратегия | Обоснование |
|---|---|---|---|---|---|
| DAST | Не задан заголовок Content-Security-Policy (CSP) | Medium (High) | https://preview.owasp-juice.shop/ | Fix | Находка среднего риска влияет на защиту браузера; нужно проверить контекст и настроить CSP. |
| DAST | Ошибочная междоменная конфигурация | Medium (Medium) | https://preview.owasp-juice.shop/assets/public/favicon_js.ico | Backlog | Базовое DAST-сканирование требует проверки контекста перед возможной блокировкой выпуска. |
| DAST | Заголовок Cross-Origin-Embedder-Policy отсутствует или задан неверно | Low (Medium) | https://preview.owasp-juice.shop/ | Monitor | Низкоприоритетный сигнал; оставить в плане усиления защиты и наблюдать. |
| DAST | Заголовок Cross-Origin-Opener-Policy отсутствует или задан неверно | Low (Medium) | https://preview.owasp-juice.shop/ | Monitor | Низкоприоритетный сигнал; оставить в плане усиления защиты и наблюдать. |
| DAST | Используются потенциально опасные функции JavaScript | Low (Low) | https://preview.owasp-juice.shop/chunk-Bvta1DJp.js | Monitor | Информационный сигнал; проверить при дальнейшем усилении защиты. |
| DAST | Используется устаревший заголовок Feature-Policy | Low (Medium) | https://preview.owasp-juice.shop/ | Monitor | Низкоприоритетная конфигурационная находка. |
| DAST | Не задан заголовок Permissions-Policy | Low (Medium) | https://preview.owasp-juice.shop/ftp/package-lock.json.bak | Monitor | Низкоприоритетная конфигурационная находка. |
| DAST | Сервер раскрывает версию через HTTP-заголовок Server | Low (High) | https://preview.owasp-juice.shop/ftp/coupons_2013.md.bak | Monitor | Утечка технической информации сама по себе не является срочной причиной блокировки. |
| DAST | Не задан заголовок Strict-Transport-Security | Low (High) | https://preview.owasp-juice.shop/assets/public/favicon_js.ico | Monitor | Находку нужно учесть при усилении настроек HTTPS. |
| DAST | Раскрывается временная метка Unix | Low (Low) | https://preview.owasp-juice.shop/assets/public/favicon_js.ico | Monitor | Информационная находка низкого приоритета. |
| DAST | Обнаружено современное веб-приложение | Informational (Medium) | https://preview.owasp-juice.shop/ | Monitor | Информационный сигнал, самостоятельного исправления не требует. |
| DAST | Нужно проверить директивы Cache-Control | Informational (Low) | https://preview.owasp-juice.shop/ftp | Monitor | Проверить при плановом усилении настроек кэширования. |
| DAST | Содержимое можно сохранять и кэшировать | Informational (Medium) | https://preview.owasp-juice.shop/robots.txt | Monitor | Проверить, соответствует ли кэширование назначению ресурса. |
| DAST | Содержимое можно сохранять, но оно не кэшируется | Informational (Medium) | https://preview.owasp-juice.shop/ | Monitor | Информационный сигнал для проверки политики кэширования. |

## Значение стратегий

- **Fix** — исправить; блокирующие проблемы должны быть устранены до прохождения контрольной точки.
- **Backlog** — запланировать исправление после проверки контекста.
- **Accept** — принять риск только через документированное, согласованное и ограниченное по сроку исключение с компенсирующими мерами.
- **Monitor** — наблюдать за изменениями и повторно оценивать риск при появлении новых данных.

Стратегия `Accept` намеренно не назначается автоматически.
