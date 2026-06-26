# Evernote Archive Navigator (MDBrowser)

로컬로 백업된 에버노트 마크다운 아카이브를 탐색, 읽기 및 관리할 수 있는 다크 모드 기반의 프리미엄 로컬 마크다운 뷰어 및 중복 정리 도구입니다.

---

## 주요 기능

1. **마크다운 아카이브 탐색기**: 노트북 별 탐색 및 자동 태그 클라우드 집계 필터링.
2. **3단 멀티 뷰어**: 렌더링된 프리뷰, 순수 마크다운 소스, 구문 강조(Prism.js)가 적용된 HTML 소스 토글 뷰.
3. **에버노트 리소스 연동**: 백업 폴더 내의 첨부 이미지, PDF 문서를 로컬 경로에 맞춰 깨짐 없이 시각화.
4. **중복 파일 정리기**: 동일한 제목으로 생성된 중복 마크다운 복제본(`*_1.md`, `*_2.md` 등)을 자동 스캔하여 안전하게 일괄 제거.
5. **보안 샌드박스 개별 삭제**: 경로 탈출 차단 보안 로직을 탑재하여 개별 노트를 화면에서 비동기로 즉시 영구 삭제.

---

## 로컬 실행 방법 (개발 모드)

### 1. 의존성 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 기동 방법
* **배치 런처 실행**: `run_server.bat`를 더블 클릭합니다.
* **직접 실행**:
  ```bash
  python server.py
  ```
  기동 후 브라우저에서 `http://127.0.0.1:5000/`로 접속합니다.

---

## 📦 독립 실행형 (.exe) 빌드 방법

더 이상 Python 환경이 설치되어 있지 않은 환경에서도 실행 파일 하나만 클릭하여 마크다운 뷰어를 실행할 수 있도록 패키징할 수 있습니다.

### 1. PyInstaller 설치
```bash
pip install pyinstaller
```

### 2. 패키징 실행 (Windows 환경)
프로젝트 루트 디렉토리에서 다음 명령어를 실행하여 빌드를 수행합니다.

```powershell
python -m PyInstaller --clean --onefile --name mdbrower-server --add-data "templates;templates" --add-data "static;static" server.py
```

* **옵션 설명**:
  * `--clean`: 빌드 시작 전 기존 캐시 및 임시 파일 청소.
  * `--onefile`: 단일 실행 파일(`.exe`) 형태로 압축 패키징.
  * `--name mdbrower-server`: 생성될 실행 파일 이름을 `mdbrower-server.exe`로 지정.
  * `--add-data`: 웹 페이지를 이루는 `templates`와 `static` 정적 자원들을 바이너리 내부로 묶어 전달.

### 3. 빌드 결과물 확인
* 빌드가 완료되면 **`dist/`** 폴더에 **`mdbrower-server.exe`** 파일이 생성됩니다.
* 실행 시 프로그램과 동일한 경로에 `config.json` 환경 설정 파일이 자동으로 생성되어 마크다운 보관소 경로를 영구 기억합니다.
