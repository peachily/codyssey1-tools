# 에셋 관리

```text
assets/
├── images/peachily.jpg        # 사용자 제공 복숭아 이미지
├── icons/ui.svg              # 직접 제작한 공통 UI SVG Sprite
├── icons/technologies/       # 기술별 브랜드 로고, 각 원본 1개
└── licenses/
    ├── devicon-MIT.txt       # Devicon MIT 라이선스 원문
    ├── simple-icons-CC0.txt   # PocketBase 로고 라이선스 원문
    └── sources.json          # 파일별 원본 URL·버전·SHA-256·라이선스
```

런타임 CDN, 아이콘 폰트, 프레임워크 의존성 없이 로컬 SVG 파일을 사용합니다. 기술 이름은 이미지와 별개의 HTML 텍스트로 남겨 이미지 로딩 실패 시에도 읽을 수 있습니다. 기술 로고는 이름이 중복 설명하므로 `alt=""`로 처리합니다. REST API는 Skills에서 제외합니다. Projects의 REST API·CSV·XML 등 매핑이 없는 기술은 텍스트만 표시합니다.

## 브랜드 로고 출처와 사용 조건

확인일: 2026-10-23.

- HTML5, CSS3, JavaScript, TypeScript, React, Vite, Python, Node.js, FastAPI, SQLite, Git, GitHub, Linux, Amazon Web Services, Railway, Cloudflare, Tailwind CSS, PostgreSQL, Supabase, Docker, Netlify, Figma: [Devicon](https://github.com/devicons/devicon) 원본 SVG. Revision `6a37858047b0e8d9c9c0e68f4a071fc410652e89`로 고정했습니다. 라이선스 원문은 `licenses/devicon-MIT.txt`에 포함합니다. AWS는 `amazonwebservices-original-wordmark`, SQLite는 `sqlite-original` 로고이며 임의의 대체 그림을 사용하지 않습니다.
- OpenAI API: [OpenAI 공식 로고 묶음](https://cdn.openai.com/brand/OpenAI-Logos-2025.zip)의 `OpenAI-logos(new)/SVGs/OpenAI-black-monoblossom.svg`를 수정 없이 사용합니다. 일반 채팅 아이콘이 아닌 공식 Blossom입니다. OpenAI 로고는 Devicon MIT 라이선스 대상이 아니며 [공식 브랜드 가이드·사용 조건](https://openai.com/brand/)을 따릅니다. OpenAI 및 Blossom 상표의 권리는 OpenAI에 있습니다.
- Devicon의 MIT 라이선스와 별개로 각 브랜드명·로고·상표의 권리는 해당 소유자에게 있습니다. 포트폴리오의 기술 사용을 식별하기 위해 사용하며 제휴·후원·공식 인증을 의미하지 않습니다.
- PocketBase: [Simple Icons](https://github.com/simple-icons/simple-icons), revision `c71c69e3a27e4436936b831c72643e6513b9f49b`의 `icons/pocketbase.svg`. CC0-1.0 원문은 `licenses/simple-icons-CC0.txt`에 포함합니다. 상표 권리는 PocketBase에 있습니다.
- 사용하지 않는 라이브러리·로고 변형은 저장하지 않습니다. `js/technologies.js`가 Skills와 Projects의 브랜드 매핑과 표시 명칭을 함께 관리합니다.

로고의 원본 색상·비율·도형을 유지합니다. 배지를 라이트·다크 모드 모두 흰색, 글자를 짙은 색으로 두어 검은 OpenAI/GitHub와 다색 AWS/SQLite 로고가 그대로 보이도록 합니다. Railway 원본은 흰색이므로 18px 로고 뒤에 작은 짙은 원형 배경을 둡니다. CSS 색 반전이나 로고 재색칠은 사용하지 않습니다.

## 이미지 교체

`images/peachily.jpg`는 사용자가 제공한 750×750 이미지입니다. 파일 내용은 변경하지 않았고 Hero·About에서 같은 파일을 사용합니다. Hero의 중복 이미지는 장식 처리하며 About에는 이미지 내용에 맞는 alt를 제공합니다. 교체 시 동일 파일을 덮어쓰거나 HTML의 두 src를 함께 갱신합니다.
