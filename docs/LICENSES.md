# Реестр сторонних лицензий

Сформирован автоматически (27.10.2026): backend — `pip-licenses`, frontend — `license-checker --production`. Все компоненты распространяются по открытым лицензиям (MIT, BSD, Apache-2.0, ISC, PSF, MPL-2.0, OFL для шрифта Roboto), допускающим коммерческое использование и передачу исходников.

Примечание: `@img/sharp-libvips-*` (LGPL-3.0) — нативная библиотека обработки изображений libvips, опциональная транзитивная зависимость Next.js (пакет `sharp`); используется как динамически подключаемая библиотека без изменений, что LGPL допускает без влияния на лицензию проекта. Собственный код проекта от GPL-компонентов не зависит.

## Frontend (npm, production-зависимости): сводка по лицензиям

```
├─ MIT: 25
├─ Apache-2.0: 8
├─ ISC: 2
├─ OFL-1.1: 1
├─ LGPL-3.0-or-later: 1
├─ CC-BY-4.0: 1
├─ UNLICENSED: 1
├─ BSD-3-Clause: 1
└─ 0BSD: 1

```

## Backend (Python)

| Name                    | Version    | License                              | URL                                                                                |
|-------------------------|------------|--------------------------------------|------------------------------------------------------------------------------------|
| cyclonedx-python-lib    | 11.12.0    | Apache Software License              | https://github.com/CycloneDX/cyclonedx-python-lib/#readme                          |
| pip_api                 | 0.0.35     | Apache Software License              | https://pypi.org/project/pip-api/                                                  |
| pip_audit               | 2.10.1     | Apache Software License              | https://pypi.org/project/pip-audit/                                                |
| py-serializable         | 2.1.0      | Apache Software License              | https://github.com/madpah/serializable#readme                                      |
| requests                | 2.34.2     | Apache Software License              | https://github.com/psf/requests                                                    |
| sortedcontainers        | 2.4.0      | Apache Software License              | http://www.grantjenks.com/docs/sortedcontainers/                                   |
| uvloop                  | 0.23.0     | Apache Software License; MIT License | UNKNOWN                                                                            |
| CacheControl            | 0.14.4     | Apache-2.0                           | https://pypi.org/project/CacheControl/                                             |
| asyncpg                 | 0.32.0     | Apache-2.0                           | UNKNOWN                                                                            |
| license-expression      | 30.4.4     | Apache-2.0                           | https://github.com/aboutcode-org/license-expression                                |
| msgpack                 | 1.2.4      | Apache-2.0                           | https://msgpack.org/                                                               |
| opentelemetry-api       | 1.45.1     | Apache-2.0                           | https://github.com/open-telemetry/opentelemetry-python/tree/main/opentelemetry-api |
| pytest-asyncio          | 1.4.1      | Apache-2.0                           | https://github.com/pytest-dev/pytest-asyncio                                       |
| python-multipart        | 0.0.32     | Apache-2.0                           | https://github.com/Kludex/python-multipart                                         |
| packaging               | 26.3       | Apache-2.0 OR BSD-2-Clause           | https://github.com/pypa/packaging                                                  |
| Jinja2                  | 3.1.6      | BSD License                          | https://github.com/pallets/jinja/                                                  |
| babel                   | 2.18.0     | BSD License                          | https://babel.pocoo.org/                                                           |
| httpx                   | 0.28.1     | BSD License                          | https://github.com/encode/httpx                                                    |
| itsdangerous            | 2.2.0      | BSD License                          | https://github.com/pallets/itsdangerous/                                           |
| Pygments                | 2.21.0     | BSD-2-Clause                         | https://pygments.org                                                               |
| boolean.py              | 5.0        | BSD-2-Clause                         | https://github.com/bastikr/boolean.py                                              |
| wrapt                   | 2.5.1      | BSD-2-Clause                         | https://github.com/GrahamDumpleton/wrapt                                           |
| MarkupSafe              | 3.0.4      | BSD-3-Clause                         | https://github.com/pallets/markupsafe/                                             |
| click                   | 8.5.0      | BSD-3-Clause                         | https://github.com/pallets/click/                                                  |
| httpcore                | 1.0.9      | BSD-3-Clause                         | https://www.encode.io/httpcore/                                                    |
| idna                    | 3.20       | BSD-3-Clause                         | https://github.com/kjd/idna                                                        |
| pycparser               | 3.12       | BSD-3-Clause                         | https://github.com/eliben/pycparser                                                |
| python-dotenv           | 1.2.4      | BSD-3-Clause                         | https://github.com/theskumar/python-dotenv                                         |
| starlette               | 1.10.0     | BSD-3-Clause                         | https://github.com/Kludex/starlette                                                |
| uvicorn                 | 0.54.0     | BSD-3-Clause                         | https://uvicorn.dev/                                                               |
| websockets              | 17.3       | BSD-3-Clause                         | https://github.com/python-websockets/websockets                                    |
| dnspython               | 2.9.0      | ISC                                  | https://www.dnspython.org                                                          |
| Deprecated              | 3.0.0      | MIT                                  | https://github.com/laurent-laporte-pro/deprecated                                  |
| Mako                    | 1.4.3      | MIT                                  | https://www.makotemplates.org/                                                     |
| SQLAlchemy              | 2.1.6      | MIT                                  | https://www.sqlalchemy.org                                                         |
| aiosmtplib              | 5.1.3      | MIT                                  | https://github.com/cole/aiosmtplib/blob/main/CHANGELOG.rst                         |
| alembic                 | 1.20.1     | MIT                                  | https://alembic.sqlalchemy.org                                                     |
| annotated-doc           | 0.0.5      | MIT                                  | https://github.com/fastapi/annotated-doc                                           |
| annotated-types         | 0.8.0      | MIT                                  | https://github.com/annotated-types/annotated-types                                 |
| anyio                   | 4.15.1     | MIT                                  | https://anyio.readthedocs.io/en/stable/versionhistory.html                         |
| argon2-cffi             | 25.1.0     | MIT                                  | https://github.com/hynek/argon2-cffi/blob/main/CHANGELOG.md                        |
| argon2-cffi-bindings    | 26.1.0     | MIT                                  | https://github.com/hynek/argon2-cffi-bindings/blob/main/CHANGELOG.md               |
| charset-normalizer      | 3.5.2      | MIT                                  | https://github.com/jawah/charset_normalizer/blob/master/CHANGELOG.md               |
| fastapi                 | 0.162.0    | MIT                                  | https://github.com/fastapi/fastapi                                                 |
| filelock                | 4.2.4      | MIT                                  | https://github.com/tox-dev/py-filelock                                             |
| httptools               | 0.9.0      | MIT                                  | https://github.com/MagicStack/httptools                                            |
| iniconfig               | 2.3.1      | MIT                                  | https://github.com/pytest-dev/iniconfig                                            |
| limits                  | 5.8.0      | MIT                                  | https://limits.readthedocs.org                                                     |
| pip-requirements-parser | 32.0.1     | MIT                                  | https://github.com/nexB/pip-requirements-parser                                    |
| platformdirs            | 4.13.5     | MIT                                  | https://github.com/tox-dev/platformdirs                                            |
| puremagic               | 2.2.0      | MIT                                  | https://github.com/cdgriffith/puremagic                                            |
| pydantic                | 2.14.1     | MIT                                  | https://github.com/pydantic/pydantic                                               |
| pydantic-settings       | 2.16.1     | MIT                                  | https://github.com/pydantic/pydantic-settings                                      |
| pydantic_core           | 2.50.1     | MIT                                  | https://github.com/pydantic                                                        |
| pyparsing               | 3.3.3      | MIT                                  | https://github.com/pyparsing/pyparsing/                                            |
| pytest                  | 9.1.1      | MIT                                  | https://docs.pytest.org/en/latest/                                                 |
| ruff                    | 0.17.2     | MIT                                  | https://docs.astral.sh/ruff                                                        |
| starlette-admin         | 1.0.3      | MIT                                  | https://github.com/jowilf/starlette-admin                                          |
| tomli                   | 2.5.0      | MIT                                  | https://github.com/hukkin/tomli                                                    |
| typing-inspection       | 0.4.4      | MIT                                  | https://github.com/pydantic/typing-inspection                                      |
| urllib3                 | 2.8.0      | MIT                                  | https://github.com/urllib3/urllib3/blob/main/CHANGES.rst                           |
| greenlet                | 3.5.6      | MIT AND PSF-2.0                      | https://greenlet.readthedocs.io                                                    |
| Faker                   | 40.43.0    | MIT License                          | https://github.com/joke2k/faker                                                    |
| PyYAML                  | 6.0.3      | MIT License                          | https://pyyaml.org/                                                                |
| h11                     | 0.16.0     | MIT License                          | https://github.com/python-hyper/h11                                                |
| markdown-it-py          | 4.2.0      | MIT License                          | https://github.com/executablebooks/markdown-it-py                                  |
| mdurl                   | 0.1.2      | MIT License                          | https://github.com/executablebooks/mdurl                                           |
| packageurl-python       | 0.17.6     | MIT License                          | https://github.com/package-url/packageurl-python                                   |
| pluggy                  | 1.7.0      | MIT License                          | https://github.com/pytest-dev/pluggy                                               |
| pwdlib                  | 0.3.1      | MIT License                          | https://github.com/frankie567/pwdlib                                               |
| rich                    | 15.0.0     | MIT License                          | https://github.com/Textualize/rich                                                 |
| slowapi                 | 0.1.10     | MIT License                          | https://github.com/laurents/slowapi                                                |
| tomli_w                 | 1.2.0      | MIT License                          | https://github.com/hukkin/tomli-w                                                  |
| watchfiles              | 1.3.0      | MIT License                          | https://github.com/samuelcolvin/watchfiles                                         |
| cffi                    | 2.1.1      | MIT-0                                | https://cffi.readthedocs.io/en/latest/whatsnew.html                                |
| pillow                  | 13.0.0     | MIT-CMU                              | https://python-pillow.org                                                          |
| certifi                 | 2026.10.23 | Mozilla Public License 2.0 (MPL 2.0) | https://github.com/certifi/python-certifi                                          |
| typing_extensions       | 4.16.0     | PSF-2.0                              | https://github.com/python/typing_extensions                                        |
| defusedxml              | 0.7.1      | Python Software Foundation License   | https://github.com/tiran/defusedxml                                                |
| email-validator         | 2.3.0      | The Unlicense (Unlicense)            | https://github.com/JoshData/python-email-validator                                 |

## Frontend (npm): полный список

```
"module name","license"
"@fontsource-variable/roboto@5.3.0","OFL-1.1"
"@img/colour@1.1.0","MIT"
"@img/sharp-darwin-arm64@0.35.5","Apache-2.0"
"@img/sharp-libvips-darwin-arm64@1.3.4","LGPL-3.0-or-later"
"@next/env@16.4.3","MIT"
"@next/swc-darwin-arm64@16.4.3","MIT"
"@parcel/watcher-darwin-arm64@2.6.0","MIT"
"@parcel/watcher@2.6.0","MIT"
"@playwright/test@1.64.1","Apache-2.0"
"@swc/helpers@0.5.23","Apache-2.0"
"@tanstack/query-core@5.105.0","MIT"
"@tanstack/react-query@5.105.0","MIT"
"@types/react@19.3.0","MIT"
"baseline-browser-mapping@2.11.33","Apache-2.0"
"caniuse-lite@1.0.30001819","CC-BY-4.0"
"chokidar@5.0.0","MIT"
"client-only@0.0.1","MIT"
"csstype@3.2.3","MIT"
"detect-libc@2.1.2","Apache-2.0"
"frontend@0.1.0","UNLICENSED"
"immutable@5.1.9","MIT"
"is-extglob@2.1.1","MIT"
"is-glob@4.0.3","MIT"
"nanoid@3.3.20","MIT"
"next@16.4.3","MIT"
"node-addon-api@7.1.1","MIT"
"picocolors@1.1.1","ISC"
"picomatch@4.0.7","MIT"
"playwright-core@1.64.1","Apache-2.0"
"playwright@1.64.1","Apache-2.0"
"postcss@8.5.23","MIT"
"react-dom@19.3.0","MIT"
"react@19.3.0","MIT"
"readdirp@5.1.1","MIT"
"sass@1.106.1","MIT"
"scheduler@0.28.0","MIT"
"semver@7.8.5","ISC"
"sharp@0.35.5","Apache-2.0"
"source-map-js@1.2.2","BSD-3-Clause"
"styled-jsx@5.1.6","MIT"
"tslib@2.8.1","0BSD"
```
