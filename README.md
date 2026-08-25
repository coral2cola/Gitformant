# Gitformant | ギトフルマント
![logo](https://i.imgur.com/rflqsil.png "Gitformant Logo")

## 변경사항 (Changelog) — 2026-08

이 포크는 오래된 원본 코드의 보안·로직 문제를 개선했습니다.

- **토큰 하드코딩 제거**: GitHub API 토큰을 소스에 직접 넣지 않고 `.env` 파일에서 불러오도록 변경했습니다. `.gitignore`에 `.env`를 추가해 실수로 커밋되는 것을 막았습니다.
- **폐기된 인증 방식 교체**: GitHub가 2020년에 제거한 `access_token` URL 쿼리 파라미터 인증을 `Authorization` 헤더 방식으로 교체했습니다. 기존 방식으로는 도구가 동작하지 않았고, 토큰이 URL/로그에 노출되는 문제도 있었습니다.
- **로직 버그 수정**: 레이트리밋 시 발생하던 무한 루프, 도달할 수 없던 신뢰도(`VERY LOW`) 분기, 오류 시 예외 객체를 개수처럼 반환하던 문제, API 오류 응답 미처리, 초기 검색 실패 시 발생하던 `NameError` 등을 수정했습니다.
- **사내망(SSL 검사) 지원**: SSL 검사(TLS 인터셉션) 프록시가 있는 사내망에서도 인증서 검증을 끄지 않고 동작하도록, `truststore`로 운영체제(Windows) 인증서 저장소를 신뢰합니다. 사내 루트 CA가 설치된 회사 PC에서 별도 설정 없이 그대로 실행됩니다.
- **기타**: 요청에 타임아웃을 추가하고, `requirements.txt`를 UTF-8로 재저장하며 `python-dotenv`와 `truststore`를 추가했습니다.

### 설정 방법 (Setup)

1. `.env.example`을 복사해 `.env` 파일을 만들고 `GITHUB_API_TOKEN` 값을 채웁니다.
   ```
   cp .env.example .env
   ```
2. 의존성을 설치합니다.
   ```
   pip install -r requirements.txt
   ```
3. 실행합니다.
   ```
   python gitformant.py "<keyword>"
   ```

---

## Changelog (English) — 2026-08

This fork improves the security and logic issues in the original, unmaintained code.

- **Removed the hardcoded token**: the GitHub API token is now loaded from a `.env` file instead of being written into the source. `.env` is listed in `.gitignore` so it cannot be committed by accident.
- **Replaced the deprecated auth method**: the `access_token` URL query parameter (removed by GitHub in 2020) was replaced with the `Authorization` header. The old method no longer worked and leaked the token into URLs/logs.
- **Fixed logic bugs**: an infinite loop on rate limiting, an unreachable `VERY LOW` confidence branch, returning an exception object where a count was expected, unhandled API error responses, and a `NameError` when the initial search failed.
- **Corporate network (SSL inspection) support**: trusts the operating system's (Windows) certificate store via `truststore`, so the tool keeps working behind SSL-inspecting proxies without disabling certificate verification. It runs as-is on a corporate PC where the internal root CA is installed.
- **Other**: added request timeouts, re-saved `requirements.txt` as UTF-8, and added `python-dotenv` and `truststore`.

### Setup

1. Copy `.env.example` to `.env` and fill in `GITHUB_API_TOKEN`:
   ```
   cp .env.example .env
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run:
   ```
   python gitformant.py "<keyword>"
   ```

Gitformant is an Open Source Intelligence (OSINT) tool developed by [Shogun Lab](http://www.shogunlab.com/) to aid researchers and security professionals in discovering Github repositories that may contain confidential information. It works by [searching Github](https://developer.github.com/v3/search/) for a keyword (internal URL, project specific acronym or terminology, etc) from code or internal documents. Additional checks can be performed if provided with a second list of keywords for verifying that the repository contents belong to a specific entity (ACME, acme.com/employee_login, Project Roadrunner, etc).

## Installation
Gitformant can be installed by downloading the zip file [here](https://github.com/shogunlab/gitformant/archive/master.zip) or by cloning the [Git](https://github.com/shogunlab/gitformant.git) repository:

`git clone https://github.com/shogunlab/gitformant.git`

Gitformant works with [Python](http://www.python.org/download/) **3** on any platform.

The included `requirements.txt` file can be used to install the pre-requisites with the following:
```
pip install -r requirements.txt
```

## Features
- Search Github for keywords belonging to confidential documents and discover leaks.
- Perform checks on discovered repositories to confirm or deny that they belong to a target organization.
- Log all results for further investigation and reporting.

## Usage
To perform a search on Github for an internal keyword, type:

`python gitformant.py "<insert internal keyword here>"`

To check the returned results for the existence of additional keywords, type:

`python gitformant.py "<insert internal keyword here>" "<insert confirmation keywords list here (comma separated)>"`

## Example Use Case
1. Alice is hired by ACME Inc. to perform an Open Source Intelligence assessment and find out if confidential ACME code is being leaked online.
2. She checks multiple search engines to see if the leaked code is being indexed, but doesn't find anything.
3. Alice asks the client if there are internal URLs or company keywords that are frequently used in development code.
4. The client gives Alice "login.acme-portal.com", the URL for their employee login portal and a link that frequently appears in the clients' private Github.
5. Alice performs a search for the keyword using Gitformant:
- `python gitformant.py "login.acme-portal.com"`
6. Alice finds no results, thinking that the keyword may be too specific, she changes the query to "acme-portal.com":
- `python gitformant.py "acme-portal.com"`
7. Alice is surprised to find several hundred results, however many of the findings are simply junk that makes reference to "acme-portal.com" among many other online portals.
8. Undeterred, Alice performs additional checks for ACME specific keywords in the repositories discovered using Gitformant:
- `python gitformant.py "acme-portal.com" "ACME,www.acme.com,ACME Inc"`
9. Alice discovers that one repository contains "acme-portal.com" and also has 32 hits for ACME, 15 hits for acme.com and 3 hits for ACME Inc.
10. Alice investigates the repository and finds that it is source code for an ACME Inc. production website with hardcoded admin login credentials.


### Misc. Usage and Performance Notes
- **Don't forget to add your Github API key!** Copy `.env.example` to `.env` and set `GITHUB_API_TOKEN` (it is no longer stored in the source). Find out more about creating a token [here](https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/).
- There is a rate limit on the Github Search API, to avoid going over this limit a delay is built into the calls to Github's API
    - If the rate limit is hit, the application will sleep and then resume after 10 seconds
- Each confirmation keyword provided means an additional check is performed on every discovered repo, which means it can get **slow** FAST!
    - Try to limit confirmation keyword lists to two or three words (or grab a cup of coffee)

## Screenshots
**Basic usage**
![screen_1](https://i.imgur.com/m3OMqiF.png?1 "Gitformant Screenshot #1")

**With confirmation keywords list**
![screen_2](https://i.imgur.com/7lNK9i8.png?1 "Gitformant Screenshot #2")
![screen_3](https://i.imgur.com/EZ30blE.png?2 "Gitformant Screenshot #3")

## Legal
Gitformant was inspired by an excellent OSINT tool, called [Datasploit](https://github.com/DataSploit/datasploit).

The Gitformant OSINT tool is licensed under a GNU General Public License v3.0, you can read it [here](https://github.com/shogunlab/gitformant/blob/master/LICENSE.md).

The Gitformant logo is licensed under a [Creative Commons Creative Attribution 3.0 United States License](https://creativecommons.org/licenses/by/3.0/us/legalcode). Authored by ProSymbols.
