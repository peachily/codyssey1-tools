# Formspree 연결하기

웹사이트에서 보낸 메시지를 Gmail로 받기 위한 설정입니다. 서버나 API 키는 필요하지 않습니다.

1. [Formspree](https://formspree.io/)에 가입하고 가입 이메일 인증을 완료합니다.
2. 대시보드에서 **+ → New Form**을 누릅니다. 이름은 `peachily contact`처럼 알아보기 쉽게 정하고, 수신 이메일은 `peachily1108@gmail.com`으로 지정합니다.
3. 만든 폼을 열고 **Integration**에서 **Form Endpoint**를 복사합니다. `https://formspree.io/f/`로 시작하는 주소입니다.
4. 그 주소를 담당 개발자에게 전달하거나 `B1-1/js/config.js`의 `formEndpoint: ''` 따옴표 안에 넣습니다. 비밀번호나 비공개 키를 공유할 필요는 없습니다.
5. 연결 후 웹사이트 폼으로 테스트 메시지 한 건을 보내고 Gmail 수신함·스팸함과 Formspree 대시보드에서 도착 여부를 확인합니다.

2026-10-23 사용자 제공 endpoint `https://formspree.io/f/mnppayoo`를 연결했습니다. 코드에서 실제 전송 테스트를 하지는 않았으므로 Gmail 수신 확인은 남아 있습니다. 초기 화면에는 설정 안내를 표시하지 않습니다.

공식 안내: [Building an HTML Form](https://help.formspree.io/articles/building-your-form/building-an-html-form/)
