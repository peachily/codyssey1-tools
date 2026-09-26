# Troubleshooting

## IAM 최소 권한 설정으로 인한 Security Group 조회 오류

| 항목 | 내용 |
| --- | --- |
| **증상** | EC2 인스턴스 생성 과정에서 기존 Security Group을 선택했을 때 `ec2:GetSecurityGroupsForVpc` 권한이 없다는 오류가 발생하였다. |
| **원인 가설** | IAM 사용자에게 적용한 최소 권한 정책에 EC2 생성 과정에서 필요한 Security Group 조회 권한이 누락된 것으로 판단하였다. |
| **검증** | 오류 메시지에서 거부된 작업이 `ec2:GetSecurityGroupsForVpc`임을 확인하고, 기존 IAM 정책에 해당 권한이 포함되어 있지 않은 것을 확인하였다. |
| **조치** | IAM 정책에 `ec2:GetSecurityGroupsForVpc` 권한을 추가하였다. 기존 서울 리전(`ap-northeast-2`) 제한은 유지하였다. |
| **결과** | IAM 사용자로 다시 접속한 후 기존 Security Group을 사용하여 EC2 인스턴스 생성을 정상적으로 진행하였다. |
| **재발 방지** | 최소 권한 정책 구성 시 필요한 조회 권한을 함께 확인하고, 권한 오류 발생 시 관리자 권한을 부여하지 않고 필요한 권한만 추가한다. |

### 정책 수정 내용

```json
"Action": [
  "ec2:Describe*",
  "ec2:GetSecurityGroupsForVpc"
]
```

- `AdministratorAccess` 사용하지 않음
- 필요한 권한만 추가
- `ap-northeast-2` 리전 제한 유지