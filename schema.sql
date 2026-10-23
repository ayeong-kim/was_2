-- 동물병원 WAS 테이블 생성 (MySQL 8.0 / RDS)
-- 클라우드에서 admin(관리) 계정으로 한 번 실행합니다. WAS는 테이블을 만들지 않습니다.
--   mysql -h <RDS 엔드포인트> -u admin -p < schema.sql

CREATE DATABASE IF NOT EXISTS petclinic CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE petclinic;

CREATE TABLE IF NOT EXISTS User (
    uid      INT AUTO_INCREMENT PRIMARY KEY,
    login_id VARCHAR(50)  COLLATE utf8mb4_bin NOT NULL UNIQUE,   -- 대소문자 구분
    password VARCHAR(255) NOT NULL,                              -- sha256 해시
    name     VARCHAR(50)  NOT NULL,
    role     VARCHAR(20)  NOT NULL,                              -- desk / vet
    branch   VARCHAR(50)  NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS Session (
    session_id VARCHAR(32) PRIMARY KEY,                          -- 쿠키로 주고받는 값
    uid        INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uid) REFERENCES User(uid),
    INDEX idx_session_created (created_at)                       -- 만료 세션 조회·삭제
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS Owner (
    oid     INT AUTO_INCREMENT PRIMARY KEY,
    oname   VARCHAR(50)  NOT NULL,
    pnum    VARCHAR(20)  NOT NULL,
    address VARCHAR(255),
    branch  VARCHAR(50)  NOT NULL,                               -- 등록한 지점 (다른 지점에서는 안 보임)
    INDEX idx_owner_branch_name (branch, oname)                  -- 지점별 보호자 이름 검색
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS Pet (
    pid    INT AUTO_INCREMENT PRIMARY KEY,
    oid    INT NOT NULL,
    pname  VARCHAR(50) NOT NULL,
    gender VARCHAR(10),
    age    INT,
    weight DECIMAL(5,2),
    type   VARCHAR(20) NOT NULL,
    breed  VARCHAR(50),
    notes  TEXT,
    FOREIGN KEY (oid) REFERENCES Owner(oid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS Consultation (
    cid       INT AUTO_INCREMENT PRIMARY KEY,
    pid       INT NOT NULL,
    vet_uid   INT NOT NULL,
    date      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    purpose   VARCHAR(100) NOT NULL,
    diagnosis TEXT,
    status    VARCHAR(20) NOT NULL DEFAULT '대기',               -- 대기 / 진료중 / 종료
    FOREIGN KEY (pid) REFERENCES Pet(pid),
    FOREIGN KEY (vet_uid) REFERENCES User(uid),
    INDEX idx_consult_vet_status (vet_uid, status)               -- 수의사별 대기·진료중 목록
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- WAS 전용 계정: 최소 권한(CRUD)만. <비밀번호>를 바꾼 뒤 실행하세요.
-- '10.0.2%.%' = WAS 서브넷(10.0.21.x, 10.0.22.x)에서만 접속 허용
-- CREATE USER IF NOT EXISTS 'petclinic_app'@'10.0.2%.%' IDENTIFIED BY '<비밀번호>';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON petclinic.* TO 'petclinic_app'@'10.0.2%.%';
-- SHOW GRANTS FOR 'petclinic_app'@'10.0.2%.%';

-- 이미 테이블이 만들어진 DB에는 위 인덱스가 없으니, 아래 3줄을 admin 계정으로 한 번만 실행하세요.
-- (MySQL은 CREATE INDEX IF NOT EXISTS가 없어서, 두 번 실행하면 "Duplicate key name" 에러가 납니다)
-- CREATE INDEX idx_consult_vet_status ON Consultation (vet_uid, status);
-- CREATE INDEX idx_owner_branch_name  ON Owner (branch, oname);
-- CREATE INDEX idx_session_created    ON Session (created_at);
