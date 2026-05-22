# Implementation Plan - MDBrowser Individual Note Deletion

사용자가 마크다운 노트를 읽는 도중 필요 없는 노트를 즉시 삭제할 수 있도록, **개별 노트 영구 삭제 기능 (Individual Note Deletion)**을 추가합니다.

---

## User Review Required

> [!IMPORTANT]
> - **삭제 경고 및 토스트**:
>   - 삭제 작업은 로컬 디스크에서 파일을 영구 삭제하므로, 즉각적인 삭제를 피하고 브라우저 `confirm` 창을 통해 사용자의 명시적인 재확인을 받습니다.
>   - 삭제가 성공하면 우측 하단에 미려한 녹색 **성공 토스트(Toast) 알림**을 띄워 시각적 피드백을 전달합니다.
> - **실시간 목록 갱신**:
>   - 노트가 삭제되면 현재 뷰어 영역을 즉시 비움(Empty State) 처리합니다.
>   - 좌측 사이드바의 노트북 노트 갯수 및 태그 카운트가 즉각 차감되어 실시간 갱신되도록 하고, 중앙의 노트 카드 목록에서도 해당 카드가 부드럽게 사라지도록 동적 갱신 로직을 통합합니다.
> - **강력한 샌드박스 보안**:
>   - 백엔드(`/api/notes/delete`) 단에서 경로 탈출 문자(`..`, `/`, `\\`)를 검증하고, 오직 `.md` 마크다운 확장자만 허용되도록 강제하는 샌드박스 보안 장치를 구현합니다.

---

## Proposed Changes

### [Backend Server Component]

#### [MODIFY] [server.py](file:///C:/_My2026/_EVERBK/_MDBrower/server.py)
* **`/api/notes/delete` (POST) API 구현**:
  * 요청된 노트북명과 파일명을 수신합니다.
  * **보안 예외 검사**:
    * 노트북 이름과 파일 이름에 `..`, `/`, `\\` 등의 탈출 경로 기호가 절대 포함될 수 없도록 강제합니다.
    * 삭제 파일 확장자가 `.md` 인지 체크합니다.
    * 파일이 실제로 `C:/_My2026/_EVERBK/markdown/<notebook>/<filename>`에 존재하는지 실존 여부를 검사합니다.
  * 검증 통과 시 파일을 영구 삭제(`unlink()`)하고 JSON 성공 신호를 응답합니다.

---

### [Frontend Component]

#### [MODIFY] [index.html](file:///C:/_My2026/_EVERBK/_MDBrower/templates/index.html)
* **UI 마크업 추가**:
  - `view-options-group` 바로 오른쪽에 붉은색 포인트 테두리와 아이콘이 포함된 프리미엄 삭제 버튼(`[delete]`)을 마크업합니다.
  - 마우스 오버 시 `var(--accent-danger)` 글로우와 배경 투명도가 알맞게 변하도록 호버 스크립트와 스타일을 주입합니다.
  - 화면 하단에 삭제 성공 토스트 팝업 마크업 및 애니메이션 스타일(CSS)을 연동합니다.
* **Javascript 제어 로직 추가**:
  - 현재 읽고 있는 노트의 `currentNotebook` 및 `currentFilename` 정보를 전역에서 관리합니다.
  - `viewNote(notebook, filename)` 호출 시 해당 전역 변수들을 세팅합니다.
  - 삭제 단추 클릭 시 동작할 `deleteCurrentNote()` 함수를 구현합니다:
    - 팝업으로 재확인을 거친 후 `POST /api/notes/delete`로 삭제 요청을 전송합니다.
    - 삭제 성공 시 성공 토스트 알림을 연출합니다.
    - 뷰어를 비움(Empty State) 상태로 전환합니다.
    - `loadNotebooks()`, `loadTags()` 및 현재 필터 기준(`activeNotebook`, `activeTag` 여부)에 부합하는 `loadNotebookNotes()` / `loadTaggedNotes()` / `loadAllNotes()` 함수들을 순차 호출하여 화면 전체를 유기적이고 상쾌하게 실시간 갱신합니다.
