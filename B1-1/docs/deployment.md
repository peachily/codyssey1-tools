# 배포와 사용자 설정

2026-10-22 기준. **로컬 준비만 완료. 사용자 요청에 따라 push 및 실제 배포는 실행하지 않았습니다.**

## GitHub Pages

현재 저장소: https://github.com/peachily/codyssey1-tools
소스: `B1-1/`. 다른 과제 디렉터리는 배포 대상에 포함하지 않습니다.

1. 변경사항을 검토한 뒤 사용자가 명시적으로 허용한 경우에만 원격에 push합니다.
2. 저장소 Settings → Pages → Build and deployment → Source를 **GitHub Actions**로 선택합니다.
3. 개인 GitHub Settings → Pages에서 `peachily.dev`를 추가합니다. 화면에 제시되는 TXT 이름과 값을 Cloudflare에 그대로 추가하고 Verify를 완료합니다. 인증 문자열은 계정마다 다르므로 이 문서에서 만들지 않습니다. 검증 후에도 TXT 레코드를 유지합니다.
4. 저장소 Settings → Pages → Custom domain에 `peachily.dev`를 저장합니다. DNS를 사이트로 연결하기 전에 이 설정을 먼저 수행합니다.
5. 아래 DNS를 설정합니다. 저장소의 Actions → Deploy peachily portfolio → Run workflow를 명시적으로 실행합니다. 워크플로에는 push 트리거가 없습니다.
6. Actions 성공, Pages의 DNS check, 도메인 소유 검증, TLS 인증서 발급을 각각 확인한 뒤 **Enforce HTTPS**를 켭니다. 이후 실제 도메인과 www 리다이렉트, CSS/JS 경로, API와 폼을 검증합니다.

워크플로는 빌드 도구 없이 HTML/CSS/JS/SVG만 업로드합니다. `CNAME`은 다른 branch 기반 배포로 옮길 때도 사용할 수 있게 준비했습니다. **Actions 방식에서는 CNAME만으로 도메인이 연결되지 않고 Settings의 Custom domain 설정이 필요합니다.**

## Cloudflare DNS

Cloudflare → peachily.dev → DNS → Records. TTL Auto. 초기 연결은 DNS only(회색 구름)로 두어 GitHub 대상 주소와 인증 상태를 직접 점검합니다. 이는 이 프로젝트의 운영 선택이며 Cloudflare가 모든 웹사이트에 DNS only를 권장한다는 의미는 아닙니다.

| 유형 | Name | Content | Proxy |
| --- | --- | --- | --- |
| A | @ | 185.199.108.153 | DNS only |
| A | @ | 185.199.109.153 | DNS only |
| A | @ | 185.199.110.153 | DNS only |
| A | @ | 185.199.111.153 | DNS only |
| CNAME | www | peachily.github.io | DNS only |
| TXT | GitHub에서 제공한 이름 | GitHub에서 제공한 값 | 해당 없음 |

IPv6 사용 시 추가하는 AAAA: `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153` (각각 @). 기존의 충돌하는 웹 레코드는 확인 후 조정하고 이메일용 MX/TXT는 보존합니다. wildcard 레코드는 만들지 않습니다.

```sh
dig +short peachily.dev A
dig +short www.peachily.dev CNAME
curl -I https://peachily.dev
```

실제 확인: 2026-10-22 현재 이 환경에서 apex A 조회에 결과가 없었고 HTTPS 요청은 `Could not resolve host`로 실패했습니다. DNS 관리 화면, 소유 검증, 인증서 발급은 확인되지 않았습니다. DNS 전파 및 GitHub HTTPS 준비에 시간이 필요할 수 있습니다.

공식 근거: [GitHub Custom Domain](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site), [GitHub Domain Verification](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/verifying-your-custom-domain-for-github-pages), [Cloudflare Proxy Status](https://developers.cloudflare.com/dns/proxy-status/).

## Formspree

처음 설정한다면 [간단한 연결 순서](formspree.md)를 참고하세요.

1. 사용자 계정으로 Formspree에서 폼을 만들고 수신 주소 `peachily1108@gmail.com`을 연결·검증합니다.
2. 대시보드에서 확인한 공개 endpoint `https://formspree.io/f/...`를 `js/config.js`의 `formEndpoint`에 넣습니다. 공개 폼 ID는 클라이언트 설정값이며, 비공개 API 키를 넣으면 안 됩니다.
3. 서비스에서 필요하면 허용 도메인에 `peachily.dev`를 설정합니다. 서비스 요금제·전송 한도·스팸 정책은 본인 계정에서 확인합니다.
4. 로컬 또는 배포 사이트에서 본인의 테스트 메시지를 한 번 보내고, 성공 UI뿐 아니라 **수신함 도착**을 확인합니다. 실제 수신 검증 전에는 완료로 표시하지 않습니다.

빈 endpoint 상태에서도 입력 검증은 동작하며, 전송 요청 없이 이메일 대안을 안내합니다. 연결 후에는 JSON POST와 `Accept: application/json`을 사용합니다. 진행 중 중복 전송을 막고, 실패 시 입력을 유지합니다. 타임아웃은 서버 수신 여부가 불명확하므로 재전송 주의 문구를 표시합니다.

[Formspree 공식 AJAX 안내](https://formspree.io/blog/formspree-ajax/)

## 나머지 설정

- 이미지: 제공된 `images/peachily.jpg` 연결 완료. 교체 방법은 [images 안내](../images/README.md) 참고.
- YouTube / Blog: 사용자 제공 URL 연결 완료. `js/config.js`에서 변경할 수 있습니다.
- Live Demo: 직접 접속 확인한 공개 URL만 `featuredProjects[].demo`에 입력합니다. 현재는 확인된 URL이 없어 표시하지 않습니다.
- MADI: 조직 저장소의 정확한 주소와 공개 여부 확인 후 별도로 연결해야 합니다. 현재는 About의 기획 소개에만 등장하며 가짜 프로젝트 카드는 없습니다.
