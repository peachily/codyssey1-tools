# Cleanup Checklist

## 생성 리소스 정리

- [x] EC2 인스턴스 종료(Terminate)
- [x] EBS 볼륨 삭제 확인
- [x] Internet Gateway 분리 및 삭제
- [x] Public Subnet 삭제
- [x] Route Table 삭제
- [x] Security Group 삭제
- [x] VPC 삭제
- [x] Key Pair 삭제

## IAM 리소스 정리

- [x] IAM 사용자 `IAM-peachily` 삭제
- [x] IAM 사용자 그룹 `codyssey_B3-1` 삭제
- [x] IAM 정책 `codyssey_B3-1_MinimumAccess` 삭제

## 추가 과금 리소스 확인

- [x] Elastic IP 없음
- [x] NAT Gateway 없음
- [x] Load Balancer 없음
- [x] RDS Database 없음

## 최종 확인

- [x] 실행 중인 EC2 인스턴스 없음
- [x] EBS 볼륨 없음
- [x] 실습에서 생성한 네트워크 리소스 삭제 완료
- [x] 실습에서 생성한 IAM 리소스 삭제 완료