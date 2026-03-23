# ระบบ Web Application สำหรับ Affiliate Video Automation (TikTok/Shopee/Lazada)

เอกสารนี้สรุปสถาปัตยกรรมและขอบเขตการพัฒนาระบบตามโจทย์: ดึงข้อมูลสินค้า affiliate จาก TikTok Shop/TikTok Affiliate รวม Shopee/Lazada, สร้างวิดีโอไวรัลอัตโนมัติ, โพสต์วิดีโออัตโนมัติ, เก็บฐานข้อมูลสินค้าและคอนเทนต์, มีแดชบอร์ดแยกบทบาท (Admin/User/Developer), รองรับระบบเช่าใช้งานรายเดือน/รายปี/ถาวร, เชื่อมระบบสต็อก, และมีเครื่องมือจัดกลุ่ม source code ที่ยังไม่จำเป็น.

## 1) สถาปัตยกรรมหลัก

- **Ingestion Layer**
  - TikTok Shop API Connector
  - TikTok Affiliate API Connector
  - Shopee API Connector
  - Lazada API Connector
- **Normalization Layer**
  - แปลงข้อมูลสินค้าเป็น schema กลาง (`product_catalog`)
  - ตรวจสอบข้อมูลซ้ำด้วย `source_platform + source_product_id`
- **Content Intelligence Layer**
  - คำนวณ Viral Score จาก CTR/CVR/Margin/Trend/Stock
  - สร้าง Script/Hook/CTA ต่อสินค้า
- **Video Generation Layer**
  - Template-based Render (ไม่สุ่มใน logic หลัก)
  - Multi-format output (9:16, 1:1)
- **Publishing Layer**
  - Scheduler จำกัดไม่เกิน `30 videos/day` ต่อ account
  - Auto-post queue พร้อม retry และ rate-limit
- **Analytics Layer**
  - Dashboard แยกบทบาท: Admin / User / Developer
  - รายงาน conversion, ROI, inventory impact
- **SaaS & Billing Layer**
  - แผนเช่าใช้งาน: Monthly / Yearly / Lifetime
  - License validation + tenant isolation

## 2) โครงสร้างฐานข้อมูลแนะนำ

ตารางหลักที่ต้องมี:

1. `tenants`
2. `users`
3. `products`
4. `product_inventory`
5. `content_blueprints`
6. `generated_videos`
7. `publish_jobs`
8. `affiliate_metrics`
9. `subscriptions`
10. `dashboard_snapshots`

หลักการสำคัญ:
- ใช้ `tenant_id` ในทุกตารางธุรกิจ (multi-tenant isolation)
- บังคับ unique key สำหรับแหล่งข้อมูลสินค้า
- เก็บ audit trail (`created_by`, `updated_by`, `source`, `trace_id`)

## 3) Workflow การทำงานรายวัน (Route 30 Video/Day)

1. ดึงข้อมูลสินค้าใหม่ + อัปเดตสต็อก
2. คำนวณคะแนนสินค้า (viral candidate scoring)
3. เลือกสินค้า Top-N ตามงบและ stock
4. Generate content blueprint ต่อสินค้า
5. Render วิดีโอ
6. บันทึกวิดีโอลงฐานข้อมูล
7. ส่งเข้า Auto-post queue
8. Scheduler กระจายโพสต์สูงสุด 30 วิดีโอ/วัน
9. เก็บผลลัพธ์ (views/click/order/revenue)
10. สรุปรายงานบน dashboard

## 4) Dashboard ตามบทบาท

- **Admin Dashboard**
  - Tenant overview
  - Revenue by subscription plan
  - System health + queue health + SLA
- **User Dashboard**
  - Product performance
  - Video performance
  - Conversion funnel
- **Developer Dashboard**
  - API error rate
  - Retry queue depth
  - Latency และ job throughput

## 5) รองรับหลายแพลตฟอร์มการใช้งาน

- **Windows**: ผ่าน Web + Desktop wrapper (optional)
- **Android/iOS**: ผ่าน Mobile App หรือ PWA
- **Web Control Center**: จัดการสต็อกสินค้า บริการ และสถานะโพสต์

## 6) ระบบตรวจจับและแยกโค้ดที่ยังไม่จำเป็น

ใน repository นี้เพิ่มสคริปต์:
- `scripts/repo_cleanup_audit.py`
- config: `configs/repo_cleanup_entrypoints.json`

ความสามารถ:
1. วิเคราะห์ dependency graph (Python + JS/TS local imports)
2. หาไฟล์ที่ไม่ reachable จาก entrypoint
3. สร้างรายงาน JSON
4. ย้ายไฟล์ที่ยังไม่จำเป็นไป `feature_repo/unused_candidates` แบบ deterministic

ตัวอย่างคำสั่ง:

```bash
python3 scripts/repo_cleanup_audit.py
python3 scripts/repo_cleanup_audit.py --apply
```

## 7) Security Baseline (บังคับ)

- เก็บ secret ใน ENV เท่านั้น
- ทุก API ใช้ schema validation
- JWT ต้องมี expiration และ signature validation
- ใส่ rate limiter ทุก endpoint public
- เก็บ structured logs (JSON) สำหรับ audit

## 8) Next Implementation Steps

1. สร้าง service `affiliate-automation` (API + Scheduler + Publisher)
2. เพิ่ม migrations สำหรับตาราง affiliate/video/subscription
3. เชื่อม API connectors ของ TikTok/Shopee/Lazada
4. เชื่อม renderer และ uploader จริง
5. เชื่อม billing gateway และ license enforcement
6. เพิ่ม integration tests ครอบคลุม flow ทั้งระบบ
