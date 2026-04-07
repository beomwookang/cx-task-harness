<p align="center">
  <h1 align="center">CX Task Harness</h1>
  <p align="center">
    <strong>고객 지원 자동화 설계 도구 — Claude Code 플러그인</strong>
  </p>
  <p align="center">
    <a href="#설치">설치</a> &middot;
    <a href="#작동-방식">작동 방식</a> &middot;
    <a href="#활용-사례">활용 사례</a> &middot;
    <a href="#템플릿">템플릿</a> &middot;
    <a href="docs/TASK_SPEC.md">스펙 레퍼런스</a>
  </p>
  <p align="center">
    <a href="README.md">English</a> | <a href="README.ko.md"><strong>한국어</strong></a>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0-blue" alt="Version" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License" />
  <img src="https://img.shields.io/badge/Claude_Code-Plugin-blueviolet" alt="Claude Code Plugin" />
  <img src="https://img.shields.io/badge/python-3.11+-yellow" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/n8n-1.x-orange" alt="n8n 1.x" />
</p>

---

> **고객 지원 대화를 실제로 작동하는 자동화 워크플로우로 변환합니다.**
>
> CX Task Harness는 지원 데이터를 분석하고, 구조화된 자동화 스펙을 설계하며, 이를 가져올 수 있는 n8n 워크플로우로 변환합니다 — 모두 Claude Code 안에서 처리됩니다.

---

## 문제

고객 지원 팀은 매일 수천 건의 반복적인 문의를 처리합니다 — 주문 취소, 배송 추적, 예약 변경. AI 에이전트로 이를 자동화할 수 있지만, 병목은 **자동화 설계 과정** 자체에 있습니다:

- 어떤 문의를 자동화해야 할까?
- 대화 흐름은 어떻게 구성해야 할까?
- 어떤 API를 언제 호출해야 할까?
- 조건에 따라 에이전트가 어떻게 분기해야 할까?

**CX Task Harness는 설계 과정 자체를 자동화합니다.**

## 작동 방식

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   1. 분석              2. 설계             3. 변환               │
│                                                                  │
│   지원 로그      ──>  CX Task Spec   ──>  n8n 워크플로우          │
│   (CSV/JSON)          (구조화됨)          (가져오기 가능)          │
│                                                                  │
│   "무엇을               "어떻게             "실행 가능하게          │
│    자동화할까?"           작동할까?"          만들기"               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                              │
                  ┌───────────┴───────────┐
                  │                       │
            4. 검증                  5. 가이드
                  │                       │
            변환 전 구조 검사        수동 설정 항목에 대한
                                    설정 보고서 생성
```

| 단계 | 처리 내용 | 담당 |
|------|----------|------|
| **분석** | 의도별 지원 로그 클러스터링, 자동화 가능성 점수 산출 | Claude Code (LLM) |
| **설계** | 시나리오로부터 구조화된 CX Task Spec 생성 | Claude Code (LLM) |
| **검증** | 참조 오류, 순환 의존성, 분기 대상 확인 | MCP Tool (결정론적) |
| **변환** | 스펙을 가져올 수 있는 n8n 워크플로우 JSON으로 변환 | MCP Tool (결정론적) |
| **가이드** | 수동 설정 항목에 대한 설정 안내 생성 | Claude Code (LLM) |

### 왜 하이브리드 방식인가?

LLM 기반 작업(분석, 설계)은 프롬프트를 즉시 반복할 수 있는 Claude Code에서 처리합니다. 결정론적 작업(검증, 변환)은 Python이 정확성을 보장하는 MCP 서버에서 실행됩니다. 두 방식의 장점을 모두 활용합니다.

## 주요 기능

**구조화된 Task Spec** — 플랫폼 독립적인 JSON 스키마로 7가지 스텝 타입 제공 (agent, code, message, action, function, branch, browser), Pydantic 검증 및 discriminated union 지원

**스마트 검증** — 변환 전에 끊어진 참조, 순환 의존성, 도달 불가능한 스텝, 누락된 오류 핸들러를 사전에 감지

**n8n 워크플로우 생성** — 자동 배치 노드, 올바른 연결, 다중 분기 라우팅을 위한 Switch 노드가 포함된 가져오기 가능한 n8n JSON 생성

**목업 데이터 모드** — 외부 API 설정 없이 전체 플로우를 테스트할 수 있도록 목업 응답 노드 삽입

**산업별 템플릿** — 4개 산업에 걸쳐 8개의 완성된 템플릿 제공, 영어 및 한국어 지원

**설정 가이드** — 수동 설정이 필요한 노드를 자동으로 식별하고 단계별 안내 생성

## 설치

### Claude Code MCP 플러그인으로 설치

```bash
# MCP를 통해 설치
claude mcp add cx-task-harness \
  -- uv run --with fastmcp --with pydantic --with jsonschema \
  fastmcp run src/cx_task_harness/server.py
```

### 슬래시 커맨드 (선택 사항)

가이드 워크플로우를 위한 슬래시 커맨드를 프로젝트에 복사합니다:

```bash
# cx-task-harness 디렉터리에서 실행
cp claude/CLAUDE.md your-project/CLAUDE.md        # 또는 기존 파일에 병합
cp -r claude/commands/ your-project/.claude/commands/
```

이렇게 하면 Claude Code에서 세 가지 커맨드를 사용할 수 있습니다:

| 커맨드 | 설명 |
|--------|------|
| `/analyze` | 지원 로그를 분석하고 자동화 기회를 식별 |
| `/design` | 자연어 시나리오로부터 CX Task Spec 설계 |
| `/guide` | n8n 워크플로우 설정 가이드 생성 |

### 소스에서 설치

```bash
git clone https://github.com/your-username/cx-task-harness.git
cd cx-task-harness
uv sync --dev
uv run python -m pytest -v  # 88개 테스트
```

## 활용 사례

### "지원 채팅 로그가 있는데 무엇을 자동화할지 알고 싶어요"

```
> /analyze support_logs.csv

452개의 대화에서 자동화 가능한 패턴 3개 발견:
  1. 주문 취소 (127건, 점수: 0.92)
  2. 배송 추적 (98건, 점수: 0.88)
  3. 사이즈 교환 (67건, 점수: 0.75)
예상 자동화율: 64%
```

### "주문 취소 워크플로우를 설계해주세요"

```
> /design "이커머스 스토어의 주문 취소를 처리합니다.
>  주문 취소 가능 여부를 확인하고, 환불을 처리하며,
>  이미 배송된 경우 상담원에게 에스컬레이션합니다."

9개 스텝으로 구성된 TaskSpec 생성됨:
  agent → function → branch → function → message → action
  검증 완료: 오류 0개, 경고 0개
```

### "n8n으로 변환하고 설정할 항목을 알려주세요"

```
> 주문 취소 스펙을 n8n으로 변환해주세요

14개 노드로 구성된 n8n 워크플로우 생성됨
  2개 노드에 설정 필요:
  - "Check Order Status" → API 엔드포인트 + 인증
  - "Execute Cancellation" → API 엔드포인트 + 인증

> /guide

설정 가이드:
  바로 실행 가능: 12개 노드 (목업 데이터 포함)
  수동 설정 필요: HTTP Request 노드 2개
  [상세 단계별 안내...]
```

### "한국어 버전이 필요합니다"

```
> list_templates(industry="ecommerce", locale="ko")

템플릿:
  - ecommerce/order_cancel — 주문 취소 및 환불
  - ecommerce/exchange_return — 교환 및 반품 처리
  - ecommerce/delivery_tracking — 배송 조회
  - ecommerce/size_stock_check — 사이즈 및 재고 확인
```

## MCP 도구

| 도구 | 입력 | 출력 | 목적 |
|------|------|------|------|
| `validate_task_spec` | TaskSpec JSON | `{valid, errors, warnings}` | 구조 검증 |
| `convert_to_n8n` | TaskSpec JSON | `{workflow, setup_required}` | n8n 워크플로우 생성 |
| `validate_n8n` | n8n 워크플로우 JSON | `{valid, errors, n8n_version}` | n8n 스키마 검증 |
| `list_templates` | industry?, locale? | `{templates: [...]}` | 산업별 템플릿 탐색 |

## 템플릿

**영어**와 **한국어**로 제공되는 8개의 프로덕션 수준 템플릿:

| 산업 | 템플릿 | 스텝 수 | 설명 |
|------|--------|---------|------|
| **ecommerce** | `order_cancel` | 9 | 주문 취소 및 환불 |
| **ecommerce** | `exchange_return` | 8 | 교환 및 반품 처리 |
| **ecommerce** | `delivery_tracking` | 7 | 배송 상태 조회 |
| **ecommerce** | `size_stock_check` | 6 | 사이즈 및 재고 확인 |
| **travel** | `reservation_change` | 8 | 예약 변경 |
| **travel** | `reservation_cancel` | 8 | 예약 취소 |
| **saas** | `subscription_manage` | 8 | 구독 변경 및 취소 |
| **medical** | `appointment_change` | 7 | 예약 일정 변경 |

각 템플릿에는 트리거 조건, 종료 조건이 포함된 에이전트 지침, 오류 처리가 있는 API 호출 스텝, 조건부 분기, 자동화 가능성 점수가 포함됩니다.

## CX Task Spec

CX Task Spec은 고객 지원 자동화 작업을 설명하기 위한 **플랫폼 독립적인 JSON 스키마**입니다. 어떤 에이전트 플랫폼의 네이티브 형식으로도 변환할 수 있도록 설계되었습니다.

### 스텝 타입

| 타입 | 목적 | n8n 매핑 |
|------|------|---------|
| `agent` | 구조화된 지침이 있는 LLM 기반 대화 | AI Agent (LangChain) |
| `code` | 프로그래밍 로직 (JavaScript/Python) | Code Node |
| `message` | 고정 메시지 전달 | Set Node |
| `action` | 내부 작업 (팀 배정, 태그 설정, 종료) | Set Node |
| `function` | 외부 API 호출 | HTTP Request Node |
| `branch` | N개 조건을 가진 조건부 라우팅 | Switch Node |
| `browser` | 웹 자동화 | HTTP Request (플레이스홀더) |

전체 스키마 레퍼런스는 [TASK_SPEC.md](docs/TASK_SPEC.md)를 참고하세요.

## 아키텍처

```
cx-task-harness/
├── src/cx_task_harness/
│   ├── server.py              # FastMCP 서버 진입점
│   ├── models/                # Pydantic v2 모델 (Discriminated Union)
│   │   ├── common.py          # Trigger, AgentInstruction, BranchCondition
│   │   ├── steps.py           # 7가지 스텝 타입 + Step union
│   │   └── task_spec.py       # TaskSpec 최상위 모델
│   ├── tools/                 # MCP 도구 구현체
│   │   ├── validator.py       # 참조 검사, 순환 감지
│   │   ├── converter.py       # TaskSpec → n8n 오케스트레이터
│   │   ├── n8n_validator.py   # JSON Schema 검증
│   │   └── templates.py       # 템플릿 목록 및 로딩
│   ├── n8n/                   # n8n 변환 내부 구현
│   │   ├── mapper.py          # 스텝 → 노드 매핑
│   │   ├── layout.py          # 자동 배치 알고리즘
│   │   └── node_templates.py  # 노드 JSON 팩토리
│   └── templates/             # 16개 산업별 템플릿 파일
│       ├── ecommerce/         # 4개 템플릿 × 2개 로케일
│       ├── travel/            # 2개 템플릿 × 2개 로케일
│       ├── saas/              # 1개 템플릿 × 2개 로케일
│       └── medical/           # 1개 템플릿 × 2개 로케일
│
├── claude/                    # Claude Code 통합
│   ├── CLAUDE.md              # 워크플로우 가이드
│   └── commands/              # /analyze, /design, /guide
│
└── tests/                     # 88개 테스트 (단위 + 통합 + e2e)
```

## 기술 스택

| 컴포넌트 | 기술 |
|---------|------|
| MCP 서버 | [FastMCP](https://github.com/jlowin/fastmcp) (Python) |
| 스키마 검증 | [Pydantic v2](https://docs.pydantic.dev/) (Discriminated Union) |
| n8n 검증 | [jsonschema](https://python-jsonschema.readthedocs.io/) |
| 패키지 관리 | [uv](https://docs.astral.sh/uv/) |
| 테스팅 | pytest + syrupy (스냅샷 테스트) |

## 로드맵

- [ ] 자동화된 프로젝트 설정을 위한 `cx-task-harness init` CLI
- [ ] 다중 버전 n8n 스키마 지원
- [ ] 커뮤니티 템플릿 기여 시스템
- [ ] 추가 플랫폼 어댑터 (n8n 외)
- [ ] 템플릿 마켓플레이스

## 기여

기여를 환영합니다! 새로운 산업에 대한 템플릿은 특히 감사히 받겠습니다.

```bash
# 테스트 실행
uv sync --dev
uv run python -m pytest -v

# 새 템플릿 추가
# 1. src/cx_task_harness/templates/{industry}/{name}.en.json 생성
# 2. .ko.json 버전 생성
# 3. 테스트 실행 — 모든 템플릿을 자동으로 탐색하고 검증합니다
```

## 라이선스

[MIT](LICENSE) — 개인 및 상업 프로젝트에서 자유롭게 사용하세요.
