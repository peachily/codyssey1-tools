# 에셋 관리

`icons.svg`는 이 프로젝트에서 만든 공통 SVG Sprite입니다. 외부 아이콘 라이브러리나 이미지 의존성은 없습니다.

프로필 사진은 아직 제공되지 않아 About에 이름 기반 placeholder를 사용합니다.
사진 제공 후 `images/profile.webp` 등으로 저장하고 `.profile-placeholder`를 다음과 같이 교체합니다.

```html
<img class="profile-placeholder profile-photo" src="images/profile.webp"
     alt="김수정 프로필 사진" width="176" height="176" loading="lazy">
```

`profile-photo`에 `object-fit: cover`를 적용합니다. Hero는 작은 이니셜을 유지하거나
동일 사진을 120px 이하로 사용하고, About과 중복 설명이면 `alt=""`로 장식 처리합니다.
실제 파일이 생기기 전에는 위 예시 경로를 HTML에 삽입하지 않습니다.
