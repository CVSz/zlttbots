# สรุปสถานะปัจจุบันและสิ่งที่ควรเพิ่มต่อ (Current Status & Next Steps)

เอกสารนี้สรุปว่า **ตอนนี้ระบบมีอะไรแล้ว** และเสนอว่า **ควรเพิ่มอะไรต่อเป็นลำดับถัดไป** พร้อมตัวอย่างงานที่เริ่มทำได้ทันที

## 1) ตอนนี้เราเขียนอะไรไปแล้วบ้าง

จากโครงสร้างโปรเจกต์และเอกสารปัจจุบัน แพลตฟอร์มมีองค์ประกอบหลักครบระดับ Foundation แล้ว:

- โครงสร้างเป็น Microservices หลายตัว เช่น `viral-predictor`, `market-crawler`, `gpu-renderer`, `arbitrage-engine`, `analytics`, `account-farm`, `tiktok-uploader` และ `ai-video-generator`
- มี Infrastructure ระดับใช้งานจริง: Docker Compose, PostgreSQL migrations, Kubernetes manifests, CI/deploy scripts
- มีเอกสารครอบคลุมหลายมุม: สถาปัตยกรรม, การติดตั้ง, การปฏิบัติการ (logging/monitoring/backup), และ API overview
- มีสคริปต์ช่วย run/repair/deploy จำนวนมากใน `scripts/` และ `infrastructure/scripts/`

> สรุปสั้น: สถานะตอนนี้คือ “ระบบฐานพร้อมใช้งานและขยายต่อได้” แต่ยังขาดส่วน “การบูรณาการและคุณภาพการผลิต (production quality gates)” บางส่วน

## 2) ควรเพิ่มอะไรต่อ (เรียงตามความคุ้มค่า)

## Priority 1: ทำให้ระบบตรวจสอบสุขภาพได้ครบทุก service

**เป้าหมาย:** ทุก service ควรมี endpoint เช่น `/healthz` และมีมาตรฐาน response เดียวกัน

สิ่งที่ต้องเพิ่ม:

1. เพิ่ม health endpoint ที่ตอบสถานะ dependency สำคัญ (DB/queue/external API)
2. รวม health check เข้ากับ `docker-compose.yml` และถ้ามี k8s ให้ใส่ readiness/liveness probes
3. สร้างหน้าเอกสารกลางที่บอกว่า endpoint สุขภาพของแต่ละ service คืออะไร

ผลลัพธ์ที่ได้ทันที:
- ลดเวลาหาสาเหตุตอนระบบล่ม
- Auto-restart ทำงานได้แม่นยำขึ้น

## Priority 2: เพิ่ม “Integration Test แบบเส้นทางหลัก”

**เป้าหมาย:** ทดสอบ flow สำคัญตั้งแต่รับ request จนถึงบันทึกผลลัพธ์

สิ่งที่ต้องเพิ่ม:

1. เลือก 2-3 เส้นทางหลัก เช่น
   - `market-crawler -> analytics`
   - `tiktok-uploader -> analytics`
   - `ai-video-generator -> gpu-renderer`
2. ทำ test harness ที่รันด้วย Docker Compose profile test
3. เพิ่มคำสั่งทดสอบกลาง เช่น `./scripts/test-integration.sh`

ผลลัพธ์ที่ได้ทันที:
- มั่นใจขึ้นเวลา merge/upgrade dependency
- ลด incident จาก service contract ที่เปลี่ยนโดยไม่ตั้งใจ

## Priority 3: เพิ่ม API contract และ schema validation

**เป้าหมาย:** ลด bug จาก payload ไม่ตรงรูปแบบ

สิ่งที่ต้องเพิ่ม:

1. กำหนด JSON schema/OpenAPI สำหรับ endpoint หลัก
2. Validate request/response ฝั่ง API
3. เพิ่ม contract tests ระหว่าง service ที่คุยกันบ่อย

ผลลัพธ์ที่ได้ทันที:
- ทีมพัฒนาเชื่อม service กันง่ายขึ้น
- เอกสาร API อัปเดตตามโค้ดได้จริง

## Priority 4: ทำ Observability ให้ครบ trace + metrics + structured logs

**เป้าหมาย:** รู้ให้ได้ว่า request หนึ่งวิ่งผ่าน service ไหนบ้างและช้าเพราะอะไร

สิ่งที่ต้องเพิ่ม:

1. Correlation ID กลางในทุก service
2. Structured logging รูปแบบเดียวกัน (JSON + fields มาตรฐาน)
3. Metrics dashboard ชุดเดียวสำหรับ latency/error rate/throughput

## Priority 5: Security baseline ที่ enforce ได้จริง

**เป้าหมาย:** ลดความเสี่ยงเชิงระบบก่อนโต

สิ่งที่ต้องเพิ่ม:

1. Secrets management (ย้ายค่าลับออกจากไฟล์ plain env)
2. Dependency scanning ใน CI
3. Image scanning + minimum base image hardening
4. Rate limiting และ auth policy สำหรับ endpoint ที่เสี่ยง

## 3) ตัวอย่างแผน 2 สัปดาห์ (เริ่มได้เลย)

### Week 1
- สร้างมาตรฐาน `/healthz` ทุก service
- ต่อ health check เข้า compose/k8s
- เขียนเอกสาร endpoint สุขภาพรวม

### Week 2
- ทำ integration test เส้นทางหลักอย่างน้อย 2 flow
- เพิ่ม schema validation ให้ endpoint สำคัญ 3 จุด
- ใส่ CI gate: ถ้า integration test fail ให้ block merge

## 4) Definition of Done (DoD) ที่แนะนำ

งานแต่ละ service ถือว่าเสร็จเมื่อ:

- มี health endpoint และผ่าน check อัตโนมัติ
- มี integration test อย่างน้อย 1 เคสต่อเส้นทางหลัก
- มี schema validation สำหรับ request สำคัญ
- มี structured logs พร้อม correlation id
- มีเอกสารอัปเดตใน `docs/services/*.md`

## 5) Backlog พร้อมหยิบทำ (Ready-to-implement)

1. สร้างไฟล์ `docs/operations/health-checks.md` รวบรวม endpoint สุขภาพทั้งหมด
2. เพิ่มสคริปต์ `scripts/test-integration.sh` สำหรับรัน smoke/integration test
3. เพิ่ม CI job `integration-test` ใน pipeline
4. อัปเดต `docs/api/api-overview.md` ให้มีตัวอย่าง payload ที่ตรวจ schema แล้ว
5. เพิ่มเอกสาร runbook incident สั้น ๆ ต่อ service ใน `docs/operations/`

---

หากต้องการต่อยอดทันที แนะนำเริ่มจาก **Priority 1 + Priority 2** ก่อน เพราะได้ผลด้านเสถียรภาพเร็วที่สุดและลดปัญหาตอน deploy จริงอย่างชัดเจน
