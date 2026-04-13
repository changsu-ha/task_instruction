# Robot Scenario Viewer

로봇 manipulation 데이터 수집을 위한 경량 Ubuntu Python 데스크탑 앱입니다.  
VLA(Vision-Language-Action) 모델의 imitation learning 데이터를 수집하는 외부 인력(collector)에게 에피소드별 설정(물체 위치/자세, target 위치 등)을 시각적으로 전달하고, 수집 결과를 데이터셋 메타데이터로 로깅합니다.

---

## 화면 구성

```
┌─────────────────────────────────────────────────────────────────┐
│ 메뉴: File | Help                                               │
├──────────────────────────────┬──────────────────────────────────┤
│                              │ [태스크명]                        │
│      SCENE CANVAS            │ Episode 1 / 10                   │
│   (2D top-down 뷰)           │ Episode 1 — 박스 중앙, 왼쪽 선반  │
│                              │ ─────────────────────────────── │
│  [그리드]                    │ Objects:                         │
│  [로봇 베이스 ●]              │  ■ Red Box → +5cm (오른쪽)       │
│  [박스 ■ + 방향 화살표]       │  ░ Target Shelf → 왼쪽 선반      │
│  [target ░ dashed]           │  ○ Home → front center          │
│                              │                                  │
│  Ctrl+스크롤: 줌             │ Notes: (에피소드 주의사항)        │
│  드래그: 팬                  │ ─────────────────────────────── │
│                              │ Notes: [메모 입력창]             │
│                              │ [Collected] [Skip] [Retry]      │
│                              │ Collected:0 Skip:0 Retry:0      │
│                              │ [Export…]                        │
├──────────────────────────────┴──────────────────────────────────┤
│  [<< Prev]   Episode 1 / 10   [Next >>]   [Random]   [Go to ▼] │
└─────────────────────────────────────────────────────────────────┘
```

| 영역 | 설명 |
|------|------|
| **Scene Canvas (왼쪽)** | 작업 공간을 top-down 2D로 시각화. 로봇 베이스, 물체 위치/자세, target 구역을 그래픽으로 표시 |
| **Config Panel (오른쪽 상단)** | 현재 에피소드의 설정을 텍스트로 표시. 물체별 컬러 아이콘 + 라벨 + 설명 |
| **Log Panel (오른쪽 하단)** | 수집 상태 기록 버튼 (Collected / Skip / Retry) 및 메모 입력, 로그 내보내기 |
| **Nav Bar (하단)** | 에피소드 이동 (이전/다음/랜덤/드롭다운) |

---

## 설치 및 실행

### 요구사항

- Ubuntu 18.04 이상
- Python 3.8 이상

### 설치

```bash
git clone <repo-url>
cd task_instruction
pip install -r requirements.txt
```

`requirements.txt`:
```
PyQt5>=5.15.11
PyYAML>=6.0.1
```

### 실행

```bash
# 태스크 파일을 직접 지정해서 실행
python run.py --task tasks/pick_and_place.yaml

# 다른 태스크 파일로 실행
python run.py --task tasks/shelf_sorting.yaml

# 로그 저장 위치 지정
python run.py --task tasks/pick_and_place.yaml --log-dir /path/to/logs

# 인자 없이 실행 (메뉴에서 File > Open Task로 파일 열기)
python run.py
```

---

## 프로젝트 구조

```
task_instruction/
├── run.py                       # CLI 진입점
├── requirements.txt
│
├── app/                         # UI 위젯
│   ├── __init__.py
│   ├── main_window.py           # 루트 창: QSplitter로 전체 레이아웃 조립
│   ├── scene_view.py            # Scene Canvas: QGraphicsView 기반 2D 뷰
│   ├── config_panel.py          # Config Panel: 에피소드 텍스트 정보 표시
│   ├── nav_bar.py               # Nav Bar: Prev/Next/Random/드롭다운
│   └── log_panel.py             # Log Panel: 상태 버튼, 메모, Export
│
├── core/                        # 비즈니스 로직 (UI 독립)
│   ├── __init__.py
│   ├── models.py                # 데이터클래스 정의
│   ├── episode_manager.py       # YAML 로드 + 에피소드 상태 관리 (Qt Signal)
│   ├── renderer.py              # Episode → QGraphicsItem 변환 (순수 함수)
│   └── logger.py                # JSONL 로거 + CSV/JSON 내보내기
│
├── tasks/                       # 태스크 정의 YAML 파일
│   ├── pick_and_place.yaml      # 예시: 박스 집어서 선반에 놓기 (10 에피소드)
│   └── shelf_sorting.yaml       # 예시: 멀티 오브젝트 선반 정렬 (5 에피소드)
│
└── logs/                        # 수집 세션 로그 (런타임 자동 생성)
    └── .gitkeep
```

---

## 태스크 YAML 파일 작성 방법

새로운 태스크를 추가하려면 `tasks/` 폴더에 YAML 파일을 작성합니다.

### 전체 구조

```yaml
task:
  name: "태스크 이름"
  description: >
    collector에게 보여줄 태스크 설명 텍스트.
    여러 줄로 작성 가능합니다.
  version: "1.0"

  workspace:
    width_cm: 60        # 작업 공간 가로 (cm)
    height_cm: 50       # 작업 공간 세로 (cm)
    origin: "center"    # 좌표 원점: "center" (중앙) 또는 "top-left"

  robot:
    base_x_cm: 0        # 로봇 베이스 X 위치 (cm, 원점 기준)
    base_y_cm: -22      # 로봇 베이스 Y 위치 (음수 = 화면 아래쪽, 조작자 방향)
    base_radius_cm: 5   # 시각화 크기

  object_types:         # 에피소드에서 사용할 물체 팔레트
    <타입명>:
      shape: "rectangle"  # "rectangle" 또는 "circle"
      color: "#E74C3C"    # 16진수 색상 코드
      width_cm: 8         # rectangle 전용
      height_cm: 6        # rectangle 전용
      radius_cm: 3.5      # circle 전용
      style: "solid"      # "solid" (실선) 또는 "dashed" (점선, target 구역에 권장)

episodes:
  - id: 1
    label: "에피소드 제목"
    objects:
      - id: "고유_ID"
        type: "object_types에서 정의한 타입명"
        x_cm: 5.0         # X 위치 (cm, 원점 기준)
        y_cm: 0.0         # Y 위치 (cm, 원점 기준, 양수 = 화면 위쪽)
        rotation_deg: 0   # 회전 각도 (도, 반시계 방향 양수)
        label: "화면에 표시할 라벨"
        description: "Config Panel에 표시할 설명 (예: +5cm (오른쪽))"
    notes: "이 에피소드 관련 주의사항 (노란색으로 강조 표시)"
```

### 물체 타입(object_types) 설계 가이드

| 용도 | 권장 설정 |
|------|---------|
| 조작 대상 물체 (박스, 캔 등) | `shape: rectangle/circle`, `style: solid`, 눈에 띄는 색상 |
| Target 구역 (목표 위치) | `style: dashed`, 반투명한 녹색 계열 |
| Gripper 홈 포지션 | `shape: circle`, 보라색 계열 |

### 좌표계

```
           +Y (화면 위, 로봇에서 멀어지는 방향)
            |
  -X ───── 0 ───── +X
            |
           -Y (화면 아래, 로봇 베이스 방향)
```

- `origin: "center"` 기준으로 로봇 베이스는 보통 `-Y` 방향에 위치 (`base_y_cm: -20` 등)
- `rotation_deg: 0` = 위쪽(+Y 방향), 양수 값은 반시계 방향 회전

### 예시: pick_and_place.yaml

```yaml
task:
  name: "Pick and Place - Box to Shelf"
  description: >
    빨간 박스를 테이블에서 집어서 목표 선반 위치에 놓으세요.
  version: "1.0"
  workspace:
    width_cm: 60
    height_cm: 50
    origin: "center"
  robot:
    base_x_cm: 0
    base_y_cm: -22
    base_radius_cm: 5

  object_types:
    box:
      shape: "rectangle"
      color: "#E74C3C"
      width_cm: 8
      height_cm: 6
    shelf_target:
      shape: "rectangle"
      color: "#2ECC71"
      width_cm: 12
      height_cm: 8
      style: "dashed"

episodes:
  - id: 1
    label: "Episode 1 — 박스 중앙, 왼쪽 선반"
    objects:
      - id: "box_1"
        type: "box"
        x_cm: 5
        y_cm: 0
        rotation_deg: 0
        label: "Red Box"
        description: "+5cm (오른쪽)"
      - id: "target_1"
        type: "shelf_target"
        x_cm: -18
        y_cm: 8
        rotation_deg: 0
        label: "Target Shelf"
        description: "왼쪽 선반"
    notes: ""
```

---

## 데이터 수집 워크플로우

1. **앱 실행**: `python run.py --task tasks/my_task.yaml`
2. **에피소드 확인**: Scene Canvas에서 물체/target 배치를 확인하고, Config Panel에서 텍스트 정보를 확인
3. **실제 환경 세팅**: 화면에 표시된 위치/자세대로 물체 배치
4. **데이터 수집 진행**: 로봇으로 태스크 수행
5. **결과 기록**:
   - **Collected**: 수집 성공 → 자동으로 다음 에피소드로 이동
   - **Skip**: 해당 에피소드 건너뜀 (조명 불량, 셋업 문제 등)
   - **Retry**: 재수집 필요 표시 (나중에 다시 돌아옴)
6. **메모 입력** (선택): Notes 입력란에 특이사항 기록
7. **내보내기**: 세션 종료 시 [Export…] 또는 메뉴 File > Export Log로 로그 저장

---

## 로그 파일

### 자동 저장 위치

수집 도중 `logs/` 폴더에 JSONL 형식으로 자동 저장됩니다.

```
logs/
└── Pick_and_Place_Box_to_Shelf_a3f2b1c4.jsonl
```

파일명: `<태스크명>_<세션UUID 앞 8자리>.jsonl`

### JSONL 형식 (라인별 1개 에피소드 레코드)

```jsonl
{"session_id": "a3f2b1c4-...", "task_name": "Pick and Place - Box to Shelf", "episode_id": 1, "status": "collected", "start_time": "2026-04-13T14:30:00.000+00:00", "end_time": "2026-04-13T14:32:01.500+00:00", "duration_seconds": 121.5, "operator_notes": "", "config_snapshot": {"label": "Episode 1 — 박스 중앙, 왼쪽 선반", "objects": [...]}}
{"session_id": "a3f2b1c4-...", "task_name": "Pick and Place - Box to Shelf", "episode_id": 2, "status": "skipped", "start_time": "...", "end_time": "...", "duration_seconds": 4.2, "operator_notes": "조명 불량"}
```

| 필드 | 설명 |
|------|------|
| `session_id` | 앱 실행마다 새로 생성되는 UUID |
| `episode_id` | 에피소드 번호 (YAML의 `id` 값) |
| `status` | `collected` / `skipped` / `retry` / `pending` |
| `start_time` / `end_time` | ISO 8601 타임스탬프 |
| `duration_seconds` | 에피소드 소요 시간 |
| `operator_notes` | 수집자 메모 |
| `config_snapshot` | 해당 에피소드의 물체 배치 정보 (YAML 변경 후에도 추적 가능) |

### Export (수동 내보내기)

**JSON 내보내기** (데이터셋 메타데이터로 활용 권장):

```json
{
  "export_time": "2026-04-13T15:00:00.000+00:00",
  "session_id": "a3f2b1c4-...",
  "task": {
    "name": "Pick and Place - Box to Shelf"
  },
  "summary": {
    "total": 10,
    "collected": 8,
    "skipped": 1,
    "retry": 1,
    "pending": 0
  },
  "episodes": [
    {
      "episode_id": 1,
      "status": "collected",
      "duration_seconds": 121.5,
      "operator_notes": "",
      "config_snapshot": {
        "label": "Episode 1 — 박스 중앙, 왼쪽 선반",
        "objects": [
          {"id": "box_1", "x_cm": 5.0, "y_cm": 0.0, "rotation_deg": 0.0, ...}
        ]
      }
    }
  ]
}
```

**CSV 내보내기** (스프레드시트 분석용):

```csv
session_id,task_name,episode_id,status,start_time,end_time,duration_seconds,operator_notes
a3f2b1c4,...,Pick and Place,1,collected,2026-04-13T14:30:00Z,2026-04-13T14:32:01Z,121.5,
a3f2b1c4,...,Pick and Place,2,skipped,2026-04-13T14:32:01Z,2026-04-13T14:32:05Z,4.2,조명 불량
```

---

## 키보드 단축키

| 단축키 | 동작 |
|--------|------|
| `Ctrl+O` | 태스크 YAML 파일 열기 |
| `Ctrl+E` | 로그 내보내기 |
| `Ctrl+Q` | 종료 |
| `Ctrl+스크롤` | Scene Canvas 줌 인/아웃 |
| `드래그 (마우스)` | Scene Canvas 팬 |

---

## 핵심 모듈 설명

### `core/models.py` — 데이터 모델

모든 데이터 구조를 Python 데이터클래스로 정의합니다. YAML 파서, 렌더러, 로거 간의 계약 역할을 합니다.

```
TaskConfig       태스크 전체 설정 (이름, workspace, object_types, episodes)
WorkspaceConfig  작업 공간 크기, 원점 설정, 로봇 베이스 위치
ObjectTypeConfig 물체 팔레트 항목 (shape, color, size, style)
PlacedObject     에피소드 내 물체 인스턴스 (위치, 회전, 라벨)
Episode          에피소드 1개 (id, label, objects, notes)
LogEntry         수집 결과 1건 (status, 시간, 메모, config_snapshot)
```

### `core/episode_manager.py` — 에피소드 관리

YAML을 파싱하고 현재 에피소드 상태를 관리합니다. Qt 시그널로 UI에 변경을 전파합니다.

```python
manager = EpisodeManager()
task_config = manager.load_task(Path("tasks/pick_and_place.yaml"))
manager.episode_changed.connect(my_slot)  # (Episode, index) 시그널

manager.next()       # 다음 에피소드
manager.prev()       # 이전 에피소드
manager.random()     # 랜덤 에피소드
manager.go_to(3)     # 인덱스 지정 이동
```

### `core/renderer.py` — 2D 렌더러

Episode와 TaskConfig를 받아 QGraphicsItem 리스트를 반환합니다. UI 상태를 갖지 않아 단독 테스트가 가능합니다.

```python
renderer = SceneRenderer(workspace_config, px_per_cm=10.0)
items = renderer.render_episode(episode, task_config.object_types)
for item in items:
    scene.addItem(item)
```

좌표 변환: 실세계 cm → Qt scene 픽셀 (Y축 반전 포함)

```python
scene_point = renderer.world_to_scene(x_cm=5.0, y_cm=3.0)
```

### `core/logger.py` — 세션 로거

에피소드 시작/종료를 기록하고 JSONL로 append합니다.

```python
logger = SessionLogger(task_name="My Task", log_dir=Path("logs"))

logger.start_episode(episode)                        # 타이머 시작
logger.end_episode(episode.id, "collected", "메모")  # 기록 및 JSONL append

logger.export_json(Path("output.json"))              # JSON 전체 내보내기
logger.export_csv(Path("output.csv"))                # CSV 내보내기

summary = logger.get_summary()
# {"collected": 5, "skipped": 1, "retry": 1, "pending": 3}
```

---

## 새 태스크 추가하기

1. `tasks/` 폴더에 새 YAML 파일 생성
2. `task.object_types`에 사용할 물체 타입 정의
3. `episodes` 리스트에 에피소드별 물체 배치 작성
4. 실행: `python run.py --task tasks/my_new_task.yaml`

물체 타입을 추가하거나 에피소드를 수정해도 앱 코드를 변경할 필요가 없습니다.

---

## 확장 포인트

| 확장 | 방법 |
|------|------|
| 새 물체 shape 추가 | `core/renderer.py`의 `_render_object()` 메서드에 분기 추가 |
| 원격 로그 서버 전송 | `core/logger.py`의 `_append_record()` 메서드에서 HTTP POST 추가 |
| 에피소드 무작위 샘플링 정책 | `core/episode_manager.py`의 `random()` 메서드 수정 |
| 카메라 오버레이 | `app/scene_view.py`에 `QGraphicsPixmapItem`으로 카메라 프레임 합성 |
